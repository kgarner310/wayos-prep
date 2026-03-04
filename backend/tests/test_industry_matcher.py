"""Tests for industry matching logic.

Note: These tests use mocked database objects since SQLite doesn't support
PostgreSQL ARRAY columns used in the real model.
"""
from unittest.mock import MagicMock, patch


def _make_profile(name, synonyms=None):
    """Create a mock industry profile."""
    p = MagicMock()
    p.industry_name = name
    p.synonyms = synonyms or []
    return p


@patch("app.services.industry_matcher.settings")
def test_direct_name_match(mock_settings):
    mock_settings.llm_provider = "none"

    from app.services.industry_matcher import match_industry

    mock_db = MagicMock()
    roofing = _make_profile("Roofing", ["roofer"])

    # Simulate ilike match
    mock_db.query.return_value.filter.return_value.first.return_value = roofing

    result = match_industry("roofing", mock_db)
    assert result.industry_name == "Roofing"


@patch("app.services.industry_matcher.settings")
def test_synonym_match(mock_settings):
    mock_settings.llm_provider = "none"

    from app.services.industry_matcher import match_industry

    mock_db = MagicMock()

    # Direct match returns None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    roofing = _make_profile("Roofing", ["roofer", "roofing contractor"])
    landscaping = _make_profile("Landscaping", ["landscaper", "lawn care"])
    mock_db.query.return_value.all.return_value = [roofing, landscaping]

    result = match_industry("I need help with a roofer", mock_db)
    assert result.industry_name == "Roofing"


@patch("app.services.industry_matcher.settings")
def test_no_match_returns_none(mock_settings):
    mock_settings.llm_provider = "none"

    from app.services.industry_matcher import match_industry

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.all.return_value = [
        _make_profile("Roofing", ["roofer"]),
    ]

    result = match_industry("underwater basket weaving", mock_db)
    assert result is None
