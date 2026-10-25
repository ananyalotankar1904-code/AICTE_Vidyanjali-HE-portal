import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aicte.db")

# For SQLite, ensure check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all database tables defined on Base metadata."""
    # Import all models to ensure they are registered with Base metadata
    from backend.app.models.application import Application
    from backend.app.models.audit import AuditEvent
    from backend.app.models.evc import EVCRecord
    from backend.app.models.compliance import ComplianceObligation
    from backend.app.models.document import Document
    from backend.app.models.deadline import DeadlineRecord
    from backend.app.models.notification import Notification

    Base.metadata.create_all(bind=engine)
