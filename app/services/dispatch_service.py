"""Dispatch Service — CRUD for dispatch records."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import DispatchRecord

logger = logging.getLogger(__name__)


def create_dispatch(
    db: Session,
    recipient_type: str,
    channel: str,
    body: str,
    subject: Optional[str] = None,
    triage_request_id: Optional[UUID] = None,
    account_id: Optional[UUID] = None,
    agency_id: Optional[UUID] = None,
    dispatched_by_user_id: Optional[UUID] = None,
    status: str = "logged",
) -> DispatchRecord:
    """Create a dispatch record."""
    record = DispatchRecord(
        triage_request_id=triage_request_id,
        account_id=account_id,
        agency_id=agency_id,
        recipient_type=recipient_type,
        channel=channel,
        subject=subject,
        body=body,
        dispatched_by_user_id=dispatched_by_user_id,
        status=status,
    )
    db.add(record)
    db.flush()
    logger.info("Dispatch record created: %s -> %s (%s)", record.id, recipient_type, channel)
    return record


def list_dispatches(
    db: Session,
    account_id: Optional[UUID] = None,
    agency_id: Optional[UUID] = None,
    triage_request_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DispatchRecord], int]:
    """List dispatch records with optional filters."""
    q = db.query(DispatchRecord)

    if account_id:
        q = q.filter(DispatchRecord.account_id == account_id)
    if agency_id:
        q = q.filter(DispatchRecord.agency_id == agency_id)
    if triage_request_id:
        q = q.filter(DispatchRecord.triage_request_id == triage_request_id)

    total = q.count()
    results = q.order_by(DispatchRecord.dispatched_at.desc()).offset(offset).limit(limit).all()
    return results, total


def get_dispatch(db: Session, dispatch_id: UUID) -> Optional[DispatchRecord]:
    """Get a single dispatch record by ID."""
    return db.query(DispatchRecord).filter(DispatchRecord.id == dispatch_id).first()
