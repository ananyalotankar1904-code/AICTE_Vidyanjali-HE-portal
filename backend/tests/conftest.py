import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.db import Base, get_db
from backend.app.main import app
from backend.app.models.application import Application
from backend.app.enums import ApplicationStatus, WorkflowStage

# In-memory SQLite database isolated for each test run
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh isolated database for each test and tears it down afterwards."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Pre-seed a test application
    test_app = Application(
        id="test-app-001",
        application_number="APP-TEST-001",
        institution_id="INST-TEST-01",
        institution_name="Test Institute of Technology",
        application_type="EXTENSION_OF_APPROVAL",
        route_id="ROUTE_FULL_SCRUTINY_EVC",
        status=ApplicationStatus.SUBMITTED,
        current_stage=WorkflowStage.SCRUTINY,
    )
    db.add(test_app)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient with the isolated database session overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
