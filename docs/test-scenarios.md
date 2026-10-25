# Test Scenarios and Automated Test Results

**Module:** Member 4 — Backend Compliance, EVC, Documents & Deadlines  
**Test Framework:** pytest 9.1.1, FastAPI TestClient, SQLite in-memory StaticPool  
**Execution Date:** 2026-10-25  

---

## 1. Test Summary

| Test Suite | Total Tests | Passed | Failed | Status |
|---|---|---|---|---|
| `test_evc.py` | 3 | 3 | 0 | PASSED |
| `test_compliance.py` | 2 | 2 | 0 | PASSED |
| `test_documents.py` | 2 | 2 | 0 | PASSED |
| `test_deadlines_notifications.py` | 2 | 2 | 0 | PASSED |
| `test_dashboard_integration.py` | 3 | 3 | 0 | PASSED |
| **Total** | **12** | **12** | **0** | **100% PASSED** |

---

## 2. Test Execution Details

### EVC Lifecycle Tests (`backend/tests/test_evc.py`)
1. **`test_create_and_schedule_evc`**:
   - Creates EVC record in `PENDING_SCHEDULING`.
   - Schedules initial visit for `T + 5 days`.
   - Reschedules to `T + 7 days` with travel delay reason.
   - Verifies `reschedule_history` length is 1 and preserves prior date and reason.
2. **`test_evc_invalid_transition`**:
   - Attempts to complete visit from `PENDING_SCHEDULING` directly.
   - Asserts API returns HTTP 400 Bad Request with descriptive message.
3. **`test_evc_full_lifecycle`**:
   - Executes full pipeline: `PENDING_SCHEDULING -> SCHEDULED -> VISIT_COMPLETED -> REPORT_SUBMITTED -> REPORT_REVIEWED`.
   - Verifies unauthorized applicant cannot review report (HTTP 403 Forbidden).
   - Verifies compliance officer successfully reviews report.
   - Confirms audit logs created for all 5 actions.

### Compliance Undertakings Tests (`backend/tests/test_compliance.py`)
1. **`test_obligation_full_lifecycle`**:
   - Registers obligation in `PENDING`.
   - Submits evidence document -> status transitions to `SUBMITTED`.
   - Requests correction -> status transitions to `NEEDS_CORRECTION`, `correction_history` populated.
   - Resubmits revised evidence -> status returns to `SUBMITTED`.
   - Rejects unauthorized applicant verification attempt (HTTP 403).
   - Authorizes compliance officer verification -> status transitions to `VERIFIED`.
   - Verifies immutable audit events for all transitions.
2. **`test_standalone_obligation_without_application`**:
   - Creates an obligation without an application ID (general institutional undertaking).
   - Confirms independent tracking.

### Document Versioning & Expiry Tests (`backend/tests/test_documents.py`)
1. **`test_document_registration_and_renewal_versioning`**:
   - Registers document v1 with `is_latest: true`.
   - Renews document creating v2 linked to v1.
   - Verifies v2 has `version: 2`, `is_latest: true`, `previous_version_id: v1.id`.
   - Verifies v1 is retained intact with `version: 1`, `is_latest: false`, unchanged file name.
2. **`test_document_expiry_queries`**:
   - Registers document expiring in 15 days, document expired 5 days ago, and document with no expiry.
   - Queries `/api/documents/status/expiring-soon` with 30-day threshold: matches only the 15-day document.
   - Queries `/api/documents/status/expired`: matches only the past-due document.

### Deadlines & Notifications Tests (`backend/tests/test_deadlines_notifications.py`)
1. **`test_deadline_deterministic_evaluation_and_deduplication`**:
   - Registers upcoming deadline (due in 24h) and overdue deadline (due -2h), and completed deadline.
   - Evaluates with fixed `reference_time`.
   - Confirms upcoming warning and overdue escalation generated.
   - Evaluates second time: confirms exact same notification count (no duplicate alerts).
   - Confirms completed deadline generates zero alerts.
2. **`test_notification_read_workflow`**:
   - Queries unread notifications (`is_read: false`).
   - Calls `/api/notifications/{id}/read`.
   - Confirms `is_read: true` and `read_at` timestamp populated.

### Dashboard & Integration Tests (`backend/tests/test_dashboard_integration.py`)
1. **`test_dashboard_compliance_metrics`**:
   - Verifies metrics reflect real SQL counts as records are added.
   - Verifies unified dashboard `/api/dashboard/summary`.
2. **`test_invalid_entity_id_handling`**:
   - Confirms 404 response on non-existent EVC, obligation, document, and deadline IDs.
3. **`test_health_and_root_endpoints`**:
   - Confirms `/health` returns status healthy and `/` returns documentation links.

---

## 3. How to Run Tests Locally

```powershell
cd backend
python -m pytest tests -v
```
Output: `12 passed in 2.40s`
