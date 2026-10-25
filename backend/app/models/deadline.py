import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Boolean, JSON
from app.db import Base
from app.enums import DeadlineStatus


def utc_now():
    return datetime.now(timezone.utc)


class DeadlineRecord(Base):
    """Deterministic deadline tracking with escalation policy and notification history."""
    __tablename__ = "deadlines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False, index=True)  # APPLICATION, EVC, UNDERTAKING, DOCUMENT
    entity_id = Column(String(100), nullable=False, index=True)
    
    deadline_type = Column(String(100), nullable=False, index=True)  # e.g. DEFICIENCY_RESPONSE, EVC_REPORT, OBLIGATION_SUBMISSION
    title = Column(String(200), nullable=False)
    due_date = Column(DateTime, nullable=False, index=True)
    
    owner_role = Column(String(50), nullable=False, index=True)
    owner_id = Column(String(100), nullable=True)
    
    source_reference = Column(String(200), nullable=False, default="Illustrative Demo Policy")
    is_statutory = Column(Boolean, default=False, nullable=False)  # Statutory vs internal warning/demo
    
    status = Column(SQLEnum(DeadlineStatus), default=DeadlineStatus.ACTIVE, nullable=False, index=True)
    warning_threshold_hours = Column(Integer, default=48, nullable=False)
    
    last_evaluated_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    escalation_policy = Column(String(100), default="NOTIFY_REGIONAL_OFFICER_ON_OVERDUE", nullable=False)
    escalation_triggered = Column(Boolean, default=False, nullable=False)
    # Escalation history: list of {timestamp, event_type, escalated_to_role, reason}
    escalation_history = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
