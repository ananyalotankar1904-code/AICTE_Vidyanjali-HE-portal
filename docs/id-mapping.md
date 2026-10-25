# SIH26262 — Canonical Identifier & Entity Mapping Strategy

**Project:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Regulatory Compliance Management System  
**Phase:** Phase 1 — Prepare for Safe Integration  
**Date:** October 25, 2026  
**Auditor / Integration Engineer:** Senior Software Integration Engineer  

---

## 1. Overview & Strategy

The SIH26262 project has evolved with three parallel representation layers:
1. **Nine Excel Datasets (`data/seed/`)**: The definitive ground truth source for institution masters, initial applications, workflow rules, EVC visits, undertakings, and audit history.
2. **Member 3 & Member 4 Backends (`app/` & `backend/app/`)**: Operational database models. Member 3 strictly adheres to canonical dataset IDs (`APP001`, `INST001`), whereas Member 4 was developed with flexible UUID string IDs.
3. **Frontend Prototype Mock Store (`src/data/mockStore.ts`)**: High-fidelity UI mockups using realistic synthetic portal IDs (`AI-2026-1842`, `EVC-301`, `DOC-101`).

To ensure a seamless, non-destructive integration without breaking UI components or database relations, this document establishes the **Canonical Identifier Standard** and the bidirectional mapping rules.

---

## 2. Canonical Identifier Schemes

All persisted entities across the unified backend and database must follow these canonical formats:

| Entity Type | Canonical Prefix | ID Format | Example | Dataset Origin |
|---|---|---|---|---|
| **Institution** | `INST` | `INST` + 3 digits | `INST001` – `INST015` | Dataset 1 (Sheet 1) |
| **Application** | `APP` | `APP` + 3 digits (auto-increment `APP026+`) | `APP001` – `APP025` | Dataset 2 (Sheet 1) |
| **EVC Schedule** | `EVC` | `EVC` + 3 digits | `EVC001` – `EVC007` | Dataset 4 (Sheet 1) |
| **Undertaking** | `UND` | `UND-YYYY-` + 3 digits | `UND-2026-001` – `UND-2026-010` | Dataset 5 (Sheet 1) |
| **Document** | `DOC` | `DOC-YYYY-` + 4 digits | `DOC-2026-0001` – `DOC-2026-0014`| Dataset 6 (Sheet 1) |
| **Deadline** | `DDL` | `DDL-YYYY-` + 3 digits | `DDL-2026-001` – `DDL-2026-024` | Dataset 7 (Sheet 1) |
| **Notification** | `NOTIF` | `NOTIF-YYYY-` + 3 digits| `NOTIF-2026-001` – `NOTIF-2026-030`| Dataset 7 (Sheet 2) |
| **Audit Event** | `EVT` | `EVT-YYYY-` + 4 digits | `EVT-2026-0001` – `EVT-2026-0020`| Dataset 9 (Sheet 1) |
| **Role Code** | `ROLE_` | Standard uppercase enum | `ROLE_SCRUTINY`, `ROLE_AUTHORITY`| Dataset 8 (Sheet 1) |

---

## 3. Bidirectional Mapping: Frontend Mock IDs to Canonical Dataset IDs

When the frontend switches `USE_LOCAL_MOCK = false` or when mock data is seeded into the live database, this explicit mapping table governs entity translation:

### 3.1 Applications Master Mapping

| Frontend Mock ID | Mock Institution Name | Canonical ID | Dataset Institution ID | Application Type | Current Stage | Operational Status |
|---|---|---|---|---|---|---|
| `AI-2026-1842` | Pune Institute of Technology | **`APP001`** | `INST001` | Extension of Approval | `INITIAL_SCRUTINY` | `IN_PROGRESS` |
| `AI-2026-1826` | Sahyadri College of Engineering | **`APP002`** | `INST002` | Increase in Intake | `DEFICIENCY_RAISED` | `ACTION_REQUIRED` |
| `AI-2026-1794` | Chennai Technical University | **`APP003`** | `INST004` | New Programme | `EVC_SCHEDULED` | `IN_PROGRESS` |
| `AI-2026-1711` | Jyothi College of Applied Sciences | **`APP007`** | `INST007` | Extension of Approval | `EVC_COMPLETED` | `IN_PROGRESS` |
| `AI-2026-1763` | Malwa Institute of Technology | **`APP012`** | `INST003` | Increase in Intake | `EVC_SCHEDULED` | `IN_PROGRESS` |
| `AI-2026-1778` | Apex Institute of Design | **`APP014`** | `INST012` | New Programme | `EVC_COMPLETED` | `IN_PROGRESS` |
| `AI-2026-1801` | Gujarat Technological Academy | **`APP018`** | `INST005` | Extension of Approval | `COMMITTEE_REVIEW` | `IN_PROGRESS` |
| `AI-2026-1815` | National Engineering Institute | **`APP021`** | `INST009` | New Programme | `DECISION_PENDING` | `IN_PROGRESS` |
| `AI-2026-1690` | Vidya Vikas Institute of Technology | **`APP025`** | `INST015` | Closure of Course | `COMPLETED` | `COMPLETED (Rejected)` |

### 3.2 EVC Records Mapping

| Frontend Mock EVC ID | Linked App (Mock) | Canonical EVC ID | Canonical App ID | Planned Date | Inspection Mode | Lead Evaluator / Members |
|---|---|---|---|---|---|---|
| `EVC-301` | `AI-2026-1794` | **`EVC001`** | `APP003` | `2026-11-07` | On-site | Dr Meera Shah, Prof. S. Iyer |
| `EVC-302` | `AI-2026-1711` | **`EVC002`** | `APP007` | `2026-10-21` | Virtual | Dr A. Kulkarni, Prof. N. Bose |
| `EVC-303` | `AI-2026-1763` | **`EVC003`** | `APP012` | `2026-11-13` | On-site | Assignment pending / Dr V. Sharma |
| `EVC-304` | `AI-2026-1778` | **`EVC004`** | `APP014` | `2026-10-14` | Virtual | Dr M. Gupta, Prof. P. Rao |

### 3.3 Compliance Documents Mapping

| Frontend Mock Doc ID | Document Title | Canonical Doc ID | Linked Institution | Expiry Date | Status |
|---|---|---|---|---|---|
| `DOC-101` | Land ownership & 30-year lease deed | **`DOC-2026-0001`** | `INST001` | `2035-12-31` | Valid |
| `DOC-102` | State Fire Safety Clearance NOC | **`DOC-2026-0002`** | `INST001` | `2027-03-31` | Valid |
| `DOC-103` | Certified Faculty Cadre Roster | **`DOC-2026-0003`** | `INST002` | `2026-11-15` | Expiring soon |
| `DOC-104` | Barrier-Free & Ramp Accessibility Certificate | **`DOC-2026-0004`** | `INST002` | `2026-08-31` | Expired (Renewal Pending)|
| `DOC-105` | AICTE Biometric Attendance Affidavit | **`DOC-2026-0005`** | `INST004` | `2027-05-30` | Valid |

---

## 4. Cross-Module Foreign Key Consistency

In the unified data architecture, all compliance modules link back to the core application via `application_id`:

```
applications (PK: application_id, e.g. "APP001")
    ^
    |--- workflow_history (FK: application_id)
    |--- scrutiny_records (FK: application_id)
    |--- deficiency_records (FK: application_id)
    |--- decision_records (FK: application_id)
    |--- evc_records (FK: application_id -> applications.application_id)
    |--- compliance_obligations (FK: application_id -> applications.application_id)
    |--- documents (FK: application_id -> applications.application_id)
    |--- deadlines (polymorphic entity_type="APPLICATION", entity_id=application_id)
    |--- notifications (polymorphic entity_type="APPLICATION", entity_id=application_id)
    |--- audit_events (polymorphic entity_type="APPLICATION", entity_id=application_id)
```

### Foreign Key Fallback Policy:
1. **Independent Obligations:** Compliance obligations without an application reference have `application_id = NULL` and link strictly to `institution_id` (`INST001`–`INST015`).
2. **Polymorphic Entities:** `deadlines`, `notifications`, and `audit_events` store `entity_type` as a string (`APPLICATION`, `EVC`, `UNDERTAKING`, `DOCUMENT`) and `entity_id` as a string (e.g. `APP001`, `EVC001`, `DOC-2026-0001`), providing loose coupling without cascading constraint deadlocks.

---

## 5. UI Client Adapter Normalization Rules

In `src/api/client.ts`, the frontend adapter must implement normalization routines to handle canonical backend payloads transparently:

```typescript
// Example: Normalizing Backend Application to Frontend ApplicationRecord
function normalizeApplication(raw: any): ApplicationRecord {
  return {
    id: raw.application_id || raw.id,
    name: raw.institution_name || `Institution ${raw.institution_id}`,
    city: raw.city || 'Regional Center',
    type: raw.application_type,
    stage: mapStageNameToIndex(raw.current_stage),
    status: mapBackendStatusToFrontend(raw.application_status, raw.current_stage),
    owner: raw.assigned_role || 'Intake Officer',
    deadline: raw.due_date || '2026-11-15',
    age: computeAgeDays(raw.submitted_date),
    deficiency: raw.deficiency_flag === 'Yes' ? 'Deficiencies outstanding' : '',
    documents: [],
    assignedRoute: raw.route_id || 'Standard Route',
    submittedAt: raw.submitted_date,
    contactEmail: raw.contact_email,
    contactPhone: raw.contact_phone,
    intakeCapacity: raw.intake_approved,
  };
}

// Example: Normalizing Backend EVC to Frontend EvcRecord
function normalizeEvc(raw: any): EvcRecord {
  return {
    id: raw.id,
    app: raw.application_id,
    date: raw.planned_visit_date ? raw.planned_visit_date.split('T')[0] : '2026-11-15',
    mode: raw.venue_address?.includes('Virtual') ? 'Virtual' : 'On-site',
    members: Array.isArray(raw.assigned_members) ? raw.assigned_members.join(', ') : (raw.assigned_members || 'Pending'),
    status: raw.status === 'SCHEDULED' ? 'Scheduled' : raw.status === 'VISIT_COMPLETED' ? 'Completed' : 'Awaiting assignment',
    evidence: raw.report_document_id || 'Not uploaded',
  };
}
```

This normalization ensures that neither the React view components nor the backend business logic needs to be rewritten.
