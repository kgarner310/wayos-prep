"""Tests for the Producer Ammo Questions Engine (generate_producer_ammo)."""

from app.services.producer_ammo import generate_producer_ammo


# --- Known industry response structure ---

def test_roofing_returns_all_sections():
    """Known industry should return all 4 ammo_questions sections."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
        "account_stage": "renewal",
    })
    assert "ammo_questions" in result
    ammo = result["ammo_questions"]
    assert "top_questions" in ammo
    assert "coverage_traps" in ammo
    assert "operational_change_questions" in ammo
    assert "underwriting_flags" in ammo


def test_response_includes_industry_and_stage():
    """Response should echo back industry and account_stage."""
    result = generate_producer_ammo({
        "industry": "trucking",
        "state": "TX",
        "account_stage": "prospect",
    })
    assert result["industry"] == "trucking"
    assert result["account_stage"] == "prospect"


def test_all_sections_are_lists_of_strings():
    """Every section should be a list of non-empty strings."""
    result = generate_producer_ammo({
        "industry": "manufacturing",
        "state": "OH",
        "employee_count": 50,
        "account_stage": "renewal",
    })
    for key in ["top_questions", "coverage_traps", "operational_change_questions", "underwriting_flags"]:
        section = result["ammo_questions"][key]
        assert isinstance(section, list)
        for item in section:
            assert isinstance(item, str)
            assert len(item) > 10


def test_sections_capped_at_5():
    """Each section should have at most 5 items."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "FL",
        "employee_count": 120,
        "vehicle_count": 10,
        "experience_mod": 1.30,
        "uses_subcontractors": True,
        "current_coverages": [],
        "claims_summary": "Two WC claims in 2024",
        "account_stage": "remarket",
    })
    for key in ["top_questions", "coverage_traps", "operational_change_questions", "underwriting_flags"]:
        assert len(result["ammo_questions"][key]) <= 5


def test_roofing_top_questions_are_industry_specific():
    """Roofing should produce roofing-specific top questions."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
        "account_stage": "renewal",
    })
    questions = result["ammo_questions"]["top_questions"]
    # At least one question should mention roofing-relevant terms
    relevant_terms = {"slope", "subcontract", "fall", "builder", "vehicle", "job site"}
    assert any(
        any(term in q.lower() for term in relevant_terms)
        for q in questions
    )


def test_trucking_top_questions():
    """Trucking should produce trucking-specific questions."""
    result = generate_producer_ammo({
        "industry": "trucking",
        "state": "TX",
        "account_stage": "renewal",
    })
    questions = result["ammo_questions"]["top_questions"]
    relevant_terms = {"driver", "cargo", "mvr", "dot", "telematics", "fleet"}
    assert any(
        any(term in q.lower() for term in relevant_terms)
        for q in questions
    )


def test_restaurant_coverage_traps():
    """Restaurant should flag industry-specific coverage traps."""
    result = generate_producer_ammo({
        "industry": "restaurant",
        "state": "CA",
        "account_stage": "renewal",
    })
    traps = result["ammo_questions"]["coverage_traps"]
    relevant_terms = {"liquor", "food", "delivery", "spoilage", "tip"}
    assert any(
        any(term in t.lower() for term in relevant_terms)
        for t in traps
    )


# --- Unknown industry fallback ---

def test_unknown_industry_returns_valid_response():
    """Unknown industry should still return a valid, complete response."""
    result = generate_producer_ammo({
        "industry": "underwater basket weaving",
        "state": "NC",
        "account_stage": "renewal",
    })
    assert "ammo_questions" in result
    ammo = result["ammo_questions"]
    assert len(ammo["top_questions"]) >= 1
    assert len(ammo["coverage_traps"]) >= 1
    assert len(ammo["underwriting_flags"]) >= 1
    assert len(ammo["operational_change_questions"]) >= 1


def test_unknown_industry_uses_generic_questions():
    """Unknown industry should use generic commercial-lines questions."""
    result = generate_producer_ammo({
        "industry": "space tourism",
        "state": "FL",
        "account_stage": "prospect",
    })
    questions = result["ammo_questions"]["top_questions"]
    # Generic questions should mention broad commercial terms
    assert any("operations" in q.lower() or "employees" in q.lower() for q in questions)


def test_unknown_industry_still_responds_to_attributes():
    """Unknown industry with high mod should still flag mod in questions."""
    result = generate_producer_ammo({
        "industry": "artisanal cheese making",
        "state": "OH",
        "experience_mod": 1.25,
        "account_stage": "renewal",
    })
    questions = result["ammo_questions"]["top_questions"]
    assert any("mod" in q.lower() or "1.25" in q for q in questions)


# --- Stage-based tailoring ---

def test_prospect_stage_generates_discovery_questions():
    """Prospect stage should focus on discovery and exposure mapping."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
        "account_stage": "prospect",
    })
    ops = result["ammo_questions"]["operational_change_questions"]
    # Prospect questions should include discovery language
    assert any("current" in q.lower() or "look like" in q.lower() or "contract" in q.lower() for q in ops)


def test_renewal_stage_generates_change_questions():
    """Renewal stage should ask about operational changes since last renewal."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
        "account_stage": "renewal",
    })
    ops = result["ammo_questions"]["operational_change_questions"]
    assert any("change" in q.lower() or "renewal" in q.lower() or "since" in q.lower() for q in ops)


def test_remarket_stage_generates_friction_questions():
    """Remarket stage should ask about underwriting friction and documentation."""
    result = generate_producer_ammo({
        "industry": "trucking",
        "state": "TX",
        "account_stage": "remarket",
    })
    ops = result["ammo_questions"]["operational_change_questions"]
    assert any("remarket" in q.lower() or "loss runs" in q.lower() or "documentation" in q.lower() or "carrier" in q.lower() for q in ops)


def test_service_review_stage_generates_drift_questions():
    """Service review stage should ask about account drift and endorsements."""
    result = generate_producer_ammo({
        "industry": "manufacturing",
        "state": "OH",
        "account_stage": "service_review",
    })
    ops = result["ammo_questions"]["operational_change_questions"]
    assert any("change" in q.lower() or "added" in q.lower() or "vehicle" in q.lower() or "location" in q.lower() for q in ops)


def test_invalid_stage_defaults_to_renewal():
    """Invalid account_stage should default to renewal."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
        "account_stage": "invalid_stage",
    })
    assert result["account_stage"] == "renewal"


def test_missing_stage_defaults_to_renewal():
    """Missing account_stage should default to renewal."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
    })
    assert result["account_stage"] == "renewal"


# --- Output contains all required categories ---

def test_output_has_top_questions():
    """Output must contain top_questions."""
    result = generate_producer_ammo({"industry": "hvac", "state": "NC"})
    assert "top_questions" in result["ammo_questions"]
    assert len(result["ammo_questions"]["top_questions"]) >= 1


def test_output_has_coverage_traps():
    """Output must contain coverage_traps."""
    result = generate_producer_ammo({"industry": "hvac", "state": "NC"})
    assert "coverage_traps" in result["ammo_questions"]
    assert len(result["ammo_questions"]["coverage_traps"]) >= 1


def test_output_has_operational_change_questions():
    """Output must contain operational_change_questions."""
    result = generate_producer_ammo({"industry": "hvac", "state": "NC"})
    assert "operational_change_questions" in result["ammo_questions"]
    assert len(result["ammo_questions"]["operational_change_questions"]) >= 1


def test_output_has_underwriting_flags():
    """Output must contain underwriting_flags."""
    result = generate_producer_ammo({"industry": "hvac", "state": "NC"})
    assert "underwriting_flags" in result["ammo_questions"]
    assert len(result["ammo_questions"]["underwriting_flags"]) >= 1


# --- Contextual tailoring ---

def test_high_mod_adds_underwriting_flag():
    """High experience mod should add a mod-related underwriting flag."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "NC",
        "experience_mod": 1.18,
    })
    flags = result["ammo_questions"]["underwriting_flags"]
    assert any("mod" in f.lower() or "1.18" in f for f in flags)


def test_subcontractor_usage_adds_questions():
    """Subcontractor usage should add relevant questions."""
    result = generate_producer_ammo({
        "industry": "landscaping",
        "state": "NC",
        "uses_subcontractors": True,
    })
    all_text = " ".join(
        result["ammo_questions"]["top_questions"]
        + result["ammo_questions"]["underwriting_flags"]
    )
    assert "subcontract" in all_text.lower() or "certificate" in all_text.lower()


def test_wind_state_adds_coverage_trap():
    """High-wind state should add named-storm coverage trap."""
    result = generate_producer_ammo({
        "industry": "roofing",
        "state": "FL",
    })
    traps = result["ammo_questions"]["coverage_traps"]
    assert any("storm" in t.lower() or "wind" in t.lower() or "FL" in t for t in traps)


def test_claims_summary_adds_underwriting_flag():
    """Providing claims_summary should add a claims-related underwriting flag."""
    result = generate_producer_ammo({
        "industry": "manufacturing",
        "state": "OH",
        "claims_summary": "Two WC claims totaling $120K in 2024",
    })
    flags = result["ammo_questions"]["underwriting_flags"]
    assert any("claim" in f.lower() or "loss" in f.lower() for f in flags)


def test_empty_profile_returns_valid_response():
    """Completely empty profile should return valid response."""
    result = generate_producer_ammo({})
    assert "ammo_questions" in result
    assert result["account_stage"] == "renewal"
    for key in ["top_questions", "coverage_traps", "operational_change_questions", "underwriting_flags"]:
        assert isinstance(result["ammo_questions"][key], list)


def test_industry_alias_normalization():
    """'roofing contractor' should normalize and use roofing questions."""
    result = generate_producer_ammo({
        "industry": "roofing contractor",
        "state": "NC",
    })
    # Should use roofing-specific questions, not generic
    questions = result["ammo_questions"]["top_questions"]
    relevant_terms = {"slope", "subcontract", "fall", "builder", "vehicle", "job site", "mod"}
    assert any(
        any(term in q.lower() for term in relevant_terms)
        for q in questions
    )
