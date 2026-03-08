"""Tests for Account Health Card Service.

Tests cover:
- Deterministic scoring with full, partial, and minimal data
- Duty-to-advise alert counting
- Workers comp mod scoring (elevated and good)
- Confidence calculation (all fields vs none)
- Claims impact on scoring
- Coverage score calculation (full vs empty)
- Carrier fit scoring (multiple carriers)
- Persistence behavior (db flush)
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.health_service import (
    compute_account_health,
    _compute_coverage_score,
    _compute_workers_comp_score,
    _compute_carrier_fit_score,
    _compute_confidence,
    CONFIDENCE_FIELDS,
)


def _make_account(**kwargs):
    """Create a mock Account for testing."""
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_name": "Test Roofing",
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
        "extracted_text": None,
        "website_url": None,
        "social_urls": None,
        "notes": "",
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# FULL DATA SCORING
# ============================================================


class TestFullDataScoring:
    def test_full_data_scoring(self):
        """Account with all fields populated should produce reasonable scores and high confidence."""
        account = _make_account(
            industry="roofing",
            state="NC",
            employee_count=38,
            annual_revenue=4200000,
            workers_comp_mod=Decimal("1.12"),
            current_coverages=[
                "workers_comp", "general_liability", "commercial_auto",
                "umbrella", "inland_marine", "builders_risk", "property",
            ],
            current_carriers=["Travelers", "Cincinnati", "Hartford"],
            claims_summary={"open_claims": 0, "total_claims_3yr": 1},
            payroll_estimate=1800000,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        health = compute_account_health(account, mock_db)

        assert 0 <= health.overall_score <= 100
        assert 0 <= health.coverage_score <= 100
        assert 0 <= health.workers_comp_score <= 100
        assert 0 <= health.carrier_fit_score <= 100
        assert float(health.confidence) > 0.5


# ============================================================
# PARTIAL DATA SCORING
# ============================================================


class TestPartialDataScoring:
    def test_partial_data_scoring(self):
        """Account with only industry and state should work, but have low confidence."""
        account = _make_account(
            industry="roofing",
            state="NC",
            employee_count=None,
            annual_revenue=None,
            workers_comp_mod=None,
            current_coverages=None,
            current_carriers=None,
            claims_summary=None,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        health = compute_account_health(account, mock_db)

        assert float(health.confidence) < 0.5
        assert 0 <= health.overall_score <= 100
        assert 0 <= health.coverage_score <= 100


# ============================================================
# MINIMAL DATA SCORING
# ============================================================


class TestMinimalDataScoring:
    def test_minimal_data_scoring(self):
        """Account with only account_name should not crash and return scores."""
        account = _make_account(
            account_name="Unknown Company",
            industry=None,
            state=None,
            employee_count=None,
            annual_revenue=None,
            workers_comp_mod=None,
            current_coverages=None,
            current_carriers=None,
            claims_summary=None,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        health = compute_account_health(account, mock_db)

        assert 0 <= health.overall_score <= 100
        assert health.coverage_score is not None
        assert health.workers_comp_score is not None
        assert health.carrier_fit_score is not None


# ============================================================
# DUTY TO ADVISE ALERTS
# ============================================================


class TestDutyToAdviseAlerts:
    def test_duty_to_advise_alerts(self):
        """Roofing account with no coverages should have duty_to_advise_alert_count > 0."""
        account = _make_account(
            industry="roofing",
            state="NC",
            current_coverages=[],
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        health = compute_account_health(account, mock_db)

        assert health.duty_to_advise_alert_count > 0


# ============================================================
# ELEVATED MOD SCORING
# ============================================================


class TestElevatedModScoring:
    def test_elevated_mod_scoring(self):
        """Account with workers_comp_mod=1.25 should have low WC score and elevated issue."""
        account = _make_account(
            workers_comp_mod=Decimal("1.25"),
        )
        score, issues = _compute_workers_comp_score(account)

        assert score <= 50
        assert any("mod" in i.lower() or "high" in i.lower() for i in issues)


# ============================================================
# GOOD MOD SCORING
# ============================================================


class TestGoodModScoring:
    def test_good_mod_scoring(self):
        """Account with workers_comp_mod=0.85 should have high WC score."""
        account = _make_account(
            workers_comp_mod=Decimal("0.85"),
        )
        score, issues = _compute_workers_comp_score(account)

        assert score >= 85


# ============================================================
# CONFIDENCE ALL FIELDS
# ============================================================


class TestConfidenceAllFields:
    def test_confidence_all_fields(self):
        """Account with all CONFIDENCE_FIELDS filled should have confidence 1.0."""
        account = _make_account(
            industry="roofing",
            state="NC",
            employee_count=25,
            current_coverages=["workers_comp"],
            workers_comp_mod=Decimal("1.0"),
            current_carriers=["Travelers"],
            claims_summary={"open_claims": 0},
            annual_revenue=3000000,
        )
        confidence = _compute_confidence(account)
        assert confidence == 1.0


# ============================================================
# CONFIDENCE NO FIELDS
# ============================================================


class TestConfidenceNoFields:
    def test_confidence_no_fields(self):
        """Account with no optional fields should have very low confidence."""
        account = _make_account(
            industry=None,
            state=None,
            employee_count=None,
            current_coverages=None,
            workers_comp_mod=None,
            current_carriers=None,
            claims_summary=None,
            annual_revenue=None,
        )
        confidence = _compute_confidence(account)
        assert confidence < 0.2


# ============================================================
# CLAIMS AFFECT SCORE
# ============================================================


class TestClaimsAffectScore:
    def test_claims_affect_score(self):
        """Account with open claims should have lower WC score than one without."""
        account_clean = _make_account(
            workers_comp_mod=Decimal("1.05"),
            claims_summary={"open_claims": 0, "total_claims_3yr": 0},
        )
        account_claims = _make_account(
            workers_comp_mod=Decimal("1.05"),
            claims_summary={"open_claims": 2, "total_claims_3yr": 4},
        )
        score_clean, _ = _compute_workers_comp_score(account_clean)
        score_claims, _ = _compute_workers_comp_score(account_claims)

        assert score_claims < score_clean


# ============================================================
# COVERAGE SCORE FULL
# ============================================================


class TestCoverageScoreFull:
    def test_coverage_score_full(self):
        """Roofing account with all expected coverages should have score near 100."""
        account = _make_account(
            industry="roofing",
            current_coverages=[
                "workers_comp", "general_liability", "commercial_auto",
                "umbrella", "inland_marine", "builders_risk", "property",
            ],
        )
        score, issues, duty_alerts = _compute_coverage_score(account)

        assert score >= 90
        assert duty_alerts == 0


# ============================================================
# COVERAGE SCORE EMPTY
# ============================================================


class TestCoverageScoreEmpty:
    def test_coverage_score_empty(self):
        """Roofing account with no coverages should have very low score."""
        account = _make_account(
            industry="roofing",
            current_coverages=[],
        )
        score, issues, duty_alerts = _compute_coverage_score(account)

        assert score <= 30
        assert duty_alerts > 0


# ============================================================
# CARRIER FIT MULTIPLE CARRIERS
# ============================================================


class TestCarrierFitMultipleCarriers:
    def test_carrier_fit_multiple_carriers(self):
        """Account with 3+ carriers should score better than single carrier."""
        account_single = _make_account(current_carriers=["Travelers"])
        account_multi = _make_account(
            current_carriers=["Travelers", "Cincinnati", "Hartford"],
        )

        score_single, _ = _compute_carrier_fit_score(account_single)
        score_multi, _ = _compute_carrier_fit_score(account_multi)

        assert score_multi > score_single


# ============================================================
# PERSISTENCE
# ============================================================


class TestComputeAccountHealthPersists:
    def test_compute_account_health_persists(self):
        """compute_account_health should create/update AccountHealth and call db.flush()."""
        account = _make_account(
            industry="roofing",
            state="NC",
            current_coverages=["workers_comp"],
        )
        mock_db = MagicMock()
        # Simulate no existing health record
        mock_db.query.return_value.filter.return_value.first.return_value = None

        health = compute_account_health(account, mock_db)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert health.overall_score is not None
        assert health.account_id == account.id
