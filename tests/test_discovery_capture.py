"""Tests for the Discovery Capture service (save_discovery).

Unit tests only — no real DB. Tests use mock sessions.
"""

from unittest.mock import MagicMock

from app.services.discovery_capture import save_discovery


def _mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


def test_save_returns_ok_status():
    """save_discovery should return status=ok and saved=True."""
    db = _mock_db()
    result = save_discovery(db, {
        "industry": "roofing",
        "state": "NC",
        "source_type": "coverage_gap_engine",
        "source_key": "inland_marine",
        "exposure_found": True,
    })
    assert result["status"] == "ok"
    assert result["saved"] is True


def test_save_calls_db_add_and_commit():
    """save_discovery should add to session and commit."""
    db = _mock_db()
    save_discovery(db, {
        "industry": "trucking",
        "state": "TX",
        "source_type": "producer_ammo",
        "source_key": "cargo_question",
        "exposure_found": False,
    })
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_save_with_all_optional_fields():
    """All optional fields should be accepted without error."""
    db = _mock_db()
    result = save_discovery(db, {
        "industry": "roofing",
        "state": "nc",
        "account_stage": "renewal",
        "source_type": "coverage_gap_engine",
        "source_key": "inland_marine",
        "exposure_found": True,
        "exposure_type": "missing_coverage",
        "coverage_added": "inland_marine",
        "notes": "Producer added IM floater at renewal",
    })
    assert result["status"] == "ok"


def test_save_with_minimal_fields():
    """Minimal required fields should work."""
    db = _mock_db()
    result = save_discovery(db, {
        "industry": "hvac",
        "state": "OH",
        "source_type": "manual",
        "source_key": "observation",
        "exposure_found": False,
    })
    assert result["saved"] is True


def test_save_state_uppercased():
    """State should be stored uppercased."""
    db = _mock_db()
    save_discovery(db, {
        "industry": "roofing",
        "state": "nc",
        "source_type": "manual",
        "source_key": "test",
        "exposure_found": True,
    })
    added_obj = db.add.call_args[0][0]
    assert added_obj.state == "NC"


def test_save_empty_state_handled():
    """Empty state should not crash."""
    db = _mock_db()
    result = save_discovery(db, {
        "industry": "roofing",
        "state": "",
        "source_type": "manual",
        "source_key": "test",
        "exposure_found": False,
    })
    assert result["status"] == "ok"
