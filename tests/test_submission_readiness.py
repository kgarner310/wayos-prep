"""Tests for Submission Readiness Scoring system.

Tests cover:
- Template registry and lookup
- Readiness evaluation for multiple industries
- Scoring mechanics (penalties, clamping, levels)
- Weak field detection
- Strength identification
- Office learnings integration
- API endpoints
- Demo example endpoints
- Regressions
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.knowledge.submission_requirements import (
    SubmissionRequirement,
    IndustrySubmissionTemplate,
    INDUSTRY_SUBMISSION_TEMPLATES,
    get_submission_template,
    list_submission_templates,
)
from app.services.submission_readiness import (
    evaluate_submission_readiness,
    normalize_submission_input,
    is_weak_field,
    build_readiness_explanation,
)
from app.main import app

client = TestClient(app)


# ============================================================
# TEMPLATE REGISTRY
# ============================================================


class TestTemplateRegistry:
    def test_templates_loaded(self):
        assert len(INDUSTRY_SUBMISSION_TEMPLATES) >= 6

    def test_roofing_template_exists(self):
        t = get_submission_template("roofing contractor")
        assert t is not None
        assert t.industry == "roofing contractor"

    def test_suffix_fallback(self):
        t = get_submission_template("roofing")
        assert t is not None
        assert t.industry == "roofing contractor"

    def test_case_insensitive(self):
        t = get_submission_template("ROOFING CONTRACTOR")
        assert t is not None

    def test_trucking_template(self):
        t = get_submission_template("trucking company")
        assert t is not None
        req_names = [r.field_name for r in t.required_fields]
        assert "driver_information" in req_names
        assert "fleet_radius" in req_names
        assert "cargo_types" in req_names

    def test_restaurant_template(self):
        t = get_submission_template("restaurant")
        assert t is not None
        req_names = [r.field_name for r in t.required_fields]
        assert "cooking_exposure" in req_names
        assert "liquor_exposure" in req_names

    def test_unknown_industry_returns_none(self):
        assert get_submission_template("underwater basket weaving") is None

    def test_list_templates(self):
        templates = list_submission_templates()
        assert "roofing contractor" in templates
        assert "restaurant" in templates
        assert "trucking company" in templates

    def test_all_templates_have_required_fields(self):
        for key, t in INDUSTRY_SUBMISSION_TEMPLATES.items():
            assert len(t.required_fields) > 0, f"{key} has no required fields"

    def test_all_templates_have_common_fields(self):
        common = {"legal_entity_name", "operations_description", "annual_revenue", "payroll", "loss_runs"}
        for key, t in INDUSTRY_SUBMISSION_TEMPLATES.items():
            field_names = {r.field_name for r in t.required_fields}
            for c in common:
                assert c in field_names, f"{key} missing common field {c}"

    def test_to_dict(self):
        t = get_submission_template("roofing contractor")
        d = t.to_dict()
        assert d["industry"] == "roofing contractor"
        assert isinstance(d["required_fields"], list)
        assert isinstance(d["required_fields"][0], dict)

    def test_requirement_to_dict(self):
        r = SubmissionRequirement(
            field_name="test", label="Test", importance="high",
        )
        d = r.to_dict()
        assert d["field_name"] == "test"
        assert d["importance"] == "high"


# ============================================================
# HELPERS
# ============================================================


class TestNormalizeInput:
    def test_lowercase_keys(self):
        result = normalize_submission_input({"Legal_Entity_Name": "Foo"})
        assert "legal_entity_name" in result

    def test_replace_hyphens(self):
        result = normalize_submission_input({"fall-protection-program": True})
        assert "fall_protection_program" in result

    def test_replace_spaces(self):
        result = normalize_submission_input({"fall protection program": True})
        assert "fall_protection_program" in result

    def test_strip_whitespace(self):
        result = normalize_submission_input({"  payroll  ": 500000})
        assert "payroll" in result


class TestIsWeakField:
    def test_none_is_weak(self):
        assert is_weak_field("any_field", None) is True

    def test_empty_string_is_weak(self):
        assert is_weak_field("any_field", "") is True

    def test_unknown_is_weak(self):
        assert is_weak_field("loss_runs", "unknown") is True

    def test_tbd_is_weak(self):
        assert is_weak_field("any_field", "TBD") is True

    def test_na_is_weak(self):
        assert is_weak_field("any_field", "N/A") is True

    def test_short_operations_description(self):
        assert is_weak_field("operations_description", "roofing") is True

    def test_adequate_operations_description(self):
        assert is_weak_field("operations_description", "Commercial roofing installation and repair") is False

    def test_zero_revenue_is_weak(self):
        assert is_weak_field("annual_revenue", 0) is True

    def test_nonzero_revenue_is_strong(self):
        assert is_weak_field("annual_revenue", 500000) is False

    def test_false_safety_program_is_weak(self):
        assert is_weak_field("safety_program", False) is True

    def test_true_safety_program_is_strong(self):
        assert is_weak_field("safety_program", True) is False

    def test_false_fall_protection_is_weak(self):
        assert is_weak_field("fall_protection_program", False) is True

    def test_normal_string_not_weak(self):
        assert is_weak_field("legal_entity_name", "ABC Roofing LLC") is False


class TestBuildExplanation:
    def test_strong_submission(self):
        text = build_readiness_explanation(92, "strong", [], [], [], "roofing contractor")
        assert "92/100" in text
        assert "strong" in text

    def test_missing_critical(self):
        text = build_readiness_explanation(55, "fair", ["Payroll", "Loss Runs"], [], [], "roofing contractor")
        assert "critical" in text.lower() or "missing" in text.lower()
        assert "Payroll" in text

    def test_weak_fields_mentioned(self):
        text = build_readiness_explanation(70, "good", [], [], ["Operations Description"], "restaurant")
        assert "strengthening" in text


# ============================================================
# ROOFING EVALUATIONS
# ============================================================


class TestRoofingStrong:
    """Strong roofing submission with most fields provided."""

    def setup_method(self):
        self.result = evaluate_submission_readiness(
            industry="roofing contractor",
            submission_data={
                "legal_entity_name": "Summit Ridge Roofing LLC",
                "operations_description": "Commercial and residential roof installation and repair across central North Carolina",
                "years_in_business": 12,
                "annual_revenue": 4200000,
                "payroll": 1200000,
                "employee_count": 38,
                "subcontractor_usage": "yes, approximately 30% of labor, certificates tracked",
                "loss_runs": "provided, 5-year history",
                "current_coverages": "GL $1M/$2M, WC statutory, Auto $1M",
                "requested_coverages": "GL, WC, Auto, Umbrella",
                "vehicle_count": 12,
                "fall_protection_program": True,
                "safety_program": True,
                "roof_types": "shingle, flat, TPO",
                "max_height": "4 stories",
                "tool_equipment_values": 185000,
            },
            jurisdiction="NC",
        )

    def test_high_score(self):
        assert self.result["readiness_score"] >= 80

    def test_strong_level(self):
        assert self.result["readiness_level"] == "strong"

    def test_no_critical_missing(self):
        assert len(self.result["missing_critical_fields"]) == 0

    def test_has_strengths(self):
        assert len(self.result["strengths"]) > 0

    def test_output_shape(self):
        expected_keys = {
            "industry", "jurisdiction", "readiness_score", "readiness_level",
            "missing_critical_fields", "missing_recommended_fields",
            "weak_fields", "strengths", "next_steps", "office_learnings",
            "explanation",
        }
        assert set(self.result.keys()) == expected_keys


class TestRoofingMissingCritical:
    """Roofing submission missing payroll and fall protection."""

    def setup_method(self):
        self.result = evaluate_submission_readiness(
            industry="roofing contractor",
            submission_data={
                "legal_entity_name": "Quick Roof Inc",
                "operations_description": "Residential re-roofing in the greater Raleigh area",
                "years_in_business": 3,
                "annual_revenue": 800000,
                "employee_count": 6,
                "loss_runs": "provided",
                "current_coverages": "GL $1M",
                "requested_coverages": "GL, WC",
                # missing: payroll, subcontractor_usage, fall_protection_program, vehicle_count
            },
        )

    def test_lower_score(self):
        assert self.result["readiness_score"] < 80

    def test_not_strong(self):
        assert self.result["readiness_level"] != "strong"

    def test_payroll_missing(self):
        assert "Total Payroll" in self.result["missing_critical_fields"]

    def test_fall_protection_missing(self):
        assert "Fall Protection Program" in self.result["missing_critical_fields"]

    def test_next_steps_include_critical(self):
        steps_text = " ".join(self.result["next_steps"])
        assert "critical" in steps_text.lower()


# ============================================================
# RESTAURANT EVALUATION
# ============================================================


class TestRestaurantMissingDelivery:
    """Restaurant decent but missing delivery exposure info."""

    def setup_method(self):
        self.result = evaluate_submission_readiness(
            industry="restaurant",
            submission_data={
                "legal_entity_name": "Bella Cucina Restaurant",
                "operations_description": "Full-service Italian restaurant with bar, dinner service only, downtown location",
                "years_in_business": 7,
                "annual_revenue": 1500000,
                "payroll": 420000,
                "employee_count": 22,
                "loss_runs": "provided, 5-year clean history",
                "current_coverages": "GL, Property, WC, Liquor",
                "requested_coverages": "GL, Property, WC, Liquor, Umbrella",
                "cooking_exposure": "deep frying, gas grill, Ansul system installed",
                "building_ownership": "leased, 3800 sq ft",
                "liquor_exposure": "full bar, 30% of revenue",
                # missing: delivery_exposure (recommended, not critical)
            },
        )

    def test_good_or_strong(self):
        assert self.result["readiness_level"] in ("good", "strong")

    def test_no_critical_missing(self):
        assert len(self.result["missing_critical_fields"]) == 0

    def test_delivery_in_recommended(self):
        assert "Delivery Exposure" in self.result["missing_recommended_fields"]

    def test_cooking_is_strength(self):
        assert any("Cooking" in s for s in self.result["strengths"])


# ============================================================
# TRUCKING EVALUATION
# ============================================================


class TestTruckingMissingDriverInfo:
    """Trucking submission missing driver info and garaging."""

    def setup_method(self):
        self.result = evaluate_submission_readiness(
            industry="trucking company",
            submission_data={
                "legal_entity_name": "FastFreight Logistics LLC",
                "operations_description": "Regional freight hauling, general commodities, primarily southeastern US",
                "years_in_business": 10,
                "annual_revenue": 6000000,
                "payroll": 2200000,
                "employee_count": 30,
                "loss_runs": "provided",
                "current_coverages": "GL, Auto, Cargo, WC",
                "requested_coverages": "GL, Auto, Cargo, WC, Umbrella",
                "vehicle_count": 18,
                "fleet_radius": "regional, 600-mile radius",
                "cargo_types": "general freight, max load $120,000",
                # missing: driver_information, garaging_address, mvr_review_process
            },
        )

    def test_not_strong(self):
        assert self.result["readiness_level"] != "strong"

    def test_driver_info_missing(self):
        assert "Driver Information" in self.result["missing_critical_fields"]

    def test_garaging_missing(self):
        # garaging_address is high importance — shows up in next_steps
        steps_text = " ".join(self.result["next_steps"])
        assert "Garaging" in steps_text

    def test_fleet_radius_is_strength(self):
        assert any("Fleet" in s for s in self.result["strengths"])

    def test_has_next_steps(self):
        assert len(self.result["next_steps"]) > 0


# ============================================================
# WEAK FIELD DETECTION IN EVALUATION
# ============================================================


class TestWeakFieldInEvaluation:
    """Thin operations description triggers weak field detection."""

    def setup_method(self):
        self.result = evaluate_submission_readiness(
            industry="roofing contractor",
            submission_data={
                "legal_entity_name": "ABC Roofing",
                "operations_description": "roofing",  # too short
                "years_in_business": 5,
                "annual_revenue": 1000000,
                "payroll": 400000,
                "employee_count": 8,
                "subcontractor_usage": "no",
                "loss_runs": "provided",
                "current_coverages": "GL, WC",
                "requested_coverages": "GL, WC",
                "vehicle_count": 3,
                "fall_protection_program": True,
                "safety_program": True,
            },
        )

    def test_operations_is_weak(self):
        assert "Operations Description" in self.result["weak_fields"]

    def test_score_reduced(self):
        # Should be reduced but not catastrophically
        assert self.result["readiness_score"] < 100


# ============================================================
# SCORE CLAMPING
# ============================================================


class TestScoreClamping:
    def test_score_never_negative(self):
        """Empty submission should clamp at 0."""
        result = evaluate_submission_readiness(
            industry="trucking company",
            submission_data={},
        )
        assert result["readiness_score"] >= 0

    def test_score_never_above_100(self):
        """Even a perfect submission can't exceed 100."""
        result = evaluate_submission_readiness(
            industry="restaurant",
            submission_data={
                "legal_entity_name": "Perfect Restaurant",
                "operations_description": "Full-service dining establishment with comprehensive safety program and detailed records",
                "years_in_business": 20,
                "annual_revenue": 3000000,
                "payroll": 800000,
                "employee_count": 40,
                "loss_runs": "provided, 5-year spotless history",
                "current_coverages": "Full commercial package",
                "requested_coverages": "GL, Property, WC, Liquor, Umbrella",
                "cooking_exposure": "full commercial kitchen, Ansul system, grease traps maintained",
                "building_ownership": "owned, 5000 sq ft",
                "liquor_exposure": "full bar, 20% of revenue",
                "delivery_exposure": "no delivery",
                "safety_program": True,
                "hours_of_operation": "Mon-Sun 11am-11pm",
                "seating_capacity": "120 indoor, 40 patio",
                "prior_carrier": "Travelers",
                "reason_for_change": "seeking broader coverage",
                "effective_date": "2026-07-01",
            },
        )
        assert result["readiness_score"] <= 100
        assert result["readiness_level"] == "strong"

    def test_empty_submission_is_poor(self):
        result = evaluate_submission_readiness(
            industry="roofing contractor",
            submission_data={},
        )
        assert result["readiness_level"] == "poor"


# ============================================================
# OFFICE LEARNINGS
# ============================================================


class TestOfficeLearnings:
    def test_no_learnings_without_office_id(self):
        result = evaluate_submission_readiness(
            industry="roofing contractor",
            submission_data={"legal_entity_name": "Test"},
        )
        assert result["office_learnings"] == []

    def test_learnings_appear_with_office_id(self):
        from app.services.learning_store import (
            OFFICE_LEARNINGS, add_office_learning,
        )
        # Clear and add a test learning
        OFFICE_LEARNINGS.clear()
        add_office_learning("test-office", "roofing contractor", "Always check sub certs")

        result = evaluate_submission_readiness(
            industry="roofing contractor",
            submission_data={"legal_entity_name": "Test"},
            office_id="test-office",
        )
        assert len(result["office_learnings"]) == 1
        assert "sub certs" in result["office_learnings"][0]

        # Clean up
        OFFICE_LEARNINGS.clear()


# ============================================================
# UNKNOWN INDUSTRY
# ============================================================


class TestUnknownIndustry:
    def test_unknown_returns_zero(self):
        result = evaluate_submission_readiness(
            industry="alien technology",
            submission_data={"legal_entity_name": "Area 51 Corp"},
        )
        assert result["readiness_score"] == 0
        assert result["readiness_level"] == "poor"
        assert "No submission template" in result["explanation"]


# ============================================================
# API ENDPOINTS
# ============================================================


class TestSubmissionEndpoint:
    def test_post_readiness(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "industry": "roofing contractor",
            "jurisdiction": "NC",
            "submission_data": {
                "legal_entity_name": "Test Roofing LLC",
                "operations_description": "Residential and commercial roofing installation and repair",
                "years_in_business": 8,
                "annual_revenue": 2000000,
                "payroll": 700000,
                "employee_count": 12,
                "loss_runs": "provided",
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "readiness_score" in data
        assert "readiness_level" in data
        assert "missing_critical_fields" in data
        assert "explanation" in data

    def test_missing_industry_returns_422(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "submission_data": {"legal_entity_name": "Test"},
        })
        assert resp.status_code == 422

    def test_empty_submission_data(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "industry": "restaurant",
            "submission_data": {},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_level"] == "poor"


class TestDemoExampleEndpoints:
    def test_list_examples(self):
        resp = client.get("/api/v1/submission/demo-examples")
        assert resp.status_code == 200
        data = resp.json()
        assert "demo-roofing-nc-strong" in data["examples"]
        assert "demo-landscaping-tx-fair" in data["examples"]
        assert "demo-restaurant-ca-poor" in data["examples"]

    def test_get_example(self):
        resp = client.get("/api/v1/submission/demo-examples/demo-roofing-nc-strong")
        assert resp.status_code == 200
        data = resp.json()
        assert data["industry"] == "roofing contractor"
        assert "submission_data" in data

    def test_get_unknown_example(self):
        resp = client.get("/api/v1/submission/demo-examples/nonexistent")
        assert resp.status_code == 404

    def test_evaluate_strong_demo(self):
        resp = client.post("/api/v1/submission/demo-evaluate/demo-roofing-nc-strong")
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_level"] == "strong"

    def test_evaluate_fair_demo(self):
        resp = client.post("/api/v1/submission/demo-evaluate/demo-landscaping-tx-fair")
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_level"] in ("fair", "poor")

    def test_evaluate_poor_demo(self):
        resp = client.post("/api/v1/submission/demo-evaluate/demo-restaurant-ca-poor")
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_level"] == "poor"

    def test_evaluate_unknown_example(self):
        resp = client.post("/api/v1/submission/demo-evaluate/nonexistent")
        assert resp.status_code == 404


# ============================================================
# REGRESSIONS
# ============================================================


class TestRegressions:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12

    def test_existing_coverage_gaps_unchanged(self):
        from app.services.coverage_gap_detector import detect_knowledge_gaps
        result = detect_knowledge_gaps("roofing contractor", ["general liability"])
        assert "missing_coverages" in result

    def test_meeting_brief_unchanged(self):
        from app.services.meeting_brief import generate_meeting_brief
        result = generate_meeting_brief("roofing contractor")
        assert "top_exposures" in result
