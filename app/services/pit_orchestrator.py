"""PIT Orchestrator — Transition layer wiring triage -> dispatch -> account memory.

When a triage request is approved, this orchestrator:
1. Creates DispatchRecord entries for each draft (insured, carrier, AMS note)
2. Logs to AccountMemoryEntry so the account ledger reflects the action
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import ServiceTriageRequest, DispatchRecord, AccountMemoryEntry
from app.services.dispatch_service import create_dispatch

logger = logging.getLogger(__name__)


def on_triage_approved(
    db: Session,
    triage_request_id: UUID,
    approved_by_user_id: Optional[UUID] = None,
) -> list[DispatchRecord]:
    """Called when a triage request is approved. Creates dispatch records and logs to account memory."""
    triage = db.query(ServiceTriageRequest).filter(
        ServiceTriageRequest.id == triage_request_id
    ).first()
    if not triage:
        logger.warning("on_triage_approved: triage %s not found", triage_request_id)
        return []

    dispatch_records = []
    dispatch_summaries = []

    # Create dispatch for insured draft
    if triage.draft_insured:
        rec = create_dispatch(
            db=db,
            recipient_type="insured",
            channel="email",
            subject=triage.draft_insured.get("subject", ""),
            body=triage.draft_insured.get("body", ""),
            triage_request_id=triage.id,
            account_id=triage.account_id,
            agency_id=triage.agency_id,
            dispatched_by_user_id=approved_by_user_id,
            status="logged",
        )
        dispatch_records.append(rec)
        dispatch_summaries.append("insured notified")

    # Create dispatch for carrier draft
    if triage.draft_carrier:
        rec = create_dispatch(
            db=db,
            recipient_type="carrier",
            channel="email",
            subject=triage.draft_carrier.get("subject", ""),
            body=triage.draft_carrier.get("body", ""),
            triage_request_id=triage.id,
            account_id=triage.account_id,
            agency_id=triage.agency_id,
            dispatched_by_user_id=approved_by_user_id,
            status="logged",
        )
        dispatch_records.append(rec)
        dispatch_summaries.append("carrier contacted")

    # Create dispatch for AMS note
    if triage.draft_ams_note:
        note = triage.draft_ams_note
        body_parts = [note.get("summary", "")]
        action_items = note.get("action_items", [])
        if action_items:
            body_parts.append("\nAction Items:")
            body_parts.extend(f"- {item}" for item in action_items)

        rec = create_dispatch(
            db=db,
            recipient_type="internal",
            channel="ams_note",
            subject=note.get("category", "Service Note"),
            body="\n".join(body_parts),
            triage_request_id=triage.id,
            account_id=triage.account_id,
            agency_id=triage.agency_id,
            dispatched_by_user_id=approved_by_user_id,
            status="logged",
        )
        dispatch_records.append(rec)
        dispatch_summaries.append("AMS note logged")

    # Log to account memory if we have an account
    if triage.account_id and dispatch_records:
        request_type = (triage.request_type or "service request").replace("_", " ")
        summary_text = f"{request_type.title()} triaged and dispatched"
        if dispatch_summaries:
            summary_text += f" — {', '.join(dispatch_summaries)}"

        memory_entry = AccountMemoryEntry(
            account_id=str(triage.account_id),
            agency_id=str(triage.agency_id) if triage.agency_id else None,
            entry_type="service_dispatch",
            summary=summary_text,
            payload_json={
                "triage_request_id": str(triage.id),
                "dispatch_ids": [str(r.id) for r in dispatch_records],
                "request_type": triage.request_type,
                "urgency": triage.urgency,
            },
            created_by=str(approved_by_user_id) if approved_by_user_id else None,
        )
        db.add(memory_entry)
        db.flush()

    logger.info(
        "PIT orchestrator: triage %s approved -> %d dispatches created",
        triage_request_id, len(dispatch_records),
    )
    return dispatch_records
