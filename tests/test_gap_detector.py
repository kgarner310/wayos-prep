"""Tests for Knowledge-Profile-Based Coverage Gap Detection."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.services.coverage_gap_detector import detect_knowledge_gaps


# ============================================================
# CORE GAP DETECTION LOGIC
# ============================================================


class TestDetectKnowledgeGaps:

    def test_roofing_missing_workers_comp(self):
        """Roofing contractor missing workers comp should be high risk."""
        result = detect_knowledge_gaps("roofing", ["commercial auto", "general liability"])
        assert result["risk_level"] == "high"
        assert "workers compensation" in result["missing_coverages"]
        assert len(result["top_exposures"]) >= 3
        assert len(result["recommended_questions"]) >= 3

    def test_roofing_missing_only_umbrella(self):
        """Roofing with all critical coverages but missing umbrella = medium."""
        result = detect_knowledge_gaps("roofing", [
            "workers compensation", "commercial auto", "general liability", "inland marine",
        ])
        assert result["risk_level"] == "medium"
        assert "umbrella" in result["missing_coverages"]

    def test_landscaping_missing_inland_marine(self):
        """Landscaping contractor missing inland marine should be medium risk."""
        result = detect_knowledge_gaps("landscaping", [
            "workers compensation", "commercial auto", "general liability",
            "umbrella", "pollution liability",
        ])
        assert result["risk_level"] == "medium"
        assert "inland marine" in result["missing_coverages"]

    def test_restaurant_full_coverage(self):
        """Restaurant with all policy lines should be low risk."""
        result = detect_knowledge_gaps("restaurant", [
            "workers compensation", "general liability", "commercial property",
            "liquor liability", "employment practices liability",
            "cyber liability", "commercial auto", "umbrella",
        ])
        assert result["risk_level"] == "low"
        assert len(result["missing_coverages"]) == 0

    def test_restaurant_partial_coverage(self):
        """Restaurant missing critical coverages = high risk."""
        result = detect_knowledge_gaps("restaurant", ["liquor liability"])
        assert result["risk_level"] == "high"
        assert "workers compensation" in result["missing_coverages"]
        assert "general liability" in result["missing_coverages"]

    def test_unknown_industry(self):
        """Unknown industry returns empty results with error."""
        result = detect_knowledge_gaps("underwater basket weaving", ["general liability"])
        assert result["risk_level"] == "low"
        assert result["missing_coverages"] == []
        assert "error" in result

    def test_empty_policies(self):
        """No current policies = high risk for any known industry."""
        result = detect_knowledge_gaps("roofing", [])
        assert result["risk_level"] == "high"
        assert len(result["missing_coverages"]) >= 3

    def test_hvac_gaps(self):
        """HVAC missing pollution and cyber should be identified."""
        result = detect_knowledge_gaps("hvac", [
            "workers compensation", "commercial auto", "general liability",
            "inland marine", "professional liability", "umbrella",
        ])
        # Remaining: pollution liability, cyber liability
        assert "pollution liability" in result["missing_coverages"]
        assert "cyber liability" in result["missing_coverages"]

    def test_trucking_missing_cargo(self):
        """Trucking company missing motor truck cargo."""
        result = detect_knowledge_gaps("trucking", [
            "commercial auto", "general liability", "workers compensation",
        ])
        assert "motor truck cargo" in result["missing_coverages"]

    def test_case_insensitive_policies(self):
        """Policy matching should be case insensitive."""
        result = detect_knowledge_gaps("roofing", [
            "Workers Compensation", "Commercial Auto", "General Liability",
            "Inland Marine", "Umbrella",
        ])
        assert result["risk_level"] == "low"
        assert len(result["missing_coverages"]) == 0

    def test_underscore_policies(self):
        """Policy names with underscores should match."""
        result = detect_knowledge_gaps("restaurant", [
            "workers_compensation", "general_liability", "commercial_property",
            "liquor_liability", "employment_practices_liability",
            "cyber_liability", "commercial_auto", "umbrella",
        ])
        assert result["risk_level"] == "low"

    def test_output_structure(self):
        """Output should have all required fields."""
        result = detect_knowledge_gaps("roofing", [])
        assert "industry" in result
        assert "missing_coverages" in result
        assert "risk_level" in result
        assert "recommended_questions" in result
        assert "top_exposures" in result
        assert isinstance(result["missing_coverages"], list)
        assert isinstance(result["recommended_questions"], list)
        assert isinstance(result["top_exposures"], list)


# ============================================================
# RISK LEVEL LOGIC
# ============================================================


class TestRiskLevelLogic:

    def test_high_when_workers_comp_missing(self):
        result = detect_knowledge_gaps("restaurant", ["general liability"])
        assert result["risk_level"] == "high"

    def test_high_when_commercial_auto_missing(self):
        result = detect_knowledge_gaps("trucking", [
            "workers compensation", "general liability", "motor truck cargo",
        ])
        assert result["risk_level"] == "high"

    def test_high_when_gl_missing(self):
        result = detect_knowledge_gaps("restaurant", ["workers compensation"])
        assert result["risk_level"] == "high"

    def test_medium_when_umbrella_missing(self):
        result = detect_knowledge_gaps("landscaping", [
            "workers compensation", "commercial auto", "general liability",
            "inland marine", "pollution liability",
        ])
        assert result["risk_level"] == "medium"

    def test_low_when_all_present(self):
        result = detect_knowledge_gaps("plumber", [
            "workers compensation", "commercial auto", "general liability",
            "professional liability", "inland marine", "umbrella",
        ])
        # Only pollution liability missing — not in high or medium sets
        assert result["risk_level"] == "low"


# ============================================================
# API ENDPOINT
# ============================================================


class TestGapsEndpoint:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_get_gaps_roofing(self, client):
        resp = client.get("/api/v1/risk/gaps?industry=roofing&current_policies=general+liability,commercial+auto")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "high"
        assert "workers compensation" in data["missing_coverages"]

    def test_get_gaps_empty_policies(self, client):
        resp = client.get("/api/v1/risk/gaps?industry=restaurant&current_policies=")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "high"

    def test_get_gaps_unknown_industry(self, client):
        resp = client.get("/api/v1/risk/gaps?industry=unknown_xyz&current_policies=gl")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_get_gaps_full_coverage(self, client):
        policies = ",".join([
            "workers compensation", "commercial auto", "general liability",
            "inland marine", "umbrella",
        ])
        resp = client.get(f"/api/v1/risk/gaps?industry=roofing&current_policies={policies}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == "low"


# ============================================================
# DEMO INTEGRATION
# ============================================================


class TestDemoAccountGaps:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch("app.api.routes.get_account")
    def test_demo_account_gaps(self, mock_get, client):
        mock_acct = MagicMock()
        mock_acct.id = uuid.uuid4()
        mock_acct.account_name = "Summit Ridge Roofing LLC"
        mock_acct.industry = "roofing"
        mock_acct.current_coverages = ["general_liability", "workers_comp"]
        mock_get.return_value = mock_acct

        resp = client.get(f"/api/v1/demo/account-gaps/{mock_acct.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_name"] == "Summit Ridge Roofing LLC"
        assert len(data["missing_coverages"]) > 0

    @patch("app.api.routes.get_account")
    def test_demo_account_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get(f"/api/v1/demo/account-gaps/{uuid.uuid4()}")
        assert resp.status_code == 404


# ============================================================
# REGRESSIONS
# ============================================================


class TestGapDetectorRegressions:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_existing_coverage_gaps_endpoint_unchanged(self, client):
        """Original POST /risk/coverage-gaps still works."""
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "coverage_gaps" in data

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_industry_profiles_still_loaded(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12
