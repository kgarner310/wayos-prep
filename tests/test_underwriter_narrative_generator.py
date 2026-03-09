"""Tests for Underwriter Narrative Generator."""

import pytest

from app.services.underwriter_narrative_generator import generate_underwriter_narrative


# ============================================================
# FIXTURES
# ============================================================

REQUIRED_KEYS = {
    "account_name", "narrative_type", "email_version", "memo_version",
    "supporting_points", "fact_sources", "source_signals", "cautions", "style_applied",
}


@pytest.fixture
def minimal_profile():
    return {"industry": "roofing", "state": "TX"}


@pytest.fixture
def renewal_profile():
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
        "narrative_type": "renewal",
        "loss_run_data": {
            "summary": {"total_claims": 5, "open_claims": 1, "total_incurred": 120_000},
            "patterns": ["Repeated fall-related WC claims"],
            "underwriting_flags": ["3 WC claims in 24 months"],
            "producer_talking_points": ["Ask about fall protection"],
        },
        "experience_mod_data": {
            "mod_trend": {"current": 1.21, "prior": 1.08, "change": 0.13, "direction": "worsening"},
            "flags": ["Mod increased from 1.08 to 1.21 (+0.13) — claims are driving costs up"],
            "insights": [],
            "talking_points": ["The mod is at 1.21."],
        },
    }


@pytest.fixture
def new_business_profile():
    return {
        "account_name": "Metro Trucking",
        "industry": "trucking",
        "state": "OH",
        "employee_count": 30,
        "vehicle_count": 15,
        "current_coverages": ["general_liability", "commercial_auto"],
        "narrative_type": "new_business",
        "account_stage": "prospect",
    }


@pytest.fixture
def profile_with_intel():
    return {
        "account_name": "Apex Roofing",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 27,
        "narrative_type": "renewal",
        "current_coverages": ["general_liability", "workers_comp"],
        "public_web_intel": {
            "company_identity": {"company_name": "Apex Roofing", "founded_year": 2012},
            "operations_signals": [
                "Residential roof replacement/repair/installation services",
                "Storm restoration work",
            ],
            "safety_signals": [
                "References OSHA compliance or procedures",
                "Fall protection measures referenced",
            ],
            "scale_signals": ["Multi-crew/location operations"],
            "carrier_relevant_signals": ["Manufacturer certifications/authorizations"],
            "observed_public_signals": ["Recent project activity posted"],
            "cautions": [
                "Public content may reflect marketing language and should not be treated as independently verified fact"
            ],
        },
    }


@pytest.fixture
def profile_with_brief():
    return {
        "account_name": "Apex Roofing",
        "industry": "roofing",
        "state": "NC",
        "narrative_type": "renewal",
        "renewal_brief": {
            "account_summary": {
                "account_name": "Apex Roofing",
                "industry": "roofing",
                "state": "NC",
                "account_stage": "renewal",
                "key_facts": ["27 employees", "9 vehicles", "Uses subcontractors"],
            },
            "risk_overview": {
                "risk_level": "high",
                "confidence": 0.85,
                "headline": "Elevated renewal attention recommended.",
            },
            "underwriter_concerns": ["Mod increased from 1.08 to 1.21"],
            "coverage_gaps": [
                {"coverage": "Umbrella", "reason": "Excess liability needed", "risk_level": "high", "confidence": 0.85, "applied_rules": []},
            ],
            "loss_patterns": ["Repeated fall-related WC claims"],
            "mod_trends": ["Experience mod increased from 1.08 to 1.21"],
            "producer_questions": ["Ask about fall protection"],
            "defense_strategy": ["Prepare explanation for upward mod trend"],
            "peer_insights": ["Producers working similar risks frequently ask about subcontractors"],
            "recommended_actions": ["Review umbrella exposure"],
        },
    }


# ============================================================
# STRUCTURE TESTS
# ============================================================


class TestResponseStructure:

    def test_all_keys_present(self, minimal_profile):
        result = generate_underwriter_narrative(minimal_profile)
        assert set(result.keys()) == REQUIRED_KEYS

    def test_email_version_has_body(self, minimal_profile):
        result = generate_underwriter_narrative(minimal_profile)
        assert "body" in result["email_version"]
        assert len(result["email_version"]["body"]) > 20

    def test_memo_version_has_body(self, minimal_profile):
        result = generate_underwriter_narrative(minimal_profile)
        assert "body" in result["memo_version"]
        assert len(result["memo_version"]["body"]) > 20

    def test_fact_sources_structure(self, minimal_profile):
        result = generate_underwriter_narrative(minimal_profile)
        fs = result["fact_sources"]
        assert "account_profile_used" in fs
        assert "renewal_brief_used" in fs
        assert "public_web_intel_used" in fs


# ============================================================
# RENEWAL NARRATIVE TESTS
# ============================================================


class TestRenewalNarrative:

    def test_narrative_type_renewal(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert result["narrative_type"] == "renewal"

    def test_email_subject(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert "Apex Roofing" in result["email_version"]["subject"]
        assert "Renewal" in result["email_version"]["subject"]

    def test_email_body_mentions_account(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert "Apex Roofing" in result["email_version"]["body"]

    def test_memo_title(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert "Apex Roofing" in result["memo_version"]["title"]

    def test_memo_has_sections(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        body = result["memo_version"]["body"]
        assert "ACCOUNT OVERVIEW" in body
        assert "RISK ASSESSMENT" in body

    def test_supporting_points_populated(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert len(result["supporting_points"]) >= 1

    def test_fact_sources_profile_and_brief(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert result["fact_sources"]["account_profile_used"] is True
        assert result["fact_sources"]["renewal_brief_used"] is True


# ============================================================
# NEW BUSINESS NARRATIVE TESTS
# ============================================================


class TestNewBusinessNarrative:

    def test_narrative_type_new_business(self, new_business_profile):
        result = generate_underwriter_narrative(new_business_profile)
        assert result["narrative_type"] == "new_business"

    def test_email_subject_new_business(self, new_business_profile):
        result = generate_underwriter_narrative(new_business_profile)
        assert "New Business" in result["email_version"]["subject"]
        assert "Metro Trucking" in result["email_version"]["subject"]

    def test_memo_title_new_business(self, new_business_profile):
        result = generate_underwriter_narrative(new_business_profile)
        assert "New Business" in result["memo_version"]["title"]

    def test_email_body_has_content(self, new_business_profile):
        result = generate_underwriter_narrative(new_business_profile)
        assert len(result["email_version"]["body"]) > 50

    def test_memo_body_has_content(self, new_business_profile):
        result = generate_underwriter_narrative(new_business_profile)
        assert len(result["memo_version"]["body"]) > 50


# ============================================================
# PUBLIC INTEL INTEGRATION TESTS
# ============================================================


class TestPublicIntelIntegration:

    def test_intel_signals_in_memo(self, profile_with_intel):
        result = generate_underwriter_narrative(profile_with_intel)
        body = result["memo_version"]["body"]
        # Public intel ops signals should appear in memo
        assert "public" in body.lower() or "PUBLIC" in body

    def test_safety_signals_in_email(self, profile_with_intel):
        result = generate_underwriter_narrative(profile_with_intel)
        body = result["email_version"]["body"]
        assert "public-facing" in body.lower() or "osha" in body.lower()

    def test_fact_sources_show_intel_used(self, profile_with_intel):
        result = generate_underwriter_narrative(profile_with_intel)
        assert result["fact_sources"]["public_web_intel_used"] is True

    def test_cautions_from_intel(self, profile_with_intel):
        result = generate_underwriter_narrative(profile_with_intel)
        assert len(result["cautions"]) >= 1
        assert any("marketing" in c.lower() or "verified" in c.lower() for c in result["cautions"])

    def test_no_intel_no_cautions_about_marketing(self, minimal_profile):
        result = generate_underwriter_narrative(minimal_profile)
        assert result["fact_sources"]["public_web_intel_used"] is False


# ============================================================
# PRE-SUPPLIED BRIEF TESTS
# ============================================================


class TestPreSuppliedBrief:

    def test_uses_supplied_brief(self, profile_with_brief):
        result = generate_underwriter_narrative(profile_with_brief)
        # Memo should use data from the supplied brief
        body = result["memo_version"]["body"]
        assert "Elevated renewal attention" in body or "RISK ASSESSMENT" in body

    def test_concerns_from_brief_in_memo(self, profile_with_brief):
        result = generate_underwriter_narrative(profile_with_brief)
        body = result["memo_version"]["body"]
        assert "1.08" in body or "1.21" in body


# ============================================================
# POSITIONING TESTS
# ============================================================


class TestPositioning:

    def test_defensive_positioning(self, renewal_profile):
        renewal_profile["intended_market_positioning"] = "defensive"
        result = generate_underwriter_narrative(renewal_profile)
        body = result["email_version"]["body"]
        assert "address" in body.lower() or "directly" in body.lower()

    def test_favorable_positioning_improving_mod(self):
        profile = {
            "account_name": "Safe Co",
            "industry": "manufacturing",
            "state": "PA",
            "narrative_type": "renewal",
            "intended_market_positioning": "favorable",
            "experience_mod_data": {
                "mod_trend": {"current": 0.82, "prior": 0.90, "change": -0.08, "direction": "improving"},
                "flags": [],
                "insights": ["Mod improved"],
                "talking_points": [],
            },
        }
        result = generate_underwriter_narrative(profile)
        body = result["email_version"]["body"]
        assert "positive" in body.lower() or "clean" in body.lower() or "improved" in body.lower()

    def test_invalid_positioning_defaults_to_standard(self, renewal_profile):
        renewal_profile["intended_market_positioning"] = "aggressive"
        result = generate_underwriter_narrative(renewal_profile)
        # Should not crash, produces valid output
        assert len(result["email_version"]["body"]) > 20


# ============================================================
# GRACEFUL DEGRADATION TESTS
# ============================================================


class TestGracefulDegradation:

    def test_empty_profile(self):
        result = generate_underwriter_narrative({})
        assert set(result.keys()) == REQUIRED_KEYS
        assert result["account_name"] == "Unnamed Account"

    def test_no_brief_no_intel(self, minimal_profile):
        result = generate_underwriter_narrative(minimal_profile)
        assert result["fact_sources"]["renewal_brief_used"] is True  # auto-generated
        assert result["fact_sources"]["public_web_intel_used"] is False

    def test_invalid_narrative_type(self, minimal_profile):
        minimal_profile["narrative_type"] = "invalid_type"
        result = generate_underwriter_narrative(minimal_profile)
        assert result["narrative_type"] == "renewal"  # defaults

    def test_supporting_points_capped(self, renewal_profile):
        result = generate_underwriter_narrative(renewal_profile)
        assert len(result["supporting_points"]) <= 7

    def test_unknown_industry(self):
        result = generate_underwriter_narrative({
            "industry": "underwater basket weaving",
            "narrative_type": "new_business",
        })
        assert len(result["email_version"]["body"]) > 20


# ============================================================
# API ENDPOINT TESTS
# ============================================================


class TestAPIEndpoint:

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
        response = client.post("/api/v1/narrative/underwriter", json={
            "industry": "roofing",
            "state": "TX",
            "narrative_type": "renewal",
        })
        assert response.status_code == 200

    def test_endpoint_valid_structure(self, client):
        response = client.post("/api/v1/narrative/underwriter", json={
            "account_name": "Test Account",
            "industry": "trucking",
            "state": "OH",
            "narrative_type": "new_business",
        })
        data = response.json()
        assert set(data.keys()) == REQUIRED_KEYS
        assert data["narrative_type"] == "new_business"

    def test_endpoint_empty_body(self, client):
        response = client.post("/api/v1/narrative/underwriter", json={})
        assert response.status_code == 200

    def test_endpoint_with_public_intel(self, client, profile_with_intel):
        response = client.post("/api/v1/narrative/underwriter", json=profile_with_intel)
        assert response.status_code == 200
        data = response.json()
        assert data["fact_sources"]["public_web_intel_used"] is True
