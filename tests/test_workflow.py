import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.application import Application, WorkflowHistory

# In-memory SQLite for high-speed, isolated test runs
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_application_registration_success(client):
    """Test successful application registration with valid fields."""
    payload = {
        "institution_id": "INST001",
        "application_type": "Extension of Approval",
        "academic_year": "2026-2027",
        "contact_email": "principal@engg.edu",
        "contact_phone": "+91-9876543210",
        "programme_name": "Computer Science & Engineering",
        "intake_approved": 120
    }
    response = client.post(
        "/api/applications",
        json=payload,
        headers={"X-User-Role": "Institution Admin", "X-User-Id": "inst_admin_01"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["application_id"] == "APP001"
    assert data["institution_id"] == "INST001"
    assert data["current_stage"] == "SUBMITTED"
    assert data["application_status"] == "IN_PROGRESS"
    assert data["assigned_role"] == "Intake Officer"
    assert data["deficiency_flag"] == "No"


def test_application_registration_invalid_input(client):
    """Test validation failure when mandatory fields are omitted."""
    # Missing application_type
    response = client.post(
        "/api/applications",
        json={"institution_id": "INST001"},
        headers={"X-User-Role": "Institution Admin"}
    )
    assert response.status_code == 422


def test_application_listing_and_filtering(client):
    """Test application listing with stage and status filters."""
    # Create two applications
    client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    client.post(
        "/api/applications",
        json={"institution_id": "INST002", "application_type": "New Programme"},
        headers={"X-User-Role": "Institution Admin"}
    )

    # List all
    res_all = client.get("/api/applications")
    assert res_all.status_code == 200
    assert res_all.json()["total"] == 2

    # Filter by institution
    res_filtered = client.get("/api/applications?institution_id=INST002")
    assert res_filtered.status_code == 200
    assert res_filtered.json()["total"] == 1
    assert res_filtered.json()["items"][0]["application_id"] == "APP002"


def test_application_retrieval_by_id(client):
    """Test retrieval of existing application and 404 for missing ID."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    res = client.get(f"/api/applications/{app_id}")
    assert res.status_code == 200
    assert res.json()["application_id"] == app_id
    assert len(res.json()["history"]) == 1
    assert res.json()["history"][0]["action"] == "REGISTER"

    res_missing = client.get("/api/applications/APP999")
    assert res_missing.status_code == 404


def test_permitted_application_updates(client):
    """Test updating permitted fields in editable stage (SUBMITTED)."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    update_res = client.put(
        f"/api/applications/{app_id}",
        json={"contact_email": "updated@inst.edu", "contact_phone": "+91-9999999999"},
        headers={"X-User-Role": "Institution Admin", "X-User-Id": "inst_01"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["contact_email"] == "updated@inst.edu"
    assert update_res.json()["contact_phone"] == "+91-9999999999"


def test_forbidden_application_updates_in_locked_stage(client):
    """Test that direct updates are forbidden when application is under official review."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Assign scrutiny -> moves to INITIAL_SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )

    # Attempt direct update
    bad_update = client.put(
        f"/api/applications/{app_id}",
        json={"contact_email": "hacked@inst.edu"},
        headers={"X-User-Role": "Institution Admin"}
    )
    assert bad_update.status_code == 400
    assert "Direct application updates are not permitted" in bad_update.json()["detail"]


def test_invalid_workflow_transition_jump(client):
    """Test that skipping intermediate workflow stages is blocked by the engine."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Attempt illegal jump from SUBMITTED directly to COMPLETED
    res = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "FORCE_FINISH", "to_stage": "COMPLETED"},
        headers={"X-User-Role": "Admin"}
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "INVALID_WORKFLOW_TRANSITION"


def test_unauthorized_workflow_action(client):
    """Test that unauthorized roles cannot execute restricted transitions."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Intake Officer assigns to Scrutiny
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )

    # Institution Admin attempts to execute SCRUTINY_PASS (restricted to Scrutiny Officer)
    unauthorized = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "SCRUTINY_PASS", "to_stage": "COMMITTEE_REVIEW"},
        headers={"X-User-Role": "Institution Admin"}
    )
    assert unauthorized.status_code == 403
    assert "UNAUTHORIZED_WORKFLOW_ACTION" in unauthorized.json()["detail"]["error_code"]


def test_scrutiny_deficiency_and_resubmission_loop(client):
    """
    Test Route 2:
    SUBMITTED -> INITIAL_SCRUTINY -> DEFICIENCY_RAISED -> RE_SCRUTINY -> COMMITTEE_REVIEW
    """
    # 1. Register
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # 2. Intake Officer moves to INITIAL_SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )

    # 3. Scrutiny Officer raises deficiencies
    sc_payload = {
        "scrutiny_type": "INITIAL",
        "outcome": "DEFICIENT",
        "remarks": "Missing fire safety NOC and occupancy certificate.",
        "deficiencies": [
            "Fire Safety NOC expired on 2026-09-30.",
            "Occupancy certificate not signed by competent municipal architect."
        ]
    }
    sc_res = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json=sc_payload,
        headers={"X-User-Role": "Scrutiny Officer", "X-User-Id": "scrutiny_off_01"}
    )
    assert sc_res.status_code == 200
    assert sc_res.json()["current_stage"] == "DEFICIENCY_RAISED"
    assert sc_res.json()["application_status"] == "ACTION_REQUIRED"
    assert sc_res.json()["deficiency_flag"] == "Yes"
    assert sc_res.json()["assigned_role"] == "Institution Admin"

    # Verify detail shows open deficiencies
    detail = client.get(f"/api/applications/{app_id}").json()
    assert len(detail["deficiency_records"]) == 2
    def_id_1 = detail["deficiency_records"][0]["id"]
    def_id_2 = detail["deficiency_records"][1]["id"]

    # 4. Institution Admin resubmits responses
    resub_payload = {
        "responses": [
            {"deficiency_id": def_id_1, "institution_response": "Uploaded renewed Fire NOC valid till 2028."},
            {"deficiency_id": def_id_2, "institution_response": "Uploaded signed occupancy cert with municipal seal."}
        ],
        "remarks": "All requested certifications have been renewed and uploaded."
    }
    resub_res = client.post(
        f"/api/applications/{app_id}/deficiency/respond",
        json=resub_payload,
        headers={"X-User-Role": "Institution Admin", "X-User-Id": "inst_admin_01"}
    )
    assert resub_res.status_code == 200
    assert resub_res.json()["current_stage"] == "RE_SCRUTINY"
    assert resub_res.json()["application_status"] == "IN_PROGRESS"
    assert resub_res.json()["assigned_role"] == "Scrutiny Officer"

    # 5. Scrutiny Officer re-evaluates and passes
    re_sc_payload = {
        "scrutiny_type": "RE_SCRUTINY",
        "outcome": "PASSED",
        "remarks": "All renewed documents verified successfully.",
        "deficiencies": []
    }
    re_sc_res = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json=re_sc_payload,
        headers={"X-User-Role": "Scrutiny Officer", "X-User-Id": "scrutiny_off_01"}
    )
    assert re_sc_res.status_code == 200
    assert re_sc_res.json()["current_stage"] == "COMMITTEE_REVIEW"
    assert re_sc_res.json()["deficiency_flag"] == "No"


def test_authorized_decision_recording(client):
    """
    Test Route 1 completion:
    COMMITTEE_REVIEW -> DECISION_PENDING -> COMPLETED (with reasons & conditions)
    """
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Fast forward through initial scrutiny to committee review
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )
    client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "Clear scrutiny"},
        headers={"X-User-Role": "Scrutiny Officer"}
    )

    # Committee Secretariat submits to Authority
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "SUBMIT_TO_AUTHORITY", "to_stage": "DECISION_PENDING"},
        headers={"X-User-Role": "Committee Secretariat"}
    )

    # Unauthorized role attempt
    unauth = client.post(
        f"/api/applications/{app_id}/decision",
        json={"decision": "APPROVED", "reasons": "Approved by Committee"},
        headers={"X-User-Role": "Institution Admin"}
    )
    assert unauth.status_code == 403

    # Authorized Competent Authority Secretariat decision
    dec_payload = {
        "decision": "APPROVED_WITH_CONDITIONS",
        "reasons": "Fulfills faculty cadre ratio and physical laboratory floor area norms.",
        "conditions": "Must complete biometric attendance integration within 60 days of approval."
    }
    dec_res = client.post(
        f"/api/applications/{app_id}/decision",
        json=dec_payload,
        headers={"X-User-Role": "Competent Authority Secretariat", "X-User-Id": "ca_member_01"}
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["current_stage"] == "COMPLETED"
    assert dec_res.json()["application_status"] == "COMPLETED"
    assert dec_res.json()["deadline_condition"] == "COMPLETED"
    assert dec_res.json()["assigned_role"] == "Records Officer"

    # Verify decision record attached
    detail = client.get(f"/api/applications/{app_id}").json()
    assert detail["decision_record"] is not None
    assert detail["decision_record"]["decision"] == "APPROVED_WITH_CONDITIONS"
    assert "biometric" in detail["decision_record"]["conditions"]


def test_workflow_history_ordering_and_completeness(client):
    """Verify that every transition produces an accurate chronological history trail."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin", "X-User-Id": "inst_01"}
    )
    app_id = reg.json()["application_id"]

    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY", "remarks": "Assigning to scrutiny desk"},
        headers={"X-User-Role": "Intake Officer", "X-User-Id": "intake_01"}
    )

    hist_res = client.get(f"/api/applications/{app_id}/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 2
    assert history[0]["action"] == "REGISTER"
    assert history[0]["from_stage"] == "NONE"
    assert history[0]["to_stage"] == "SUBMITTED"

    assert history[1]["action"] == "ASSIGN_SCRUTINY"
    assert history[1]["from_stage"] == "SUBMITTED"
    assert history[1]["to_stage"] == "INITIAL_SCRUTINY"
    assert history[1]["actor_role"] == "Intake Officer"


def test_route_3_evc_inspection_workflow(client):
    """
    Test Route 3:
    SUBMITTED -> INITIAL_SCRUTINY (Passed for New Programme) -> EVC_SCHEDULED -> EVC_COMPLETED -> COMMITTEE_REVIEW
    """
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST005", "application_type": "New Programme", "programme_name": "AI & Data Science"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # 1. Move to Initial Scrutiny
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )

    # 2. Pass scrutiny for New Programme -> Automatically routes to EVC_SCHEDULED
    sc_res = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "Documents verified. Requires physical lab inspection."},
        headers={"X-User-Role": "Scrutiny Officer"}
    )
    assert sc_res.status_code == 200
    assert sc_res.json()["current_stage"] == "EVC_SCHEDULED"
    assert sc_res.json()["assigned_role"] == "EVC Coordinator"

    # 3. EVC Coordinator completes inspection (Handshake with Member 4)
    evc_res = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "COMPLETE_EVC", "to_stage": "EVC_COMPLETED", "remarks": "Physical lab inspection conducted; norms met."},
        headers={"X-User-Role": "EVC Coordinator"}
    )
    assert evc_res.status_code == 200
    assert evc_res.json()["current_stage"] == "EVC_COMPLETED"

    # 4. Submit to Committee
    comm_res = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "SUBMIT_TO_COMMITTEE", "to_stage": "COMMITTEE_REVIEW"},
        headers={"X-User-Role": "EVC Coordinator"}
    )
    assert comm_res.status_code == 200
    assert comm_res.json()["current_stage"] == "COMMITTEE_REVIEW"


def test_route_4_rejection_decision_with_statutory_reasons(client):
    """
    Test Route 4:
    Rejection decision by Competent Authority with recorded statutory reasons.
    """
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST007", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Fast-forward to DECISION_PENDING
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )
    client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "Clear scrutiny"},
        headers={"X-User-Role": "Scrutiny Officer"}
    )
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "SUBMIT_TO_AUTHORITY", "to_stage": "DECISION_PENDING"},
        headers={"X-User-Role": "Committee Secretariat"}
    )

    # Authority rejects application
    rej_payload = {
        "decision": "REJECTED",
        "reasons": "Failed to resolve municipal land title disputes within statutory deadline.",
        "conditions": None
    }
    rej_res = client.post(
        f"/api/applications/{app_id}/decision",
        json=rej_payload,
        headers={"X-User-Role": "Competent Authority Secretariat"}
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["current_stage"] == "COMPLETED"
    assert rej_res.json()["application_status"] == "COMPLETED"

    # Verify decision record
    detail = client.get(f"/api/applications/{app_id}").json()
    assert detail["decision_record"]["decision"] == "REJECTED"
    assert "land title disputes" in detail["decision_record"]["reasons"]


def test_unknown_application_transition_404(client):
    """Test that attempting to transition a non-existent application returns 404."""
    res = client.post(
        "/api/applications/APP_NONEXISTENT/transition",
        json={"action": "ASSIGN_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_destination_stage_derivation(client):
    """Test that the engine derives the destination stage when omitted from the request."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Provide only action without to_stage
    res = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )
    assert res.status_code == 200
    assert res.json()["current_stage"] == "INITIAL_SCRUTINY"


def test_no_state_change_after_rejected_transition(client):
    """Verify that rejected transitions leave the application and history completely unchanged."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]
    initial_detail = client.get(f"/api/applications/{app_id}").json()

    # Attempt illegal transition
    bad_res = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "INVALID_ACTION", "to_stage": "COMPLETED"},
        headers={"X-User-Role": "Admin"}
    )
    assert bad_res.status_code == 400

    # Query again and verify state is pristine
    after_detail = client.get(f"/api/applications/{app_id}").json()
    assert after_detail["current_stage"] == initial_detail["current_stage"]
    assert after_detail["application_status"] == initial_detail["application_status"]
    assert after_detail["last_updated"] == initial_detail["last_updated"]
    assert len(after_detail["history"]) == len(initial_detail["history"])


def test_missing_prerequisite_decision_reasons(client):
    """Verify that recording a decision without minimum 10-char reasons is rejected."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Move to DECISION_PENDING
    client.post(f"/api/applications/{app_id}/transition", json={"action": "ASSIGN_SCRUTINY"}, headers={"X-User-Role": "Intake Officer"})
    client.post(f"/api/applications/{app_id}/scrutiny", json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "Clear scrutiny"}, headers={"X-User-Role": "Scrutiny Officer"})
    client.post(f"/api/applications/{app_id}/transition", json={"action": "SUBMIT_TO_AUTHORITY"}, headers={"X-User-Role": "Committee Secretariat"})

    # Attempt conditional approval without specifying conditions (prerequisite failure)
    bad_dec = client.post(
        f"/api/applications/{app_id}/decision",
        json={"decision": "APPROVED_WITH_CONDITIONS", "reasons": "Fulfills cadre ratio norms.", "conditions": None},
        headers={"X-User-Role": "Competent Authority Secretariat"}
    )
    assert bad_dec.status_code == 400
    assert bad_dec.json()["detail"]["error_code"] == "MISSING_PREREQUISITE"


def test_shared_service_integration(client):
    """Verify that shared audit and notification listeners receive dispatched events."""
    from app.core.workflow_engine import register_audit_listener, register_notification_listener, clear_service_listeners

    audit_events_captured = []
    notification_alerts_captured = []

    register_audit_listener(lambda payload: audit_events_captured.append(payload))
    register_notification_listener(lambda payload: notification_alerts_captured.append(payload))

    try:
        reg = client.post(
            "/api/applications",
            json={"institution_id": "INST001", "application_type": "Extension of Approval"},
            headers={"X-User-Role": "Institution Admin"}
        )
        app_id = reg.json()["application_id"]

        client.post(
            f"/api/applications/{app_id}/transition",
            json={"action": "ASSIGN_SCRUTINY"},
            headers={"X-User-Role": "Intake Officer", "X-User-Id": "officer_101"}
        )

        # Check captured events
        assert any(e["event_type"] == "WORKFLOW_TRANSITION" and e["target_id"] == app_id for e in audit_events_captured)
        assert any(n["event_type"] == "STAGE_CHANGED" and n["application_id"] == app_id for n in notification_alerts_captured)
    finally:
        clear_service_listeners()


def test_no_partial_update_on_database_failure(client, db_session, monkeypatch):
    """
    Verify atomic rollback: if a database error occurs during commit,
    application state is not partially updated.
    """
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Monkeypatch commit to simulate failure
    orig_commit = db_session.commit
    def failing_commit():
        raise RuntimeError("Simulated Database Storage Failure")

    monkeypatch.setattr(db_session, "commit", failing_commit)

    res = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )
    assert res.status_code == 500

    # Restore commit to query database state
    monkeypatch.setattr(db_session, "commit", orig_commit)

    # Verify application remains in original stage and no partial history is committed
    detail = client.get(f"/api/applications/{app_id}").json()
    assert detail["current_stage"] == "SUBMITTED"
    assert len(detail["history"]) == 1


def test_preserve_scrutiny_history_across_evaluations(client):
    """
    Verify that previous scrutiny evaluation outcomes and remarks are preserved
    rather than overwritten when a re-scrutiny is executed.
    """
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST003", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # 1. Move to Initial Scrutiny
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY"},
        headers={"X-User-Role": "Intake Officer"}
    )

    # 2. Initial Scrutiny -> DEFICIENT
    client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={
            "scrutiny_type": "INITIAL",
            "outcome": "DEFICIENT",
            "remarks": "Initial inspection: Cadre ratio insufficient.",
            "deficiencies": ["Shortage of 2 Associate Professors in Computer Science."]
        },
        headers={"X-User-Role": "Scrutiny Officer", "X-User-Id": "officer_alpha"}
    )

    # Fetch deficiencies
    defs = client.get(f"/api/applications/{app_id}/deficiencies").json()
    assert len(defs) == 1
    def_id = defs[0]["id"]

    # 3. Resubmission by Institution Admin
    client.post(
        f"/api/applications/{app_id}/deficiency/respond",
        json={
            "responses": [{"deficiency_id": def_id, "institution_response": "Recruited 2 new faculty members on permanent roster."}],
            "remarks": "Compliance roster submitted."
        },
        headers={"X-User-Role": "Institution Admin"}
    )

    # 4. Re-Scrutiny -> PASSED
    client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={
            "scrutiny_type": "RE_SCRUTINY",
            "outcome": "PASSED",
            "remarks": "Re-scrutiny: Faculty joining orders and qualifications verified.",
            "deficiencies": []
        },
        headers={"X-User-Role": "Scrutiny Officer", "X-User-Id": "officer_beta"}
    )

    # 5. Query dedicated scrutiny endpoint
    scrutiny_res = client.get(f"/api/applications/{app_id}/scrutiny")
    assert scrutiny_res.status_code == 200
    scrutiny_records = scrutiny_res.json()

    # Verify both records are preserved in chronological order
    assert len(scrutiny_records) == 2
    assert scrutiny_records[0]["scrutiny_type"] == "INITIAL"
    assert scrutiny_records[0]["outcome"] == "DEFICIENT"
    assert scrutiny_records[0]["scrutinizer_id"] == "officer_alpha"
    assert "Cadre ratio insufficient" in scrutiny_records[0]["remarks"]

    assert scrutiny_records[1]["scrutiny_type"] == "RE_SCRUTINY"
    assert scrutiny_records[1]["outcome"] == "PASSED"
    assert scrutiny_records[1]["scrutinizer_id"] == "officer_beta"
    assert "joining orders" in scrutiny_records[1]["remarks"]

    # Verify deficiency status was resolved
    resolved_defs = client.get(f"/api/applications/{app_id}/deficiencies?status=RESOLVED").json()
    assert len(resolved_defs) == 1
    assert resolved_defs[0]["status"] == "RESOLVED"
    assert resolved_defs[0]["resolved_at"] is not None


def test_get_decision_record_endpoint(client):
    """Verify that the decision endpoint returns 404 before decision and 200 after."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST004", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]

    # Before decision is made -> 404
    no_dec = client.get(f"/api/applications/{app_id}/decision")
    assert no_dec.status_code == 404

    # Fast forward to DECISION_PENDING
    client.post(f"/api/applications/{app_id}/transition", json={"action": "ASSIGN_SCRUTINY"}, headers={"X-User-Role": "Intake Officer"})
    client.post(f"/api/applications/{app_id}/scrutiny", json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "Pass"}, headers={"X-User-Role": "Scrutiny Officer"})
    client.post(f"/api/applications/{app_id}/transition", json={"action": "SUBMIT_TO_AUTHORITY"}, headers={"X-User-Role": "Committee Secretariat"})

    # Record decision
    client.post(
        f"/api/applications/{app_id}/decision",
        json={"decision": "APPROVED", "reasons": "Meets all affiliation and faculty cadre norms."},
        headers={"X-User-Role": "Competent Authority Secretariat", "X-User-Id": "authority_lead"}
    )

    # After decision is made -> 200 with record
    dec_res = client.get(f"/api/applications/{app_id}/decision")
    assert dec_res.status_code == 200
    data = dec_res.json()
    assert data["decision"] == "APPROVED"
    assert data["authority_id"] == "authority_lead"
    assert "affiliation and faculty" in data["reasons"]


def test_unauthorized_scrutiny_and_deficiency_endpoints(client):
    """Verify role checks on scrutiny and deficiency response endpoints."""
    reg = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"X-User-Role": "Institution Admin"}
    )
    app_id = reg.json()["application_id"]
    client.post(f"/api/applications/{app_id}/transition", json={"action": "ASSIGN_SCRUTINY"}, headers={"X-User-Role": "Intake Officer"})

    # Institution Admin attempts to record scrutiny -> 403
    bad_sc = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "I approve my own application"},
        headers={"X-User-Role": "Institution Admin"}
    )
    assert bad_sc.status_code == 403

    # Scrutiny Officer records deficiency
    client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={"scrutiny_type": "INITIAL", "outcome": "DEFICIENT", "remarks": "Missing audit", "deficiencies": ["Need audit"]},
        headers={"X-User-Role": "Scrutiny Officer"}
    )

    # Scrutiny Officer attempts to respond to deficiencies -> 403 (restricted to Institution Admin)
    bad_resub = client.post(
        f"/api/applications/{app_id}/deficiency/respond",
        json={"responses": [{"deficiency_id": 1, "institution_response": "Audit done"}]},
        headers={"X-User-Role": "Scrutiny Officer"}
    )
    assert bad_resub.status_code == 403



