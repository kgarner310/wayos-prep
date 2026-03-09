"""Tests for the Agency Ammo Feed (build_agency_ammo_feed)."""

from app.services.agency_ammo_feed import (
    build_agency_ammo_feed,
    normalize_question_theme,
    summarize_top_themes,
    summarize_rising_topics,
    summarize_common_gaps,
    suggest_openers_from_patterns,
)


# ============================================================
# Feed response structure
# ============================================================

def test_response_has_all_top_level_keys():
    """Response must include industry, state, date_range_days, summary."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    assert "industry" in result
    assert "state" in result
    assert "date_range_days" in result
    assert "summary" in result


def test_summary_has_all_sections():
    """Summary must contain all 4 sections."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    summary = result["summary"]
    assert "top_question_themes" in summary
    assert "rising_risk_topics" in summary
    assert "common_coverage_gaps" in summary
    assert "suggested_openers" in summary


def test_all_sections_are_lists_of_strings():
    """Every section should be a list of non-empty strings."""
    result = build_agency_ammo_feed({"industry": "trucking", "state": "TX"})
    for key in ["top_question_themes", "rising_risk_topics", "common_coverage_gaps", "suggested_openers"]:
        section = result["summary"][key]
        assert isinstance(section, list)
        for item in section:
            assert isinstance(item, str)
            assert len(item) > 0


def test_response_echoes_filters():
    """Response should echo back the filter values."""
    result = build_agency_ammo_feed({
        "industry": "roofing contractor",
        "state": "NC",
        "date_range_days": 60,
    })
    assert result["industry"] == "roofing contractor"
    assert result["state"] == "NC"
    assert result["date_range_days"] == 60


def test_default_date_range():
    """Missing date_range_days should default to 30."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    assert result["date_range_days"] == 30


def test_negative_date_range_defaults_to_30():
    """Negative date_range_days should default to 30."""
    result = build_agency_ammo_feed({
        "industry": "roofing",
        "state": "NC",
        "date_range_days": -5,
    })
    assert result["date_range_days"] == 30


# ============================================================
# Empty / sparse log fallback behavior
# ============================================================

def test_empty_filters_returns_valid_response():
    """Completely empty filters should return a valid response with generic data."""
    result = build_agency_ammo_feed({})
    assert "summary" in result
    summary = result["summary"]
    assert len(summary["top_question_themes"]) >= 1
    assert len(summary["common_coverage_gaps"]) >= 1
    assert len(summary["suggested_openers"]) >= 1


def test_no_db_falls_back_to_seeded():
    """When no DB session is provided, should use seeded industry data."""
    result = build_agency_ammo_feed(
        {"industry": "roofing", "state": "NC"},
        db=None,
    )
    summary = result["summary"]
    assert len(summary["top_question_themes"]) >= 1
    assert len(summary["rising_risk_topics"]) >= 1
    assert len(summary["common_coverage_gaps"]) >= 1
    assert len(summary["suggested_openers"]) >= 1


def test_unknown_industry_returns_generic_data():
    """Unknown industry should return generic fallback data."""
    result = build_agency_ammo_feed({
        "industry": "underwater basket weaving",
        "state": "OH",
    })
    summary = result["summary"]
    assert len(summary["top_question_themes"]) >= 1
    assert len(summary["common_coverage_gaps"]) >= 1
    assert len(summary["suggested_openers"]) >= 1


def test_sparse_logs_uses_seeded_data():
    """With no real logs (db=None), should still produce meaningful output."""
    result = build_agency_ammo_feed(
        {"industry": "manufacturing", "state": "OH"},
        db=None,
    )
    summary = result["summary"]
    # Should have manufacturing-relevant content
    all_text = " ".join(
        summary["top_question_themes"]
        + summary["rising_risk_topics"]
        + summary["common_coverage_gaps"]
    ).lower()
    # At least some manufacturing-relevant terms should appear
    assert any(term in all_text for term in [
        "machine", "lockout", "osha", "equipment", "combustible", "product",
        "cyber", "inland marine",
    ])


# ============================================================
# Question theme aggregation
# ============================================================

def test_normalize_subcontractor_theme():
    """Subcontractor-related questions should normalize to subcontractor theme."""
    theme = normalize_question_theme(
        "How are subcontractor certificates and AI requirements being tracked?"
    )
    assert theme == "subcontractor certificate tracking"


def test_normalize_vehicle_theme():
    """Personal vehicle questions should normalize to personal vehicle theme."""
    theme = normalize_question_theme(
        "Do any employees use personal vehicles to job sites?"
    )
    assert theme == "personal vehicle use on company business"


def test_normalize_mvr_theme():
    """MVR/driver screening questions should normalize correctly."""
    theme = normalize_question_theme(
        "Do you run MVR checks on all drivers at hire and annually?"
    )
    assert theme == "driver eligibility and MVR concerns"


def test_normalize_mod_theme():
    """Experience mod questions should normalize correctly."""
    theme = normalize_question_theme(
        "Your experience mod is 1.18 — what loss control changes have been made?"
    )
    assert theme == "experience modification concerns"


def test_normalize_fleet_theme():
    """Fleet/vehicle count questions should normalize correctly."""
    theme = normalize_question_theme(
        "How many vehicles are in your fleet, and who takes them home?"
    )
    assert theme == "fleet management and auto exposure"


def test_normalize_unknown_returns_none():
    """Questions that don't match any pattern should return None."""
    theme = normalize_question_theme(
        "What is the meaning of life?"
    )
    assert theme is None


def test_normalize_case_insensitive():
    """Theme normalization should be case-insensitive."""
    theme = normalize_question_theme(
        "Do you have a LOCKOUT/TAGOUT program?"
    )
    assert theme == "lockout/tagout and machine guarding"


def test_summarize_top_themes_from_logs():
    """With log entries, should extract and rank themes by frequency."""
    logs = [
        {"query": "How are subcontractor certificates tracked?"},
        {"query": "Do employees use personal vehicles?"},
        {"query": "Tell me about your subcontractor COI compliance"},
        {"query": "Any subcontractor certificate issues?"},
        {"query": "What about fleet telematics?"},
    ]
    themes = summarize_top_themes(logs, industry="roofing")
    assert themes[0] == "subcontractor certificate tracking"


def test_summarize_top_themes_empty_logs():
    """With empty logs, should fall back to seeded data."""
    themes = summarize_top_themes([], industry="roofing")
    assert len(themes) >= 1


def test_summarize_rising_topics_sparse():
    """With fewer than 10 logs, should fall back to seeded data."""
    logs = [{"query": "subcontractor question"}] * 3
    topics = summarize_rising_topics(logs, industry="roofing", date_range_days=30)
    assert len(topics) >= 1


def test_summarize_rising_topics_enough_data():
    """With 10+ logs, should attempt trend detection."""
    # Recent half has more subcontractor mentions
    logs = (
        [{"query": "How are subcontractor certificates tracked?"}] * 6
        + [{"query": "What about fleet telematics?"}] * 6
    )
    topics = summarize_rising_topics(logs, industry="roofing", date_range_days=30)
    assert len(topics) >= 1
    # Subcontractor should be rising (more in recent half)
    assert topics[0] == "subcontractor certificate tracking"


# ============================================================
# Industry / state filter handling
# ============================================================

def test_roofing_industry_produces_relevant_content():
    """Roofing industry should produce roofing-specific themes and gaps."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    summary = result["summary"]
    all_content = " ".join(
        summary["top_question_themes"]
        + summary["common_coverage_gaps"]
        + summary["suggested_openers"]
    ).lower()
    # Should mention roofing-relevant concerns
    roofing_terms = ["subcontract", "vehicle", "fall", "equipment", "inland marine", "builders risk", "slope", "tool"]
    assert any(term in all_content for term in roofing_terms)


def test_trucking_industry_produces_relevant_content():
    """Trucking industry should produce trucking-specific themes and gaps."""
    result = build_agency_ammo_feed({"industry": "trucking", "state": "TX"})
    summary = result["summary"]
    all_content = " ".join(
        summary["top_question_themes"]
        + summary["common_coverage_gaps"]
    ).lower()
    trucking_terms = ["cargo", "driver", "mvr", "fleet", "dot", "freight"]
    assert any(term in all_content for term in trucking_terms)


def test_different_industries_produce_different_feeds():
    """Different industries should produce different feed content."""
    roofing = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    trucking = build_agency_ammo_feed({"industry": "trucking", "state": "TX"})
    # At least the gaps should differ
    assert roofing["summary"]["common_coverage_gaps"] != trucking["summary"]["common_coverage_gaps"]


def test_state_is_echoed_correctly():
    """State filter should be echoed in uppercase."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "nc"})
    assert result["state"] == "NC"


def test_industry_alias_handling():
    """Industry aliases should normalize correctly."""
    result = build_agency_ammo_feed({"industry": "roofing contractor", "state": "NC"})
    summary = result["summary"]
    # Should use roofing-specific data
    assert len(summary["top_question_themes"]) >= 1
    assert len(summary["common_coverage_gaps"]) >= 1


# ============================================================
# Coverage gap summarization
# ============================================================

def test_common_gaps_for_roofing():
    """Roofing should flag commonly missed coverages."""
    gaps = summarize_common_gaps("roofing")
    assert len(gaps) >= 1
    gaps_lower = [g.lower() for g in gaps]
    # Roofing commonly misses inland marine and builders risk
    assert any("inland marine" in g or "equipment" in g for g in gaps_lower)


def test_common_gaps_for_trucking():
    """Trucking should flag cargo coverage."""
    gaps = summarize_common_gaps("trucking")
    gaps_lower = [g.lower() for g in gaps]
    assert any("cargo" in g for g in gaps_lower)


def test_common_gaps_unknown_industry():
    """Unknown industry should return generic gaps."""
    gaps = summarize_common_gaps("space exploration")
    assert len(gaps) >= 1


# ============================================================
# Suggested openers
# ============================================================

def test_openers_are_question_format():
    """Suggested openers should generally be in question format."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    openers = result["summary"]["suggested_openers"]
    assert len(openers) >= 1
    # Most openers should end with ?
    question_count = sum(1 for o in openers if o.strip().endswith("?"))
    assert question_count >= len(openers) // 2


def test_openers_max_4():
    """Suggested openers should be capped at 4."""
    result = build_agency_ammo_feed({"industry": "roofing", "state": "NC"})
    assert len(result["summary"]["suggested_openers"]) <= 4


def test_openers_prioritize_themes():
    """Openers should prioritize questions matching top themes."""
    openers = suggest_openers_from_patterns(
        "roofing",
        ["subcontractor certificate tracking", "personal vehicle use on company business"],
    )
    assert len(openers) >= 1
