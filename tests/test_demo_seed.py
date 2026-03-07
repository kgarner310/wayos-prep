"""Tests for Phase 13: Demo Seed, Reset, Admin Endpoints, Friction Fixes."""

import uuid
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# DEMO SEED SERVICE
# ============================================================


class TestDemoSeedService:

    def test_demo_accounts_data_complete(self):
        from app.services.demo_seed_service import DEMO_ACCOUNTS
        assert len(DEMO_ACCOUNTS) == 4
        for acct in DEMO_ACCOUNTS:
            assert acct["account_name"]
            assert acct["industry"]
            assert acct["state"]
            assert acct["employee_count"] > 0
            assert acct["annual_revenue"] > 0
            assert "current_coverages" in acct
            assert len(acct["current_coverages"]) >= 2
            assert acct.get("website_url")
            assert "[DEMO-SEED]" in acct["notes"]

    def test_demo_accounts_have_unique_industries(self):
        from app.services.demo_seed_service import DEMO_ACCOUNTS
        industries = [a["industry"] for a in DEMO_ACCOUNTS]
        assert len(set(industries)) == 4

    def test_seed_creates_accounts(self):
        from app.services.demo_seed_service import seed_demo_accounts
        db = MagicMock()
        # No existing accounts
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        results = seed_demo_accounts(db)
        assert len(results) == 4
        assert all(r["status"] == "created" for r in results)
        # 4 accounts + 1 log_event
        assert db.add.call_count >= 4
        db.commit.assert_called()

    def test_seed_skips_existing(self):
        from app.services.demo_seed_service import seed_demo_accounts
        db = MagicMock()
        existing = MagicMock()
        existing.id = uuid.uuid4()
        existing.account_name = "Summit Ridge Roofing LLC"
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = existing

        results = seed_demo_accounts(db)
        assert len(results) == 4
        assert all(r["status"] == "already_exists" for r in results)
        # Only log_event adds, no accounts
        assert db.add.call_count <= 1

    def test_reset_clears_demo_data(self):
        from app.services.demo_seed_service import reset_demo_data
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.delete.return_value = 0
        db.query.return_value.filter.return_value.in_.return_value = MagicMock()
        db.query.return_value.delete.return_value = 3

        result = reset_demo_data(db)
        assert "accounts_deleted" in result
        assert "artifacts_deleted" in result
        assert "feedback_deleted" in result
        db.commit.assert_called()

    def test_list_demo_scenarios(self):
        from app.services.demo_seed_service import list_demo_scenarios
        scenarios = list_demo_scenarios()
        assert len(scenarios) == 4
        for s in scenarios:
            assert s["account_name"]
            assert s["industry"]
            assert s["key_exposures"]
            assert s["likely_gaps"]
            assert s["demo_story"]

    def test_demo_scenarios_have_gaps(self):
        from app.services.demo_seed_service import list_demo_scenarios
        scenarios = list_demo_scenarios()
        for s in scenarios:
            assert len(s["likely_gaps"]) >= 1, f"{s['industry']} should have coverage gaps"

    def test_get_demo_accounts_empty(self):
        from app.services.demo_seed_service import get_demo_accounts
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = get_demo_accounts(db)
        assert result == []

    def test_get_demo_accounts_returns_info(self):
        from app.services.demo_seed_service import get_demo_accounts
        db = MagicMock()
        mock_acct = MagicMock()
        mock_acct.id = uuid.uuid4()
        mock_acct.account_name = "Test Co"
        mock_acct.industry = "roofing"
        mock_acct.state = "NC"
        mock_acct.employee_count = 10
        mock_acct.website_url = "https://test.com"
        mock_acct.current_coverages = ["gl", "wc"]
        mock_acct.last_public_intel_refresh_at = None
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_acct]

        result = get_demo_accounts(db)
        assert len(result) == 1
        assert result[0]["account_name"] == "Test Co"
        assert result[0]["has_website"] is True
        assert result[0]["coverage_count"] == 2
        assert result[0]["has_intel"] is False


# ============================================================
# DEMO ADMIN ENDPOINTS
# ============================================================


class TestDemoAdminEndpoints:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch("app.api.routes.seed_demo_accounts")
    def test_seed_endpoint(self, mock_seed, client):
        mock_seed.return_value = [
            {"account_id": str(uuid.uuid4()), "account_name": "Test", "status": "created"},
        ]
        resp = client.post("/api/v1/demo/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["total"] == 1

    @patch("app.api.routes.reset_demo_data")
    def test_reset_endpoint(self, mock_reset, client):
        mock_reset.return_value = {
            "accounts_deleted": 4,
            "artifacts_deleted": 2,
            "feedback_deleted": 1,
            "events_deleted": 5,
        }
        resp = client.post("/api/v1/demo/reset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "reset_complete"
        assert data["accounts_deleted"] == 4

    @patch("app.api.routes.list_demo_scenarios")
    def test_scenarios_endpoint(self, mock_scenarios, client):
        mock_scenarios.return_value = [
            {"account_name": "Test", "industry": "roofing", "state": "NC",
             "employee_count": 10, "annual_revenue": 1000000,
             "key_exposures": ["falls"], "likely_gaps": ["umbrella"],
             "demo_story": "Test story"},
        ]
        resp = client.get("/api/v1/demo/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["scenarios"][0]["industry"] == "roofing"

    @patch("app.api.routes.get_demo_accounts")
    def test_demo_accounts_endpoint(self, mock_accts, client):
        mock_accts.return_value = []
        resp = client.get("/api/v1/demo/accounts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_feedback_list_endpoint(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value \
            .limit.return_value.all.return_value = []
        resp = client.get("/api/v1/demo/feedback-list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_feedback_list_with_hours(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value \
            .limit.return_value.all.return_value = []
        resp = client.get("/api/v1/demo/feedback-list?hours=48&limit=10")
        assert resp.status_code == 200


# ============================================================
# DEMO NOTES TAG
# ============================================================


class TestDemoNotesTag:

    def test_tag_is_consistent(self):
        from app.services.demo_seed_service import DEMO_NOTES_TAG, DEMO_ACCOUNTS
        for acct in DEMO_ACCOUNTS:
            assert DEMO_NOTES_TAG in acct["notes"]

    def test_tag_value(self):
        from app.services.demo_seed_service import DEMO_NOTES_TAG
        assert DEMO_NOTES_TAG == "[DEMO-SEED]"


# ============================================================
# KEY EXPOSURES AND GAPS
# ============================================================


class TestExposuresAndGaps:

    def test_roofing_exposures(self):
        from app.services.demo_seed_service import _get_key_exposures
        exposures = _get_key_exposures("roofing")
        assert len(exposures) >= 3
        assert any("fall" in e.lower() for e in exposures)

    def test_restaurant_exposures(self):
        from app.services.demo_seed_service import _get_key_exposures
        exposures = _get_key_exposures("restaurant")
        assert len(exposures) >= 3

    def test_unknown_industry_exposures(self):
        from app.services.demo_seed_service import _get_key_exposures
        exposures = _get_key_exposures("unknown_industry")
        assert exposures == ["general operations"]

    def test_roofing_gaps_exclude_existing(self):
        from app.services.demo_seed_service import _get_likely_gaps
        acct = {
            "industry": "roofing",
            "current_coverages": ["general_liability", "workers_comp", "inland_marine"],
        }
        gaps = _get_likely_gaps(acct)
        assert "inland_marine" not in gaps
        assert "umbrella" in gaps

    def test_restaurant_gaps(self):
        from app.services.demo_seed_service import _get_likely_gaps, DEMO_ACCOUNTS
        restaurant = next(a for a in DEMO_ACCOUNTS if a["industry"] == "restaurant")
        gaps = _get_likely_gaps(restaurant)
        assert "epli" in gaps
        assert "cyber_liability" in gaps

    def test_demo_story_exists(self):
        from app.services.demo_seed_service import _get_demo_story
        for industry in ["roofing", "landscaping", "hvac", "restaurant"]:
            story = _get_demo_story(industry)
            assert len(story) > 10

    def test_unknown_demo_story(self):
        from app.services.demo_seed_service import _get_demo_story
        story = _get_demo_story("widget_manufacturing")
        assert "demo" in story.lower()


# ============================================================
# REGRESSIONS
# ============================================================


class TestPhase13Regressions:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_coverage_gaps_still_works(self, client):
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp"],
        })
        assert resp.status_code == 200

    def test_auth_me_still_requires_token(self, client, mock_db):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_demo_event_still_works(self, client, mock_db):
        resp = client.post("/api/v1/demo/event", json={
            "event_type": "test_event",
            "session_id": "test",
        })
        assert resp.status_code == 200

    def test_demo_session_summary_still_works(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value \
            .count.return_value = 0
        resp = client.get("/api/v1/demo/session-summary?session_id=test")
        assert resp.status_code == 200

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_still_works(self, mock_log, mock_workspace, client):
        mock_workspace.return_value = {
            "account_id": str(uuid.uuid4()),
            "account_summary": {"account_name": "Test"},
            "operations_signals": {},
            "risk_overview": {},
            "coverage_gaps": [],
            "producer_questions": [],
            "underwriter_narrative": {},
            "recommended_actions": [],
            "sections_available": [],
        }
        resp = client.post(f"/api/v1/packet/submission/{uuid.uuid4()}", json={})
        assert resp.status_code == 200
