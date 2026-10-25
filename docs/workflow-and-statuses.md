# Workflow, Stages, and Statuses

**Module:** Compliance, EVC, Undertakings, Documents & Deadlines  
**System:** AICTE Approval Workflow Automation & Compliance Management Platform  

---

## 1. Expert Visit Committee (EVC) Lifecycle

```
[ PENDING_SCHEDULING ]
         |
         | schedule_evc (planned_visit_date, venue)
         v
   [ SCHEDULED ] <------------+
         |                    | reschedule_evc (appends to reschedule_history)
         | complete_visit     +
         v
[ VISIT_COMPLETED ]
         |
         | submit_evc_report (findings, recommendation)
         v
[ REPORT_SUBMITTED ]
         |
         | review_evc_report (outcome: ACCEPTED | CLARIFICATION_REQUESTED)
         v
[ REPORT_REVIEWED ]
```

### Transition Rules
1. `SCHEDULED` requires a valid planned datetime in the future.
2. `reschedule_evc` can only be performed from `SCHEDULED` status. It appends the previous date, new date, reason, user, and timestamp into `reschedule_history`.
3. `complete_visit` requires an actual inspection date.
4. `submit_report` requires factual observations and an explicit recommendation (`RECOMMENDED`, `DEFICIENCIES_NOTED`, or `NOT_RECOMMENDED`).
5. `review_report` is restricted to authorized roles (`COMPLIANCE_OFFICER`, `SCRUTINY_OFFICER`, `ADMIN`).

---

## 2. Compliance Obligations & Undertakings Lifecycle

```
[ PENDING ]
    |
    | submit_evidence (evidence_document_id)
    v
[ SUBMITTED ] <-----------------------------------+
    |                                             |
    +-----> [ NEEDS_CORRECTION ]                  |
    |            |                                |
    |            +--- submit_corrected_evidence --+
    |
    | verify_obligation (Role: COMPLIANCE_OFFICER)
    v
[ VERIFIED ]
```

### Lifecycle Rules
- Obligations can be linked to an application or track campus-wide regulatory conditions independently.
- Even if an application is `COMPLETED`, ongoing annual undertakings remain active.
- Correction requests append to `correction_history` and notify the institution.
- Verification requires explicit officer sign-off; uploading a file does not automatically verify an obligation.

---

## 3. Document Versioning & Expiry Lifecycle

```
[ Version 1 Registered ] (is_latest = True)
          |
          | renew_document (creates Version 2)
          +----------------------------------------------+
          |                                              |
          v                                              v
[ Version 1 Retained ]                        [ Version 2 Active ]
  (is_latest = False,                           (is_latest = True,
   previous_version_id = None)                   previous_version_id = V1.id)
```

### Expiry Conditions (Non-Terminal Flags)
- **Active / Valid:** `expiry_date > reference_time + 30 days`
- **Approaching Expiry:** `reference_time <= expiry_date <= reference_time + 30 days` (triggers renewal reminder)
- **Past Expiry:** `expiry_date < reference_time` (flags document as expired; does **not** cancel statutory approval)

---

## 4. Deadline Monitoring Lifecycle

```
       [ ACTIVE ]
        /      \
       /        \
[ COMPLETED ]   [ OVERDUE ] (due_date < reference_time)
(Task done;          |
 no alerts)          +--> [ ESCALATION_ALERT ] generated
                          (escalation_triggered = True)
```

- If `reference_time <= due_date <= reference_time + warning_threshold`: emits `DEADLINE_UPCOMING` warning.
- If `due_date < reference_time`: marks `OVERDUE` and generates `ESCALATION_ALERT` to regional supervisor.
- Once marked `COMPLETED` or `CANCELLED`, future reminder cycles ignore the record.
