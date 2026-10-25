from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.enums import NotificationType


class NotificationCreateRequest(BaseModel):
    recipient_role: str
    recipient_id: Optional[str] = None
    notification_type: NotificationType
    entity_type: str
    entity_id: str
    title: str
    message: str
    deduplication_key: str
    source_event: Optional[str] = None


class NotificationResponse(BaseModel):
    id: str
    recipient_role: str
    recipient_id: Optional[str] = None
    notification_type: NotificationType
    entity_type: str
    entity_id: str
    title: str
    message: str
    is_read: bool
    read_at: Optional[datetime] = None
    deduplication_key: str
    source_event: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
