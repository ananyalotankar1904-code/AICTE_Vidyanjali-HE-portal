from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.notification import Notification
from app.enums import NotificationType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_notification(
    db: Session,
    recipient_role: str,
    notification_type: str,
    entity_type: str,
    entity_id: str,
    title: str,
    message: str,
    deduplication_key: str,
    recipient_id: Optional[str] = None,
    source_event: Optional[str] = None
) -> Notification:
    """
    Creates an in-app notification if one with the same deduplication_key does not already exist.
    Prevents duplicate alerts for the same event/window.
    """
    existing = db.query(Notification).filter(Notification.deduplication_key == deduplication_key).first()
    if existing:
        return existing

    # Handle string or Enum type
    if isinstance(notification_type, str):
        notification_type_enum = NotificationType(notification_type)
    else:
        notification_type_enum = notification_type

    notification = Notification(
        recipient_role=recipient_role,
        recipient_id=recipient_id,
        notification_type=notification_type_enum,
        entity_type=entity_type,
        entity_id=str(entity_id),
        title=title,
        message=message,
        deduplication_key=deduplication_key,
        source_event=source_event,
        is_read=False
    )
    db.add(notification)
    db.flush()
    return notification


def list_notifications(
    db: Session,
    recipient_role: Optional[str] = None,
    recipient_id: Optional[str] = None,
    is_read: Optional[bool] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Notification]:
    query = db.query(Notification)
    if recipient_role:
        query = query.filter(Notification.recipient_role == recipient_role)
    if recipient_id:
        query = query.filter(Notification.recipient_id == recipient_id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if entity_type:
        query = query.filter(Notification.entity_type == entity_type)
    if entity_id:
        query = query.filter(Notification.entity_id == entity_id)
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_notification_as_read(db: Session, notification_id: str) -> Notification:
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id '{notification_id}' not found."
        )
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = utc_now()
        db.commit()
        db.refresh(notif)
    return notif


def count_unread_notifications(
    db: Session,
    recipient_role: Optional[str] = None,
    recipient_id: Optional[str] = None
) -> int:
    query = db.query(Notification).filter(Notification.is_read.is_(False))
    if recipient_role:
        query = query.filter(Notification.recipient_role == recipient_role)
    if recipient_id:
        query = query.filter(Notification.recipient_id == recipient_id)
    return query.count()
