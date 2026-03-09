"""Tests for Phase 11: Submission Packet, Renderer, Endpoint, Demo Polish."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# SUBMISSION PACKET SERVICE — unit tests
# ============================================================


MOCK_WORKSPACE = {
    "account_id": str(uuid.uuid4()),
    "account_summary": {
        "account_name": "Acme Roofing",
        "industry": "roofing",
        "state": "TX",
        "account_stage": "renewal",
        "key_facts": ["25 employees", "$2.5M revenue"],
    },
    "operations_signals": {
        "company_identity": {},
        "operations_signals": ["Roof replacement services"],
        "safety_signals": ["OSHA training mentioned"],
        "scale_signals": [],
        "carrier_relevant_signals": [],
    },
    "risk_overview": {
        "risk_level": "moderate",
        "confidence": 0.72,
        "headline": "Elevated risk from heights exposure",
        "contributing_factors": ["Heights work", "Subcontractor use"],
        "signal_count": 4,
    },
    "coverage_gaps": [
        {
            "coverage": "Umbrella / Excess Liability",
            "reason": "Industry standard for roofing contractors",
            "risk_level": "high",
            "confidence": 0.85,
            "applied_rules": [],
            "why_this_is_here": ["Industry-expected coverage for roofing"],
        },
    ],
    "producer_questions": [
        "Do you use subcontractors for any roofing work?",
        "What safety training protocols are in place?",
    ],
    "underwriter_narrative": {
        "email_version": "Subject: Renewal – Acme Roofing\n\nBody text here.",
        "memo_version": "Memo version text here.",
        "style_applied": {},
        "fact_sources": {},
        "source_signals": ["Website references: OSHA training"],
    },
    "recommended_actions": [
        "Request current certificates of insurance",
        "Confirm subcontractor agreements",
    ],
    "sections_available": [
        "operations_signals",
        "risk_overview",
        "coverage_gaps",
        "underwriter_narrative",
        "recommended_actions",
    ],
}


class TestSubmissionPacketService:

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_build_packet_full_data(self, mock_log, mock_workspace):
        mock_workspace.return_value = MOCK_WORKSPACE
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4())

        assert result["packet_title"].startswith("Submission Packet")
        assert "Acme Roofing" in result["packet_title"]
        assert "roofing" in result["packet_title"]
        assert len(result["sections"]) >= 4
        assert result["rendered_text"]
        assert result["rendered_markdown"]
        assert result["account_id"] == MOCK_WORKSPACE["account_id"]

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_build_packet_error_passthrough(self, mock_log, mock_workspace):
        mock_workspace.return_value = {"error": "Account not found", "account_id": "xxx"}
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4())
        assert result["error"] == "Account not found"

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_build_packet_without_questions(self, mock_log, mock_workspace):
        mock_workspace.return_value = MOCK_WORKSPACE
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4(), {"include_questions": False})
        assert result["producer_questions"] == []

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_build_packet_without_gaps(self, mock_log, mock_workspace):
        mock_workspace.return_value = MOCK_WORKSPACE
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4(), {"include_gaps": False})
        assert result["coverage_gaps"] == []

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_build_packet_without_public_intel(self, mock_log, mock_workspace):
        mock_workspace.return_value = MOCK_WORKSPACE
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4(), {"include_public_intel": False})
        assert result.get("operations_signals") is None

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_section_titles(self, mock_log, mock_workspace):
        mock_workspace.return_value = MOCK_WORKSPACE
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4())
        titles = [s["title"] for s in result["sections"]]
        assert "Account Summary" in titles
        assert "Risk Overview" in titles
        assert "Coverage Gaps" in titles
        assert "Underwriter Narrative" in titles

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_minimal_workspace(self, mock_log, mock_workspace):
        """Packet handles workspace with minimal data gracefully."""
        mock_workspace.return_value = {
            "account_id": str(uuid.uuid4()),
            "account_summary": {"account_name": "Minimal Co"},
            "operations_signals": {},
            "risk_overview": {},
            "coverage_gaps": [],
            "producer_questions": [],
            "underwriter_narrative": {},
            "recommended_actions": [],
            "sections_available": [],
        }
        db = MagicMock()

        from app.services.submission_packet_service import build_submission_packet
        result = build_submission_packet(db, uuid.uuid4())
        assert result["packet_title"].startswith("Submission Packet")
        assert len(result["sections"]) >= 1  # at least account summary


# ============================================================
# RENDERER — unit tests
# ============================================================


class TestSubmissionPacketRenderer:

    def test_render_plain_text(self):
        from app.services.submission_packet_renderer import render_plain_text
        sections = [
            {"title": "Summary", "content_type": "text", "body": "Test body", "items": ["fact1"]},
            {"title": "Gaps", "content_type": "list", "body": "", "items": ["gap1", "gap2"]},
        ]
        text = render_plain_text("Test Packet", sections, {})
        assert "TEST PACKET" in text
        assert "SUMMARY" in text
        assert "Test body" in text
        assert "- fact1" in text
        assert "- gap1" in text

    def test_render_markdown(self):
        from app.services.submission_packet_renderer import render_markdown
        sections = [
            {"title": "Summary", "content_type": "text", "body": "Test body", "items": []},
            {"title": "Gaps", "content_type": "list", "body": "", "items": ["gap1"]},
        ]
        md = render_markdown("Test Packet", sections, {})
        assert "# Test Packet" in md
        assert "## Summary" in md
        assert "Test body" in md
        assert "- gap1" in md

    def test_render_empty_sections(self):
        from app.services.submission_packet_renderer import render_plain_text, render_markdown
        text = render_plain_text("Empty", [], {})
        md = render_markdown("Empty", [], {})
        assert "EMPTY" in text
        assert "# Empty" in md


# ============================================================
# ENDPOINT — integration tests
# ============================================================


class TestSubmissionPacketEndpoint:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_endpoint_200(self, mock_log, mock_workspace, client):
        mock_workspace.return_value = MOCK_WORKSPACE
        account_id = uuid.uuid4()
        resp = client.post(f"/api/v1/packet/submission/{account_id}", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["packet_title"]
        assert data["rendered_text"]
        assert data["rendered_markdown"]
        assert len(data["sections"]) >= 4

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_endpoint_404(self, mock_log, mock_workspace, client):
        mock_workspace.return_value = {"error": "Account not found", "account_id": "xxx"}
        resp = client.post(f"/api/v1/packet/submission/{uuid.uuid4()}", json={})
        assert resp.status_code == 404

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_endpoint_response_shape(self, mock_log, mock_workspace, client):
        mock_workspace.return_value = MOCK_WORKSPACE
        resp = client.post(f"/api/v1/packet/submission/{uuid.uuid4()}", json={})
        data = resp.json()
        required_keys = {
            "account_id", "packet_title", "account_summary", "risk_overview",
            "coverage_gaps", "producer_questions", "underwriter_narrative",
            "recommended_actions", "sections", "rendered_text", "rendered_markdown",
            "sections_available",
        }
        assert required_keys.issubset(set(data.keys()))

    @patch("app.services.submission_packet_service.build_renewal_workspace")
    @patch("app.services.submission_packet_service.log_event")
    def test_packet_with_options(self, mock_log, mock_workspace, client):
        mock_workspace.return_value = MOCK_WORKSPACE
        resp = client.post(f"/api/v1/packet/submission/{uuid.uuid4()}", json={
            "include_questions": False,
            "include_gaps": False,
            "include_public_intel": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["coverage_gaps"] == []
        assert data["producer_questions"] == []


# ============================================================
# REGRESSIONS — existing endpoints still work
# ============================================================


class TestPhase11Regressions:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_health_still_works(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_workspace_endpoint_still_works(self, client, mock_db):
        """Workspace endpoint is not broken by packet additions."""
        with patch("app.services.renewal_workspace_service.get_account") as mock_acct, \
             patch("app.services.renewal_workspace_service.get_latest_public_intel", return_value=None), \
             patch("app.services.renewal_workspace_service.log_event"):
            acct = MagicMock()
            acct.account_name = "Test"
            acct.industry = "roofing"
            acct.state = "TX"
            acct.employee_count = 10
            acct.annual_revenue = 1000000
            acct.vehicle_count = 3
            acct.uses_subcontractors = False
            acct.current_coverages = ["workers_comp"]
            acct.website_url = None
            acct.notes = ""
            mock_acct.return_value = acct

            resp = client.post(f"/api/v1/workspace/renewal/{uuid.uuid4()}", json={})
            assert resp.status_code == 200

    def test_coverage_gaps_still_works(self, client):
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp"],
        })
        assert resp.status_code == 200

    def test_public_web_intel_still_works(self, client, mock_db):
        resp = client.post("/api/v1/intel/public-web-intel", json={
            "company_name": "Test",
            "raw_website_text": "OSHA safety training for crews.",
        })
        assert resp.status_code == 200

    def test_auth_login_still_works(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        resp = client.post("/api/v1/auth/login", json={
            "email": "noone@test.com",
            "password": "bad",
        })
        assert resp.status_code == 401


# ============================================================
# SCHEMA — validation
# ============================================================


class TestSubmissionPacketSchema:

    def test_request_defaults(self):
        from app.schemas.submission_packet import SubmissionPacketRequest
        req = SubmissionPacketRequest()
        assert req.include_public_intel is True
        assert req.include_questions is True
        assert req.include_gaps is True
        assert req.narrative_type == "renewal"

    def test_response_model(self):
        from app.schemas.submission_packet import SubmissionPacketResponse
        resp = SubmissionPacketResponse(
            account_id="abc",
            packet_title="Test Packet",
            rendered_text="text",
            rendered_markdown="# text",
        )
        assert resp.packet_title == "Test Packet"
        assert resp.sections == []
        assert resp.coverage_gaps == []
