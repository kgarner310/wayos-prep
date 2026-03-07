"""Tests for Edge Score Engine.

Tests cover:
- Base score calculation
- Individual factor adjustments
- Combined factor scoring
- Strength band assignment
- Score clamping (0-100)
- API endpoint integration
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.services.edge_score_service import calculate_edge_score, _get_strength
from app.main import app
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


# ============================================================
# STRENGTH BANDS
# ============================================================


class TestStrengthBands:
    def test_weak(self):
        assert _get_strength(15) == "Weak"

    def test_below_average(self):
        assert _get_strength(40) == "Below Average"

    def test_competitive(self):
        assert _get_strength(55) == "Competitive"

    def test_strong(self):
        assert _get_strength(70) == "Strong"

    def test_dominant(self):
        assert _get_strength(90) == "Dominant"


# ============================================================
# CORE SCORING
# ============================================================


class TestCalculateEdgeScore:
    def test_baseline_empty_account(self):
        result = calculate_edge_score({})
        assert result["edge_score"] == 50
        assert result["strength"] == "Competitive"
        assert result["drivers"] == []
        assert result["drags"] == []

    def test_low_risk_score_adds_10(self):
        result = calculate_edge_score({"risk_score": 25})
        assert result["edge_score"] == 60
        assert "Low risk score" in result["drivers"]

    def test_moderate_risk_score_adds_5(self):
        result = calculate_edge_score({"risk_score": 45})
        assert result["edge_score"] == 55
        assert "Moderate risk score" in result["drivers"]

    def test_high_risk_score_subtracts_10(self):
        result = calculate_edge_score({"risk_score": 80})
        assert result["edge_score"] == 40
        assert "High risk score" in result["drags"]

    def test_premium_below_median(self):
        result = calculate_edge_score({"premium": 80000, "estimated_median_premium": 100000})
        assert result["edge_score"] == 60
        assert "Premium below regional median" in result["drivers"]

    def test_premium_above_median(self):
        result = calculate_edge_score({"premium": 120000, "estimated_median_premium": 100000})
        assert result["edge_score"] == 40
        assert "Premium above regional median" in result["drags"]

    def test_carrier_appetite_positive(self):
        result = calculate_edge_score({"carrier_appetite": "positive"})
        assert result["edge_score"] == 55
        assert "Carrier appetite strong" in result["drivers"]

    def test_carrier_appetite_negative(self):
        result = calculate_edge_score({"carrier_appetite": "negative"})
        assert result["edge_score"] == 45
        assert "Carrier appetite weak" in result["drags"]

    def test_coverage_comprehensive(self):
        result = calculate_edge_score({"coverage_completeness": 0.95})
        assert result["edge_score"] == 55
        assert "Coverage program comprehensive" in result["drivers"]

    def test_coverage_gaps(self):
        result = calculate_edge_score({"coverage_completeness": 0.3})
        assert result["edge_score"] == 45
        assert "Significant coverage gaps" in result["drags"]

    def test_favorable_mod(self):
        result = calculate_edge_score({"mod": 0.78})
        assert result["edge_score"] == 55
        assert "Favorable experience mod" in result["drivers"]

    def test_elevated_mod(self):
        result = calculate_edge_score({"mod": 1.35})
        assert result["edge_score"] == 45
        assert "Elevated experience mod" in result["drags"]

    def test_low_loss_ratio(self):
        result = calculate_edge_score({"loss_ratio": 0.3})
        assert result["edge_score"] == 55

    def test_high_loss_ratio(self):
        result = calculate_edge_score({"loss_ratio": 0.8})
        assert result["edge_score"] == 45

    def test_combined_positive_factors(self):
        result = calculate_edge_score({
            "risk_score": 20,
            "premium": 70000,
            "estimated_median_premium": 100000,
            "carrier_appetite": "positive",
            "coverage_completeness": 0.95,
            "mod": 0.75,
            "loss_ratio": 0.25,
        })
        assert result["edge_score"] == 90
        assert result["strength"] == "Dominant"
        assert len(result["drivers"]) >= 5

    def test_combined_negative_factors(self):
        result = calculate_edge_score({
            "risk_score": 85,
            "premium": 130000,
            "estimated_median_premium": 100000,
            "carrier_appetite": "negative",
            "coverage_completeness": 0.3,
            "mod": 1.5,
            "loss_ratio": 0.9,
        })
        assert result["edge_score"] == 10
        assert result["strength"] == "Weak"
        assert len(result["drags"]) >= 5

    def test_score_clamped_at_0(self):
        result = calculate_edge_score({
            "risk_score": 90,
            "premium": 200000,
            "estimated_median_premium": 100000,
            "carrier_appetite": "negative",
            "coverage_completeness": 0.2,
            "mod": 2.0,
            "loss_ratio": 1.0,
        })
        assert result["edge_score"] >= 0

    def test_score_clamped_at_100(self):
        result = calculate_edge_score({
            "risk_score": 10,
            "premium": 50000,
            "estimated_median_premium": 100000,
            "carrier_appetite": "positive",
            "coverage_completeness": 1.0,
            "mod": 0.5,
            "loss_ratio": 0.1,
        })
        assert result["edge_score"] <= 100

    def test_median_zero_ignored(self):
        result = calculate_edge_score({"premium": 50000, "estimated_median_premium": 0})
        assert result["edge_score"] == 50


# ============================================================
# API ENDPOINT
# ============================================================


class TestEdgeScoreEndpoint:
    def test_basic_request(self):
        resp = client.post("/api/v1/edge-score", json={
            "risk_score": 30,
            "carrier_appetite": "positive",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "edge_score" in data
        assert "strength" in data
        assert "drivers" in data

    def test_empty_body(self):
        resp = client.post("/api/v1/edge-score", json={})
        assert resp.status_code == 200
        assert resp.json()["edge_score"] == 50

    def test_score_in_valid_range(self):
        resp = client.post("/api/v1/edge-score", json={
            "risk_score": 20,
            "premium": 80000,
            "estimated_median_premium": 100000,
        })
        data = resp.json()
        assert 0 <= data["edge_score"] <= 100
