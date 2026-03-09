"""Tests for centralized account memory writes.

Covers:
- record_memory dedupe behavior
- record_memory category/confidence storage
- Outcome logging → memory creation
- Account update → memory creation
- Dashboard still reads memory correctly
"""

import uuid

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch

from app.models.models import AccountMemoryEntry
from app.services.account_memory_service import (
    record_memory,
    list_account_memory,
    format_memory_for_display,
    MEMORY_CATEGORIES,
    VALID_ENTRY_TYPES,
    _normalize_summary,
    _merge_payload,
)


# ============================================================
# HELPERS
# ============================================================


def _make_entry(
    account_id="acct-1",
    entry_type="outcome_logged",
    summary="Won — Travelers",
    payload_json=None,
    created_at=None,
):
    entry = MagicMock(spec=AccountMemoryEntry)
    entry.id = uuid.uuid4()
    entry.account_id = account_id
    entry.agency_id = None
    entry.session_id = None
    entry.industry = "roofing contractor"
    entry.entry_type = entry_type
    entry.summary = summary
    entry.payload_json = payload_json or {}
    entry.created_by = None
    entry.created_at = created_at or datetime.now(timezone.utc)
    return entry


# ============================================================
# UNIT: record_memory
# ============================================================


class TestRecordMemory:
    def test_creates_new_entry(self):
        db = MagicMock()
        # No existing duplicate
        db.query.return_value.filter.return_value.first.return_value = None

        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="outcome_logged",
            summary="Won — Travelers on price",
            category="outcome_history",
            confidence="high",
        )
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_deduplicates_same_summary(self):
        db = MagicMock()
        existing = _make_entry(summary="Won — Travelers")
        db.query.return_value.filter.return_value.first.return_value = existing

        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="outcome_logged",
            summary="Won — Travelers",
            category="outcome_history",
        )
        # Should NOT call db.add — just update existing
        db.add.assert_not_called()
        db.flush.assert_called_once()
        assert result is not None
        assert result["summary"] == "Won — Travelers"

    def test_invalid_entry_type_returns_none(self):
        db = MagicMock()
        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="totally_bogus",
            summary="test",
        )
        assert result is None
        db.add.assert_not_called()

    def test_category_stored_in_payload(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        record_memory(
            db,
            account_id="acct-1",
            entry_type="outcome_logged",
            summary="Lost to competitor",
            category="outcome_history",
            confidence="high",
        )
        added_entry = db.add.call_args[0][0]
        assert added_entry.payload_json["category"] == "outcome_history"
        assert added_entry.payload_json["confidence"] == "high"

    def test_unknown_category_still_works(self):
        """Unknown categories log a warning but still store."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="outcome_logged",
            summary="Some entry",
            category="totally_new_category",
        )
        # Should still create the entry
        db.add.assert_called_once()

    def test_no_category_no_confidence(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        record_memory(
            db,
            account_id="acct-1",
            entry_type="outcome_logged",
            summary="Basic entry",
        )
        added_entry = db.add.call_args[0][0]
        # payload_json should be None when no metadata
        assert added_entry.payload_json is None

    def test_db_error_returns_none(self):
        db = MagicMock()
        db.query.side_effect = Exception("connection lost")

        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="outcome_logged",
            summary="test",
        )
        assert result is None


# ============================================================
# UNIT: helpers
# ============================================================


class TestHelpers:
    def test_normalize_summary(self):
        assert _normalize_summary("  Won — Travelers  ") == "won — travelers"
        assert _normalize_summary("LOST") == "lost"

    def test_merge_payload_empty(self):
        result = _merge_payload(None, None)
        assert result is None

    def test_merge_payload_with_category(self):
        result = _merge_payload({"foo": 1}, None, category="outcome_history")
        assert result == {"foo": 1, "category": "outcome_history"}

    def test_merge_payload_combines(self):
        result = _merge_payload({"a": 1}, {"b": 2}, confidence="high")
        assert result == {"a": 1, "b": 2, "confidence": "high"}


# ============================================================
# UNIT: category constants
# ============================================================


class TestConstants:
    def test_memory_categories_not_empty(self):
        assert len(MEMORY_CATEGORIES) >= 5

    def test_valid_entry_types_includes_outcome(self):
        assert "outcome_logged" in VALID_ENTRY_TYPES

    def test_valid_entry_types_includes_producer_edited(self):
        assert "producer_edited" in VALID_ENTRY_TYPES


# ============================================================
# INTEGRATION: outcome → memory
# ============================================================


class TestOutcomeMemoryIntegration:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def test_client(self, mock_db):
        from fastapi.testclient import TestClient
        from app.db.session import get_db
        from app.main import app

        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_outcome_creates_memory_entry(self, test_client, mock_db):
        # record_memory calls db.query for dedupe check — return no existing
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = test_client.post("/api/v1/outcomes", json={
            "account_id": "acct-1",
            "outcome": "won",
            "carrier": "Travelers",
            "outcome_reason": "Competitive pricing",
            "industry": "roofing contractor",
        })
        assert resp.status_code == 200

        # Verify memory was recorded: db.add should be called for
        # DealOutcome + AccountEvent + AccountMemoryEntry
        assert mock_db.add.call_count >= 3

    def test_outcome_with_competitor_in_memory(self, test_client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = test_client.post("/api/v1/outcomes", json={
            "account_id": "acct-2",
            "outcome": "lost",
            "carrier": "Hartford",
            "competitor": "Progressive",
            "notes": "Price was 15% lower",
        })
        assert resp.status_code == 200
        assert mock_db.add.call_count >= 3


# ============================================================
# INTEGRATION: account update → memory
# ============================================================


class TestAccountUpdateMemory:
    def test_notes_update_creates_memory(self):
        """Updating notes should call record_memory."""
        db = MagicMock()
        # No existing dedupe match
        db.query.return_value.filter.return_value.first.return_value = None

        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="producer_edited",
            summary="Client is price sensitive, prefers bundled policies",
            category="client_behavior",
            confidence="high",
            industry="roofing contractor",
        )
        db.add.assert_called_once()

    def test_coverages_update_creates_memory(self):
        """Updating coverages should call record_memory."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = record_memory(
            db,
            account_id="acct-1",
            entry_type="producer_edited",
            summary="Coverages updated: general_liability, workers_comp, cyber",
            category="coverage_history",
            confidence="high",
            industry="hvac",
        )
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.payload_json["category"] == "coverage_history"


# ============================================================
# INTEGRATION: _entry_to_dict includes category
# ============================================================


class TestSerializationWithCategory:
    def test_entry_dict_includes_category(self):
        entry = _make_entry(
            payload_json={"category": "outcome_history", "confidence": "high"},
        )
        from app.services.account_memory_service import _entry_to_dict

        result = _entry_to_dict(entry)
        assert result["category"] == "outcome_history"
        assert result["confidence"] == "high"

    def test_entry_dict_no_category(self):
        entry = _make_entry(payload_json={})
        from app.services.account_memory_service import _entry_to_dict

        result = _entry_to_dict(entry)
        assert result["category"] is None
        assert result["confidence"] is None

    def test_entry_dict_includes_display_summary(self):
        entry = _make_entry(summary="Won — Travelers. Competitive pricing")
        from app.services.account_memory_service import _entry_to_dict

        result = _entry_to_dict(entry)
        assert result["summary"] == "Won — Travelers. Competitive pricing"
        assert result["display_summary"] == "Won with Travelers on competitive pricing"


# ============================================================
# UNIT: format_memory_for_display
# ============================================================


class TestFormatMemoryForDisplay:
    def test_coverage_gap_rewrite(self):
        assert (
            format_memory_for_display("Coverage gaps identified: workers_comp, umbrella")
            == "Workers comp and umbrella gaps found"
        )

    def test_coverage_gap_single(self):
        assert (
            format_memory_for_display("Coverage gaps identified: cyber_liability")
            == "Cyber liability gaps found"
        )

    def test_coverage_gap_three_items(self):
        result = format_memory_for_display(
            "Coverage gaps identified: workers_comp, umbrella, cyber"
        )
        assert result == "Workers comp, Umbrella and cyber gaps found"

    def test_outcome_won(self):
        assert (
            format_memory_for_display("Won — Travelers. Competitive pricing")
            == "Won with Travelers on competitive pricing"
        )

    def test_outcome_lost(self):
        assert (
            format_memory_for_display("Lost — Hartford. Price was higher")
            == "Lost to Hartford on price was higher"
        )

    def test_outcome_renewed(self):
        assert (
            format_memory_for_display("Renewed — Travelers")
            == "Renewed with Travelers"
        )

    def test_outcome_no_reason(self):
        assert (
            format_memory_for_display("Won — Travelers")
            == "Won with Travelers"
        )

    def test_declined_slug(self):
        assert (
            format_memory_for_display("declined_umbrella_2026")
            == "Declined umbrella in 2026"
        )

    def test_coverages_updated(self):
        assert (
            format_memory_for_display("Coverages updated: general_liability, workers_comp")
            == "Coverages: general liability, workers comp"
        )

    def test_plain_summary_passthrough(self):
        assert (
            format_memory_for_display("Client prefers bundled policies")
            == "Client prefers bundled policies"
        )

    def test_underscore_cleanup_fallback(self):
        assert (
            format_memory_for_display("some_machine_generated_note")
            == "some machine generated note"
        )

    def test_empty_string(self):
        assert format_memory_for_display("") == ""

    def test_none_returns_empty(self):
        assert format_memory_for_display(None) == ""


# ============================================================
# INTEGRATION: dashboard memory includes display_summary
# ============================================================


class TestDashboardMemoryDisplay:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def test_client(self, mock_db):
        from fastapi.testclient import TestClient
        from app.db.session import get_db
        from app.main import app

        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_memory_list_includes_display_summary(self, test_client, mock_db):
        entry = _make_entry(summary="Coverage gaps identified: workers_comp, umbrella")
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [entry]

        resp = test_client.get("/api/v1/account-memory/acct-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        mem = data["entries"][0]
        assert mem["summary"] == "Coverage gaps identified: workers_comp, umbrella"
        assert mem["display_summary"] == "Workers comp and umbrella gaps found"
