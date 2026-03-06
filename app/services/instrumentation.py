"""Product Instrumentation — lightweight event logging for WAYOS product usage.

Records timestamped events (prep queries, coverage gap runs, ammo requests, etc.)
for analytics dashboards and product signals.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.models import EventLog

logger = logging.getLogger(__name__)


def log_event(
    db: Session,
    event_type: str,
    payload: dict | None = None,
    user_id: str | None = None,
) -> None:
    """Record a product event to the event_log table.

    Args:
        db: SQLAlchemy session
        event_type: Category string, e.g. "prep_query", "coverage_gap_run",
                     "producer_ammo_run", "agency_feed_view", "discovery_capture"
        payload: Optional JSON-serializable dict with event details
        user_id: Optional user identifier
    """
    try:
        event = EventLog(
            event_type=event_type,
            event_payload=payload,
            user_id=user_id,
        )
        db.add(event)
        db.commit()
    except Exception:
        logger.warning("Failed to log event %s", event_type, exc_info=True)
        db.rollback()


def get_product_signals(db: Session, days: int = 7) -> dict:
    """Aggregate product usage signals over the given time window.

    Returns:
        {"days": int, "signals": {event_type: count, ...}}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        rows = (
            db.query(EventLog)
            .filter(EventLog.created_at >= cutoff)
            .all()
        )
        counts = Counter(row.event_type for row in rows)
        signals = dict(counts.most_common())
    except Exception:
        logger.warning("Failed to query product signals", exc_info=True)
        signals = {}

    return {"days": days, "signals": signals}
