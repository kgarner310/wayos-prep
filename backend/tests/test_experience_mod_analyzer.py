"""Tests for the experience mod analyzer service."""
from app.services.experience_mod_analyzer import analyze_experience_mod, render_experience_mod_text


def test_basic_mod_above_unity():
    result = analyze_experience_mod(current_mod=1.25)

    assert result["current_mod"] == 1.25
    assert any("above unity" in f.lower() or "significantly above" in f.lower() for f in result["flags"])
    assert len(result["talking_points"]) > 0


def test_basic_mod_below_unity():
    result = analyze_experience_mod(current_mod=0.80)

    assert result["current_mod"] == 0.80
    assert any("below unity" in i.lower() for i in result["insights"])


def test_mod_trending_improving():
    result = analyze_experience_mod(current_mod=0.95, prior_mod=1.10)

    assert result["mod_trend"] is not None
    assert result["mod_trend"]["direction"] == "improving"
    assert result["mod_trend"]["change"] < 0
    assert any("improved" in i.lower() or "improving" in i.lower() or "trending down" in p.lower()
               for p in result.get("talking_points", [])
               for i in result.get("insights", [p]))


def test_mod_trending_worsening():
    result = analyze_experience_mod(current_mod=1.20, prior_mod=1.05)

    assert result["mod_trend"]["direction"] == "worsening"
    assert result["mod_trend"]["change"] > 0
    assert any("increased" in f.lower() for f in result["flags"])


def test_mod_flat():
    result = analyze_experience_mod(current_mod=1.00, prior_mod=1.00)

    assert result["mod_trend"]["direction"] == "flat"
    assert result["mod_trend"]["change"] == 0


def test_loss_deviation_positive():
    result = analyze_experience_mod(
        current_mod=1.15,
        expected_losses=100000,
        actual_primary_losses=90000,
        actual_excess_losses=40000,
    )

    assert result["loss_analysis"] is not None
    assert result["loss_analysis"]["actual_total"] == 130000
    assert result["loss_analysis"]["deviation"] == 30000
    # 30% deviation should be flagged
    assert any("exceed" in f.lower() for f in result["flags"])


def test_loss_deviation_favorable():
    result = analyze_experience_mod(
        current_mod=0.85,
        expected_losses=100000,
        actual_primary_losses=40000,
        actual_excess_losses=10000,
    )

    assert result["loss_analysis"]["deviation"] == -50000
    assert any("below expected" in i.lower() or "favorable" in i.lower() for i in result["insights"])


def test_primary_vs_excess_frequency():
    result = analyze_experience_mod(
        current_mod=1.15,
        expected_losses=100000,
        actual_primary_losses=80000,
        actual_excess_losses=10000,
    )

    # Primary is 89% of total — should flag frequency
    assert any("primary" in f.lower() and "frequency" in f.lower() for f in result["flags"])


def test_excess_dominated():
    result = analyze_experience_mod(
        current_mod=1.15,
        expected_losses=100000,
        actual_primary_losses=10000,
        actual_excess_losses=90000,
    )

    assert any("excess" in f.lower() and "large claims" in f.lower() for f in result["flags"])


def test_claims_analysis():
    result = analyze_experience_mod(
        current_mod=1.20,
        mod_claims=[
            {"description": "Back injury — warehouse", "incurred": 75000, "medical_only": False, "year": "2023"},
            {"description": "Finger laceration", "incurred": 5000, "medical_only": True, "year": "2024"},
        ],
    )

    assert len(result["claims_analysis"]) == 2
    # Sorted by incurred desc
    assert result["claims_analysis"][0]["incurred"] == 75000
    assert result["claims_analysis"][0]["mod_impact"] == "high"
    assert result["claims_analysis"][1]["mod_impact"] == "low"

    # Should note medical vs indemnity
    assert any("medical-only" in i.lower() for i in result["insights"])

    # Top claim should be flagged
    assert any("top claim" in f.lower() or "biggest" in f.lower() for f in result["flags"])


def test_class_code_analysis():
    result = analyze_experience_mod(
        current_mod=1.10,
        class_code_entries=[
            {"class_code": "8810", "description": "Clerical", "payroll": 500000, "expected_loss_rate": 0.15},
            {"class_code": "5403", "description": "Carpentry", "payroll": 200000, "expected_loss_rate": 8.50},
        ],
    )

    assert len(result["class_code_analysis"]) == 2
    assert result["class_code_analysis"][0]["expected_losses"] is not None


def test_render_experience_mod_text():
    result = analyze_experience_mod(
        current_mod=1.15,
        prior_mod=1.05,
        expected_losses=80000,
        actual_primary_losses=60000,
        actual_excess_losses=30000,
        mod_claims=[
            {"description": "Back injury", "incurred": 55000, "medical_only": False},
        ],
    )
    text = render_experience_mod_text(result, "XYZ Plumbing")

    assert "XYZ PLUMBING" in text
    assert "WAYOS PREP" in text
    assert "1.15" in text
    assert "1.05" in text
    assert "WORSENING" in text
    assert "EXPECTED vs ACTUAL" in text
    assert "Back injury" in text
    assert "PRODUCER TALKING POINTS" in text


def test_mod_reduction_strategies_above_unity():
    result = analyze_experience_mod(current_mod=1.10)

    assert any("reduction strategies" in p.lower() or "return-to-work" in p.lower()
               for p in result["talking_points"])


def test_cross_reference_talking_point():
    result = analyze_experience_mod(current_mod=1.00)

    assert any("cross-reference" in p.lower() for p in result["talking_points"])


def test_well_below_unity_strength():
    result = analyze_experience_mod(current_mod=0.75)

    assert any("strength" in p.lower() or "negotiate" in p.lower()
               for p in result["talking_points"])
