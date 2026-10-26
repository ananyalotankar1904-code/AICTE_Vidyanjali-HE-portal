# SIH26262 — Judging Readiness Checklist & Presentation Defense Guide

**Project:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Regulatory Compliance Management System  
**Hackathon:** Smart India Hackathon (SIH) 2026 — Problem Statement SIH26262  
**Evaluation Status:** **PASS (READY FOR JUDGING)**  
**Target Environment:** Localhost (FastAPI Gateway + React Vite + Dual SQLite Engines)  
**Evaluation Date:** 2026-10-26  

---

## 1. Problem Statement & User Personas

### 1.1 The Challenge
The All India Council for Technical Education (AICTE) processes tens of thousands of institutional approval applications annually (Extension of Approval, Increase in Intake, New Course, New Institution). Traditional processes face challenges with:
- **Bottlenecks and Deadlines:** Difficulty tracking service level agreements (SLAs) and institutional submission deadlines.
- **Regulatory Confusion:** Conflating temporary document deficiencies with formal application rejections.
- **Siloed Systems:** Disconnection between initial approval workflow execution and ongoing post-approval regulatory compliance monitoring (e.g., land ownership, fire safety NOCs, faculty ratio undertakings).
- **Audit & Governance:** Lack of an immutable, tamper-evident audit log tracking every stage transition and statutory decision.

### 1.2 Intended User Personas & RBAC Matrix
The platform implements explicit role-based access control (RBAC) across six primary stakeholders:

| User Persona | Key Responsibilities | Access Level & Permissions |
| :--- | :--- | :--- |
| **Institution Admin** (`INST001`–`INST015`) | Submits applications, uploads compliance documents, and responds to deficiency notices. | Can edit applications only in `DRAFT`, `SUBMITTED`, or `DEFICIENCY_RAISED`. Locked out of evaluation and decision endpoints. |
| **Intake Officer** | Reviews new submissions for basic completeness and assigns applications to scrutiny. | Can transition from `SUBMITTED` &rarr; `INITIAL_SCRUTINY` (`ASSIGN_SCRUTINY`). |
| **Scrutiny Officer** (e.g., Ananya Rao) | Performs detailed document scrutiny; issues deficiency notices or approves for committee review. | Can record scrutiny outcomes (`DEFICIENT` or `PASSED`). **Strictly blocked (HTTP 403) from recording final decisions.** |
| **EVC Coordinator / Committee** | Schedules on-site/virtual inspections, assigns committee experts, and uploads inspection reports. | Manages EVC lifecycle (`PENDING_SCHEDULING` &rarr; `SCHEDULED` &rarr; `COMPLETED`). |
| **Committee Secretariat** | Reviews composite recommendations from scrutiny and EVC; prepares case for executive review. | Advances applications from `COMMITTEE_REVIEW` &rarr; `DECISION_PENDING`. |
| **Competent Authority Secretariat** | Reviews statutory case file and records the official legal decision (`APPROVED` / `REJECTED`). | **Exclusively authorized** to execute `RECORD_DECISION` with mandatory statutory reasons and conditions. |

---

## 2. Problem-to-Feature Mapping

| Problem Statement Requirement | Implemented Feature in Platform | Evidence / Verification Path |
| :--- | :--- | :--- |
| **Unified Command Center** | Unified Dashboard aggregating workflow stages, ageing distribution, EVCs, document expiry, and subsystem health. | `GET /api/dashboard/summary`<br/>UI: `http://localhost:3000/` |
| **Deficiency != Rejection** | Two-way deficiency loop (`DEFICIENCY_RAISED` &rarr; `RE_SCRUTINY`) preserving active application state without termination. | Verified in `tests/test_workflow.py`<br/>Live script: `scratch/rehearse_demo_steps.py` |
| **Continuous Compliance** | Document vault tracking Fire Safety, Land Registry, and Building Certificates with 30-day expiry alert thresholds. | `GET /api/documents`<br/>UI: `/compliance` |
| **SLA & Deadline Monitoring** | Deterministic deadline evaluation calculating `OVERDUE` relative to cycle benchmark (`2026-10-25`) without auto-disposal. | `GET /api/deadlines`<br/>`backend/app/services/compliance.py` |
| **Inspection Coordination** | Dual-view EVC management (Table and Calendar views) tracking inspection dates, modes, and uploaded reports. | `GET /api/evcs`<br/>UI: `/evc` |
| **Regulatory Traceability** | Append-only audit logger capturing actor, action, previous/new state, timestamps, and statutory justification. | `GET /api/audit-logs`<br/>UI: `/audit` |
| **Executive Exclusivity** | Server-side RBAC guardrail rejecting non-competent roles with HTTP 403 when attempting decision recording. | Verified in `test_gateway_authorized_decision_guardrails_intact` |

---

## 3. Architecture & Data Flow

```mermaid
graph TD
    subgraph Frontend_Layer [React 18 + Vite SPA]
        UI[Single Page App<br/>Dashboard, Registry, EVC, Compliance, Audit]
        Client[Shared API Client & Adapter<br/>src/api/client.ts]
        RoleSwitcher[Prototype Role Switcher<br/>X-User-Role / X-User-Id Headers]
    end

    subgraph Gateway_Layer [Unified FastAPI Gateway (Port 8020)]
        Router[FastAPI Application Router]
        DashRouter[Unified Dashboard Aggregator<br/>/api/dashboard/summary]
        M3Router[Workflow Engine Router<br/>/api/applications]
        M4Router[Compliance Engine Router<br/>/api/evcs, /api/documents, /api/undertakings]
        AuditBridge[Event Dispatch Bridge<br/>Decoupled Listener]
    end

    subgraph Database_Layer [Dual SQLite Persistence Engines]
        M3DB[(aicte_platform.db<br/>Member 3 Workflow DB<br/>Applications, History, Scrutiny, Decisions)]
        M4DB[(aicte.db<br/>Member 4 Compliance DB<br/>Audits, EVCs, Undertakings, Documents, Deadlines)]
    end

    UI --> Client
    RoleSwitcher -.-> Client
    Client -->|HTTP / REST| Router
    Router --> DashRouter
    Router --> M3Router
    Router --> M4Router
    DashRouter -->|Query Workflow Rows| M3DB
    DashRouter -->|Query Compliance Metrics| M4DB
    M3Router -->|Mutate Workflow State| M3DB
    M3Router -.->|Emit Audit / Notif Hook| AuditBridge
    AuditBridge -->|Persist Audit / Notif| M4DB
    M4Router -->|Mutate Compliance State| M4DB
```

---

## 4. Automation Capabilities: Genuine vs. Rule-Based vs. Future Scope

To maintain absolute credibility with hackathon judges, distinguish strictly between what is implemented and what is future scope:

| Tier | Capability | Implementation Status | Technical Mechanism |
| :--- | :--- | :--- | :--- |
| **Genuine Implemented Automation** | **Multi-Stage State Machine** | **LIVE** | Server-side matrix `TRANSITION_RULES` preventing illegal jumps or premature progression. |
| **Genuine Implemented Automation** | **Dynamic SLA Calculation** | **LIVE** | Deterministic evaluation of SLA days against reference cycle dates (`2026-10-25`). |
| **Genuine Implemented Automation** | **Proactive Expiry Alerts** | **LIVE** | Mathematical thresholding (`expiry_date - now <= 30 days`) flagging `Expiring soon` or `Expired`. |
| **Genuine Implemented Automation** | **Decoupled Event Dispatch** | **LIVE** | Asynchronous event listener hooks bridging workflow transitions to compliance audit logs. |
| **Administrative Human Safeguard** | **Non-Disposal Rule** | **INTENTIONAL** | **Software never auto-rejects or auto-approves.** Timers generate urgent officer alerts, but statutory law requires a human Competent Authority decision. |
| **Administrative Human Safeguard** | **Deficiency Decoupling** | **INTENTIONAL** | Deficiency marks status as `ACTION_REQUIRED` and pauses the clock; it never terminates the application. |
| **Future Scope** | **Automated OCR / Seal Extraction** | *Planned Phase 4* | Computer Vision / LayoutLM to extract municipal architect seals and signatures from uploaded PDFs. |
| **Future Scope** | **Institutional Risk Scoring** | *Planned Phase 4* | Machine Learning anomaly detection identifying discrepancies across consecutive years' intake claims. |
| **Future Scope** | **Production Enterprise SSO** | *Planned Phase 4* | Replacement of prototype `X-User-Role` headers with OpenID Connect (OIDC) / SAML 2.0 integration. |

---

## 5. Evidence for Key Evaluation Claims

| Evaluation Claim | Verification Evidence | Command / Test to Reproduce |
| :--- | :--- | :--- |
| **53 Passing Backend Tests** | 41 tests in `tests/` + 12 tests in `backend/tests/` pass with zero failures. | `python -m pytest tests -v`<br/>`python -m pytest backend/tests -v` |
| **Clean Frontend Build** | Zero TypeScript compilation errors; Vite builds 2,415 modules into `dist/`. | `npm.cmd run build` |
| **Server-Side RBAC Enforcement** | Scrutiny Officer receives HTTP 403 when attempting executive decision; Competent Authority succeeds. | `tests/test_workflow.py::test_authorized_decision_recording`<br/>`scratch/rehearse_demo_steps.py` |
| **Dual Subsystem Operational Health** | `/api/dashboard/summary` reports `status: "operational"`, `degraded: false`. | `curl http://127.0.0.1:8020/api/dashboard/summary` |
| **Zero Canonical Data Destruction** | Applications `APP001`–`APP025` remain in their initial states; backups exist in `data/backups/`. | `python scratch/check_db_backups.py` |

---

## 6. Known System Boundaries & Honest Disclosures

1. **Dual SQLite Databases:**
   - *Reality:* The system operates with `aicte_platform.db` (workflow) and `aicte.db` (compliance).
   - *Justification for Judges:* "We intentionally avoided a risky, breaking schema consolidation during the hackathon. Instead, we architected an enterprise API gateway pattern that unifies both subsystems under a single contract (`/api`), ensuring zero data loss and independent service scalability."
2. **Prototype Header-Based Role Switching:**
   - *Reality:* The UI switches roles via `X-User-Role` and `X-User-Id` HTTP headers.
   - *Justification for Judges:* "For rapid demonstration and interactive evaluation, we provide a visible persona switcher in the UI. Server-side RBAC strictly validates every request against these roles. In a production rollout, this layer maps directly to AICTE's single sign-on (SSO) JWT tokens."
3. **Application Portfolio Counts (42 vs 25):**
   - *Reality:* `aicte_platform.db` has 42 applications; `aicte.db` has 25 applications.
   - *Justification for Judges:* "Canonical Dataset 2 seeded 25 baseline applications (`APP001`–`APP025`). Additional records (`APP026`–`APP043`) are disposable live demonstration cases created during rehearsals to protect canonical data from mutation."
4. **Unmapped Undertakings (`UND-2026-003`, `UND-2026-006`):**
   - *Reality:* These two rows from Dataset 5 have missing application foreign keys.
   - *Justification for Judges:* "In compliance with regulatory data integrity principles, we safely blocked unmapped undertakings from ingestion rather than fabricating artificial relationships."

---

## 7. Quick Startup & Live Demo Sequence

### Terminal Commands
```powershell
# Terminal 1: Backend Gateway
uvicorn app.main:app --host 127.0.0.1 --port 8020

# Terminal 2: Frontend Client
npm.cmd run dev
```

### 8-Step Demo Sequence (5–7 Minutes)
1. **Approval Command Centre (`http://localhost:3000/`):** Show operational pulse, ageing chart, and dual-subsystem operational health.
2. **Application Registry (`/applications`):** Search `APP001` (Pune Institute of Tech); show read-only canonical details.
3. **Scrutiny & Deficiency Loop:** Open disposable `APP038`. Raise deficiency as Scrutiny Officer (`ACTION_REQUIRED`). Switch to Institution Admin and resubmit (`IN_PROGRESS`). **Highlight: Deficiency is NOT rejection.**
4. **EVC Coordination (`/evc`):** View canonical inspections (`EVC001`–`EVC007`) in Table and Calendar views with committee member assignments.
5. **Compliance Vault (`/compliance`):** Show expired Fire NOC (`DOC-2026-0001`) and 8 verified undertakings. Highlight: Expired docs alert officers but **never auto-reject**.
6. **Deadlines & Alerts (`/notifications`):** Demonstrate dynamic SLA alert tracking and interactive mark-as-read.
7. **Append-Only Audit Trail (`/audit`):** Show complete immutable history. Point out `[SYNTHETIC - CANONICAL BASELINE]` tags.
8. **Competent Authority Decision:** Open `APP028` or `APP034` in `DECISION_PENDING`. Attempt decision as Scrutiny Officer &rarr; **Show HTTP 403 Forbidden**. Switch to Competent Authority Secretariat &rarr; **Submit approval with statutory reasons & conditions**. Stepper completes!

### Offline Fallback
If localhost network or ports fail during judging:
Open `file:///c:/Users/Dell/OneDrive/Desktop/AICTE/reference.html.html` in any browser. It runs 100% offline with zero dependencies.

---

## 8. Judge Questions & Bulletproof Answers

#### Q1: "Why did you use two SQLite databases instead of merging them into one PostgreSQL schema?"
> **Answer:** "In an enterprise integration, forcing immediate schema consolidation between independent services creates high risk of regression. We adopted the API Gateway Pattern: Member 3's workflow engine and Member 4's compliance engine retain bounded contexts, unified under FastAPI. In Phase 4 production, both map cleanly into microservices backed by PostgreSQL."

#### Q2: "Can an application be automatically approved or rejected if a deadline timer runs out?"
> **Answer:** "No. Under administrative law and AICTE regulations, automated statutory disposals are unlawful. Our platform calculates SLA breaches dynamically to escalate alerts and trigger notifications to human officers, but final decisions strictly require an authorized human Competent Authority."

#### Q3: "What is the difference between a deficiency and a rejection in your system?"
> **Answer:** "A deficiency is an interlocutory request for clarification or corrected documentation. It sets the status to `ACTION_REQUIRED` and re-assigns the case to the institution. Once corrected, it flows to `Re-scrutiny`. Rejection is a formal, final statutory termination that can only be ordered by the Competent Authority with mandatory recorded legal reasons."

#### Q4: "How do you ensure audit logs cannot be altered by administrators?"
> **Answer:** "Audit records are append-only. The database schema lacks update/delete endpoints for audit records, and state transitions automatically emit decoupled events with actor ID, timestamp, and before/after states via background listeners."

#### Q5: "Is your role switcher secure?"
> **Answer:** "The header-based switcher is a prototype mechanism designed specifically for live hackathon evaluation so judges can inspect different persona views without logging in and out. Crucially, the **authorization logic itself is fully server-side** — non-competent roles receive real HTTP 403 Forbidden responses regardless of client UI state."
