"""Tests for experience mod analyzer — unit tests and integration tests."""

import pytest

from app.services.experience_mod_analyzer import analyze_experience_mod


# ============================================================
# UNIT TESTS — analyze_experience_mod()
# ============================================================


class TestModClassification:
    """Tests for mod classification flags and insights."""

    def test_basic_mod_above_unity(self):
        result = analyze_experience_mod(current_mod=1.10)
        assert any("above unity" in f for f in result["flags"])

    def test_basic_mod_significantly_above_unity(self):
        result = analyze_experience_mod(current_mod=1.30)
        assert any("significantly above unity" in f for f in result["flags"])

    def test_basic_mod_below_unity(self):
        result = analyze_experience_mod(current_mod=0.95)
        assert any("at or below unity" in i for i in result["insights"])

    def test_basic_mod_well_below_unity(self):
        result = analyze_experience_mod(current_mod=0.80)
        assert any("well below unity" in i for i in result["insights"])


class TestModTrending:
    """Tests for mod trend detection."""

    def test_mod_trend_improving(self):
        result = analyze_experience_mod(current_mod=0.90, prior_mod=1.05)
        assert result["mod_trend"]["direction"] == "improving"
        assert result["mod_trend"]["change"] < 0
        assert any("improved" in i or "safety investments" in i for i in result["insights"])

    def test_mod_trend_worsening(self):
        result = analyze_experience_mod(current_mod=1.15, prior_mod=1.00)
        assert result["mod_trend"]["direction"] == "worsening"
        assert result["mod_trend"]["change"] > 0
        assert any("increased" in f or "driving costs" in f for f in result["flags"])

    def test_mod_trend_flat(self):
        result = analyze_experience_mod(current_mod=1.00, prior_mod=1.00)
        assert result["mod_trend"]["direction"] == "flat"

    def test_no_prior_mod_no_trend(self):
        result = analyze_experience_mod(current_mod=1.10)
        assert result["mod_trend"] is None

    def test_small_change_no_trend_flag(self):
        """Change within ±0.05 doesn't generate trend flag/insight."""
        result = analyze_experience_mod(current_mod=1.03, prior_mod=1.00)
        assert result["mod_trend"]["direction"] == "worsening"
        # No flag about "increased" because change is only 0.03 (< 0.05 threshold)
        assert not any("increased" in f and "driving costs" in f for f in result["flags"])


class TestLossAnalysis:
    """Tests for expected vs actual loss deviation."""

    def test_loss_deviation_positive(self):
        result = analyze_experience_mod(
            current_mod=1.20,
            expected_losses=100_000,
            actual_primary_losses=90_000,
            actual_excess_losses=40_000,
        )
        assert result["loss_analysis"] is not None
        assert result["loss_analysis"]["deviation"] > 0
        assert any("primary mod driver" in f for f in result["flags"])

    def test_loss_deviation_favorable(self):
        result = analyze_experience_mod(
            current_mod=0.85,
            expected_losses=100_000,
            actual_primary_losses=50_000,
            actual_excess_losses=30_000,
        )
        assert result["loss_analysis"] is not None
        assert result["loss_analysis"]["deviation"] < 0
        assert any("favorable" in i for i in result["insights"])

    def test_primary_vs_excess_frequency(self):
        """Primary >70% triggers frequency flag."""
        result = analyze_experience_mod(
            current_mod=1.15,
            expected_losses=50_000,
            actual_primary_losses=80_000,
            actual_excess_losses=10_000,
        )
        assert any("frequency" in f.lower() for f in result["flags"])

    def test_primary_vs_excess_severity(self):
        """Excess >60% triggers severity flag."""
        result = analyze_experience_mod(
            current_mod=1.15,
            expected_losses=50_000,
            actual_primary_losses=20_000,
            actual_excess_losses=80_000,
        )
        assert any("excess losses dominate" in f.lower() for f in result["flags"])

    def test_no_loss_analysis_without_expected(self):
        result = analyze_experience_mod(
            current_mod=1.10,
            actual_primary_losses=50_000,
        )
        assert result["loss_analysis"] is None


class TestClaimsAnalysis:
    """Tests for claims impact categorization."""

    def test_claims_impact_categorization(self):
        claims = [
            {"description": "Back injury", "incurred": 60_000},
            {"description": "Slip and fall", "incurred": 20_000},
            {"description": "Minor cut", "incurred": 5_000},
        ]
        result = analyze_experience_mod(current_mod=1.15, mod_claims=claims)
        impacts = {c["description"]: c["mod_impact"] for c in result["claims_analysis"]}
        assert impacts["Back injury"] == "high"
        assert impacts["Slip and fall"] == "medium"
        assert impacts["Minor cut"] == "low"

    def test_medical_only_insight(self):
        claims = [
            {"description": "Strain", "incurred": 3_000, "medical_only": True},
            {"description": "Fracture", "incurred": 40_000, "medical_only": False},
        ]
        result = analyze_experience_mod(current_mod=1.10, mod_claims=claims)
        assert any("medical-only" in i and "70%" in i for i in result["insights"])

    def test_top_claim_flag(self):
        claims = [
            {"description": "Shoulder surgery", "incurred": 75_000},
            {"description": "Minor", "incurred": 2_000},
        ]
        result = analyze_experience_mod(current_mod=1.20, mod_claims=claims)
        assert any("Shoulder surgery" in f and "$75,000" in f for f in result["flags"])

    def test_claims_sorted_by_incurred(self):
        claims = [
            {"description": "Small", "incurred": 1_000},
            {"description": "Large", "incurred": 50_000},
            {"description": "Medium", "incurred": 20_000},
        ]
        result = analyze_experience_mod(current_mod=1.10, mod_claims=claims)
        incurred_values = [c["incurred"] for c in result["claims_analysis"]]
        assert incurred_values == sorted(incurred_values, reverse=True)

    def test_pct_of_total(self):
        claims = [
            {"description": "A", "incurred": 60_000},
            {"description": "B", "incurred": 40_000},
        ]
        result = analyze_experience_mod(current_mod=1.10, mod_claims=claims)
        pcts = {c["description"]: c["pct_of_total"] for c in result["claims_analysis"]}
        assert pcts["A"] == 0.6
        assert pcts["B"] == 0.4


class TestClassCodeAnalysis:
    """Tests for class code analysis."""

    def test_class_code_expected_losses(self):
        entries = [
            {"class_code": "5551", "description": "Roofing", "payroll": 500_000, "expected_loss_rate": 8.5},
        ]
        result = analyze_experience_mod(current_mod=1.10, class_code_entries=entries)
        assert len(result["class_code_analysis"]) == 1
        cc = result["class_code_analysis"][0]
        assert cc["class_code"] == "5551"
        assert cc["expected_losses"] == 42_500.0  # 500_000 * 8.5 / 100

    def test_class_code_no_rate(self):
        entries = [
            {"class_code": "8810", "description": "Clerical", "payroll": 200_000},
        ]
        result = analyze_experience_mod(current_mod=0.90, class_code_entries=entries)
        cc = result["class_code_analysis"][0]
        assert cc["expected_losses"] is None


class TestTalkingPoints:
    """Tests for talking points generation."""

    def test_talking_points_generated(self):
        result = analyze_experience_mod(current_mod=1.10)
        assert len(result["talking_points"]) >= 1

    def test_high_mod_framing(self):
        result = analyze_experience_mod(current_mod=1.25)
        assert any("reviewed the worksheet" in p for p in result["talking_points"])

    def test_low_mod_framing(self):
        result = analyze_experience_mod(current_mod=0.80)
        assert any("strength" in p for p in result["talking_points"])

    def test_worsening_trend_talking_point(self):
        result = analyze_experience_mod(current_mod=1.20, prior_mod=1.00)
        assert any("moved up" in p for p in result["talking_points"])

    def test_improving_trend_talking_point(self):
        result = analyze_experience_mod(current_mod=0.90, prior_mod=1.10)
        assert any("trending down" in p for p in result["talking_points"])

    def test_cross_reference_always_present(self):
        result = analyze_experience_mod(current_mod=1.00)
        assert any("cross-reference" in p.lower() for p in result["talking_points"])


class TestCaps:
    """Tests for output capping."""

    def test_flags_capped_at_5(self):
        # Extreme case with many triggers
        claims = [
            {"description": f"Claim {i}", "incurred": 60_000}
            for i in range(10)
        ]
        result = analyze_experience_mod(
            current_mod=1.30,
            prior_mod=1.00,
            expected_losses=10_000,
            actual_primary_losses=80_000,
            actual_excess_losses=5_000,
            mod_claims=claims,
        )
        assert len(result["flags"]) <= 5

    def test_talking_points_capped_at_5(self):
        result = analyze_experience_mod(
            current_mod=1.30,
            prior_mod=1.00,
            expected_losses=50_000,
            actual_primary_losses=80_000,
            actual_excess_losses=20_000,
            mod_claims=[
                {"description": "Big", "incurred": 100_000, "medical_only": False},
                {"description": "Med", "incurred": 5_000, "medical_only": True},
            ],
        )
        assert len(result["talking_points"]) <= 5


class TestEdgeCases:
    """Tests for edge cases and minimal inputs."""

    def test_empty_claims_and_class_codes(self):
        result = analyze_experience_mod(
            current_mod=1.05,
            mod_claims=[],
            class_code_entries=[],
        )
        assert result["claims_analysis"] == []
        assert result["class_code_analysis"] == []

    def test_all_none_optional_fields(self):
        result = analyze_experience_mod(current_mod=1.00)
        assert result["current_mod"] == 1.00
        assert result["prior_mod"] is None
        assert result["mod_trend"] is None
        assert result["loss_analysis"] is None
        assert result["claims_analysis"] == []
        assert result["class_code_analysis"] == []

    def test_return_structure(self):
        result = analyze_experience_mod(current_mod=1.10)
        expected_keys = {
            "current_mod", "prior_mod", "mod_trend", "loss_analysis",
            "claims_analysis", "class_code_analysis", "flags", "insights",
            "talking_points",
        }
        assert set(result.keys()) == expected_keys


# ============================================================
# INTEGRATION TESTS — coverage_gap_detector + producer_ammo
# ============================================================


class TestCoverageGapIntegration:
    """Experience mod data integration with coverage_gap_detector."""

    def test_mod_worsening_boosts_wc_confidence(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps

        # Roofing account missing WC, with worsening mod data
        profile = {
            "industry": "roofing",
            "state": "TX",
            "employee_count": 15,
            "current_coverages": ["general_liability", "commercial_auto"],
            "experience_mod_data": {
                "mod_trend": {"direction": "worsening", "current": 1.15, "prior": 1.00, "change": 0.15},
                "flags": ["Mod at 1.15 — above unity"],
                "talking_points": [],
            },
        }
        result = detect_coverage_gaps(profile)
        wc_gaps = [g for g in result["coverage_gaps"] if "workers" in g["coverage"].lower()]
        assert len(wc_gaps) >= 1

        wc_gap = wc_gaps[0]
        mod_rules = [r for r in wc_gap.get("applied_rules", []) if r["code"] == "mod_trend_worsening"]
        assert len(mod_rules) == 1
        assert mod_rules[0]["confidence_delta"] == 0.05

    def test_mod_above_unity_flag_boosts_wc(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps

        profile = {
            "industry": "roofing",
            "state": "TX",
            "employee_count": 15,
            "current_coverages": ["general_liability", "commercial_auto"],
            "experience_mod_data": {
                "mod_trend": None,
                "flags": ["Mod at 1.10 — above unity, room for improvement"],
                "talking_points": [],
            },
        }
        result = detect_coverage_gaps(profile)
        wc_gaps = [g for g in result["coverage_gaps"] if "workers" in g["coverage"].lower()]
        assert len(wc_gaps) >= 1
        mod_rules = [r for r in wc_gaps[0].get("applied_rules", []) if r["code"] == "mod_trend_worsening"]
        assert len(mod_rules) == 1

    def test_no_mod_data_no_change(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps

        profile = {
            "industry": "roofing",
            "state": "TX",
            "employee_count": 15,
            "current_coverages": ["general_liability", "commercial_auto"],
        }
        result = detect_coverage_gaps(profile)
        wc_gaps = [g for g in result["coverage_gaps"] if "workers" in g["coverage"].lower()]
        assert len(wc_gaps) >= 1
        mod_rules = [r for r in wc_gaps[0].get("applied_rules", []) if r["code"] == "mod_trend_worsening"]
        assert len(mod_rules) == 0

    def test_mod_rule_not_duplicated(self):
        """Both worsening trend and above-unity flag should only apply rule once."""
        from app.services.coverage_gap_detector import detect_coverage_gaps

        profile = {
            "industry": "roofing",
            "state": "TX",
            "employee_count": 15,
            "current_coverages": ["general_liability", "commercial_auto"],
            "experience_mod_data": {
                "mod_trend": {"direction": "worsening", "current": 1.15, "prior": 1.00, "change": 0.15},
                "flags": ["Mod at 1.15 — above unity"],
                "talking_points": [],
            },
        }
        result = detect_coverage_gaps(profile)
        wc_gaps = [g for g in result["coverage_gaps"] if "workers" in g["coverage"].lower()]
        mod_rules = [r for r in wc_gaps[0].get("applied_rules", []) if r["code"] == "mod_trend_worsening"]
        assert len(mod_rules) == 1  # Not duplicated


class TestProducerAmmoIntegration:
    """Experience mod data integration with producer_ammo."""

    def test_mod_flags_in_producer_ammo_underwriting(self):
        from app.services.producer_ammo import generate_producer_ammo

        profile = {
            "industry": "roofing",
            "state": "TX",
            "account_stage": "renewal",
            "experience_mod_data": {
                "flags": ["Mod at 1.20 — above unity, room for improvement"],
                "talking_points": ["Lead with the mod worksheet review."],
                "mod_trend": {"direction": "worsening"},
            },
        }
        result = generate_producer_ammo(profile)
        flags = result["ammo_questions"]["underwriting_flags"]
        assert any("above unity" in f for f in flags)

    def test_mod_talking_points_in_ammo_top_questions(self):
        from app.services.producer_ammo import generate_producer_ammo

        # Use a tier industry (fewer base questions) to avoid [:5] cap cutting appended items
        profile = {
            "industry": "Cattle Ranching",
            "state": "TX",
            "account_stage": "renewal",
            "experience_mod_data": {
                "flags": [],
                "talking_points": ["Lead with the mod worksheet review."],
                "mod_trend": None,
            },
        }
        result = generate_producer_ammo(profile)
        top = result["ammo_questions"]["top_questions"]
        assert any("mod worksheet" in q for q in top)

    def test_worsening_mod_adds_operational_question(self):
        from app.services.producer_ammo import generate_producer_ammo

        # Use a tier industry to avoid [:5] cap cutting the appended question
        profile = {
            "industry": "Cattle Ranching",
            "state": "TX",
            "account_stage": "prospect",
            "experience_mod_data": {
                "flags": [],
                "talking_points": [],
                "mod_trend": {"direction": "worsening"},
            },
        }
        result = generate_producer_ammo(profile)
        ops = result["ammo_questions"]["operational_change_questions"]
        assert any("trending upward" in q for q in ops)

    def test_no_mod_data_no_effect(self):
        from app.services.producer_ammo import generate_producer_ammo

        profile_with = {
            "industry": "roofing",
            "state": "TX",
            "account_stage": "renewal",
        }
        profile_without = {
            "industry": "roofing",
            "state": "TX",
            "account_stage": "renewal",
            "experience_mod_data": None,
        }
        result_with = generate_producer_ammo(profile_with)
        result_without = generate_producer_ammo(profile_without)
        # Both should produce same output when no mod data
        assert result_with["ammo_questions"] == result_without["ammo_questions"]
