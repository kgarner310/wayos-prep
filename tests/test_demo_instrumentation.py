"""Tests for Phase 12: Demo Instrumentation, Session Summaries, Feedback."""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# MODELS
# ============================================================


class TestModels:

    def test_event_log_has_session_id(self):
        from app.models.models import EventLog
        cols = {c.name for c in EventLog.__table__.columns}
        assert "session_id" in cols

    def test_demo_feedback_model_exists(self):
        from app.models.models import DemoFeedback
        assert DemoFeedback.__tablename__ == "demo_feedback"
        cols = {c.name for c in DemoFeedback.__table__.columns}
        expected = {"id", "user_id", "agency_id", "session_id", "account_id",
                    "would_use_before_meeting", "most_useful_part",
                    "unclear_or_untrustworthy", "what_next", "overall_rating",
                    "notes", "created_at"}
        assert expected.issubset(cols)


# ============================================================
# INSTRUMENTATION
# ============================================================


class TestInstrumentation:

    def test_log_event_with_session_id(self):
        from app.services.instrumentation import log_event
        db = MagicMock()
        log_event(db, "test_event", payload={"key": "val"}, session_id="sess_123")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        event = db.add.call_args[0][0]
        assert event.event_type == "test_event"
        assert event.session_id == "sess_123"

    def test_log_event_without_session_id(self):
        from app.services.instrumentation import log_event
        db = MagicMock()
        log_event(db, "basic_event")
        db.add.assert_called_once()
        event = db.add.call_args[0][0]
        assert event.session_id is None


# ============================================================
# DEMO SESSION SERVICE
# ============================================================


class TestDemoSessionService:

    def _make_event(self, event_type, session_id="s1", minutes_ago=0):
        e = MagicMock()
        e.event_type = event_type
        e.session_id = session_id
        e.user_id = "user1"
        e.event_payload = {}
        e.created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        return e

    def test_summary_with_events(self):
        from app.services.demo_session_service import build_demo_session_summary
        db = MagicMock()

        events = [
            self._make_event("demo_session_started", minutes_ago=10),
            self._make_event("account_selected", minutes_ago=9),
            self._make_event("workspace_generated", minutes_ago=8),
            self._make_event("public_intel_refreshed", minutes_ago=7),
            self._make_event("submission_packet_generated", minutes_ago=5),
            self._make_event("narrative_copied", minutes_ago=4),
            self._make_event("packet_copied", minutes_ago=3),
        ]

        db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = events
        db.query.return_value.filter.return_value.filter.return_value \
            .count.return_value = 1

        result = build_demo_session_summary(db, session_id="s1")

        assert result["event_count"] == 7
        assert "demo_session_started" in result["actions_completed"]
        assert "workspace_generated" in result["actions_completed"]
        assert "submission_packet_generated" in result["actions_completed"]
        assert result["copy_actions"] == 2
        assert result["public_intel_refreshed_before_packet"] is True
        assert result["time_to_first_workspace_seconds"] is not None
        assert result["time_to_first_packet_seconds"] is not None
        assert len(result["timeline"]) == 7

    def test_summary_empty(self):
        from app.services.demo_session_service import build_demo_session_summary
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []

        result = build_demo_session_summary(db, session_id="empty")
        assert result["event_count"] == 0
        assert result["actions_completed"] == []
        assert result["copy_actions"] == 0

    def test_summary_no_intel_before_packet(self):
        from app.services.demo_session_service import build_demo_session_summary
        db = MagicMock()

        events = [
            self._make_event("workspace_generated", minutes_ago=5),
            self._make_event("submission_packet_generated", minutes_ago=3),
        ]
        db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = events
        db.query.return_value.filter.return_value.filter.return_value \
            .count.return_value = 0

        result = build_demo_session_summary(db, session_id="s2")
        assert result["public_intel_refreshed_before_packet"] is False

    def test_list_recent_sessions(self):
        from app.services.demo_session_service import list_recent_sessions
        db = MagicMock()

        events = [
            self._make_event("workspace_generated", session_id="s1", minutes_ago=5),
            self._make_event("account_selected", session_id="s1", minutes_ago=10),
            self._make_event("workspace_generated", session_id="s2", minutes_ago=2),
        ]
        db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = events

        result = list_recent_sessions(db)
        assert len(result) == 2
        session_ids = {s["session_id"] for s in result}
        assert "s1" in session_ids
        assert "s2" in session_ids


# ============================================================
# ENDPOINTS
# ============================================================


class TestDemoEndpoints:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_log_demo_event(self, client, mock_db):
        resp = client.post("/api/v1/demo/event", json={
            "event_type": "workspace_generated",
            "session_id": "test_session",
            "payload": {"account_id": "abc"},
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_submit_demo_feedback(self, client, mock_db):
        resp = client.post("/api/v1/demo/feedback", json={
            "session_id": "test_session",
            "would_use_before_meeting": "definitely",
            "most_useful_part": "coverage gaps",
            "overall_rating": 4,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["overall_rating"] == 4

    def test_session_summary_endpoint(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value \
            .count.return_value = 0

        resp = client.get("/api/v1/demo/session-summary?session_id=test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_count"] == 0
        assert "actions_completed" in data

    def test_recent_sessions_endpoint(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []

        resp = client.get("/api/v1/demo/recent-sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0


# ============================================================
# SCHEMAS
# ============================================================


class TestDemoSchemas:

    def test_feedback_request_defaults(self):
        from app.schemas.demo import DemoFeedbackRequest
        req = DemoFeedbackRequest()
        assert req.session_id is None
        assert req.overall_rating is None

    def test_session_summary_response(self):
        from app.schemas.demo import DemoSessionSummaryResponse
        resp = DemoSessionSummaryResponse(event_count=5, copy_actions=2)
        assert resp.event_count == 5
        assert resp.copy_actions == 2
        assert resp.timeline == []

    def test_instrument_event_request(self):
        from app.schemas.demo import InstrumentEventRequest
        req = InstrumentEventRequest(event_type="test", session_id="s1")
        assert req.event_type == "test"


# ============================================================
# REGRESSIONS
# ============================================================


class TestPhase12Regressions:

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

    def test_auth_me_still_requires_token(self, mock_db):
        # Use a client without the conftest auth bypass
        from app.api.deps import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_db] = lambda: mock_db
        c = TestClient(app)
        resp = c.get("/api/v1/auth/me")
        assert resp.status_code == 401

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
