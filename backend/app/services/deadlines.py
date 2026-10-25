from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.deadline import DeadlineRecord
from app.schemas.deadline import DeadlineEvaluationSummary
from app.enums import DeadlineStatus, NotificationType, EntityType, UserRole
from app.services.audit import record_audit_event
from app.services.notifications import create_notification
from app.utils.datetime_utils import utc_now, ensure_naive_utc


def get_deadline_by_id(db: Session, deadline_id: str) -> DeadlineRecord:
    deadline = db.query(DeadlineRecord).filter(DeadlineRecord.id == deadline_id).first()
    if not deadline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deadline with id '{deadline_id}' not found."
        )
    return deadline


def list_deadlines(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_role: Optional[str] = None,
    status_filter: Optional[DeadlineStatus] = None,
    skip: int = 0,
    limit: int = 50
) -> List[DeadlineRecord]:
    query = db.query(DeadlineRecord)
    if entity_type:
        query = query.filter(DeadlineRecord.entity_type == entity_type)
    if entity_id:
        query = query.filter(DeadlineRecord.entity_id == entity_id)
    if owner_role:
        query = query.filter(DeadlineRecord.owner_role == owner_role)
    if status_filter:
        query = query.filter(DeadlineRecord.status == status_filter)
    return query.order_by(DeadlineRecord.due_date.asc()).offset(skip).limit(limit).all()


def create_deadline_record(
    db: Session,
    entity_type: str,
    entity_id: str,
    deadline_type: str,
    title: str,
    due_date: datetime,
    owner_role: str,
    owner_id: Optional[str] = None,
    source_reference: str = "Illustrative Demo Policy",
    is_statutory: bool = False,
    warning_threshold_hours: int = 48,
    escalation_policy: str = "NOTIFY_REGIONAL_OFFICER_ON_OVERDUE",
    actor_id: str = "SYSTEM",
    actor_role: str = UserRole.ADMIN.value
) -> DeadlineRecord:
    normalized_due_date = ensure_naive_utc(due_date)

    deadline = DeadlineRecord(
        entity_type=entity_type,
        entity_id=entity_id,
        deadline_type=deadline_type,
        title=title,
        due_date=normalized_due_date,
        owner_role=owner_role,
        owner_id=owner_id,
        source_reference=source_reference,
        is_statutory=is_statutory,
        status=DeadlineStatus.ACTIVE,
        warning_threshold_hours=warning_threshold_hours,
        escalation_policy=escalation_policy,
        escalation_triggered=False,
        escalation_history=[]
    )
    db.add(deadline)
    db.flush()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="CREATE_DEADLINE",
        entity_type=EntityType.DEADLINE.value,
        entity_id=deadline.id,
        after_state={"title": title, "due_date": normalized_due_date.isoformat(), "owner_role": owner_role},
        reason=f"Registered {('statutory' if is_statutory else 'operational')} deadline: {title}"
    )

    db.commit()
    db.refresh(deadline)
    return deadline


def complete_deadline(
    db: Session,
    deadline_id: str,
    actor_id: str = "SYSTEM",
    actor_role: str = UserRole.SYSTEM.value
) -> DeadlineRecord:
    """Marks a deadline as completed so it will never generate future warnings or escalations."""
    deadline = get_deadline_by_id(db, deadline_id)
    if deadline.status in (DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED):
        return deadline

    before_state = {"status": deadline.status.value}
    deadline.status = DeadlineStatus.COMPLETED
    deadline.completed_at = utc_now()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="COMPLETE_DEADLINE",
        entity_type=EntityType.DEADLINE.value,
        entity_id=deadline.id,
        before_state=before_state,
        after_state={"status": deadline.status.value},
        reason="Underlying task fulfilled; deadline stopped"
    )

    db.commit()
    db.refresh(deadline)
    return deadline


def cancel_deadline(
    db: Session,
    deadline_id: str,
    reason: Optional[str] = None,
    actor_id: str = "SYSTEM",
    actor_role: str = UserRole.SYSTEM.value
) -> DeadlineRecord:
    """Cancels an obsolete or superseded deadline."""
    deadline = get_deadline_by_id(db, deadline_id)
    if deadline.status in (DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED):
        return deadline

    before_state = {"status": deadline.status.value}
    deadline.status = DeadlineStatus.CANCELLED
    deadline.cancelled_at = utc_now()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="CANCEL_DEADLINE",
        entity_type=EntityType.DEADLINE.value,
        entity_id=deadline.id,
        before_state=before_state,
        after_state={"status": deadline.status.value},
        reason=reason or "Deadline cancelled/superseded"
    )

    db.commit()
    db.refresh(deadline)
    return deadline


def evaluate_deadlines(
    db: Session,
    reference_time: Optional[datetime] = None
) -> DeadlineEvaluationSummary:
    """
    Deterministic deadline evaluation engine.
    Uses reference_time (defaults to utc_now) so tests can control time.
    Evaluates upcoming warnings and overdue escalations.
    Guarantees idempotency via deduplication keys.
    Never alters statutory approval/rejection decisions.
    """
    ref = ensure_naive_utc(reference_time) or utc_now()

    # Query only active or overdue deadlines (skips completed and cancelled!)
    evaluable = db.query(DeadlineRecord).filter(
        DeadlineRecord.status.in_([DeadlineStatus.ACTIVE, DeadlineStatus.OVERDUE])
    ).all()

    upcoming_count = 0
    escalation_count = 0
    marked_overdue_count = 0

    for dl in evaluable:
        dl.last_evaluated_at = ref
        due = ensure_naive_utc(dl.due_date)

        # 1. Check if OVERDUE
        if due < ref:
            if dl.status != DeadlineStatus.OVERDUE:
                dl.status = DeadlineStatus.OVERDUE
                marked_overdue_count += 1

            if not dl.escalation_triggered:
                dl.escalation_triggered = True
                escalation_entry = {
                    "timestamp": ref.isoformat(),
                    "event_type": "OVERDUE_ESCALATION",
                    "escalated_to_role": UserRole.REGIONAL_OFFICER.value,
                    "reason": f"Deadline '{dl.title}' for {dl.entity_type} {dl.entity_id} expired at {due.isoformat()}"
                }
                history = list(dl.escalation_history or [])
                history.append(escalation_entry)
                dl.escalation_history = history

                # Notify regional officer and owner
                create_notification(
                    db=db,
                    recipient_role=UserRole.REGIONAL_OFFICER.value,
                    notification_type=NotificationType.ESCALATION_ALERT.value,
                    entity_type=dl.entity_type,
                    entity_id=dl.entity_id,
                    title=f"ESCALATION: Overdue Deadline - {dl.title}",
                    message=f"Deadline '{dl.title}' is overdue. Assigned role: {dl.owner_role}. Immediate supervisor review required.",
                    deduplication_key=f"deadline:escalation:{dl.id}",
                    source_event="DEADLINE_EVALUATION"
                )

                record_audit_event(
                    db=db,
                    actor_id="DEADLINE_SERVICE",
                    actor_role=UserRole.SYSTEM.value,
                    action="ESCALATE_OVERDUE_DEADLINE",
                    entity_type=EntityType.DEADLINE.value,
                    entity_id=dl.id,
                    after_state={"status": dl.status.value, "escalation_triggered": True},
                    reason=f"Deadline exceeded due date {due.isoformat()}"
                )
                escalation_count += 1

        # 2. Check if UPCOMING WARNING
        elif ref <= due <= (ref + timedelta(hours=dl.warning_threshold_hours)):
            create_notification(
                db=db,
                recipient_role=dl.owner_role,
                recipient_id=dl.owner_id,
                notification_type=NotificationType.DEADLINE_UPCOMING.value,
                entity_type=dl.entity_type,
                entity_id=dl.entity_id,
                title=f"Upcoming Deadline Warning: {dl.title}",
                message=f"Reminder: Deadline '{dl.title}' is due at {due.strftime('%Y-%m-%d %H:%M')}.",
                deduplication_key=f"deadline:upcoming:{dl.id}",
                source_event="DEADLINE_EVALUATION"
            )
            upcoming_count += 1

    db.commit()

    return DeadlineEvaluationSummary(
        evaluated_at=utc_now(),
        reference_time=ref,
        total_active_evaluated=len(evaluable),
        upcoming_warnings_issued=upcoming_count,
        overdue_escalations_issued=escalation_count,
        deadlines_marked_overdue=marked_overdue_count
    )
