"""Learning Store — in-memory store for office learnings and producer feedback.

Lightweight institutional memory layer. Canonical industry knowledge stays
stable; this store captures additive office-specific notes and feedback
for future intelligence work.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.knowledge.learning_models import OfficeLearning, ProducerFeedback

logger = logging.getLogger(__name__)

# ============================================================
# IN-MEMORY COLLECTIONS
# ============================================================

OFFICE_LEARNINGS: list[OfficeLearning] = []
PRODUCER_FEEDBACK: list[ProducerFeedback] = []


# ============================================================
# OFFICE LEARNINGS
# ============================================================


def add_office_learning(
    office_id: str,
    industry: str,
    note: str,
    created_by: Optional[str] = None,
    confidence: float = 0.5,
    tags: Optional[list[str]] = None,
) -> dict:
    """Add an office-specific learning note.

    Returns the created learning as a dict.
    """
    learning = OfficeLearning(
        office_id=office_id,
        industry=industry.lower().strip(),
        note=note,
        created_at=datetime.now(timezone.utc).isoformat(),
        created_by=created_by,
        confidence=confidence,
        tags=tags or [],
    )
    OFFICE_LEARNINGS.append(learning)
    logger.info(
        "Office learning added: office=%s industry=%s note=%.60s",
        office_id, industry, note,
    )
    return learning.to_dict()


def list_office_learnings(
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
) -> list[dict]:
    """List office learnings, optionally filtered by office_id and/or industry."""
    results = OFFICE_LEARNINGS
    if office_id:
        results = [l for l in results if l.office_id == office_id]
    if industry:
        key = industry.lower().strip()
        results = [l for l in results if l.industry == key]
    return [l.to_dict() for l in results]


# ============================================================
# PRODUCER FEEDBACK
# ============================================================


def add_producer_feedback(
    office_id: str,
    industry: str,
    endpoint: str,
    input_payload: dict,
    output_payload: dict,
    feedback_type: str,
    feedback_note: Optional[str] = None,
) -> dict:
    """Record producer feedback on WAYOS output.

    Returns the created feedback as a dict.
    """
    feedback = ProducerFeedback(
        office_id=office_id,
        industry=industry.lower().strip(),
        endpoint=endpoint,
        input_payload=input_payload,
        output_payload=output_payload,
        feedback_type=feedback_type,
        feedback_note=feedback_note,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    PRODUCER_FEEDBACK.append(feedback)
    logger.info(
        "Producer feedback recorded: office=%s industry=%s type=%s endpoint=%s",
        office_id, industry, feedback_type, endpoint,
    )
    return feedback.to_dict()


def list_producer_feedback(
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
) -> list[dict]:
    """List producer feedback, optionally filtered."""
    results = PRODUCER_FEEDBACK
    if office_id:
        results = [f for f in results if f.office_id == office_id]
    if industry:
        key = industry.lower().strip()
        results = [f for f in results if f.industry == key]
    return [f.to_dict() for f in results]


# ============================================================
# OFFICE CONTEXT
# ============================================================


def get_office_context(office_id: str, industry: str) -> dict:
    """Get aggregated office context for an industry.

    Returns learnings, feedback counts, and summary statistics.
    """
    key = industry.lower().strip()

    learnings = [
        l for l in OFFICE_LEARNINGS
        if l.office_id == office_id and l.industry == key
    ]
    feedback = [
        f for f in PRODUCER_FEEDBACK
        if f.office_id == office_id and f.industry == key
    ]

    positive_types = {"up", "useful"}
    negative_types = {"down", "not_useful"}

    return {
        "office_id": office_id,
        "industry": industry,
        "learnings": [l.to_dict() for l in learnings],
        "learning_count": len(learnings),
        "feedback_count": len(feedback),
        "positive_feedback_count": sum(
            1 for f in feedback if f.feedback_type in positive_types
        ),
        "negative_feedback_count": sum(
            1 for f in feedback if f.feedback_type in negative_types
        ),
    }


# ============================================================
# DEMO SEED DATA
# ============================================================


def seed_demo_learnings() -> int:
    """Seed demo office learnings. Returns count of learnings added."""
    demo_learnings = [
        {
            "office_id": "demo-roofing-nc",
            "industry": "roofing contractor",
            "note": "In this office, subcontractor certificate tracking is a recurring issue on smaller accounts.",
            "created_by": "demo-seed",
            "confidence": 0.7,
            "tags": ["subcontractors", "certificates"],
        },
        {
            "office_id": "demo-landscaping-tx",
            "industry": "landscaping contractor",
            "note": "Seasonal crews often create workers comp classification confusion.",
            "created_by": "demo-seed",
            "confidence": 0.65,
            "tags": ["workers comp", "seasonal labor"],
        },
        {
            "office_id": "demo-restaurant-ca",
            "industry": "restaurant",
            "note": "Delivery exposure is commonly missed when owners say they only use third-party apps.",
            "created_by": "demo-seed",
            "confidence": 0.8,
            "tags": ["delivery", "auto", "liability"],
        },
    ]

    count = 0
    for data in demo_learnings:
        # Skip if already seeded (check by note text)
        existing = [
            l for l in OFFICE_LEARNINGS
            if l.office_id == data["office_id"] and l.note == data["note"]
        ]
        if not existing:
            add_office_learning(**data)
            count += 1

    logger.info("Demo learnings seeded: %d new", count)
    return count
