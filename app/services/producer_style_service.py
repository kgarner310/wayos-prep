"""Producer style preferences persistence service."""

import logging

from sqlalchemy.orm import Session

from app.models.models import ProducerStylePreference

logger = logging.getLogger(__name__)


def save_style(db: Session, data: dict) -> ProducerStylePreference:
    """Create or update producer style preferences (upsert by producer_id)."""
    producer_id = data["producer_id"]
    existing = (
        db.query(ProducerStylePreference)
        .filter(ProducerStylePreference.producer_id == producer_id)
        .first()
    )

    if existing:
        for key, value in data.items():
            if key != "producer_id" and value is not None and hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        logger.info("Producer style updated: producer_id=%s", producer_id)
        return existing

    pref = ProducerStylePreference(
        producer_id=producer_id,
        audience=data.get("audience", "underwriter"),
        default_posture=data.get("default_posture", "balanced"),
        directness=data.get("directness"),
        verbosity=data.get("verbosity"),
        warmth=data.get("warmth"),
        confidence_style=data.get("confidence_style"),
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    logger.info("Producer style created: producer_id=%s", producer_id)
    return pref


def get_style(db: Session, producer_id: str) -> ProducerStylePreference | None:
    """Get style preferences by producer ID."""
    return (
        db.query(ProducerStylePreference)
        .filter(ProducerStylePreference.producer_id == producer_id)
        .first()
    )


def update_style(db: Session, producer_id: str, data: dict) -> ProducerStylePreference | None:
    """Update style preferences for a producer."""
    pref = (
        db.query(ProducerStylePreference)
        .filter(ProducerStylePreference.producer_id == producer_id)
        .first()
    )
    if not pref:
        return None

    for key, value in data.items():
        if value is not None and hasattr(pref, key):
            setattr(pref, key, value)

    db.commit()
    db.refresh(pref)
    logger.info("Producer style updated: producer_id=%s", producer_id)
    return pref
