from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.enums import EVCStatus, UserRole
from backend.app.schemas.evc import (
    EVCCreateRequest,
    EVCScheduleRequest,
    EVCRescheduleRequest,
    EVCCompleteVisitRequest,
    EVCSubmitReportRequest,
    EVCReviewReportRequest,
    EVCUpdateRequest,
    EVCResponse,
)
from backend.app.services.evc import (
    create_evc_record,
    get_evc_by_id,
    list_evcs,
    schedule_evc_visit,
    reschedule_evc_visit,
    complete_evc_visit,
    submit_evc_report,
    review_evc_report,
)

router = APIRouter(prefix="/evcs", tags=["Expert Visit Committee (EVC)"])


@router.get("", response_model=List[EVCResponse])
def get_evc_records(
    application_id: Optional[str] = Query(None, description="Filter by application UUID"),
    status: Optional[EVCStatus] = Query(None, description="Filter by EVC status"),
    assigned_team_id: Optional[str] = Query(None, description="Filter by assigned team ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists EVC inspection records with optional status, team, and application filters."""
    return list_evcs(
        db=db,
        application_id=application_id,
        status_filter=status,
        assigned_team_id=assigned_team_id,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=EVCResponse, status_code=status.HTTP_201_CREATED)
def create_evc(
    payload: EVCCreateRequest,
    x_user_id: Optional[str] = Header("OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.SCRUTINY_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Creates a new EVC record linked to an application in PENDING_SCHEDULING status."""
    return create_evc_record(
        db=db,
        application_id=payload.application_id,
        assigned_team_id=payload.assigned_team_id,
        assigned_members=payload.assigned_members,
        venue_address=payload.venue_address,
        scheduling_notes=payload.scheduling_notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.get("/{evc_id}", response_model=EVCResponse)
def get_evc_detail(
    evc_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves detailed EVC information, including reschedule history and report status."""
    return get_evc_by_id(db, evc_id)


@router.patch("/{evc_id}", response_model=EVCResponse)
def update_evc_metadata(
    evc_id: str,
    payload: EVCUpdateRequest,
    db: Session = Depends(get_db)
):
    """Updates team assignment or venue information before visit completion."""
    evc = get_evc_by_id(db, evc_id)
    if payload.assigned_team_id is not None:
        evc.assigned_team_id = payload.assigned_team_id
    if payload.assigned_members is not None:
        evc.assigned_members = payload.assigned_members
    if payload.venue_address is not None:
        evc.venue_address = payload.venue_address
    if payload.scheduling_notes is not None:
        evc.scheduling_notes = payload.scheduling_notes
    db.commit()
    db.refresh(evc)
    return evc


@router.post("/{evc_id}/schedule", response_model=EVCResponse)
def schedule_visit(
    evc_id: str,
    payload: EVCScheduleRequest,
    x_user_id: Optional[str] = Header("OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.SCRUTINY_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Schedules an initial planned visit date and time."""
    return schedule_evc_visit(
        db=db,
        evc_id=evc_id,
        planned_visit_date=payload.planned_visit_date,
        venue_address=payload.venue_address,
        assigned_team_id=payload.assigned_team_id,
        assigned_members=payload.assigned_members,
        notes=payload.notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{evc_id}/reschedule", response_model=EVCResponse)
def reschedule_visit(
    evc_id: str,
    payload: EVCRescheduleRequest,
    x_user_id: Optional[str] = Header("OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.SCRUTINY_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Reschedules an EVC visit while preserving the full rescheduling history."""
    return reschedule_evc_visit(
        db=db,
        evc_id=evc_id,
        new_planned_visit_date=payload.new_planned_visit_date,
        reason=payload.reason,
        notes=payload.notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{evc_id}/complete-visit", response_model=EVCResponse)
def complete_visit(
    evc_id: str,
    payload: EVCCompleteVisitRequest,
    x_user_id: Optional[str] = Header("EVC_LEAD_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.EVC_TEAM.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Records that the on-site or virtual visit has concluded."""
    return complete_evc_visit(
        db=db,
        evc_id=evc_id,
        actual_visit_date=payload.actual_visit_date,
        visit_notes=payload.visit_notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{evc_id}/submit-report", response_model=EVCResponse)
def submit_report(
    evc_id: str,
    payload: EVCSubmitReportRequest,
    x_user_id: Optional[str] = Header("EVC_LEAD_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.EVC_TEAM.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Submits the EVC report with factual findings and recommendations."""
    return submit_evc_report(
        db=db,
        evc_id=evc_id,
        findings_summary=payload.findings_summary,
        recommendation=payload.recommendation,
        report_document_id=payload.report_document_id,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{evc_id}/review-report", response_model=EVCResponse)
def review_report(
    evc_id: str,
    payload: EVCReviewReportRequest,
    x_user_id: Optional[str] = Header("COMPLIANCE_OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.COMPLIANCE_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Authorized officer reviews the EVC report (Accepts or Requests Clarification)."""
    return review_evc_report(
        db=db,
        evc_id=evc_id,
        outcome=payload.outcome,
        review_notes=payload.review_notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )
