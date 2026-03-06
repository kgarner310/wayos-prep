"""Tests for the Product Instrumentation service (log_event, get_product_signals).

Unit tests only — no real DB. Tests use mock sessions.
"""

from unittest.mock import MagicMock

from app.services.instrumentation import log_event, get_product_signals


def _mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


# --- log_event ---

def test_log_event_adds_and_commits():
    """log_event should add an EventLog and commit."""
    db = _mock_db()
    log_event(db, "prep_query", payload={"industry": "roofing"})
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_log_event_with_user_id():
    """log_event should accept optional user_id."""
    db = _mock_db()
    log_event(db, "coverage_gap_run", user_id="user123")
    added_obj = db.add.call_args[0][0]
    assert added_obj.user_id == "user123"


def test_log_event_no_payload():
    """log_event should work without payload."""
    db = _mock_db()
    log_event(db, "agency_feed_view")
    db.add.assert_called_once()


def test_log_event_swallows_exceptions():
    """log_event should not raise on DB errors."""
    db = _mock_db()
    db.add.side_effect = Exception("DB error")
    log_event(db, "test_event")  # Should not raise
    db.rollback.assert_called_once()


# --- get_product_signals ---

def test_signals_returns_days():
    """get_product_signals should echo back the days parameter."""
    db = _mock_db()
    db.query.return_value.filter.return_value.all.return_value = []
    result = get_product_signals(db, days=14)
    assert result["days"] == 14


def test_signals_returns_empty_dict_on_no_events():
    """With no events, signals should be empty dict."""
    db = _mock_db()
    db.query.return_value.filter.return_value.all.return_value = []
    result = get_product_signals(db, days=7)
    assert result["signals"] == {}


def test_signals_counts_event_types():
    """Should count events by type."""
    db = _mock_db()
    mock_events = [
        MagicMock(event_type="prep_query"),
        MagicMock(event_type="prep_query"),
        MagicMock(event_type="coverage_gap_run"),
    ]
    db.query.return_value.filter.return_value.all.return_value = mock_events
    result = get_product_signals(db, days=7)
    assert result["signals"]["prep_query"] == 2
    assert result["signals"]["coverage_gap_run"] == 1


def test_signals_handles_db_error():
    """Should return empty signals on DB error."""
    db = _mock_db()
    db.query.side_effect = Exception("DB error")
    result = get_product_signals(db, days=7)
    assert result["signals"] == {}
    assert result["days"] == 7
