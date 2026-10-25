from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import (
    Application,
    WorkflowHistory,
    ScrutinyRecord,
    DeficiencyRecord,
    DecisionRecord,
)
from app.schemas.workflow import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationDetailResponse,
    ApplicationListResponse,
    DashboardSummaryRow,
    DashboardSummaryResponse,
    TransitionRequest,
    ScrutinySubmitRequest,
    DeficiencyResponseRequest,
    DecisionSubmitRequest,
    WorkflowHistoryItem,
    ScrutinyRecordItem,
    DeficiencyRecordItem,
    DecisionRecordItem,
)
from app.core.auth import get_current_user, require_roles, UserIdentity
from app.core.workflow_engine import (
    execute_workflow_transition,
    emit_audit_event,
    emit_notification_hook,
)

router = APIRouter()


def generate_next_application_id(db: Session) -> str:
    """Generates the next sequential ID in the format APP001, APP002, etc."""
    apps = db.query(Application.application_id).all()
    max_num = 0
    for (aid,) in apps:
        if aid.startswith("APP") and aid[3:].isdigit():
            num = int(aid[3:])
            if num > max_num:
                max_num = num
    return f"APP{max_num + 1:03d}"


# 1. Application Registration
@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new application"
)
def register_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_roles("Institution Admin", "Intake Officer", "Admin"))
):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    app_id = generate_next_application_id(db)

    # Determine initial due date (default: 14 days from submission if not supplied)
    due_date = payload.due_date or today_str

    new_app = Application(
        application_id=app_id,
        institution_id=payload.institution_id,
        application_type=payload.application_type,
        current_stage="SUBMITTED",
        application_status="IN_PROGRESS",
        submitted_date=today_str,
        stage_entered_date=today_str,
        due_date=due_date,
        assigned_role="Intake Officer",
        deficiency_flag="No",
        last_updated=today_str,
        data_type="SYNTHETIC_DEMO",
        deadline_condition="ON_TRACK",
        reference_date="2026-10-25",
        demo_notes="Registered via API prototype.",
        academic_year=payload.academic_year,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        programme_name=payload.programme_name,
        intake_approved=payload.intake_approved,
    )

    db.add(new_app)

    # Initial history log entry
    initial_history = WorkflowHistory(
        application_id=app_id,
        from_stage="NONE",
        to_stage="SUBMITTED",
        from_status="NONE",
        to_status="IN_PROGRESS",
        action="REGISTER",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        timestamp=datetime.now(timezone.utc),
        remarks=f"Application registered by {current_user.role}",
    )
    db.add(initial_history)
    db.commit()
    db.refresh(new_app)

    emit_audit_event(
        event_type="APPLICATION_REGISTERED",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        target_id=app_id,
        details={"institution_id": payload.institution_id, "type": payload.application_type}
    )

    emit_notification_hook(
        event_type="APPLICATION_SUBMITTED",
        application_id=app_id,
        recipient_role="Intake Officer",
        message=f"New application {app_id} submitted by {payload.institution_id}."
    )

    return new_app


# 2. Application Listing with Filtering
@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List applications with filtering"
)
def list_applications(
    stage: Optional[str] = Query(None, description="Filter by current_stage"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by application_status"),
    institution_id: Optional[str] = Query(None, description="Filter by institution_id"),
    assigned_role: Optional[str] = Query(None, description="Filter by assigned_role"),
    deadline_condition: Optional[str] = Query(None, description="Filter by deadline_condition"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    query = db.query(Application)

    if stage:
        query = query.filter(Application.current_stage == stage)
    if status_filter:
        query = query.filter(Application.application_status == status_filter)
    if institution_id:
        query = query.filter(Application.institution_id == institution_id)
    if assigned_role:
        query = query.filter(Application.assigned_role == assigned_role)
    if deadline_condition:
        query = query.filter(Application.deadline_condition == deadline_condition)

    total = query.count()
    items = query.order_by(Application.application_id.asc()).offset(offset).limit(limit).all()

    return ApplicationListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


# 2.5 Dashboard Summary Aggregations (Dataset 2 Sheet 3 Contract)
@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    summary="Get aggregated application statistics for dashboard"
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    total = db.query(func.count(Application.application_id)).scalar() or 0
    action_required = db.query(func.count(Application.application_id)).filter(Application.application_status == "ACTION_REQUIRED").scalar() or 0
    overdue = db.query(func.count(Application.application_id)).filter(Application.deadline_condition == "OVERDUE").scalar() or 0

    stage_counts = db.query(Application.current_stage, func.count(Application.application_id)).group_by(Application.current_stage).all()
    by_stage = {stage: count for stage, count in stage_counts}

    status_counts = db.query(Application.application_status, func.count(Application.application_id)).group_by(Application.application_status).all()
    by_status = {st: count for st, count in status_counts}

    deadline_counts = db.query(Application.deadline_condition, func.count(Application.application_id)).group_by(Application.deadline_condition).all()
    by_deadline_condition = {dc: count for dc, count in deadline_counts}

    # Grouped matrix by (current_stage, application_status, deadline_condition) matching Sheet 3
    matrix_counts = db.query(
        Application.current_stage,
        Application.application_status,
        Application.deadline_condition,
        func.count(Application.application_id)
    ).group_by(
        Application.current_stage,
        Application.application_status,
        Application.deadline_condition
    ).order_by(
        Application.current_stage.asc(),
        Application.application_status.asc(),
        Application.deadline_condition.asc()
    ).all()

    summary_matrix = [
        DashboardSummaryRow(
            current_stage=stage,
            application_status=st,
            deadline_condition=dc,
            record_count=count
        )
        for stage, st, dc, count in matrix_counts
    ]

    return DashboardSummaryResponse(
        total_applications=total,
        action_required_count=action_required,
        overdue_count=overdue,
        by_stage=by_stage,
        by_status=by_status,
        by_deadline_condition=by_deadline_condition,
        summary_matrix=summary_matrix
    )


# 3. Retrieve Single Application by ID
@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Retrieve application by ID"
)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.application_id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found."
        )
    return app


# 4. Permitted Application Updates
@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Update permitted application fields"
)
def update_application_details(
    application_id: str,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_roles("Institution Admin", "Admin"))
):
    app = db.query(Application).filter(Application.application_id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found."
        )

    # Protected stage check: updates only allowed during early editable stages
    permitted_update_stages = ["SUBMITTED", "DEFICIENCY_RAISED"]
    if app.current_stage not in permitted_update_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Direct application updates are not permitted while in stage '{app.current_stage}'. "
                f"Updates are only permitted in stages: {permitted_update_stages}."
            )
        )

    # Apply only permitted fields (protected workflow fields are untouched)
    updated_fields = []
    if payload.contact_email is not None:
        app.contact_email = payload.contact_email
        updated_fields.append("contact_email")
    if payload.contact_phone is not None:
        app.contact_phone = payload.contact_phone
        updated_fields.append("contact_phone")
    if payload.programme_name is not None:
        app.programme_name = payload.programme_name
        updated_fields.append("programme_name")
    if payload.intake_approved is not None:
        app.intake_approved = payload.intake_approved
        updated_fields.append("intake_approved")
    if payload.academic_year is not None:
        app.academic_year = payload.academic_year
        updated_fields.append("academic_year")

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    app.last_updated = today_str

    history_entry = WorkflowHistory(
        application_id=app.application_id,
        from_stage=app.current_stage,
        to_stage=app.current_stage,
        from_status=app.application_status,
        to_status=app.application_status,
        action="DETAILS_UPDATED",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        timestamp=datetime.now(timezone.utc),
        remarks=f"Updated fields: {', '.join(updated_fields)}" if updated_fields else "No fields changed.",
    )
    db.add(history_entry)
    db.commit()
    db.refresh(app)

    emit_audit_event(
        event_type="APPLICATION_UPDATED",
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        target_id=app.application_id,
        details={"updated_fields": updated_fields}
    )

    return app


# 5. Workflow History Retrieval
@router.get(
    "/{application_id}/history",
    response_model=List[WorkflowHistoryItem],
    summary="Retrieve workflow transition history"
)
def get_application_history(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.application_id == application_id).first()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{application_id}' not found."
        )

    history = (
        db.query(WorkflowHistory)
        .filter(WorkflowHistory.application_id == application_id)
        .order_by(WorkflowHistory.id.asc())
        .all()
    )
    return history


# 6. Configurable Workflow Transition
@router.post(
    "/{application_id}/transition",
    response_model=ApplicationResponse,
    summary="Trigger a permitted workflow transition"
)
def transition_application(
    application_id: str,
    payload: TransitionRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    app = service.execute_transition(
        application_id=application_id,
        action=payload.action,
        to_stage=payload.to_stage,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        remarks=payload.remarks,
    )
    return app


# 7. Scrutiny Outcomes (Initial Scrutiny and Re-Scrutiny)
@router.post(
    "/{application_id}/scrutiny",
    response_model=ApplicationResponse,
    summary="Record scrutiny outcome (Passed / Deficient)"
)
def submit_scrutiny(
    application_id: str,
    payload: ScrutinySubmitRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_roles("Scrutiny Officer", "Admin"))
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    return service.record_scrutiny(
        application_id=application_id,
        scrutiny_type=payload.scrutiny_type,
        outcome=payload.outcome,
        remarks=payload.remarks,
        deficiencies=payload.deficiencies,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
    )


@router.get(
    "/{application_id}/scrutiny",
    response_model=List[ScrutinyRecordItem],
    summary="Retrieve all scrutiny evaluations (preserving history)"
)
def get_application_scrutiny(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    return service.get_scrutiny_records(application_id)


# 8. Deficiency Resubmission (Institution Admin)
@router.post(
    "/{application_id}/deficiency/respond",
    response_model=ApplicationResponse,
    summary="Submit institution response to deficiencies"
)
def respond_to_deficiencies(
    application_id: str,
    payload: DeficiencyResponseRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_roles("Institution Admin", "Admin"))
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    return service.record_deficiency_responses(
        application_id=application_id,
        responses=payload.responses,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        remarks=payload.remarks,
    )


@router.get(
    "/{application_id}/deficiencies",
    response_model=List[DeficiencyRecordItem],
    summary="Retrieve deficiency records for application"
)
def get_application_deficiencies(
    application_id: str,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (OPEN, RESPONDED, RESOLVED)"),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    return service.get_deficiency_records(application_id, status_filter=status_filter)


# 9. Authorized Decision Recording (Competent Authority)
@router.post(
    "/{application_id}/decision",
    response_model=ApplicationResponse,
    summary="Record authorized official decision"
)
def record_official_decision(
    application_id: str,
    payload: DecisionSubmitRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_roles("Competent Authority Secretariat", "Admin"))
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    return service.record_official_decision(
        application_id=application_id,
        decision=payload.decision,
        reasons=payload.reasons,
        conditions=payload.conditions,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
    )


@router.get(
    "/{application_id}/decision",
    response_model=DecisionRecordItem,
    summary="Retrieve recorded official decision"
)
def get_application_decision(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user)
):
    from app.core.workflow_engine import WorkflowService
    service = WorkflowService(db)
    return service.get_decision_record(application_id)
