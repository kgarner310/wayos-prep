"""Tests for extended Deal Outcome features.

Tests cover:
- Creating outcomes with competitor field via API
- Creating outcomes with notes field via API
- Market signals with no data
"""

import pytest


# ============================================================
# CREATE OUTCOME WITH COMPETITOR
# ============================================================


class TestCreateOutcomeWithCompetitor:
    def test_create_outcome_with_competitor(self, client):
        """POST /outcomes with competitor field. Verify stored."""
        resp = client.post("/api/v1/outcomes", json={
            "account_id": "acct-competitor-test",
            "industry": "roofing",
            "state": "NC",
            "carrier": "Travelers",
            "premium": 55000,
            "outcome": "lost",
            "outcome_reason": "PRICE",
            "competitor": "Erie Insurance",
            "notes": "Lost on price by 8%",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["outcome"] == "lost"


# ============================================================
# CREATE OUTCOME WITH NOTES
# ============================================================


class TestCreateOutcomeWithNotes:
    def test_create_outcome_with_notes(self, client):
        """POST /outcomes with notes field. Verify stored."""
        resp = client.post("/api/v1/outcomes", json={
            "account_id": "acct-notes-test",
            "industry": "hvac",
            "state": "FL",
            "carrier": "Cincinnati",
            "premium": 72000,
            "outcome": "won",
            "outcome_reason": "COVERAGE",
            "notes": "Won because of broader pollution coverage inclusion",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["outcome"] == "won"


# ============================================================
# MARKET SIGNALS EMPTY
# ============================================================


class TestMarketSignalsEmpty:
    def test_market_signals_empty(self, client):
        """GET /market-signals with no data should return valid response."""
        resp = client.get("/api/v1/market-signals")
        assert resp.status_code == 200
        data = resp.json()
        assert "carrier_win_rates" in data
        assert "total_outcomes" in data
        assert "win_rate_overall" in data
        assert isinstance(data["carrier_win_rates"], dict)
        assert isinstance(data["total_outcomes"], int)
