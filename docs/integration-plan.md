# SIH26262 — Safe Integration Plan

**Project:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Regulatory Compliance Management System  
**Phase:** Phase 1 — Prepare for Safe Integration  
**Date:** October 25, 2026  
**Auditor / Integration Engineer:** Senior Software Integration Engineer  
**Baseline Git Commit:** `4aca628` (`main` branch)

---

## 1. Executive Strategy & Recommended Architecture

### 1.1 The Core Dilemma
The repository currently contains two independent, highly functional backend implementations:
1. **Member 3 (`app/`)**: The core workflow state machine, managing application intake, scrutiny queues, deficiency-resubmission loops, committee evaluations, role-based transitions, and authorized human decisions. Tested with 29 passing tests connecting to `aicte_platform.db`.
2. **Member 4 (`backend/app/`)**: The compliance engine, managing EVC visit lifecycle, undertakings, document versioning/expiry, deterministic deadline evaluation, notification deduplication, and audit trails. Tested with 12 passing tests connecting to `aicte.db`.

In addition, the React frontend (`src/`) currently operates via an in-memory client adapter (`src/api/client.ts`) with `USE_LOCAL_MOCK = true`, utilizing mock IDs (`AI-2026-1842`, `EVC-301`).

### 1.2 Evaluated Architectural Alternatives

| Architecture Alternative | Description | Pros | Cons | Feasibility for Immediate Merge |
|---|---|---|---|---|
| **Alternative A: Premature Hard Consolidation** | Forcibly merge all models into a single `Base` and single database file immediately. | Single `.db` file from day one. | **FATAL CONFLICT:** Both modules define `__tablename__ = "applications"` with differing primary keys (`application_id: String(32)` vs `id: String(36)`). SQLAlchemy immediately throws `InvalidRequestError`. Breaks 41 passing tests. | **UNSAFE / BLOCKED** |
| **Alternative B: Dual-Daemon Reverse Proxy** | Run Member 3 on port 8000 and Member 4 on port 8005 indefinitely; use an Nginx/Vite proxy to route between them. | Zero backend code changes. | Requires developers and hackathon evaluators to run 3 separate terminal processes. High operational friction on localhost. | Suboptimal |
| **Alternative C: Gateway-Mount Evolutionary Architecture (RECOMMENDED)** | Run a **single unified FastAPI application** on `http://localhost:8000` (under `app/main.py`). Mount Member 4's API routers alongside Member 3's routers. Initially maintain separate SQLAlchemy session dependencies (`app.database.get_db` and `backend.app.db.get_db`), then bridge audit/notification events. | **Single server, single localhost port (8000), 100% preservation of all 41 existing passing tests**, zero model namespace collisions, immediate frontend access to all `/api/*` endpoints. | Temporarily operates two SQLite database files (`aicte_platform.db` and `aicte.db`) until Phase 3 data consolidation. | **HIGHLY FEASIBLE & SAFE** |

### 1.3 Selected Architecture: Gateway-Mount Unified Server

```
                          +-------------------------------------------------------+
                          |                 React + Vite Frontend                 |
                          |               http://localhost:5173                   |
                          +-------------------------------------------------------+
                                                     |
                                                     | HTTP Fetch (Base: /api)
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                    Unified FastAPI Application Server                                   |
|                                         http://localhost:8000                                           |
|                                                                                                         |
|   +---------------------------------------+             +-------------------------------------------+   |
|   |        Workflow Routers (Member 3)    |             |       Compliance Routers (Member 4)       |   |
|   |  /api/applications                    |             |  /api/evcs, /api/undertakings             |   |
|   |  /api/applications/{id}/scrutiny      |             |  /api/documents, /api/deadlines           |   |
|   |  /api/applications/{id}/deficiency    |             |  /api/notifications, /api/audit-logs      |   |
|   |  /api/applications/{id}/decision      |             |  /api/dashboard/compliance-summary        |   |
|   +---------------------------------------+             +-------------------------------------------+   |
|                       |                                                       |                         |
|                       |                                                       |                         |
|        +--------------v--------------+                         +--------------v--------------+          |
|        | SessionLocal (Workflow)     |                         | SessionLocal (Compliance)   |          |
|        | app.database.get_db         |                         | backend.app.db.get_db       |          |
|        +--------------+--------------+                         +--------------+--------------+          |
|                       |                                                       |                         |
|                       v                                                       v                         |
|         aicte_platform.db (SQLite)                                    aicte.db (SQLite)                 |
|                                                                                                         |
|   +-------------------------------------------------------------------------------------------------+   |
|   |                       Inter-Module Event Bridge (app/core/bridge.py)                            |   |
|   |   Workflow State Engine  ---(register_audit_listener)--->  Member 4 Central Audit Sink          |   |
|   |   Workflow State Engine  ---(register_notification_listener)--->  Member 4 Notification Worker  |   |
|   +-------------------------------------------------------------------------------------------------+   |
|                                                                                                         |
|   +-------------------------------------------------------------------------------------------------+   |
|   |                       Unified Dashboard Aggregator (/api/dashboard/summary)                     |   |
|   |   Combines Member 3 Application KPIs + Member 4 SLA Deadlines, EVCs & Document Expirations      |   |
|   +-------------------------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Immediate Feasibility of a Single Shared Database

### Finding: **NOT Immediately Feasible Without Phased Refactoring**

Static and schema inspection reveals three structural incompatibilities that prevent dropping both codebases into a single database schema today:

1. **Table Metadata Name Collision:**
   - Both `app/models/application.py` and `backend/app/models/application.py` register `__tablename__ = "applications"`.
   - If imported into the same SQLAlchemy declarative base, Python halts with `InvalidRequestError: Table 'applications' is already defined for this MetaData instance`.
2. **Primary Key Divergence:**
   - Member 3's `Application` uses `application_id = Column(String(32), primary_key=True)` (e.g. `APP001`).
   - Member 4's `EVCRecord`, `ComplianceObligation`, and `Document` define foreign keys pointing to `applications.id` (UUID format).
   - Member 4's placeholder `Application` model was an isolated stub.
3. **Enum vs String Deserialization:**
   - Member 4 models use strict Python enums (`EVCStatus`, `WorkflowStage`, `ApplicationStatus`).
   - Member 3 models use `String(64)` matching the exact string values in Dataset 2 (`"INITIAL_SCRUTINY"`, `"DEFICIENCY_RAISED"`, `"COMPLETED"`).
   - Direct cross-querying causes enum lookup exceptions unless strings are mapped.

### Resolution Strategy:
In Phase 2, we implement **Isolated Sessions under Unified FastAPI**. Member 4's foreign keys in `aicte.db` are relaxed or mapped via `application_id`, while both database sessions run concurrently in the same process. Once all integration tests pass, Phase 3 will merge the models into a single declarative base by migrating Member 4 foreign keys to `applications.application_id`.

---

## 3. Endpoints & Owning Modules

The complete, unified API route table for the integrated application is as follows:

| Endpoint Path | HTTP Method | Owning Module | Description | Authorized Roles |
|---|---|---|---|---|
| `/health` | `GET` | Core System | Health check returning service status | Public |
| `/api/dashboard/summary` | `GET` | Unified (M3 + M4) | Full KPI metrics: applications, scrutiny, EVCs, documents, deadlines | All authenticated |
| `/api/applications` | `GET` | Member 3 | List applications with filtering by stage, status, role, condition | All authenticated |
| `/api/applications` | `POST` | Member 3 | Register new application (`APP026+`) | `Institution Admin`, `Intake Officer`, `Admin` |
| `/api/applications/{id}` | `GET` | Member 3 | Get detailed application with scrutiny, deficiencies, decision, history | All authenticated |
| `/api/applications/{id}` | `PUT` | Member 3 | Update permitted fields (email, phone, intake) | `Institution Admin`, `Admin` |
| `/api/applications/{id}/history` | `GET` | Member 3 | Complete workflow transition history audit log | All authenticated |
| `/api/applications/{id}/transition` | `POST` | Member 3 | Trigger permitted workflow stage transition | Role authorized by transition matrix |
| `/api/applications/{id}/scrutiny` | `POST` | Member 3 | Record scrutiny outcome (`PASSED`, `DEFICIENT`) | `Scrutiny Officer`, `Admin` |
| `/api/applications/{id}/scrutiny` | `GET` | Member 3 | Get all historical scrutiny evaluations | All authenticated |
| `/api/applications/{id}/deficiencies` | `GET` | Member 3 | Get open and resolved deficiency items | All authenticated |
| `/api/applications/{id}/deficiency/respond` | `POST` | Member 3 | Institution submits deficiency responses; sets `RE_SCRUTINY` | `Institution Admin`, `Admin` |
| `/api/applications/{id}/decision` | `POST` | Member 3 | Authorized official records formal decision with reasons | `Competent Authority Secretariat`, `Admin` |
| `/api/applications/{id}/decision` | `GET` | Member 3 | Get recorded official decision | All authenticated |
| `/api/evcs` | `GET` | Member 4 | List EVC records with filtering | All authenticated |
| `/api/evcs` | `POST` | Member 4 | Schedule or assign EVC inspection | `EVC Coordinator`, `Admin` |
| `/api/evcs/{id}` | `GET` | Member 4 | Get EVC record, schedule history, and report | All authenticated |
| `/api/evcs/{id}/schedule` | `POST` | Member 4 | Set visit date and venue | `EVC Coordinator`, `Admin` |
| `/api/evcs/{id}/reschedule` | `POST` | Member 4 | Reschedule visit date with reason preservation | `EVC Coordinator`, `Admin` |
| `/api/evcs/{id}/complete-visit` | `POST` | Member 4 | Record physical/virtual visit completion | `EVC Team`, `EVC Coordinator`, `Admin` |
| `/api/evcs/{id}/submit-report` | `POST` | Member 4 | Submit factual inspection report and recommendation | `EVC Team`, `Admin` |
| `/api/evcs/{id}/review-report` | `POST` | Member 4 | Review and accept EVC report | `Compliance Officer`, `Admin` |
| `/api/undertakings` | `GET` | Member 4 | List compliance obligations and undertakings | All authenticated |
| `/api/undertakings` | `POST` | Member 4 | Register compliance obligation or undertaking | `Compliance Officer`, `Admin` |
| `/api/undertakings/{id}/submit` | `POST` | Member 4 | Institution submits undertaking evidence | `Institution Admin`, `Admin` |
| `/api/undertakings/{id}/verify` | `POST` | Member 4 | Compliance officer verifies evidence | `Compliance Officer`, `Admin` |
| `/api/documents` | `GET` | Member 4 | List document metadata and versions | All authenticated |
| `/api/documents` | `POST` | Member 4 | Register regulatory document | `Institution Admin`, `Compliance Officer` |
| `/api/documents/{id}/renew` | `POST` | Member 4 | Renew document; creates version N+1 and retains prior version | `Institution Admin`, `Compliance Officer` |
| `/api/deadlines` | `GET` | Member 4 | List active and historical deadlines | All authenticated |
| `/api/deadlines/check` | `POST` | Member 4 | Deterministic deadline evaluation against reference timestamp | System, `Admin` |
| `/api/notifications` | `GET` | Member 4 | List in-app notifications for active role | All authenticated |
| `/api/notifications/{id}/read` | `PATCH` | Member 4 | Mark notification as read | Recipient |
| `/api/audit-logs` | `GET` | Member 4 | List immutable system audit events | All authenticated |

---

## 4. Audit & Notification Event Integration

### 4.1 Integration Pattern
Member 3's `app/core/workflow_engine.py` already includes decoupled listener mechanisms:
```python
register_audit_listener(callback: Callable[[Dict[str, Any]], None])
register_notification_listener(callback: Callable[[Dict[str, Any]], None])
```

### 4.2 Bridge Implementation (`app/core/bridge.py` for Phase 2)
```python
def handle_workflow_audit_event(event_dict: dict):
    \"\"\"Adapts Member 3 workflow event into Member 4 AuditEvent record.\"\"\"
    db = backend.app.db.SessionLocal()
    try:
        backend.app.services.audit.record_audit_event(
            db=db,
            actor_id=event_dict.get("actor_id", "SYSTEM"),
            actor_role=event_dict.get("actor_role", "SYSTEM"),
            action=event_dict.get("event_type", "WORKFLOW_ACTION"),
            entity_type="APPLICATION",
            entity_id=event_dict.get("target_id", "UNKNOWN"),
            details=event_dict.get("details", {})
        )
    finally:
        db.close()

def handle_workflow_notification_event(notif_dict: dict):
    \"\"\"Adapts Member 3 notification hook into Member 4 deduplicated Notification.\"\"\"
    db = backend.app.db.SessionLocal()
    try:
        backend.app.services.notifications.create_notification(
            db=db,
            recipient_role=notif_dict.get("recipient_role", "APPLICANT"),
            notification_type=NotificationType.OBLIGATION_ACTION_REQUIRED,
            entity_type="APPLICATION",
            entity_id=notif_dict.get("application_id", ""),
            title=f"Workflow Update: {notif_dict.get('event_type')}",
            message=notif_dict.get("message", ""),
            deduplication_key=f"workflow:{notif_dict.get('event_type')}:{notif_dict.get('application_id')}"
        )
    finally:
        db.close()
```

---

## 5. Phased Implementation Sequence & Test Gates

### Phase 2: Gateway Integration & Router Mounting
- **Actions:**
  1. Update `app/main.py` to mount Member 4's routers alongside Member 3's routers.
  2. Implement `app/api/dashboard.py` uniting application counts and compliance metrics.
  3. Wire `app/core/bridge.py` during FastAPI startup lifespan.
  4. Configure CORS for `http://localhost:5173`.
- **Test Gate 2:**
  - `python -m pytest tests -v` $\rightarrow$ 29/29 pass.
  - `python -m pytest backend/tests -v` $\rightarrow$ 12/12 pass.
  - Test unified `/health` and `/api/dashboard/summary` via TestClient.

### Phase 3: Frontend Client Alignment & Build
- **Actions:**
  1. Run `npm install` (once authorized).
  2. Run `npm run build` and `npm run lint`.
  3. Update `src/api/client.ts` to map canonical backend schemas (EVC date/members formatting, dashboard response shape).
  4. Update `src/api/client.ts` to switch `USE_LOCAL_MOCK = false` when backend is active.
- **Test Gate 3:**
  - TypeScript build clean (`0 errors`).
  - Frontend development server runs on `http://localhost:5173`.
  - Application list and dashboard load from backend `http://localhost:8000`.

### Phase 4: Full Dataset Seed & Workflow End-to-End
- **Actions:**
  1. Consolidate `python -m app.seed` to ingest all 9 Excel datasets into both databases (`APP001`–`APP025`, `INST001`–`INST015`, `EVC001`–`EVC007`).
  2. Restore BPMN showcase into `bpmn/` directory.
  3. Execute the 4 end-to-end demonstration scenarios.
- **Test Gate 4:**
  - Fast-Track approval route succeeds end-to-end.
  - Scrutiny deficiency resubmission loop succeeds end-to-end.
  - EVC schedule and report review succeeds end-to-end.
  - Statutory rejection with recorded reasons succeeds end-to-end.

---

## 6. Backward Compatibility & Rollback Plan

1. **Test Isolation:**
   - Both test suites use in-memory SQLite fixtures (`sqlite:///:memory:` with `StaticPool`). Merging routers in `app/main.py` will not break either test suite because test fixtures override session dependencies.
2. **Git Working Tree Protection:**
   - All Phase 1 changes are documentation-only (`docs/integration-plan.md`, `docs/api-contract.md`, `docs/id-mapping.md`).
   - If Phase 2 encounters unexpected issues, `git checkout -- app/main.py` reverts immediately to the pristine Member 3 baseline.
3. **Frontend Fallback:**
   - The toggle `const USE_LOCAL_MOCK = true;` in `src/api/client.ts` remains intact as a zero-latency fallback if the backend service is offline.
