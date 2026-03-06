"""Scoring utilities for authority and freshness."""

from datetime import datetime, timezone
from app.core.enums import AuthorityLevel


def compute_authority_score(authority_level: str) -> float:
    return AuthorityLevel.SCORES.get(authority_level, 5.0)


def compute_freshness_score(published_at: datetime | None) -> float:
    if not published_at:
        return 5.0

    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    age_days = (now - published_at).days

    if age_days <= 90:
        return 9.5
    elif age_days <= 180:
        return 8.5
    elif age_days <= 365:
        return 7.0
    elif age_days <= 730:
        return 5.5
    elif age_days <= 1095:
        return 4.0
    else:
        return 2.5
