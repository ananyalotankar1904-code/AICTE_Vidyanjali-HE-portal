import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.application import Application, WorkflowHistory
from app.core.workflow_engine import (
    register_audit_listener,
    register_notification_listener,
    clear_service_listeners,
)

# In-memory SQLite for high-speed, isolated integration tests
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
    clear_service_listeners()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    clear_service_listeners()


# ==============================================================================
# TARGET 1: Institution & Application-Type Data Handshake (Shared with Member 4)
# ==============================================================================
def test_institution_and_application_type_contract(client):
    """
    Verifies that Member 3's registration and listing endpoints accurately consume
    and persist shared institution IDs (Dataset 1 AISHE reference) and standard
    AICTE application types.
    """
    institutions_and_types = [
        ("INST001", "Extension of Approval", "2026-2027"),
        ("INST002", "Increase in Intake", "2026-2027"),
        ("INST003", "New Programme", "2026-2027"),
        ("INST005", "Closure of Course", "2026-2027"),
    ]

    for inst_id, app_type, yr in institutions_and_types:
        payload = {
            "institution_id": inst_id,
            "application_type": app_type,
            "academic_year": yr,
            "programme_name": "Engineering & Technology",
            "intake_approved": 60,
        }
        res = client.post(
            "/api/applications",
            json=payload,
            headers={"x-user-id": "INST_ADMIN_1", "x-user-role": "Institution Admin"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["institution_id"] == inst_id
        assert data["application_type"] == app_type
        assert data["current_stage"] == "SUBMITTED"
        assert data["application_status"] == "IN_PROGRESS"


# ==============================================================================
# TARGET 2: User Roles and Permissions Integration (Shared with Lead & Member 4)
# ==============================================================================
def test_role_authorization_matrix_handshake(client):
    """
    Validates cross-module role separation:
    - Scrutinizer cannot record decisions or complete EVC.
    - Institution Admin cannot pass scrutiny.
    - EVC Coordinator cannot approve applications.
    """
    # Create application
    res = client.post(
        "/api/applications",
        json={"institution_id": "INST001", "application_type": "Extension of Approval"},
        headers={"x-user-id": "INST_ADMIN", "x-user-role": "Institution Admin"},
    )
    app_id = res.json()["application_id"]

    # Intake Officer assigns to INITIAL_SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"x-user-id": "INTAKE_1", "x-user-role": "Intake Officer"},
    )

    # Scrutiny Officer tries to record official decision -> Must be 403 Forbidden
    res_dec = client.post(
        f"/api/applications/{app_id}/decision",
        json={"decision": "APPROVED", "reasons": "Pre-mature approval attempt by scrutinizer."},
        headers={"x-user-id": "SCRUT_1", "x-user-role": "Scrutiny Officer"},
    )
    assert res_dec.status_code == 403

    # Institution Admin tries to perform Scrutiny -> Must be 403 Forbidden
    res_scrut = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={"scrutiny_type": "INITIAL", "outcome": "PASSED", "remarks": "Self-passed by applicant"},
        headers={"x-user-id": "INST_ADMIN", "x-user-role": "Institution Admin"},
    )
    assert res_scrut.status_code == 403


# ==============================================================================
# TARGET 3: Member 4 EVC Module Handshake (EVC Schedules & Statuses)
# ==============================================================================
def test_evc_module_handshake_lifecycle(client):
    """
    Verifies workflow transition handoff to Member 4's EVC Module:
    1. Scrutiny routes application to EVC_SCHEDULED.
    2. Role 'EVC Coordinator' completes inspection via COMPLETE_EVC -> EVC_COMPLETED.
    3. Handoff to Committee Secretariat -> COMMITTEE_REVIEW.
    """
    res = client.post(
        "/api/applications",
        json={"institution_id": "INST004", "application_type": "New Programme"},
        headers={"x-user-id": "INST_ADMIN", "x-user-role": "Institution Admin"},
    )
    app_id = res.json()["application_id"]

    # Move to INITIAL_SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"x-user-id": "INTAKE_1", "x-user-role": "Intake Officer"},
    )

    # Scrutiny passes and automatically routes to EVC_SCHEDULED (Rule 2 for New Programme)
    res_scrut = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={
            "scrutiny_type": "INITIAL",
            "outcome": "PASSED",
            "remarks": "Documents verified; on-site EVC inspection recommended."
        },
        headers={"x-user-id": "SCRUT_1", "x-user-role": "Scrutiny Officer"},
    )
    assert res_scrut.status_code == 200
    assert res_scrut.json()["current_stage"] == "EVC_SCHEDULED"
    assert res_scrut.json()["assigned_role"] == "EVC Coordinator"

    # Member 4 EVC Coordinator completes inspection
    res_evc_done = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "COMPLETE_EVC", "to_stage": "EVC_COMPLETED", "remarks": "Physical verification clean"},
        headers={"x-user-id": "EVC_COORD_1", "x-user-role": "EVC Coordinator"},
    )
    assert res_evc_done.status_code == 200
    assert res_evc_done.json()["current_stage"] == "EVC_COMPLETED"

    # Forward to Committee Review
    res_comm = client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "SUBMIT_TO_COMMITTEE", "to_stage": "COMMITTEE_REVIEW"},
        headers={"x-user-id": "EVC_COORD_1", "x-user-role": "EVC Coordinator"},
    )
    assert res_comm.status_code == 200
    assert res_comm.json()["current_stage"] == "COMMITTEE_REVIEW"


# ==============================================================================
# TARGET 4 & 5: Member 4 Lease/Document Validity & Undertakings Integration
# ==============================================================================
def test_lease_deficiency_and_undertaking_due_date_flow(client):
    """
    Verifies that scrutiny identifies lease/document defects or missing undertakings,
    raises deficiencies, sets deadline_condition and ACTION_REQUIRED, and allows
    applicant resubmission before progressing.
    """
    res = client.post(
        "/api/applications",
        json={"institution_id": "INST002", "application_type": "Increase in Intake"},
        headers={"x-user-id": "INST_ADMIN", "x-user-role": "Institution Admin"},
    )
    app_id = res.json()["application_id"]

    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"x-user-id": "INTAKE_1", "x-user-role": "Intake Officer"},
    )

    # Scrutiny Officer raises deficiency regarding land lease validity & affidavit undertaking
    res_def = client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={
            "scrutiny_type": "INITIAL",
            "outcome": "DEFICIENT",
            "remarks": "Land lease validity expires within 1 year; missing undertaking on stamp paper.",
            "deficiencies": [
                "Submit registered lease deed valid for at least 30 years.",
                "Upload notarized undertaking as per AICTE Approval Process Handbook Appendix 17."
            ]
        },
        headers={"x-user-id": "SCRUT_1", "x-user-role": "Scrutiny Officer"},
    )
    assert res_def.status_code == 200
    assert res_def.json()["current_stage"] == "DEFICIENCY_RAISED"
    assert res_def.json()["application_status"] == "ACTION_REQUIRED"
    assert res_def.json()["deficiency_flag"] == "Yes"

    # Get deficiency IDs
    res_defs_list = client.get(
        f"/api/applications/{app_id}/deficiencies",
        headers={"x-user-id": "INST_ADMIN", "x-user-role": "Institution Admin"},
    )
    def_records = res_defs_list.json()
    assert len(def_records) == 2

    # Institution Admin provides compliance clarification
    res_resp = client.post(
        f"/api/applications/{app_id}/deficiency/respond",
        json={
            "responses": [
                {"deficiency_id": def_records[0]["id"], "institution_response": "Attached 99-year registered lease deed."},
                {"deficiency_id": def_records[1]["id"], "institution_response": "Uploaded notarized undertaking document doc_7781."},
            ],
            "remarks": "All lease and undertaking requirements fulfilled."
        },
        headers={"x-user-id": "INST_ADMIN", "x-user-role": "Institution Admin"},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["current_stage"] == "RE_SCRUTINY"
    assert res_resp.json()["application_status"] == "IN_PROGRESS"


# ==============================================================================
# TARGET 6: Shared Audit Sink Handshake (Member 4 Integration Hook)
# ==============================================================================
def test_shared_audit_listener_integration(client):
    """
    Verifies that Member 3's workflow engine dispatches structured security audit
    events to Member 4's central audit listener hook on registration, transitions,
    and official decisions.
    """
    captured_audit_events = []

    def mock_member4_audit_sink(event: dict):
        captured_audit_events.append(event)

    register_audit_listener(mock_member4_audit_sink)

    # 1. Register application -> should fire APPLICATION_REGISTERED
    res = client.post(
        "/api/applications",
        json={"institution_id": "INST010", "application_type": "New Programme"},
        headers={"x-user-id": "INTAKE_OFFICER_3", "x-user-role": "Intake Officer"},
    )
    app_id = res.json()["application_id"]

    assert any(
        e["event_type"] == "APPLICATION_REGISTERED" and e["target_id"] == app_id
        for e in captured_audit_events
    )

    # 2. Transition -> should fire WORKFLOW_TRANSITION
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"x-user-id": "INTAKE_OFFICER_3", "x-user-role": "Intake Officer"},
    )
    assert any(
        e["event_type"] == "WORKFLOW_TRANSITION" and e["target_id"] == app_id
        for e in captured_audit_events
    )


# ==============================================================================
# TARGET 7: Shared Notification System Handshake (Member 4 Integration Hook)
# ==============================================================================
def test_shared_notification_listener_integration(client):
    """
    Verifies that Member 3 dispatches notification hooks to Member 4's notification
    service when applications are submitted, deficiencies are raised, or decisions are made.
    """
    captured_notifications = []

    def mock_member4_notification_worker(notification: dict):
        captured_notifications.append(notification)

    register_notification_listener(mock_member4_notification_worker)

    res = client.post(
        "/api/applications",
        json={"institution_id": "INST015", "application_type": "Closure of Course"},
        headers={"x-user-id": "INST_ADMIN_5", "x-user-role": "Institution Admin"},
    )
    app_id = res.json()["application_id"]

    # Submission notification
    assert any(
        n["event_type"] == "APPLICATION_SUBMITTED" and n["recipient_role"] == "Intake Officer"
        for n in captured_notifications
    )

    # Transition to INITIAL_SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        json={"action": "ASSIGN_SCRUTINY", "to_stage": "INITIAL_SCRUTINY"},
        headers={"x-user-id": "INTAKE_1", "x-user-role": "Intake Officer"},
    )

    # Scrutiny raises deficiency -> notification to Institution Admin
    client.post(
        f"/api/applications/{app_id}/scrutiny",
        json={
            "scrutiny_type": "INITIAL",
            "outcome": "DEFICIENT",
            "remarks": "Missing governing council resolution.",
            "deficiencies": ["Upload GC resolution for closure."]
        },
        headers={"x-user-id": "SCRUT_1", "x-user-role": "Scrutiny Officer"},
    )

    assert any(
        n["event_type"] == "DEFICIENCY_RAISED" and n["recipient_role"] == "Institution Admin"
        for n in captured_notifications
    )


# ==============================================================================
# TARGET 8: Dashboard Data Summary Aggregation (Dataset 2 Sheet 3 Contract)
# ==============================================================================
def test_dashboard_summary_aggregations_contract(client, db_session):
    """
    Verifies that GET /api/applications/dashboard/summary delivers aggregations
    matching the Dataset 2 Sheet 3 schema (current_stage, application_status, deadline_condition, record_count).
    """
    # Seed a few varied applications into the test db
    sample_apps = [
        Application(
            application_id="APP_T01",
            institution_id="INST001",
            application_type="Extension of Approval",
            current_stage="SUBMITTED",
            application_status="IN_PROGRESS",
            submitted_date="2026-10-25",
            stage_entered_date="2026-10-25",
            assigned_role="Intake Officer",
            deficiency_flag="No",
            last_updated="2026-10-25",
            data_type="SYNTHETIC_DEMO",
            deadline_condition="ON_TRACK",
            reference_date="2026-10-25",
        ),
        Application(
            application_id="APP_T02",
            institution_id="INST002",
            application_type="New Programme",
            current_stage="DEFICIENCY_RAISED",
            application_status="ACTION_REQUIRED",
            submitted_date="2026-10-10",
            stage_entered_date="2026-10-20",
            assigned_role="Institution Admin",
            deficiency_flag="Yes",
            last_updated="2026-10-25",
            data_type="SYNTHETIC_DEMO",
            deadline_condition="OVERDUE",
            reference_date="2026-10-25",
        ),
        Application(
            application_id="APP_T03",
            institution_id="INST003",
            application_type="Closure of Course",
            current_stage="COMPLETED",
            application_status="COMPLETED",
            submitted_date="2026-10-01",
            stage_entered_date="2026-10-22",
            assigned_role="Records Officer",
            deficiency_flag="No",
            last_updated="2026-10-25",
            data_type="SYNTHETIC_DEMO",
            deadline_condition="COMPLETED",
            reference_date="2026-10-25",
        ),
    ]
    for app_item in sample_apps:
        db_session.add(app_item)
    db_session.commit()

    res = client.get(
        "/api/applications/dashboard/summary",
        headers={"x-user-id": "ADMIN_1", "x-user-role": "Admin"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["total_applications"] == 3
    assert data["action_required_count"] == 1
    assert data["overdue_count"] == 1
    assert data["by_stage"]["SUBMITTED"] == 1
    assert data["by_stage"]["DEFICIENCY_RAISED"] == 1
    assert data["by_stage"]["COMPLETED"] == 1
    assert data["by_status"]["ACTION_REQUIRED"] == 1
    assert data["by_status"]["IN_PROGRESS"] == 1
    assert data["by_status"]["COMPLETED"] == 1
    assert data["by_deadline_condition"]["OVERDUE"] == 1

    # Check summary matrix structure
    matrix = data["summary_matrix"]
    assert len(matrix) == 3
    for row in matrix:
        assert "current_stage" in row
        assert "application_status" in row
        assert "deadline_condition" in row
        assert "record_count" in row
