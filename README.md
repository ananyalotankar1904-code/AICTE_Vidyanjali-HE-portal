# AICTE Approval & Compliance Platform — Backend Workflow Module

**Author / Role**: Member 3 — Backend Workflow Developer  
**Technology Stack**: Python 3.13, FastAPI, SQLite, SQLAlchemy 2.0, Pydantic v2, pytest

---

## 1. Module Overview

This module implements the core workflow state machine and application management engine for the AICTE Approval & Compliance Platform. It manages the complete lifecycle of institutional applications through scrutiny, deficiency resubmissions, expert inspections (EVC), committee evaluations, and authorized decision recording.

### Ground Truth Coordination
- **Data Contract**: Strictly coordinates with `Dataset_2_Synthetic_Applications_25.xlsx` (Sheet 2 schema, Sheet 1 records `APP001`–`APP025`).
- **Separation of State**:
  - `current_stage`: Pipeline phase (`SUBMITTED`, `INITIAL_SCRUTINY`, `DEFICIENCY_RAISED`, `RE_SCRUTINY`, `EVC_SCHEDULED`, `EVC_COMPLETED`, `COMMITTEE_REVIEW`, `DECISION_PENDING`, `COMPLETED`).
  - `application_status`: Operational condition (`IN_PROGRESS`, `ACTION_REQUIRED`, `COMPLETED`).
  - `deadline_condition`: SLA benchmark (`ON_TRACK`, `UPCOMING`, `OVERDUE`, `DUE_TODAY`, `COMPLETED`).

---

## 2. API Endpoints

All endpoints are namespaced under `/api/applications`:

| Method | Endpoint | Authorized Roles | Description |
|---|---|---|---|
| **POST** | `/api/applications` | `Institution Admin`, `Intake Officer`, `Admin` | Register a new application. Automatically generates sequential ID (`APP026+`) and assigns to `Intake Officer`. |
| **GET** | `/api/applications` | All authenticated roles | List applications with optional query filters: `stage`, `status`, `institution_id`, `assigned_role`, `deadline_condition`, `limit`, `offset`. |
| **GET** | `/api/applications/{id}` | All authenticated roles | Retrieve detailed application by ID, including active scrutiny, open deficiencies, decision record, and history. |
| **PUT** | `/api/applications/{id}` | `Institution Admin`, `Admin` | Update permitted editable fields (`contact_email`, `contact_phone`, `programme_name`, etc.). Blocked when in official review. |
| **GET** | `/api/applications/{id}/history` | All authenticated roles | Retrieve chronological audit trail of all workflow transitions for the application. |
| **POST** | `/api/applications/{id}/transition` | Matrix-authorized roles | Configurable workflow transition trigger. Validates state changes against the transition rules engine. |
| **POST** | `/api/applications/{id}/scrutiny` | `Scrutiny Officer`, `Admin` | Record scrutiny outcome (`PASSED` or `DEFICIENT`). If deficient, creates child deficiency records and sets `deficiency_flag='Yes'`. |
| **GET** | `/api/applications/{id}/scrutiny` | All authenticated roles | Retrieve all historical scrutiny evaluation records (initial and re-scrutiny) in chronological order. |
| **POST** | `/api/applications/{id}/deficiency/respond` | `Institution Admin`, `Admin` | Submit institution responses to open deficiencies; transitions application to `RE_SCRUTINY`. |
| **GET** | `/api/applications/{id}/deficiencies` | All authenticated roles | Retrieve all deficiency records for application (optional `?status=OPEN` filter). |
| **POST** | `/api/applications/{id}/decision` | `Competent Authority Secretariat`, `Admin` | Record official human decision (`APPROVED`, `REJECTED`, `APPROVED_WITH_CONDITIONS`) with mandatory statutory reasons. |
| **GET** | `/api/applications/{id}/decision` | All authenticated roles | Retrieve recorded official decision with reasons and conditions (or 404 if pending). |

---

## 3. Four Illustrative Demo Routes

1. **Route 1: Fast-Track / Direct Committee Route**  
   `SUBMITTED` $\rightarrow$ `INITIAL_SCRUTINY` (Passed) $\rightarrow$ `COMMITTEE_REVIEW` $\rightarrow$ `DECISION_PENDING` $\rightarrow$ `COMPLETED (Approved)`
2. **Route 2: Scrutiny Deficiency & Resubmission Loop**  
   `SUBMITTED` $\rightarrow$ `INITIAL_SCRUTINY` (Deficient) $\rightarrow$ `DEFICIENCY_RAISED` $\rightarrow$ Institution Resubmission $\rightarrow$ `RE_SCRUTINY` (Passed) $\rightarrow$ `COMMITTEE_REVIEW` $\rightarrow$ `DECISION_PENDING` $\rightarrow$ `COMPLETED`
3. **Route 3: Comprehensive Physical Inspection Route (EVC)**  
   `SUBMITTED` $\rightarrow$ `INITIAL_SCRUTINY` (Passed) $\rightarrow$ `EVC_SCHEDULED` $\rightarrow$ `EVC_COMPLETED` $\rightarrow$ `COMMITTEE_REVIEW` $\rightarrow$ `DECISION_PENDING` $\rightarrow$ `COMPLETED`
4. **Route 4: Statutory Rejection Route with Recorded Reasons**  
   `SUBMITTED` $\rightarrow$ `INITIAL_SCRUTINY` $\rightarrow$ `DEFICIENCY_RAISED` $\rightarrow$ `RE_SCRUTINY` (Unresolved) $\rightarrow$ `COMMITTEE_REVIEW` $\rightarrow$ `DECISION_PENDING` $\rightarrow$ `COMPLETED (Rejected)`

---

## 4. Running the Project

### Install Dependencies
```powershell
pip install -r requirements.txt
```

### Seed Synthetic Demo Dataset (APP001 - APP025)
```powershell
python -m app.seed
```

### Launch Development Server
```powershell
uvicorn app.main:app --reload --port 8000
```
Interactive OpenAPI documentation will be accessible at: `http://localhost:8000/docs`

### Run Automated Tests (22 Passing Tests)
```powershell
pytest -v tests/test_workflow.py
```
Validates registration, listing, filtering, permitted updates, stage locking, destination derivation, invalid jumps, unauthorized roles, scrutiny outcomes, deficiency loops, re-scrutiny history preservation, official decisions, unknown apps, audit/notification hooks, and atomic rollbacks.

---

## 5. Integration Boundaries & Handshakes

- **Member 4 (EVC Module)**: Coordinates via `EVC_SCHEDULED` and `EVC_COMPLETED` stages. Member 4's EVC inspection records link to `applications.application_id`.
- **Member 4 (Central Audit Sink)**: Member 3 emits decoupled events via `app.core.workflow_engine.emit_audit_event()`.
- **Member 4 (Notification Engine)**: Member 3 emits decoupled alerts via `app.core.workflow_engine.emit_notification_hook()`.
- **Member 4 (Undertakings & Documents)**: Member 4 links undertakings and document compliance files directly to `applications.application_id`.
- **BPMN Simulator**: Member 3's REST endpoints (`/transition`, `/scrutiny`, `/decision`) are idempotent and ready to be driven by or synchronized with the external BPMN simulator.
