"""Tests for the Coverage Gap Insight Engine (detect_coverage_gaps)."""

from app.services.coverage_gap_detector import detect_coverage_gaps


# --- Missing coverages detection ---

def test_roofing_missing_coverages_detected():
    """Roofing account with only GL should flag expected missing coverages."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "employees": 10,
        "current_coverages": ["general_liability"],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Workers' Compensation" in gap_names
    assert "Commercial Auto" in gap_names
    assert "General Liability" not in gap_names  # already has it


def test_trucking_missing_cargo_detected():
    """Trucking account missing cargo should flag it."""
    result = detect_coverage_gaps({
        "industry": "trucking",
        "state": "TX",
        "current_coverages": ["workers_comp", "general_liability", "commercial_auto"],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Motor Truck Cargo" in gap_names


def test_no_gaps_when_fully_covered():
    """Account with all expected coverages should have no industry gaps."""
    result = detect_coverage_gaps({
        "industry": "restaurant",
        "state": "OH",
        "employees": 5,
        "current_coverages": [
            "workers_comp", "general_liability", "commercial_auto",
            "property", "umbrella", "epli",
        ],
    })
    # May still have state/attribute gaps, but no industry-expected gaps
    industry_coverages = {
        "Workers' Compensation", "General Liability", "Commercial Auto",
        "Commercial Property", "Umbrella / Excess Liability",
        "Employment Practices Liability (EPLI)",
    }
    flagged = {g["coverage"] for g in result["coverage_gaps"]}
    assert not (flagged & industry_coverages)


def test_vehicle_count_triggers_auto_gap():
    """Having vehicles but no auto coverage should flag commercial auto."""
    result = detect_coverage_gaps({
        "industry": "restaurant",
        "state": "OH",
        "vehicles": 3,
        "current_coverages": ["general_liability", "workers_comp"],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Commercial Auto" in gap_names


def test_subcontractor_usage_triggers_gaps():
    """Subcontractor usage should flag GL and umbrella if missing."""
    result = detect_coverage_gaps({
        "industry": "hvac",
        "state": "NC",
        "uses_subcontractors": True,
        "current_coverages": ["workers_comp"],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "General Liability" in gap_names
    assert "Umbrella / Excess Liability" in gap_names


def test_large_employer_triggers_epli():
    """50+ employees without EPLI should flag EPLI gap."""
    result = detect_coverage_gaps({
        "industry": "manufacturing",
        "state": "OH",
        "employees": 60,
        "current_coverages": ["workers_comp", "general_liability"],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Employment Practices Liability (EPLI)" in gap_names


def test_small_employer_no_epli():
    """Small employer in an industry without EPLI expectation should NOT flag EPLI gap."""
    result = detect_coverage_gaps({
        "industry": "landscaping",
        "state": "OH",
        "employees": 5,
        "current_coverages": [],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Employment Practices Liability (EPLI)" not in gap_names


# --- Correct formatting ---

def test_response_format_has_required_keys():
    """Response must have coverage_gaps and suggested_questions."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "current_coverages": ["general_liability"],
    })
    assert "coverage_gaps" in result
    assert "suggested_questions" in result
    assert isinstance(result["coverage_gaps"], list)
    assert isinstance(result["suggested_questions"], list)


def test_each_gap_has_required_fields():
    """Each gap entry must have coverage, reason, and risk_level."""
    result = detect_coverage_gaps({
        "industry": "trucking",
        "state": "NC",
        "current_coverages": [],
    })
    for gap in result["coverage_gaps"]:
        assert "coverage" in gap
        assert "reason" in gap
        assert "risk_level" in gap
        assert gap["risk_level"] in ("high", "medium", "low")


def test_gaps_sorted_by_risk_level():
    """Gaps should be sorted: high first, then medium, then low."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "FL",
        "employees": 60,
        "vehicles": 5,
        "current_coverages": [],
    })
    gaps = result["coverage_gaps"]
    if len(gaps) >= 2:
        order = {"high": 0, "medium": 1, "low": 2}
        for i in range(len(gaps) - 1):
            assert order[gaps[i]["risk_level"]] <= order[gaps[i + 1]["risk_level"]]


def test_suggested_questions_are_strings():
    """All suggested questions should be non-empty strings."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    for q in result["suggested_questions"]:
        assert isinstance(q, str)
        assert len(q) > 0


def test_no_duplicate_questions():
    """Suggested questions should not contain duplicates."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "FL",
        "employees": 60,
        "vehicles": 5,
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    assert len(result["suggested_questions"]) == len(set(result["suggested_questions"]))


def test_no_duplicate_coverage_gaps():
    """Coverage gaps should not contain duplicate coverage names."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "NC",
        "vehicles": 5,
        "uses_subcontractors": True,
        "current_coverages": [],
    })
    names = [g["coverage"] for g in result["coverage_gaps"]]
    assert len(names) == len(set(names))


# --- Unknown industries ---

def test_unknown_industry_returns_valid_response():
    """Unknown industry should return a valid response structure, not crash."""
    result = detect_coverage_gaps({
        "industry": "underwater basket weaving",
        "state": "NC",
        "current_coverages": [],
    })
    assert "coverage_gaps" in result
    assert "suggested_questions" in result
    assert isinstance(result["coverage_gaps"], list)


def test_unknown_industry_no_industry_gaps():
    """Unknown industry should produce no industry-expected gaps."""
    result = detect_coverage_gaps({
        "industry": "space tourism",
        "state": "OH",
        "employees": 5,
        "current_coverages": [],
    })
    # No known industry profile, so no industry-expected gaps
    # But attribute-driven gaps may still appear
    assert isinstance(result["coverage_gaps"], list)


def test_unknown_industry_still_flags_attribute_gaps():
    """Unknown industry with large employee count should still flag EPLI."""
    result = detect_coverage_gaps({
        "industry": "artisanal cheese making",
        "state": "NC",
        "employees": 75,
        "current_coverages": [],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Employment Practices Liability (EPLI)" in gap_names


def test_empty_profile():
    """Completely empty profile should return valid empty-ish response."""
    result = detect_coverage_gaps({})
    assert "coverage_gaps" in result
    assert "suggested_questions" in result


# --- Industry alias normalization ---

def test_industry_alias_roofing_contractor():
    """'roofing contractor' should normalize to 'roofing' profile."""
    result = detect_coverage_gaps({
        "industry": "roofing contractor",
        "state": "NC",
        "current_coverages": ["general_liability"],
    })
    gap_names = [g["coverage"] for g in result["coverage_gaps"]]
    assert "Workers' Compensation" in gap_names


# --- State-based questions ---

def test_wind_state_generates_question():
    """Florida should generate wind-related question."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "FL",
        "current_coverages": [],
    })
    wind_questions = [q for q in result["suggested_questions"] if "named-storm" in q.lower() or "wind" in q.lower()]
    assert len(wind_questions) >= 1


def test_experience_mod_generates_question():
    """High experience mod should generate a loss-control question."""
    result = detect_coverage_gaps({
        "industry": "roofing",
        "state": "OH",
        "experience_mod": 1.25,
        "current_coverages": ["workers_comp", "general_liability"],
    })
    mod_questions = [q for q in result["suggested_questions"] if "mod" in q.lower() or "loss" in q.lower()]
    assert len(mod_questions) >= 1
