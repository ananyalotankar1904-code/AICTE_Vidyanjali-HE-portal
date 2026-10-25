
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

# SIH26262 --- AICTE Approval Workflow Automation, Compliance Monitoring & Regulatory Compliance Management System

> **Project type:** Smart India Hackathon (SIH) prototype\
> **Development target:** Working localhost demonstration\
> **Project stage:** Implement the actual workflow management
> application alongside the existing BPMN simulator\
> **Team size:** 6 members\
> **Important:** This is a prototype, not an official AICTE system. Use
> synthetic demo records. Any unverified rules, deadlines, routes, or
> outcomes must be labelled as illustrative configuration.

------------------------------------------------------------------------

## 1. Read this first

This README is the shared source of truth for all six team members. Read
it before creating or modifying code.

The project is **one shared application**, not six separate
mini-projects. All modules must use the same repository, frontend,
backend, database, API contracts, identifiers, workflow stages, status
values, role definitions, audit mechanism, and notification mechanism.

The existing BPMN simulator demonstrates how the process is intended to
behave. The actual prototype must allow users to perform operational
actions, save records, validate transitions, and see resulting changes
in the dashboard. Do not confuse a visual simulation with persisted
application functionality.

### Non-negotiable rules

1.  Do not create a separate frontend, backend, database, or design
    system for your branch.
2.  Do not rename shared fields, statuses, stages, roles, endpoints, or
    identifiers without coordinating with the Integration Lead.
3.  Do not hard-code an official regulatory rule unless it has been
    verified against an authoritative source.
4.  Mark unverified routes, deadlines, and sample rules as
    **illustrative demo configuration**.
5.  The system must never automatically grant or reject a statutory
    application because a timer expired or a workflow stage completed.
6.  A competent, authorised human must record the official decision.
7.  A deficiency request is not the same as formal rejection. An overdue
    flag is not itself a decision.
8.  Keep a history of important state changes. Do not silently overwrite
    old evidence or audit events.
9.  Use synthetic data for the prototype. Do not put real institutional,
    applicant, or personal data in the repository.
10. Deliver working code and test it; do not submit only mockups, plans,
    or unconnected screens.

------------------------------------------------------------------------

## 2. Project overview

### Project title

**Integrated AICTE Approval Workflow Automation, Compliance Monitoring
and Regulatory Compliance Management System**

### Problem being addressed

Approval and compliance processes can involve multiple stages, actors,
documents, committees, visits, deadlines, corrections, and follow-up
obligations. When these activities are tracked across disconnected tools
or manually, it can be difficult to determine the current stage,
identify pending actions, monitor ageing and deadlines, preserve
document history, and understand who performed an action.

### Project objective

Build a coherent localhost prototype that centralises the tracking and
management of institutional application workflows and related compliance
obligations. The application should provide clear role-specific work
queues, controlled workflow transitions, evidence and document tracking,
deadline alerts, auditability, and dashboards.

### Expected outcome

A reviewer should be able to run the application locally and demonstrate
end-to-end scenarios such as:

-   an application moving through its configured route to a manually
    recorded official decision;
-   a scrutiny deficiency being issued, corrected, resubmitted, and
    re-scrutinised;
-   a deadline becoming due or overdue and producing an alert/escalation
    record;
-   an EVC being scheduled and its visit/report being tracked;
-   an undertaking being submitted and verified;
-   a document approaching expiry, being renewed, and retaining its
    prior version;
-   the audit history showing who did what and when;
-   the BPMN showcase illustrating the same workflow vocabulary and test
    cases.

### Scope boundary

This is a **demonstration prototype**, not a production-grade national
regulatory platform. Do not claim production security, legal compliance,
live integration with AICTE, verified official routing,
digital-signature validity, or automated legal interpretation unless
those capabilities are genuinely implemented and validated.

------------------------------------------------------------------------

## 3. Functional scope

### 3.1 Application intake and registration

-   Allow an institution/demo applicant to start and submit an
    application.
-   Capture a stable application identifier, application type/category,
    institution/demo identity, submission time, current stage, current
    status, and assigned route.
-   Perform basic form validation and required-field checks.
-   Distinguish basic technical validation from statutory scrutiny.
-   Register the application and record an audit event when submitted.
-   Allow filtering and searching by ID, type, stage, status, and other
    agreed fields.

### 3.2 Configurable workflow routing

-   Select a configured route using application type/category and
    verified configuration.
-   Do not assume every application passes through every stage.
-   Support routes that skip, add, or conditionally enter stages.
-   Keep route definitions/configuration separate from the code where
    feasible.
-   For demo routes that are not verified against the official handbook,
    display a clear "Illustrative demo route" label.
-   Record the selected route and the route/configuration version used
    for the case where practical.

### 3.3 Scrutiny and deficiencies

-   Provide a scrutiny work queue for authorised demo roles.
-   Allow an authorised reviewer to record a scrutiny outcome.
-   If evidence or information is deficient, record the deficiency
    reason, requested correction, issuing user, issue time, and response
    deadline if applicable.
-   Notify the institution/demo applicant that action is required.
-   Allow corrected information/evidence to be submitted.
-   Retain prior document/evidence versions instead of silently
    replacing them.
-   Route the case to re-scrutiny and record the review outcome.
-   Support repeated correction cycles only as allowed by the configured
    demo rules.
-   Do not treat a missing response or an overdue deadline as automatic
    formal rejection.

### 3.4 EVC lifecycle

-   Track EVC queue/assignment, scheduling, planned date, rescheduling,
    visit status, findings, report submission, and report
    review/acknowledgement.
-   Record responsible users and timestamps.
-   Make pending scheduling, delayed visits, and pending reports
    visible.
-   Support relevant exception cases such as rescheduling or a report
    requiring clarification.
-   Use only routes that apply to the configured application type.

### 3.5 Applicable committee review

-   Track a configured SAC/SHC or other applicable committee review
    where relevant.
-   Record review status, meeting/review metadata where appropriate,
    findings, and recommendations.
-   Distinguish a committee recommendation from the formal decision of
    the competent authority.
-   Do not send every application through a committee by default.

### 3.6 Official decision

-   Assemble/display the case information required by the authorised
    decision-maker.
-   Route the case to a competent-authority/authorised-official task.
-   Require an authorised human user to record the official outcome.
-   Store decision outcome, decision-maker, decision timestamp,
    rationale/reason, and conditions or related metadata where
    applicable.
-   Support configured outcomes such as approval/grant, conditional
    approval where applicable, non-approval/rejection, or further
    review/other permitted outcomes.
-   If formal signing or issuance is a separate step in the model,
    represent it as a separate human task.
-   Record the outcome in the audit trail and notify relevant users.
-   A timer, overdue flag, model prediction, dashboard metric, or
    completed prerequisite must never itself create the official
    decision.

### 3.7 Undertakings and compliance evidence

-   Track an obligation/undertaking, its due date, evidence submission,
    review status, reviewer, and verification outcome.
-   Support pending, submitted, needs-correction, verified, and other
    agreed statuses.
-   Allow a correction/resubmission loop where applicable.
-   Keep compliance obligations independently trackable; they may remain
    active after the main application reaches a terminal state.
-   Record evidence versions and audit events.

### 3.8 Document validity and renewal

-   Track document type, associated application/institution,
    issue/expiry dates when relevant, version, submission time, and
    review status.
-   Identify documents approaching expiry and documents past expiry.
-   Allow a replacement/renewal submission and reviewer verification.
-   Preserve prior versions and renewal history.
-   Treat expiry as a tracked condition/flag. Do not automatically
    impose a penalty, reject an application, or withdraw an approval
    merely because a date has passed.
-   Do not claim a document is legally valid simply because a file has
    been uploaded.

### 3.9 Deadlines, notifications, and escalation

-   Support deadlines for configured workflow tasks, deficiency
    responses, EVC activities, undertakings, document renewals, and
    other applicable follow-ups.
-   Track deadline date/time, related entity, owner/assignee, current
    condition, and notification/escalation history.
-   Provide upcoming, due, overdue, completed, and cancelled/obsolete
    deadline views as appropriate.
-   Send or simulate in-app notifications and escalation records.
-   Avoid duplicate notifications for the same event/rule/window.
-   Stop or cancel obsolete reminders after the underlying task is
    completed, withdrawn, or superseded.
-   Preserve notification history.
-   Escalation must notify or route work to an authorised role; it must
    not automatically decide the underlying statutory case.

### 3.10 Dashboards and reports

Provide role-relevant summaries such as:

-   total applications;
-   counts by stage and status;
-   pending scrutiny;
-   deficiency responses awaiting action;
-   EVCs pending/scheduled/completed;
-   committee reviews pending where applicable;
-   decisions awaiting authorised action;
-   upcoming and overdue deadlines;
-   pending undertakings;
-   documents nearing expiry or expired;
-   average or median stage age where meaningful;
-   recent audit activity.

Clearly label demo metrics and sample data. Do not present simulated
metrics as official AICTE statistics.

### 3.11 Role-based access and audit trail

-   Define the demo roles centrally.
-   The backend---not only the frontend---must validate permissions for
    protected actions.
-   Record significant events: application creation/submission, route
    selection, assignment, transition, deficiency issue/response, EVC
    changes, document/evidence changes, deadline/notification events,
    and official decision recording.
-   Audit events should include a stable event ID, actor, action/event
    type, entity type/ID, timestamp, and useful before/after or metadata
    fields where appropriate.
-   Do not allow ordinary users to edit or erase audit history through
    normal application endpoints.
-   If authentication is simplified for the demo, clearly label it
    **demo authentication** and do not claim it is production-ready.

### 3.12 Rejection/corrective-guidance USP --- future extension

The team may add a rejection-guidance feature after its scope and
verified content are finalised. Keep a clean extension point, but do not
delay core workflow functionality.

Potential flow:

1.  An authorised official records a formal rejection/non-approval and
    the reason.
2.  The system classifies or maps the reason using an approved, verified
    mapping.
3.  The system retrieves only supported guidance or permitted next
    steps.
4.  The interface explains the guidance and any applicable
    conditions/limitations.
5.  A follow-up or new application can be linked where permitted.

Do not invent remedies, guarantee approval, reverse an official
decision, or imply that every rejection can be appealed or corrected.
Guidance must not replace the authorised decision-maker.

------------------------------------------------------------------------

## 4. Workflow model and BPMN requirements

The BPMN artefacts and the implemented application must describe the
same process concepts. The BPMN is the process specification and
demonstration aid; the actual backend remains responsible for enforcing
transitions and saving state.

### 4.1 Master process outline

The master workflow is conditional. Not every application follows every
stage.

1.  Institution/demo applicant initiates an application and selects its
    type/category.
2.  The system loads the configured route, checklist, and applicable
    rules.
3.  The institution completes the form and uploads evidence.
4.  The system performs basic validation.
5.  If required information is missing, the applicant corrects the form
    and retries.
6.  The system registers the application ID, timestamp, and audit event.
7.  The system assigns the application to the appropriate configured
    queue/route.
8.  The applicable scrutiny and/or EVC process begins according to the
    route.
9.  An authorised scrutiny user reviews the case.
10. If deficient, the reviewer issues a deficiency request; the
    applicant corrects and resubmits; the case returns for re-scrutiny.
11. Where applicable, EVC work is scheduled, performed, and documented;
    the report is submitted and reviewed.
12. Where applicable, a committee reviews the case and records
    findings/recommendations.
13. The system assembles/routes the case file to the competent
    authority.
14. An authorised competent authority examines the case and records the
    official decision.
15. The system records the decision metadata, audit event, status, and
    notifications.
16. Applicable conditional obligations, undertakings, document renewal,
    appeal/review, or follow-up processes continue independently where
    relevant.
17. The deadline service monitors active deadlines and generates
    alerts/escalations according to configuration.
18. Dashboards and audit history expose current state and prior actions.

### 4.2 BPMN lanes and task types

Use clear pools/lanes. Recommended lanes include:

-   Institution / Applicant;
-   Application System / Workflow Service;
-   Scrutiny Officer;
-   EVC Team / Visitor;
-   Applicable Committee;
-   Competent Authority / Authorised Official;
-   Compliance / Document Reviewer;
-   Deadline / Notification Service.

If the institution is an external participant, represent it as a
separate pool and use **message flows** between pools. Sequence flows
remain inside a pool; do not connect sequence flows across separate
pools.

Use BPMN elements consistently:

-   **User Task:** a human must perform an action, such as completing an
    application, scrutinising evidence, recording a deficiency,
    scheduling/conducting an EVC, reviewing a committee case, verifying
    an undertaking, or recording the official decision.
-   **Service Task:** the system performs an operation, such as
    validating fields, registering an ID, selecting a configured route,
    recording a transition, generating a notification, or calculating
    deadline state.
-   **Exclusive Gateway (XOR):** exactly one configured path is
    selected, such as complete/deficient or which route applies.
-   **Parallel Gateway:** use only when work genuinely proceeds
    concurrently and the model defines how it joins.
-   **Timer Event:** represents a deadline, wait, or monitoring point. A
    timer can trigger a reminder/escalation path, not an automatic
    statutory approval/rejection.
-   **Message Events/Flows:** represent communication between separate
    pools/participants.
-   **Subprocess:** use for repeated or logically separate lifecycle
    sections such as deficiency correction, EVC, official decision,
    document renewal, and compliance verification.
-   **End Events:** distinguish relevant outcomes where helpful, without
    implying all routes share one mandatory path.

### 4.3 Official decision must be explicit

The competent-authority lane must visibly contain a **User Task** for
examining the case and a separate **User Task** for recording the
official decision. If required by the chosen model, formal
signing/issuance may be another human task.

The system can prepare the case file, validate required fields, store
the decision, and notify users. It must not autonomously decide the
statutory outcome.

### 4.4 Deficiency, rejection, appeal, and overdue are distinct

-   **Deficiency:** a reviewer asks for correction or additional
    information; the process may return to the applicant and then to
    re-scrutiny.
-   **Formal rejection/non-approval:** an authorised decision-maker
    records an official outcome.
-   **Appeal/review:** a separate conditional path, only if applicable
    and permitted by the configured rules.
-   **Overdue:** a deadline condition/flag that can trigger reminders or
    escalation; it is not a replacement for the application status and
    not an automatic decision.

### 4.5 Deadline and compliance lifecycles

Model deadline monitoring as a reusable service or event subprocess
rather than duplicating inconsistent timer logic in every stage. Model
undertaking and document-renewal lifecycles so that they can continue
after the main application is completed.

### 4.6 BPMN artefact requirements

Maintain the existing working showcase unless there is a concrete reason
to change it. The expected artefacts are:

-   `bpmn/aicte_approval_workflow.bpmn` --- BPMN 2.0 XML, with process
    elements and diagram interchange (DI) layout where supported.
-   `bpmn/aicte_bpmn_prototype_showcase.html` --- standalone interactive
    showcase/simulator, if that is the existing agreed filename.
-   The showcase should demonstrate the configured route, current step,
    task type, gateways/branches, event history, and resulting scenario.
-   Keep the BPMN XML valid and exportable/importable in a
    BPMN-compatible viewer where possible.
-   Use synthetic cases and clearly label illustrative route rules.
-   Keep the simulator separate from the production-like operational UI,
    but make it reachable from the main application if practical.
-   Share workflow names, stage names, status terminology, and scenario
    IDs across the BPMN showcase and the application.
-   Do not let the simulator become the only working part of the
    project.

### 4.7 Required demonstration scenarios

At minimum, the team should be able to demonstrate:

1.  **Successful configured route:** application submission, relevant
    checks/reviews, and manual official decision.
2.  **Deficiency loop:** scrutiny → deficiency issued → applicant
    correction/resubmission → re-scrutiny → workflow resumes.
3.  **Deadline escalation:** an active deadline becomes due/overdue and
    produces a visible alert/escalation record without automatically
    deciding the application.
4.  **Document expiry/renewal:** upcoming expiry → reminder →
    replacement/renewal submission → review → prior version retained.
5.  **EVC path:** EVC scheduled, rescheduled if applicable, visit/report
    recorded, report reviewed.
6.  **Compliance undertaking:** obligation created → evidence submitted
    → verified or correction requested.
7.  **Rejected/non-approved case:** official outcome recorded by an
    authorised human; optional guidance only if the extension has been
    verified and implemented.

------------------------------------------------------------------------

## 5. Status and stage conventions

The team must use shared enums/constants rather than inventing strings
independently.

### 5.1 Application status

Suggested high-level statuses:

-   `DRAFT`
-   `SUBMITTED`
-   `IN_PROGRESS`
-   `ACTION_REQUIRED`
-   `ON_HOLD`
-   `COMPLETED`
-   `REJECTED`
-   `WITHDRAWN`

These are prototype conventions, not a claim that they are official
AICTE status names. Confirm the final set before implementation.

Guidance:

-   `ACTION_REQUIRED` indicates an actor needs to respond or perform a
    requested action.
-   `ON_HOLD` must include a reason and should be used only where
    permitted by the configured process.
-   `COMPLETED` means the configured application workflow is complete;
    separate compliance obligations may remain active.
-   `REJECTED` is set only after an authorised human records the formal
    outcome.
-   `WITHDRAWN` is available only where the demo rules permit
    withdrawal.
-   `OVERDUE` should generally be represented as a deadline
    condition/flag, not as the application status.

### 5.2 Workflow stage

Possible stage identifiers include:

-   `INTAKE`
-   `VALIDATION`
-   `SCRUTINY`
-   `DEFICIENCY_PENDING`
-   `RE_SCRUTINY`
-   `EVC_PENDING`
-   `EVC_SCHEDULED`
-   `EVC_IN_PROGRESS`
-   `EVC_REPORT_REVIEW`
-   `COMMITTEE_REVIEW`
-   `DECISION_PENDING`
-   `DECISION_RECORDED`
-   `COMPLETED`

These are suggested internal identifiers. Configure stage applicability
by route. Do not assume every application uses every stage. The final
contract should define display labels and allowed transitions for each
stage.

### 5.3 Separate lifecycle statuses

EVC, undertaking, document, deadline, notification, and appeal/review
records should have their own lifecycle/status fields where necessary.
Do not overload the application status to represent all of these
independent processes.

------------------------------------------------------------------------

## 6. Recommended technology stack

Use the stack below unless the existing working prototype already has a
functioning implementation that would be expensive or risky to replace.
If changing a technology is necessary, coordinate it first.

### Frontend

-   **React + Vite + TypeScript** --- application interface and
    development server.
-   **Tailwind CSS** --- responsive styling and consistent design
    tokens.
-   **React Router** --- page navigation.
-   **React Hook Form + Zod** --- form state and client-side validation.
-   **Native `fetch`** initially, or Axios if the team agrees.
-   **Recharts** --- dashboard charts where useful.
-   **Lucide React** --- icons.
-   Shared typed API client and shared TypeScript types.

### Backend

-   **Python + FastAPI** --- REST API and backend logic.
-   **Pydantic** --- request/response validation.
-   **SQLAlchemy** --- database models and ORM.
-   **SQLite** --- local persistent database.
-   **Alembic** --- migrations if time permits; at minimum, use a
    controlled and repeatable schema-initialisation process.
-   **pytest** --- backend tests.
-   FastAPI OpenAPI/Swagger UI for API inspection.

### Collaboration and tooling

-   Git + one shared GitHub repository.
-   Feature branches and pull requests.
-   `.env.example` for configuration templates; never commit secrets.
-   A stable local run procedure documented in this README.
-   Frontend tests for critical interactions if time permits.
-   Keep a reproducible seed-data command.

### Avoid unnecessary complexity

For the three-day prototype window, avoid adding Docker, Redis, Celery,
microservices, a cloud database, or a full BPMN execution engine unless
already implemented and genuinely needed. A simple controlled
deadline-check command or demo trigger is acceptable if its behaviour is
explicit and tested.

### Authentication note

If implementing login, use a maintained password-hashing library. For a
demo-only role switcher, label it clearly as demo authentication and do
not present it as secure production identity management. Regardless of
the UI, backend actions must still validate role permissions.

------------------------------------------------------------------------

## 7. Shared repository structure

Use this as the starting point. Preserve existing working files and
adapt the structure carefully.

``` text
aicte-approval-platform/
├── frontend/
│   ├── src/
│   │   ├── components/          # reusable UI components
│   │   ├── layouts/             # application shell/navigation
│   │   ├── pages/                # route-level pages
│   │   ├── features/
│   │   │   ├── applications/
│   │   │   ├── scrutiny/
│   │   │   ├── evc/
│   │   │   ├── compliance/
│   │   │   ├── documents/
│   │   │   ├── notifications/
│   │   │   └── audit/
│   │   ├── api/                  # API client and endpoint functions
│   │   ├── types/                # shared interfaces/enums
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── api/                  # routers/endpoints
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/
│   │   │   ├── workflow.py
│   │   │   ├── deadlines.py
│   │   │   ├── notifications.py
│   │   │   └── audit.py
│   │   ├── seed/
│   │   ├── db.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── bpmn/
│   ├── aicte_approval_workflow.bpmn
│   └── aicte_bpmn_prototype_showcase.html
├── docs/
│   ├── api-contract.md
│   ├── architecture.md
│   ├── workflow-and-statuses.md
│   ├── test-scenarios.md
│   └── decisions-and-known-limitations.md
├── .gitignore
└── README.md
```

------------------------------------------------------------------------

## 8. Shared data model --- minimum design

The Integration Lead and backend developers must agree on exact names
and relationships before parallel implementation. The entities below
describe the minimum conceptual model; do not create duplicate versions
of the same entity in different modules.

### 8.1 Application

Suggested fields:

-   `id` --- stable UUID or agreed string identifier;
-   `application_number` --- human-readable demo identifier if needed;
-   `institution_id` or synthetic institution reference;
-   `application_type` / `application_category`;
-   `route_id` and optionally route/configuration version;
-   `status`;
-   `current_stage`;
-   `assigned_to` / queue metadata where applicable;
-   `submitted_at`, `created_at`, `updated_at`;
-   optional `completed_at`;
-   other fields agreed for the demo.

### 8.2 Workflow event/history

-   `id`;
-   `application_id`;
-   `from_stage`, `to_stage`;
-   `from_status`, `to_status`;
-   `action` / transition name;
-   `actor_id` and role;
-   `reason` or comments where relevant;
-   timestamp;
-   structured metadata as appropriate.

The history should make it possible to reconstruct the major path taken
by an application.

### 8.3 Deficiency / correction record

-   application reference;
-   issuing reviewer;
-   deficiency reason and requested correction;
-   issued timestamp;
-   response deadline if applicable;
-   current state;
-   response/submission reference;
-   re-scrutiny result and timestamps.

Keep the deficiency record separate from the official decision record.

### 8.4 EVC record

-   application reference;
-   assigned team/user;
-   scheduled date/time;
-   status;
-   rescheduling metadata/reason;
-   visit date;
-   findings/report reference;
-   report submitted/reviewed timestamps;
-   review outcome and actor.

### 8.5 Undertaking / compliance obligation

-   linked application/institution;
-   obligation type and description;
-   source/rule reference or clearly marked demo configuration;
-   due date;
-   status;
-   submitted evidence reference/version;
-   reviewer and verification outcome;
-   created/updated timestamps.

### 8.6 Document

-   document ID;
-   linked application/institution/compliance obligation;
-   document type;
-   file metadata or local storage reference;
-   version number;
-   issue date/expiry date when relevant;
-   submitted timestamp;
-   review status;
-   superseded/replaced reference where appropriate;
-   created by and timestamps.

Do not store sensitive files in a public repository. For a demo, use
synthetic placeholder documents or safe local test files.

### 8.7 Deadline

-   deadline ID;
-   linked entity type and ID;
-   deadline type;
-   due timestamp;
-   owner/assignee;
-   status/condition;
-   escalation policy/configuration reference;
-   last evaluated timestamp;
-   completed/cancelled timestamps when applicable.

### 8.8 Notification

-   notification ID;
-   recipient/role;
-   related entity;
-   notification type;
-   message;
-   created timestamp;
-   read timestamp/state;
-   deduplication key or equivalent;
-   delivery channel (in-app/demo).

### 8.9 Audit event

-   event ID;
-   actor and role;
-   action/event type;
-   entity type and ID;
-   timestamp;
-   before/after values or metadata where useful;
-   reason/comment where applicable.

### 8.10 Official decision

-   application reference;
-   outcome;
-   authorised decision-maker;
-   decision timestamp;
-   reason/rationale;
-   conditions or follow-up obligations where relevant;
-   related evidence/case-file references;
-   signing/issuance metadata if modelled separately.

Use a separate decision record or a clearly structured event/model; do
not let ordinary stage transitions implicitly manufacture an official
decision.

### Data-model implementation rules

-   Use foreign keys and relationships where appropriate.
-   Use a consistent timestamp policy and ISO 8601 in API payloads.
-   Define enums/constants centrally.
-   Use database transactions for a state transition and its associated
    history/audit writes.
-   Validate input on the backend even if the frontend validates it too.
-   Avoid duplicating current status in multiple places without a clear
    source of truth.
-   Keep the initial model practical; do not over-engineer for
    hypothetical production needs.

------------------------------------------------------------------------

## 9. API contract and integration rules

All API routes use the `/api` prefix unless the team explicitly agrees
otherwise.

### 9.1 Minimum endpoints

  --------------------------------------------------------------------------------------------------
  Method            Endpoint                              Purpose                  Primary owner
  ----------------- ------------------------------------- ------------------------ -----------------
  `GET`             `/api/dashboard/summary`              Counts and summary       Members 3 + 4,
                                                          metrics                  coordinated by 5

  `GET`             `/api/applications`                   List/filter applications Member 3

  `POST`            `/api/applications`                   Create/submit            Member 3
                                                          application              

  `GET`             `/api/applications/{id}`              Application detail       Member 3

  `POST`            `/api/applications/{id}/transition`   Request a permitted      Member 3
                                                          workflow transition      

  `GET`             `/api/applications/{id}/history`      Workflow history         Member 3

  `GET`             `/api/evcs`                           List EVC records         Member 4

  `POST`            `/api/evcs`                           Create/schedule an EVC   Member 4
                                                          record                   

  `GET`             `/api/undertakings`                   List compliance          Member 4
                                                          obligations              

  `POST`            `/api/undertakings`                   Create a demo            Member 4
                                                          undertaking/obligation   

  `GET`             `/api/documents`                      List document records    Member 4

  `POST`            `/api/documents`                      Register a               Member 4
                                                          document/renewal         
                                                          submission               

  `GET`             `/api/notifications`                  List notifications       Member 4

  `GET`             `/api/audit-logs`                     List permitted audit     Shared service /
                                                          history                  Members 3 + 4
  --------------------------------------------------------------------------------------------------

Additional endpoints may be required for assignments, deficiency
responses, decision records, document versions, notification read state,
deadline checks, or individual record details. Add them to
`docs/api-contract.md` before independently implementing both sides.

### 9.2 Example transition request

The exact schema must be frozen by the backend team, but a request could
follow this pattern:

``` json
{
  "action": "ISSUE_DEFICIENCY",
  "reason": "Illustrative demo deficiency",
  "comment": "Please submit the missing evidence.",
  "metadata": {}
}
```

The server must verify that the requested action is permitted from the
current state and that the actor has the required role. Do not let the
frontend send arbitrary `to_status` values and have the server accept
them without transition validation.

### 9.3 Example error response

Use one consistent error format. For example:

``` json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "This action is not permitted from the current workflow stage.",
    "details": {}
  }
}
```

The exact error schema can vary, but all members must use the agreed
contract.

### 9.4 API rules

-   Return appropriate HTTP status codes.
-   Validate request and response shapes.
-   Use pagination/filtering for lists if needed.
-   Return consistent date/time formats.
-   Keep business rules in backend services, not duplicated in UI
    components.
-   Do not return fake success from a frontend mock when the real
    endpoint is expected.
-   Display loading, empty, validation-error, API-error, and success
    states.
-   Use FastAPI OpenAPI docs to inspect actual schemas.
-   Document every changed endpoint or field in `docs/api-contract.md`.

------------------------------------------------------------------------

## 10. Workflow transition service

The backend must provide one central place to validate and perform
workflow transitions. Individual modules should call it rather than
independently changing application status.

The shared transition service should:

1.  Load the application and current workflow state.
2.  Confirm that the requested action exists for that state/route.
3.  Confirm the actor has the required role/permission.
4.  Validate required data for the action.
5.  Apply the configured state/stage change.
6.  Create the workflow-history record.
7.  Create the audit event.
8.  Create any relevant notification/deadline updates.
9.  Commit related changes consistently in a database transaction.
10. Return the updated application and relevant event details.

Reject invalid transitions with a clear error and leave the record
unchanged.

Examples of actions that may be configured include `SUBMIT_APPLICATION`,
`ASSIGN_REVIEWER`, `COMPLETE_SCRUTINY`, `ISSUE_DEFICIENCY`,
`SUBMIT_CORRECTION`, `COMPLETE_RE_SCRUTINY`, `SCHEDULE_EVC`,
`RECORD_EVC_REPORT`, `SUBMIT_FOR_DECISION`, `RECORD_OFFICIAL_DECISION`,
and `COMPLETE_WORKFLOW`. Final action names must be agreed and used
consistently by the frontend, backend, tests, and simulator.

Do not let a frontend page directly set `status = "APPROVED"` or
equivalent. Official outcomes must go through the authorised decision
workflow.

------------------------------------------------------------------------

## 11. Deadline, notification, and audit service rules

### Deadline service

-   Use one shared deadline evaluation function/service.
-   Make deadline evaluation deterministic and testable with a supplied
    reference time.
-   Do not rely on a permanently running background worker for the
    prototype.
-   It is acceptable to trigger a deadline check manually or through a
    lightweight local mechanism for the demo.
-   Separate the underlying task state from its deadline condition.
-   Do not treat an overdue deadline as proof of non-compliance or as an
    automatic legal outcome.
-   Ensure completed/cancelled/superseded tasks stop generating
    reminders.

### Notifications

-   Store notification records so that the dashboard can show them.
-   Define a stable deduplication strategy.
-   Record what triggered the notification and when.
-   Use in-app/demo notifications if email/SMS integration is outside
    scope.
-   Make notification generation testable without sending external
    messages.

### Audit

-   Write audit events from shared backend services.
-   Include actor, action, entity, timestamp, and useful context.
-   Capture failed/denied attempts if useful and safe, without leaking
    secrets.
-   Keep audit history separate from ordinary user-editable notes.
-   Ensure workflow updates and their corresponding audit/history writes
    do not diverge on a partial failure.

------------------------------------------------------------------------

## 12. Frontend implementation standards

### Design

-   Use a professional, accessible, institutional/government-portal
    visual style.
-   Establish shared typography, spacing, colours, borders, status
    badges, table patterns, form fields, buttons, cards, dialogs, and
    empty states.
-   Prefer a consistent shared layout over page-by-page visual
    improvisation.
-   Keep navigation labels and status labels consistent across pages.
-   Ensure layouts work at typical laptop and projector sizes; support
    smaller widths where practical.

### Usability

-   Every primary button must perform a real action or be explicitly
    disabled with an explanation.
-   Use confirmation dialogs for consequential actions.
-   Show success/error feedback after API calls.
-   Avoid silently discarding form edits.
-   Include loading, empty, error, and retry states.
-   Use accessible labels and sensible keyboard navigation.
-   Use date/time displays consistently.
-   Do not imply that a demo login is production authentication.

### Suggested pages

-   Dashboard;
-   Applications list;
-   Application detail and timeline;
-   New application form;
-   Scrutiny queue/detail;
-   Deficiency request and correction/resubmission;
-   EVC queue and schedule/report details;
-   Committee review where applicable;
-   Decision-pending queue and official decision entry;
-   Compliance/undertakings;
-   Documents and renewal;
-   Deadlines and notifications;
-   Audit history;
-   BPMN showcase/simulator;
-   About/demo limitations page if useful.

Not every page needs to be equally elaborate. Prioritise the end-to-end
scenarios and the pages needed to demonstrate them.

------------------------------------------------------------------------

## 13. Roles and ownership

### Member 1 --- Frontend Lead

**Owns:** main dashboard, application list/detail views, shared
application shell, reusable UI components, design tokens, common
navigation, frontend consistency.

**Must coordinate with:** Member 2 on shared components; Member 5 on API
contracts and integration.

**Must not:** create a separate frontend architecture or independently
rename backend fields.

**Handover checklist:** - pages run locally; - reusable components are
documented; - screens use shared types and API client; -
loading/error/empty states exist; - API assumptions are listed; - no
unrelated member files are overwritten.

### Member 2 --- Frontend Workflow & Compliance

**Owns:** scrutiny, deficiency, resubmission, EVC, committee review
where applicable, undertakings, documents, renewal, deadlines,
notifications, and audit screens.

**Must coordinate with:** Member 1 for visual components; Members 3 and
4 for API schemas; Member 5 for integration.

**Must not:** implement business-rule enforcement only in the frontend
or fabricate API responses as if persisted.

**Handover checklist:** - each screen maps to an agreed
endpoint/action; - form validation and error states work; - successful
actions refresh the relevant data; - permissions/disabled actions are
reflected in the UI; - assumptions and missing endpoints are documented.

### Member 3 --- Backend Workflow Developer

**Owns:** application CRUD, workflow configuration, route selection,
allowed transitions, scrutiny, deficiencies, correction/resubmission,
re-scrutiny, official decision recording, application history, and
related APIs.

**Must coordinate with:** Member 4 on shared entities/services and
Member 5 on the data/API contract.

**Must not:** let arbitrary client-provided statuses bypass transition
validation or create automatic official decisions.

**Handover checklist:** - endpoints match `docs/api-contract.md`; -
schemas and enums are shared and stable; - transition rules are enforced
server-side; - state/history/audit writes are consistent; - tests cover
valid and invalid transitions; - seed data demonstrates multiple routes
and outcomes.

### Member 4 --- Backend Compliance Developer

**Owns:** EVC records/scheduling, undertaking lifecycle, document
metadata/versioning/expiry/renewal, deadlines, notifications, escalation
records, and supporting dashboard metrics.

**Must coordinate with:** Member 3 on shared application/entity
relationships and shared services; Member 5 on integration.

**Must not:** duplicate the application/workflow model or implement a
separate notification/audit mechanism.

**Handover checklist:** - entities use the agreed IDs and
relationships; - endpoints match the API contract; - deadline and expiry
logic are testable; - reminders do not duplicate or continue after
completion; - document versions are retained; - tests cover
rescheduling, expiry, renewal, and escalation.

### Member 5 --- Integration Lead

**Owns:** repository coordination, shared contract, common enums/types,
branch integration, environment/run instructions, cross-module testing,
BPMN/prototype alignment, stable demo build, and final README.

**Must coordinate with:** all members, especially Members 3 and 4 for
the data model/API contract and Members 1 and 2 for frontend
integration.

**Must not:** allow parallel branches to silently diverge on IDs,
endpoint paths, field names, status values, or transition names.

**Handover checklist:** - one clean clone can be set up from
instructions; - frontend and backend communicate locally; - database and
seed data initialise reliably; - main scenarios pass end-to-end; - BPMN
terminology aligns with implemented transitions; - known limitations are
recorded; - a stable demo branch/commit is identified.

### Member 6 --- Research, Documentation & Demo

**Owns:** abstract, project description/report, literature review and
references, SIH presentation, diagrams, screenshots, test evidence, demo
script, and video.

**Must coordinate with:** developers to ensure claims match implemented
functionality; Member 5 for final architecture and screenshots.

**Must not:** claim unimplemented functionality, unverified official
routes, or simulated metrics are live/official capabilities.

**Handover checklist:** - report explains problem, objective,
architecture, workflow, features, results, limitations, and future
scope; - sources/references are organised; - 6--7 slide SIH Idea
Template deck is ready; - diagrams match the actual implementation; -
test scenarios/results are recorded; - demo script is repeatable; -
screenshots contain only synthetic data.

------------------------------------------------------------------------

## 14. Git and collaboration workflow

### Repository rules

-   Use one shared repository.
-   Protect the integration/main branch from unreviewed changes where
    possible.
-   Each member works on a feature branch.
-   Merge through a pull request or a reviewed merge.
-   Pull the latest integration branch before starting a new task.
-   Never commit local databases, secrets, real applicant data, build
    artefacts, or large temporary files.
-   Keep `.gitignore` updated.

### Suggested branches

``` text
main
integration
feature/frontend-dashboard
feature/frontend-workflow-compliance
feature/backend-workflow
feature/backend-compliance
feature/docs-demo
```

The Integration Lead may adjust names, but announce the convention to
everyone.

### Pull request checklist

Before merging, the contributor should confirm:

-   [ ] The module runs locally.
-   [ ] Changed files and behaviour are described.
-   [ ] API/data-contract changes are documented.
-   [ ] Tests pass or known failures are clearly listed.
-   [ ] No secrets or real personal data are included.
-   [ ] No unrelated files are overwritten.
-   [ ] Status/stage/role names match the shared contract.
-   [ ] Error and empty states are handled.
-   [ ] Any new demo rules are labelled illustrative unless verified.
-   [ ] Integration instructions are included.

### Shared files requiring coordination

Do not independently change these without notifying the Integration
Lead:

-   `docs/api-contract.md`
-   shared TypeScript interfaces/enums;
-   backend status/stage/action enums;
-   SQLAlchemy entities shared by multiple modules;
-   database initialisation/migration files;
-   workflow transition service;
-   audit and notification services;
-   application route definitions;
-   BPMN stage/transition vocabulary;
-   root README and run scripts.

------------------------------------------------------------------------

## 15. Local setup and run instructions

These instructions are a baseline. Exact commands may be adjusted to the
repository and operating system. The final team must test the actual
commands and update this section before handover.

### Prerequisites

Install:

-   a current supported Node.js LTS release and npm;
-   Python 3.11 or another version agreed by the team;
-   Git;
-   a code editor such as VS Code.

Check installations:

``` bash
node --version
npm --version
python --version
git --version
```

### Clone the repository

``` bash
git clone <SHARED_REPOSITORY_URL>
cd aicte-approval-platform
git checkout integration
```

Replace `<SHARED_REPOSITORY_URL>` with the team's actual repository URL.
Do not invent or commit a placeholder URL as if it were real.

### Backend setup

From the repository root:

``` bash
cd backend
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

``` powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

``` bat
.venv\Scripts\activate.bat
```

**macOS/Linux**

``` bash
source .venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Initialise the database using the project's agreed command. Examples
might be a migration command or a seed script, but **the team must
implement and document the real command**. Do not assume a command
exists until it has been added.

Start the API using the actual application entry point (configured on port 8005 to avoid collisions):

``` bash
uvicorn app.main:app --reload --port 8005
```
or:
``` bash
python -m app.main
```

Open the FastAPI documentation in a browser at:

``` text
http://127.0.0.1:8005/docs
```

Port is configurable via the `PORT` variable in `backend/.env`.

### Frontend setup

Open a second terminal from the repository root:

``` bash
cd frontend
npm install
```

Create a local environment file from `.env.example` if the project uses
one. The API base URL should point to the locally running backend, using
the agreed environment-variable name.

Start the development server:

``` bash
npm run dev
```

Use the local URL printed by Vite in the terminal. Do not assume the
port if Vite selects a different one.

### BPMN showcase

Open the existing standalone HTML showcase directly in a browser, or use
the route/integration method already chosen by the team. Verify that the
BPMN XML and HTML file are committed at the agreed paths. The showcase
should work with synthetic scenarios and should not require a cloud
service unless that dependency is explicitly documented.

### First-run verification

-   [ ] Backend starts without import errors.
-   [ ] Database initialises from a clean state.
-   [ ] Seed command creates repeatable synthetic demo records.
-   [ ] `/docs` loads and lists expected endpoints.
-   [ ] Frontend starts without build/type errors.
-   [ ] Frontend can reach the backend.
-   [ ] Dashboard data comes from the API, not only hard-coded
    placeholders.
-   [ ] A workflow action changes persistent state and creates
    history/audit records.
-   [ ] Restarting the backend does not erase persisted records
    unexpectedly.
-   [ ] BPMN showcase opens and demonstrates the agreed scenarios.

------------------------------------------------------------------------

## 16. Seed data and demo safety

Seed data is essential for a three-day prototype. Create a small,
repeatable dataset that covers different stages and exception cases.

Recommended synthetic examples:

-   an application at intake/draft;
-   an application submitted and awaiting scrutiny;
-   an application with a pending deficiency response;
-   an application returned for re-scrutiny;
-   an application with EVC scheduled;
-   an application awaiting an applicable committee review;
-   an application awaiting an authorised decision;
-   a completed application with a manually recorded decision;
-   a formally rejected/non-approved example with a recorded authorised
    reason;
-   an undertaking awaiting evidence;
-   an undertaking awaiting verification;
-   a document approaching expiry;
-   a document past expiry with renewal pending;
-   an overdue deadline with a visible escalation record;
-   a case with several workflow-history and audit events.

Use fictional institutions, fictional names, and clearly synthetic
identifiers. Ensure the seed process can be run repeatedly without
creating duplicate records unintentionally. Document whether reseeding
resets the local demo database.

Never present seeded data as live AICTE records or official statistics.

------------------------------------------------------------------------

## 17. Testing requirements

Tests should cover business rules and end-to-end behaviour, not only
whether pages render.

### Backend tests

At minimum, test:

-   application creation and required-field validation;
-   configured route selection;
-   valid stage transitions;
-   invalid transitions are rejected;
-   role permission checks for restricted actions;
-   deficiency issue, correction submission, and re-scrutiny;
-   authorised decision recording;
-   unauthorised decision attempts are rejected;
-   deadline due/overdue calculation using a controlled reference time;
-   reminder deduplication;
-   completed/cancelled tasks no longer generate reminders;
-   EVC scheduling/rescheduling;
-   document expiry and renewal/version history;
-   undertaking evidence submission and verification;
-   audit/history creation for key actions;
-   dashboard counts match stored data.

### Frontend tests/manual checks

At minimum, verify:

-   dashboard renders returned API data;
-   list filters and navigation work;
-   forms show validation errors;
-   loading, empty, API-error, and success states work;
-   a permitted action updates the visible record;
-   an invalid action shows a clear error;
-   role-restricted controls are disabled/hidden appropriately;
-   date and status labels are consistent;
-   no button is decorative while appearing functional.

### End-to-end acceptance scenarios

**Scenario A --- Successful route** 1. Create/submit a synthetic
application. 2. Confirm its ID, route, stage, and status. 3. Complete
the applicable configured review steps. 4. Route it to the competent
authority. 5. Record an official outcome using an authorised demo role.
6. Confirm status, history, audit event, notification, and dashboard
counts update.

**Scenario B --- Deficiency cycle** 1. Submit an application. 2. Issue a
deficiency from the scrutiny task. 3. Confirm the applicant sees the
action request and deadline if configured. 4. Submit corrected evidence.
5. Confirm the previous evidence version remains available. 6.
Re-scrutinise and continue the configured route.

**Scenario C --- Deadline escalation** 1. Create a deadline in the past
or use a controlled test clock. 2. Run the deadline evaluation. 3.
Confirm an overdue condition and notification/escalation record are
created. 4. Confirm the application has not been automatically approved
or rejected. 5. Complete/cancel the underlying task and confirm future
reminders stop.

**Scenario D --- Document renewal** 1. Seed a document nearing expiry.
2. Evaluate its expiry condition and show the reminder. 3. Submit a
replacement/renewal record. 4. Verify the new document. 5. Confirm both
old and new versions and their relationships remain visible.

**Scenario E --- EVC and report** 1. Create an EVC record for a route
that requires it. 2. Schedule or reschedule it. 3. Record visit/report
details. 4. Review the report. 5. Confirm queue counts, audit history,
and application progression update appropriately.

**Scenario F --- Undertaking** 1. Create an obligation with an
illustrative or verified source label. 2. Submit evidence. 3. Request
correction or verify it. 4. Confirm the lifecycle and audit events are
visible.

### Final acceptance criteria

The prototype is ready for demonstration when:

-   [ ] It runs from a clean clone using documented steps.
-   [ ] Frontend and backend are integrated.
-   [ ] Database records persist locally.
-   [ ] Shared IDs, statuses, stages, roles, and action names are
    consistent.
-   [ ] At least the core success and deficiency scenarios work
    end-to-end.
-   [ ] Deadline and document-renewal scenarios are demonstrable.
-   [ ] Official decision entry is a restricted human action.
-   [ ] Invalid transitions are rejected by the backend.
-   [ ] History/audit records are created for key actions.
-   [ ] Dashboard counts reflect actual seeded/stored data.
-   [ ] BPMN showcase uses consistent workflow terminology and required
    branches.
-   [ ] Demo data is synthetic and illustrative rules are labelled.
-   [ ] Known limitations and unimplemented features are documented.

------------------------------------------------------------------------

## 18. Three-day priority plan

The exact timing may change, but use this order to reduce integration
risk.

### Phase 1 --- Contract and skeleton

-   Confirm repository and branch names.
-   Freeze shared enums, roles, core entity fields, and API
    request/response schemas.
-   Create frontend/backend skeletons and database initialisation.
-   Verify a simple frontend-to-backend request.
-   Preserve the existing BPMN showcase.

**Exit condition:** all members can run the project and understand the
shared contract.

### Phase 2 --- Core workflow

-   Implement application registration/list/detail.
-   Implement backend transition validation and history/audit writes.
-   Implement scrutiny/deficiency/resubmission/re-scrutiny.
-   Build dashboard and core application screens.
-   Add synthetic seed data.

**Exit condition:** the main application path and deficiency loop work
end-to-end.

### Phase 3 --- Compliance and deadlines

-   Implement EVC records.
-   Implement undertakings and evidence verification.
-   Implement document expiry/renewal/versioning.
-   Implement deadline evaluation, notifications, and escalation
    records.
-   Connect operational screens and dashboard metrics.

**Exit condition:** the core compliance and deadline scenarios are
demonstrable.

### Phase 4 --- Integration and demo polish

-   Run end-to-end scenarios from a clean start.
-   Fix API mismatches and data inconsistencies.
-   Validate the BPMN XML and simulator paths.
-   Collect screenshots and update the report/PPT.
-   Record the demo and document known limitations.

**Exit condition:** one stable local build demonstrates the agreed
scenarios without manual code edits during the demo.

### Prioritisation rule

If time becomes short, prefer a smaller, integrated, testable flow over
a larger set of disconnected screens. Do not sacrifice the authorised
human-decision boundary, backend transition validation, persistent
records, or auditability to add decorative features.

------------------------------------------------------------------------

## 19. Documentation and final deliverables

The final repository should include:

-   [ ] This root `README.md`, updated with tested commands.
-   [ ] `docs/api-contract.md` --- endpoint schemas, examples, error
    format, shared enums.
-   [ ] `docs/architecture.md` --- frontend/backend/database
    architecture and data flow.
-   [ ] `docs/workflow-and-statuses.md` --- stages, statuses, roles,
    allowed transitions, route configuration.
-   [ ] `docs/test-scenarios.md` --- repeatable steps and actual test
    results.
-   [ ] `docs/decisions-and-known-limitations.md` --- design decisions,
    assumptions, limitations.
-   [ ] BPMN 2.0 XML and the working simulator/showcase.
-   [ ] Backend tests and a repeatable seed-data command.
-   [ ] Screenshots from the functioning application.
-   [ ] Project abstract and detailed description/report.
-   [ ] Literature review and reference list.
-   [ ] 6--7 slide SIH Idea Template presentation.
-   [ ] Demo script/video and recorded test evidence.
-   [ ] Clear setup instructions that work from a clean clone.

Documentation must distinguish between: - implemented and tested
functionality; - implemented but not fully tested functionality; -
illustrative demo behaviour; - planned/future functionality.

------------------------------------------------------------------------

## 20. Known limitations to disclose honestly

Unless actually implemented and validated, do not claim:

-   live integration with AICTE systems or portals;
-   official, complete coverage of every application type or route;
-   production-grade authentication/authorisation;
-   legal validity of uploaded documents;
-   real email/SMS delivery;
-   automated statutory approval/rejection;
-   a legally authoritative interpretation of regulatory text;
-   production-scale performance, security, availability, or audit
    compliance;
-   a full BPMN execution engine merely because a BPMN diagram/simulator
    exists.

These limitations do not make the prototype weak. A clear, working,
auditable demonstration is better than unsupported claims.

------------------------------------------------------------------------

## 21. Official-rule and source discipline

The team has an uploaded **AICTE Approval Process Handbook (APH)
2024--2027** and related project research files. Use the authoritative
handbook and verified sources when implementing regulatory routes,
deadlines, role permissions, obligations, or decision outcomes.

-   Cite the relevant handbook section/clause/table in project
    documentation where a rule is implemented.
-   Record the source and verification status for configurable rules.
-   If a rule cannot be confirmed within the available time, mark it as
    illustrative and keep it configurable.
-   Do not silently reconcile conflicting sources; flag the conflict for
    review.
-   Literature review papers can justify design choices but should not
    be treated as proof of an official AICTE rule.
-   Do not claim a rule is official just because it appears in a
    generated BPMN scenario or seed dataset.

------------------------------------------------------------------------

## 22. Final message to every member

Your task is to deliver your assigned module as a working part of the
shared prototype. Before coding, read the common brief, confirm your
dependencies, and check the current API contract. When handing work
over, provide the changed files, run instructions, endpoints/actions
added, test results, assumptions, and known issues.

**The success criterion is not six individually impressive branches. It
is one coherent application in which the modules work together, state
changes are persisted and validated, deadlines and compliance are
traceable, official decisions remain under authorised human control, and
the BPMN showcase matches the implemented workflow.**

