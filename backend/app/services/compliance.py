from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.compliance import ComplianceObligation
from app.models.application import Application
from app.enums import ObligationStatus, EntityType, NotificationType, UserRole
from app.services.audit import record_audit_event
from app.services.notifications import create_notification


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_obligation_by_id(db: Session, obligation_id: str) -> ComplianceObligation:
    record = db.query(ComplianceObligation).filter(ComplianceObligation.id == obligation_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance obligation with id '{obligation_id}' not found."
        )
    return record


def list_obligations(
    db: Session,
    institution_id: Optional[str] = None,
    application_id: Optional[str] = None,
    status_filter: Optional[ObligationStatus] = None,
    skip: int = 0,
    limit: int = 50
) -> List[ComplianceObligation]:
    query = db.query(ComplianceObligation)
    if institution_id:
        query = query.filter(ComplianceObligation.institution_id == institution_id)
    if application_id:
        query = query.filter(ComplianceObligation.application_id == application_id)
    if status_filter:
        query = query.filter(ComplianceObligation.status == status_filter)
    return query.order_by(ComplianceObligation.created_at.desc()).offset(skip).limit(limit).all()


def create_compliance_obligation(
    db: Session,
    institution_id: str,
    title: str,
    obligation_type: str,
    description: str,
    application_id: Optional[str] = None,
    source_reference: str = "Illustrative Demo Configuration",
    is_illustrative_demo_rule: bool = True,
    due_date: Optional[datetime] = None,
    responsible_owner: Optional[str] = None,
    actor_id: str = "SYSTEM",
    actor_role: str = UserRole.ADMIN.value
) -> ComplianceObligation:
    # If application_id is provided, verify it exists
    if application_id:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked application '{application_id}' not found."
            )

    obligation = ComplianceObligation(
        institution_id=institution_id,
        application_id=application_id,
        title=title,
        obligation_type=obligation_type,
        description=description,
        source_reference=source_reference,
        is_illustrative_demo_rule=is_illustrative_demo_rule,
        due_date=due_date,
        responsible_owner=responsible_owner,
        status=ObligationStatus.PENDING,
        correction_history=[]
    )
    db.add(obligation)
    db.flush()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="CREATE_COMPLIANCE_OBLIGATION",
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        after_state={"status": obligation.status.value, "title": title, "institution_id": institution_id},
        reason=f"Registered compliance obligation: {title}"
    )

    db.commit()
    db.refresh(obligation)
    return obligation


def submit_obligation_evidence(
    db: Session,
    obligation_id: str,
    evidence_document_id: str,
    submission_notes: Optional[str] = None,
    actor_id: str = "INSTITUTION_REP",
    actor_role: str = UserRole.APPLICANT.value
) -> ComplianceObligation:
    obligation = get_obligation_by_id(db, obligation_id)
    # Can submit from PENDING or NEEDS_CORRECTION
    if obligation.status not in (ObligationStatus.PENDING, ObligationStatus.NEEDS_CORRECTION):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit evidence when obligation status is '{obligation.status.value}'. Must be 'PENDING' or 'NEEDS_CORRECTION'."
        )

    before_state = {
        "status": obligation.status.value,
        "evidence_document_id": obligation.evidence_document_id
    }

    obligation.status = ObligationStatus.SUBMITTED
    obligation.evidence_document_id = evidence_document_id
    obligation.submission_notes = submission_notes
    obligation.submitted_at = utc_now()
    obligation.submitted_by = actor_id

    # If resubmitting after correction, note it in correction history
    if before_state["status"] == ObligationStatus.NEEDS_CORRECTION.value and obligation.correction_history:
        history = list(obligation.correction_history)
        if history:
            history[-1]["resubmitted_at"] = utc_now().isoformat()
            history[-1]["resubmission_notes"] = submission_notes
            obligation.correction_history = history

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="SUBMIT_COMPLIANCE_EVIDENCE",
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        before_state=before_state,
        after_state={"status": obligation.status.value, "evidence_document_id": evidence_document_id},
        reason="Evidence document submitted for regulatory undertaking verification"
    )

    create_notification(
        db=db,
        recipient_role=UserRole.COMPLIANCE_OFFICER.value,
        notification_type=NotificationType.OBLIGATION_ACTION_REQUIRED.value,
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        title="Compliance Evidence Submitted",
        message=f"Evidence for obligation '{obligation.title}' has been submitted and awaits officer verification.",
        deduplication_key=f"obligation:evidence_submitted:{obligation.id}:{evidence_document_id}"
    )

    db.commit()
    db.refresh(obligation)
    return obligation


def verify_compliance_obligation(
    db: Session,
    obligation_id: str,
    verification_notes: Optional[str] = None,
    actor_id: str = "COMPLIANCE_OFFICER_1",
    actor_role: str = UserRole.COMPLIANCE_OFFICER.value
) -> ComplianceObligation:
    obligation = get_obligation_by_id(db, obligation_id)
    if obligation.status != ObligationStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot verify obligation with status '{obligation.status.value}'. Must be in 'SUBMITTED' state."
        )

    # Permission check: must be compliance officer or admin
    permitted_roles = [UserRole.COMPLIANCE_OFFICER.value, UserRole.ADMIN.value]
    if actor_role not in permitted_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor_role}' is not authorized to verify compliance obligations."
        )

    before_state = {"status": obligation.status.value}

    obligation.status = ObligationStatus.VERIFIED
    obligation.verification_result = "VERIFIED"
    obligation.verification_notes = verification_notes
    obligation.verified_at = utc_now()
    obligation.verified_by = actor_id

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="VERIFY_COMPLIANCE_OBLIGATION",
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        before_state=before_state,
        after_state={"status": obligation.status.value, "verified_by": actor_id},
        reason=verification_notes or "Obligation evidence verified as meeting standards"
    )

    create_notification(
        db=db,
        recipient_role=UserRole.APPLICANT.value,
        recipient_id=obligation.institution_id,
        notification_type=NotificationType.OBLIGATION_VERIFIED.value,
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        title="Compliance Obligation Verified",
        message=f"Compliance undertaking '{obligation.title}' has been officially verified.",
        deduplication_key=f"obligation:verified:{obligation.id}"
    )

    db.commit()
    db.refresh(obligation)
    return obligation


def request_obligation_correction(
    db: Session,
    obligation_id: str,
    reason: str,
    guidance: Optional[str] = None,
    actor_id: str = "COMPLIANCE_OFFICER_1",
    actor_role: str = UserRole.COMPLIANCE_OFFICER.value
) -> ComplianceObligation:
    obligation = get_obligation_by_id(db, obligation_id)
    if obligation.status != ObligationStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot request correction for obligation with status '{obligation.status.value}'. Must be in 'SUBMITTED' state."
        )

    permitted_roles = [UserRole.COMPLIANCE_OFFICER.value, UserRole.ADMIN.value]
    if actor_role not in permitted_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor_role}' is not authorized to request corrections."
        )

    before_state = {"status": obligation.status.value}

    obligation.status = ObligationStatus.NEEDS_CORRECTION
    obligation.correction_reason = reason
    
    # Append to correction history
    history_entry = {
        "requested_at": utc_now().isoformat(),
        "requested_by": actor_id,
        "reason": reason,
        "guidance": guidance,
        "resubmitted_at": None,
        "resubmission_notes": None
    }
    history = list(obligation.correction_history or [])
    history.append(history_entry)
    obligation.correction_history = history

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="REQUEST_OBLIGATION_CORRECTION",
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        before_state=before_state,
        after_state={"status": obligation.status.value, "reason": reason},
        reason=reason
    )

    create_notification(
        db=db,
        recipient_role=UserRole.APPLICANT.value,
        recipient_id=obligation.institution_id,
        notification_type=NotificationType.OBLIGATION_ACTION_REQUIRED.value,
        entity_type=EntityType.UNDERTAKING.value,
        entity_id=obligation.id,
        title="Compliance Correction Requested",
        message=f"Correction requested for obligation '{obligation.title}': {reason}",
        deduplication_key=f"obligation:correction_requested:{obligation.id}:{len(history)}"
    )

    db.commit()
    db.refresh(obligation)
    return obligation
