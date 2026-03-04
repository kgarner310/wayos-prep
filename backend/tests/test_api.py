"""Tests for API endpoints using TestClient."""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


def _get_mock_db():
    return MagicMock()


app.dependency_overrides[get_db] = _get_mock_db


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "wayos-prep"


def test_list_industries():
    mock_db = MagicMock()
    mock_profile = MagicMock()
    mock_profile.id = 1
    mock_profile.industry_name = "Roofing"
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_profile]

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/industries")
    assert response.status_code == 200

    # Reset
    app.dependency_overrides[get_db] = _get_mock_db


def test_get_industry_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/industries/999")
    assert response.status_code == 404

    app.dependency_overrides[get_db] = _get_mock_db
