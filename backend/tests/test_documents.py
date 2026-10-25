from datetime import datetime, timezone, timedelta
from backend.app.enums import DocumentReviewStatus


def test_document_registration_and_renewal_versioning(client):
    ref_time = datetime.now(timezone.utc)
    expiry = (ref_time + timedelta(days=20)).isoformat()

    # 1. Register Document (v1)
    reg_res = client.post(
        "/api/documents",
        json={
            "institution_id": "INST-TEST-01",
            "application_id": "test-app-001",
            "document_type": "FIRE_SAFETY_NOC",
            "title": "Fire Safety Certificate 2025",
            "file_name": "fire_noc_2025.pdf",
            "file_size_bytes": 500000,
            "expiry_date": expiry,
            "is_expiry_tracked": True
        }
    )
    assert reg_res.status_code == 201
    v1_doc = reg_res.json()
    assert v1_doc["version"] == 1
    assert v1_doc["is_latest"] is True
    assert v1_doc["previous_version_id"] is None
    v1_id = v1_doc["id"]

    # 2. Renew Document (creates v2, retains v1)
    new_expiry = (ref_time + timedelta(days=365)).isoformat()
    renew_res = client.post(
        f"/api/documents/{v1_id}/renew",
        json={
            "title": "Fire Safety Certificate (2026 Renewal)",
            "file_name": "fire_noc_2026_renewed.pdf",
            "file_size_bytes": 520000,
            "expiry_date": new_expiry,
            "renewal_reason": "Annual renewal submission"
        }
    )
    assert renew_res.status_code == 201
    v2_doc = renew_res.json()
    assert v2_doc["version"] == 2
    assert v2_doc["is_latest"] is True
    assert v2_doc["previous_version_id"] == v1_id

    # 3. Verify prior version v1 is intact (retained without silent overwrite)
    v1_check = client.get(f"/api/documents/{v1_id}").json()
    assert v1_check["version"] == 1
    assert v1_check["is_latest"] is False
    assert v1_check["file_name"] == "fire_noc_2025.pdf"


def test_document_expiry_queries(client):
    ref = datetime.now(timezone.utc)

    # Document expiring in 15 days
    client.post(
        "/api/documents",
        json={
            "institution_id": "INST-TEST-01",
            "document_type": "POLLUTION_CLEARANCE",
            "title": "Pollution Control Board NOC",
            "file_name": "pcb_noc.pdf",
            "expiry_date": (ref + timedelta(days=15)).isoformat(),
            "is_expiry_tracked": True
        }
    )

    # Document already expired 5 days ago
    client.post(
        "/api/documents",
        json={
            "institution_id": "INST-TEST-01",
            "document_type": "WATER_SAFETY_NOC",
            "title": "Potable Water Certificate",
            "file_name": "water_noc.pdf",
            "expiry_date": (ref - timedelta(days=5)).isoformat(),
            "is_expiry_tracked": True
        }
    )

    # Document with no expiry date
    client.post(
        "/api/documents",
        json={
            "institution_id": "INST-TEST-01",
            "document_type": "LAND_DEED",
            "title": "Perpetual Land Ownership Deed",
            "file_name": "land_deed.pdf",
            "expiry_date": None,
            "is_expiry_tracked": False
        }
    )

    # Query expiring soon (within 30 days) - using params dict for safe URL encoding
    soon_res = client.get(
        "/api/documents/status/expiring-soon",
        params={"reference_time": ref.isoformat(), "threshold_days": 30}
    )
    assert soon_res.status_code == 200
    soon_titles = [d["title"] for d in soon_res.json()]
    assert "Pollution Control Board NOC" in soon_titles
    assert "Potable Water Certificate" not in soon_titles
    assert "Perpetual Land Ownership Deed" not in soon_titles

    # Query expired
    expired_res = client.get(
        "/api/documents/status/expired",
        params={"reference_time": ref.isoformat()}
    )
    assert expired_res.status_code == 200
    exp_titles = [d["title"] for d in expired_res.json()]
    assert "Potable Water Certificate" in exp_titles
    assert "Pollution Control Board NOC" not in exp_titles
    assert "Perpetual Land Ownership Deed" not in exp_titles
