"""Tests for the Producer Ammo service."""

from app.services.producer_ammo import generate_ammo


def test_ammo_returns_all_sections():
    """Ammo should always return all 4 sections."""
    ammo = generate_ammo(industry="roofing", state="NC")
    assert "renewal_pressure_points" in ammo
    assert "underwriting_hot_buttons" in ammo
    assert "cross_sell_openings" in ammo
    assert "hard_questions_to_ask" in ammo


def test_ammo_sections_are_lists():
    """Each section should be a list of strings."""
    ammo = generate_ammo(industry="roofing", state="NC", current_mod=1.15)
    for key in ["renewal_pressure_points", "underwriting_hot_buttons", "cross_sell_openings", "hard_questions_to_ask"]:
        assert isinstance(ammo[key], list)
        for item in ammo[key]:
            assert isinstance(item, str)
            assert len(item) > 10  # Should be substantive


def test_high_mod_generates_renewal_pressure():
    """High mod should generate mod-specific renewal pressure point."""
    ammo = generate_ammo(
        industry="roofing", state="NC",
        current_mod=1.20,
    )
    mod_items = [p for p in ammo["renewal_pressure_points"] if "mod" in p.lower()]
    assert len(mod_items) >= 1


def test_low_mod_generates_leverage_point():
    """Low mod should generate positive leverage point."""
    ammo = generate_ammo(
        industry="manufacturing", state="NC",
        current_mod=0.78,
    )
    low_mod_items = [p for p in ammo["renewal_pressure_points"] if "better than average" in p.lower()]
    assert len(low_mod_items) >= 1


def test_fleet_themes_generate_underwriting_points():
    """Fleet risk themes should trigger fleet underwriting hot button."""
    ammo = generate_ammo(
        industry="trucking", state="NC",
        risk_themes={"fleet_accidents"},
    )
    fleet_items = [u for u in ammo["underwriting_hot_buttons"] if "fleet" in u.lower()]
    assert len(fleet_items) >= 1


def test_sub_usage_generates_hard_question():
    """Subcontractor usage should generate hard question about COI/AI."""
    ammo = generate_ammo(
        industry="roofing", state="NC",
        account_traits=["uses_subcontractors"],
    )
    sub_questions = [q for q in ammo["hard_questions_to_ask"] if "sub" in q.lower() or "coi" in q.lower()]
    assert len(sub_questions) >= 1


def test_missing_cyber_generates_cross_sell():
    """No cyber coverage should generate cross-sell opening."""
    ammo = generate_ammo(
        industry="manufacturing", state="NC",
        employee_count=30,
        coverage_tags={"workers_comp", "general_liability"},
    )
    cyber_items = [c for c in ammo["cross_sell_openings"] if "cyber" in c.lower()]
    assert len(cyber_items) >= 1


def test_missing_epli_generates_cross_sell():
    """No EPLI with 25+ employees should generate EPLI cross-sell."""
    ammo = generate_ammo(
        industry="manufacturing", state="NC",
        employee_count=35,
        coverage_tags=set(),
    )
    epli_items = [c for c in ammo["cross_sell_openings"] if "epli" in c.lower()]
    assert len(epli_items) >= 1


def test_roofing_generates_falls_underwriting():
    """Roofing with falls theme should generate falls underwriting point."""
    ammo = generate_ammo(
        industry="roofing", state="NC",
        risk_themes={"falls_from_height"},
    )
    falls_items = [u for u in ammo["underwriting_hot_buttons"] if "fall" in u.lower()]
    assert len(falls_items) >= 1


def test_public_entity_generates_renewal_point():
    """Public entity should generate pool comparison point."""
    ammo = generate_ammo(
        industry="municipality", state="NC",
        entity_type="public_entity",
    )
    pool_items = [p for p in ammo["renewal_pressure_points"] if "pool" in p.lower()]
    assert len(pool_items) >= 1


def test_law_enforcement_generates_underwriting_point():
    """Law enforcement department should generate LE underwriting point."""
    ammo = generate_ammo(
        industry="municipality", state="NC",
        entity_type="public_entity",
        department="law_enforcement",
    )
    le_items = [u for u in ammo["underwriting_hot_buttons"] if "force" in u.lower() or "camera" in u.lower()]
    assert len(le_items) >= 1


def test_default_ammo_when_no_triggers():
    """Should still produce content even with minimal inputs."""
    ammo = generate_ammo(industry="unknown_industry", state="XX")
    # Should have at least defaults
    assert len(ammo["renewal_pressure_points"]) >= 1
    assert len(ammo["underwriting_hot_buttons"]) >= 1
    assert len(ammo["hard_questions_to_ask"]) >= 1


def test_sections_capped_at_5():
    """Each section should have at most 5 items."""
    ammo = generate_ammo(
        industry="roofing", state="FL",
        current_mod=1.25,
        employee_count=120,
        account_traits=["uses_subcontractors", "young_fleet", "heavy_equipment", "multi_state_operations", "high_turnover"],
        risk_themes={"fleet_accidents", "falls_from_height", "subcontractor_transfer"},
    )
    for key in ["renewal_pressure_points", "underwriting_hot_buttons", "cross_sell_openings", "hard_questions_to_ask"]:
        assert len(ammo[key]) <= 5
