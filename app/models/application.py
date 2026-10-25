from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utcnow_dt() -> datetime:
    return datetime.now(timezone.utc)


class Application(Base):
    """
    Core Application Entity.
    Strictly coordinates with Dataset_2_Synthetic_Applications_25 contract.
    """
    __tablename__ = "applications"

    # Core identification
    application_id = Column(String(32), primary_key=True, index=True)
    institution_id = Column(String(32), nullable=False, index=True)
    application_type = Column(String(64), nullable=False)

    # Workflow & stage tracking (kept strictly separate per contract)
    current_stage = Column(String(64), nullable=False, default="SUBMITTED", index=True)
    application_status = Column(String(32), nullable=False, default="IN_PROGRESS", index=True)
    
    # Dates & timeline
    submitted_date = Column(String(16), nullable=False, default=utcnow_str)
    stage_entered_date = Column(String(16), nullable=False, default=utcnow_str)
    due_date = Column(String(16), nullable=True)
    last_updated = Column(String(16), nullable=False, default=utcnow_str)

    # Assignment & Flags
    assigned_role = Column(String(64), nullable=False, default="Intake Officer")
    deficiency_flag = Column(String(8), nullable=False, default="No")

    # Metadata & SLA demo classifications
    data_type = Column(String(32), nullable=False, default="SYNTHETIC_DEMO")
    deadline_condition = Column(String(32), nullable=False, default="ON_TRACK")
    reference_date = Column(String(16), nullable=False, default="2026-10-25")
    demo_notes = Column(Text, nullable=True)

    # Permitted application fields (editable during permitted stages)
    academic_year = Column(String(16), nullable=True, default="2026-2027")
    contact_email = Column(String(128), nullable=True)
    contact_phone = Column(String(32), nullable=True)
    programme_name = Column(String(128), nullable=True)
    intake_approved = Column(Integer, nullable=True)

    # Relationships
    history = relationship(
        "WorkflowHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="WorkflowHistory.id"
    )
    scrutiny_records = relationship(
        "ScrutinyRecord",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ScrutinyRecord.id"
    )
    deficiency_records = relationship(
        "DeficiencyRecord",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="DeficiencyRecord.id"
    )
    decision_record = relationship(
        "DecisionRecord",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan"
    )


class WorkflowHistory(Base):
    """
    Dedicated workflow transition audit trail.
    Records every stage progression, actor, and comment.
    """
    __tablename__ = "workflow_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String(32), ForeignKey("applications.application_id"), nullable=False, index=True)
    from_stage = Column(String(64), nullable=False)
    to_stage = Column(String(64), nullable=False)
    from_status = Column(String(32), nullable=False)
    to_status = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)
    actor_id = Column(String(64), nullable=False)
    actor_role = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=utcnow_dt, nullable=False)
    remarks = Column(Text, nullable=True)

    application = relationship("Application", back_populates="history")


class ScrutinyRecord(Base):
    """
    Records scrutiny evaluation outcomes (Initial Scrutiny and Re-Scrutiny).
    """
    __tablename__ = "scrutiny_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String(32), ForeignKey("applications.application_id"), nullable=False, index=True)
    scrutiny_type = Column(String(32), nullable=False)  # INITIAL | RE_SCRUTINY
    outcome = Column(String(32), nullable=False)        # PASSED | DEFICIENT
    remarks = Column(Text, nullable=False)
    deficiency_summary = Column(Text, nullable=True)
    scrutinizer_id = Column(String(64), nullable=False)
    scrutinizer_role = Column(String(64), nullable=False, default="Scrutiny Officer")
    created_at = Column(DateTime, default=utcnow_dt, nullable=False)

    application = relationship("Application", back_populates="scrutiny_records")
    deficiencies = relationship("DeficiencyRecord", back_populates="scrutiny", cascade="all, delete-orphan")


class DeficiencyRecord(Base):
    """
    Specific deficiency request and institution resubmission tracking.
    """
    __tablename__ = "deficiency_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String(32), ForeignKey("applications.application_id"), nullable=False, index=True)
    scrutiny_id = Column(Integer, ForeignKey("scrutiny_records.id"), nullable=True)
    deficiency_text = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="OPEN")  # OPEN | RESPONDED | RESOLVED
    institution_response = Column(Text, nullable=True)
    raised_at = Column(DateTime, default=utcnow_dt, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    application = relationship("Application", back_populates="deficiency_records")
    scrutiny = relationship("ScrutinyRecord", back_populates="deficiencies")


class DecisionRecord(Base):
    """
    Authorized human decision by Competent Authority.
    Includes mandatory reasons and conditional compliance stipulations.
    """
    __tablename__ = "decision_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String(32), ForeignKey("applications.application_id"), unique=True, nullable=False, index=True)
    decision = Column(String(32), nullable=False)  # APPROVED | REJECTED | APPROVED_WITH_CONDITIONS
    reasons = Column(Text, nullable=False)
    conditions = Column(Text, nullable=True)
    authority_id = Column(String(64), nullable=False)
    authority_role = Column(String(64), nullable=False, default="Competent Authority Secretariat")
    decided_at = Column(DateTime, default=utcnow_dt, nullable=False)

    application = relationship("Application", back_populates="decision_record")
