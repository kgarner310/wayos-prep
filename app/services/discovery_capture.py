"""Discovery Capture — records producer-discovered exposures and coverage actions.

Tracks when a producer finds an exposure (via coverage gap engine, ammo questions,
or manual discovery) and whether coverage was added as a result.
"""

import logging

from sqlalchemy.orm import Session

from app.models.models import DiscoveryOutcome

logger = logging.getLogger(__name__)


def save_discovery(db: Session, data: dict) -> dict:
    """Persist a discovery outcome to the database.

    Args:
        db: SQLAlchemy session
        data: dict with keys:
            industry, state, source_type, source_key, exposure_found,
            and optional: account_stage, exposure_type, coverage_added, notes

    Returns:
        {"status": "ok", "saved": True}
    """
    outcome = DiscoveryOutcome(
        industry=data.get("industry", ""),
        state=(data.get("state") or "").upper(),
        account_stage=data.get("account_stage"),
        source_type=data.get("source_type", ""),
        source_key=data.get("source_key", ""),
        exposure_found=data.get("exposure_found", False),
        exposure_type=data.get("exposure_type"),
        coverage_added=data.get("coverage_added"),
        notes=data.get("notes"),
    )
    db.add(outcome)
    db.commit()

    logger.info(
        "Discovery captured: industry=%s source_type=%s exposure_found=%s",
        outcome.industry, outcome.source_type, outcome.exposure_found,
    )

    return {"status": "ok", "saved": True}
