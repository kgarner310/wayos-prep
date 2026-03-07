"""Tests for Account Memory Ledger.

Tests cover:
- Service layer: create, list, summarize, write_memory_safe
- API endpoints: POST, GET list, GET summary
- Auto-write hooks: brief_generated, producer_feedback
- Validation: invalid entry_type
- Regressions
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

from fastapi.testclient import TestClient

from app.models.models import AccountMemoryEntry
from app.services.account_memory_service import (
    create_account_memory_entry,
    list_account_memory,
    summarize_account_memory,
    write_memory_safe,
    VALID_ENTRY_TYPES,
)
from app.db.session import get_db
from app.main import app


# ============================================================
# HELPERS
# ============================================================


def _make_entry(
    account_id="acct-1",
    entry_type="brief_generated",
    summary="Meeting brief generated for roofing contractor",
    industry="roofing contractor",
    agency_id=None,
    created_at=None,
):
    """Build a mock AccountMemoryEntry."""
    entry = MagicMock(spec=AccountMemoryEntry)
    entry.id = uuid.uuid4()
    entry.account_id = account_id
    entry.agency_id = agency_id
    entry.session_id = None
    entry.industry = industry
    entry.entry_type = entry_type
    entry.summary = summary
    entry.payload_json = {}
    entry.created_by = None
    entry.created_at = created_at or datetime.now(timezone.utc)
    return entry


# ============================================================
# SERVICE LAYER
# ============================================================


class TestCreateEntry:
    def test_create_entry(self):
        db = MagicMock()
        result = create_account_memory_entry(
            db=db,
            account_id="acct-1",
            entry_type="account_created",
            summary="Demo account created",
            industry="roofing contractor",
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_invalid_entry_type_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="Invalid entry_type"):
            create_account_memory_entry(
                db=db,
                account_id="acct-1",
                entry_type="invalid_type",
                summary="test",
            )

    def test_all_valid_entry_types(self):
        for et in VALID_ENTRY_TYPES:
            db = MagicMock()
            create_account_memory_entry(
                db=db, account_id="acct-1", entry_type=et, summary="test",
            )
            db.add.assert_called_once()


class TestListEntries:
    def test_list_by_account(self):
        db = MagicMock()
        entries = [_make_entry(), _make_entry(entry_type="account_created")]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = entries

        result = list_account_memory(db, "acct-1")
        assert len(result) == 2
        assert result[0]["entry_type"] == "brief_generated"

    def test_empty_list(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = list_account_memory(db, "acct-nonexistent")
        assert result == []


class TestSummarize:
    def test_empty_summary(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = summarize_account_memory(db, "acct-empty")
        assert result["total_entries"] == 0
        assert result["latest_entry_type"] is None

    def test_summary_with_entries(self):
        db = MagicMock()
        now = datetime.now(timezone.utc)
        entries = [
            _make_entry(entry_type="brief_generated", summary="Brief generated", created_at=now),
            _make_entry(entry_type="account_created", summary="Account created"),
            _make_entry(entry_type="outcome_logged", summary="Won the account"),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = entries

        result = summarize_account_memory(db, "acct-1")
        assert result["total_entries"] == 3
        assert result["latest_entry_type"] == "brief_generated"
        assert result["latest_summary"] == "Brief generated"
        assert result["latest_outcome"] == "Won the account"
        assert result["latest_brief_generated_at"] is not None
        assert result["entry_type_counts"]["brief_generated"] == 1
        assert result["entry_type_counts"]["account_created"] == 1

    def test_summary_no_outcome(self):
        db = MagicMock()
        entries = [_make_entry(entry_type="brief_generated")]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = entries

        result = summarize_account_memory(db, "acct-1")
        assert result["latest_outcome"] is None


class TestWriteMemorySafe:
    def test_safe_write_success(self):
        db = MagicMock()
        result = write_memory_safe(
            db, account_id="acct-1", entry_type="brief_generated",
            summary="Brief generated",
        )
        db.add.assert_called_once()

    def test_safe_write_on_exception(self):
        db = MagicMock()
        db.add.side_effect = Exception("db error")
        result = write_memory_safe(
            db, account_id="acct-1", entry_type="brief_generated",
            summary="Brief generated",
        )
        assert result is None  # No exception raised

    def test_safe_write_invalid_type(self):
        db = MagicMock()
        result = write_memory_safe(
            db, account_id="acct-1", entry_type="invalid",
            summary="test",
        )
        assert result is None  # ValueError caught safely


# ============================================================
# API ENDPOINTS
# ============================================================


class TestAccountMemoryEndpoints:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def test_client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_post_memory_entry(self, test_client, mock_db):
        resp = test_client.post("/api/v1/account-memory", json={
            "account_id": "acct-1",
            "entry_type": "account_created",
            "summary": "New account created",
            "industry": "roofing contractor",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        mock_db.add.assert_called()

    def test_post_memory_missing_fields(self, test_client):
        resp = test_client.post("/api/v1/account-memory", json={
            "account_id": "acct-1",
        })
        assert resp.status_code == 422

    def test_post_memory_invalid_type(self, test_client):
        resp = test_client.post("/api/v1/account-memory", json={
            "account_id": "acct-1",
            "entry_type": "invalid_type",
            "summary": "test",
        })
        assert resp.status_code == 422

    def test_get_memory_list(self, test_client, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            _make_entry(),
        ]
        resp = test_client.get("/api/v1/account-memory/acct-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_id"] == "acct-1"
        assert data["count"] == 1

    def test_get_memory_summary(self, test_client, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            _make_entry(entry_type="brief_generated"),
        ]
        resp = test_client.get("/api/v1/account-memory/acct-1/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] == 1
        assert data["latest_entry_type"] == "brief_generated"


# ============================================================
# AUTO-WRITE HOOKS
# ============================================================


class TestAutoWriteHooks:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def test_client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_brief_generates_memory_entry(self, test_client, mock_db):
        """Meeting brief with account_id should auto-write memory entry."""
        resp = test_client.get(
            "/api/v1/meeting/brief?industry=roofing+contractor&account_id=acct-123"
        )
        assert resp.status_code == 200
        # write_memory_safe calls db.add + db.commit
        assert mock_db.add.call_count >= 1

    def test_brief_without_account_id_no_memory(self, test_client, mock_db):
        """Meeting brief without account_id should not write memory."""
        resp = test_client.get(
            "/api/v1/meeting/brief?industry=roofing+contractor"
        )
        assert resp.status_code == 200
        # No memory write — db.add should not be called for memory
        assert mock_db.add.call_count == 0

    def test_feedback_with_account_writes_memory(self, test_client, mock_db):
        """Telemetry feedback with account_id should auto-write memory."""
        resp = test_client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "output_id": "out_abc",
            "feedback_type": "up",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
            "account_id": "acct-456",
            "industry": "roofing contractor",
        })
        assert resp.status_code == 200
        # Should have written a producer_feedback memory entry
        assert mock_db.add.call_count >= 1

    def test_edited_feedback_writes_producer_edited(self, test_client, mock_db):
        """Edited feedback should write producer_edited entry type."""
        resp = test_client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "output_id": "out_xyz",
            "feedback_type": "edited",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
            "account_id": "acct-789",
            "edited_text": "My edited version",
        })
        assert resp.status_code == 200
        # Verify the entry was attempted
        assert mock_db.add.call_count >= 1


# ============================================================
# REGRESSIONS
# ============================================================


class TestRegressions:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def test_client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_health(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12

    def test_meeting_brief_still_works(self, test_client):
        """Meeting brief without account_id continues to work as before."""
        resp = test_client.get("/api/v1/meeting/brief?industry=roofing+contractor")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_exposures" in data

    def test_telemetry_feedback_still_works(self, test_client):
        """Telemetry feedback without account_id continues to work."""
        from app.services.telemetry_store import RENDERED_OUTPUT_FEEDBACK
        RENDERED_OUTPUT_FEEDBACK.clear()
        resp = test_client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "output_id": "out_reg",
            "feedback_type": "up",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
        })
        assert resp.status_code == 200
        RENDERED_OUTPUT_FEEDBACK.clear()
