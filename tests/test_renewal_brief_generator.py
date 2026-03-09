"""Tests for Renewal Risk Brief Generator — unit tests, integration tests, and API tests."""

import pytest

from app.services.renewal_brief_generator import generate_renewal_brief
from app.services.renewal_brief_renderer import render_renewal_brief_text


# ============================================================
# EXPECTED RESPONSE STRUCTURE
# ============================================================

REQUIRED_KEYS = {
    "account_summary",
    "risk_overview",
    "underwriter_concerns",
    "coverage_gaps",
    "loss_patterns",
    "mod_trends",
    "producer_questions",
    "defense_strategy",
    "peer_insights",
    "recommended_actions",
}

ACCOUNT_SUMMARY_KEYS = {"account_name", "industry", "state", "account_stage", "key_facts"}
RISK_OVERVIEW_KEYS = {"risk_level", "confidence", "headline", "contributing_factors", "signal_count"}


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def minimal_profile():
    return {"industry": "roofing", "state": "TX"}


@pytest.fixture
def full_profile():
    return {
        "account_name": "Apex Roofing",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 27,
        "annual_revenue": 4_800_000,
        "vehicle_count": 9,
        "uses_subcontractors": True,
        "current_coverages": ["general_liability", "workers_comp", "commercial_auto"],
        "experience_mod": 1.21,
        "account_stage": "renewal",
        "claims_summary": "3 WC claims in past 24 months",
        "notes": "",
        "loss_run_data": {
            "summary": {"total_claims": 5, "open_claims": 1, "total_incurred": 120_000},
            "patterns": [
                "Repeated fall-related WC claims",
                "Open claim severity remains a renewal concern",
            ],
            "underwriting_flags": [
                "3 WC claims in 24 months signals frequency issue",
                "1 open claim with reserves still active",
            ],
            "producer_talking_points": [
                "Ask about fall protection and return-to-work programs",
                "Get status on the open claim before submission",
            ],
        },
        "experience_mod_data": {
            "current_mod": 1.21,
            "prior_mod": 1.08,
            "mod_trend": {
                "current": 1.21,
                "prior": 1.08,
                "change": 0.13,
                "direction": "worsening",
            },
            "flags": [
                "Mod increased from 1.08 to 1.21 (+0.13) — claims are driving costs up",
                "Mod at 1.21 — above unity, room for improvement",
            ],
            "insights": [],
            "talking_points": [
                "The mod is at 1.21 — open by acknowledging you've reviewed the worksheet.",
                "Mod moved up (1.08 → 1.21). Be prepared to explain why.",
            ],
        },
    }


@pytest.fixture
def loss_run_only_profile():
    return {
        "industry": "trucking",
        "state": "OH",
        "employee_count": 15,
        "current_coverages": ["general_liability", "commercial_auto"],
        "loss_run_data": {
            "summary": {"total_claims": 3, "open_claims": 0, "total_incurred": 45_000},
            "patterns": ["Vehicle-related claims dominate"],
            "underwriting_flags": ["Auto frequency noted"],
            "producer_talking_points": ["Review fleet management controls"],
        },
    }


@pytest.fixture
def mod_only_profile():
    return {
        "industry": "manufacturing",
        "state": "PA",
        "employee_count": 50,
        "current_coverages": ["general_liability", "workers_comp"],
        "experience_mod_data": {
            "current_mod": 0.82,
            "prior_mod": 0.90,
            "mod_trend": {
                "current": 0.82,
                "prior": 0.90,
                "change": -0.08,
                "direction": "improving",
            },
            "flags": [],
            "insights": ["Mod at 0.82 — well below unity, strong safety record"],
            "talking_points": ["Mod at 0.82 is a strength."],
        },
    }


# ============================================================
# STRUCTURE TESTS
# ============================================================


class TestResponseStructure:
    """Verify the brief response has all required sections."""

    def test_all_top_level_keys_present(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert set(result.keys()) == REQUIRED_KEYS

    def test_account_summary_keys(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert set(result["account_summary"].keys()) == ACCOUNT_SUMMARY_KEYS

    def test_risk_overview_keys(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert set(result["risk_overview"].keys()) == RISK_OVERVIEW_KEYS

    def test_risk_level_valid(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert result["risk_overview"]["risk_level"] in ("low", "moderate", "high")

    def test_confidence_in_range(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert 0.0 <= result["risk_overview"]["confidence"] <= 1.0

    def test_all_list_sections_are_lists(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        for key in [
            "underwriter_concerns", "coverage_gaps", "loss_patterns",
            "mod_trends", "producer_questions", "defense_strategy",
            "peer_insights", "recommended_actions",
        ]:
            assert isinstance(result[key], list), f"{key} should be a list"


# ============================================================
# MINIMAL PROFILE TESTS
# ============================================================


class TestMinimalProfile:
    """Tests with minimal input — no loss run, no mod data."""

    def test_generates_without_crash(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert result["account_summary"]["industry"] == "roofing"

    def test_no_loss_patterns(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert result["loss_patterns"] == []

    def test_no_mod_trends(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert result["mod_trends"] == []

    def test_coverage_gaps_still_generated(self, minimal_profile):
        """Even minimal profiles should detect coverage gaps from industry defaults."""
        result = generate_renewal_brief(minimal_profile)
        assert len(result["coverage_gaps"]) >= 1

    def test_producer_questions_generated(self, minimal_profile):
        result = generate_renewal_brief(minimal_profile)
        assert len(result["producer_questions"]) >= 1

    def test_peer_insights_generated(self, minimal_profile):
        """Peer insights fall back to seeded intelligence."""
        result = generate_renewal_brief(minimal_profile)
        assert len(result["peer_insights"]) >= 1

    def test_default_account_name(self):
        result = generate_renewal_brief({"industry": "roofing"})
        assert result["account_summary"]["account_name"] == "Unnamed Account"


# ============================================================
# FULL PROFILE TESTS
# ============================================================


class TestFullProfile:
    """Tests with complete profile including loss run and mod data."""

    def test_account_summary_populated(self, full_profile):
        result = generate_renewal_brief(full_profile)
        summary = result["account_summary"]
        assert summary["account_name"] == "Apex Roofing"
        assert summary["state"] == "NC"
        assert len(summary["key_facts"]) >= 3

    def test_key_facts_include_employees(self, full_profile):
        result = generate_renewal_brief(full_profile)
        facts = result["account_summary"]["key_facts"]
        assert any("27 employees" in f for f in facts)

    def test_key_facts_include_vehicles(self, full_profile):
        result = generate_renewal_brief(full_profile)
        facts = result["account_summary"]["key_facts"]
        assert any("9 vehicles" in f for f in facts)

    def test_key_facts_include_subcontractors(self, full_profile):
        result = generate_renewal_brief(full_profile)
        facts = result["account_summary"]["key_facts"]
        assert any("subcontractor" in f.lower() for f in facts)

    def test_risk_level_high_with_bad_mod_and_losses(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert result["risk_overview"]["risk_level"] == "high"

    def test_headline_mentions_reasons(self, full_profile):
        result = generate_renewal_brief(full_profile)
        headline = result["risk_overview"]["headline"]
        assert len(headline) > 20

    def test_underwriter_concerns_populated(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["underwriter_concerns"]) >= 2

    def test_loss_patterns_from_loss_run(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["loss_patterns"]) >= 1
        assert any("fall" in p.lower() for p in result["loss_patterns"])

    def test_mod_trends_from_mod_data(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["mod_trends"]) >= 1
        assert any("1.08" in t and "1.21" in t for t in result["mod_trends"])

    def test_coverage_gaps_present(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["coverage_gaps"]) >= 1

    def test_coverage_gaps_have_applied_rules(self, full_profile):
        result = generate_renewal_brief(full_profile)
        gaps_with_rules = [g for g in result["coverage_gaps"] if g.get("applied_rules")]
        assert len(gaps_with_rules) >= 1

    def test_defense_strategy_populated(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["defense_strategy"]) >= 2

    def test_defense_includes_mod_strategy(self, full_profile):
        result = generate_renewal_brief(full_profile)
        strategies = result["defense_strategy"]
        assert any("mod" in s.lower() or "loss control" in s.lower() for s in strategies)

    def test_defense_includes_subcontractor_strategy(self, full_profile):
        result = generate_renewal_brief(full_profile)
        strategies = result["defense_strategy"]
        assert any("subcontract" in s.lower() for s in strategies)

    def test_recommended_actions_populated(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["recommended_actions"]) >= 2

    def test_sections_capped(self, full_profile):
        result = generate_renewal_brief(full_profile)
        assert len(result["underwriter_concerns"]) <= 7
        assert len(result["coverage_gaps"]) <= 5
        assert len(result["loss_patterns"]) <= 5
        assert len(result["mod_trends"]) <= 5
        assert len(result["producer_questions"]) <= 7
        assert len(result["defense_strategy"]) <= 5
        assert len(result["peer_insights"]) <= 5
        assert len(result["recommended_actions"]) <= 5


# ============================================================
# PARTIAL DATA TESTS
# ============================================================


class TestPartialData:
    """Tests with loss run only or mod data only."""

    def test_loss_run_only_has_patterns(self, loss_run_only_profile):
        result = generate_renewal_brief(loss_run_only_profile)
        assert len(result["loss_patterns"]) >= 1
        assert result["mod_trends"] == []

    def test_loss_run_only_has_recommended_actions(self, loss_run_only_profile):
        result = generate_renewal_brief(loss_run_only_profile)
        assert any("narrative" in a.lower() or "loss" in a.lower() for a in result["recommended_actions"])

    def test_mod_only_has_trends(self, mod_only_profile):
        result = generate_renewal_brief(mod_only_profile)
        assert len(result["mod_trends"]) >= 1
        assert result["loss_patterns"] == []

    def test_improving_mod_lower_risk(self, mod_only_profile):
        result = generate_renewal_brief(mod_only_profile)
        # Low mod + improving trend should not be high risk
        assert result["risk_overview"]["risk_level"] != "high"


# ============================================================
# RISK OVERVIEW LOGIC TESTS
# ============================================================


class TestRiskOverview:
    """Tests for risk level computation."""

    def test_empty_profile_low_to_moderate(self):
        result = generate_renewal_brief({"industry": "consulting"})
        assert result["risk_overview"]["risk_level"] in ("low", "moderate")

    def test_high_risk_with_high_mod(self):
        profile = {
            "industry": "roofing",
            "state": "TX",
            "experience_mod": 1.30,
            "current_coverages": [],
            "experience_mod_data": {
                "mod_trend": {"direction": "worsening", "current": 1.30, "prior": 1.10, "change": 0.20},
                "flags": ["Mod at 1.30 — significantly above unity"],
                "insights": [],
                "talking_points": [],
            },
        }
        result = generate_renewal_brief(profile)
        assert result["risk_overview"]["risk_level"] == "high"

    def test_confidence_higher_with_more_data(self, full_profile, minimal_profile):
        full_result = generate_renewal_brief(full_profile)
        minimal_result = generate_renewal_brief(minimal_profile)
        assert full_result["risk_overview"]["confidence"] >= minimal_result["risk_overview"]["confidence"]


# ============================================================
# GRACEFUL DEGRADATION TESTS
# ============================================================


class TestGracefulDegradation:
    """Verify brief handles missing/empty/None data without crashing."""

    def test_empty_profile(self):
        result = generate_renewal_brief({})
        assert set(result.keys()) == REQUIRED_KEYS

    def test_none_loss_run_data(self):
        result = generate_renewal_brief({"industry": "roofing", "loss_run_data": None})
        assert result["loss_patterns"] == []

    def test_none_experience_mod_data(self):
        result = generate_renewal_brief({"industry": "roofing", "experience_mod_data": None})
        assert result["mod_trends"] == []

    def test_empty_loss_run_data(self):
        result = generate_renewal_brief({
            "industry": "roofing",
            "loss_run_data": {"patterns": [], "underwriting_flags": [], "producer_talking_points": []},
        })
        assert result["loss_patterns"] == []

    def test_empty_experience_mod_data(self):
        result = generate_renewal_brief({
            "industry": "roofing",
            "experience_mod_data": {"flags": [], "insights": [], "talking_points": [], "mod_trend": None},
        })
        assert result["mod_trends"] == []

    def test_unknown_industry(self):
        result = generate_renewal_brief({"industry": "underwater basket weaving"})
        assert result["account_summary"]["industry"] == "underwater basket weaving"
        assert len(result["producer_questions"]) >= 1

    def test_invalid_account_stage(self):
        result = generate_renewal_brief({"industry": "roofing", "account_stage": "invalid_stage"})
        # Brief records what was given; downstream services handle their own validation
        assert set(result.keys()) == REQUIRED_KEYS
        assert len(result["producer_questions"]) >= 1


# ============================================================
# RENDERER TESTS
# ============================================================


class TestRenderer:
    """Tests for the optional text renderer."""

    def test_renderer_produces_string(self, full_profile):
        brief = generate_renewal_brief(full_profile)
        text = render_renewal_brief_text(brief)
        assert isinstance(text, str)
        assert len(text) > 100

    def test_renderer_includes_account_name(self, full_profile):
        brief = generate_renewal_brief(full_profile)
        text = render_renewal_brief_text(brief)
        assert "APEX ROOFING" in text

    def test_renderer_includes_risk_level(self, full_profile):
        brief = generate_renewal_brief(full_profile)
        text = render_renewal_brief_text(brief)
        assert "RISK LEVEL:" in text

    def test_renderer_includes_sections(self, full_profile):
        brief = generate_renewal_brief(full_profile)
        text = render_renewal_brief_text(brief)
        assert "UNDERWRITER CONCERNS" in text
        assert "PRODUCER QUESTIONS" in text
        assert "DEFENSE STRATEGY" in text
        assert "RECOMMENDED ACTIONS" in text

    def test_renderer_handles_minimal(self, minimal_profile):
        brief = generate_renewal_brief(minimal_profile)
        text = render_renewal_brief_text(brief)
        assert "WAYOS PREP" in text


# ============================================================
# API ENDPOINT TESTS
# ============================================================


class TestAPIEndpoint:
    """Tests for the /brief/renewal endpoint via TestClient."""

    @pytest.fixture
    def client(self):
        from unittest.mock import MagicMock
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.session import get_db

        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_endpoint_returns_200(self, client):
        response = client.post("/api/v1/brief/renewal", json={
            "industry": "roofing",
            "state": "TX",
        })
        assert response.status_code == 200

    def test_endpoint_returns_valid_structure(self, client):
        response = client.post("/api/v1/brief/renewal", json={
            "account_name": "Test Account",
            "industry": "trucking",
            "state": "OH",
            "employee_count": 20,
        })
        data = response.json()
        assert set(data.keys()) == REQUIRED_KEYS
        assert data["account_summary"]["account_name"] == "Test Account"

    def test_endpoint_with_full_payload(self, client, full_profile):
        response = client.post("/api/v1/brief/renewal", json=full_profile)
        assert response.status_code == 200
        data = response.json()
        assert data["account_summary"]["account_name"] == "Apex Roofing"
        assert len(data["coverage_gaps"]) >= 1

    def test_endpoint_empty_body(self, client):
        response = client.post("/api/v1/brief/renewal", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["account_summary"]["account_name"] == "Unnamed Account"
