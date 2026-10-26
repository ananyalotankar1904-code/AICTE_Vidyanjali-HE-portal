# SIH26262 — Live Demo Runbook (Smart India Hackathon)

**System:** AICTE Approval Workflow Automation & Regulatory Compliance Monitoring Platform  
**Target Audience:** SIH Presentation Team / Presenters  
**Audience Prerequisites:** Basic browser operation; no backend development experience needed.  

---

## 1. Quick Launch (3-Minute Setup)

Open two PowerShell terminal windows in the project root directory (`c:\Users\Dell\OneDrive\Desktop\AICTE`):

### Terminal 1: Backend Gateway (FastAPI)
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8020
```
- **Verification:** Open `http://127.0.0.1:8020/health` in your browser.
- **Expected Output:** `{"status":"healthy","service":"AICTE Approval & Regulatory Compliance Platform","workflow_engine":"operational","compliance_engine":"operational"}`

### Terminal 2: Frontend Application (React + Vite)
```powershell
npm.cmd run dev
```
- **Verification:** Open `http://localhost:3000/` in Google Chrome or Microsoft Edge.
- **Expected Output:** Approval Command Centre dashboard appears with warm Indian government palette (gold/saffron accents), zero error banners.

### Terminal 3 (Fallback Only): Offline BPMN Showcase
If there is any network, port, or server issue during judging, double-click or open directly:
```
file:///c:/Users/Dell/OneDrive/Desktop/AICTE/reference.html.html
```

---

## 2. Safe Record IDs Cheat Sheet

> [!IMPORTANT]
> **DO NOT** approve or reject canonical applications `APP001` through `APP025`. Use separate, dedicated disposable records for each stage so completed applications are never reused for scrutiny.

| Demo Stage | Dedicated Safe Record ID | Institution / Description | State in Database | Expected Demo Action |
| :--- | :--- | :--- | :--- | :--- |
| **Search & Intake Inspection** | `APP001` | Pune Institute of Technology (Canonical) | `SUBMITTED` / View-Only | Search, filter, inspect details (read-only). |
| **Deficiency Issuance** | `APP038` | Sahyadri College of Eng. (Disposable) | `INITIAL_SCRUTINY` (`IN_PROGRESS`) | As Scrutiny Officer, click "Return for Deficiency". |
| **Institution Resubmission** | `APP039` | Sahyadri College of Eng. (Disposable) | `DEFICIENCY_RAISED` (`ACTION_REQUIRED`) | As Institution Admin, click "Resubmit Correction". |
| **EVC Inspection Scheduling** | `EVC001` | Physical Visit · Planned 2026-10-29 | `PENDING_SCHEDULING` | View in List & Calendar view; assign team. |
| **Document Expiry Warning** | `DOC-2026-0001` | Fire Safety Certificate (Expired) | `EXPIRED` | Show red expiry alert; verify non-disposal. |
| **Deadlines & Notifications** | `DDL-2026-001` / `NOTIF-2026-001` | Land Registry NOC SLA reminder | `OVERDUE` (Alert only) | Demonstrate dynamic SLA alert & mark read. |
| **Authority Decision (403 & 200)** | `APP028` or `APP034` | Pune Inst. of Tech (Disposable) | `DECISION_PENDING` (`IN_PROGRESS`) | Demonstrate 403 on Scrutiny Officer, then approve as CA Secretariat. |
| **Completed Decision Certificate**| `APP041` or `APP042` | Sahyadri College of Eng. (Disposable) | `COMPLETED` (`COMPLETED`) | Show immutable approved certificate, reasons, & conditions. |
| **Fresh Cycle Repeat** | Click "Start New Intake" | Register fresh demo case (e.g. `APP044`) | `SUBMITTED` &rarr; `INITIAL_SCRUTINY` | Creates fresh case in 5 seconds if judges ask to re-run from scratch. |

---

## 3. The 8-Step Demo Presentation Script (5–7 Minutes)

### Step 1: Approval Command Centre (Dashboard)
- **URL:** `http://localhost:3000/`
- **Presenter Role:** `Scrutiny Officer` (Ananya Rao)
- **Talking Points:**
  1. "Welcome to the unified AICTE Approval and Regulatory Compliance platform. We have unified two separate architectures — workflow execution and continuous compliance monitoring — under a single pane of glass."
  2. "The dashboard provides an instant operational pulse: application ageing distribution, 6-stage workflow breakdown, scheduled EVC inspections, and proactive compliance alerts."
  3. "Both underlying engines report fully `operational` health."

---

### Step 2: Application Registry & Real-Time Search
- **URL:** `http://localhost:3000/applications`
- **Action:**
  1. In the search box, type `APP001` or `Pune`.
  2. Point out the instant filtering and institutional metadata (`INST001`, `Extension of Approval`).
  3. Click **Inspect** to open `APP001`.
- **Talking Points:**
  1. "Here we inspect canonical application `APP001` from Pune Institute of Technology."
  2. "The platform maintains full institutional history, document checklist, and SLA deadlines."

---

### Step 3: Scrutiny & Deficiency Resubmission Loop (Statutory Non-Rejection)
- **Action:**
  1. Open disposable application `APP038` (already in `INITIAL_SCRUTINY`) or click **Start New Intake** at top-right to register a fresh application in 5 seconds.
  2. With role set to **Scrutiny Officer**, click **Return for Deficiency**. Enter notes: `"Updated faculty appointment letters and fire safety NOC required"`. Submit.
  3. Notice: Application status changes to `ACTION_REQUIRED` and current stage becomes `DEFICIENCY_RAISED` with an amber alert banner.
  4. Switch role (top-right avatar dropdown) to **Institution Admin**. Click **Submit Correction / Resubmit** (or open `APP039` which is already in `DEFICIENCY_RAISED`). Enter: `"Uploaded renewed valid certificates"`. Submit.
  5. Notice: Amber alert clears! Application status moves to `IN_PROGRESS` and advances to `Re-scrutiny`.
- **Talking Points:**
  1. "Under AICTE regulations, a deficiency is **strictly distinct from a rejection**. Notice that the application was never rejected or closed."
  2. "The institution was assigned an action item. Upon resubmission, the deficiency flag cleared and the case safely progressed to Re-scrutiny."

---

### Step 4: Expert Visiting Committee (EVC) Inspection Flow
- **URL:** `http://localhost:3000/evc`
- **Action:**
  1. Show the 7 canonical inspection records in **List View**.
  2. Toggle to **Calendar View** using the segment switcher at the top right.
  3. Highlight `EVC001` with assigned committee members (`Dr. K. Sharma`, `Prof. P. Varma`).
- **Talking Points:**
  1. "Physical and virtual site visits are route-specific and strictly scheduled."
  2. "Our system manages committee assignments, inspection dates, and report evidence uploads."

---

### Step 5: Compliance Vault & Document Validity
- **URL:** `http://localhost:3000/compliance`
- **Action:**
  1. Filter by urgency: select **Expired**.
  2. Point to `DOC-2026-0001` (Fire Safety NOC).
  3. Switch filter to **Expiring soon** &rarr; point to `DOC-2026-0002` (Building Completion Certificate).
  4. Click the **Undertakings** tab to show the 8 verified compliance undertakings.
- **Talking Points:**
  1. "Regulatory compliance is monitored continuously throughout the institutional lifecycle."
  2. "Notice that when a document expires, the platform raises warning badges and recommendations, but **never performs automated statutory disposals**."

---

### Step 6: Deadlines & SLA Breach Alerts
- **URL:** `http://localhost:3000/notifications`
- **Action:**
  1. Point out category badges: `Deficiency alert`, `Deadline reminder`, `EVC reminder`.
  2. Click **Mark read** on a notification to demonstrate interactive state updates.
- **Talking Points:**
  1. "Deadlines are computed dynamically against AICTE SLA norms relative to the cycle date."
  2. "`OVERDUE` is tracked as an alert condition for officers, not as a lifecycle status."

---

### Step 7: Append-Only Immutable Audit Trail
- **URL:** `http://localhost:3000/audit`
- **Action:**
  1. In the search box, type `APP` or `DEFICIENCY`.
  2. Highlight the timeline showing actor role, previous state &rarr; new state pill, timestamp, and justification.
  3. Point out that canonical synthetic records are visibly tagged with `[SYNTHETIC - CANONICAL BASELINE]`.
- **Talking Points:**
  1. "Every stage movement, deficiency note, committee assignment, and decision is recorded in an immutable append-only audit log."
  2. "Synthetic baseline data is visibly distinguished from live operational events, guaranteeing complete transparency."

---

### Step 8: Competent Authority Decision (Strict Server-Side RBAC)
- **Action:**
  1. Navigate to disposable application `APP028` or `APP034` (currently in `DECISION_PENDING`, awaiting official decision).
  2. Ensure your active role in top-right header is **Scrutiny Officer**.
  3. Attempt to record an approval decision &rarr; **The system immediately displays an HTTP 403 Forbidden error**:
     *`Access denied for role 'Scrutiny Officer'. Action requires one of: ['Competent Authority Secretariat', 'Admin']`*
  4. Now switch role to **Competent Authority Secretariat**.
  5. Click **Record Decision**. Select **APPROVED**, enter statutory reason: `"Institution satisfies AICTE APH 2024-27 norms for Extension of Approval."`, enter condition: `"Annual compliance report due 31 Dec 2026."`. Submit.
  6. The application completes! The progress stepper turns green, and the official decision certificate block renders.
  7. *(Optional)* Open `APP041` or `APP042` to show how an existing completed application retains its immutable decision and reasons permanently.
- **Talking Points:**
  1. "Regulatory authority is strictly enforced on the server. Scrutiny officers cannot record executive decisions."
  2. "Only the designated Competent Authority Secretariat can record formal statutory decisions with mandatory reasons and conditions."

---

## 4. Emergency Troubleshooting & Fallback Procedures

| Symptom | Cause | 10-Second Fix |
| :--- | :--- | :--- |
| **"Live API Connection Failed" red banner** | Backend gateway not running | In Terminal 1, run `uvicorn app.main:app --host 127.0.0.1 --port 8020`. Then click "Retry Backend Connection" in UI. |
| **Port 8020 already in use** | A previous background process is holding the port | Run `Get-Process python \| Stop-Process -Force` in PowerShell, then re-launch the uvicorn command. |
| **Port 3000 already in use** | A previous Vite server is active | In Terminal 2, run `npx.cmd vite --port 3001` and update `.env` if needed. |
| **Application stage is locked / won't advance** | Application has reached terminal `COMPLETED` stage | Click **Start New Intake** (`/applications/new`) and create a fresh application (e.g. `APP043`) in 5 seconds. |
| **Live API completely unreachable (Total network loss)** | Hardware or network disconnection | Open `file:///c:/Users/Dell/OneDrive/Desktop/AICTE/reference.html.html` in browser. It runs 100% offline with zero dependencies! |

---

## 5. Summary of System Boundaries for Judges' Q&A

1. **Dual-Database Architecture:** "We deliberately maintained Member 3's workflow engine (`aicte_platform.db`) and Member 4's compliance monitoring engine (`aicte.db`) to preserve data boundaries and prevent disruptive migrations, unifying them via a FastAPI gateway."
2. **Deficiency vs. Rejection:** "Per AICTE regulations, deficiency returns the application to the institution for correction. Rejection is an executive decision exclusively made by the Competent Authority."
3. **Automated Timers:** "Under administrative law, computers cannot arbitrarily reject applications due to timer expirations. Timers generate urgent alerts and escalations for human officers."
4. **Role Switching Header:** "For this demonstration, we expose a role-switcher widget via `X-User-Role` headers. In a production rollout, this is replaced by OpenID Connect / SAML 2.0 single sign-on."
