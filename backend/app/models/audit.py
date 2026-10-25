import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from backend.app.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    """Immutable audit trail event tracking key system and compliance actions."""
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(100), nullable=False, index=True)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    reason = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
