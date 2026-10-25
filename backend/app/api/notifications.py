from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas.notification import NotificationResponse
from backend.app.services.notifications import list_notifications, mark_notification_as_read

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    recipient_role: Optional[str] = Query(None, description="Filter by recipient role"),
    recipient_id: Optional[str] = Query(None, description="Filter by recipient user/institution ID"),
    is_read: Optional[bool] = Query(None, description="Filter by read/unread status"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists in-app notifications with filtering options."""
    return list_notifications(
        db=db,
        recipient_role=recipient_role,
        recipient_id=recipient_id,
        is_read=is_read,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=limit
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """Marks a notification as read."""
    return mark_notification_as_read(db=db, notification_id=notification_id)
