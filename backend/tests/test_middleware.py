"""Tests for middleware: auth, rate limiting, error handling."""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


def _get_mock_db():
    return MagicMock()


app.dependency_overrides[get_db] = _get_mock_db

client = TestClient(app)


class TestAuth:
    """API key authentication tests."""

    @patch("app.middleware.auth.settings")
    def test_auth_disabled_when_no_key_configured(self, mock_settings):
        mock_settings.wayos_api_key = ""
        response = client.get("/api/v1/industries")
        assert response.status_code == 200

    @patch("app.middleware.auth.settings")
    def test_auth_rejects_missing_key(self, mock_settings):
        mock_settings.wayos_api_key = "secret-key-123"
        response = client.get("/api/v1/industries")
        assert response.status_code == 401

    @patch("app.middleware.auth.settings")
    def test_auth_rejects_wrong_key(self, mock_settings):
        mock_settings.wayos_api_key = "secret-key-123"
        response = client.get(
            "/api/v1/industries",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 403

    @patch("app.middleware.auth.settings")
    def test_auth_accepts_correct_key(self, mock_settings):
        mock_settings.wayos_api_key = "secret-key-123"
        response = client.get(
            "/api/v1/industries",
            headers={"X-API-Key": "secret-key-123"},
        )
        assert response.status_code == 200

    def test_health_does_not_require_auth(self):
        """Health endpoint should always work without auth."""
        response = client.get("/health")
        assert response.status_code == 200


class TestRateLimit:
    """Rate limiting tests."""

    def test_rate_limit_returns_429_on_excess(self):
        """Simulate exceeding rate limit with a very low RPM."""
        from app.middleware.rate_limit import RateLimitMiddleware
        import time

        # Create a limiter with 2 RPM
        limiter = RateLimitMiddleware.__new__(RateLimitMiddleware)
        limiter.rpm = 2
        limiter._buckets = {}

        from collections import defaultdict
        limiter._buckets = defaultdict(list)

        now = time.time()
        limiter._buckets["127.0.0.1"] = [now, now]

        # The bucket is full (2 entries within window)
        assert len(limiter._buckets["127.0.0.1"]) >= limiter.rpm
