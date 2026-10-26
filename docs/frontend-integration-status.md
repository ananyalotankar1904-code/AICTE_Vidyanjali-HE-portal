# SIH26262 — Phase 2B: Frontend-to-Backend Integration Status Report

**Project:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Regulatory Compliance Management System  
**Stage:** Phase 2B (Frontend-to-Backend Integration)  
**Date:** October 26, 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 2B connects the React frontend application (`src/`) to the unified FastAPI gateway (`app/main.py`), utilizing real API responses, canonical entity schemas, server-side role-based authorization headers, and graceful error/degraded/empty states.

### Key Milestones Achieved
1. **Preserved Working Tree:** Reviewed Git working tree and ensured Phase 2A.2 gateway fixes and test suites (53 tests) were fully protected.
2. **Adapter & Normalization Layer:** Implemented `src/api/client.ts` with comprehensive mapping between Member 3 workflow models, Member 4 compliance records, canonical IDs (`INST001`–`INST015`), and frontend UI models.
3. **Incremental Screen Integration:** Successfully migrated all 8 primary frontend screens from static in-memory mocks to live backend API communication.
4. **Honest Error & Resilience States:** Replaced silent mock fallbacks with honest error reporting, loading skeletons, empty database notices, and compliance subsystem degradation banners.
5. **Full Verification:** 
   - 41 of 41 tests passing in `tests/`.
   - 12 of 12 tests passing in `backend/tests/`.
   - Frontend production build (`tsc && vite build`) passing with 0 TypeScript or bundling errors.
   - Live end-to-end integration verified against running unified gateway on port 8020.

---

## 2. Screen-to-Endpoint Mapping & Contract Handling

| Screen | URL Route | Endpoint | Method | Backend Source | Live Data Fields | Adapter / Normalization Logic |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Approval Command Centre** | `/` | `/api/dashboard/summary`<br>`/api/applications`<br>`/api/audit-logs` | `GET` | Unified Gateway<br>(M3 + M4) | `totalApplications`, `pendingScrutiny`, `deficiencyCases`, `evcsScheduled`, `expiringDocuments`, `upcomingDeadlines`, `stageDistribution`, `ageingBuckets`, `status`, `degraded` | Consumes unified dual-contract summary. Adapts `ageingBuckets` and `stageDistribution` to Recharts format. Displays Amber warning banner if `degraded: true`. |
| **Applications Registry** | `/applications` | `/api/applications` | `GET` | Member 3 Router via Gateway | `items`: `application_id`, `institution_id`, `application_type`, `current_stage`, `application_status`, `deficiency_flag`, `submitted_date`, `due_date` | Normalizes `institution_id` to institution name/city using canonical dictionary (`INST001`–`INST015`). Maps stages (`SUBMITTED`–`COMPLETED`) to stepper indices `0`..`5`. Derives age in days from `submitted_date`. |
| **Application Detail** | `/applications/:id` | `/api/applications/{id}`<br>`/api/documents`<br>`/api/audit-logs` | `GET` | Member 3 Router & Member 4 Routers | `application_id`, `institution_id`, `current_stage`, `programme_name`, `intake_approved`, `academic_year`, `contact_email`, `contact_phone`, `decision_record` | Fetches application record by ID. Rejects unknown applications with an honest 404 card instead of falling back to mock record 0. Displays related documents and audit events. |
| **Workflow State Transitions** | `/applications/:id` (Modal) | `/api/applications/{id}/transition`<br>`/api/applications/{id}/decision` | `POST` | Member 3 Router via Gateway | `action`, `to_stage`, `remarks`, `decision`, `reasons` | Transmits caller role headers (`x-user-id`, `x-user-role`). Maps UI modal actions (`ADVANCE_STAGE`, `ISSUE_DEFICIENCY`, `RECORD_OFFICIAL_DECISION`) to backend actions (`SCRUTINY_PASS`, `SCRUTINY_DEFICIENT`, `APPROVED`/`REJECTED`). Displays server rejection message if 400 or 403. |
| **Application Intake** | `/applications/new` | `/api/applications` | `POST` | Member 3 Router via Gateway | `institution_id`, `application_type`, `academic_year`, `contact_email`, `contact_phone`, `programme_name`, `intake_approved` | Submits validated Zod form data to backend `POST /api/applications`. Receives 201 Created with canonical `application_id` (`APP031`), redirects to live detail page. |
| **EVC Management** | `/evc` | `/api/evcs`<br>`/api/applications` | `GET` | Member 4 Router via Gateway | `id`, `application_id`, `planned_visit_date`, `status`, `assigned_members`, `findings_summary`, `report_review_notes` | Maps EVC status (`COMPLETED`, `SCHEDULED`, `PENDING`) to frontend status. Resolves application ID to institution name. Supports both List and Calendar views with live loading skeletons. |
| **Compliance & Documents** | `/compliance` | `/api/documents`<br>`/api/applications` | `GET` | Member 4 Router via Gateway | `id`, `institution_id`, `document_type`, `title`, `file_name`, `version`, `expiry_date`, `review_status` | Maps document category (Land, Faculty, Safety, Infrastructure, Undertaking) from `document_type`. Normalizes verification and expiry status. Calculates valid, expiring, and urgent document counts. |
| **Notifications & Reminders** | `/notifications` | `/api/notifications` | `GET` | Member 4 Router via Gateway | `id`, `entity_id`, `notification_type`, `source_event`, `title`, `message`, `is_read`, `created_at` | Categorizes notifications (`Deficiency alert`, `EVC reminder`, `Deadline reminder`, `Escalation`). Formats human-readable timestamps. |
| **Regulatory Audit Trail** | `/audit` | `/api/audit-logs` | `GET` | Member 4 Router via Gateway | `id`, `entity_type`, `entity_id`, `action`, `actor_id`, `actor_role`, `before_state`, `after_state`, `reason`, `created_at` | Normalizes audit records into chronological timeline events. Formats state transition diffs (`before` -> `after`) and enables CSV export of live records. |

---

## 3. Contract Mismatches Identified & Resolved

### 1. Unified Dashboard Payload Format
- **Mismatch:** Member 3's original schema returned raw database models, whereas Member 4 returned compliance counts under snake_case keys. The frontend UI expected camelCase fields (`totalApplications`, `pendingScrutiny`, `stageDistribution`, `ageingBuckets`).
- **Resolution:** In Phase 2A/2A.2, `app/api/unified_dashboard.py` was established to return the dual contract. In `src/api/client.ts`, both camelCase and snake_case keys (`totalApplications ?? total_applications ?? 0`) are safely extracted with nullish coalescing.

### 2. Canonical Institution ID vs Display Strings
- **Mismatch:** Member 3 and Member 4 store canonical foreign keys like `INST001` through `INST015`. The frontend previously displayed hardcoded string names like `"Pune Institute of Technology"`.
- **Resolution:** Implemented `INSTITUTION_DIRECTORY` in `src/api/client.ts`, mapping canonical IDs (`INST001`–`INST015`) to their official institution name and city/state as defined in `docs/id-mapping.md` and Dataset 1.

### 3. Workflow Stage Enum vs Stepper Index
- **Mismatch:** The backend stores string enums (`SUBMITTED`, `INITIAL_SCRUTINY`, `DEFICIENCY_RAISED`, `RE_SCRUTINY`, `EVC_SCHEDULED`, `EVC_COMPLETED`, `COMMITTEE_REVIEW`, `DECISION_PENDING`, `COMPLETED`). The frontend stepper component consumes a numeric index `0` to `5`.
- **Resolution:** `STAGE_INDEX_MAP` translates each backend stage into its canonical 0..5 stepper position, ensuring `DEFICIENCY_RAISED` maps to Stage 1 (Scrutiny) and `RE_SCRUTINY` maps to Stage 2.

### 4. RBAC Header Handshake
- **Mismatch:** Member 3 routes require `x-user-id` and `x-user-role` headers for authorized workflow actions (e.g., `Scrutiny Officer`, `Competent Authority Secretariat`), returning 403 Forbidden when missing or invalid.
- **Resolution:** `src/api/client.ts` automatically attaches authentication headers based on the active session role, translating UI role labels (`Competent Authority` -> `Competent Authority Secretariat`, `EVC Committee Lead` -> `EVC Coordinator`).

---

## 4. UI Resilience: Loading, Error, Degraded & Empty States

Per Hackathon requirements, the frontend does **not** silently fall back to mock data when an API request fails. Instead, honest, informative feedback is provided:

1. **Loading Skeletons:** Every connected screen displays structured `<Skeleton lines={...} />` elements while waiting for live API responses.
2. **Honest Error Cards:** If a backend request fails (network error, 500 internal server error, or 404 not found):
   - An alert card is displayed with the exact server error message.
   - A `Retry Connection` / `Retry Request` action button is provided to re-execute the query.
   - No fake records are synthesized.
3. **Empty Database Notices:** When an endpoint returns an empty array (`[]`), screens render an `<EmptyState />` explaining that no records exist in the database, with a call-to-action to register new applications or submit intake.
4. **Degraded Mode Banner:** If the unified dashboard returns `degraded: true` (indicating the compliance database is unreachable), the dashboard displays an amber warning banner informing officers that compliance metrics are running on fallback values while core workflow metrics remain active.

---

## 5. Verification Results

### 1. Automated Test Suites (53/53 Passing)
- **Member 3 + Gateway Tests:** `tests/` — **41 passed** in 12.61s.
- **Member 4 Compliance Tests:** `backend/tests/` — **12 passed** in 2.18s.
- **Total Backend Tests:** **53 passed, 0 failed**.

### 2. Frontend Production Build
- **Command:** `cmd /c npm run build` (`tsc && vite build`)
- **Result:** Successfully built in 1m 31s with **0 TypeScript errors** and **0 lint errors**.
- **Output Artifacts:** `dist/index.html` (1.01 kB), `dist/assets/index-BsYWDdU3.css` (20.57 kB), `dist/assets/index-Cn4I4Diy.js` (756.99 kB).

### 3. Live End-to-End API Integration
Executed real HTTP queries against the running unified FastAPI gateway (`http://127.0.0.1:8020`):
- `GET /health` -> HTTP 200 (both workflow and compliance engines operational).
- `GET /api/dashboard/summary` -> HTTP 200 (live application count and distributions).
- `GET /api/applications` -> HTTP 200 (retrieved registered applications).
- `POST /api/applications` -> HTTP 201 Created (`APP031` generated).
- `GET /api/applications/APP031` -> HTTP 200 (retrieved stage `SUBMITTED`).
- `POST /api/applications/APP031/transition` -> HTTP 200 (transitioned to `INITIAL_SCRUTINY` with audit and notification bridge dispatch).
- `GET /api/documents` -> HTTP 200.
- `GET /api/evcs` -> HTTP 200.
- `GET /api/notifications` -> HTTP 200.
- `GET /api/audit-logs` -> HTTP 200.
- `GET /api/applications/APP-NON-EXISTENT-999` -> HTTP 404 Not Found (honest error verified).
- `POST /api/applications/APP031/transition` (invalid stage jump) -> HTTP 400 Bad Request (`INVALID_WORKFLOW_TRANSITION`).
- `POST /api/applications/APP031/transition` (unauthorized role) -> HTTP 403 Forbidden (`UNAUTHORIZED_WORKFLOW_ACTION`).

---

## 6. Screen Connectivity Matrix

| Screen | Status | Data Source | Notes |
| :--- | :--- | :--- | :--- |
| **Approval Command Centre** (`/`) | **Live Connected** | Unified Gateway `/api/dashboard/summary` | Real-time counts, ageing, stage distribution, attention list. Degraded mode banner active if compliance DB fails. |
| **Applications Registry** (`/applications`) | **Live Connected** | Gateway `/api/applications` | Real application listing, search, view filters, sorting, pagination, and refresh. |
| **Application Detail** (`/applications/:id`) | **Live Connected** | Gateway `/api/applications/{id}` | Full case file, linked documents, and audit history. Honest 404 when ID does not exist. |
| **Workflow State Transition Modals** | **Live Connected** | Gateway `/api/applications/{id}/transition` & `/decision` | Executes live server-side state transitions with caller RBAC headers. Rejections show exact server detail. |
| **Application Intake** (`/applications/new`) | **Live Connected** | Gateway `/api/applications` | Zod-validated registration form creates real database records via HTTP POST. |
| **EVC Management** (`/evc`) | **Live Connected** | Gateway `/api/evcs` | Inspects real EVC records; List and Calendar views with live loading skeletons. |
| **Compliance & Documents** (`/compliance`) | **Live Connected** | Gateway `/api/documents` | Live statutory evidence tracking, category filtering, and renewal versioning. |
| **Notifications & Reminders** (`/notifications`) | **Live Connected** | Gateway `/api/notifications` | Live notification stream with category filters and unread status toggle. |
| **Regulatory Audit Trail** (`/audit`) | **Live Connected** | Gateway `/api/audit-logs` | Live tamper-evident audit events, timeline diff view, and CSV export. |
| **BPMN Workflow Showcase** | Preserved Demo | Local BPMN XML definition | Kept intact as visual architecture showcase; no backend dependency needed. |

---

## 7. Files Changed and Why

1. `src/api/client.ts`:
   - Added `isMockMode()` toggle (defaults to live API mode, configurable via `VITE_USE_MOCK`).
   - Added canonical `INSTITUTION_DIRECTORY` dictionary (`INST001`–`INST015`).
   - Implemented normalization functions for applications, documents, EVC records, notifications, and audit logs.
   - Implemented live HTTP fetch calls for all unified gateway endpoints with RBAC headers.
2. `src/types/index.ts`:
   - Added optional `status`, `degraded`, and `subsystem_status` fields to `DashboardSummary`.
3. `vite.config.ts`:
   - Configured dev server reverse proxy forwarding `/api` and `/health` requests to `http://127.0.0.1:8020` (or `VITE_API_URL`).
4. `src/pages/DashboardPage.tsx`:
   - Connected to `apiClient.getDashboardSummary()`, `apiClient.getApplications()`, and `apiClient.getAuditLogs()`.
   - Added loading skeleton cards, degraded mode alert banner, honest error card, and empty states.
5. `src/pages/ApplicationsListPage.tsx`:
   - Connected to `apiClient.getApplications()`.
   - Replaced prototype mock simulation buttons with real "Refresh" action.
   - Added skeleton loading, empty database state, and honest error handling.
6. `src/pages/ApplicationDetailPage.tsx`:
   - Connected to `apiClient.getApplicationById(id)`.
   - Removed silent fallback to mock application 0; shows honest 404 card on missing application.
   - Connected transition modal actions to `apiClient.requestTransition(...)` with live server state refresh.
7. `src/pages/ApplicationIntakePage.tsx`:
   - Connected form submission to `apiClient.createApplication(...)`.
   - Submits real POST request and navigates to the resulting application ID.
8. `src/pages/AuditHistoryPage.tsx`:
   - Connected to `apiClient.getAuditLogs()` with loading, honest error, and empty states.
9. `src/pages/NotificationsPage.tsx`:
   - Connected to `apiClient.getNotifications()` with loading, honest error, and empty states.
10. `src/pages/EvcManagementPage.tsx`:
    - Connected to `apiClient.getEvcs()` with loading, honest error, and empty states for both List and Calendar views.
11. `src/pages/CompliancePage.tsx`:
    - Connected to `apiClient.getDocuments()` with loading, honest error, and empty states.
12. `.env.example`:
    - Created template showing `VITE_API_URL=http://127.0.0.1:8020` and `VITE_USE_MOCK=false`.
13. `src/vite-env.d.ts`:
    - Provided Vite client type declarations for `import.meta.env`.

---

## 8. Remaining Limitations & Recommended Next Steps

1. **Database Consolidation (Phase 3):**
   - The platform currently runs Member 3 (`aicte_platform.db`) and Member 4 (`aicte.db`) on separate SQLite databases via the Phase 2A gateway bridges.
   - Next step: Plan a consolidated schema and database migration so all tables reside in a unified SQLite or PostgreSQL store.
2. **Dataset Seeding (Phase 3):**
   - Bulk ingestion from the 9 Excel datasets (`docs/id-mapping.md`) was deliberately deferred from Phase 2B to keep the frontend integration review safe and isolated.
   - Next step: Implement idempotent dataset seeders for institutions `INST001`–`INST015`, initial compliance documents, and undertakings.
3. **Multi-Role Session Switching:**
   - Role headers (`x-user-id`, `x-user-role`) are currently supplied based on the frontend role switcher.
   - Next step: Connect with JWT authentication once Member 1/2 auth service is integrated.

---
*Report prepared for SIH26262 integration milestone review. Stopping per instructions.*
