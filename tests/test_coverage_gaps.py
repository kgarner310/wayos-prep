"""Tests for the Coverage Gap Detector service."""

from app.services.coverage_gap_detector import detect_gaps


def test_fleet_industry_triggers_auto_gap():
    """Trucking without commercial auto should flag auto gap."""
    gaps = detect_gaps(
        industry="trucking", state="NC",
        known_coverages=[],
    )
    auto_gaps = [g for g in gaps if "auto" in g["title"].lower()]
    assert len(auto_gaps) >= 1
    assert auto_gaps[0]["severity"] == "high"


def test_no_auto_gap_when_coverage_present():
    """No auto gap when commercial auto is already known."""
    gaps = detect_gaps(
        industry="trucking", state="NC",
        known_coverages=["commercial_auto"],
    )
    auto_gaps = [g for g in gaps if g["title"] == "Commercial Auto Coverage Gap"]
    assert len(auto_gaps) == 0


def test_high_mod_triggers_gap():
    """High mod should trigger experience mod gap."""
    gaps = detect_gaps(
        industry="roofing", state="NC",
        current_mod=1.25,
    )
    mod_gaps = [g for g in gaps if "mod" in g["title"].lower()]
    assert len(mod_gaps) >= 1
    assert mod_gaps[0]["severity"] == "high"


def test_moderate_mod_triggers_medium_severity():
    """Mod above 1.0 but below 1.20 should be medium severity."""
    gaps = detect_gaps(
        industry="roofing", state="NC",
        current_mod=1.08,
    )
    mod_gaps = [g for g in gaps if "Experience Mod" in g["title"]]
    assert len(mod_gaps) == 1
    assert mod_gaps[0]["severity"] == "medium"


def test_subcontractor_exposure_triggers_gap():
    """Account with subcontractor trait should flag risk transfer gap."""
    gaps = detect_gaps(
        industry="roofing", state="NC",
        account_traits=["uses_subcontractors"],
    )
    sub_gaps = [g for g in gaps if "subcontractor" in g["title"].lower()]
    assert len(sub_gaps) >= 1
    assert sub_gaps[0]["severity"] == "high"


def test_wind_state_triggers_property_gap():
    """Florida should trigger wind/named storm gap."""
    gaps = detect_gaps(
        industry="manufacturing", state="FL",
    )
    wind_gaps = [g for g in gaps if "wind" in g["title"].lower()]
    assert len(wind_gaps) >= 1


def test_non_wind_state_no_wind_gap():
    """Ohio should not trigger wind gap."""
    gaps = detect_gaps(
        industry="manufacturing", state="OH",
    )
    wind_gaps = [g for g in gaps if "wind" in g["title"].lower()]
    assert len(wind_gaps) == 0


def test_large_employer_epli_gap():
    """50+ employees without EPLI should flag EPLI gap."""
    gaps = detect_gaps(
        industry="manufacturing", state="NC",
        employee_count=60,
        known_coverages=[],
    )
    epli_gaps = [g for g in gaps if "epli" in g["title"].lower()]
    assert len(epli_gaps) >= 1


def test_small_employer_no_epli_gap():
    """10 employees should NOT flag EPLI gap."""
    gaps = detect_gaps(
        industry="manufacturing", state="NC",
        employee_count=10,
    )
    epli_gaps = [g for g in gaps if "epli" in g["title"].lower()]
    assert len(epli_gaps) == 0


def test_public_entity_law_enforcement_gap():
    """Law enforcement department should flag LE liability gap."""
    gaps = detect_gaps(
        industry="municipality", state="NC",
        entity_type="public_entity",
        department="law_enforcement",
    )
    le_gaps = [g for g in gaps if "law enforcement" in g["title"].lower()]
    assert len(le_gaps) >= 1
    assert le_gaps[0]["severity"] == "high"


def test_roofing_inland_marine_gap():
    """Roofing without inland marine should flag tools/equipment gap."""
    gaps = detect_gaps(
        industry="roofing", state="NC",
        known_coverages=["workers_comp", "general_liability"],
    )
    im_gaps = [g for g in gaps if "inland marine" in g["title"].lower()]
    assert len(im_gaps) >= 1


def test_gaps_sorted_by_severity():
    """Gaps should be sorted: high first, then medium, then low."""
    gaps = detect_gaps(
        industry="roofing", state="FL",
        current_mod=1.25,
        employee_count=60,
        account_traits=["uses_subcontractors"],
    )
    if len(gaps) >= 2:
        severity_order = {"high": 0, "medium": 1, "low": 2}
        for i in range(len(gaps) - 1):
            assert severity_order[gaps[i]["severity"]] <= severity_order[gaps[i + 1]["severity"]]


def test_gaps_capped_at_10():
    """Should return at most 10 gaps."""
    gaps = detect_gaps(
        industry="roofing", state="FL",
        current_mod=1.30,
        employee_count=120,
        account_traits=["uses_subcontractors", "young_fleet", "delivery_operations"],
        active_risk_themes={"fleet_accidents", "falls_from_height", "machine_guarding"},
    )
    assert len(gaps) <= 10


def test_gap_has_required_fields():
    """Each gap should have all required fields."""
    gaps = detect_gaps(
        industry="trucking", state="NC",
        current_mod=1.15,
    )
    for gap in gaps:
        assert "title" in gap
        assert "severity" in gap
        assert gap["severity"] in ("high", "medium", "low")
        assert "reason" in gap
        assert "suggested_question" in gap
        assert "suggested_coverage_or_action" in gap
        assert "evidence_source" in gap


def test_business_income_gap_for_large_operations():
    """Large operations should flag business income review."""
    gaps = detect_gaps(
        industry="manufacturing", state="NC",
        employee_count=75,
    )
    bi_gaps = [g for g in gaps if "business income" in g["title"].lower()]
    assert len(bi_gaps) >= 1
