from datetime import datetime, timezone, timedelta
from app.enums import DeadlineStatus, UserRole, NotificationType


def test_deadline_deterministic_evaluation_and_deduplication(client):
    ref_now = datetime.now(timezone.utc)

    # 1. Create upcoming deadline (due in 24 hours, threshold 48 hours)
    dl_upcoming = client.post(
        "/api/deadlines",
        json={
            "entity_type": "APPLICATION",
            "entity_id": "test-app-001",
            "deadline_type": "DEFICIENCY_RESPONSE",
            "title": "Technical Deficiency Clarification Window",
            "due_date": (ref_now + timedelta(hours=24)).isoformat(),
            "owner_role": UserRole.APPLICANT.value,
            "warning_threshold_hours": 48
        }
    ).json()

    # 2. Create overdue deadline (due 2 hours ago)
    dl_overdue = client.post(
        "/api/deadlines",
        json={
            "entity_type": "UNDERTAKING",
            "entity_id": "ob-test-999",
            "deadline_type": "COMPLIANCE_SUBMISSION",
            "title": "Mandatory Faculty Matrix Submission",
            "due_date": (ref_now - timedelta(hours=2)).isoformat(),
            "owner_role": UserRole.COMPLIANCE_OFFICER.value,
            "warning_threshold_hours": 48
        }
    ).json()

    # 3. Create completed deadline (already fulfilled)
    dl_completed = client.post(
        "/api/deadlines",
        json={
            "entity_type": "EVC",
            "entity_id": "evc-test-completed",
            "deadline_type": "EVC_REPORT",
            "title": "Fulfilled EVC Report",
            "due_date": (ref_now - timedelta(hours=5)).isoformat(),
            "owner_role": UserRole.EVC_TEAM.value
        }
    ).json()
    client.post(f"/api/deadlines/{dl_completed['id']}/complete")

    # 4. Run evaluation with reference_time = ref_now
    eval_res1 = client.post(
        "/api/deadlines/evaluate",
        json={"reference_time": ref_now.isoformat()}
    )
    assert eval_res1.status_code == 200
    summary1 = eval_res1.json()
    assert summary1["upcoming_warnings_issued"] == 1
    assert summary1["overdue_escalations_issued"] == 1
    assert summary1["deadlines_marked_overdue"] == 1

    # Check notification count after first run
    notifs1 = client.get("/api/notifications").json()
    initial_notif_count = len(notifs1)
    assert initial_notif_count == 2

    # 5. Run evaluation SECOND time (Idempotency / Deduplication check!)
    eval_res2 = client.post(
        "/api/deadlines/evaluate",
        json={"reference_time": ref_now.isoformat()}
    )
    assert eval_res2.status_code == 200
    # Overdue deadline has escalation_triggered=True, so overdue_escalations_issued is 0 on 2nd run
    summary2 = eval_res2.json()
    assert summary2["overdue_escalations_issued"] == 0

    # Notification count MUST remain exactly 2 (No duplicates created!)
    notifs2 = client.get("/api/notifications").json()
    assert len(notifs2) == initial_notif_count

    # 6. Verify Completed deadline did NOT generate any overdue alerts
    completed_alerts = [n for n in notifs2 if n["entity_id"] == "evc-test-completed"]
    assert len(completed_alerts) == 0


def test_notification_read_workflow(client):
    ref = datetime.now(timezone.utc)
    # Trigger deadline to generate notification
    client.post(
        "/api/deadlines",
        json={
            "entity_type": "APPLICATION",
            "entity_id": "test-app-001",
            "deadline_type": "FEE_PAYMENT",
            "title": "Processing Fee Clearance",
            "due_date": (ref + timedelta(hours=10)).isoformat(),
            "owner_role": UserRole.APPLICANT.value,
            "warning_threshold_hours": 24
        }
    )
    client.post("/api/deadlines/evaluate", json={"reference_time": ref.isoformat()})

    notifs = client.get("/api/notifications?is_read=false").json()
    assert len(notifs) >= 1
    target_notif = notifs[0]
    assert target_notif["is_read"] is False

    # Mark as read
    read_res = client.post(f"/api/notifications/{target_notif['id']}/read")
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True
    assert read_res.json()["read_at"] is not None
