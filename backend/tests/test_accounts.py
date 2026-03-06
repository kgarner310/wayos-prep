"""Tests for account API endpoints and account-linked workflows."""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


def _get_mock_db():
    return MagicMock()


app.dependency_overrides[get_db] = _get_mock_db
client = TestClient(app)


def test_create_account():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def mock_refresh(obj):
        obj.id = 1
        obj.name = "ABC Manufacturing"
        obj.industry = "Manufacturing"
        obj.location = "Charlotte, NC"
        obj.employee_count = 50
        obj.current_mod = 1.15
        obj.vehicle_exposure = "3 trucks"
        obj.policy_expiration = "2026-06-15"
        obj.renewal_status = "upcoming"
        obj.notes = None
        from datetime import datetime
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()

    mock_db.refresh.side_effect = mock_refresh
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post("/api/v1/accounts", json={
        "name": "ABC Manufacturing",
        "industry": "Manufacturing",
        "location": "Charlotte, NC",
        "employee_count": 50,
        "current_mod": 1.15,
        "vehicle_exposure": "3 trucks",
        "policy_expiration": "2026-06-15",
        "renewal_status": "upcoming",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ABC Manufacturing"
    assert data["current_mod"] == 1.15

    app.dependency_overrides[get_db] = _get_mock_db


def test_create_account_duplicate():
    mock_db = MagicMock()
    existing = MagicMock()
    existing.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = existing
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post("/api/v1/accounts", json={"name": "ABC Manufacturing"})
    assert response.status_code == 409

    app.dependency_overrides[get_db] = _get_mock_db


def test_list_accounts():
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    mock_account.name = "Test Account"
    mock_account.industry = None
    mock_account.location = None
    mock_account.current_mod = None
    mock_account.policy_expiration = None
    mock_account.renewal_status = None
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_account]
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/accounts")
    assert response.status_code == 200

    app.dependency_overrides[get_db] = _get_mock_db


def test_get_account_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/accounts/999")
    assert response.status_code == 404

    app.dependency_overrides[get_db] = _get_mock_db


def test_update_account():
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    mock_account.name = "Test Account"
    mock_account.industry = "Roofing"
    mock_account.location = "NC"
    mock_account.employee_count = 10
    mock_account.current_mod = 1.0
    mock_account.vehicle_exposure = None
    mock_account.policy_expiration = None
    mock_account.renewal_status = None
    mock_account.notes = None
    from datetime import datetime
    mock_account.created_at = datetime.now()
    mock_account.updated_at = datetime.now()

    mock_db.query.return_value.filter.return_value.first.return_value = mock_account
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.patch("/api/v1/accounts/1", json={
        "current_mod": 1.25,
        "renewal_status": "in_progress",
    })
    assert response.status_code == 200

    app.dependency_overrides[get_db] = _get_mock_db


def test_delete_account():
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_account
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.delete("/api/v1/accounts/1")
    assert response.status_code == 204

    app.dependency_overrides[get_db] = _get_mock_db


def test_delete_account_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.delete("/api/v1/accounts/999")
    assert response.status_code == 404

    app.dependency_overrides[get_db] = _get_mock_db


def test_list_upcoming_renewals():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/accounts/renewals")
    assert response.status_code == 200

    app.dependency_overrides[get_db] = _get_mock_db


def test_create_account_validation():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    # Name too short
    response = client.post("/api/v1/accounts", json={"name": ""})
    assert response.status_code == 422

    # Mod out of range
    response = client.post("/api/v1/accounts", json={"name": "Test", "current_mod": 15.0})
    assert response.status_code == 422

    app.dependency_overrides[get_db] = _get_mock_db
