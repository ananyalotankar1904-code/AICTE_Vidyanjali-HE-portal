# Decisions and Known Limitations

**Author:** Member 4 — Backend Compliance Developer  
**System:** AICTE Approval Workflow Automation & Compliance Management Platform  

---

## 1. Architectural & Design Decisions

1. **Deterministic Time Evaluation vs Background Daemons**:
   - Rather than relying on Celery, Redis, or OS cron daemons that complicate localhost hackathon demos, deadline evaluation is exposed via a service and endpoint `POST /api/deadlines/evaluate`.
   - Accepting an optional `reference_time` enables reviewers and automated tests to fast-forward into the future and demonstrate deadline alerts reproducibly.

2. **Deduplication Strategy**:
   - Notifications use deterministic deduplication keys (e.g. `deadline:overdue:{id}`, `deadline:upcoming:{id}`).
   - Even if the deadline evaluation is triggered repeatedly, duplicate alerts are impossible.

3. **Non-Destructive Document Versioning**:
   - Document replacement creates a new version row with `previous_version_id` pointing to the prior version.
   - Prior version files and metadata are retained indefinitely with `is_latest = false`.

4. **Statutory Decision Safeguard**:
   - EVC recommendations (`RECOMMENDED`, `NOT_RECOMMENDED`) and deadline overdue flags **never** automatically grant, reject, or alter the statutory application status. Statutory decisions remain strictly within Member 3's human decision-maker workflow.

---

## 2. Dependencies & Coordination with Other Members

- **Member 3 (Backend Workflow Lead):**
  - Member 4 created a foundational `Application` model with foreign key relationships (`evc_records`, `compliance_obligations`, `documents`). Member 3 can extend this model with scrutiny deficiencies, committee reviews, and formal decision records without conflict.
- **Member 5 (Integration Lead):**
  - Standardized enums (`enums.py`), session dependency (`db.py`), and unified dashboard summary endpoint `/api/dashboard/summary` combine application metrics with compliance metrics.
- **Member 2 (Frontend Workflow & Compliance Lead):**
  - Frontend screens for EVC scheduling, undertakings, document renewals, and deadline alerts can consume the endpoints documented in `docs/api-contract.md`.

---

## 3. Disclosed Prototype Limitations

1. **Demo Authentication**:
   - For demo convenience, role verification is simulated via `X-User-Role` headers (e.g., `COMPLIANCE_OFFICER`, `APPLICANT`). Production deployment will require OAuth2 / JWT integration with AICTE SSO.
2. **Abstract File Storage**:
   - Documents store safe abstract file storage references (e.g., `/vault/docs/...`). Physical binary upload handlers to AWS S3 or MinIO can be wired to this storage abstraction without changing metadata or versioning models.
3. **In-App Notifications Only**:
   - External SMS/Email gateways are stubbed for prototype safety to prevent test spam.
4. **Synthetic Data**:
   - All seeded records use fictional colleges (`INST-MUMBAI-01`, `INST-PUNE-02`) and illustrative regulatory policies.
