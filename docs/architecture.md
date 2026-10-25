# Architecture: Compliance, EVC, Documents, Deadlines & Audit

**Module Owner:** Member 4 — Backend Compliance Developer  
**System:** AICTE Approval Workflow Automation & Compliance Management Platform (SIH26262)  
**Technology Stack:** Python 3.14 / 3.11, FastAPI, SQLAlchemy 2.0 ORM, SQLite Database  

---

## 1. System Context & Module Responsibilities

Member 4 provides the backend subsystems for institutional compliance verification, on-site/virtual inspections (EVC), document versioning, and deterministic time/deadline monitoring.

```
+-----------------------------------------------------------------------------------+
|                               FastAPI REST Layer                                  |
|   /api/evcs   |   /api/undertakings   |   /api/documents   |   /api/deadlines     |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                  Service Layer                                    |
|   evc.py      |     compliance.py     |     document.py    |     deadlines.py     |
+-----------------------------------------------------------------------------------+
                               |                  |
           +-------------------+                  +-------------------+
           v                                                          v
+------------------------+                                 +------------------------+
|   Notification Service |                                 |     Audit Service      |
|   (Deduplicated alerts)|                                 |  (Immutable event log) |
+------------------------+                                 +------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                SQLAlchemy Models                                  |
|   EVCRecord   |   ComplianceObligation   |   Document   |   DeadlineRecord        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               SQLite Local Database                               |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

### 1. Separation of Concerns & Statutory Boundary
- **EVC Findings ≠ Statutory Decision:** The EVC team submits factual observations and recommendations (`RECOMMENDED`, `DEFICIENCIES_NOTED`, `NOT_RECOMMENDED`). They **never** autonomously decide an application. Only the Competent Authority (Member 3 workflow) can issue an official grant or rejection.
- **Overdue Flag ≠ Formal Rejection:** When a deadline expires, the system triggers reminders and supervisory escalation (`ESCALATION_ALERT`), but does not cancel or reject the application.
- **Document Expiry ≠ Approval Withdrawal:** Expiry is a tracked condition that flags a document for renewal.

### 2. Document Versioning & Immutability
- Document renewals (Version N+1) are linked via `previous_version_id` to the predecessor.
- Prior versions are preserved with `is_latest = False`. No document record or storage pointer is silently overwritten or erased.

### 3. Deterministic Deadline Engine & Idempotency
- `evaluate_deadlines` takes an optional `reference_time`. This decouples time-dependent business logic from the system clock, allowing unit tests and demo scripts to simulate future dates deterministically.
- Notifications utilize composite `deduplication_key` values (e.g. `deadline:overdue:{id}`, `deadline:upcoming:{id}`). Running evaluation repeatedly is 100% idempotent.

### 4. Atomic Audit Logging & Transaction Integrity
- Every state transition across EVC, undertakings, documents, and deadlines writes an `AuditEvent` inside the exact same database transaction.
- If a state mutation fails, the audit record is rolled back, preventing state/audit divergence.
