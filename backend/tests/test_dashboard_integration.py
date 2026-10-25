from datetime import datetime, timezone, timedelta
from backend.app.enums import UserRole


def test_dashboard_compliance_metrics(client):
    ref_time = datetime.now(timezone.utc)

    # Initially empty metrics
    initial_metrics = client.get(
        "/api/dashboard/compliance-summary",
        params={"reference_time": ref_time.isoformat()}
    ).json()
    assert initial_metrics["evc"]["pending_scheduling"] == 0
    assert initial_metrics["compliance"]["open_obligations"] == 0

    # 1. Create an EVC record
    client.post(
        "/api/evcs",
        json={"application_id": "test-app-001"}
    )

    # 2. Create a compliance obligation
    client.post(
        "/api/undertakings",
        json={
            "institution_id": "INST-TEST-01",
            "title": "Faculty Cadre Compliance",
            "obligation_type": "FACULTY_CADRE",
            "description": "Maintain faculty cadre ratio."
        }
    )

    # 3. Create document nearing expiry (in 10 days)
    client.post(
        "/api/documents",
        json={
            "institution_id": "INST-TEST-01",
            "document_type": "FIRE_SAFETY",
            "title": "Fire Certificate",
            "file_name": "fire.pdf",
            "expiry_date": (ref_time + timedelta(days=10)).isoformat(),
            "is_expiry_tracked": True
        }
    )

    # 4. Create an overdue deadline
    client.post(
        "/api/deadlines",
        json={
            "entity_type": "APPLICATION",
            "entity_id": "test-app-001",
            "deadline_type": "DEFICIENCY",
            "title": "Deficiency Window",
            "due_date": (ref_time - timedelta(days=1)).isoformat(),
            "owner_role": UserRole.APPLICANT.value
        }
    )

    # Trigger evaluation
    client.post("/api/deadlines/evaluate", json={"reference_time": ref_time.isoformat()})

    # Query updated metrics
    metrics = client.get(
        "/api/dashboard/compliance-summary",
        params={"reference_time": ref_time.isoformat()}
    ).json()
    assert metrics["evc"]["pending_scheduling"] == 1
    assert metrics["compliance"]["open_obligations"] == 1
    assert metrics["documents"]["nearing_expiry_30_days"] == 1
    assert metrics["deadlines"]["overdue"] == 1
    assert metrics["deadlines"]["escalations_generated"] == 1
    assert metrics["audit"]["total_events_logged"] > 0

    # Query unified dashboard
    unified = client.get(
        "/api/dashboard/summary",
        params={"reference_time": ref_time.isoformat()}
    ).json()
    assert unified["total_applications"] >= 1
    assert "compliance_summary" in unified
    assert unified["compliance_summary"]["evc"]["pending_scheduling"] == 1


def test_invalid_entity_id_handling(client):
    # Non-existent EVC
    res_evc = client.get("/api/evcs/non-existent-uuid")
    assert res_evc.status_code == 404

    # Non-existent Obligation
    res_ob = client.get("/api/undertakings/non-existent-uuid")
    assert res_ob.status_code == 404

    # Non-existent Document
    res_doc = client.get("/api/documents/non-existent-uuid")
    assert res_doc.status_code == 404

    # Non-existent Deadline
    res_dl = client.get("/api/deadlines/non-existent-uuid")
    assert res_dl.status_code == 404


def test_health_and_root_endpoints(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    root = client.get("/")
    assert root.status_code == 200
    assert "/docs" in root.json()["documentation"]
