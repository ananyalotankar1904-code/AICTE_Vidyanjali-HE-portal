from datetime import datetime, timezone, timedelta
from app.enums import EVCStatus, EVCRecommendation, EVCReportReviewOutcome, UserRole


def test_create_and_schedule_evc(client):
    # 1. Create EVC
    create_res = client.post(
        "/api/evcs",
        json={
            "application_id": "test-app-001",
            "assigned_team_id": "TEAM_A",
            "assigned_members": ["Dr. Smith", "Dr. Johnson"],
            "venue_address": "Campus Road 1"
        }
    )
    assert create_res.status_code == 201
    evc_data = create_res.json()
    assert evc_data["status"] == EVCStatus.PENDING_SCHEDULING.value
    evc_id = evc_data["id"]

    # 2. Schedule visit
    planned_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    sched_res = client.post(
        f"/api/evcs/{evc_id}/schedule",
        json={
            "planned_visit_date": planned_date,
            "notes": "Initial schedule"
        }
    )
    assert sched_res.status_code == 200
    assert sched_res.json()["status"] == EVCStatus.SCHEDULED.value

    # 3. Reschedule visit
    new_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resched_res = client.post(
        f"/api/evcs/{evc_id}/reschedule",
        json={
            "new_planned_visit_date": new_date,
            "reason": "Expert committee travel delay"
        }
    )
    assert resched_res.status_code == 200
    resched_data = resched_res.json()
    assert len(resched_data["reschedule_history"]) == 1
    assert resched_data["reschedule_history"][0]["reason"] == "Expert committee travel delay"


def test_evc_invalid_transition(client):
    # Cannot complete visit if not scheduled
    create_res = client.post(
        "/api/evcs",
        json={"application_id": "test-app-001"}
    )
    evc_id = create_res.json()["id"]

    # Try to complete visit directly from PENDING_SCHEDULING
    visit_date = datetime.now(timezone.utc).isoformat()
    bad_res = client.post(
        f"/api/evcs/{evc_id}/complete-visit",
        json={"actual_visit_date": visit_date}
    )
    assert bad_res.status_code == 400
    assert "Cannot complete visit" in bad_res.json()["detail"]


def test_evc_full_lifecycle(client):
    # 1. Create
    evc = client.post("/api/evcs", json={"application_id": "test-app-001"}).json()
    evc_id = evc["id"]

    # 2. Schedule
    planned = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    client.post(f"/api/evcs/{evc_id}/schedule", json={"planned_visit_date": planned})

    # 3. Complete visit
    actual = datetime.now(timezone.utc).isoformat()
    comp_res = client.post(
        f"/api/evcs/{evc_id}/complete-visit",
        json={"actual_visit_date": actual, "visit_notes": "All labs inspected"}
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == EVCStatus.VISIT_COMPLETED.value

    # 4. Submit report
    rep_res = client.post(
        f"/api/evcs/{evc_id}/submit-report",
        json={
            "findings_summary": "All infrastructure verified adhering to norms.",
            "recommendation": EVCRecommendation.RECOMMENDED.value
        }
    )
    assert rep_res.status_code == 200
    assert rep_res.json()["status"] == EVCStatus.REPORT_SUBMITTED.value

    # 5. Review report - Unauthorized role rejected
    bad_role_res = client.post(
        f"/api/evcs/{evc_id}/review-report",
        headers={"X-User-Role": UserRole.APPLICANT.value},
        json={"outcome": EVCReportReviewOutcome.ACCEPTED.value}
    )
    assert bad_role_res.status_code == 403

    # 6. Review report - Authorized role accepted
    ok_rev_res = client.post(
        f"/api/evcs/{evc_id}/review-report",
        headers={"X-User-Role": UserRole.COMPLIANCE_OFFICER.value},
        json={
            "outcome": EVCReportReviewOutcome.ACCEPTED.value,
            "review_notes": "Findings accepted."
        }
    )
    assert ok_rev_res.status_code == 200
    assert ok_rev_res.json()["status"] == EVCStatus.REPORT_REVIEWED.value

    # 7. Verify Audit Events recorded
    audit_res = client.get("/api/audit-logs?entity_type=EVC")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    actions = [log["action"] for log in logs]
    assert "CREATE_EVC_RECORD" in actions
    assert "SCHEDULE_EVC_VISIT" in actions
    assert "COMPLETE_EVC_VISIT" in actions
    assert "SUBMIT_EVC_REPORT" in actions
    assert "REVIEW_EVC_REPORT" in actions
