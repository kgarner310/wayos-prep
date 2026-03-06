"""Producer question retrieval service.

Retrieves relevant producer questions from the database
based on entity type, department, risk theme, and coverage filters.
"""

import logging

from sqlalchemy import or_, cast, Text
from sqlalchemy.orm import Session

from app.models.models import ProducerQuestion

logger = logging.getLogger(__name__)

# Max questions to return per query
MAX_QUESTIONS = 8


def get_producer_questions(
    db: Session,
    entity_type: str | None = None,
    department: str | None = None,
    risk_themes: list[str] | None = None,
    coverages: list[str] | None = None,
    category: str | None = None,
    limit: int = MAX_QUESTIONS,
) -> list[dict]:
    """Retrieve producer questions matching query criteria.

    Filters are applied with OR logic across risk_themes and coverages
    to maximize relevant question coverage. Results are sorted by
    importance_score descending.

    Returns list of question dicts ready for brief integration.
    """
    q = db.query(ProducerQuestion)

    # Entity type filter (required match if provided)
    if entity_type:
        q = q.filter(ProducerQuestion.entity_type == entity_type)

    # Department filter — match specific department or general questions
    if department:
        q = q.filter(
            or_(
                ProducerQuestion.department == department,
                ProducerQuestion.department.is_(None),
            )
        )

    # Category filter
    if category:
        q = q.filter(ProducerQuestion.category == category)

    # Risk theme and coverage filters (OR logic — match any)
    theme_coverage_filters = []
    if risk_themes:
        theme_coverage_filters.append(ProducerQuestion.risk_theme.in_(risk_themes))
    if coverages:
        # coverage is JSONB array — use ?| operator to match any value in the array
        from sqlalchemy.dialects.postgresql import JSONB as JSONB_TYPE
        from sqlalchemy import text, literal_column
        for cov in coverages:
            theme_coverage_filters.append(
                ProducerQuestion.coverage.op("@>")(f'["{cov}"]')
            )

    if theme_coverage_filters:
        q = q.filter(or_(*theme_coverage_filters))

    # Sort by importance, then difficulty (easier questions first for producers)
    q = q.order_by(
        ProducerQuestion.importance_score.desc(),
        ProducerQuestion.difficulty_score.asc(),
    )

    questions = q.limit(limit).all()

    return [
        {
            "id": str(pq.id),
            "question": pq.question_text,
            "purpose": pq.purpose or "",
            "category": pq.category,
            "department": pq.department,
            "risk_theme": pq.risk_theme,
            "coverage": pq.coverage,
            "importance_score": float(pq.importance_score) if pq.importance_score else 5.0,
            "follow_up_questions": pq.follow_up_questions or [],
        }
        for pq in questions
    ]


def get_questions_for_brief(
    db: Session,
    entity_type: str | None = None,
    department: str | None = None,
    risk_themes: list[str] | None = None,
    coverages: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    """Get producer questions formatted for brief integration.

    Returns questions in the format expected by the brief's
    questions_to_ask section.
    """
    questions = get_producer_questions(
        db=db,
        entity_type=entity_type,
        department=department,
        risk_themes=risk_themes,
        coverages=coverages,
        limit=limit,
    )

    # Convert to brief format
    return [
        {
            "question": q["question"],
            "purpose": q["purpose"],
            "source_ids": [],  # DB questions don't have source attribution
        }
        for q in questions
    ]
