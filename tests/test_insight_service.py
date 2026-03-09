"""Tests for Insight Feed Service.

Tests cover:
- Insight generation with coverage gaps (duty_to_advise)
- Workers comp mod signal generation
- Graceful handling of minimal data
- Cross-sell opportunity detection
- Low confidence warning generation
"""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.insight_service import generate_insights


def _make_account(**kwargs):
    """Create a mock Account for insight testing."""
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_name": "Insight Test Co",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 25,
        "annual_revenue": 3000000,
        "workers_comp_mod": None,
        "current_coverages": [],
        "current_carriers": None,
        "claims_summary": None,
        "uses_subcontractors": False,
        "vehicle_count": 5,
        "payroll_estimate": None,
        "named_insured": None,
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_health(**kwargs):
    """Create a mock AccountHealth for insight testing."""
    obj = MagicMock()
    defaults = {
        "overall_score": 50,
        "coverage_score": 50,
        "workers_comp_score": 50,
        "carrier_fit_score": 50,
        "confidence": Decimal("0.5"),
        "top_issues_json": [],
        "duty_to_advise_alert_count": 0,
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_mock_db(deal_outcomes=None):
    """Create a mock db session for insight generation."""
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = deal_outcomes or []
    mock_db.query.return_value = mock_query
    return mock_db


# ============================================================
# INSIGHTS WITH GAPS
# ============================================================


class TestInsightsWithGaps:
    def test_insights_with_gaps(self):
        """Account missing critical coverages should generate duty_to_advise insights."""
        account = _make_account(
            industry="roofing",
            current_coverages=[],
        )
        health = _make_health(
            top_issues_json=[
                "No Workers Comp detected",
                "No General Liability detected",
                "Missing Umbrella coverage",
            ],
            duty_to_advise_alert_count=2,
        )
        mock_db = _make_mock_db()

        insights = generate_insights(account, health, mock_db)

        duty_insights = [i for i in insights if i["insight_type"] == "duty_to_advise"]
        assert len(duty_insights) >= 1

        coverage_alerts = [i for i in insights if i["insight_type"] == "coverage_alert"]
        assert len(coverage_alerts) >= 1


# ============================================================
# INSIGHTS WITH ELEVATED MOD
# ============================================================


class TestInsightsWithElevatedMod:
    def test_insights_with_elevated_mod(self):
        """Account with mod > 1.10 should generate workers_comp_signal."""
        account = _make_account(
            workers_comp_mod=Decimal("1.18"),
        )
        health = _make_health(top_issues_json=[])
        mock_db = _make_mock_db()

        insights = generate_insights(account, health, mock_db)

        wc_insights = [i for i in insights if i["insight_type"] == "workers_comp_signal"]
        assert len(wc_insights) >= 1
        assert "1.18" in wc_insights[0]["title"]


# ============================================================
# INSIGHTS WITH NO DATA
# ============================================================


class TestInsightsWithNoData:
    def test_insights_with_no_data(self):
        """Account with minimal data should handle gracefully (no crash)."""
        account = _make_account(
            industry=None,
            state=None,
            employee_count=None,
            workers_comp_mod=None,
            current_coverages=None,
            claims_summary=None,
        )
        health = _make_health(
            top_issues_json=[],
            confidence=Decimal("0.1"),
        )
        mock_db = _make_mock_db()

        # Should not raise
        insights = generate_insights(account, health, mock_db)
        assert isinstance(insights, list)


# ============================================================
# CROSS-SELL OPPORTUNITY
# ============================================================


class TestInsightsCrossSellOpportunity:
    def test_insights_cross_sell_opportunity(self):
        """Account with 10+ employees, no cyber should generate opportunity insight."""
        account = _make_account(
            employee_count=15,
            current_coverages=["workers_comp", "general_liability"],
        )
        health = _make_health(top_issues_json=[])
        mock_db = _make_mock_db()

        insights = generate_insights(account, health, mock_db)

        opportunity_insights = [i for i in insights if i["insight_type"] == "opportunity"]
        titles = [i["title"] for i in opportunity_insights]
        assert any("cyber" in t.lower() for t in titles), (
            f"Expected cyber cross-sell opportunity, got titles: {titles}"
        )


# ============================================================
# LOW CONFIDENCE WARNING
# ============================================================


class TestInsightLowConfidenceWarning:
    def test_insight_low_confidence_warning(self):
        """Account with very low confidence should generate a warning insight."""
        account = _make_account(
            industry=None,
            workers_comp_mod=None,
            current_coverages=None,
            employee_count=None,
        )
        health = _make_health(
            confidence=Decimal("0.15"),
            top_issues_json=[],
        )
        mock_db = _make_mock_db()

        insights = generate_insights(account, health, mock_db)

        low_confidence = [
            i for i in insights
            if "limited" in i.get("title", "").lower()
            or "data" in i.get("title", "").lower()
        ]
        assert len(low_confidence) >= 1, (
            f"Expected low confidence warning, got: {[i['title'] for i in insights]}"
        )
