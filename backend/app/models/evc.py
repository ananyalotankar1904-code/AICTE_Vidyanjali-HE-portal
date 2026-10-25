import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums import EVCStatus, EVCRecommendation, EVCReportReviewOutcome


def utc_now():
    return datetime.now(timezone.utc)


class EVCRecord(Base):
    """Represents an Expert Visit Committee (EVC) verification lifecycle."""
    __tablename__ = "evc_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    
    status = Column(SQLEnum(EVCStatus), default=EVCStatus.PENDING_SCHEDULING, nullable=False, index=True)
    assigned_team_id = Column(String(100), nullable=True)
    assigned_members = Column(JSON, nullable=True)  # List of member names/roles
    
    planned_visit_date = Column(DateTime, nullable=True)
    actual_visit_date = Column(DateTime, nullable=True)
    venue_address = Column(String(300), nullable=True)
    scheduling_notes = Column(Text, nullable=True)
    
    # Rescheduling tracking: list of {previous_date, new_date, reason, rescheduled_by, rescheduled_at}
    reschedule_history = Column(JSON, default=list, nullable=False)
    
    # Visit completion findings & report
    visit_notes = Column(Text, nullable=True)
    findings_summary = Column(Text, nullable=True)
    recommendation = Column(SQLEnum(EVCRecommendation), nullable=True)
    report_document_id = Column(String(100), nullable=True)
    report_submitted_at = Column(DateTime, nullable=True)
    report_submitted_by = Column(String(100), nullable=True)
    
    # Report review outcome (Reviewer can accept or request clarification; does NOT decide statutory approval)
    report_reviewed_at = Column(DateTime, nullable=True)
    report_reviewed_by = Column(String(100), nullable=True)
    report_review_outcome = Column(SQLEnum(EVCReportReviewOutcome), nullable=True)
    report_review_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="evc_records")
