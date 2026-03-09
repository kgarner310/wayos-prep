"""Tests for Phase 10: Authentication, Authorization, Agency Scoping, Audit."""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# AUTH SERVICE — unit tests
# ============================================================


class TestPasswordHashing:

    def test_hash_and_verify(self):
        from app.services.auth_service import hash_password, verify_password
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert verify_password("secret123", hashed)
        assert not verify_password("wrong", hashed)

    def test_different_hashes(self):
        from app.services.auth_service import hash_password
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # bcrypt salts differ


class TestJWTTokens:

    def test_create_and_decode_access_token(self):
        from app.services.auth_service import create_access_token, decode_token
        token = create_access_token("user-1", "agency-1", "producer")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-1"
        assert payload["agency_id"] == "agency-1"
        assert payload["role"] == "producer"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        from app.services.auth_service import create_refresh_token, decode_token
        token = create_refresh_token("user-2")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-2"
        assert payload["type"] == "refresh"

    def test_expired_token_returns_none(self):
        import jwt
        from app.core.config import settings
        from app.services.auth_service import decode_token
        expired_payload = {
            "sub": "user-1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert decode_token(token) is None

    def test_invalid_token_returns_none(self):
        from app.services.auth_service import decode_token
        assert decode_token("garbage.token.here") is None

    def test_wrong_secret_returns_none(self):
        import jwt
        from app.services.auth_service import decode_token
        payload = {"sub": "user-1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        assert decode_token(token) is None


class TestSlugGeneration:

    def test_make_slug(self):
        from app.services.auth_service import _make_slug
        assert _make_slug("Apex Insurance Group") == "apex-insurance-group"
        assert _make_slug("O'Brien & Sons") == "o-brien-sons"
        assert _make_slug("   ABC   ") == "abc"


class TestRegisterUser:

    def test_register_creates_agency_and_user(self):
        from app.services.auth_service import register_user
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None  # no existing user/agency

        with patch("app.services.auth_service.hash_password", return_value="hashed"), \
             patch("app.services.auth_service.create_access_token", return_value="at"), \
             patch("app.services.auth_service.create_refresh_token", return_value="rt"):
            result = register_user(db, "test@test.com", "pass", "Test User", "Test Agency")

        assert "error" not in result
        assert result["tokens"]["access_token"] == "at"
        assert db.add.call_count >= 2  # agency + user
        db.commit.assert_called_once()

    def test_register_duplicate_email(self):
        from app.services.auth_service import register_user
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()  # existing user

        result = register_user(db, "dup@test.com", "pass", "Dup", "Agency")
        assert result["error"] == "Email already registered"


class TestLoginUser:

    def test_login_success(self):
        from app.services.auth_service import login_user
        db = MagicMock()
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "user@test.com"
        user.full_name = "User"
        user.role = "producer"
        user.agency_id = uuid.uuid4()
        user.is_active = True
        user.hashed_password = "hashed"

        agency = MagicMock()
        agency.agency_name = "Test Agency"

        db.query.return_value.filter.return_value.first.side_effect = [user, agency]

        with patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.create_access_token", return_value="at"), \
             patch("app.services.auth_service.create_refresh_token", return_value="rt"):
            result = login_user(db, "user@test.com", "pass")

        assert "error" not in result
        assert result["tokens"]["access_token"] == "at"

    def test_login_wrong_password(self):
        from app.services.auth_service import login_user
        db = MagicMock()
        user = MagicMock()
        user.is_active = True
        user.hashed_password = "hashed"
        db.query.return_value.filter.return_value.first.return_value = user

        with patch("app.services.auth_service.verify_password", return_value=False):
            result = login_user(db, "user@test.com", "wrong")
        assert result["error"] == "Invalid email or password"

    def test_login_no_user(self):
        from app.services.auth_service import login_user
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = login_user(db, "noone@test.com", "pass")
        assert result["error"] == "Invalid email or password"

    def test_login_disabled_user(self):
        from app.services.auth_service import login_user
        db = MagicMock()
        user = MagicMock()
        user.is_active = False
        db.query.return_value.filter.return_value.first.return_value = user

        result = login_user(db, "disabled@test.com", "pass")
        assert result["error"] == "Account is disabled"


class TestRefreshTokens:

    def test_refresh_success(self):
        from app.services.auth_service import refresh_tokens, create_refresh_token
        db = MagicMock()
        user = MagicMock()
        user.id = uuid.uuid4()
        user.agency_id = uuid.uuid4()
        user.role = "producer"
        user.is_active = True
        db.query.return_value.filter.return_value.first.return_value = user

        token = create_refresh_token(str(user.id))
        result = refresh_tokens(db, token)
        assert "error" not in result
        assert "access_token" in result

    def test_refresh_with_access_token_fails(self):
        from app.services.auth_service import refresh_tokens, create_access_token
        db = MagicMock()
        token = create_access_token("user-1", "agency-1", "producer")
        result = refresh_tokens(db, token)
        assert result["error"] == "Invalid or expired refresh token"


# ============================================================
# AUTH ENDPOINTS — integration tests
# ============================================================


class TestAuthEndpoints:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        # Remove the conftest auth bypass so real JWT auth is tested
        from app.api.deps import get_current_user
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_register_endpoint(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.auth_service.hash_password", return_value="hashed"), \
             patch("app.services.auth_service.create_access_token", return_value="at"), \
             patch("app.services.auth_service.create_refresh_token", return_value="rt"):
            resp = client.post("/api/v1/auth/register", json={
                "email": "new@test.com",
                "password": "secret123",
                "full_name": "New User",
                "agency_name": "New Agency",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "at"
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        resp = client.post("/api/v1/auth/register", json={
            "email": "dup@test.com",
            "password": "secret123",
            "full_name": "Dup",
            "agency_name": "Agency",
        })
        assert resp.status_code == 400

    def test_login_endpoint(self, client, mock_db):
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "user@test.com"
        user.full_name = "User"
        user.role = "producer"
        user.agency_id = uuid.uuid4()
        user.is_active = True
        user.hashed_password = "hashed"

        agency = MagicMock()
        agency.agency_name = "Agency"

        mock_db.query.return_value.filter.return_value.first.side_effect = [user, agency]

        with patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.create_access_token", return_value="at"), \
             patch("app.services.auth_service.create_refresh_token", return_value="rt"):
            resp = client.post("/api/v1/auth/login", json={
                "email": "user@test.com",
                "password": "secret",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "at"

    def test_login_invalid_credentials(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.post("/api/v1/auth/login", json={
            "email": "no@test.com",
            "password": "bad",
        })
        assert resp.status_code == 401

    def test_me_endpoint(self, client, mock_db):
        from app.services.auth_service import create_access_token
        uid = uuid.uuid4()
        aid = uuid.uuid4()
        token = create_access_token(str(uid), str(aid), "producer")

        user = MagicMock()
        user.id = uid
        user.email = "me@test.com"
        user.full_name = "Me User"
        user.role = "producer"
        user.agency_id = aid
        user.is_active = True

        agency = MagicMock()
        agency.agency_name = "My Agency"
        agency.id = aid

        mock_db.query.return_value.filter.return_value.first.side_effect = [user, agency]

        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@test.com"
        assert data["agency_name"] == "My Agency"

    def test_me_without_token(self, client, mock_db):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_expired_token(self, client, mock_db):
        import jwt
        from app.core.config import settings
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "agency_id": str(uuid.uuid4()),
            "role": "producer",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_refresh_endpoint(self, client, mock_db):
        from app.services.auth_service import create_refresh_token
        uid = uuid.uuid4()
        refresh = create_refresh_token(str(uid))

        user = MagicMock()
        user.id = uid
        user.agency_id = uuid.uuid4()
        user.role = "producer"
        user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data


# ============================================================
# DEPS — agency scoping
# ============================================================


class TestDeps:

    def test_get_current_user_no_token(self):
        from app.api.deps import get_current_user
        with pytest.raises(Exception):
            get_current_user(credentials=None, db=MagicMock())

    def test_require_role_blocks_unauthorized(self):
        from app.api.deps import require_role, CurrentUser
        checker = require_role(["admin"])
        user = CurrentUser(
            user_id=uuid.uuid4(),
            agency_id=uuid.uuid4(),
            role="producer",
            email="p@test.com",
            full_name="Producer",
        )
        with pytest.raises(Exception):
            checker(user)

    def test_require_role_allows_authorized(self):
        from app.api.deps import require_role, CurrentUser
        checker = require_role(["admin", "producer"])
        user = CurrentUser(
            user_id=uuid.uuid4(),
            agency_id=uuid.uuid4(),
            role="admin",
            email="a@test.com",
            full_name="Admin",
        )
        result = checker(user)
        assert result.role == "admin"


# ============================================================
# AUDIT SERVICE
# ============================================================


class TestAuditService:

    def test_log_audit_event(self):
        from app.services.audit_service import log_audit_event
        db = MagicMock()
        uid = uuid.uuid4()
        aid = uuid.uuid4()

        event = log_audit_event(
            db,
            event_type="test_event",
            user_id=uid,
            agency_id=aid,
            resource_type="account",
            resource_id="abc-123",
            detail={"key": "value"},
            ip_address="1.2.3.4",
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()


# ============================================================
# MODELS — Agency/User/AuditEvent exist
# ============================================================


class TestModels:

    def test_agency_model_exists(self):
        from app.models.models import Agency
        assert Agency.__tablename__ == "agencies"

    def test_user_model_exists(self):
        from app.models.models import User
        assert User.__tablename__ == "users"

    def test_audit_event_model_exists(self):
        from app.models.models import AuditEvent
        assert AuditEvent.__tablename__ == "audit_events"

    def test_account_has_agency_id(self):
        from app.models.models import Account
        cols = {c.name for c in Account.__table__.columns}
        assert "agency_id" in cols

    def test_saved_artifact_has_agency_id(self):
        from app.models.models import SavedArtifact
        cols = {c.name for c in SavedArtifact.__table__.columns}
        assert "agency_id" in cols

    def test_producer_style_has_agency_id(self):
        from app.models.models import ProducerStylePreference
        cols = {c.name for c in ProducerStylePreference.__table__.columns}
        assert "agency_id" in cols


# ============================================================
# CONFIG — auth settings present
# ============================================================


class TestConfig:

    def test_jwt_settings(self):
        from app.core.config import settings
        assert hasattr(settings, "JWT_SECRET_KEY")
        assert hasattr(settings, "JWT_ALGORITHM")
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert hasattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS")
        assert settings.JWT_ALGORITHM == "HS256"


# ============================================================
# RATE LIMITING — limiter attached to app
# ============================================================


class TestRateLimiting:

    def test_app_has_limiter(self):
        assert hasattr(app.state, "limiter")


# ============================================================
# REGRESSION — existing endpoints still work
# ============================================================


class TestAuthRegressions:

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_public_web_intel_still_works(self, client, mock_db):
        resp = client.post("/api/v1/intel/public-web-intel", json={
            "company_name": "Test",
            "raw_website_text": "OSHA safety training for crews.",
        })
        assert resp.status_code == 200

    def test_coverage_gaps_still_works(self, client):
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp"],
        })
        assert resp.status_code == 200
