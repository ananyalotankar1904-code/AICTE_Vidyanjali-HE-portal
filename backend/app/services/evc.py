from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.evc import EVCRecord
from app.models.application import Application
from app.enums import EVCStatus, EVCRecommendation, EVCReportReviewOutcome, EntityType, NotificationType, UserRole
from app.services.audit import record_audit_event
from app.services.notifications import create_notification


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_evc_by_id(db: Session, evc_id: str) -> EVCRecord:
    record = db.query(EVCRecord).filter(EVCRecord.id == evc_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EVC record with id '{evc_id}' not found."
        )
    return record


def list_evcs(
    db: Session,
    application_id: Optional[str] = None,
    status_filter: Optional[EVCStatus] = None,
    assigned_team_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[EVCRecord]:
    query = db.query(EVCRecord)
    if application_id:
        query = query.filter(EVCRecord.application_id == application_id)
    if status_filter:
        query = query.filter(EVCRecord.status == status_filter)
    if assigned_team_id:
        query = query.filter(EVCRecord.assigned_team_id == assigned_team_id)
    return query.order_by(EVCRecord.created_at.desc()).offset(skip).limit(limit).all()


def create_evc_record(
    db: Session,
    application_id: str,
    assigned_team_id: Optional[str] = None,
    assigned_members: Optional[List[str]] = None,
    venue_address: Optional[str] = None,
    scheduling_notes: Optional[str] = None,
    actor_id: str = "SYSTEM",
    actor_role: str = UserRole.ADMIN.value
) -> EVCRecord:
    # Verify application exists
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found. Cannot create EVC record."
        )

    evc = EVCRecord(
        application_id=application_id,
        status=EVCStatus.PENDING_SCHEDULING,
        assigned_team_id=assigned_team_id,
        assigned_members=assigned_members or [],
        venue_address=venue_address,
        scheduling_notes=scheduling_notes,
        reschedule_history=[]
    )
    db.add(evc)
    db.flush()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="CREATE_EVC_RECORD",
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        after_state={"status": evc.status.value, "application_id": application_id},
        reason="Initiated EVC lifecycle for application verification"
    )
    db.commit()
    db.refresh(evc)
    return evc


def schedule_evc_visit(
    db: Session,
    evc_id: str,
    planned_visit_date: datetime,
    venue_address: Optional[str] = None,
    assigned_team_id: Optional[str] = None,
    assigned_members: Optional[List[str]] = None,
    notes: Optional[str] = None,
    actor_id: str = "OFFICER",
    actor_role: str = UserRole.SCRUTINY_OFFICER.value
) -> EVCRecord:
    evc = get_evc_by_id(db, evc_id)
    if evc.status != EVCStatus.PENDING_SCHEDULING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot schedule EVC visit from status '{evc.status.value}'. Must be in '{EVCStatus.PENDING_SCHEDULING.value}'."
        )

    before_state = {"status": evc.status.value, "planned_visit_date": None}

    evc.status = EVCStatus.SCHEDULED
    evc.planned_visit_date = planned_visit_date
    if venue_address:
        evc.venue_address = venue_address
    if assigned_team_id:
        evc.assigned_team_id = assigned_team_id
    if assigned_members:
        evc.assigned_members = assigned_members
    if notes:
        evc.scheduling_notes = notes

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="SCHEDULE_EVC_VISIT",
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        before_state=before_state,
        after_state={"status": evc.status.value, "planned_visit_date": planned_visit_date.isoformat()},
        reason=notes or "EVC visit scheduled"
    )

    create_notification(
        db=db,
        recipient_role=UserRole.EVC_TEAM.value,
        notification_type=NotificationType.EVC_SCHEDULED.value,
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        title="EVC Visit Scheduled",
        message=f"EVC visit for application {evc.application_id} has been scheduled for {planned_visit_date.strftime('%Y-%m-%d %H:%M')}.",
        deduplication_key=f"evc:scheduled:{evc.id}:{planned_visit_date.strftime('%Y%m%d%H%M')}"
    )

    db.commit()
    db.refresh(evc)
    return evc


def reschedule_evc_visit(
    db: Session,
    evc_id: str,
    new_planned_visit_date: datetime,
    reason: str,
    notes: Optional[str] = None,
    actor_id: str = "OFFICER",
    actor_role: str = UserRole.SCRUTINY_OFFICER.value
) -> EVCRecord:
    evc = get_evc_by_id(db, evc_id)
    if evc.status != EVCStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reschedule visit when current status is '{evc.status.value}'. Must be in '{EVCStatus.SCHEDULED.value}'."
        )

    previous_date_str = evc.planned_visit_date.isoformat() if evc.planned_visit_date else None
    
    # Preserve rescheduling history without silently overwriting previous schedule
    history_entry = {
        "previous_date": previous_date_str,
        "new_date": new_planned_visit_date.isoformat(),
        "reason": reason,
        "rescheduled_by": actor_id,
        "rescheduled_at": utc_now().isoformat(),
        "notes": notes
    }
    history = list(evc.reschedule_history or [])
    history.append(history_entry)
    evc.reschedule_history = history

    evc.planned_visit_date = new_planned_visit_date
    if notes:
        evc.scheduling_notes = (evc.scheduling_notes or "") + f"\n[Rescheduled: {reason}]"

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="RESCHEDULE_EVC_VISIT",
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        before_state={"planned_visit_date": previous_date_str},
        after_state={"planned_visit_date": new_planned_visit_date.isoformat(), "reason": reason},
        reason=reason
    )

    create_notification(
        db=db,
        recipient_role=UserRole.EVC_TEAM.value,
        notification_type=NotificationType.EVC_RESCHEDULED.value,
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        title="EVC Visit Rescheduled",
        message=f"EVC visit for application {evc.application_id} rescheduled to {new_planned_visit_date.strftime('%Y-%m-%d %H:%M')}. Reason: {reason}",
        deduplication_key=f"evc:rescheduled:{evc.id}:{new_planned_visit_date.strftime('%Y%m%d%H%M')}"
    )

    db.commit()
    db.refresh(evc)
    return evc


def complete_evc_visit(
    db: Session,
    evc_id: str,
    actual_visit_date: datetime,
    visit_notes: Optional[str] = None,
    actor_id: str = "EVC_LEAD",
    actor_role: str = UserRole.EVC_TEAM.value
) -> EVCRecord:
    evc = get_evc_by_id(db, evc_id)
    if evc.status != EVCStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete visit from status '{evc.status.value}'. Must be in '{EVCStatus.SCHEDULED.value}'."
        )

    before_state = {"status": evc.status.value}
    evc.status = EVCStatus.VISIT_COMPLETED
    evc.actual_visit_date = actual_visit_date
    evc.visit_notes = visit_notes

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="COMPLETE_EVC_VISIT",
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        before_state=before_state,
        after_state={"status": evc.status.value, "actual_visit_date": actual_visit_date.isoformat()},
        reason="Physical or virtual inspection completed by EVC team"
    )

    db.commit()
    db.refresh(evc)
    return evc


def submit_evc_report(
    db: Session,
    evc_id: str,
    findings_summary: str,
    recommendation: EVCRecommendation,
    report_document_id: Optional[str] = None,
    actor_id: str = "EVC_LEAD",
    actor_role: str = UserRole.EVC_TEAM.value
) -> EVCRecord:
    evc = get_evc_by_id(db, evc_id)
    # Permitted from VISIT_COMPLETED or if clarification was previously requested
    if evc.status != EVCStatus.VISIT_COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit EVC report from status '{evc.status.value}'. Must be in '{EVCStatus.VISIT_COMPLETED.value}'."
        )

    before_state = {"status": evc.status.value}
    evc.status = EVCStatus.REPORT_SUBMITTED
    evc.findings_summary = findings_summary
    evc.recommendation = recommendation
    evc.report_document_id = report_document_id
    evc.report_submitted_at = utc_now()
    evc.report_submitted_by = actor_id

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="SUBMIT_EVC_REPORT",
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        before_state=before_state,
        after_state={
            "status": evc.status.value,
            "recommendation": recommendation.value,
            "report_document_id": report_document_id
        },
        reason="EVC inspection report submitted with factual findings"
    )

    create_notification(
        db=db,
        recipient_role=UserRole.COMPLIANCE_OFFICER.value,
        notification_type=NotificationType.EVC_REPORT_SUBMITTED.value,
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        title="EVC Report Submitted for Review",
        message=f"EVC report for application {evc.application_id} has been submitted with recommendation '{recommendation.value}'.",
        deduplication_key=f"evc:report_submitted:{evc.id}"
    )

    db.commit()
    db.refresh(evc)
    return evc


def review_evc_report(
    db: Session,
    evc_id: str,
    outcome: EVCReportReviewOutcome,
    review_notes: Optional[str] = None,
    actor_id: str = "COMPLIANCE_OFFICER_1",
    actor_role: str = UserRole.COMPLIANCE_OFFICER.value
) -> EVCRecord:
    evc = get_evc_by_id(db, evc_id)
    if evc.status != EVCStatus.REPORT_SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review report from status '{evc.status.value}'. Must be in '{EVCStatus.REPORT_SUBMITTED.value}'."
        )

    # Permission check: must be reviewer role
    permitted_roles = [UserRole.COMPLIANCE_OFFICER.value, UserRole.ADMIN.value, UserRole.SCRUTINY_OFFICER.value]
    if actor_role not in permitted_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor_role}' is not authorized to review EVC reports."
        )

    before_state = {"status": evc.status.value}
    evc.status = EVCStatus.REPORT_REVIEWED
    evc.report_reviewed_at = utc_now()
    evc.report_reviewed_by = actor_id
    evc.report_review_outcome = outcome
    evc.report_review_notes = review_notes

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="REVIEW_EVC_REPORT",
        entity_type=EntityType.EVC.value,
        entity_id=evc.id,
        before_state=before_state,
        after_state={"status": evc.status.value, "outcome": outcome.value},
        reason=review_notes or f"EVC report reviewed with outcome {outcome.value}"
    )

    db.commit()
    db.refresh(evc)
    return evc
