# SIH26262 — Unified System API Contract

**System:** AICTE Approval Workflow Automation & Regulatory Compliance Platform  
**Status:** Unified API Specification (Phase 1 Baseline)  
**Base URL:** `http://localhost:8000/api`  
**Protocol:** REST / JSON  
**Encoding:** UTF-8, ISO 8601 Timestamps (`YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD`)  

---

## 1. Authentication & Role Headers

Authentication is simplified for the localhost hackathon prototype. All role-restricted endpoints accept demo headers:

| Header Name | Type | Description | Permitted Values |
|---|---|---|---|
| `X-User-Id` | String | Unique actor identifier | e.g. `INST_ADMIN_1`, `SCRUT_01`, `CA_MEMBER_01`, `EVC_COORD_1` |
| `X-User-Role` | String | Active authorization role | `Institution Admin`, `Intake Officer`, `Scrutiny Officer`, `EVC Coordinator`, `EVC Team`, `Committee Member`, `Competent Authority Secretariat`, `Compliance Officer`, `Admin` |

### Role Hierarchy & Responsibilities:
- **`Institution Admin` / `APPLICANT`:** Submit applications, respond to deficiencies, submit undertaking evidence, submit renewal documents.
- **`Intake Officer`:** Receive new submissions, verify basic required fields, assign to scrutiny queue.
- **`Scrutiny Officer`:** Conduct technical scrutiny, raise specific deficiency clauses, review resubmissions.
- **`EVC Coordinator` / `EVC Team`:** Schedule physical/virtual inspection visits, record visit findings, submit inspection reports.
- **`Committee Member`:** Review Standing Approval Committee (SAC) cases, record recommendations.
- **`Competent Authority Secretariat`:** **Exclusively authorized** to record official approval, rejection, or conditional grant decisions.
- **`Compliance Officer`:** Verify undertakings and post-approval regulatory conditions.
- **`Admin`:** Super-user role with global permissions for demo administration.

---

## 2. Global Error Response Standard

All endpoints return a uniform error object when requests fail:

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "This action is not permitted from current stage 'DEFICIENCY_RAISED'.",
    "details": {
      "current_stage": "DEFICIENCY_RAISED",
      "attempted_action": "SUBMIT_TO_COMMITTEE",
      "required_action": "SUBMIT_DEFICIENCY_RESPONSE"
    }
  }
}
```

### Standard Status Codes:
- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Validation failure or illegal state-machine transition.
- `403 Forbidden`: Authenticated actor does not have the required role for this action.
- `404 Not Found`: Target entity ID does not exist.
- `422 Unprocessable Entity`: Request body failed schema validation.

---

## 3. Workflow & Application Endpoints (Member 3)

### `GET /api/applications`
- **Description:** List institutional applications with multi-criteria filtering.
- **Query Parameters:**
  - `stage` (string, optional): e.g. `SUBMITTED`, `INITIAL_SCRUTINY`, `DEFICIENCY_RAISED`, `RE_SCRUTINY`, `EVC_SCHEDULED`, `COMMITTEE_REVIEW`, `DECISION_PENDING`, `COMPLETED`
  - `status` (string, optional): `IN_PROGRESS`, `ACTION_REQUIRED`, `COMPLETED`
  - `institution_id` (string, optional): e.g. `INST001`
  - `assigned_role` (string, optional): Filter by assigned queue
  - `deadline_condition` (string, optional): `ON_TRACK`, `UPCOMING`, `OVERDUE`, `DUE_TODAY`
  - `limit` (int, default: 50)
  - `offset` (int, default: 0)
- **Response `200 OK`:**
  ```json
  {
    "items": [
      {
        "application_id": "APP001",
        "institution_id": "INST001",
        "application_type": "Extension of Approval",
        "current_stage": "INITIAL_SCRUTINY",
        "application_status": "IN_PROGRESS",
        "submitted_date": "2026-10-13",
        "stage_entered_date": "2026-10-14",
        "due_date": "2026-11-04",
        "assigned_role": "Scrutiny Officer",
        "deficiency_flag": "No",
        "last_updated": "2026-10-25",
        "data_type": "SYNTHETIC_DEMO",
        "deadline_condition": "ON_TRACK",
        "reference_date": "2026-10-25",
        "programme_name": "Engineering & Technology",
        "intake_approved": 480
      }
    ],
    "total": 25,
    "limit": 50,
    "offset": 0
  }
  ```

### `POST /api/applications`
- **Description:** Register and submit a new institutional application.
- **Headers:** `X-User-Role: Institution Admin` or `Intake Officer`
- **Request Body:**
  ```json
  {
    "institution_id": "INST001",
    "application_type": "Extension of Approval",
    "academic_year": "2026-2027",
    "contact_email": "registrar@pit-pune.edu.in",
    "contact_phone": "+91 20 2567 8901",
    "programme_name": "Computer Engineering",
    "intake_approved": 120
  }
  ```
- **Response `201 Created`:** Complete `ApplicationResponse` with auto-generated ID `APP026+`.

### `GET /api/applications/{id}`
- **Description:** Retrieve full application dossier including historical transitions, active scrutiny, deficiencies, and formal decision.
- **Response `200 OK`:** `ApplicationDetailResponse`

### `POST /api/applications/{id}/transition`
- **Description:** Trigger an allowed state progression in the workflow state machine.
- **Request Body:**
  ```json
  {
    "action": "ASSIGN_SCRUTINY",
    "to_stage": "INITIAL_SCRUTINY",
    "remarks": "Assigned to Scrutiny Panel 3"
  }
  ```
- **Response `200 OK`:** Updated `ApplicationResponse`

### `POST /api/applications/{id}/scrutiny`
- **Description:** Record technical scrutiny evaluation. If deficient, creates deficiency items and sets `deficiency_flag='Yes'`.
- **Headers:** `X-User-Role: Scrutiny Officer` or `Admin`
- **Request Body:**
  ```json
  {
    "scrutiny_type": "INITIAL",
    "outcome": "DEFICIENT",
    "remarks": "Land lease deed and fire safety certificate require attention.",
    "deficiencies": [
      "Submit registered lease deed valid for at least 30 years.",
      "Upload valid Fire Safety Clearance NOC from competent municipal authority."
    ]
  }
  ```
- **Response `200 OK`:** Application record transitioned to `DEFICIENCY_RAISED`.

### `POST /api/applications/{id}/deficiency/respond`
- **Description:** Institution responds to open deficiency items, advancing case to `RE_SCRUTINY`.
- **Headers:** `X-User-Role: Institution Admin`
- **Request Body:**
  ```json
  {
    "responses": [
      {
        "deficiency_id": 1,
        "institution_response": "Uploaded 99-year registered lease agreement (doc_7712.pdf)."
      },
      {
        "deficiency_id": 2,
        "institution_response": "Attached renewed Fire Safety Certificate valid until 2028."
      }
    ],
    "remarks": "All documents corrected and resubmitted."
  }
  ```
- **Response `200 OK`:** Application record transitioned to `RE_SCRUTINY`.

### `POST /api/applications/{id}/decision`
- **Description:** Record the official statutory decision. **Restricted exclusively to Competent Authority.**
- **Headers:** `X-User-Role: Competent Authority Secretariat` or `Admin`
- **Request Body:**
  ```json
  {
    "decision": "APPROVED",
    "reasons": "All statutory norms under AICTE APH 2024-27 satisfied. Scrutiny and EVC clean.",
    "conditions": "Subject to submission of annual biometric attendance compliance report."
  }
  ```
- **Response `200 OK`:** Application record transitioned to `COMPLETED` with immutable decision audit entry.

---

## 4. Compliance, EVC, Document & Deadline Endpoints (Member 4)

### `GET /api/evcs`
- **Description:** List EVC inspection records.
- **Response `200 OK`:**
  ```json
  [
    {
      "id": "EVC001",
      "application_id": "APP003",
      "status": "SCHEDULED",
      "assigned_team_id": "EVC_TEAM_SOUTH_01",
      "assigned_members": ["Dr Meera Shah", "Prof. S. Iyer"],
      "planned_visit_date": "2026-11-07T10:00:00Z",
      "venue_address": "Chennai Technical University Campus",
      "reschedule_history": [],
      "created_at": "2026-10-15T09:00:00Z"
    }
  ]
  ```

### `POST /api/evcs`
- **Description:** Schedule or initialize an EVC inspection for an application.
- **Request Body:**
  ```json
  {
    "application_id": "APP003",
    "assigned_team_id": "EVC_TEAM_SOUTH_01",
    "assigned_members": ["Dr Meera Shah", "Prof. S. Iyer"],
    "venue_address": "Chennai Technical University Campus",
    "scheduling_notes": "Physical lab and library inspection"
  }
  ```
- **Response `201 Created`:** `EVCResponse`

### `POST /api/evcs/{id}/schedule`
- **Description:** Set planned inspection date and venue. Transitions status to `SCHEDULED`.

### `POST /api/evcs/{id}/reschedule`
- **Description:** Reschedule visit date with mandatory justification. Retains prior date in `reschedule_history`.
- **Request Body:**
  ```json
  {
    "new_planned_visit_date": "2026-11-12T10:00:00Z",
    "reason": "Expert committee travel delay due to adverse weather",
    "notes": "Coordinated with institution principal"
  }
  ```

### `POST /api/evcs/{id}/complete-visit`
- **Description:** Record visit conclusion. Transitions status to `VISIT_COMPLETED`.

### `POST /api/evcs/{id}/submit-report`
- **Description:** EVC committee submits factual findings and recommendation.
- **Request Body:**
  ```json
  {
    "findings_summary": "All 12 computer laboratories, server rooms, and fire escapes physically inspected.",
    "recommendation": "RECOMMENDED",
    "report_document_id": "DOC-2026-0008"
  }
  ```

### `GET /api/undertakings`
- **Description:** List compliance obligations and statutory undertakings.
- **Response `200 OK`:** List of `ObligationResponse`

### `POST /api/undertakings`
- **Description:** Register a new compliance obligation.

### `POST /api/undertakings/{id}/submit`
- **Description:** Institution uploads undertaking evidence document.

### `POST /api/undertakings/{id}/verify`
- **Description:** Compliance Officer verifies submitted evidence.
- **Headers:** `X-User-Role: Compliance Officer`

### `GET /api/documents`
- **Description:** List institutional regulatory documents with version history and expiry tracking.

### `POST /api/documents/{id}/renew`
- **Description:** Submit renewed document. Creates version $N+1$, marks version $N$ as superseded (`is_latest: false`), and retains version lineage.

### `GET /api/deadlines`
- **Description:** List active deadlines, SLA benchmarks, and escalation states.

### `POST /api/deadlines/check`
- **Description:** Deterministic deadline evaluation against an optional `reference_time`.
- **Query Parameters:** `reference_time` (ISO 8601 string, optional)

### `GET /api/notifications`
- **Description:** List in-app notifications for the active user/role. Supports deduplication.

### `PATCH /api/notifications/{id}/read`
- **Description:** Mark notification as read.

### `GET /api/audit-logs`
- **Description:** Retrieve system-wide immutable audit trail.
- **Query Parameters:** `entity_type`, `entity_id`, `actor_id`, `skip`, `limit`

---

## 5. Unified Dashboard Endpoint

### `GET /api/dashboard/summary`
- **Description:** Aggregates overall application pipeline statistics with compliance, EVC, and document metrics.
- **Response `200 OK`:**
  ```json
  {
    "totalApplications": 25,
    "pendingScrutiny": 7,
    "deficiencyCases": 5,
    "evcsScheduled": 3,
    "expiringDocuments": 4,
    "upcomingDeadlines": 6,
    "stageDistribution": [
      {"stage": "Submitted", "count": 4},
      {"stage": "Scrutiny", "count": 7},
      {"stage": "Re-scrutiny", "count": 3},
      {"stage": "EVC", "count": 3},
      {"stage": "Executive Decision", "count": 5},
      {"stage": "Appeal/Post-approval", "count": 3}
    ],
    "ageingBuckets": [
      {"bucket": "0–15 days", "count": 8},
      {"bucket": "16–30 days", "count": 10},
      {"bucket": "31–45 days", "count": 4},
      {"bucket": "46–60 days", "count": 2},
      {"bucket": "60+ days", "count": 1}
    ],
    "compliance_summary": {
      "evcs_pending_scheduling": 1,
      "evcs_scheduled": 3,
      "evcs_completed_pending_report": 1,
      "evcs_reports_pending_review": 1,
      "open_obligations": 6,
      "documents_expiring_soon": 2,
      "documents_expired": 2,
      "deadlines_overdue": 3
    },
    "by_stage": {
      "SUBMITTED": 4,
      "INITIAL_SCRUTINY": 7,
      "DEFICIENCY_RAISED": 3,
      "RE_SCRUTINY": 2,
      "EVC_SCHEDULED": 2,
      "EVC_COMPLETED": 1,
      "COMMITTEE_REVIEW": 2,
      "DECISION_PENDING": 2,
      "COMPLETED": 2
    },
    "by_status": {
      "IN_PROGRESS": 18,
      "ACTION_REQUIRED": 5,
      "COMPLETED": 2
    }
  }
  ```
