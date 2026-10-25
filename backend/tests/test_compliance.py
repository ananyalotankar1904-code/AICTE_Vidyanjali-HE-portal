from datetime import datetime, timezone, timedelta
from app.enums import ObligationStatus, UserRole


def test_obligation_full_lifecycle(client):
    # 1. Create obligation
    due = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    create_res = client.post(
        "/api/undertakings",
        json={
            "institution_id": "INST-TEST-01",
            "application_id": "test-app-001",
            "title": "Clean Energy Infrastructure Undertaking",
            "obligation_type": "SOLAR_POWER_COMPLIANCE",
            "description": "Commitment to install 20kW rooftop solar.",
            "source_reference": "Illustrative Demo Configuration",
            "is_illustrative_demo_rule": True,
            "due_date": due
        }
    )
    assert create_res.status_code == 201
    ob = create_res.json()
    ob_id = ob["id"]
    assert ob["status"] == ObligationStatus.PENDING.value
    assert ob["is_illustrative_demo_rule"] is True

    # 2. Submit evidence
    sub_res = client.post(
        f"/api/undertakings/{ob_id}/submit",
        json={
            "evidence_document_id": "doc-solar-contract-01",
            "submission_notes": "Vendor purchase order attached"
        }
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == ObligationStatus.SUBMITTED.value

    # 3. Request correction
    corr_res = client.post(
        f"/api/undertakings/{ob_id}/request-correction",
        headers={"X-User-Role": UserRole.COMPLIANCE_OFFICER.value},
        json={
            "reason": "Missing installation timeline breakdown",
            "guidance": "Please attach annexure 4"
        }
    )
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["status"] == ObligationStatus.NEEDS_CORRECTION.value
    assert len(corr_data["correction_history"]) == 1
    assert corr_data["correction_history"][0]["reason"] == "Missing installation timeline breakdown"

    # 4. Resubmit corrected evidence
    resub_res = client.post(
        f"/api/undertakings/{ob_id}/submit",
        json={
            "evidence_document_id": "doc-solar-contract-02",
            "submission_notes": "Annexure 4 timeline added"
        }
    )
    assert resub_res.status_code == 200
    assert resub_res.json()["status"] == ObligationStatus.SUBMITTED.value

    # 5. Verify - Unauthorized role check
    bad_verify = client.post(
        f"/api/undertakings/{ob_id}/verify",
        headers={"X-User-Role": UserRole.APPLICANT.value},
        json={"verification_notes": "Attempt self-verification"}
    )
    assert bad_verify.status_code == 403

    # 6. Verify - Authorized Compliance Officer
    ok_verify = client.post(
        f"/api/undertakings/{ob_id}/verify",
        headers={"X-User-Role": UserRole.COMPLIANCE_OFFICER.value},
        json={"verification_notes": "Document verified compliant with standards."}
    )
    assert ok_verify.status_code == 200
    assert ok_verify.json()["status"] == ObligationStatus.VERIFIED.value

    # 7. Check audit trail
    audit_res = client.get(f"/api/audit-logs?entity_type=UNDERTAKING&entity_id={ob_id}")
    assert audit_res.status_code == 200
    actions = [log["action"] for log in audit_res.json()]
    assert "CREATE_COMPLIANCE_OBLIGATION" in actions
    assert "SUBMIT_COMPLIANCE_EVIDENCE" in actions
    assert "REQUEST_OBLIGATION_CORRECTION" in actions
    assert "VERIFY_COMPLIANCE_OBLIGATION" in actions


def test_standalone_obligation_without_application(client):
    """Obligations can remain independent or stand alone without a specific application ID."""
    res = client.post(
        "/api/undertakings",
        json={
            "institution_id": "INST-STANDALONE-09",
            "title": "Annual Green Audit",
            "obligation_type": "GREEN_AUDIT",
            "description": "Annual statutory campus environmental assessment."
        }
    )
    assert res.status_code == 201
    assert res.json()["application_id"] is None
    assert res.json()["institution_id"] == "INST-STANDALONE-09"
