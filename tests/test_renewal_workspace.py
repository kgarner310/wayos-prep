"""Tests for Phase 8: Renewal Workspace Service."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_account_obj(**overrides):
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_name": "Apex Roofing",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 27,
        "annual_revenue": 4800000.0,
        "vehicle_count": 9,
        "uses_subcontractors": True,
        "current_coverages": ["general_liability", "workers_comp"],
        "website_url": "https://apexroofing.com",
        "social_urls": None,
        "notes": "",
        "last_public_intel_refresh_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


MOCK_PUBLIC_INTEL = {
    "artifact_id": str(uuid.uuid4()),
    "created_at": datetime.now(timezone.utc).isoformat(),
    "content": {
        "public_web_intel": {
            "company_identity": {
                "company_name": "Apex Roofing",
                "founded_year": 2012,
                "service_area": ["Charlotte", "Mecklenburg County"],
            },
            "operations_signals": [
                "Roof replacement/repair/installation services",
                "Storm restoration work",
            ],
            "safety_signals": ["References OSHA compliance or procedures"],
            "scale_signals": ["Multi-crew/location operations"],
            "carrier_relevant_signals": ["Professional certifications/licensing"],
            "observed_public_signals": [],
            "cautions": ["Public content may reflect marketing language"],
        },
    },
}


# ============================================================
# SERVICE TESTS
# ============================================================


class TestBuildRenewalWorkspace:

    def test_workspace_full_data(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=MOCK_PUBLIC_INTEL), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(mock_db, account.id)

        assert result["account_id"] == str(account.id)
        assert result["account_summary"]["account_name"] == "Apex Roofing"
        assert result["account_summary"]["industry"] == "roofing"
        assert "operations_signals" in result
        assert result["operations_signals"]["company_identity"]["company_name"] == "Apex Roofing"
        assert len(result["operations_signals"]["operations_signals"]) >= 1
        assert "risk_overview" in result
        assert "risk_level" in result["risk_overview"]
        assert isinstance(result["coverage_gaps"], list)
        assert isinstance(result["producer_questions"], list)
        assert "email_version" in result["underwriter_narrative"]
        assert isinstance(result["recommended_actions"], list)
        assert isinstance(result["sections_available"], list)
        assert "error" not in result

    def test_workspace_no_public_intel(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(mock_db, account.id)

        assert result["account_id"] == str(account.id)
        assert result["operations_signals"] == {}
        # Should still have renewal brief, gaps, narrative
        assert result["account_summary"]["account_name"] == "Apex Roofing"
        assert "risk_overview" in result
        assert "error" not in result

    def test_workspace_minimal_account(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj(
            industry="",
            state="",
            employee_count=0,
            annual_revenue=0,
            vehicle_count=0,
            uses_subcontractors=False,
            current_coverages=[],
        )

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(mock_db, account.id)

        assert result["account_id"] == str(account.id)
        assert "error" not in result
        # Should still produce a workspace even with minimal data
        assert isinstance(result["coverage_gaps"], list)
        assert isinstance(result["recommended_actions"], list)

    def test_workspace_account_not_found(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        fake_id = uuid.uuid4()
        with patch("app.services.renewal_workspace_service.get_account", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(mock_db, fake_id)

        assert result["error"] == "Account not found"
        assert result["account_id"] == str(fake_id)

    def test_workspace_with_loss_data(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()
        loss_run_data = {
            "patterns": ["Repeat slip-and-fall claims at same location"],
            "underwriting_flags": ["3 open claims with increasing reserves"],
            "summary": {"total_claims": 5, "open_claims": 2},
        }

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=MOCK_PUBLIC_INTEL), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(
                mock_db, account.id, {"loss_run_data": loss_run_data},
            )

        assert "error" not in result
        # With loss data, should have risk overview and recommended actions
        assert result["risk_overview"] is not None

    def test_workspace_with_mod_data(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()
        experience_mod_data = {
            "mod_trend": {"direction": "worsening", "current": 1.15, "prior": 0.95},
            "flags": ["Mod above unity"],
            "insights": ["Increasing frequency driving mod upward"],
        }

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(
                mock_db, account.id,
                {"experience_mod": 1.15, "experience_mod_data": experience_mod_data},
            )

        assert "error" not in result
        assert result["risk_overview"].get("risk_level") is not None

    def test_workspace_public_intel_error_graceful(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", side_effect=Exception("DB error")), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(mock_db, account.id)

        # Should still complete without crashing
        assert result["account_id"] == str(account.id)
        assert "error" not in result
        assert result["operations_signals"] == {}

    def test_sections_available_populated(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=MOCK_PUBLIC_INTEL), \
             patch("app.services.renewal_workspace_service.log_event"):

            result = build_renewal_workspace(mock_db, account.id)

        sections = result["sections_available"]
        assert isinstance(sections, list)
        assert "operations_signals" in sections
        assert "risk_overview" in sections

    def test_instrumentation_events(self, mock_db):
        from app.services.renewal_workspace_service import build_renewal_workspace

        account = _make_account_obj()

        with patch("app.services.renewal_workspace_service.get_account", return_value=account), \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event") as mock_log:

            build_renewal_workspace(mock_db, account.id)

        event_types = [call.args[1] for call in mock_log.call_args_list]
        assert "renewal_workspace_requested" in event_types
        assert "renewal_workspace_generated" in event_types


# ============================================================
# ENDPOINT TESTS
# ============================================================


class TestRenewalWorkspaceEndpoint:

    def test_endpoint_200(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "account_id": str(aid),
            "account_summary": {
                "account_name": "Apex Roofing",
                "industry": "roofing",
                "state": "NC",
                "account_stage": "renewal",
                "key_facts": ["27 employees"],
            },
            "operations_signals": {
                "company_identity": {"company_name": "Apex Roofing", "founded_year": 2012, "service_area": []},
                "operations_signals": ["Roof replacement"],
                "safety_signals": [],
                "scale_signals": [],
                "carrier_relevant_signals": [],
            },
            "risk_overview": {
                "risk_level": "moderate",
                "confidence": 0.55,
                "headline": "Moderate renewal complexity.",
            },
            "coverage_gaps": [
                {"coverage": "umbrella", "reason": "Missing for roofing", "risk_level": "high", "confidence": 0.85, "applied_rules": []},
            ],
            "producer_questions": ["Has the safety program been updated?"],
            "underwriter_narrative": {
                "email_version": "Dear Underwriter...",
                "memo_version": "**Apex Roofing Renewal**...",
                "style_applied": {},
            },
            "recommended_actions": ["Review umbrella exposure"],
            "sections_available": ["operations_signals", "risk_overview", "coverage_gaps", "underwriter_narrative", "recommended_actions"],
        }

        with patch("app.api.routes.build_renewal_workspace", return_value=mock_result):
            response = client.post(f"/api/v1/workspace/renewal/{aid}", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == str(aid)
        assert data["account_summary"]["account_name"] == "Apex Roofing"
        assert len(data["coverage_gaps"]) == 1
        assert len(data["sections_available"]) >= 1

    def test_endpoint_404(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "error": "Account not found",
            "account_id": str(aid),
        }

        with patch("app.api.routes.build_renewal_workspace", return_value=mock_result):
            response = client.post(f"/api/v1/workspace/renewal/{aid}", json={})

        assert response.status_code == 404

    def test_endpoint_with_options(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "account_id": str(aid),
            "account_summary": {"account_name": "Test", "industry": "", "state": "", "account_stage": "remarket", "key_facts": []},
            "operations_signals": {},
            "risk_overview": {"risk_level": "low", "confidence": 0.4, "headline": ""},
            "coverage_gaps": [],
            "producer_questions": [],
            "underwriter_narrative": {"email_version": "", "memo_version": "", "style_applied": {}},
            "recommended_actions": [],
            "sections_available": [],
        }

        with patch("app.api.routes.build_renewal_workspace", return_value=mock_result):
            response = client.post(f"/api/v1/workspace/renewal/{aid}", json={
                "account_stage": "remarket",
                "narrative_type": "new_business",
                "producer_id": "prod-123",
            })

        assert response.status_code == 200

    def test_endpoint_response_shape(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "account_id": str(aid),
            "account_summary": {"account_name": "X", "industry": "", "state": "", "account_stage": "renewal", "key_facts": []},
            "operations_signals": {},
            "risk_overview": {"risk_level": "low", "confidence": 0.4, "headline": ""},
            "coverage_gaps": [],
            "producer_questions": [],
            "underwriter_narrative": {"email_version": "", "memo_version": "", "style_applied": {}},
            "recommended_actions": [],
            "sections_available": [],
        }

        with patch("app.api.routes.build_renewal_workspace", return_value=mock_result):
            response = client.post(f"/api/v1/workspace/renewal/{aid}", json={})

        data = response.json()
        expected_keys = {
            "account_id", "account_summary", "operations_signals",
            "risk_overview", "coverage_gaps", "producer_questions",
            "underwriter_narrative", "recommended_actions",
            "sections_available", "error",
        }
        assert set(data.keys()) == expected_keys


# ============================================================
# REGRESSION TESTS
# ============================================================


class TestRegressions:

    def test_renewal_brief_standalone(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({"industry": "roofing", "state": "TX"})
        assert "account_summary" in result
        assert "risk_overview" in result
        assert "coverage_gaps" in result

    def test_coverage_gap_standalone(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({"industry": "roofing", "state": "TX"})
        assert len(result["coverage_gaps"]) >= 1

    def test_narrative_standalone(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing"})
        assert "email_version" in result

    def test_public_web_intel_standalone(self):
        from app.services.public_web_intel import extract_public_web_intel
        result = extract_public_web_intel({
            "company_name": "Test",
            "raw_website_text": "Residential roof replacement services.",
        })
        assert result["company_identity"]["company_name"] == "Test"
