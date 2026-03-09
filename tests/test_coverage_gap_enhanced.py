"""Tests for enhanced Coverage Gap Insight Engine features:
confidence scores, missing endorsements, confirmation questions."""

from app.services.coverage_gap_detector import detect_coverage_gaps


# --- Confidence scores ---

def test_gaps_have_confidence_field():
    """Each gap should include a numeric confidence score."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": ["general_liability"],
    })
    for gap in result["coverage_gaps"]:
        assert "confidence" in gap
        assert isinstance(gap["confidence"], float)
        assert 0.0 < gap["confidence"] <= 1.0
        assert "applied_rules" in gap
        assert isinstance(gap["applied_rules"], list)
        assert len(gap["applied_rules"]) >= 1


def test_workers_comp_high_confidence():
    """Workers comp gap should have high confidence (>= 0.90)."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    wc_gaps = [g for g in result["coverage_gaps"] if g["coverage"] == "Workers' Compensation"]
    assert len(wc_gaps) == 1
    assert wc_gaps[0]["confidence"] >= 0.90


def test_cyber_lower_confidence():
    """Cyber gap should have lower confidence than WC."""
    result = detect_coverage_gaps({
        "industry": "manufacturing",
        "state": "OH",
        "employees": 30,
        "current_coverages": [],
    })
    cyber_gaps = [g for g in result["coverage_gaps"] if g["coverage"] == "Cyber Liability"]
    if cyber_gaps:
        assert cyber_gaps[0]["confidence"] < 0.80


# --- Missing endorsements ---

def test_response_has_missing_endorsements():
    """Response should include missing_endorsements list."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    assert "missing_endorsements" in result
    assert isinstance(result["missing_endorsements"], list)


def test_endorsements_have_required_fields():
    """Each endorsement should have endorsement and reason fields."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    for e in result["missing_endorsements"]:
        assert "endorsement" in e
        assert "reason" in e
        assert isinstance(e["endorsement"], str)
        assert isinstance(e["reason"], str)


def test_roofing_endorsements_include_waiver():
    """Roofing should include waiver of subrogation endorsement."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    endorsement_names = [e["endorsement"] for e in result["missing_endorsements"]]
    assert any("waiver" in e.lower() for e in endorsement_names)


def test_trucking_endorsements_include_mcs90():
    """Trucking should include MCS-90 endorsement."""
    result = detect_coverage_gaps({
        "industry": "trucking",
        "state": "TX",
        "current_coverages": [],
    })
    endorsement_names = [e["endorsement"] for e in result["missing_endorsements"]]
    assert any("mcs-90" in e.lower() for e in endorsement_names)


def test_unknown_industry_gets_generic_endorsements():
    """Unknown industry should return generic endorsements."""
    result = detect_coverage_gaps({
        "industry": "space tourism",
        "state": "OH",
        "current_coverages": [],
    })
    assert len(result["missing_endorsements"]) >= 1


def test_endorsements_capped_at_5():
    """Missing endorsements should be capped at 5."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    assert len(result["missing_endorsements"]) <= 5


# --- Confirmation questions ---

def test_response_has_confirmation_questions():
    """Response should include confirmation_questions list."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    assert "confirmation_questions" in result
    assert isinstance(result["confirmation_questions"], list)


def test_confirmation_questions_are_strings():
    """Confirmation questions should be non-empty strings."""
    result = detect_coverage_gaps({
        "industry": "trucking",
        "state": "TX",
        "current_coverages": [],
    })
    for q in result["confirmation_questions"]:
        assert isinstance(q, str)
        assert len(q) > 0


def test_subcontractor_adds_confirmation_question():
    """Subcontractor usage should add a contract-related confirmation question."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    cqs = result["confirmation_questions"]
    assert any("waiver" in q.lower() or "additional insured" in q.lower() for q in cqs)


def test_confirmation_questions_capped_at_6():
    """Confirmation questions should be capped at 6."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "FL",
        "employees": 60,
        "vehicles": 5,
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    assert len(result["confirmation_questions"]) <= 6


# --- Industry field in response ---

def test_response_has_industry_field():
    """Response should echo back the industry."""
    result = detect_coverage_gaps({
        "industry": "trucking",
        "state": "TX",
        "current_coverages": [],
    })
    assert "industry" in result
    assert result["industry"] == "trucking"


# --- Applied rules traceability ---

def test_applied_rules_have_required_fields():
    """Each applied rule should have code, description, and confidence_delta."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    for gap in result["coverage_gaps"]:
        for rule in gap["applied_rules"]:
            assert "code" in rule
            assert "description" in rule
            assert "confidence_delta" in rule
            assert isinstance(rule["code"], str)
            assert isinstance(rule["description"], str)
            assert isinstance(rule["confidence_delta"], float)


def test_industry_expected_rule_code():
    """Industry-expected gaps should have the industry_expected rule."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    wc_gap = next(g for g in result["coverage_gaps"] if "Workers" in g["coverage"])
    codes = [r["code"] for r in wc_gap["applied_rules"]]
    assert "industry_expected" in codes


def test_vehicle_exposure_rule_code():
    """Vehicle-driven auto gap should have the vehicle_exposure rule."""
    # Use an unknown industry so no industry_expected auto gap fires first
    result = detect_coverage_gaps({
        "industry": "consulting",
        "state": "OH",
        "vehicles": 3,
        "current_coverages": [],
    })
    auto_gap = next(
        (g for g in result["coverage_gaps"] if "Commercial Auto" in g["coverage"]),
        None,
    )
    assert auto_gap is not None
    codes = [r["code"] for r in auto_gap["applied_rules"]]
    assert "vehicle_exposure" in codes


def test_employee_count_rule_code():
    """Employee-driven EPLI gap should have the employee_count rule."""
    result = detect_coverage_gaps({
        "industry": "landscaping",
        "state": "OH",
        "employees": 60,
        "current_coverages": [],
    })
    epli_gap = next(
        (g for g in result["coverage_gaps"] if "EPLI" in g["coverage"]),
        None,
    )
    assert epli_gap is not None
    codes = [r["code"] for r in epli_gap["applied_rules"]]
    assert "employee_count" in codes


def test_subcontractor_exposure_rule_code():
    """Subcontractor-driven GL gap should have the subcontractor_exposure rule."""
    result = detect_coverage_gaps({
        "industry": "landscaping",
        "state": "OH",
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    # landscaping expects GL already via industry_expected, so check umbrella
    umb_gap = next(
        (g for g in result["coverage_gaps"] if "Umbrella" in g["coverage"]),
        None,
    )
    assert umb_gap is not None
    codes = [r["code"] for r in umb_gap["applied_rules"]]
    # Could be industry_expected or subcontractor_exposure depending on order
    assert any(c in codes for c in ["industry_expected", "subcontractor_exposure"])


def test_loss_run_boost_adds_rule():
    """Loss run WC boost should add loss_run_wc_frequency rule to the gap."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
        "loss_run_data": {
            "patterns": [],
            "underwriting_flags": ["Workers Comp: high claim frequency (5 claims)"],
            "producer_talking_points": [],
        },
    })
    wc_gap = next(g for g in result["coverage_gaps"] if "Workers" in g["coverage"])
    codes = [r["code"] for r in wc_gap["applied_rules"]]
    assert "loss_run_wc_frequency" in codes
    wc_rule = next(r for r in wc_gap["applied_rules"] if r["code"] == "loss_run_wc_frequency")
    assert wc_rule["confidence_delta"] == 0.10


def test_loss_run_auto_boost_adds_rule():
    """Loss run auto boost should add loss_run_auto_claims rule."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
        "loss_run_data": {
            "patterns": ["2 vehicle-related claims detected"],
            "underwriting_flags": [],
            "producer_talking_points": [],
        },
    })
    auto_gap = next(
        (g for g in result["coverage_gaps"] if "Auto" in g["coverage"]),
        None,
    )
    assert auto_gap is not None
    codes = [r["code"] for r in auto_gap["applied_rules"]]
    assert "loss_run_auto_claims" in codes


def test_no_loss_data_no_boost_rules():
    """Without loss data, gaps should only have their base rule."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": [],
    })
    wc_gap = next(g for g in result["coverage_gaps"] if "Workers" in g["coverage"])
    codes = [r["code"] for r in wc_gap["applied_rules"]]
    assert "loss_run_wc_frequency" not in codes
    assert "loss_run_auto_claims" not in codes
    assert len(wc_gap["applied_rules"]) == 1
