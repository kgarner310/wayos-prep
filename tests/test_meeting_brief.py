"""Tests for Meeting Brief Generator."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.services.meeting_brief import generate_meeting_brief


# ============================================================
# SERVICE LOGIC
# ============================================================


class TestGenerateMeetingBrief:

    def test_roofing_exposures(self):
        result = generate_meeting_brief("roofing")
        assert len(result["top_exposures"]) >= 3
        assert "fall from height" in result["top_exposures"]

    def test_roofing_claims(self):
        result = generate_meeting_brief("roofing")
        assert len(result["common_claims"]) >= 3

    def test_roofing_questions(self):
        result = generate_meeting_brief("roofing")
        assert len(result["discovery_questions"]) >= 3
        for q in result["discovery_questions"]:
            assert q.endswith("?")

    def test_roofing_coverage_watchouts(self):
        result = generate_meeting_brief("roofing")
        assert len(result["coverage_watchouts"]) >= 3
        assert "uninsured subcontractors" in result["coverage_watchouts"]

    def test_roofing_talking_points(self):
        result = generate_meeting_brief("roofing")
        assert len(result["recommended_talking_points"]) >= 3

    def test_restaurant_brief(self):
        result = generate_meeting_brief("restaurant")
        assert result["industry"] == "restaurant"
        assert len(result["top_exposures"]) >= 3
        assert any("slip" in e.lower() for e in result["top_exposures"])
        assert len(result["coverage_watchouts"]) >= 3

    def test_trucking_brief(self):
        result = generate_meeting_brief("trucking")
        assert result["industry"] == "trucking company"
        assert any("cargo" in c.lower() for c in result["common_claims"])

    def test_hvac_brief(self):
        result = generate_meeting_brief("hvac")
        assert result["industry"] == "hvac contractor"
        assert any("refrigerant" in e.lower() for e in result["top_exposures"])

    def test_unknown_industry(self):
        result = generate_meeting_brief("underwater basket weaving")
        assert "error" in result
        assert result["top_exposures"] == []
        assert result["confidence"] == 0.0

    def test_case_insensitive(self):
        result = generate_meeting_brief("ROOFING")
        assert result["industry"] == "roofing contractor"

    def test_output_structure(self):
        result = generate_meeting_brief("restaurant")
        assert "industry" in result
        assert "top_exposures" in result
        assert "common_claims" in result
        assert "recommended_talking_points" in result
        assert "discovery_questions" in result
        assert "coverage_watchouts" in result
        assert "policy_lines" in result
        assert "risk_score_factors" in result
        assert "data_sources" in result
        assert "confidence" in result
        assert "office_learnings" in result

    def test_policy_lines_included(self):
        result = generate_meeting_brief("roofing")
        assert "workers compensation" in result["policy_lines"]
        assert "umbrella" in result["policy_lines"]

    def test_risk_score_factors_included(self):
        result = generate_meeting_brief("roofing")
        assert len(result["risk_score_factors"]) >= 3
        assert "subcontractor_usage" in result["risk_score_factors"]

    def test_confidence_range(self):
        result = generate_meeting_brief("roofing")
        assert 0.0 < result["confidence"] <= 1.0

    def test_data_sources_included(self):
        result = generate_meeting_brief("roofing")
        assert len(result["data_sources"]) >= 2

    def test_bar_tavern(self):
        result = generate_meeting_brief("bar/tavern")
        assert result["industry"] == "bar/tavern"
        assert any("liquor" in e.lower() for e in result["top_exposures"])

    def test_daycare(self):
        result = generate_meeting_brief("daycare")
        assert any("child" in e.lower() for e in result["top_exposures"])

    def test_auto_repair(self):
        result = generate_meeting_brief("auto repair shop")
        assert any("garage" in e.lower() for e in result["top_exposures"])


# ============================================================
# API ENDPOINT
# ============================================================


class TestMeetingBriefEndpoint:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_get_brief_roofing(self, client):
        resp = client.get("/api/v1/meeting/brief?industry=roofing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["industry"] == "roofing contractor"
        assert len(data["top_exposures"]) >= 3
        assert len(data["discovery_questions"]) >= 3

    def test_get_brief_restaurant(self, client):
        resp = client.get("/api/v1/meeting/brief?industry=restaurant")
        assert resp.status_code == 200
        data = resp.json()
        assert data["industry"] == "restaurant"

    def test_get_brief_unknown(self, client):
        resp = client.get("/api/v1/meeting/brief?industry=unknown_xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_get_brief_empty(self, client):
        resp = client.get("/api/v1/meeting/brief?industry=")
        assert resp.status_code == 200

    def test_json_renderable(self, client):
        """Response should be clean JSON suitable for UI cards."""
        import json
        resp = client.get("/api/v1/meeting/brief?industry=roofing")
        data = resp.json()
        # Verify all values are JSON-serializable primitives/lists/dicts
        json_str = json.dumps(data)
        assert len(json_str) > 100
        # All list fields should contain strings
        for field in ["top_exposures", "common_claims", "discovery_questions",
                       "coverage_watchouts", "recommended_talking_points"]:
            assert all(isinstance(item, str) for item in data[field])


# ============================================================
# REGRESSIONS
# ============================================================


class TestMeetingBriefRegressions:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_existing_coverage_gaps_unchanged(self, client):
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing", "state": "NC", "current_coverages": [],
        })
        assert resp.status_code == 200

    def test_knowledge_gaps_unchanged(self, client):
        resp = client.get("/api/v1/risk/gaps?industry=roofing&current_policies=")
        assert resp.status_code == 200

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12
