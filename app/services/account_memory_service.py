"""Account Memory Service — persistent ledger for account lifecycle events.

Records what was known, recommended, changed, and what happened next for
each account. All writes are additive — entries are never mutated.
"""

import logging
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import AccountMemoryEntry

logger = logging.getLogger(__name__)

VALID_ENTRY_TYPES = {
    "account_created",
    "brief_generated",
    "brief_viewed",
    "producer_edited",
    "producer_feedback",
    "outcome_logged",
    "renewal_started",
    "submission_packet_generated",
}


def create_account_memory_entry(
    db: Session,
    account_id: str,
    entry_type: str,
    summary: str,
    agency_id: Optional[str] = None,
    session_id: Optional[str] = None,
    industry: Optional[str] = None,
    payload_json: Optional[dict] = None,
    created_by: Optional[str] = None,
) -> dict:
    """Create a new account memory entry. Returns the entry as a dict."""
    if entry_type not in VALID_ENTRY_TYPES:
        raise ValueError(f"Invalid entry_type '{entry_type}'. Must be one of: {sorted(VALID_ENTRY_TYPES)}")

    entry = AccountMemoryEntry(
        account_id=account_id,
        agency_id=agency_id,
        session_id=session_id,
        industry=industry,
        entry_type=entry_type,
        summary=summary,
        payload_json=payload_json,
        created_by=created_by,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _entry_to_dict(entry)


def list_account_memory(db: Session, account_id: str) -> list[dict]:
    """List all memory entries for an account, ordered by created_at desc."""
    entries = (
        db.query(AccountMemoryEntry)
        .filter(AccountMemoryEntry.account_id == account_id)
        .order_by(AccountMemoryEntry.created_at.desc())
        .all()
    )
    return [_entry_to_dict(e) for e in entries]


def list_account_memory_by_agency(
    db: Session, agency_id: str, limit: int = 100,
) -> list[dict]:
    """List memory entries across all accounts for an agency."""
    entries = (
        db.query(AccountMemoryEntry)
        .filter(AccountMemoryEntry.agency_id == agency_id)
        .order_by(AccountMemoryEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_entry_to_dict(e) for e in entries]


def summarize_account_memory(db: Session, account_id: str) -> dict:
    """Return a compact summary of the account's memory ledger."""
    entries = (
        db.query(AccountMemoryEntry)
        .filter(AccountMemoryEntry.account_id == account_id)
        .order_by(AccountMemoryEntry.created_at.desc())
        .all()
    )

    if not entries:
        return {
            "account_id": account_id,
            "total_entries": 0,
            "latest_entry_type": None,
            "latest_summary": None,
            "entry_type_counts": {},
            "latest_outcome": None,
            "latest_brief_generated_at": None,
        }

    type_counts = Counter(e.entry_type for e in entries)

    latest_outcome = None
    for e in entries:
        if e.entry_type == "outcome_logged":
            latest_outcome = e.summary
            break

    latest_brief_at = None
    for e in entries:
        if e.entry_type == "brief_generated":
            latest_brief_at = e.created_at.isoformat() if e.created_at else None
            break

    latest = entries[0]
    return {
        "account_id": account_id,
        "total_entries": len(entries),
        "latest_entry_type": latest.entry_type,
        "latest_summary": latest.summary,
        "entry_type_counts": dict(type_counts),
        "latest_outcome": latest_outcome,
        "latest_brief_generated_at": latest_brief_at,
    }


def write_memory_safe(
    db: Session,
    account_id: str,
    entry_type: str,
    summary: str,
    **kwargs,
) -> Optional[dict]:
    """Non-blocking wrapper for writing memory entries from hooks.

    Returns the entry dict on success, None on failure.
    Never raises — logs errors and continues.
    """
    try:
        return create_account_memory_entry(
            db=db,
            account_id=account_id,
            entry_type=entry_type,
            summary=summary,
            **kwargs,
        )
    except Exception:
        logger.debug("Failed to write account memory entry", exc_info=True)
        return None


def _entry_to_dict(entry: AccountMemoryEntry) -> dict:
    """Serialize an AccountMemoryEntry to JSON-compatible dict."""
    return {
        "id": str(entry.id),
        "account_id": entry.account_id,
        "agency_id": entry.agency_id,
        "session_id": entry.session_id,
        "industry": entry.industry,
        "entry_type": entry.entry_type,
        "summary": entry.summary,
        "payload_json": entry.payload_json,
        "created_by": entry.created_by,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }
