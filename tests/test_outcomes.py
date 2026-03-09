"""Tests for Deal Outcomes and Outcome Aggregation.

Tests cover:
- Outcome creation via API
- Market signals aggregation
- Carrier win rate calculation
- Account timeline recording
- API endpoint integration
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.services.outcome_learning_service import (
    get_carrier_win_rates,
    get_outcome_reason_breakdown,
    get_market_signals,
    get_market_edge,
    MIN_SAMPLE_SIZE,
    VALID_OUTCOMES,
    VALID_OUTCOME_REASONS,
)
from app.main import app
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


# ============================================================
# CONSTANTS
# ============================================================


class TestConstants:
    def test_valid_outcomes(self):
        assert "won" in VALID_OUTCOMES
        assert "lost" in VALID_OUTCOMES
        assert "pending" in VALID_OUTCOMES

    def test_valid_outcome_reasons(self):
        assert "PRICE" in VALID_OUTCOME_REASONS
        assert "COVERAGE" in VALID_OUTCOME_REASONS
        assert "RELATIONSHIP" in VALID_OUTCOME_REASONS
        assert "APPETITE" in VALID_OUTCOME_REASONS
        assert "SERVICE" in VALID_OUTCOME_REASONS
        assert "UNKNOWN" in VALID_OUTCOME_REASONS


# ============================================================
# CARRIER WIN RATES (UNIT)
# ============================================================


class TestCarrierWinRates:
    def _make_outcome(self, carrier, outcome, industry=None, state=None):
        m = MagicMock()
        m.carrier = carrier
        m.outcome = outcome
        m.industry = industry
        m.state = state
        m.outcome_reason = None
        return m

    def test_simple_win_rates(self):
        mock_db = MagicMock()
        outcomes = [
            self._make_outcome("Travelers", "won"),
            self._make_outcome("Travelers", "lost"),
            self._make_outcome("Travelers", "won"),
            self._make_outcome("Cincinnati", "won"),
            self._make_outcome("Cincinnati", "won"),
            self._make_outcome("Cincinnati", "lost"),
        ]
        mock_db.query.return_value.all.return_value = outcomes
        # No filters applied with industry=None, state=None
        result = get_carrier_win_rates(mock_db)
        assert result["Travelers"] == 0.67
        assert result["Cincinnati"] == 0.67

    def test_empty_outcomes(self):
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        result = get_carrier_win_rates(mock_db)
        assert result == {}

    def test_no_carrier_skipped(self):
        mock_db = MagicMock()
        m = self._make_outcome(None, "won")
        mock_db.query.return_value.all.return_value = [m]
        result = get_carrier_win_rates(mock_db)
        assert result == {}


# ============================================================
# OUTCOME REASON BREAKDOWN (UNIT)
# ============================================================


class TestOutcomeReasonBreakdown:
    def test_reason_counts(self):
        mock_db = MagicMock()
        outcomes = []
        for reason in ["PRICE", "PRICE", "COVERAGE", "UNKNOWN"]:
            m = MagicMock()
            m.outcome = "lost"
            m.outcome_reason = reason
            outcomes.append(m)
        mock_db.query.return_value.filter.return_value.all.return_value = outcomes
        result = get_outcome_reason_breakdown(mock_db)
        assert result["PRICE"] == 2
        assert result["COVERAGE"] == 1
        assert result["UNKNOWN"] == 1

    def test_no_lost_outcomes(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = get_outcome_reason_breakdown(mock_db)
        assert result == {}


# ============================================================
# MARKET SIGNALS (UNIT)
# ============================================================


class TestGetMarketSignals:
    def test_full_signals(self):
        mock_db = MagicMock()

        def _make_outcome(carrier, outcome, reason=None):
            m = MagicMock()
            m.carrier = carrier
            m.outcome = outcome
            m.outcome_reason = reason
            m.industry = "roofing"
            m.state = "NC"
            return m

        outcomes = [
            _make_outcome("Travelers", "won"),
            _make_outcome("Travelers", "lost", "PRICE"),
            _make_outcome("Cincinnati", "won"),
            _make_outcome("Cincinnati", "won"),
        ]

        # The function makes multiple queries. Mock chained calls.
        mock_query = MagicMock()
        mock_query.all.return_value = outcomes
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value = mock_query

        result = get_market_signals(mock_db)
        assert "carrier_win_rates" in result
        assert "total_outcomes" in result
        assert result["total_outcomes"] == 4
        assert "top_carrier" in result


# ============================================================
# API ENDPOINTS
# ============================================================


class TestOutcomeEndpoint:
    def test_create_outcome(self):
        resp = client.post("/api/v1/outcomes", json={
            "account_id": "acct-100",
            "industry": "roofing",
            "state": "NC",
            "carrier": "Travelers",
            "premium": 55000,
            "outcome": "won",
            "outcome_reason": "PRICE",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["account_id"] == "acct-100"
        assert data["outcome"] == "won"

    def test_create_outcome_missing_fields(self):
        resp = client.post("/api/v1/outcomes", json={"carrier": "Travelers"})
        assert resp.status_code == 422

    def test_create_outcome_minimal(self):
        resp = client.post("/api/v1/outcomes", json={
            "account_id": "acct-200",
            "outcome": "lost",
        })
        assert resp.status_code == 200


class TestMarketSignalsEndpoint:
    def test_market_signals_no_filter(self):
        resp = client.get("/api/v1/market-signals")
        assert resp.status_code == 200
        data = resp.json()
        assert "carrier_win_rates" in data
        assert "total_outcomes" in data

    def test_market_signals_with_industry(self):
        resp = client.get("/api/v1/market-signals?industry=roofing")
        assert resp.status_code == 200


class TestAccountTimelineEndpoint:
    def test_timeline_returns_events(self):
        resp = client.get("/api/v1/accounts/acct-123/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_id"] == "acct-123"
        assert "events" in data
        assert "count" in data


# ============================================================
# MEETING BRIEF ENHANCEMENT
# ============================================================


class TestMeetingBriefEnhancement:
    def test_brief_without_edge_score(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing")
        assert resp.status_code == 200
        data = resp.json()
        assert "edge_score" not in data

    def test_brief_with_edge_score(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing&include_edge_score=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "edge_score" in data
        assert "edge_score" in data["edge_score"]
        assert "strength" in data["edge_score"]

    def test_brief_with_market_signals(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing&include_market_signals=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "market_signals" in data

    def test_brief_with_both(self):
        resp = client.get(
            "/api/v1/meeting/brief?industry=roofing"
            "&include_edge_score=true&include_market_signals=true"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "edge_score" in data
        assert "market_signals" in data


# ============================================================
# MARKET EDGE (UNIT)
# ============================================================


class TestGetMarketEdge:
    def _make_outcome(self, carrier, outcome, reason=None, industry="roofing", state="NC"):
        m = MagicMock()
        m.carrier = carrier
        m.outcome = outcome
        m.outcome_reason = reason
        m.industry = industry
        m.state = state
        return m

    def _mock_db(self, outcomes):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.all.return_value = outcomes
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value = mock_query
        return mock_db

    def test_sufficient_data(self):
        outcomes = [
            self._make_outcome("Cincinnati", "won"),
            self._make_outcome("Cincinnati", "won"),
            self._make_outcome("Cincinnati", "lost", "PRICE"),
            self._make_outcome("Travelers", "won"),
            self._make_outcome("Travelers", "lost", "PRICE"),
            self._make_outcome("Travelers", "lost", "COVERAGE"),
        ]
        db = self._mock_db(outcomes)
        result = get_market_edge(db, "roofing", "NC")

        assert result["industry"] == "roofing"
        assert result["state"] == "NC"
        assert result["sample_size"] == 6
        assert result["confidence"] == "normal"
        assert len(result["carrier_win_rates"]) == 2

        # Cincinnati: 2 wins / 3 total = 0.67
        cin = next(c for c in result["carrier_win_rates"] if c["carrier"] == "Cincinnati")
        assert cin["win_rate"] == 0.67
        assert cin["wins"] == 2
        assert cin["losses"] == 1

        # Travelers: 1 win / 3 total = 0.33
        trav = next(c for c in result["carrier_win_rates"] if c["carrier"] == "Travelers")
        assert trav["win_rate"] == 0.33
        assert trav["wins"] == 1
        assert trav["losses"] == 2

        # Sorted by win_rate descending
        assert result["carrier_win_rates"][0]["carrier"] == "Cincinnati"
        assert result["carrier_win_rates"][1]["carrier"] == "Travelers"

    def test_loss_reasons_aggregated(self):
        outcomes = [
            self._make_outcome("A", "lost", "PRICE"),
            self._make_outcome("A", "lost", "PRICE"),
            self._make_outcome("A", "lost", "COVERAGE"),
            self._make_outcome("B", "won"),
            self._make_outcome("B", "won"),
        ]
        db = self._mock_db(outcomes)
        result = get_market_edge(db, "roofing", "NC")

        reasons = result["top_loss_reasons"]
        assert reasons[0]["reason"] == "PRICE"
        assert reasons[0]["count"] == 2
        assert reasons[1]["reason"] == "COVERAGE"
        assert reasons[1]["count"] == 1

    def test_sparse_data_low_confidence(self):
        outcomes = [
            self._make_outcome("Travelers", "won"),
            self._make_outcome("Travelers", "lost"),
        ]
        db = self._mock_db(outcomes)
        result = get_market_edge(db, "roofing", "NC")

        assert result["sample_size"] == 2
        assert result["confidence"] == "low"
        assert result["carrier_win_rates"] == []
        assert result["top_loss_reasons"] == []

    def test_empty_data(self):
        db = self._mock_db([])
        result = get_market_edge(db, "roofing", "NC")

        assert result["sample_size"] == 0
        assert result["confidence"] == "low"
        assert result["carrier_win_rates"] == []
        assert result["top_loss_reasons"] == []

    def test_null_carrier_skipped(self):
        outcomes = [
            self._make_outcome(None, "won"),
            self._make_outcome(None, "lost"),
            self._make_outcome("Hartford", "won"),
            self._make_outcome("Hartford", "won"),
            self._make_outcome("Hartford", "lost"),
        ]
        db = self._mock_db(outcomes)
        result = get_market_edge(db, "roofing", "NC")

        assert len(result["carrier_win_rates"]) == 1
        assert result["carrier_win_rates"][0]["carrier"] == "Hartford"

    def test_min_sample_size_boundary(self):
        # Exactly at MIN_SAMPLE_SIZE should be normal confidence
        outcomes = [self._make_outcome("A", "won") for _ in range(MIN_SAMPLE_SIZE)]
        db = self._mock_db(outcomes)
        result = get_market_edge(db, "roofing", "NC")

        assert result["confidence"] == "normal"
        assert len(result["carrier_win_rates"]) > 0


# ============================================================
# MARKET EDGE ENDPOINT
# ============================================================


class TestMarketEdgeEndpoint:
    def test_market_edge_returns_200(self):
        acct_id = uuid.uuid4()
        mock_account = MagicMock()
        mock_account.id = acct_id
        mock_account.industry = "roofing"
        mock_account.state = "NC"

        mock_db = MagicMock()
        # account lookup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_account
        # deal outcome query (chained filters)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        # Re-set first for account lookup to work on first call
        mock_db.query.return_value.filter.return_value.first.return_value = mock_account

        app.dependency_overrides[get_db] = lambda: mock_db
        resp = client.get(f"/api/v1/accounts/{acct_id}/market-edge")
        assert resp.status_code == 200
        data = resp.json()
        assert "industry" in data
        assert "sample_size" in data
        assert "carrier_win_rates" in data
        assert "top_loss_reasons" in data
        assert "confidence" in data
        app.dependency_overrides[get_db] = lambda: MagicMock()

    def test_market_edge_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db
        resp = client.get(f"/api/v1/accounts/{uuid.uuid4()}/market-edge")
        assert resp.status_code == 404
        app.dependency_overrides[get_db] = lambda: MagicMock()


# ============================================================
# DASHBOARD INTEGRATION — market_edge in response
# ============================================================


class TestDashboardMarketEdge:
    def test_dashboard_endpoint_calls_get_market_edge(self):
        """Verify get_market_edge is wired into the dashboard route."""
        from app.api.routes import account_dashboard
        import inspect

        source = inspect.getsource(account_dashboard)
        assert "get_market_edge" in source
        assert '"market_edge"' in source or "'market_edge'" in source
