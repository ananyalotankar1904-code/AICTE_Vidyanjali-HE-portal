"""
SIH26262 — Canonical Data Integration & Repeatable Seeder
Idempotent seeding script for SIH demonstration using canonical datasets (Datasets 1-9).

Modes:
  python data/seed/seed_canonical_data.py --dry-run   (Default: validates & reports without writes)
  python data/seed/seed_canonical_data.py --execute   (Executes controlled transactions)
"""

import os
import sys
import argparse
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Member 3 Database & Models
from app.database import SessionLocal as M3SessionLocal
from app.models.application import Application as M3Application, WorkflowHistory as M3WorkflowHistory

# Member 4 Database & Models
from backend.app.db import SessionLocal as M4SessionLocal, init_db as m4_init_db
from backend.app.models.application import Application as M4Application
from backend.app.models.evc import EVCRecord as M4EVCRecord
from backend.app.models.compliance import ComplianceObligation as M4ComplianceObligation
from backend.app.models.document import Document as M4Document
from backend.app.models.deadline import DeadlineRecord as M4DeadlineRecord
from backend.app.models.notification import Notification as M4Notification
from backend.app.models.audit import AuditEvent as M4AuditEvent
from backend.app.enums import (
    ApplicationStatus,
    WorkflowStage,
    EVCStatus,
    EVCReportReviewOutcome,
    ObligationStatus,
    DocumentReviewStatus,
    DeadlineStatus,
    NotificationType,
    EntityType,
    UserRole,
)


# ==============================================================================
# Helper Functions: Excel Parsing & Type Conversions
# ==============================================================================

def excel_serial_to_dt(serial_val: Any) -> Optional[datetime]:
    """Converts an Excel serial date number to UTC datetime."""
    if serial_val is None or str(serial_val).strip() == "" or str(serial_val).strip() == "-":
        return None
    try:
        val = float(serial_val)
        base = datetime(1899, 12, 30, tzinfo=timezone.utc)
        return base + timedelta(days=val)
    except Exception:
        return None


def excel_serial_to_date_str(serial_val: Any) -> Optional[str]:
    """Converts an Excel serial date number to ISO YYYY-MM-DD string."""
    dt = excel_serial_to_dt(serial_val)
    return dt.strftime("%Y-%m-%d") if dt else None


def col2num(col_str: str) -> int:
    num = 0
    for c in col_str:
        num = num * 26 + (ord(c.upper()) - ord("A")) + 1
    return num


def parse_xlsx_sheet(file_path: str, sheet_name_or_index: Any = 0) -> Tuple[List[str], List[List[Any]]]:
    """Pure-Python standard-library XLSX sheet parser."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with zipfile.ZipFile(file_path, "r") as z:
        # Read shared strings
        shared_strings = []
        try:
            ss_xml = z.read("xl/sharedStrings.xml")
            ss_root = ET.fromstring(ss_xml)
            ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in ss_root.findall("ns:si", ns):
                text_pieces = [t.text for t in si.findall(".//ns:t", ns) if t.text]
                shared_strings.append("".join(text_pieces))
        except KeyError:
            shared_strings = []

        # Find sheet target
        wb_xml = z.read("xl/workbook.xml")
        wb_root = ET.fromstring(wb_xml)
        ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheets = []
        for s in wb_root.find("ns:sheets", ns).findall("ns:sheet", ns):
            name = s.get("name")
            r_id = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            sheets.append((name, r_id))

        rel_xml = z.read("xl/_rels/workbook.xml.rels")
        rel_root = ET.fromstring(rel_xml)
        rel_ns = {"ns": "http://schemas.openxmlformats.org/package/2006/relationships"}
        rels = {r.get("Id"): r.get("Target") for r in rel_root.findall("ns:Relationship", rel_ns)}

        target_path = None
        if isinstance(sheet_name_or_index, str):
            for name, r_id in sheets:
                if name.lower() == sheet_name_or_index.lower():
                    target_path = rels[r_id]
                    break
        elif isinstance(sheet_name_or_index, int) and 0 <= sheet_name_or_index < len(sheets):
            target_path = rels[sheets[sheet_name_or_index][1]]

        if not target_path:
            # default to first sheet
            target_path = rels[sheets[0][1]]

        if not target_path.startswith("xl/"):
            target_path = "xl/" + target_path

        sheet_xml = z.read(target_path)
        sroot = ET.fromstring(sheet_xml)
        sheet_data = sroot.find("ns:sheetData", ns)
        if sheet_data is None:
            return [], []

        rows_data = []
        for row in sheet_data.findall("ns:row", ns):
            row_num = int(row.get("r", len(rows_data) + 1))
            cells = {}
            max_col = 0
            for c in row.findall("ns:c", ns):
                r_ref = c.get("r", "")
                col_letters = "".join([ch for ch in r_ref if ch.isalpha()])
                col_idx = col2num(col_letters) if col_letters else len(cells) + 1
                if col_idx > max_col:
                    max_col = col_idx
                t = c.get("t")
                v = c.find("ns:v", ns)
                val = None
                if v is not None and v.text is not None:
                    if t == "s":
                        val = shared_strings[int(v.text)]
                    else:
                        val = v.text
                cells[col_idx] = val

            row_vals = [cells.get(i, None) for i in range(1, max_col + 1)]
            rows_data.append((row_num, row_vals))

        return rows_data


# ==============================================================================
# Canonical Dataset Loaders
# ==============================================================================

def load_dataset_1_institutions(base_dir: str = "data/seed") -> Dict[str, Dict[str, Any]]:
    """Loads Dataset 1 institution dictionary: INST001..INST015."""
    fpath = os.path.join(base_dir, "dataset_1_institutions.xlsx")
    rows = parse_xlsx_sheet(fpath, "Selected_Institutions")
    if not rows:
        return {}
    header = rows[0][1]
    institutions = {}
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        inst_id = str(rvals[0]).strip()
        record = dict(zip(header, rvals))
        institutions[inst_id] = {
            "institution_id": inst_id,
            "aishe_code": record.get("aishe_code"),
            "name": record.get("Name"),
            "state": record.get("State"),
            "district": record.get("District"),
            "website": record.get("Website"),
            "year_established": int(float(record.get("Year Of Establishment", 2000))),
            "location": record.get("Location"),
            "college_type": record.get("College Type"),
            "management": record.get("management"),
            "university_name": record.get("University Name"),
        }
    return institutions


def load_dataset_2_applications(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 2 applications: APP001..APP025."""
    fpath = os.path.join(base_dir, "dataset_2_applications.xlsx")
    rows = parse_xlsx_sheet(fpath, "Applications")
    if not rows:
        return []
    header = rows[0][1]
    applications = []
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        record = dict(zip(header, rvals))
        applications.append(record)
    return applications


def load_dataset_4_evc(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 4 EVC schedules: EVC001..EVC007."""
    fpath = os.path.join(base_dir, "dataset_4_evc_schedules.xlsx")
    rows = parse_xlsx_sheet(fpath, "EVC_Records")
    if not rows:
        return []
    header = rows[0][1]
    evcs = []
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        record = dict(zip(header, rvals))
        evcs.append(record)
    return evcs


def load_dataset_5_undertakings(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 5 undertakings: UND-2026-001..UND-2026-010."""
    fpath = os.path.join(base_dir, "dataset_5_undertakings.xlsx")
    rows = parse_xlsx_sheet(fpath, "Undertakings")
    if not rows:
        return []
    header = rows[0][1]
    undertakings = []
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        record = dict(zip(header, rvals))
        undertakings.append(record)
    return undertakings


def load_dataset_6_documents(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 6 documents: DOC-2026-0001..DOC-2026-0014."""
    fpath = os.path.join(base_dir, "dataset_6_documents.xlsx")
    rows = parse_xlsx_sheet(fpath, "Documents")
    if not rows:
        return []
    header = rows[0][1]
    documents = []
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        record = dict(zip(header, rvals))
        documents.append(record)
    return documents


def load_dataset_7_deadlines(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 7 deadlines: DDL-2026-001..DDL-2026-024."""
    fpath = os.path.join(base_dir, "dataset_7_deadlines_notifications.xlsx")
    rows = parse_xlsx_sheet(fpath, "Deadlines")
    if not rows:
        return []
    header = rows[0][1]
    deadlines = []
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        record = dict(zip(header, rvals))
        deadlines.append(record)
    return deadlines


def load_dataset_7_notifications(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 7 notifications: NOTIF-2026-001..NOTIF-2026-030."""
    fpath = os.path.join(base_dir, "dataset_7_deadlines_notifications.xlsx")
    rows = parse_xlsx_sheet(fpath, "Notifications")
    if not rows:
        return []
    header = rows[0][1]
    notifications = []
    for rnum, rvals in rows[1:]:
        if not rvals or not rvals[0]:
            continue
        record = dict(zip(header, rvals))
        notifications.append(record)
    return notifications


def load_dataset_9_audit_events(base_dir: str = "data/seed") -> List[Dict[str, Any]]:
    """Loads Dataset 9 audit events: EVT-2026-0001..EVT-2026-0020 (Header at Row 6!)."""
    fpath = os.path.join(base_dir, "dataset_9_audit_events.xlsx")
    rows = parse_xlsx_sheet(fpath, "Audit_Events")
    if not rows:
        return []
    
    # Critical: header is at Row 6 (index 5)
    header_row = None
    for rnum, rvals in rows:
        if rnum == 6:
            header_row = rvals
            break
    
    if not header_row:
        return []

    events = []
    for rnum, rvals in rows:
        if rnum >= 7 and rvals and rvals[0]:
            record = dict(zip(header_row, rvals))
            events.append(record)
    return events


# ==============================================================================
# Idempotent Seeder Engine
# ==============================================================================

class SeederEngine:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.reports: List[str] = []
        self.stats = {
            "m3_apps_inserted": 0,
            "m3_apps_skipped": 0,
            "m4_apps_inserted": 0,
            "m4_apps_skipped": 0,
            "evc_inserted": 0,
            "evc_skipped": 0,
            "obligations_inserted": 0,
            "obligations_skipped": 0,
            "obligations_blocked": 0,
            "documents_inserted": 0,
            "documents_skipped": 0,
            "deadlines_inserted": 0,
            "deadlines_skipped": 0,
            "notifications_inserted": 0,
            "notifications_skipped": 0,
            "audit_inserted": 0,
            "audit_skipped": 0,
        }

    def log(self, msg: str):
        print(msg)
        self.reports.append(msg)

    def run(self):
        mode_str = "DRY-RUN (VALIDATION ONLY, NO WRITES)" if self.dry_run else "EXECUTE (WRITING TRANSACTIONS)"
        self.log(f"\n=======================================================")
        self.log(f"  AICTE CANONICAL DATA SEEDER -- {mode_str}")
        self.log(f"=======================================================\n")

        # Stage 1: Ingest Institution Master
        self.log("[Stage 1] Auditing Dataset 1 Institution Master...")
        inst_dir = load_dataset_1_institutions()
        self.log(f"  Verified {len(inst_dir)} master institutions (INST001 - INST015).")

        # Stage 2: Applications Master
        self.log("\n[Stage 2] Auditing & Seeding Applications Master (Dataset 2)...")
        app_records = load_dataset_2_applications()
        self.log(f"  Loaded {len(app_records)} canonical application records (APP001 - APP025).")

        # Member 3 applications
        m3_db = M3SessionLocal()
        try:
            for rec in app_records:
                app_id = rec["application_id"]
                existing = m3_db.query(M3Application).filter(M3Application.application_id == app_id).first()
                if existing:
                    self.stats["m3_apps_skipped"] += 1
                else:
                    self.stats["m3_apps_inserted"] += 1
                    if not self.dry_run:
                        new_app = M3Application(
                            application_id=app_id,
                            institution_id=rec["institution_id"],
                            application_type=rec["application_type"],
                            current_stage=rec["current_stage"],
                            application_status=rec["application_status"],
                            submitted_date=excel_serial_to_date_str(rec.get("submitted_date")) or "2026-10-25",
                            stage_entered_date=excel_serial_to_date_str(rec.get("stage_entered_date")) or "2026-10-25",
                            due_date=excel_serial_to_date_str(rec.get("due_date")),
                            last_updated=excel_serial_to_date_str(rec.get("last_updated")) or "2026-10-25",
                            assigned_role=rec.get("assigned_role", "Intake Officer"),
                            deficiency_flag=rec.get("deficiency_flag", "No"),
                            data_type=rec.get("data_type", "SYNTHETIC_DEMO"),
                            deadline_condition=rec.get("deadline_condition", "ON_TRACK"),
                            reference_date="2026-10-25",
                            demo_notes=rec.get("demo_notes"),
                            academic_year="2026-2027",
                        )
                        m3_db.add(new_app)
                        m3_hist = M3WorkflowHistory(
                            application_id=app_id,
                            from_stage="NONE",
                            to_stage=rec["current_stage"],
                            from_status="NONE",
                            to_status=rec["application_status"],
                            action="SEED_IMPORT",
                            actor_id="system_seed",
                            actor_role="System",
                            timestamp=datetime.now(timezone.utc),
                            remarks="Imported from synthetic canonical dataset",
                        )
                        m3_db.add(m3_hist)

            if not self.dry_run:
                m3_db.commit()
            self.log(f"  aicte_platform.db (Member 3): {self.stats['m3_apps_inserted']} to insert, {self.stats['m3_apps_skipped']} existing skipped.")
        except Exception as e:
            m3_db.rollback()
            self.log(f"  [ERROR] Member 3 application seeding error: {e}")
            raise
        finally:
            m3_db.close()

        # Member 4 applications
        m4_init_db()
        m4_db = M4SessionLocal()
        try:
            for rec in app_records:
                app_id = rec["application_id"]
                existing = m4_db.query(M4Application).filter(M4Application.id == app_id).first()
                if existing:
                    self.stats["m4_apps_skipped"] += 1
                else:
                    self.stats["m4_apps_inserted"] += 1
                    inst_id = rec["institution_id"]
                    inst_meta = inst_dir.get(inst_id, {})
                    inst_name = inst_meta.get("name", f"Institution {inst_id}")

                    # Map stage and status to Member 4 enums
                    raw_stage = rec["current_stage"]
                    stage_map = {
                        "DRAFT": WorkflowStage.INTAKE,
                        "SUBMITTED": WorkflowStage.INTAKE,
                        "INITIAL_VALIDATION": WorkflowStage.VALIDATION,
                        "INITIAL_SCRUTINY": WorkflowStage.SCRUTINY,
                        "DEFICIENCY_RAISED": WorkflowStage.DEFICIENCY_PENDING,
                        "RE_SCRUTINY": WorkflowStage.RE_SCRUTINY,
                        "EVC_PENDING": WorkflowStage.EVC_PENDING,
                        "EVC_SCHEDULED": WorkflowStage.EVC_SCHEDULED,
                        "EVC_COMPLETED": WorkflowStage.EVC_REPORT_REVIEW,
                        "COMMITTEE_REVIEW": WorkflowStage.COMMITTEE_REVIEW,
                        "DECISION_PENDING": WorkflowStage.DECISION_PENDING,
                        "COMPLETED": WorkflowStage.COMPLETED,
                        "REJECTED": WorkflowStage.COMPLETED,
                    }
                    m4_stage = stage_map.get(raw_stage, WorkflowStage.SCRUTINY)

                    raw_status = rec["application_status"]
                    status_map = {
                        "DRAFT": ApplicationStatus.DRAFT,
                        "SUBMITTED": ApplicationStatus.SUBMITTED,
                        "IN_PROGRESS": ApplicationStatus.IN_PROGRESS,
                        "ACTION_REQUIRED": ApplicationStatus.ACTION_REQUIRED,
                        "COMPLETED": ApplicationStatus.COMPLETED,
                        "REJECTED": ApplicationStatus.REJECTED,
                    }
                    m4_status = status_map.get(raw_status, ApplicationStatus.IN_PROGRESS)

                    route_map = {
                        "Extension of Approval": "ROUTE_EOA_STD",
                        "New Programme": "ROUTE_NEW_INST",
                        "Increase in Intake": "ROUTE_INC_INTAKE",
                    }
                    route_id = route_map.get(rec["application_type"], "ROUTE_FULL_SCRUTINY_EVC")

                    sub_dt = excel_serial_to_dt(rec.get("submitted_date")) or datetime.now(timezone.utc)
                    ent_dt = excel_serial_to_dt(rec.get("stage_entered_date")) or sub_dt

                    if not self.dry_run:
                        new_m4_app = M4Application(
                            id=app_id,
                            application_number=app_id,
                            institution_id=inst_id,
                            institution_name=inst_name,
                            application_type=rec["application_type"],
                            route_id=route_id,
                            status=m4_status,
                            current_stage=m4_stage,
                            assigned_to=rec.get("assigned_role"),
                            description=rec.get("demo_notes"),
                            created_at=ent_dt,
                            submitted_at=sub_dt,
                            updated_at=datetime.now(timezone.utc),
                        )
                        m4_db.add(new_m4_app)

            if not self.dry_run:
                m4_db.commit()
            self.log(f"  aicte.db (Member 4): {self.stats['m4_apps_inserted']} to insert, {self.stats['m4_apps_skipped']} existing skipped.")
        except Exception as e:
            m4_db.rollback()
            self.log(f"  [ERROR] Member 4 application seeding error: {e}")
            raise

        # Stage 3: Dependent Compliance Entities (EVC, Obligations, Documents, Deadlines)
        self.log("\n[Stage 3] Auditing & Seeding Compliance Entities (Datasets 4, 5, 6, 7)...")
        
        # 3a. EVC Records
        evc_records = load_dataset_4_evc()
        for rec in evc_records:
            evc_id = rec["evc_id"]
            app_id = rec["application_id"]
            
            # Verify FK in aicte.db
            app_exists = m4_db.query(M4Application).filter(M4Application.id == app_id).first()
            if not app_exists and self.dry_run and self.stats["m4_apps_inserted"] > 0:
                # App will exist after insert
                pass
            elif not app_exists and not self.dry_run:
                self.log(f"  [FK FAILURE] EVC {evc_id} references missing application {app_id}!")
                continue

            existing = m4_db.query(M4EVCRecord).filter(M4EVCRecord.id == evc_id).first()
            if existing:
                self.stats["evc_skipped"] += 1
            else:
                self.stats["evc_inserted"] += 1
                raw_status = rec["evc_status"]
                status_map = {
                    "PROPOSED": EVCStatus.PENDING_SCHEDULING,
                    "SCHEDULED": EVCStatus.SCHEDULED,
                    "RESCHEDULED": EVCStatus.SCHEDULED,
                    "VISIT_COMPLETED": EVCStatus.VISIT_COMPLETED,
                    "REPORT_SUBMITTED": EVCStatus.REPORT_SUBMITTED,
                    "REPORT_UNDER_REVIEW": EVCStatus.REPORT_SUBMITTED,
                    "REPORT_REVIEWED": EVCStatus.REPORT_REVIEWED,
                }
                evc_status = status_map.get(raw_status, EVCStatus.PENDING_SCHEDULING)
                
                resched_history = []
                if raw_status == "RESCHEDULED" and rec.get("rescheduled_from_date"):
                    resched_history.append({
                        "previous_date": excel_serial_to_date_str(rec.get("rescheduled_from_date")),
                        "new_date": excel_serial_to_date_str(rec.get("scheduled_date")),
                        "reason": rec.get("reschedule_reason", "Administrative reschedule"),
                        "rescheduled_by": "EVC Coordinator",
                        "rescheduled_at": "2026-10-24T10:00:00Z"
                    })

                review_outcome = None
                if rec.get("report_status") == "Reviewed":
                    review_outcome = EVCReportReviewOutcome.ACCEPTED

                sched_dt = excel_serial_to_dt(rec.get("scheduled_date"))
                created_dt = excel_serial_to_dt(rec.get("record_created_date")) or datetime.now(timezone.utc)

                if not self.dry_run:
                    new_evc = M4EVCRecord(
                        id=evc_id,
                        application_id=app_id,
                        status=evc_status,
                        assigned_team_id=rec.get("evc_team_id"),
                        assigned_members=[f"Panel Expert ({rec.get('evc_team_id', 'Team')})"],
                        planned_visit_date=sched_dt,
                        actual_visit_date=sched_dt if raw_status in ["VISIT_COMPLETED", "REPORT_SUBMITTED", "REPORT_REVIEWED"] else None,
                        venue_address=f"Campus Inspection Venue for {rec.get('institution_id')}",
                        scheduling_notes=rec.get("demo_notes"),
                        reschedule_history=resched_history,
                        report_review_outcome=review_outcome,
                        created_at=created_dt,
                        updated_at=datetime.now(timezone.utc),
                    )
                    m4_db.add(new_evc)

        self.log(f"  EVC Records (Dataset 4): {self.stats['evc_inserted']} to insert, {self.stats['evc_skipped']} existing skipped.")

        # 3b. Compliance Obligations (Undertakings)
        undertakings = load_dataset_5_undertakings()
        for rec in undertakings:
            und_id = rec["undertaking_id"]
            app_id = rec["application_id"]
            inst_id = rec["institution_id"]

            # Foreign key validation check
            if inst_id not in inst_dir:
                self.log(f"  [FLAGGED FK CONFLICT] Undertaking {und_id} has invalid institution {inst_id} & app {app_id}. SKIPPING per safety policy.")
                self.stats["obligations_blocked"] += 1
                continue

            existing = m4_db.query(M4ComplianceObligation).filter(M4ComplianceObligation.id == und_id).first()
            if existing:
                self.stats["obligations_skipped"] += 1
            else:
                self.stats["obligations_inserted"] += 1
                raw_status = rec["undertaking_status"]
                status_map = {
                    "AWAITING_SUBMISSION": ObligationStatus.PENDING,
                    "DUE_SOON": ObligationStatus.PENDING,
                    "OVERDUE": ObligationStatus.PENDING,
                    "SUBMITTED": ObligationStatus.SUBMITTED,
                    "AWAITING_VERIFICATION": ObligationStatus.SUBMITTED,
                    "CORRECTION_REQUESTED": ObligationStatus.NEEDS_CORRECTION,
                    "VERIFIED": ObligationStatus.VERIFIED,
                    "COMPLETED": ObligationStatus.VERIFIED,
                }
                ob_status = status_map.get(raw_status, ObligationStatus.PENDING)
                
                due_dt = excel_serial_to_dt(rec.get("due_date"))
                sub_dt = excel_serial_to_dt(rec.get("submitted_date"))
                issued_dt = excel_serial_to_dt(rec.get("issued_date")) or datetime.now(timezone.utc)

                if not self.dry_run:
                    new_ob = M4ComplianceObligation(
                        id=und_id,
                        application_id=app_id,
                        institution_id=inst_id,
                        title=rec.get("obligation_type", "Compliance Undertaking"),
                        obligation_type=rec.get("obligation_type", "AFFIDAVIT_SUBMISSION"),
                        description=rec.get("obligation_description", "Mandatory regulatory compliance affidavit"),
                        source_reference=rec.get("source_reference", "UNVERIFIED — DEMO CONFIGURATION"),
                        is_illustrative_demo_rule=True,
                        due_date=due_dt,
                        responsible_owner=rec.get("assigned_role", "ROLE_INSTITUTION_ADMIN"),
                        status=ob_status,
                        evidence_document_id=rec.get("evidence_document_id"),
                        submitted_at=sub_dt,
                        submitted_by=rec.get("assigned_role") if sub_dt else None,
                        verification_result=rec.get("verification_outcome"),
                        verified_at=excel_serial_to_dt(rec.get("verified_date")),
                        verified_by=rec.get("verified_by"),
                        correction_history=[],
                        created_at=issued_dt,
                        updated_at=datetime.now(timezone.utc),
                    )
                    m4_db.add(new_ob)

        self.log(f"  Compliance Obligations (Dataset 5): {self.stats['obligations_inserted']} to insert, {self.stats['obligations_skipped']} skipped, {self.stats['obligations_blocked']} unmapped/blocked.")

        # 3c. Documents (Topological Order: v1 before v2)
        documents = load_dataset_6_documents()
        # Sort documents by version ascending (v1 first)
        documents.sort(key=lambda d: float(d.get("document_version", 1)))
        
        for rec in documents:
            doc_id = rec["document_id"]
            app_id = rec["application_id"]
            inst_id = rec["institution_id"]

            existing = m4_db.query(M4Document).filter(M4Document.id == doc_id).first()
            if existing:
                self.stats["documents_skipped"] += 1
            else:
                self.stats["documents_inserted"] += 1
                raw_status = rec["document_status"]
                status_map = {
                    "VALID": DocumentReviewStatus.VERIFIED,
                    "SUPERSEDED": DocumentReviewStatus.VERIFIED,
                    "EXPIRING_SOON": DocumentReviewStatus.PENDING_REVIEW,
                    "SUBMITTED": DocumentReviewStatus.PENDING_REVIEW,
                    "UNDER_REVIEW": DocumentReviewStatus.PENDING_REVIEW,
                    "EXPIRED": DocumentReviewStatus.NEEDS_REPLACEMENT,
                    "DEFICIENCY_FLAGGED": DocumentReviewStatus.NEEDS_REPLACEMENT,
                    "REJECTED": DocumentReviewStatus.REJECTED,
                }
                rev_status = status_map.get(raw_status, DocumentReviewStatus.PENDING_REVIEW)
                
                prev_id = rec.get("previous_version_document_id")
                if prev_id == "-" or not prev_id:
                    prev_id = None

                issue_dt = excel_serial_to_dt(rec.get("issue_date"))
                exp_dt = excel_serial_to_dt(rec.get("expiry_date"))
                sub_dt = excel_serial_to_dt(rec.get("submitted_date")) or datetime.now(timezone.utc)
                rev_dt = excel_serial_to_dt(rec.get("reviewed_date"))

                if not self.dry_run:
                    new_doc = M4Document(
                        id=doc_id,
                        application_id=app_id,
                        institution_id=inst_id,
                        document_type=rec.get("document_type", "Standard Compliance Document"),
                        title=rec.get("document_description", "Institutional Document"),
                        file_name=f"{doc_id.lower()}.pdf",
                        storage_path=rec.get("storage_reference", f"/vault/docs/{doc_id}.pdf"),
                        file_size_bytes=1048576,
                        file_mime_type="application/pdf",
                        version=int(float(rec.get("document_version", 1))),
                        is_latest=(raw_status != "SUPERSEDED"),
                        previous_version_id=prev_id,
                        issue_date=issue_dt,
                        expiry_date=exp_dt,
                        is_expiry_tracked=(exp_dt is not None),
                        review_status=rev_status,
                        reviewed_at=rev_dt,
                        reviewed_by=rec.get("reviewed_by") if rev_dt else None,
                        created_by=inst_id,
                        created_at=sub_dt,
                        updated_at=datetime.now(timezone.utc),
                    )
                    m4_db.add(new_doc)

        self.log(f"  Documents (Dataset 6): {self.stats['documents_inserted']} to insert, {self.stats['documents_skipped']} existing skipped.")

        # 3d. Deadlines
        deadlines = load_dataset_7_deadlines()
        for rec in deadlines:
            ddl_id = rec["deadline_id"]
            existing = m4_db.query(M4DeadlineRecord).filter(M4DeadlineRecord.id == ddl_id).first()
            if existing:
                self.stats["deadlines_skipped"] += 1
            else:
                self.stats["deadlines_inserted"] += 1
                raw_status = rec["deadline_status"]
                status_map = {
                    "UPCOMING": DeadlineStatus.ACTIVE,
                    "DUE": DeadlineStatus.ACTIVE,
                    "ESCALATED": DeadlineStatus.ACTIVE,
                    "OVERDUE": DeadlineStatus.OVERDUE,
                    "COMPLETED": DeadlineStatus.COMPLETED,
                    "CANCELLED": DeadlineStatus.CANCELLED,
                }
                ddl_status = status_map.get(raw_status, DeadlineStatus.ACTIVE)

                due_dt = excel_serial_to_dt(rec.get("due_date")) or datetime.now(timezone.utc)
                last_eval_dt = excel_serial_to_dt(rec.get("last_evaluated_date"))
                comp_dt = excel_serial_to_dt(rec.get("completion_cancellation_date"))

                if not self.dry_run:
                    new_ddl = M4DeadlineRecord(
                        id=ddl_id,
                        entity_type=rec.get("related_entity_type", "APPLICATION"),
                        entity_id=rec.get("related_entity_id", rec.get("application_id")),
                        deadline_type=rec.get("deadline_category", "GENERAL_DEADLINE"),
                        title=rec.get("deadline_description", "Regulatory Deadline"),
                        due_date=due_dt,
                        owner_role=rec.get("assigned_role", "ROLE_INSTITUTION_ADMIN"),
                        owner_id=rec.get("institution_id"),
                        source_reference=rec.get("source_reference", "Illustrative Demo Policy"),
                        is_statutory=(rec.get("is_demo_rule") == "0" or rec.get("is_demo_rule") == 0),
                        status=ddl_status,
                        warning_threshold_hours=48,
                        last_evaluated_at=last_eval_dt,
                        completed_at=comp_dt if ddl_status == DeadlineStatus.COMPLETED else None,
                        cancelled_at=comp_dt if ddl_status == DeadlineStatus.CANCELLED else None,
                        escalation_policy=rec.get("escalation_policy", "ALERT_ONLY_LEVEL_1"),
                        escalation_triggered=(raw_status == "ESCALATED"),
                        escalation_history=[],
                        created_at=datetime.now(timezone.utc) - timedelta(days=5),
                        updated_at=datetime.now(timezone.utc),
                    )
                    m4_db.add(new_ddl)

        self.log(f"  Deadlines (Dataset 7): {self.stats['deadlines_inserted']} to insert, {self.stats['deadlines_skipped']} existing skipped.")

        # Commit Stage 3 if executing
        if not self.dry_run:
            m4_db.commit()

        # Stage 4: Notifications & Audit Events
        self.log("\n[Stage 4] Auditing & Seeding Notifications & Audit Events (Datasets 7 & 9)...")
        
        # 4a. Notifications
        notifications = load_dataset_7_notifications()
        for rec in notifications:
            notif_id = rec["notification_id"]
            dedup_key = rec.get("deduplication_key", f"notif:{notif_id}")
            
            # Check by ID or dedup key
            existing = m4_db.query(M4Notification).filter(
                (M4Notification.id == notif_id) | (M4Notification.deduplication_key == dedup_key)
            ).first()
            
            if existing:
                self.stats["notifications_skipped"] += 1
            else:
                self.stats["notifications_inserted"] += 1
                raw_type = rec.get("trigger_reason", "GENERAL")
                type_map = {
                    "SLA_WARNING": NotificationType.DEADLINE_UPCOMING,
                    "SLA_EXPIRING": NotificationType.DEADLINE_UPCOMING,
                    "DEFICIENCY_FLAGGED": NotificationType.OBLIGATION_ACTION_REQUIRED,
                    "APPROVAL_ISSUED": NotificationType.GENERAL,
                    "DOCUMENT_UPLOADED": NotificationType.GENERAL,
                    "STAGE_ENTRY": NotificationType.GENERAL,
                }
                notif_type = type_map.get(raw_type, NotificationType.GENERAL)
                
                dispatch_dt = excel_serial_to_dt(rec.get("dispatch_timestamp")) or datetime.now(timezone.utc)
                read_dt = excel_serial_to_dt(rec.get("read_timestamp"))
                is_read = (rec.get("read_status") == "READ")

                if not self.dry_run:
                    new_notif = M4Notification(
                        id=notif_id,
                        recipient_role=rec.get("recipient_role", "ROLE_INSTITUTION_ADMIN"),
                        recipient_id=None,
                        notification_type=notif_type,
                        entity_type=EntityType.APPLICATION.value,
                        entity_id=rec.get("application_id", "APP001"),
                        title=rec.get("notification_title", "Regulatory Notice"),
                        message=rec.get("message_body", "System Notification Body"),
                        is_read=is_read,
                        read_at=read_dt if is_read else None,
                        deduplication_key=dedup_key,
                        source_event=rec.get("event_source", "CANONICAL_SEED"),
                        created_at=dispatch_dt,
                    )
                    m4_db.add(new_notif)

        self.log(f"  Notifications (Dataset 7): {self.stats['notifications_inserted']} to insert, {self.stats['notifications_skipped']} existing skipped.")

        # 4b. Synthetic Audit Events (Dataset 9, header row 6!)
        audit_events = load_dataset_9_audit_events()
        for rec in audit_events:
            evt_id = rec["audit_event_id"]
            existing = m4_db.query(M4AuditEvent).filter(M4AuditEvent.id == evt_id).first()
            if existing:
                self.stats["audit_skipped"] += 1
            else:
                self.stats["audit_inserted"] += 1
                evt_dt = excel_serial_to_dt(rec.get("timestamp")) or datetime.now(timezone.utc)
                
                if not self.dry_run:
                    new_evt = M4AuditEvent(
                        id=evt_id,
                        actor_id=rec.get("actor_user_id", "SYSTEM"),
                        actor_role=rec.get("actor_role", "ROLE_SYS_ADMIN"),
                        action=rec.get("action_code", "WORKFLOW_ACTION"),
                        entity_type=rec.get("entity_type", "APPLICATION"),
                        entity_id=rec.get("entity_id", rec.get("application_id", "APP001")),
                        timestamp=evt_dt,
                        before_state={"stage": rec.get("previous_stage"), "status": rec.get("previous_status")},
                        after_state={"stage": rec.get("new_stage"), "status": rec.get("new_status")},
                        reason=rec.get("reason_or_comment"),
                        details={
                            "is_synthetic_demo_event": True,
                            "action_description": rec.get("action_description"),
                            "event_source": rec.get("event_source", "DATASET_9_SEED"),
                            "demo_notes": rec.get("demo_notes"),
                        }
                    )
                    m4_db.add(new_evt)

        self.log(f"  Audit Events (Dataset 9): {self.stats['audit_inserted']} to insert, {self.stats['audit_skipped']} existing skipped.")

        # Commit Stage 4 if executing
        if not self.dry_run:
            m4_db.commit()

        m4_db.close()

        # Summary
        self.log(f"\n=======================================================")
        self.log(f"  SEEDER EXECUTION SUMMARY ({mode_str})")
        self.log(f"=======================================================")
        self.log(f"  Database 1 (aicte_platform.db):")
        self.log(f"    - Applications to insert : {self.stats['m3_apps_inserted']}")
        self.log(f"    - Existing apps skipped  : {self.stats['m3_apps_skipped']}")
        self.log(f"  Database 2 (aicte.db):")
        self.log(f"    - Applications to insert : {self.stats['m4_apps_inserted']}")
        self.log(f"    - Existing apps skipped  : {self.stats['m4_apps_skipped']}")
        self.log(f"    - EVC records to insert  : {self.stats['evc_inserted']} (skipped: {self.stats['evc_skipped']})")
        self.log(f"    - Undertakings to insert : {self.stats['obligations_inserted']} (skipped: {self.stats['obligations_skipped']}, blocked: {self.stats['obligations_blocked']})")
        self.log(f"    - Documents to insert    : {self.stats['documents_inserted']} (skipped: {self.stats['documents_skipped']})")
        self.log(f"    - Deadlines to insert    : {self.stats['deadlines_inserted']} (skipped: {self.stats['deadlines_skipped']})")
        self.log(f"    - Notifications to insert: {self.stats['notifications_inserted']} (skipped: {self.stats['notifications_skipped']})")
        self.log(f"    - Audit events to insert : {self.stats['audit_inserted']} (skipped: {self.stats['audit_skipped']})")
        self.log(f"=======================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Canonical Dataset Seeder for SIH Demo")
    parser.add_argument("--execute", action="store_true", help="Execute writes to SQLite databases (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry-run validation without database writes")
    args = parser.parse_args()

    # Dry-run by default unless explicitly --execute
    is_dry_run = not args.execute
    engine = SeederEngine(dry_run=is_dry_run)
    engine.run()
