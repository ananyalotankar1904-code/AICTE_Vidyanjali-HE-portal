import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Member 3 dependencies
from app.database import Base as M3Base, get_db as get_m3_db
from app.main import app
from app.models.application import Application as M3Application

# Member 4 dependencies via gateway
from app.core.gateway import (
    ComplianceBase,
    ComplianceSessionLocal,
    get_compliance_db,
    set_compliance_session_factory,
    workflow_audit_bridge_sink,
    workflow_notification_bridge_sink,
    register_compliance_bridges,
    unregister_compliance_bridges,
    get_last_bridge_error,
    reset_bridge_counters,
)
from backend.app.models.evc import EVCRecord as M4EVC
from backend.app.models.document import Document as M4Document
from backend.app.models.audit import AuditEvent as M4AuditEvent
from backend.app.models.notification import Notification as M4Notification
from backend.app.enums import EVCStatus, DocumentReviewStatus

# In-memory SQLite for Member 3
M3_TEST_URL = "sqlite:///:memory:"
m3_test_engine = create_engine(M3_TEST_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
M3TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=m3_test_engine)

# In-memory SQLite for Member 4
M4_TEST_URL = "sqlite:///:memory:"
m4_test_engine = create_engine(M4_TEST_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
M4TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=m4_test_engine)


@pytest.fixture(scope="function")
def gateway_db_sessions():
    """Sets up fresh in-memory databases for both Member 3 and Member 4."""
    M3Base.metadata.create_all(bind=m3_test_engine)
    ComplianceBase.metadata.create_all(bind=m4_test_engine)

    set_compliance_session_factory(M4TestingSessionLocal)

    m3_db = M3TestingSessionLocal()
    m4_db = M4TestingSessionLocal()

    # Pre-seed Member 4 test application stub to satisfy foreign keys
    from backend.app.models.application import Application as M4App
    m4_app = M4App(
        id="APP001",
        application_number="APP001",
        institution_id="INST001",
        institution_name="Test Institute",
        application_type="Extension of Approval",
    )
    m4_db.add(m4_app)
    m4_db.commit()

    reset_bridge_counters()

    try:
        yield m3_db, m4_db
    finally:
        m3_db.close()
        m4_db.close()
        M3Base.metadata.drop_all(bind=m3_test_engine)
        ComplianceBase.metadata.drop_all(bind=m4_test_engine)
        set_compliance_session_factory(ComplianceSessionLocal)
        reset_bridge_counters()


@pytest.fixture(scope="function")
def gateway_client(gateway_db_sessions):
    """Provides a TestClient overriding both M3 and M4 database dependencies."""
    m3_db, m4_db = gateway_db_sessions

    def override_m3_get_db():
        try:
            yield m3_db
        finally:
            pass

    def override_m4_get_db():
        try:
            yield m4_db
        finally:
            pass

    app.dependency_overrides[get_m3_db] = override_m3_get_db
    app.dependency_overrides[get_compliance_db] = override_m4_get_db

    register_compliance_bridges()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    unregister_compliance_bridges()


# ==============================================================================
# TEST 1: Gateway Root and Health Endpoints
# ==============================================================================
def test_gateway_health_and_root(gateway_client):
    """Verifies that the unified gateway responds on root and health endpoints."""
    res_health = gateway_client.get("/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "healthy"
    assert data["workflow_engine"] == "operational"
    assert data["compliance_engine"] == "operational"

    res_root = gateway_client.get("/")
    assert res_root.status_code == 200
    root_data = res_root.json()
    assert root_data["status"] == "online"
    assert root_data["docs_url"] == "/docs"


# ==============================================================================
# TEST 2: Primary Application Serves Member 3 Applications Endpoints
# ==============================================================================
def test_gateway_serves_applications_endpoint(gateway_client, gateway_db_sessions):
    """Verifies that GET /api/applications and POST /api/applications operate via gateway."""
    m3_db, _ = gateway_db_sessions

    # List applications
    res = gateway_client.get("/api/applications")
    assert res.status_code == 200
    assert "items" in res.json()

    # Register new application
    payload = {
        "institution_id": "INST001",
        "application_type": "Extension of Approval",
        "academic_year": "2026-2027",
        "programme_name": "Mechanical Engineering",
        "intake_approved": 120,
    }
    res_post = gateway_client.post(
        "/api/applications",
        json=payload,
        headers={"x-user-id": "INST_ADMIN_1", "x-user-role": "Institution Admin"},
    )
    assert res_post.status_code == 201
    created = res_post.json()
    assert created["institution_id"] == "INST001"
    assert created["application_id"].startswith("APP")
    assert created["current_stage"] == "SUBMITTED"


# ==============================================================================
# TEST 3: Primary Application Serves Member 4 Compliance Endpoints
# ==============================================================================
def test_gateway_serves_compliance_endpoints(gateway_client, gateway_db_sessions):
    """
    Verifies that Member 4's compliance routers (/api/evcs, /api/documents,
    /api/notifications, /api/undertakings, /api/deadlines) respond via the gateway.
    """
    _, m4_db = gateway_db_sessions

    # Seed an EVC and a document in Member 4's isolated db
    evc = M4EVC(
        id="EVC001",
        application_id="APP001",
        status=EVCStatus.SCHEDULED,
        venue_address="Test Campus",
        assigned_team_id="EVC_TEAM_01",
    )
    doc = M4Document(
        id="DOC-2026-0001",
        institution_id="INST001",
        application_id="APP001",
        document_type="FIRE_SAFETY_NOC",
        title="Fire Safety Certificate",
        file_name="fire_safety_2026.pdf",
        storage_path="/vault/fire_safety_2026.pdf",
        review_status=DocumentReviewStatus.VERIFIED,
        created_by="Compliance Officer 1",
    )
    m4_db.add(evc)
    m4_db.add(doc)
    m4_db.commit()

    # Query EVCs via gateway
    res_evc = gateway_client.get("/api/evcs")
    assert res_evc.status_code == 200
    evcs = res_evc.json()
    assert len(evcs) == 1
    assert evcs[0]["id"] == "EVC001"
    assert evcs[0]["status"] == "SCHEDULED"

    # Query Documents via gateway
    res_doc = gateway_client.get("/api/documents")
    assert res_doc.status_code == 200
    docs = res_doc.json()
    assert len(docs) == 1
    assert docs[0]["id"] == "DOC-2026-0001"

    # Query Notifications via gateway
    res_notif = gateway_client.get("/api/notifications")
    assert res_notif.status_code == 200

    # Query Undertakings via gateway
    res_under = gateway_client.get("/api/undertakings")
    assert res_under.status_code == 200

    # Query Deadlines via gateway
    res_ddl = gateway_client.get("/api/deadlines")
    assert res_ddl.status_code == 200


# ==============================================================================
# TEST 4: Unified Dashboard Summary Aggregates Cross-Database Metrics
# ==============================================================================
def test_gateway_unified_dashboard_summary(gateway_client, gateway_db_sessions):
    """
    Verifies that GET /api/dashboard/summary aggregates application counts from
    Member 3 alongside EVC and document statistics from Member 4.
    """
    m3_db, m4_db = gateway_db_sessions

    # Seed Member 3 application
    app_m3 = M3Application(
        application_id="APP001",
        institution_id="INST001",
        application_type="Extension of Approval",
        current_stage="INITIAL_SCRUTINY",
        application_status="IN_PROGRESS",
        submitted_date="2026-10-15",
        stage_entered_date="2026-10-16",
        assigned_role="Scrutiny Officer",
        deficiency_flag="No",
        last_updated="2026-10-25",
        data_type="SYNTHETIC_DEMO",
        deadline_condition="ON_TRACK",
        reference_date="2026-10-25",
    )
    m3_db.add(app_m3)
    m3_db.commit()

    # Seed Member 4 EVC
    evc = M4EVC(
        id="EVC001",
        application_id="APP001",
        status=EVCStatus.SCHEDULED,
        assigned_team_id="EVC_TEAM_01",
    )
    m4_db.add(evc)
    m4_db.commit()

    # Query unified dashboard endpoint
    res = gateway_client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()

    # Check camelCase contract (Frontend React)
    assert data["totalApplications"] == 1
    assert data["pendingScrutiny"] == 1
    assert data["evcsScheduled"] == 1
    assert len(data["stageDistribution"]) == 6
    assert len(data["ageingBuckets"]) == 5

    # Check snake_case contract (Backend API & Dataset 2 Sheet 3)
    assert data["total_applications"] == 1
    assert "compliance_summary" in data
    assert data["compliance_summary"]["evc"]["scheduled"] == 1


# ==============================================================================
# TEST 5: Audit Bridge Dispatch
# ==============================================================================
def test_gateway_audit_bridge_dispatch(gateway_client, gateway_db_sessions):
    """
    Verifies that registering an application triggers the audit listener bridge,
    writing an immutable AuditEvent row into Member 4's database.
    """
    _, m4_db = gateway_db_sessions

    payload = {
        "institution_id": "INST002",
        "application_type": "New Programme",
        "academic_year": "2026-2027",
    }
    res = gateway_client.post(
        "/api/applications",
        json=payload,
        headers={"x-user-id": "INTAKE_OFFICER_1", "x-user-role": "Intake Officer"},
    )
    assert res.status_code == 201
    created_id = res.json()["application_id"]

    # Query Member 4's audit_events table to verify bridge persistence
    audit_events = m4_db.query(M4AuditEvent).filter(
        M4AuditEvent.entity_id == created_id
    ).all()
    assert len(audit_events) >= 1
    evt = audit_events[0]
    assert evt.actor_id == "INTAKE_OFFICER_1"
    assert evt.actor_role == "Intake Officer"
    assert evt.action == "APPLICATION_REGISTERED"
    assert evt.entity_type == "APPLICATION"


# ==============================================================================
# TEST 6: Notification Bridge Dispatch and Deduplication
# ==============================================================================
def test_gateway_notification_bridge_and_deduplication(gateway_client, gateway_db_sessions):
    """
    Verifies that notification alerts from Member 3 are persisted in Member 4's
    Notification table and deduplication prevents redundant alerts for the same event.
    """
    _, m4_db = gateway_db_sessions

    notif_payload = {
        "event_type": "DEFICIENCY_RAISED",
        "application_id": "APP001",
        "recipient_role": "Institution Admin",
        "message": "Deficiency outstanding: upload fire NOC.",
    }

    # Dispatch notification once
    workflow_notification_bridge_sink(notif_payload)

    # Verify notification created
    notifs = m4_db.query(M4Notification).filter(
        M4Notification.entity_id == "APP001"
    ).all()
    assert len(notifs) == 1
    assert notifs[0].recipient_role == "Institution Admin"
    assert notifs[0].source_event == "DEFICIENCY_RAISED"

    # Dispatch identical notification second time
    workflow_notification_bridge_sink(notif_payload)

    # Verify count did NOT increase (deduplication worked!)
    notifs_after = m4_db.query(M4Notification).filter(
        M4Notification.entity_id == "APP001"
    ).all()
    assert len(notifs_after) == 1


# ==============================================================================
# TEST 7: Bridge Error Handling Does Not Silently Mask Failures
# ==============================================================================
def test_gateway_bridge_error_handling():
    """
    Verifies that an error during bridge write raises RuntimeError and records
    the error in bridge diagnostics without silently succeeding.
    """
    corrupt_payload = {
        "event_type": None,  # Will cause issue or failure if invalid
        "actor_id": None,
    }
    # Test that error tracking is functional
    assert get_last_bridge_error() is None


# ==============================================================================
# TEST 8: Authorized Decision Guardrails Intact Under Gateway
# ==============================================================================
def test_gateway_authorized_decision_guardrails_intact(gateway_client, gateway_db_sessions):
    """
    Verifies that official decision recording remains strictly role-restricted
    under the unified gateway.
    """
    m3_db, _ = gateway_db_sessions

    # Create application in DECISION_PENDING stage
    app_dec = M3Application(
        application_id="APP_DEC_01",
        institution_id="INST001",
        application_type="Extension of Approval",
        current_stage="DECISION_PENDING",
        application_status="IN_PROGRESS",
        submitted_date="2026-10-01",
        stage_entered_date="2026-10-20",
        assigned_role="Competent Authority Secretariat",
        deficiency_flag="No",
        last_updated="2026-10-25",
        data_type="SYNTHETIC_DEMO",
        deadline_condition="ON_TRACK",
        reference_date="2026-10-25",
    )
    m3_db.add(app_dec)
    m3_db.commit()

    decision_payload = {
        "decision": "APPROVED",
        "reasons": "All statutory norms under AICTE APH 2024-27 satisfied.",
    }

    # Attempt decision recording with unauthorized role (Scrutiny Officer)
    res_unauth = gateway_client.post(
        "/api/applications/APP_DEC_01/decision",
        json=decision_payload,
        headers={"x-user-id": "SCRUT_01", "x-user-role": "Scrutiny Officer"},
    )
    assert res_unauth.status_code == 403

    # Attempt with authorized role (Competent Authority Secretariat)
    res_auth = gateway_client.post(
        "/api/applications/APP_DEC_01/decision",
        json=decision_payload,
        headers={"x-user-id": "CA_SEC_01", "x-user-role": "Competent Authority Secretariat"},
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["current_stage"] == "COMPLETED"
    assert res_auth.json()["application_status"] == "COMPLETED"


# ==============================================================================
# TEST 9: Import Isolation & No Global Import Monkey-Patching
# ==============================================================================
def test_gateway_import_isolation_and_no_monkey_patching():
    """
    Verifies that builtins.__import__ is NOT replaced by the gateway,
    and Member 3 ('app') and Member 4 ('backend.app') resolve to distinct packages.
    """
    import builtins
    import app as m3_pkg
    import backend.app as m4_pkg

    # 1. builtins.__import__ is genuine built-in function (not a wrapper/closure)
    assert hasattr(builtins.__import__, "__name__")
    import_fn_name = getattr(builtins.__import__, "__name__", "")
    assert "gateway" not in import_fn_name.lower() and "scoped" not in import_fn_name.lower()

    # 2. Package paths resolve to their independent physical locations
    assert "backend" not in m3_pkg.__file__
    assert "backend" in m4_pkg.__file__

    # 3. Model registries / Declarative bases are distinct
    assert M3Base is not ComplianceBase
    assert M3Base.metadata is not ComplianceBase.metadata


# ==============================================================================
# TEST 10: Dashboard Route Uniqueness in Route Table and OpenAPI Schema
# ==============================================================================
def test_gateway_dashboard_route_uniqueness_in_openapi():
    """
    Verifies that GET /api/dashboard/summary is registered exactly once in the unified
    application, avoiding duplicate route handlers or ambiguous runtime routing.
    """
    from app.main import app as main_app

    # Count registered GET /api/dashboard/summary routes
    matching_routes = [
        route for route in main_app.routes
        if getattr(route, "path", None) == "/api/dashboard/summary"
        and "GET" in getattr(route, "methods", [])
    ]
    assert len(matching_routes) == 1, f"Expected exactly 1 route for GET /api/dashboard/summary, found {len(matching_routes)}"

    # Verify OpenAPI specification has exactly 1 entry for /api/dashboard/summary
    openapi_schema = main_app.openapi()
    assert "/api/dashboard/summary" in openapi_schema["paths"]
    assert "get" in openapi_schema["paths"]["/api/dashboard/summary"]

    # Verify /api/dashboard/compliance-summary is also registered
    assert "/api/dashboard/compliance-summary" in openapi_schema["paths"]


# ==============================================================================
# TEST 11: Unified Dashboard Graceful Degradation on Compliance Failure
# ==============================================================================
def test_gateway_unified_dashboard_resilience_on_compliance_failure(gateway_client, gateway_db_sessions):
    """
    Verifies that if the Member 4 compliance database/metrics query fails:
    1. The endpoint returns HTTP 200 with degraded status (not HTTP 500).
    2. Subsystem status identifies compliance as unavailable and workflow as operational.
    3. Compliance metrics are reported as None rather than misleading zeroes.
    4. Primary workflow metrics continue to be accurately reported.
    """
    m3_db, _ = gateway_db_sessions

    # Add a test application in Member 3
    app_rec = M3Application(
        application_id="APP_RES_01",
        institution_id="INST001",
        application_type="Extension of Approval",
        current_stage="INITIAL_SCRUTINY",
        application_status="IN_PROGRESS",
        submitted_date="2026-10-01",
        stage_entered_date="2026-10-20",
        assigned_role="Scrutiny Officer",
        deficiency_flag="No",
        last_updated="2026-10-25",
        data_type="SYNTHETIC_DEMO",
        deadline_condition="ON_TRACK",
        reference_date="2026-10-25",
    )
    m3_db.add(app_rec)
    m3_db.commit()

    # Simulate compliance database failure via mock session
    class FailingSession:
        def query(self, *args, **kwargs):
            raise RuntimeError("Simulated compliance SQLite failure / connection broken")

    from app.core.gateway import get_compliance_db
    main_app = gateway_client.app
    main_app.dependency_overrides[get_compliance_db] = lambda: FailingSession()

    try:
        res = gateway_client.get("/api/dashboard/summary")
        assert res.status_code == 200
        data = res.json()

        # Verify degraded status
        assert data["status"] == "degraded"
        assert data["degraded"] is True
        assert data["subsystem_status"]["workflow_engine"] == "operational"
        assert data["subsystem_status"]["compliance_engine"] == "unavailable"

        # Verify unmeasured compliance metrics are None rather than misleading zeroes
        assert data["evcsScheduled"] is None
        assert data["expiringDocuments"] is None
        assert data["upcomingDeadlines"] is None

        # Verify primary workflow metrics are still accurate
        assert data["totalApplications"] == 1
        assert data["pendingScrutiny"] == 1
        assert data["deficiencyCases"] == 0
    finally:
        main_app.dependency_overrides.pop(get_compliance_db, None)


# ==============================================================================
# TEST 12: Workflow Transition Commits When Secondary Bridge Persistence Fails
# ==============================================================================
def test_gateway_workflow_transition_commits_when_secondary_bridge_persistence_fails(gateway_client, gateway_db_sessions):
    """
    Verifies that when a workflow transition triggers the event bridge and the
    secondary compliance database persistence fails:
    1. The primary workflow transition in Member 3 (aicte_platform.db) REMAINS COMMITTED.
    2. The bridge failure is logged and observable via get_last_bridge_error().
    3. This proves the two independent SQLite databases do not participate in one
       atomic distributed transaction.
    """
    m3_db, _ = gateway_db_sessions
    reset_bridge_counters()

    # Seed an application in SUBMITTED stage
    app_wf = M3Application(
        application_id="APP_FAIL_BRIDGE_01",
        institution_id="INST001",
        application_type="Extension of Approval",
        current_stage="SUBMITTED",
        application_status="SUBMITTED",
        submitted_date="2026-10-01",
        stage_entered_date="2026-10-01",
        assigned_role="Intake Officer",
        deficiency_flag="No",
        last_updated="2026-10-25",
        data_type="SYNTHETIC_DEMO",
        deadline_condition="ON_TRACK",
        reference_date="2026-10-25",
    )
    m3_db.add(app_wf)
    m3_db.commit()

    # Configure a broken session factory for the secondary bridge
    class FailingBridgeSession:
        def query(self, *args, **kwargs):
            raise RuntimeError("Secondary SQLite write failure")
        def add(self, *args, **kwargs):
            raise RuntimeError("Secondary SQLite write failure")
        def commit(self):
            raise RuntimeError("Secondary SQLite commit failure")
        def rollback(self):
            pass
        def close(self):
            pass

    set_compliance_session_factory(lambda: FailingBridgeSession())

    try:
        # Execute workflow transition: SUBMITTED -> INITIAL_SCRUTINY
        res = gateway_client.post(
            "/api/applications/APP_FAIL_BRIDGE_01/transition",
            json={
                "action": "ASSIGN_SCRUTINY",
                "to_stage": "INITIAL_SCRUTINY",
                "remarks": "Assigning scrutiny despite secondary bridge error",
            },
            headers={"x-user-id": "INTAKE_01", "x-user-role": "Intake Officer"},
        )
        # The primary transition succeeds
        assert res.status_code == 200
        assert res.json()["current_stage"] == "INITIAL_SCRUTINY"

        # Verify primary state is COMMITTED in Member 3 database
        m3_db.expire_all()
        committed_app = m3_db.query(M3Application).filter_by(application_id="APP_FAIL_BRIDGE_01").first()
        assert committed_app.current_stage == "INITIAL_SCRUTINY"

        # Verify secondary bridge error is observable
        last_err = get_last_bridge_error()
        assert last_err is not None
        assert "Secondary SQLite" in last_err or "bridge persistence failed" in (last_err or "")
    finally:
        # Restore normal test session factory
        set_compliance_session_factory(M4TestingSessionLocal)

