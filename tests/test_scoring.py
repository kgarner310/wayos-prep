"""Tests for scoring utilities."""

from datetime import datetime, timezone, timedelta
from app.services.scoring import compute_authority_score, compute_freshness_score


def test_authority_score_regulator():
    assert compute_authority_score("regulator") == 9.5


def test_authority_score_court():
    assert compute_authority_score("court") == 9.0


def test_authority_score_carrier():
    assert compute_authority_score("carrier") == 7.0


def test_authority_score_user():
    assert compute_authority_score("user") == 3.0


def test_authority_score_unknown():
    assert compute_authority_score("unknown") == 5.0


def test_freshness_score_none():
    assert compute_freshness_score(None) == 5.0


def test_freshness_score_recent():
    recent = datetime.now(timezone.utc) - timedelta(days=30)
    assert compute_freshness_score(recent) == 9.5


def test_freshness_score_old():
    old = datetime.now(timezone.utc) - timedelta(days=1200)
    assert compute_freshness_score(old) == 2.5


def test_freshness_score_moderate():
    moderate = datetime.now(timezone.utc) - timedelta(days=200)
    assert compute_freshness_score(moderate) == 7.0
