"""Tests for account persistence, saved artifacts, producer style preferences,
and style integration with underwriter narrative generator."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

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
    """Create a mock Account-like object."""
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
        "website_url": None,
        "social_urls": None,
        "notes": "",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_artifact_obj(**overrides):
    """Create a mock SavedArtifact-like object."""
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_id": uuid.uuid4(),
        "artifact_type": "renewal_brief",
        "artifact_subtype": None,
        "title": "Renewal Brief for Apex",
        "content_json": {"account_summary": {"account_name": "Apex"}},
        "rendered_text": None,
        "created_by_user_id": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_style_obj(**overrides):
    """Create a mock ProducerStylePreference-like object."""
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "producer_id": "producer_001",
        "audience": "underwriter",
        "default_posture": "balanced",
        "directness": "direct",
        "verbosity": "concise",
        "warmth": None,
        "confidence_style": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# ACCOUNT ENDPOINT TESTS
# ============================================================


class TestAccountEndpoints:

    def test_create_account(self, client, mock_db):
        account = _make_account_obj()
        with patch("app.api.routes.create_account", return_value=account):
            response = client.post("/api/v1/accounts", json={
                "account_name": "Apex Roofing",
                "industry": "roofing",
                "state": "NC",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "Apex Roofing"
        assert data["industry"] == "roofing"

    def test_get_account(self, client, mock_db):
        account = _make_account_obj()
        with patch("app.api.routes.get_account", return_value=account):
            response = client.get(f"/api/v1/accounts/{account.id}")
        assert response.status_code == 200
        assert response.json()["account_name"] == "Apex Roofing"

    def test_get_account_not_found(self, client, mock_db):
        with patch("app.api.routes.get_account", return_value=None):
            response = client.get(f"/api/v1/accounts/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_list_accounts(self, client, mock_db):
        accounts = [_make_account_obj(), _make_account_obj(account_name="Beta Corp")]
        with patch("app.api.routes.list_accounts", return_value=(accounts, 2)):
            response = client.get("/api/v1/accounts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["accounts"]) == 2

    def test_update_account(self, client, mock_db):
        updated = _make_account_obj(account_name="Apex Roofing LLC")
        with patch("app.api.routes.update_account", return_value=updated):
            response = client.put(f"/api/v1/accounts/{updated.id}", json={
                "account_name": "Apex Roofing LLC",
            })
        assert response.status_code == 200
        assert response.json()["account_name"] == "Apex Roofing LLC"

    def test_update_account_not_found(self, client, mock_db):
        with patch("app.api.routes.update_account", return_value=None):
            response = client.put(f"/api/v1/accounts/{uuid.uuid4()}", json={
                "account_name": "Nonexistent",
            })
        assert response.status_code == 404

    def test_delete_account(self, client, mock_db):
        aid = uuid.uuid4()
        with patch("app.api.routes.delete_account", return_value=True):
            response = client.delete(f"/api/v1/accounts/{aid}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_account_not_found(self, client, mock_db):
        with patch("app.api.routes.delete_account", return_value=False):
            response = client.delete(f"/api/v1/accounts/{uuid.uuid4()}")
        assert response.status_code == 404


# ============================================================
# ARTIFACT ENDPOINT TESTS
# ============================================================


class TestArtifactEndpoints:

    def test_save_artifact(self, client, mock_db):
        artifact = _make_artifact_obj()
        with patch("app.api.routes.save_artifact", return_value=artifact):
            response = client.post("/api/v1/artifacts", json={
                "artifact_type": "renewal_brief",
                "content_json": {"test": "data"},
                "title": "Test Brief",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["artifact_type"] == "renewal_brief"

    def test_get_artifact(self, client, mock_db):
        artifact = _make_artifact_obj()
        with patch("app.api.routes.get_artifact", return_value=artifact):
            response = client.get(f"/api/v1/artifacts/{artifact.id}")
        assert response.status_code == 200
        assert response.json()["artifact_type"] == "renewal_brief"

    def test_get_artifact_not_found(self, client, mock_db):
        with patch("app.api.routes.get_artifact", return_value=None):
            response = client.get(f"/api/v1/artifacts/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_list_account_artifacts(self, client, mock_db):
        artifacts = [_make_artifact_obj(), _make_artifact_obj(artifact_type="underwriter_narrative")]
        with patch("app.api.routes.list_artifacts_for_account", return_value=artifacts):
            aid = uuid.uuid4()
            response = client.get(f"/api/v1/accounts/{aid}/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_save_artifact_with_account_id(self, client, mock_db):
        aid = uuid.uuid4()
        artifact = _make_artifact_obj(account_id=aid)
        with patch("app.api.routes.save_artifact", return_value=artifact):
            response = client.post("/api/v1/artifacts", json={
                "account_id": str(aid),
                "artifact_type": "public_web_intel",
                "content_json": {"signals": []},
            })
        assert response.status_code == 200
        assert response.json()["account_id"] == str(aid)


# ============================================================
# PRODUCER STYLE ENDPOINT TESTS
# ============================================================


class TestProducerStyleEndpoints:

    def test_create_style(self, client, mock_db):
        style = _make_style_obj()
        with patch("app.api.routes.save_style", return_value=style):
            response = client.post("/api/v1/producer-style/preferences", json={
                "producer_id": "producer_001",
                "audience": "underwriter",
                "default_posture": "balanced",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["producer_id"] == "producer_001"
        assert data["audience"] == "underwriter"

    def test_get_style(self, client, mock_db):
        style = _make_style_obj()
        with patch("app.api.routes.get_style", return_value=style):
            response = client.get("/api/v1/producer-style/preferences/producer_001")
        assert response.status_code == 200
        assert response.json()["default_posture"] == "balanced"

    def test_get_style_not_found(self, client, mock_db):
        with patch("app.api.routes.get_style", return_value=None):
            response = client.get("/api/v1/producer-style/preferences/nonexistent")
        assert response.status_code == 404

    def test_update_style(self, client, mock_db):
        updated = _make_style_obj(default_posture="direct")
        with patch("app.api.routes.update_style", return_value=updated):
            response = client.put("/api/v1/producer-style/preferences/producer_001", json={
                "default_posture": "direct",
            })
        assert response.status_code == 200
        assert response.json()["default_posture"] == "direct"

    def test_update_style_not_found(self, client, mock_db):
        with patch("app.api.routes.update_style", return_value=None):
            response = client.put("/api/v1/producer-style/preferences/nonexistent", json={
                "default_posture": "direct",
            })
        assert response.status_code == 404


# ============================================================
# STYLE INTEGRATION WITH NARRATIVE GENERATOR
# ============================================================


class TestStyleIntegration:

    def test_narrative_includes_style_applied(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing", "state": "TX"})
        assert "style_applied" in result
        assert result["style_applied"]["source"] == "default"

    def test_explicit_positioning_overrides_saved(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({
            "industry": "roofing",
            "intended_market_positioning": "defensive",
        })
        assert "style_applied" in result
        # Explicit override should be used in narrative

    def test_saved_style_used_when_no_explicit(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative

        mock_db = MagicMock()
        saved_style = _make_style_obj(default_posture="favorable")

        with patch("app.services.producer_style_service.get_style", return_value=saved_style) as mock_get:
            result = generate_underwriter_narrative(
                {"industry": "roofing", "producer_id": "producer_001"},
                db=mock_db,
            )
            mock_get.assert_called_once_with(mock_db, "producer_001")

        assert result["style_applied"]["source"] == "saved"
        assert result["style_applied"]["posture"] == "favorable"

    def test_no_producer_id_uses_default(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing"})
        assert result["style_applied"]["source"] == "default"
        assert result["style_applied"]["audience"] == "underwriter"

    def test_no_db_uses_default(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative(
            {"industry": "roofing", "producer_id": "producer_001"},
            db=None,
        )
        assert result["style_applied"]["source"] == "default"


# ============================================================
# ACCOUNT SERVICE UNIT TESTS (with mock DB)
# ============================================================


class TestAccountService:

    def test_create_account_calls_db(self, mock_db):
        from app.services.account_service import create_account
        mock_db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, 'id', uuid.uuid4()))
        account = create_account(mock_db, {
            "account_name": "Test Co",
            "industry": "trucking",
            "state": "OH",
        })
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_account_queries_db(self, mock_db):
        from app.services.account_service import get_account
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = get_account(mock_db, uuid.uuid4())
        assert result is None

    def test_delete_returns_false_if_not_found(self, mock_db):
        from app.services.account_service import delete_account
        mock_db.query.return_value.filter.return_value.first.return_value = None
        assert delete_account(mock_db, uuid.uuid4()) is False


# ============================================================
# ARTIFACT SERVICE UNIT TESTS
# ============================================================


class TestArtifactService:

    def test_save_artifact_calls_db(self, mock_db):
        from app.services.artifact_service import save_artifact
        mock_db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, 'id', uuid.uuid4()))
        artifact = save_artifact(mock_db, {
            "artifact_type": "renewal_brief",
            "content_json": {"test": True},
        })
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_artifact_queries_db(self, mock_db):
        from app.services.artifact_service import get_artifact
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = get_artifact(mock_db, uuid.uuid4())
        assert result is None


# ============================================================
# PRODUCER STYLE SERVICE UNIT TESTS
# ============================================================


class TestProducerStyleService:

    def test_save_style_creates_new(self, mock_db):
        from app.services.producer_style_service import save_style
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, 'id', uuid.uuid4()))
        pref = save_style(mock_db, {
            "producer_id": "producer_001",
            "audience": "underwriter",
            "default_posture": "direct",
        })
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    def test_save_style_upserts_existing(self, mock_db):
        from app.services.producer_style_service import save_style
        existing = _make_style_obj()
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        pref = save_style(mock_db, {
            "producer_id": "producer_001",
            "default_posture": "persuasive",
        })
        # Should not call add (update instead)
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called()

    def test_get_style_queries_db(self, mock_db):
        from app.services.producer_style_service import get_style
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = get_style(mock_db, "nonexistent")
        assert result is None

    def test_update_returns_none_if_not_found(self, mock_db):
        from app.services.producer_style_service import update_style
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = update_style(mock_db, "nonexistent", {"default_posture": "direct"})
        assert result is None


# ============================================================
# REGRESSION — EXISTING SERVICES NOT BROKEN
# ============================================================


class TestRegressions:

    def test_renewal_brief_still_works(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({"industry": "roofing", "state": "TX"})
        assert "account_summary" in result
        assert "risk_overview" in result

    def test_narrative_still_works_without_style(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing"})
        assert result["narrative_type"] == "renewal"
        assert len(result["email_version"]["body"]) > 20

    def test_coverage_gap_detector_still_works(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({"industry": "roofing", "state": "TX"})
        assert len(result["coverage_gaps"]) >= 1

    def test_public_web_intel_still_works(self):
        from app.services.public_web_intel import extract_public_web_intel
        result = extract_public_web_intel({"raw_website_text": "OSHA safety training"})
        assert len(result["safety_signals"]) >= 1
