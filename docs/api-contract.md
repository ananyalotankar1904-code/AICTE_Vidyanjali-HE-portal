# API Contract: Backend Compliance, EVC, Documents, Deadlines & Notifications

**Author:** Member 4 — Backend Compliance Developer  
**Status:** Implemented & Tested  
**Base URL:** `/api`  

All requests and responses use JSON and ISO 8601 timestamps. Role-restricted endpoints accept authentication headers (or demo headers: `X-User-Id` and `X-User-Role`).

---

## 1. Shared Enums

### Roles (`X-User-Role`)
- `APPLICANT`: Institution representative
- `SCRUTINY_OFFICER`: Technical scrutiny officer
- `EVC_TEAM`: Expert Visit Committee member / Convener
- `COMMITTEE_MEMBER`: Standing Approval Committee member
- `COMPLIANCE_OFFICER`: Compliance & Undertaking Verification Officer
- `COMPETENT_AUTHORITY`: Regional Officer / Statutory Decision Authority
- `ADMIN`, `SYSTEM`

### Lifecycles
- **EVC Status:** `PENDING_SCHEDULING`, `SCHEDULED`, `VISIT_COMPLETED`, `REPORT_SUBMITTED`, `REPORT_REVIEWED`
- **EVC Recommendation:** `RECOMMENDED`, `DEFICIENCIES_NOTED`, `NOT_RECOMMENDED`
- **EVC Review Outcome:** `ACCEPTED`, `CLARIFICATION_REQUESTED`
- **Obligation Status:** `PENDING`, `SUBMITTED`, `NEEDS_CORRECTION`, `VERIFIED`
- **Document Review Status:** `PENDING_REVIEW`, `VERIFIED`, `NEEDS_REPLACEMENT`, `REJECTED`
- **Deadline Status:** `ACTIVE`, `COMPLETED`, `CANCELLED`, `OVERDUE`
- **Notification Types:** `DEADLINE_UPCOMING`, `DEADLINE_OVERDUE`, `ESCALATION_ALERT`, `DOCUMENT_EXPIRING`, `DOCUMENT_EXPIRED`, `EVC_SCHEDULED`, `EVC_RESCHEDULED`, `EVC_REPORT_SUBMITTED`, `OBLIGATION_ACTION_REQUIRED`, `OBLIGATION_VERIFIED`

---

## 2. Expert Visit Committee (EVC) Endpoints

### `GET /api/evcs`
- **Purpose:** List EVC records with optional filtering.
- **Query Parameters:**
  - `application_id` (string, optional)
  - `status` (EVCStatus, optional)
  - `assigned_team_id` (string, optional)
  - `skip` (int, default: 0)
  - `limit` (int, default: 50)
- **Response:** `200 OK` List of `EVCResponse`

### `POST /api/evcs`
- **Purpose:** Initialize an EVC verification record for an application.
- **Request Body:**
  ```json
  {
    "application_id": "app-synthetic-101",
    "assigned_team_id": "EVC_TEAM_WEST_04",
    "assigned_members": ["Prof. R. K. Sharma", "Dr. Anita Desai"],
    "venue_address": "Navi Mumbai Campus",
    "scheduling_notes": "Pending schedule confirmation"
  }
  ```
- **Response:** `201 Created` (`EVCResponse`)

### `GET /api/evcs/{evc_id}`
- **Purpose:** Get detailed EVC record, including reschedule history and report status.
- **Response:** `200 OK` (`EVCResponse`)

### `POST /api/evcs/{evc_id}/schedule`
- **Purpose:** Set planned visit date and venue. Transitions status from `PENDING_SCHEDULING` to `SCHEDULED`.
- **Request Body:**
  ```json
  {
    "planned_visit_date": "2026-10-30T10:00:00Z",
    "venue_address": "Campus Road 1",
    "notes": "Official inspection date set"
  }
  ```
- **Response:** `200 OK` (`EVCResponse`)

### `POST /api/evcs/{evc_id}/reschedule`
- **Purpose:** Reschedule an existing visit. Appends prior schedule to `reschedule_history` without deleting old date.
- **Request Body:**
  ```json
  {
    "new_planned_visit_date": "2026-11-02T10:00:00Z",
    "reason": "Expert committee travel interruption",
    "notes": "Confirmed with institution"
  }
  ```
- **Response:** `200 OK` (`EVCResponse`)

### `POST /api/evcs/{evc_id}/complete-visit`
- **Purpose:** Record visit conclusion. Transitions status to `VISIT_COMPLETED`.
- **Request Body:**
  ```json
  {
    "actual_visit_date": "2026-11-02T15:30:00Z",
    "visit_notes": "All laboratories and fire exits physically inspected."
  }
  ```
- **Response:** `200 OK` (`EVCResponse`)

### `POST /api/evcs/{evc_id}/submit-report`
- **Purpose:** EVC team submits factual observations and recommendations. Status -> `REPORT_SUBMITTED`.
- **Request Body:**
  ```json
  {
    "findings_summary": "Laboratory equipment and faculty cadres comply with norms.",
    "recommendation": "RECOMMENDED",
    "report_document_id": "doc-evc-report-001"
  }
  ```
- **Response:** `200 OK` (`EVCResponse`)

### `POST /api/evcs/{evc_id}/review-report`
- **Purpose:** Authorized officer reviews report. Status -> `REPORT_REVIEWED`.
- **Headers:** `X-User-Role: COMPLIANCE_OFFICER` (or `ADMIN`, `SCRUTINY_OFFICER`)
- **Request Body:**
  ```json
  {
    "outcome": "ACCEPTED",
    "review_notes": "Findings accepted and forwarded to committee case file."
  }
  ```
- **Response:** `200 OK` (`EVCResponse`)

---

## 3. Compliance Obligations & Undertakings Endpoints

### `GET /api/undertakings`
- **Query Parameters:** `institution_id`, `application_id`, `status`, `skip`, `limit`
- **Response:** `200 OK` List of `ObligationResponse`

### `POST /api/undertakings`
- **Purpose:** Register a new regulatory undertaking or condition.
- **Request Body:**
  ```json
  {
    "institution_id": "INST-MUMBAI-01",
    "application_id": "app-synthetic-101",
    "title": "Faculty Cadre Ratio Compliance Undertaking",
    "obligation_type": "FACULTY_CADRE_RATIO",
    "description": "Maintain 1:15 cadre ratio.",
    "source_reference": "APH 2024-2027 Section 4.3",
    "is_illustrative_demo_rule": false,
    "due_date": "2026-11-15T00:00:00Z",
    "responsible_owner": "Principal"
  }
  ```
- **Response:** `201 Created` (`ObligationResponse`)

### `POST /api/undertakings/{obligation_id}/submit`
- **Purpose:** Institution submits evidence document. Status -> `SUBMITTED`.
- **Request Body:**
  ```json
  {
    "evidence_document_id": "doc-faculty-affidavit-001",
    "submission_notes": "Notarized affidavit and board resolution attached."
  }
  ```
- **Response:** `200 OK` (`ObligationResponse`)

### `POST /api/undertakings/{obligation_id}/request-correction`
- **Purpose:** Officer returns evidence for correction. Status -> `NEEDS_CORRECTION`. Appends to `correction_history`.
- **Headers:** `X-User-Role: COMPLIANCE_OFFICER`
- **Request Body:**
  ```json
  {
    "reason": "Missing Professor cadre appointment letters.",
    "guidance": "Please upload Annexure 3."
  }
  ```
- **Response:** `200 OK` (`ObligationResponse`)

### `POST /api/undertakings/{obligation_id}/verify`
- **Purpose:** Official verification by compliance officer. Status -> `VERIFIED`.
- **Headers:** `X-User-Role: COMPLIANCE_OFFICER`
- **Request Body:**
  ```json
  {
    "verification_notes": "Documents verified against sanctioned intake requirements."
  }
  ```
- **Response:** `200 OK` (`ObligationResponse`)

---

## 4. Document Metadata, Versioning & Renewal Endpoints

### `GET /api/documents`
- **Query Parameters:** `institution_id`, `application_id`, `obligation_id`, `document_type`, `is_latest`, `review_status`, `skip`, `limit`
- **Response:** `200 OK` List of `DocumentResponse`

### `POST /api/documents`
- **Purpose:** Register document metadata (Version 1).
- **Request Body:**
  ```json
  {
    "institution_id": "INST-MUMBAI-01",
    "document_type": "FIRE_SAFETY_NOC",
    "title": "Municipal Fire NOC 2025",
    "file_name": "fire_noc.pdf",
    "storage_path": "/vault/docs/INST-MUMBAI-01/fire_noc.pdf",
    "file_size_bytes": 1048576,
    "expiry_date": "2026-11-10T00:00:00Z",
    "is_expiry_tracked": true
  }
  ```
- **Response:** `201 Created` (`DocumentResponse`, `version: 1`, `is_latest: true`)

### `POST /api/documents/{document_id}/renew`
- **Purpose:** Register replacement/renewal document (Version N+1). Retains prior version intact with `is_latest: false`.
- **Request Body:**
  ```json
  {
    "title": "Municipal Fire NOC (Renewed 2026-2027)",
    "file_name": "fire_noc_2026.pdf",
    "expiry_date": "2027-11-10T00:00:00Z",
    "renewal_reason": "Annual statutory municipal renewal"
  }
  ```
- **Response:** `201 Created` (`DocumentResponse`, `version: 2`, `previous_version_id: "<v1_id>"`, `is_latest: true`)

### `GET /api/documents/status/expiring-soon`
- **Query Parameters:** `reference_time` (datetime, optional), `threshold_days` (int, default: 30)
- **Response:** `200 OK` List of active documents expiring within threshold.

### `GET /api/documents/status/expired`
- **Query Parameters:** `reference_time` (datetime, optional)
- **Response:** `200 OK` List of active documents past their expiry date.

### `POST /api/documents/{document_id}/review`
- **Purpose:** Officer verifies or rejects document.
- **Headers:** `X-User-Role: COMPLIANCE_OFFICER`
- **Request Body:**
  ```json
  {
    "status": "VERIFIED",
    "review_notes": "Verified against municipal corporation register."
  }
  ```
- **Response:** `200 OK` (`DocumentResponse`)

---

## 5. Deadlines & Escalation Monitoring Endpoints

### `GET /api/deadlines`
- **Query Parameters:** `entity_type`, `entity_id`, `owner_role`, `status`, `skip`, `limit`
- **Response:** `200 OK` List of `DeadlineResponse`

### `POST /api/deadlines`
- **Purpose:** Register tracked statutory or operational deadline.
- **Request Body:**
  ```json
  {
    "entity_type": "APPLICATION",
    "entity_id": "app-synthetic-101",
    "deadline_type": "DEFICIENCY_RESPONSE",
    "title": "Deficiency Clarification Window",
    "due_date": "2026-11-05T18:00:00Z",
    "owner_role": "APPLICANT",
    "warning_threshold_hours": 48,
    "escalation_policy": "NOTIFY_REGIONAL_OFFICER_ON_OVERDUE",
    "is_statutory": true
  }
  ```
- **Response:** `201 Created` (`DeadlineResponse`)

### `POST /api/deadlines/evaluate`
- **Purpose:** Deterministically evaluates active deadlines against `reference_time` (or system UTC). Triggers deduplicated upcoming reminders and overdue escalations.
- **Request Body:**
  ```json
  {
    "reference_time": "2026-11-06T00:00:00Z"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "evaluated_at": "2026-10-25T14:15:00Z",
    "reference_time": "2026-11-06T00:00:00Z",
    "total_active_evaluated": 5,
    "upcoming_warnings_issued": 1,
    "overdue_escalations_issued": 2,
    "deadlines_marked_overdue": 2
  }
  ```

### `POST /api/deadlines/{deadline_id}/complete`
- **Purpose:** Marks deadline completed once underlying obligation/task is done. Prevents future alerts.
- **Response:** `200 OK` (`DeadlineResponse`)

### `POST /api/deadlines/{deadline_id}/cancel`
- **Purpose:** Cancels obsolete or superseded deadline.
- **Response:** `200 OK` (`DeadlineResponse`)

---

## 6. In-App Notifications Endpoints

### `GET /api/notifications`
- **Query Parameters:** `recipient_role`, `recipient_id`, `is_read`, `entity_type`, `entity_id`, `skip`, `limit`
- **Response:** `200 OK` List of `NotificationResponse`

### `POST /api/notifications/{notification_id}/read`
- **Purpose:** Marks notification as read.
- **Response:** `200 OK` (`NotificationResponse`, `is_read: true`, `read_at: timestamp`)

---

## 7. Dashboard & Audit Endpoints

### `GET /api/dashboard/compliance-summary`
- **Purpose:** Aggregated live metrics for EVC, compliance, document renewals, deadlines, notifications, and audit volume.
- **Query Parameters:** `reference_time` (datetime, optional)
- **Response:** `200 OK`
  ```json
  {
    "computed_at": "2026-10-25T14:15:00Z",
    "evc": {
      "pending_scheduling": 1,
      "scheduled": 1,
      "completed_pending_report": 0,
      "reports_pending_review": 1
    },
    "compliance": {
      "open_obligations": 2,
      "awaiting_verification": 1,
      "overdue_obligations": 1
    },
    "documents": {
      "nearing_expiry_30_days": 1,
      "past_expiry": 1
    },
    "deadlines": {
      "upcoming_active": 1,
      "overdue": 1,
      "escalations_generated": 1
    },
    "notifications": {
      "unread_count": 2
    },
    "audit": {
      "total_events_logged": 15
    }
  }
  ```

### `GET /api/audit-logs`
- **Purpose:** Read-only immutable audit trail.
- **Query Parameters:** `entity_type`, `entity_id`, `actor_id`, `action`, `skip`, `limit`
- **Response:** `200 OK` List of `AuditLogResponse`
