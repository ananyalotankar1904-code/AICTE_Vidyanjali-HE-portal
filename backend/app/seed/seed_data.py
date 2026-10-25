"""Repeatable synthetic demo seed data generator for compliance modules."""
from datetime import datetime, timezone, timedelta
from backend.app.db import SessionLocal, init_db
from backend.app.models.application import Application
from backend.app.models.evc import EVCRecord
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import Document
from backend.app.models.deadline import DeadlineRecord
from backend.app.models.notification import Notification
from backend.app.models.audit import AuditEvent
from backend.app.enums import (
    ApplicationStatus,
    WorkflowStage,
    EVCStatus,
    EVCRecommendation,
    ObligationStatus,
    DocumentReviewStatus,
    DeadlineStatus,
    NotificationType,
    EntityType,
    UserRole
)


def seed_compliance_data():
    init_db()
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    # 1. Seed Synthetic Applications
    app1 = db.query(Application).filter(Application.application_number == "APP-2026-101").first()
    if not app1:
        app1 = Application(
            id="app-synthetic-101",
            application_number="APP-2026-101",
            institution_id="INST-MUMBAI-01",
            institution_name="National Institute of Engineering & Technology (Demo)",
            application_type="EXTENSION_OF_APPROVAL",
            route_id="ROUTE_FULL_SCRUTINY_EVC",
            status=ApplicationStatus.IN_PROGRESS,
            current_stage=WorkflowStage.EVC_IN_PROGRESS,
            assigned_to="SCRUTINY_OFFICER_1",
            description="Annual Extension of Approval application for AY 2026-27"
        )
        db.add(app1)

    app2 = db.query(Application).filter(Application.application_number == "APP-2026-102").first()
    if not app2:
        app2 = Application(
            id="app-synthetic-102",
            application_number="APP-2026-102",
            institution_id="INST-PUNE-02",
            institution_name="Apex College of Pharmaceutical Sciences (Demo)",
            application_type="NEW_COURSE",
            route_id="ROUTE_FULL_SCRUTINY_EVC",
            status=ApplicationStatus.ACTION_REQUIRED,
            current_stage=WorkflowStage.SCRUTINY,
            assigned_to="SCRUTINY_OFFICER_2",
            description="New postgraduate program introduction application"
        )
        db.add(app2)

    db.commit()

    # 2. Seed EVC Records
    evc1 = db.query(EVCRecord).filter(EVCRecord.id == "evc-synthetic-001").first()
    if not evc1:
        evc1 = EVCRecord(
            id="evc-synthetic-001",
            application_id="app-synthetic-101",
            status=EVCStatus.SCHEDULED,
            assigned_team_id="EVC_TEAM_WEST_04",
            assigned_members=["Prof. R. K. Sharma (Convener)", "Dr. Anita Desai (Member)"],
            planned_visit_date=now + timedelta(days=3),
            venue_address="Sector 4, Institutional Area, Navi Mumbai, Maharashtra",
            scheduling_notes="Scheduled after successful technical document scrutiny",
            reschedule_history=[
                {
                    "previous_date": (now + timedelta(days=1)).isoformat(),
                    "new_date": (now + timedelta(days=3)).isoformat(),
                    "reason": "Request by convener due to university exam schedule",
                    "rescheduled_by": "OFFICER_1",
                    "rescheduled_at": (now - timedelta(days=1)).isoformat()
                }
            ]
        )
        db.add(evc1)

    evc2 = db.query(EVCRecord).filter(EVCRecord.id == "evc-synthetic-002").first()
    if not evc2:
        evc2 = EVCRecord(
            id="evc-synthetic-002",
            application_id="app-synthetic-102",
            status=EVCStatus.PENDING_SCHEDULING,
            assigned_team_id="EVC_TEAM_PUNE_01",
            assigned_members=["Dr. M. K. Patil (Expert)"],
            scheduling_notes="Awaiting member confirmation"
        )
        db.add(evc2)

    evc3 = db.query(EVCRecord).filter(EVCRecord.id == "evc-synthetic-003").first()
    if not evc3:
        evc3 = EVCRecord(
            id="evc-synthetic-003",
            application_id="app-synthetic-101",
            status=EVCStatus.REPORT_SUBMITTED,
            assigned_team_id="EVC_TEAM_WEST_02",
            assigned_members=["Prof. A. S. Mehta"],
            planned_visit_date=now - timedelta(days=5),
            actual_visit_date=now - timedelta(days=5),
            visit_notes="Campus physical infrastructure and labs inspected.",
            findings_summary="Computer laboratory meets sanctioned intake norms. Fire safety renewal submitted.",
            recommendation=EVCRecommendation.RECOMMENDED,
            report_submitted_at=now - timedelta(days=2),
            report_submitted_by="Prof. A. S. Mehta"
        )
        db.add(evc3)

    db.commit()

    # 3. Seed Compliance Obligations
    ob1 = db.query(ComplianceObligation).filter(ComplianceObligation.id == "ob-synthetic-001").first()
    if not ob1:
        ob1 = ComplianceObligation(
            id="ob-synthetic-001",
            application_id="app-synthetic-101",
            institution_id="INST-MUMBAI-01",
            title="Faculty Cadre Ratio Compliance Undertaking",
            obligation_type="FACULTY_CADRE_RATIO",
            description="Undertaking to maintain 1:15 faculty-to-student ratio with designated Professor cadres.",
            source_reference="APH 2024-2027 Section 4.3 (Norms for Faculty)",
            is_illustrative_demo_rule=False,
            due_date=now + timedelta(days=14),
            responsible_owner="Principal / Registrar",
            status=ObligationStatus.SUBMITTED,
            evidence_document_id="doc-synthetic-001",
            submitted_at=now - timedelta(days=1),
            submitted_by="INST-MUMBAI-01",
            submission_notes="Attached signed affidavit by board of trustees."
        )
        db.add(ob1)

    ob2 = db.query(ComplianceObligation).filter(ComplianceObligation.id == "ob-synthetic-002").first()
    if not ob2:
        ob2 = ComplianceObligation(
            id="ob-synthetic-002",
            application_id="app-synthetic-102",
            institution_id="INST-PUNE-02",
            title="Anti-Ragging Committee Statutory Affidavit",
            obligation_type="ANTI_RAGGING_COMMITTEE",
            description="Submission of mandatory anti-ragging squad details and helpline banners.",
            source_reference="AICTE Anti-Ragging Regulations 2009",
            is_illustrative_demo_rule=False,
            due_date=now - timedelta(days=2),  # Past due for demonstration
            responsible_owner="Dean of Student Affairs",
            status=ObligationStatus.PENDING
        )
        db.add(ob2)

    db.commit()

    # 4. Seed Documents with Versioning & Expiry
    doc1_v1 = db.query(Document).filter(Document.id == "doc-synthetic-001-v1").first()
    if not doc1_v1:
        doc1_v1 = Document(
            id="doc-synthetic-001-v1",
            institution_id="INST-MUMBAI-01",
            application_id="app-synthetic-101",
            obligation_id="ob-synthetic-001",
            document_type="FIRE_SAFETY_CERTIFICATE",
            title="Municipal Fire Safety NOC (2025)",
            file_name="fire_safety_noc_2025.pdf",
            storage_path="/vault/docs/INST-MUMBAI-01/fire_noc_2025.pdf",
            file_size_bytes=1048576,
            version=1,
            is_latest=False,  # Superseded by v2!
            issue_date=now - timedelta(days=365),
            expiry_date=now - timedelta(days=10),  # Expired
            is_expiry_tracked=True,
            review_status=DocumentReviewStatus.VERIFIED,
            created_by="INST-MUMBAI-01"
        )
        db.add(doc1_v1)
        db.commit()

    doc1_v2 = db.query(Document).filter(Document.id == "doc-synthetic-001-v2").first()
    if not doc1_v2:
        doc1_v2 = Document(
            id="doc-synthetic-001-v2",
            institution_id="INST-MUMBAI-01",
            application_id="app-synthetic-101",
            obligation_id="ob-synthetic-001",
            document_type="FIRE_SAFETY_CERTIFICATE",
            title="Municipal Fire Safety NOC (Renewed 2026-2027)",
            file_name="fire_safety_noc_2026_renewed.pdf",
            storage_path="/vault/docs/INST-MUMBAI-01/fire_noc_2026_renewed.pdf",
            file_size_bytes=1224500,
            version=2,
            is_latest=True,
            previous_version_id="doc-synthetic-001-v1",
            issue_date=now - timedelta(days=5),
            expiry_date=now + timedelta(days=360),  # Valid
            is_expiry_tracked=True,
            review_status=DocumentReviewStatus.PENDING_REVIEW,
            created_by="INST-MUMBAI-01"
        )
        db.add(doc1_v2)

    doc2 = db.query(Document).filter(Document.id == "doc-synthetic-002").first()
    if not doc2:
        doc2 = Document(
            id="doc-synthetic-002",
            institution_id="INST-PUNE-02",
            application_id="app-synthetic-102",
            document_type="BUILDING_OCCUPANCY_CERTIFICATE",
            title="Structural Stability & Occupancy Certificate",
            file_name="occupancy_certificate.pdf",
            storage_path="/vault/docs/INST-PUNE-02/occupancy_certificate.pdf",
            file_size_bytes=2415000,
            version=1,
            is_latest=True,
            issue_date=now - timedelta(days=300),
            expiry_date=now + timedelta(days=12),  # Approaching expiry within 30 days!
            is_expiry_tracked=True,
            review_status=DocumentReviewStatus.VERIFIED,
            created_by="INST-PUNE-02"
        )
        db.add(doc2)

    db.commit()

    # 5. Seed Deadlines
    dl1 = db.query(DeadlineRecord).filter(DeadlineRecord.id == "dl-synthetic-001").first()
    if not dl1:
        dl1 = DeadlineRecord(
            id="dl-synthetic-001",
            entity_type=EntityType.UNDERTAKING.value,
            entity_id="ob-synthetic-002",
            deadline_type="COMPLIANCE_SUBMISSION_DEADLINE",
            title="Anti-Ragging Affidavit Submission Deadline",
            due_date=now - timedelta(days=2),  # Overdue
            owner_role=UserRole.APPLICANT.value,
            owner_id="INST-PUNE-02",
            source_reference="AICTE Mandatory Disclosure Policy",
            is_statutory=True,
            status=DeadlineStatus.OVERDUE,
            warning_threshold_hours=48,
            escalation_policy="NOTIFY_REGIONAL_OFFICER_ON_OVERDUE",
            escalation_triggered=True,
            escalation_history=[
                {
                    "timestamp": (now - timedelta(days=1)).isoformat(),
                    "event_type": "OVERDUE_ESCALATION",
                    "escalated_to_role": UserRole.REGIONAL_OFFICER.value,
                    "reason": "Submission overdue by 24h"
                }
            ]
        )
        db.add(dl1)

    dl2 = db.query(DeadlineRecord).filter(DeadlineRecord.id == "dl-synthetic-002").first()
    if not dl2:
        dl2 = DeadlineRecord(
            id="dl-synthetic-002",
            entity_type=EntityType.EVC.value,
            entity_id="evc-synthetic-001",
            deadline_type="EVC_REPORT_SUBMISSION_DEADLINE",
            title="EVC Report Submission Window",
            due_date=now + timedelta(hours=36),  # Upcoming within 48h!
            owner_role=UserRole.EVC_TEAM.value,
            owner_id="EVC_TEAM_WEST_04",
            source_reference="APH 2024-2027 Inspection Guidelines",
            is_statutory=False,
            status=DeadlineStatus.ACTIVE,
            warning_threshold_hours=48
        )
        db.add(dl2)

    db.commit()

    # 6. Seed In-App Notifications
    notif1 = db.query(Notification).filter(Notification.deduplication_key == "seed:notif:001").first()
    if notif1 is None:
        notif1 = Notification(
            id="notif-synthetic-001",
            recipient_role=UserRole.REGIONAL_OFFICER.value,
            notification_type=NotificationType.ESCALATION_ALERT,
            entity_type=EntityType.UNDERTAKING.value,
            entity_id="ob-synthetic-002",
            title="ESCALATION: Overdue Compliance Undertaking",
            message="Institution INST-PUNE-02 has exceeded the submission deadline for Anti-Ragging Committee Statutory Affidavit.",
            deduplication_key="seed:notif:001",
            is_read=False
        )
        db.add(notif1)

    notif2 = db.query(Notification).filter(Notification.deduplication_key == "seed:notif:002").first()
    if notif2 is None:
        notif2 = Notification(
            id="notif-synthetic-002",
            recipient_role=UserRole.EVC_TEAM.value,
            recipient_id="EVC_TEAM_WEST_04",
            notification_type=NotificationType.DEADLINE_UPCOMING,
            entity_type=EntityType.EVC.value,
            entity_id="evc-synthetic-001",
            title="Upcoming Deadline: EVC Report Submission",
            message="Reminder: EVC Report Submission Window is due in 36 hours.",
            deduplication_key="seed:notif:002",
            is_read=False
        )
        db.add(notif2)

    db.commit()

    # 7. Seed Initial Audit Events
    audit_count = db.query(AuditEvent).count()
    if audit_count == 0:
        db.add(AuditEvent(
            actor_id="SYSTEM",
            actor_role=UserRole.SYSTEM.value,
            action="INITIALIZE_SEED_DATA",
            entity_type=EntityType.APPLICATION.value,
            entity_id="ALL",
            reason="Populated reproducible synthetic demonstration records"
        ))
        db.commit()

    db.close()
    print("Synthetic compliance seed data populated successfully.")


if __name__ == "__main__":
    seed_compliance_data()
