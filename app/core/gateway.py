import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("aicte.gateway")

# Native Member 4 compliance module imports (isolated namespace backend.app)
from backend.app.db import (
    Base as ComplianceBase,
    engine as compliance_engine,
    get_db as get_compliance_db,
    SessionLocal as ComplianceSessionLocal,
    init_db as init_compliance_db,
)
from backend.app.api import gateway_compliance_router as compliance_api_router
from backend.app.services.audit import record_audit_event
from backend.app.services.notifications import create_notification
from backend.app.enums import NotificationType, EntityType

# Import Member 3 listener registration mechanisms
from app.core.workflow_engine import (
    register_audit_listener,
    register_notification_listener,
    clear_service_listeners,
)

# Bridge tracking state for monitoring write status and errors
_last_bridge_error: Optional[str] = None
_bridge_audit_count: int = 0
_bridge_notification_count: int = 0
_compliance_session_factory = ComplianceSessionLocal


def set_compliance_session_factory(factory) -> None:
    global _compliance_session_factory
    _compliance_session_factory = factory


def get_bridge_db_session():
    return _compliance_session_factory()


def get_last_bridge_error() -> Optional[str]:
    return _last_bridge_error


def reset_bridge_counters() -> None:
    global _last_bridge_error, _bridge_audit_count, _bridge_notification_count
    _last_bridge_error = None
    _bridge_audit_count = 0
    _bridge_notification_count = 0


def workflow_audit_bridge_sink(payload: Dict[str, Any]) -> None:
    """
    Receives structured audit events emitted by Member 3 workflow engine
    and persists them into Member 4's AuditEvent table via ComplianceSessionLocal.
    """
    global _last_bridge_error, _bridge_audit_count
    db = get_bridge_db_session()
    try:
        record_audit_event(
            db=db,
            actor_id=str(payload.get("actor_id", "SYSTEM")),
            actor_role=str(payload.get("actor_role", "SYSTEM")),
            action=str(payload.get("event_type", "WORKFLOW_ACTION")),
            entity_type=EntityType.APPLICATION.value,
            entity_id=str(payload.get("target_id", "UNKNOWN")),
            details=payload.get("details", {}),
            reason=payload.get("details", {}).get("remarks") if isinstance(payload.get("details"), dict) else None,
        )
        db.commit()
        _bridge_audit_count += 1
        logger.info(f"[GATEWAY_AUDIT_BRIDGE] Successfully recorded audit event: {payload.get('event_type')}")
    except Exception as e:
        db.rollback()
        _last_bridge_error = f"Audit bridge persistence failed: {str(e)}"
        logger.error(f"[GATEWAY_AUDIT_BRIDGE_ERROR] {_last_bridge_error}")
        raise RuntimeError(_last_bridge_error) from e
    finally:
        db.close()


def workflow_notification_bridge_sink(payload: Dict[str, Any]) -> None:
    """
    Receives notification alerts emitted by Member 3 workflow engine
    and persists them into Member 4's Notification table with deterministic deduplication.
    """
    global _last_bridge_error, _bridge_notification_count
    db = get_bridge_db_session()
    try:
        event_type = payload.get("event_type", "GENERAL")
        app_id = payload.get("application_id", "UNKNOWN")
        recipient_role = payload.get("recipient_role", "APPLICANT")
        message = payload.get("message", "")

        # Map to valid NotificationType
        if event_type == "DEFICIENCY_RAISED":
            notif_type = NotificationType.OBLIGATION_ACTION_REQUIRED
        else:
            notif_type = NotificationType.GENERAL

        # Construct deterministic deduplication key
        # Incorporates event_type and app_id to prevent redundant alerts for the same event
        dedup_key = f"wf:{event_type}:{app_id}:{recipient_role}"

        create_notification(
            db=db,
            recipient_role=recipient_role,
            notification_type=notif_type,
            entity_type=EntityType.APPLICATION.value,
            entity_id=str(app_id),
            title=f"Workflow Update: {event_type}",
            message=message,
            deduplication_key=dedup_key,
            source_event=event_type,
        )
        db.commit()
        _bridge_notification_count += 1
        logger.info(f"[GATEWAY_NOTIFICATION_BRIDGE] Successfully recorded notification: {event_type}")
    except Exception as e:
        db.rollback()
        _last_bridge_error = f"Notification bridge persistence failed: {str(e)}"
        logger.error(f"[GATEWAY_NOTIFICATION_BRIDGE_ERROR] {_last_bridge_error}")
        raise RuntimeError(_last_bridge_error) from e
    finally:
        db.close()


def register_compliance_bridges() -> None:
    """Registers audit and notification bridge callbacks into Member 3 engine."""
    register_audit_listener(workflow_audit_bridge_sink)
    register_notification_listener(workflow_notification_bridge_sink)
    logger.info("[GATEWAY] Compliance event bridges registered successfully.")


def unregister_compliance_bridges() -> None:
    """Clears listeners (useful for test isolation)."""
    clear_service_listeners()
    logger.info("[GATEWAY] Compliance event bridges unregistered.")
