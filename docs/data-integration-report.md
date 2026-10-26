# SIH26262 — Canonical Data Integration & Referential Validation Report

**Project:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Regulatory Compliance Management System  
**Phase:** Phase 2C — Canonical Data Integration & Workflow Validation  
**Date:** October 26, 2026  
**Integration Status:** Ground Truth Data Audit & Schema Mapping Complete  
**Database Architecture:** Preserved Separate Database Engines (`aicte_platform.db` and `aicte.db`)

---

## 1. Executive Summary & Purpose

This report delivers a comprehensive audit of all nine canonical datasets located in `data/seed/` and establishes the definitive referential integration plan across both operational SQLite databases:
- **`aicte_platform.db` (Member 3 Workflow Core):** 31 existing applications (`APP001`–`APP031`), 38 workflow history rows, 1 scrutiny record (`APP028`), 0 deficiency/decision records.
- **`aicte.db` (Member 4 Compliance Core):** 0 applications, 467 audit events, 19 notifications, 0 deadlines, 0 EVC records, 0 compliance obligations, 0 documents.

Before performing any database seeding, timestamped backups were created on October 26, 2026 under `data/backups/20261026_114434/`:
- `data/backups/20261026_114434/aicte_platform.db` (77,824 bytes)
- `data/backups/20261026_114434/aicte.db` (454,656 bytes)

All existing records, including live integration records `APP029`, `APP030`, and `APP031` created during Phase 2B end-to-end testing, are preserved.

---

## 2. Source File & Dataset Inventory

Every dataset file was programmatically audited down to the XML sheet structure. The exact inventory, sheet targets, and row counts are detailed below:

| Dataset File | Primary Sheets Audited | Header Row (1-indexed) | Non-Empty Data Rows | Key Entity Identifier | Canonical Range |
|---|---|---|---|---|---|
| **1. `dataset_1_institutions.xlsx`** | `Selected_Institutions` | Row 1 | 15 | `Institution_ID_Mapping` | `INST001` – `INST015` |
| **2. `dataset_2_applications.xlsx`** | `Applications` | Row 1 | 25 | `application_id` | `APP001` – `APP025` |
| **3. `dataset_3_workflow_stages.xlsx`** | `Stage_Definitions`<br>`Transition_Rules`<br>`Application_Routes`<br>`Role_Permissions` | Row 1<br>Row 1<br>Row 1<br>Row 1 | 15<br>24<br>4<br>11 | `Stage_Code`<br>`Rule_ID`<br>`Route_Code`<br>`Role_Code` | `STG_01`–`STG_15`<br>`TR_001`–`TR_024`<br>`RT_01`–`RT_04`<br>`ROL_01`–`ROL_11` |
| **4. `dataset_4_evc_schedules.xlsx`** | `EVC_Records` | Row 1 | 7 | `evc_id` | `EVC001` – `EVC007` |
| **5. `dataset_5_undertakings.xlsx`** | `Undertakings` | Row 1 | 10 | `undertaking_id` | `UND-2026-001` – `UND-2026-010` |
| **6. `dataset_6_documents.xlsx`** | `Documents` | Row 1 | 14 | `document_id` | `DOC-2026-0001` – `DOC-2026-0014` |
| **7. `dataset_7_deadlines_notifications.xlsx`** | `Deadlines`<br>`Notifications` | Row 1<br>Row 1 | 24<br>30 | `deadline_id`<br>`notification_id` | `DDL-2026-001` – `DDL-2026-024`<br>`NOTIF-2026-001` – `NOTIF-2026-030` |
| **8. `dataset_8_roles_permissions.xlsx`** | `Roles`<br>`Permissions`<br>`Demo_Users` | Row 1<br>Row 1<br>Row 1 | 8<br>38<br>8 | `role_id`<br>`permission_id`<br>`user_id` | `ROLE_*`<br>`PERM_001` – `PERM_038`<br>`USR_DEMO_001` – `USR_DEMO_008` |
| **9. `dataset_9_audit_events.xlsx`** | `Audit_Events` | **Row 6** *(Critical! Rows 1–5 are banner cards)* | 20 | `audit_event_id` | `EVT-2026-0001` – `EVT-2026-0020` |

### Critical Layout Nuances Discovered
1. **Dataset 9 Header Offset:** Rows 1–5 contain formatted summary KPI scorecards (`TOTAL AUDIT EVENTS: 20`, `UNIQUE APPLICATIONS: 11`, etc.). The actual programmatic header row is strictly at **Row 6**. Data records span **Row 7 to Row 26**.
2. **Dataset 7 Sparse Trailing Cells:** Sheets `'Deadlines'` and `'Notifications'` have 100 row elements pre-allocated in Excel, but non-empty data strictly terminates at row 25 (24 records) and row 31 (30 records). Parsers must check for `row[0] is not None`.
3. **Date Formats (Excel Serial Floats):** Dates across all workbooks are stored as floating point serial days relative to `1899-12-30` (e.g., `46319.0` represents `2026-10-24`, `46320.0` represents benchmark date `2026-10-25`). Conversion formula:
   $$\text{datetime}(1899, 12, 30) + \text{timedelta}(\text{days}=\text{val})$$

---

## 3. Canonical Identifier Conventions & Lineage

The canonical format standards established in `docs/id-mapping.md` remain the definitive ground truth:

```
[INSTITUTION] INST001 - INST015 (Dataset 1)
      |
      +---> [APPLICATION] APP001 - APP025 (Dataset 2)
                 |
                 +---> [EVC RECORD] EVC001 - EVC007 (Dataset 4)
                 +---> [UNDERTAKING] UND-2026-001 - UND-2026-010 (Dataset 5)
                 +---> [DOCUMENT] DOC-2026-0001 - DOC-2026-0014 (Dataset 6)
                 +---> [DEADLINE] DDL-2026-001 - DDL-2026-024 (Dataset 7)
                 +---> [NOTIFICATION] NOTIF-2026-001 - NOTIF-2026-030 (Dataset 7)
                 +---> [AUDIT EVENT] EVT-2026-0001 - EVT-2026-0020 (Dataset 9)
```

---

## 4. Cross-Dataset Referential Integrity & Conflict Audit

### 4.1 Master Entity Coverage
- **Institutions (`INST001`–`INST015`):** All 15 institutions in Dataset 1 are fully referenced by Dataset 2 applications.
- **Applications (`APP001`–`APP025`):** All 25 applications reference verified institutions `INST001`–`INST015`.

### 4.2 Conflicting and Orphaned Records (Dataset 5 Audit)
An exhaustive scan of `dataset_5_undertakings.xlsx` revealed **two legacy foreign key conflicts**:
1. **`UND-2026-003`:**
   - Source Data: `application_id = 'APP-2026-1024'`, `institution_id = '1-109283724'`.
   - Conflict: `1-109283724` does not exist in Dataset 1 (`INST001`–`INST015`). `APP-2026-1024` does not exist in Dataset 2 (`APP001`–`APP025`). (In Dataset 2, `APP024` maps to `INST009`).
   - Source annotation: *"FLAGGED FK CONFLICT: 1-109283724 has no master match in Dataset 1 (INST001-INST015)... Preserved original IDs and overdue scenario without guessing."*
2. **`UND-2026-006`:**
   - Source Data: `application_id = 'APP-2026-1019'`, `institution_id = '1-109283719'`.
   - Conflict: `1-109283719` does not exist in Dataset 1. `APP-2026-1019` does not exist in Dataset 2. (In Dataset 2, `APP019` maps to `INST004`).
   - Source annotation: *"FLAGGED FK CONFLICT: 1-109283719 has no master match in Dataset 1 (INST001-INST015)... Preserved original IDs and correction scenario without guessing."*

**Resolution Policy:**
Per project instructions (*"If a dataset cannot be safely mapped, leave it unloaded and document the blocker... Validate all foreign-key relationships before committing data"*):
- Records `UND-2026-001`, `002`, `004`, `005`, `007`, `008`, `009`, `010` (8 valid records) map cleanly to canonical applications and will be seeded into `compliance_obligations`.
- Records `UND-2026-003` and `UND-2026-006` **MUST NOT be forced into the database** with invented foreign keys. They are skipped during seeder execution and logged as unmapped legacy edge cases.

### 4.3 Version Lineage Checks (Dataset 6 Audit)
Dataset 6 contains 3 document version predecessor chains:
1. `DOC-2026-0002` (v2) supersedes `DOC-2026-0001` (v1)
2. `DOC-2026-0005` (v2) supersedes `DOC-2026-0004` (v1)
3. `DOC-2026-0007` (v2) supersedes `DOC-2026-0006` (v1)

**Resolution Policy:**
Seeding must occur in topological sequence: Version 1 records (`DOC-0001`, `DOC-0004`, `DOC-0006`) must be committed before Version 2 records so that `previous_version_id` foreign keys resolve without constraint violations.

---

## 5. Schema & Model Mapping Across Backends

### 5.1 Member 3 (`aicte_platform.db`) Mapping
Member 3's `applications` table stores canonical strings:
- `application_id` = `APP001` – `APP025`
- `institution_id` = `INST001` – `INST015`
- `application_type` = `Extension of Approval` | `New Programme` | `Increase in Intake`
- `current_stage` = Canonical stage string (`DRAFT`, `SUBMITTED`, `INITIAL_VALIDATION`, etc.)
- `application_status` = Canonical status string (`DRAFT`, `IN_PROGRESS`, `ACTION_REQUIRED`, etc.)
- `submitted_date`, `stage_entered_date`, `due_date`, `last_updated` = ISO `YYYY-MM-DD`
- `data_type` = `SYNTHETIC_DEMO`

*Current database state:* `APP001`–`APP025` already exist from prior initial seeds. Seeding will perform an **idempotent update check**: if the record exists, verify integrity and preserve user-modified attributes; do not create duplicate rows or overwrite runtime tests.

### 5.2 Member 4 (`aicte.db`) Mapping

Member 4's models use explicit SQLAlchemy models with foreign key constraints. Here is the exact field-by-field translation:

#### A. Applications (`Application` in `backend/app/models/application.py`)
Because `evc_records`, `compliance_obligations`, and `documents` have `ForeignKey("applications.id")`, canonical applications `APP001`–`APP025` must be present in Member 4's database to satisfy relational integrity!

| Dataset 2 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `application_id` | `id` | `String(36)` | Use canonical ID directly: `"APP001"` (fits within 36 chars) |
| `application_id` | `application_number` | `String(50)` | `"APP001"` |
| `institution_id` | `institution_id` | `String(50)` | `"INST001"` – `"INST015"` |
| *(Dataset 1 lookup)* | `institution_name` | `String(200)` | Official registered name from Dataset 1 (e.g. "Aishabai College of Education") |
| `application_type` | `application_type` | `String(100)` | `"Extension of Approval"` / `"New Programme"` / `"Increase in Intake"` |
| *(Derived Route)* | `route_id` | `String(100)` | `"ROUTE_EOA_STD"` / `"ROUTE_NEW_INST"` / `"ROUTE_INC_INTAKE"` |
| `application_status` | `status` | `SQLEnum(ApplicationStatus)` | `DRAFT`, `SUBMITTED`, `IN_PROGRESS`, `ACTION_REQUIRED`, `COMPLETED`, `REJECTED` |
| `current_stage` | `current_stage` | `SQLEnum(WorkflowStage)` | Maps Dataset 3 stage code to Member 4 enum: `INITIAL_VALIDATION` -> `VALIDATION`, `INITIAL_SCRUTINY` -> `SCRUTINY`, `DEFICIENCY_RAISED` -> `DEFICIENCY_PENDING`, `EVC_COMPLETED` -> `EVC_REPORT_REVIEW`, `REJECTED` -> `COMPLETED`. |
| `submitted_date` | `submitted_at` | `DateTime` | Converted ISO datetime (UTC) |
| `stage_entered_date`| `created_at` | `DateTime` | Converted ISO datetime (UTC) |
| `last_updated` | `updated_at` | `DateTime` | Converted ISO datetime (UTC) |

#### B. EVC Schedules (`EVCRecord` in `backend/app/models/evc.py`)

| Dataset 4 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `evc_id` | `id` | `String(36)` | `"EVC001"` – `"EVC007"` |
| `application_id` | `application_id` | `String(36)` | FK -> `applications.id` (`"APP013"`, etc.) |
| `evc_status` | `status` | `SQLEnum(EVCStatus)` | `PROPOSED` -> `PENDING_SCHEDULING`, `SCHEDULED` / `RESCHEDULED` -> `SCHEDULED`, `VISIT_COMPLETED` -> `VISIT_COMPLETED`, `REPORT_SUBMITTED` / `REPORT_UNDER_REVIEW` -> `REPORT_SUBMITTED`, `REPORT_REVIEWED` -> `REPORT_REVIEWED` |
| `evc_team_id` | `assigned_team_id` | `String(100)` | `"TEAM_A"`, `"TEAM_B"`, `"TEAM_C"` |
| `scheduled_date` | `planned_visit_date` | `DateTime` | Converted ISO datetime |
| `rescheduled_from_date`| `reschedule_history` | `JSON` | If rescheduled: `[{"previous_date": "...", "reason": reschedule_reason}]` |
| `report_status` | `report_review_outcome`| `SQLEnum(...)` | `Reviewed` -> `ACCEPTED`, else `None` |
| `demo_notes` | `scheduling_notes` | `Text` | Preserved audit note |

#### C. Undertakings (`ComplianceObligation` in `backend/app/models/compliance.py`)

| Dataset 5 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `undertaking_id` | `id` | `String(36)` | `"UND-2026-001"`, etc. |
| `application_id` | `application_id` | `String(36)` | FK -> `applications.id` (8 valid records) |
| `institution_id` | `institution_id` | `String(50)` | `"INST001"` – `"INST015"` |
| `obligation_type` | `obligation_type` | `String(100)` | `"AFFIDAVIT_SUBMISSION"`, etc. |
| `obligation_description`| `description` | `Text` | Obligation description |
| `source_reference` | `source_reference` | `String(200)` | Preserved reference (e.g. `"UNVERIFIED — DEMO CONFIGURATION"`) |
| `is_demo_rule` | `is_illustrative_demo_rule`| `Boolean` | `True` |
| `due_date` | `due_date` | `DateTime` | Converted ISO datetime |
| `assigned_role` | `responsible_owner` | `String(100)` | `"ROLE_INSTITUTION_ADMIN"`, etc. |
| `undertaking_status` | `status` | `SQLEnum(ObligationStatus)` | `AWAITING_SUBMISSION`/`DUE_SOON`/`OVERDUE` -> `PENDING`, `SUBMITTED`/`AWAITING_VERIFICATION` -> `SUBMITTED`, `CORRECTION_REQUESTED` -> `NEEDS_CORRECTION`, `VERIFIED`/`COMPLETED` -> `VERIFIED` |
| `evidence_document_id`| `evidence_document_id` | `String(100)` | `"DOC-2026-8812"`, etc. |

#### D. Documents (`Document` in `backend/app/models/document.py`)

| Dataset 6 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `document_id` | `id` | `String(36)` | `"DOC-2026-0001"` – `"DOC-2026-0014"` |
| `application_id` | `application_id` | `String(36)` | FK -> `applications.id` |
| `institution_id` | `institution_id` | `String(50)` | `"INST001"` – `"INST015"` |
| `document_type` | `document_type` | `String(100)` | E.g., `"Land Lease Deed"`, `"Fire Safety Certificate"` |
| `document_description`| `title` | `String(200)` | Document description / title |
| `storage_reference` | `storage_path` | `String(500)` | Preserved synthetic S3 URI |
| `document_version` | `version` | `Integer` | `1` or `2` |
| `previous_version_document_id`| `previous_version_id`| `String(36)` | Self-referencing FK (`DOC-2026-0001`, etc.) or `None` |
| `issue_date` | `issue_date` | `DateTime` | Converted ISO datetime |
| `expiry_date` | `expiry_date` | `DateTime` | Converted ISO datetime or `None` (for perpetual) |
| `document_status` | `review_status` | `SQLEnum(DocumentReviewStatus)`| `VALID`/`SUPERSEDED` -> `VERIFIED`, `EXPIRED`/`DEFICIENCY_FLAGGED` -> `NEEDS_REPLACEMENT`, `REJECTED` -> `REJECTED`, `SUBMITTED`/`UNDER_REVIEW` -> `PENDING_REVIEW` |
| `reviewed_by` | `reviewed_by` | `String(100)` | Reviewer role string |

#### E. Deadlines (`DeadlineRecord` in `backend/app/models/deadline.py`)

| Dataset 7 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `deadline_id` | `id` | `String(36)` | `"DDL-2026-001"` – `"DDL-2026-024"` |
| `related_entity_type` | `entity_type` | `String(50)` | `"UNDERTAKING"`, `"APPLICATION"`, etc. |
| `related_entity_id` | `entity_id` | `String(100)` | `"UND-2026-010"`, `"APP001"`, etc. |
| `deadline_category` | `deadline_type` | `String(100)` | `"EVC_READINESS"`, `"DEFICIENCY_RECTIFICATION"`, etc. |
| `deadline_description`| `title` | `String(200)` | Human-readable title |
| `due_date` | `due_date` | `DateTime` | Converted ISO datetime |
| `assigned_role` | `owner_role` | `String(50)` | `"ROLE_EVC_EXPERT"`, `"ROLE_INSTITUTION_ADMIN"`, etc. |
| `deadline_status` | `status` | `SQLEnum(DeadlineStatus)` | `UPCOMING`/`DUE`/`ESCALATED` -> `ACTIVE`, `OVERDUE` -> `OVERDUE`, `COMPLETED` -> `COMPLETED`, `CANCELLED` -> `CANCELLED` |
| `is_demo_rule` | `is_statutory` | `Boolean` | Inverted `not is_demo_rule` (statutory = not demo) |
| `escalation_policy` | `escalation_policy` | `String(100)` | `"ALERT_ONLY_LEVEL_1"`, etc. |

#### F. Notifications (`Notification` in `backend/app/models/notification.py`)

| Dataset 7 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `notification_id` | `id` | `String(36)` | `"NOTIF-2026-001"` – `"NOTIF-2026-030"` |
| `recipient_role` | `recipient_role` | `String(50)` | E.g. `"ROLE_EVC_EXPERT"` |
| `notification_title`| `title` | `String(200)` | Title |
| `message_body` | `message` | `Text` | Message text |
| `trigger_reason` | `notification_type` | `SQLEnum(NotificationType)` | Mapped: `SLA_WARNING`/`SLA_EXPIRING` -> `DEADLINE_UPCOMING`, `DEFICIENCY_FLAGGED` -> `OBLIGATION_ACTION_REQUIRED`, etc. |
| `application_id` | `entity_id` | `String(100)` | Target entity ID (`"APP001"`, etc.) |
| `deduplication_key` | `deduplication_key` | `String(255)` | Unique deduplication key from dataset |
| `read_status` | `is_read` | `Boolean` | `True` if `READ` else `False` |

#### G. Audit Events (`AuditEvent` in `backend/app/models/audit.py`)

| Dataset 9 Column | Member 4 Model Field | Data Type | Value / Normalization |
|---|---|---|---|
| `audit_event_id` | `id` | `String(36)` | `"EVT-2026-0001"` – `"EVT-2026-0020"` |
| `actor_user_id` | `actor_id` | `String(100)` | `"USR_DEMO_001"`, etc. |
| `actor_role` | `actor_role` | `String(50)` | `"ROLE_INST_APPLICANT"`, etc. |
| `action_code` | `action` | `String(100)` | `"SUBMIT_APPLICATION"`, `"FLAG_DEFICIENCIES"`, etc. |
| `entity_type` | `entity_type` | `String(50)` | `"APPLICATION"`, `"DOCUMENT"`, etc. |
| `entity_id` | `entity_id` | `String(100)` | Canonical entity ID |
| `timestamp` | `timestamp` | `DateTime` | Converted ISO datetime |
| `reason_or_comment`| `reason` | `String(500)` | Context comment |
| *(Metadata)* | `details` | `JSON` | `{"is_synthetic_demo_event": true, "event_source": row.event_source, "demo_notes": row.demo_notes}` |

*Critical Governance Mandate:* Every seeded audit event has `details["is_synthetic_demo_event"] = True`. Never fabricate genuine official statutory determinations.

---

## 6. Controlled Loading Order & Rollback Plan

### 6.1 Loading Order Dependencies

To satisfy all relational foreign keys within each database independently, data must be seeded in the following sequence:

```
Stage 1: Institutions Master (Dataset 1)
         Extract official institution directory {INST001..INST015 -> Name, City, State}.

Stage 2: Applications Master (Dataset 2)
         a. In aicte_platform.db: Upsert applications APP001..APP025 (preserve live APP029..APP031).
         b. In aicte.db: Seed applications APP001..APP025 with institution details.

Stage 3: Dependent Compliance Entities (Datasets 4, 5, 6, 7)
         a. Seed EVC Records (Dataset 4, EVC001..EVC007) -> FK to applications.
         b. Seed Compliance Obligations (Dataset 5, 8 valid records) -> FK to applications.
         c. Seed Documents (Dataset 6, DOC-0001..DOC-0014) in topological order (v1 before v2) -> FK to applications.
         d. Seed Deadlines (Dataset 7, DDL-001..DDL-024) -> polymorphic entity references.

Stage 4: Notifications & Audit Events (Datasets 7 & 9)
         a. Seed Notifications (Dataset 7, NOTIF-001..NOTIF-030) with deduplication keys.
         b. Seed Synthetic Audit Events (Dataset 9, EVT-0001..EVT-0020) with explicit synthetic demo metadata.

Stage 5: Role & Permission Validation (Dataset 8)
         Verify authorization rules against existing server-side RBAC dependencies.
```

### 6.2 Rollback Procedure
If any stage detects an unresolvable reference or transaction failure:
1. Roll back the active transaction within the affected database.
2. If disk recovery is required, restore directly from the pristine timestamped backups:
   - `data/backups/20261026_114434/aicte_platform.db`
   - `data/backups/20261026_114434/aicte.db`
3. Never use Git to force-checkout database files while processes hold open handles.

---

## 7. Fields That Cannot Safely Be Mapped (Blockers)

1. **`UND-2026-003` & `UND-2026-006`:** Refer to unmapped institutions `1-109283724` and `1-109283719`. Blocked from database insertion to prevent foreign key violations.
2. **`obligation_id` in `documents`:** Dataset 6 does not cross-reference undertaking IDs; `documents.obligation_id` will be safely set to `NULL`.
3. **`decided_at` and Official Decisions:** Datasets contain zero automated statutory approval/rejection orders. Per AICTE Act 1987, decision records are created strictly through human execution by `ROLE_COMPETENT_AUTH`.
