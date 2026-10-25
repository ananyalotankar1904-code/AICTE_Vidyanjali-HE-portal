import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, Boolean
from app.db import Base
from app.enums import NotificationType


def utc_now():
    return datetime.now(timezone.utc)


class Notification(Base):
    """In-app persistent notification with deduplication support."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_role = Column(String(50), nullable=False, index=True)
    recipient_id = Column(String(100), nullable=True, index=True)
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Deduplication key prevents duplicate notifications for the same event/window
    deduplication_key = Column(String(255), unique=True, nullable=False, index=True)
    source_event = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
