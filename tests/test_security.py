"""Tests for security hardening: auth, headers, upload validation, CORS."""

import io
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.security.upload import validate_upload, ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES


# ============================================================
# SECURITY HEADERS
# ============================================================


class TestSecurityHeaders:
    def test_health_includes_security_headers(self):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=" in resp.headers["Strict-Transport-Security"]
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


# ============================================================
# FILE UPLOAD VALIDATION
# ============================================================


class TestUploadValidation:
    def _make_upload(self, filename, content_type, size=100):
        from fastapi import UploadFile
        data = b"x" * size
        return UploadFile(filename=filename, file=io.BytesIO(data), headers={"content-type": content_type})

    def test_allowed_jpg(self):
        f = self._make_upload("photo.jpg", "image/jpeg")
        validate_upload(f)  # should not raise

    def test_allowed_png(self):
        f = self._make_upload("photo.png", "image/png")
        validate_upload(f)

    def test_allowed_pdf(self):
        f = self._make_upload("doc.pdf", "application/pdf")
        validate_upload(f)

    def test_rejected_exe(self):
        f = self._make_upload("virus.exe", "application/octet-stream")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(f)
        assert exc_info.value.status_code == 415

    def test_rejected_py(self):
        f = self._make_upload("script.py", "text/x-python")
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_upload(f)

    def test_size_limit(self):
        # 11MB file should be rejected (default limit is 10MB)
        f = self._make_upload("big.jpg", "image/jpeg", size=11 * 1024 * 1024)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_upload(f)
        assert exc_info.value.status_code == 413


# ============================================================
# AUTH ON PROTECTED ENDPOINTS
# ============================================================


class TestProtectedEndpoints:
    @pytest.fixture
    def unauthenticated_client(self):
        """Client without auth bypass — tests real auth requirement."""
        from app.api.deps import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_create_account_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.post("/api/v1/accounts", json={
            "account_name": "Test", "industry": "roofing", "state": "NC",
        })
        assert resp.status_code == 401

    def test_delete_account_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.delete(f"/api/v1/accounts/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_outcomes_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.post("/api/v1/outcomes", json={
            "account_id": "acct-1", "outcome": "won",
        })
        assert resp.status_code == 401

    def test_market_signals_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/v1/market-signals")
        assert resp.status_code == 401

    def test_edge_score_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.post("/api/v1/edge-score", json={})
        assert resp.status_code == 401

    def test_demo_seed_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.post("/api/v1/demo/seed")
        assert resp.status_code == 401

    def test_demo_reset_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.post("/api/v1/demo/reset")
        assert resp.status_code == 401


# ============================================================
# CORS CONFIGURATION
# ============================================================


class TestCORSConfig:
    def test_cors_not_wildcard(self):
        from app.core.config import settings
        assert "*" not in settings.CORS_ORIGINS

    def test_cors_has_localhost(self):
        from app.core.config import settings
        assert "http://localhost:3000" in settings.CORS_ORIGINS


# ============================================================
# SECRETS CONFIG
# ============================================================


class TestSecretsConfig:
    def test_env_example_no_real_secrets(self):
        with open(".env.example") as f:
            content = f.read()
        assert "sk-" not in content
        assert "wayos_dev_password" not in content

    def test_jwt_secret_not_empty(self):
        from app.core.config import settings
        assert len(settings.JWT_SECRET_KEY) > 0

    def test_settings_has_app_env(self):
        from app.core.config import settings
        assert hasattr(settings, "APP_ENV")
        assert settings.APP_ENV in ("development", "production", "staging", "test")

    def test_settings_has_anthropic_key(self):
        from app.core.config import settings
        assert hasattr(settings, "ANTHROPIC_API_KEY")


# ============================================================
# PROMPT INJECTION GUARDRAILS
# ============================================================


class TestPromptGuardrails:
    @pytest.mark.parametrize("prompt_file", [
        "app/prompts/coverage_gap_system.txt",
        "app/prompts/meeting_brief_system.txt",
        "app/prompts/workers_comp_snapshot_system.txt",
        "app/prompts/winnability_system.txt",
    ])
    def test_prompt_has_guardrails(self, prompt_file):
        with open(prompt_file) as f:
            content = f.read()
        assert "Never reveal" in content
        assert "Never execute" in content
        assert "Never expose" in content
