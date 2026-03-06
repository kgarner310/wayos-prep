"""Tests for API endpoints using TestClient."""
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


def _get_mock_db():
    return MagicMock()


app.dependency_overrides[get_db] = _get_mock_db

client = TestClient(app)


def test_root_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "wayos-prep"


def test_v1_health():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    app.dependency_overrides[get_db] = _get_mock_db


def test_list_industries():
    mock_db = MagicMock()
    mock_profile = MagicMock()
    mock_profile.id = 1
    mock_profile.industry_name = "Roofing"
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_profile]

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/industries")
    assert response.status_code == 200

    app.dependency_overrides[get_db] = _get_mock_db


def test_get_industry_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/industries/999")
    assert response.status_code == 404

    app.dependency_overrides[get_db] = _get_mock_db


def test_request_id_header():
    """Responses should include X-Request-ID header."""
    response = client.get("/health")
    assert "x-request-id" in response.headers


def test_custom_request_id_forwarded():
    """A provided X-Request-ID should be echoed back."""
    response = client.get("/health", headers={"X-Request-ID": "test-123"})
    assert response.headers.get("x-request-id") == "test-123"


def test_list_states():
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.id = 1
    mock_state.state_code = "NC"
    mock_state.state_name = "North Carolina"
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_state]

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/states")
    assert response.status_code == 200

    app.dependency_overrides[get_db] = _get_mock_db


def test_get_state_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/states/ZZ")
    assert response.status_code == 404

    app.dependency_overrides[get_db] = _get_mock_db
