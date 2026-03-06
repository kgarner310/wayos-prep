"""Tests for Account Risk Scoring service."""

from app.services.risk_scoring import (
    derive_base_exposure_score,
    apply_trait_amplifiers,
    apply_account_detail_modifiers,
    calculate_confidence_score,
    detect_coverage_gaps,
    detect_missing_information,
    assign_risk_band,
    INDUSTRY_BASELINES,
    DEPARTMENT_BASELINES,
)


# ============================================================
# RISK BAND ASSIGNMENT
# ============================================================

def test_risk_band_low():
    assert assign_risk_band(10.0) == "low"
    assert assign_risk_band(0.0) == "low"
    assert assign_risk_band(24.9) == "low"


def test_risk_band_moderate():
    assert assign_risk_band(25.0) == "moderate"
    assert assign_risk_band(49.9) == "moderate"


def test_risk_band_elevated():
    assert assign_risk_band(50.0) == "elevated"
    assert assign_risk_band(74.9) == "elevated"


def test_risk_band_high():
    assert assign_risk_band(75.0) == "high"
    assert assign_risk_band(100.0) == "high"


# ============================================================
# BASE EXPOSURE SCORE
# ============================================================

def test_roofing_baseline_with_falls():
    """Roofing industry with falls_from_height should produce elevated score."""
    score, components = derive_base_exposure_score(
        industry="roofing",
        entity_type="private_business",
        department=None,
        retrieved_themes=[{"slug": "falls_from_height", "strength": 0.8}],
        graph_themes=[],
    )
    # Baseline: 62 * 0.40 = 24.8, plus theme: 0.8 * 15 = 12
    assert score > 30.0
    assert any("falls_from_height" in c["key"] for c in components)


def test_trucking_baseline_with_fleet():
    """Trucking with fleet_accidents should reflect high exposure."""
    score, components = derive_base_exposure_score(
        industry="trucking",
        entity_type="private_business",
        department=None,
        retrieved_themes=[{"slug": "fleet_accidents", "strength": 0.75}],
        graph_themes=[],
    )
    # Baseline: 60 * 0.40 = 24, plus theme: 0.75 * 15 = 11.25
    assert score > 30.0
    assert any("fleet_accidents" in c["key"] for c in components)


def test_municipality_public_works_baseline():
    """Public entity with public_works department uses department baseline."""
    score, components = derive_base_exposure_score(
        industry="municipality",
        entity_type="public_entity",
        department="public_works",
        retrieved_themes=[{"slug": "road_maintenance_liability", "strength": 0.6}],
        graph_themes=[],
    )
    # Department baseline: 52 * 0.40 = 20.8, plus theme: 0.6 * 15 = 9
    assert score > 25.0
    baseline_comp = [c for c in components if "department_baseline" in c["key"]]
    assert len(baseline_comp) == 1
    assert baseline_comp[0]["raw"] == DEPARTMENT_BASELINES["public_works"]


def test_graph_themes_contribute_less():
    """Graph-expanded themes should contribute less than retrieved themes."""
    score_retrieved, _ = derive_base_exposure_score(
        industry="roofing",
        entity_type="private_business",
        department=None,
        retrieved_themes=[{"slug": "falls_from_height", "strength": 0.7}],
        graph_themes=[],
    )
    score_graph, _ = derive_base_exposure_score(
        industry="roofing",
        entity_type="private_business",
        department=None,
        retrieved_themes=[],
        graph_themes=[{"name": "falls_from_height", "node_type": "risk_theme", "weight": 0.7}],
    )
    assert score_retrieved > score_graph


def test_unknown_industry_uses_default():
    """Unknown industry should use default baseline."""
    score, components = derive_base_exposure_score(
        industry="basket_weaving",
        entity_type="private_business",
        department=None,
        retrieved_themes=[],
        graph_themes=[],
    )
    baseline_comp = [c for c in components if "industry_baseline" in c["key"]]
    assert baseline_comp[0]["raw"] == 40.0  # DEFAULT_INDUSTRY_BASELINE


# ============================================================
# TRAIT AMPLIFIERS
# ============================================================

def test_trait_amplifier_with_matching_themes():
    """Traits with matching active themes get full boost."""
    boost, components = apply_trait_amplifiers(
        account_traits=["uses_subcontractors"],
        active_themes={"subcontractor_transfer", "falls_from_height"},
    )
    assert boost > 0
    assert len(components) == 1
    assert "subcontractor" in components[0]["explanation"].lower()


def test_trait_amplifier_without_matching_themes():
    """Traits without matching themes get reduced boost (0.3x)."""
    full_boost, _ = apply_trait_amplifiers(
        account_traits=["young_fleet"],
        active_themes={"fleet_accidents"},
    )
    partial_boost, _ = apply_trait_amplifiers(
        account_traits=["young_fleet"],
        active_themes={"falls_from_height"},  # Unrelated theme
    )
    assert full_boost > partial_boost


def test_trait_amplifier_capped():
    """Total trait boost should be capped at 15.0."""
    boost, _ = apply_trait_amplifiers(
        account_traits=[
            "uses_subcontractors", "young_fleet", "high_mod",
            "heavy_equipment", "delivery_operations", "high_turnover",
        ],
        active_themes={
            "subcontractor_transfer", "fleet_accidents", "falls_from_height",
            "struck_by_object", "hired_non_owned_auto", "driver_turnover",
        },
    )
    assert boost <= 15.0


# ============================================================
# ACCOUNT DETAIL MODIFIERS
# ============================================================

def test_high_mod_increases_score():
    """High experience mod should increase score."""
    modifier, components = apply_account_detail_modifiers(
        employee_count=10, current_mod=1.35, department=None, entity_type="private_business",
    )
    assert modifier > 0
    mod_comp = [c for c in components if c["key"] == "current_mod"]
    assert len(mod_comp) == 1
    assert mod_comp[0]["weighted"] == 5.0


def test_low_mod_decreases_score():
    """Low experience mod should decrease score."""
    modifier, _ = apply_account_detail_modifiers(
        employee_count=10, current_mod=0.72, department=None, entity_type="private_business",
    )
    assert modifier < 0


def test_large_employee_count():
    """Large operations should get positive modifier."""
    modifier, components = apply_account_detail_modifiers(
        employee_count=150, current_mod=None, department=None, entity_type="private_business",
    )
    assert modifier > 0
    emp_comp = [c for c in components if c["key"] == "employee_count"]
    assert len(emp_comp) == 1


def test_small_employee_count_no_modifier():
    """Small operations should get no employee modifier."""
    modifier, components = apply_account_detail_modifiers(
        employee_count=10, current_mod=None, department=None, entity_type="private_business",
    )
    assert modifier == 0
    assert len(components) == 0


# ============================================================
# CONFIDENCE SCORING
# ============================================================

def test_confidence_decreases_with_weak_sources():
    """Low source confidence should produce low confidence score."""
    high_conf, _ = calculate_confidence_score(
        source_confidence=0.9, retrieved_theme_count=4,
        question_signal_count=3, graph_support_count=6,
    )
    low_conf, notes = calculate_confidence_score(
        source_confidence=0.1, retrieved_theme_count=1,
        question_signal_count=0, graph_support_count=1,
    )
    assert high_conf > low_conf
    assert any("confidence" in n.lower() or "limited" in n.lower() for n in notes)


def test_confidence_clamped():
    """Confidence should be clamped between 5 and 100."""
    conf, _ = calculate_confidence_score(
        source_confidence=1.0, retrieved_theme_count=10,
        question_signal_count=10, graph_support_count=20,
    )
    assert conf <= 100.0

    conf_low, _ = calculate_confidence_score(
        source_confidence=0.0, retrieved_theme_count=0,
        question_signal_count=0, graph_support_count=0,
    )
    assert conf_low >= 5.0


# ============================================================
# COVERAGE GAP DETECTION
# ============================================================

def test_fleet_without_commercial_auto_triggers_gap():
    """Fleet exposure without commercial_auto should trigger coverage gap."""
    gaps = detect_coverage_gaps(
        active_themes={"fleet_accidents"},
        known_coverages=[],
        theme_strengths={"fleet_accidents": 0.7},
    )
    assert len(gaps) > 0
    auto_gaps = [g for g in gaps if g["suggested_coverage"] == "commercial_auto"]
    assert len(auto_gaps) == 1
    assert auto_gaps[0]["alert_severity"] == "high"


def test_no_gap_when_coverage_present():
    """No gap should be flagged when required coverage is already known."""
    gaps = detect_coverage_gaps(
        active_themes={"fleet_accidents"},
        known_coverages=["commercial_auto", "umbrella"],
        theme_strengths={"fleet_accidents": 0.7},
    )
    assert len(gaps) == 0


def test_low_severity_gap_for_weak_theme():
    """Weak theme strength should produce low severity gap."""
    gaps = detect_coverage_gaps(
        active_themes={"slip_and_fall"},
        known_coverages=[],
        theme_strengths={"slip_and_fall": 0.2},
    )
    assert len(gaps) > 0
    assert gaps[0]["alert_severity"] == "low"


def test_multiple_coverage_gaps():
    """Multiple active themes should produce multiple gaps."""
    gaps = detect_coverage_gaps(
        active_themes={"falls_from_height", "fleet_accidents", "subcontractor_transfer"},
        known_coverages=[],
        theme_strengths={
            "falls_from_height": 0.8,
            "fleet_accidents": 0.7,
            "subcontractor_transfer": 0.6,
        },
    )
    assert len(gaps) >= 4  # WC, GL, commercial_auto, umbrella at minimum


# ============================================================
# MISSING INFORMATION DETECTION
# ============================================================

def test_roofing_triggers_subcontractor_question():
    """Roofing industry should trigger subcontractor usage question."""
    alerts = detect_missing_information(
        industry="roofing",
        entity_type="private_business",
        department=None,
        account_traits=[],
        active_themes=set(),
    )
    sub_alerts = [a for a in alerts if a["missing_field"] == "subcontractor_usage"]
    assert len(sub_alerts) == 1


def test_law_enforcement_triggers_body_camera_question():
    """Law enforcement department should trigger body camera question."""
    alerts = detect_missing_information(
        industry="municipality",
        entity_type="public_entity",
        department="law_enforcement",
        account_traits=[],
        active_themes=set(),
    )
    cam_alerts = [a for a in alerts if a["missing_field"] == "body_camera_policy"]
    assert len(cam_alerts) == 1
    assert cam_alerts[0]["alert_severity"] == "high"


def test_fleet_themes_trigger_mvr_question():
    """Active fleet themes should trigger MVR screening question."""
    alerts = detect_missing_information(
        industry="trucking",
        entity_type="private_business",
        department=None,
        account_traits=[],
        active_themes={"fleet_accidents"},
    )
    mvr_alerts = [a for a in alerts if a["missing_field"] == "mvr_screening"]
    assert len(mvr_alerts) == 1


# ============================================================
# END-TO-END SCORE SHAPE
# ============================================================

def test_roofing_score_shape():
    """Verify a roofing account produces expected score structure."""
    score, components = derive_base_exposure_score(
        industry="roofing",
        entity_type="private_business",
        department=None,
        retrieved_themes=[
            {"slug": "falls_from_height", "strength": 0.8},
            {"slug": "heat_illness", "strength": 0.5},
        ],
        graph_themes=[],
    )
    trait_boost, _ = apply_trait_amplifiers(
        account_traits=["residential_work"],
        active_themes={"falls_from_height", "heat_illness"},
    )
    detail_mod, _ = apply_account_detail_modifiers(
        employee_count=25, current_mod=1.15, department=None, entity_type="private_business",
    )
    final = min(max(score + trait_boost + detail_mod, 0.0), 100.0)
    band = assign_risk_band(final)

    assert final > 30.0  # Roofing with real themes should be at least moderate
    assert band in ("moderate", "elevated", "high")
