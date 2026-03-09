"""Audit logging service — security-relevant event capture."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import AuditEvent

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    event_type: str,
    user_id: Optional[UUID] = None,
    agency_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        user_id=user_id,
        agency_id=agency_id,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info("Audit: %s user=%s agency=%s resource=%s/%s",
                event_type, user_id, agency_id, resource_type, resource_id)
    return event
