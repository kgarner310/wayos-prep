"""Tests for Phase 9: Trust/Explainability Layer fields."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# COVERAGE GAP — why_this_is_here
# ============================================================


class TestCoverageGapWhyThisIsHere:

    def test_gaps_have_why_this_is_here(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp", "general_liability"],
        })
        for gap in result["coverage_gaps"]:
            assert "why_this_is_here" in gap
            assert isinstance(gap["why_this_is_here"], list)
            assert len(gap["why_this_is_here"]) >= 1

    def test_why_this_is_here_derives_from_rules(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({
            "industry": "roofing",
            "state": "NC",
            "vehicle_count": 5,
            "current_coverages": [],
        })
        hnoa_gaps = [g for g in result["coverage_gaps"] if "hired" in g["coverage"].lower()]
        assert len(hnoa_gaps) >= 1
        # HNOA gap triggered by vehicle_exposure rule should reference vehicles
        assert any("vehicle" in w.lower() for w in hnoa_gaps[0]["why_this_is_here"])

    def test_subcontractor_gap_explanation(self):
        """When subcontractors are used and GL is covered, umbrella gap still appears."""
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({
            "industry": "roofing",
            "uses_subcontractors": True,
            "current_coverages": ["general_liability", "workers_comp"],
        })
        umbrella_gaps = [g for g in result["coverage_gaps"]
                         if "umbrella" in g["coverage"].lower()]
        assert len(umbrella_gaps) >= 1
        # Umbrella gap should have why_this_is_here from industry_expected rule
        assert len(umbrella_gaps[0]["why_this_is_here"]) >= 1

    def test_loss_run_boost_appears_in_why(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({
            "industry": "roofing",
            "current_coverages": [],
            "loss_run_data": {
                "patterns": [],
                "underwriting_flags": ["workers comp frequency elevated"],
            },
        })
        wc_gaps = [g for g in result["coverage_gaps"] if "workers" in g["coverage"].lower()]
        if wc_gaps:
            # Should have both industry_expected and loss_run rule
            assert len(wc_gaps[0]["applied_rules"]) >= 2
            assert len(wc_gaps[0]["why_this_is_here"]) >= 2

    def test_empty_coverages_still_have_why(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({
            "industry": "trucking",
            "current_coverages": [],
        })
        for gap in result["coverage_gaps"]:
            assert len(gap["why_this_is_here"]) >= 1


# ============================================================
# RISK OVERVIEW — contributing_factors
# ============================================================


class TestRiskOverviewContributingFactors:

    def test_risk_overview_has_contributing_factors(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": [],
        })
        ro = result["risk_overview"]
        assert "contributing_factors" in ro
        assert isinstance(ro["contributing_factors"], list)

    def test_contributing_factors_present_when_gaps_exist(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": [],
        })
        ro = result["risk_overview"]
        # Roofing with no coverages should flag gaps
        if ro["risk_level"] in ("moderate", "high"):
            assert len(ro["contributing_factors"]) >= 1

    def test_signal_count_present(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({
            "industry": "roofing",
            "state": "NC",
        })
        assert "signal_count" in result["risk_overview"]
        assert isinstance(result["risk_overview"]["signal_count"], int)

    def test_contributing_factors_with_mod(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({
            "industry": "roofing",
            "experience_mod": 1.30,
        })
        ro = result["risk_overview"]
        assert any("mod" in f.lower() for f in ro["contributing_factors"])

    def test_empty_profile_contributing_factors(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({})
        ro = result["risk_overview"]
        assert isinstance(ro["contributing_factors"], list)


# ============================================================
# UNDERWRITER NARRATIVE — source_signals
# ============================================================


class TestNarrativeSourceSignals:

    def test_narrative_has_source_signals(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({
            "industry": "roofing",
            "state": "NC",
        })
        assert "source_signals" in result
        assert isinstance(result["source_signals"], list)
        assert len(result["source_signals"]) >= 1

    def test_source_signals_with_public_intel(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({
            "industry": "roofing",
            "state": "NC",
            "public_web_intel": {
                "company_identity": {"company_name": "Apex"},
                "operations_signals": ["Roof replacement services"],
                "safety_signals": ["OSHA compliance referenced"],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": [],
            },
        })
        signals = result["source_signals"]
        assert any("website" in s.lower() for s in signals)
        assert any("brief" in s.lower() for s in signals)

    def test_source_signals_without_intel(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing"})
        signals = result["source_signals"]
        assert any("account profile" in s.lower() or "brief" in s.lower() for s in signals)

    def test_source_signals_capped(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({
            "industry": "roofing",
            "public_web_intel": {
                "operations_signals": ["A", "B", "C", "D", "E"],
                "safety_signals": ["X", "Y", "Z"],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": [],
            },
        })
        assert len(result["source_signals"]) <= 5


# ============================================================
# WORKSPACE — trust fields pass through
# ============================================================


class TestWorkspaceTrustFields:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def _make_account(self):
        obj = MagicMock()
        for k, v in {
            "id": uuid.uuid4(), "account_name": "Apex Roofing",
            "industry": "roofing", "state": "NC", "employee_count": 27,
            "annual_revenue": 4800000.0, "vehicle_count": 9,
            "uses_subcontractors": True, "current_coverages": ["workers_comp"],
            "website_url": "https://apex.com", "social_urls": None,
            "notes": "", "last_public_intel_refresh_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }.items():
            setattr(obj, k, v)
        return obj

    def test_workspace_coverage_gaps_have_why(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = self._make_account()
        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):
            result = build_renewal_workspace(mock_db, account.id)

        for gap in result.get("coverage_gaps", []):
            assert "why_this_is_here" in gap

    def test_workspace_risk_overview_has_factors(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = self._make_account()
        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):
            result = build_renewal_workspace(mock_db, account.id)

        assert "contributing_factors" in result["risk_overview"]

    def test_workspace_narrative_has_source_signals(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = self._make_account()
        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):
            result = build_renewal_workspace(mock_db, account.id)

        assert "source_signals" in result["underwriter_narrative"]
        assert "fact_sources" in result["underwriter_narrative"]


# ============================================================
# ENDPOINT — schema correctness with trust fields
# ============================================================


class TestWorkspaceEndpointTrustFields:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_endpoint_returns_trust_fields(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "account_id": str(aid),
            "account_summary": {"account_name": "Test", "industry": "roofing", "state": "NC", "account_stage": "renewal", "key_facts": []},
            "operations_signals": {},
            "risk_overview": {
                "risk_level": "moderate",
                "confidence": 0.55,
                "headline": "Moderate.",
                "contributing_factors": ["high-severity coverage gap"],
                "signal_count": 3,
            },
            "coverage_gaps": [{
                "coverage": "Umbrella",
                "reason": "Missing",
                "risk_level": "high",
                "confidence": 0.85,
                "applied_rules": [{"code": "industry_expected", "description": "Industry standard", "confidence_delta": 0.85}],
                "why_this_is_here": ["Industry standard", "Coverage missing"],
            }],
            "producer_questions": [],
            "underwriter_narrative": {
                "email_version": "",
                "memo_version": "",
                "style_applied": {},
                "fact_sources": {"account_profile_used": True},
                "source_signals": ["Renewal brief contributed analysis"],
            },
            "recommended_actions": [],
            "sections_available": ["risk_overview", "coverage_gaps"],
        }

        with patch("app.api.routes.build_renewal_workspace", return_value=mock_result):
            response = client.post(f"/api/v1/workspace/renewal/{aid}", json={})

        assert response.status_code == 200
        data = response.json()

        # Risk overview trust fields
        assert data["risk_overview"]["contributing_factors"] == ["high-severity coverage gap"]
        assert data["risk_overview"]["signal_count"] == 3

        # Coverage gap trust fields
        assert data["coverage_gaps"][0]["why_this_is_here"] == ["Industry standard", "Coverage missing"]
        assert data["coverage_gaps"][0]["applied_rules"][0]["code"] == "industry_expected"

        # Narrative trust fields
        assert data["underwriter_narrative"]["source_signals"] == ["Renewal brief contributed analysis"]
        assert data["underwriter_narrative"]["fact_sources"]["account_profile_used"] is True


# ============================================================
# REGRESSION — existing behavior unchanged
# ============================================================


class TestTrustLayerRegressions:

    def test_coverage_gap_still_has_applied_rules(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({
            "industry": "roofing",
            "current_coverages": [],
        })
        for gap in result["coverage_gaps"]:
            assert "applied_rules" in gap
            for rule in gap["applied_rules"]:
                assert "code" in rule
                assert "description" in rule
                assert "confidence_delta" in rule

    def test_renewal_brief_still_complete(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({"industry": "roofing", "state": "TX"})
        expected_keys = {
            "account_summary", "risk_overview", "underwriter_concerns",
            "coverage_gaps", "loss_patterns", "mod_trends",
            "producer_questions", "defense_strategy", "peer_insights",
            "recommended_actions",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_narrative_still_complete(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing"})
        assert "email_version" in result
        assert "memo_version" in result
        assert "fact_sources" in result
        assert "style_applied" in result
        assert "source_signals" in result

    def test_existing_public_web_intel_endpoint(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        client = TestClient(app)
        try:
            response = client.post("/api/v1/intel/public-web-intel", json={
                "company_name": "Test",
                "raw_website_text": "OSHA safety training for crews.",
            })
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
