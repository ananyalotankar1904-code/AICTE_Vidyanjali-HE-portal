from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import DeadlineStatus, UserRole
from app.schemas.deadline import (
    DeadlineCreateRequest,
    DeadlineEvaluateRequest,
    DeadlineEvaluationSummary,
    DeadlineResponse,
)
from app.services.deadlines import (
    create_deadline_record,
    get_deadline_by_id,
    list_deadlines,
    complete_deadline,
    cancel_deadline,
    evaluate_deadlines,
)

router = APIRouter(prefix="/deadlines", tags=["Deadlines & Escalation Monitoring"])


@router.get("", response_model=List[DeadlineResponse])
def get_deadlines(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (APPLICATION, EVC, UNDERTAKING, DOCUMENT)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity UUID"),
    owner_role: Optional[str] = Query(None, description="Filter by responsible role"),
    status: Optional[DeadlineStatus] = Query(None, description="Filter by deadline status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists tracked deadlines with status and owner filters."""
    return list_deadlines(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        owner_role=owner_role,
        status_filter=status,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=DeadlineResponse, status_code=status.HTTP_201_CREATED)
def create_deadline(
    payload: DeadlineCreateRequest,
    x_user_id: Optional[str] = Header("OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.ADMIN.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Registers a new deadline for compliance or workflow monitoring."""
    return create_deadline_record(
        db=db,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        deadline_type=payload.deadline_type,
        title=payload.title,
        due_date=payload.due_date,
        owner_role=payload.owner_role,
        owner_id=payload.owner_id,
        source_reference=payload.source_reference or "Illustrative Demo Policy",
        is_statutory=payload.is_statutory,
        warning_threshold_hours=payload.warning_threshold_hours,
        escalation_policy=payload.escalation_policy or "NOTIFY_REGIONAL_OFFICER_ON_OVERDUE",
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.get("/overdue", response_model=List[DeadlineResponse])
def get_overdue_deadlines(
    db: Session = Depends(get_db)
):
    """Convenience endpoint returning all currently overdue deadlines."""
    return list_deadlines(db=db, status_filter=DeadlineStatus.OVERDUE)


@router.get("/{deadline_id}", response_model=DeadlineResponse)
def get_deadline_detail(
    deadline_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full details of a deadline, including escalation history."""
    return get_deadline_by_id(db, deadline_id)


@router.post("/evaluate", response_model=DeadlineEvaluationSummary)
def trigger_deadline_evaluation(
    payload: Optional[DeadlineEvaluateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Triggers deterministic evaluation of active deadlines.
    Can supply an optional reference_time for testable time simulation.
    Generates deduplicated upcoming warnings and overdue escalations.
    """
    ref_time = payload.reference_time if payload else None
    return evaluate_deadlines(db=db, reference_time=ref_time)


@router.post("/{deadline_id}/complete", response_model=DeadlineResponse)
def mark_deadline_completed(
    deadline_id: str,
    x_user_id: Optional[str] = Header("SYSTEM", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.SYSTEM.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Marks a deadline as completed so it will never generate future warnings or escalations."""
    return complete_deadline(db=db, deadline_id=deadline_id, actor_id=x_user_id, actor_role=x_user_role)


@router.post("/{deadline_id}/cancel", response_model=DeadlineResponse)
def mark_deadline_cancelled(
    deadline_id: str,
    reason: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header("SYSTEM", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.SYSTEM.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Cancels a deadline that has become obsolete or superseded."""
    return cancel_deadline(db=db, deadline_id=deadline_id, reason=reason, actor_id=x_user_id, actor_role=x_user_role)
