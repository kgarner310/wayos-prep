"""Tests for Phase 7: Web Fetcher, Public Web Intel Fetch, Account Refresh."""

import socket
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


# ============================================================
# FIXTURES
# ============================================================


MOCK_HTML = """
<html>
<head><title>Apex Roofing</title></head>
<body>
<nav>Home | About | Contact</nav>
<main>
<h1>Apex Roofing – Serving Charlotte Since 2012</h1>
<p>We specialize in residential roof replacement, storm restoration, and steep-slope
roofing for homeowners across the greater Charlotte area.</p>
<p>Our crews are OSHA-trained with full fall protection. As a CertainTeed-certified
installer, we deliver manufacturer-backed quality. All work is bonded and insured.</p>
<p>We use subcontractors for specialized gutter work under strict compliance.</p>
<p>Our multi-crew operations allow us to handle 3-5 active job sites simultaneously.</p>
</main>
<footer>© 2024 Apex Roofing. All rights reserved.</footer>
<script>alert('hi')</script>
</body>
</html>
"""

MOCK_ABOUT_HTML = """
<html>
<body>
<h1>About Apex Roofing</h1>
<p>Founded in 2012, Apex Roofing is a family-owned business with 25 employees.</p>
<p>Drug testing and safety training program for all crew members.</p>
</body>
</html>
"""


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_account_obj(**overrides):
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_name": "Apex Roofing",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 27,
        "annual_revenue": 4800000.0,
        "vehicle_count": 9,
        "uses_subcontractors": True,
        "current_coverages": ["general_liability", "workers_comp"],
        "website_url": "https://apexroofing.com",
        "social_urls": None,
        "notes": "",
        "last_public_intel_refresh_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_artifact_obj(**overrides):
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_id": uuid.uuid4(),
        "artifact_type": "public_web_intel",
        "artifact_subtype": "web_fetch",
        "title": "Public Web Intel — Apex Roofing",
        "content_json": {
            "public_web_intel": {
                "company_identity": {"company_name": "Apex Roofing"},
                "operations_signals": ["Roof replacement/repair/installation services"],
                "safety_signals": [],
                "scale_signals": [],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": [],
            },
            "fetch_metadata": {
                "source_url": "https://apexroofing.com",
                "fetched_urls": ["https://apexroofing.com"],
                "fetch_warnings": [],
                "refresh_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        "rendered_text": None,
        "created_by_user_id": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# WEB FETCHER SERVICE TESTS
# ============================================================


class TestWebFetcher:

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
    ])
    def test_fetch_successful(self, _mock_dns):
        import httpx
        from app.services.web_fetcher import fetch_public_page_text

        mock_response = httpx.Response(
            200,
            text=MOCK_HTML,
            headers={"content-type": "text/html"},
            request=httpx.Request("GET", "https://apexroofing.com"),
        )

        with patch("app.services.web_fetcher.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = fetch_public_page_text({
                "website_url": "https://apexroofing.com",
                "max_pages": 1,
            })

        assert result["success"] is True
        assert "apexroofing.com" in result["source_url"]
        assert len(result["fetched_urls"]) >= 1
        assert len(result["raw_text"]) > 50
        assert "Apex Roofing" in result["raw_text"]

    def test_fetch_no_url(self):
        from app.services.web_fetcher import fetch_public_page_text

        result = fetch_public_page_text({})
        assert result["success"] is False
        assert any("No website_url" in w for w in result["fetch_warnings"])

    def test_fetch_invalid_url(self):
        from app.services.web_fetcher import fetch_public_page_text

        result = fetch_public_page_text({"website_url": "ftp://internal.net"})
        assert result["success"] is False

    def test_fetch_private_ip_blocked(self):
        from app.services.web_fetcher import fetch_public_page_text

        result = fetch_public_page_text({"website_url": "http://192.168.1.1"})
        assert result["success"] is False
        assert any("blocked" in w.lower() for w in result["fetch_warnings"])

    def test_fetch_localhost_blocked(self):
        from app.services.web_fetcher import fetch_public_page_text

        result = fetch_public_page_text({"website_url": "http://localhost/admin"})
        assert result["success"] is False
        assert any("blocked" in w.lower() for w in result["fetch_warnings"])

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
    ])
    def test_fetch_timeout_handled(self, _mock_dns):
        import httpx
        from app.services.web_fetcher import fetch_public_page_text

        with patch("app.services.web_fetcher.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.TimeoutException("timeout")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = fetch_public_page_text({
                "website_url": "https://slow-site.com",
                "max_pages": 1,
            })

        assert result["success"] is False
        assert any("Timeout" in w or "No readable" in w for w in result["fetch_warnings"])

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
    ])
    def test_fetch_http_error_handled(self, _mock_dns):
        import httpx
        from app.services.web_fetcher import fetch_public_page_text

        mock_request = httpx.Request("GET", "https://example.com")
        mock_response = httpx.Response(403, request=mock_request)

        with patch("app.services.web_fetcher.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "403", request=mock_request, response=mock_response,
            )
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = fetch_public_page_text({
                "website_url": "https://example.com",
                "max_pages": 1,
            })

        assert result["success"] is False
        assert any("403" in w for w in result["fetch_warnings"])

    def test_html_text_extraction(self):
        from app.services.web_fetcher import _extract_text_from_html

        text = _extract_text_from_html(MOCK_HTML)
        assert "Apex Roofing" in text
        assert "alert" not in text  # script removed
        assert "Home | About" not in text  # nav removed

    def test_max_chars_respected(self):
        import httpx
        from app.services.web_fetcher import fetch_public_page_text

        mock_response = httpx.Response(
            200,
            text=MOCK_HTML,
            headers={"content-type": "text/html"},
            request=httpx.Request("GET", "https://apexroofing.com"),
        )

        with patch("app.services.web_fetcher.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = fetch_public_page_text({
                "website_url": "https://apexroofing.com",
                "max_pages": 1,
                "max_chars": 100,
            })

        assert len(result["raw_text"]) <= 100


# ============================================================
# PUBLIC WEB INTEL WITH FETCH TESTS
# ============================================================


class TestPublicWebIntelWithFetch:

    def test_fetch_and_extract(self):
        from app.services.public_web_intel import extract_public_web_intel_with_fetch

        mock_fetch_result = {
            "source_url": "https://apexroofing.com",
            "fetched_urls": ["https://apexroofing.com"],
            "raw_text": "Apex Roofing – residential roof replacement and storm restoration since 2012. OSHA-trained crews. CertainTeed-certified. Bonded and insured.",
            "fetch_warnings": [],
            "success": True,
        }

        with patch("app.services.web_fetcher.fetch_public_page_text", return_value=mock_fetch_result):
            result = extract_public_web_intel_with_fetch({
                "website_url": "https://apexroofing.com",
                "company_name": "Apex Roofing",
            })

        intel = result["public_web_intel"]
        assert intel["company_identity"]["company_name"] == "Apex Roofing"
        assert len(intel["operations_signals"]) >= 1
        assert result["fetch_summary"]["success"] is True

    def test_manual_text_still_works(self):
        from app.services.public_web_intel import extract_public_web_intel_with_fetch

        mock_fetch_result = {
            "source_url": "",
            "fetched_urls": [],
            "raw_text": "",
            "fetch_warnings": ["No website_url provided"],
            "success": False,
        }

        with patch("app.services.web_fetcher.fetch_public_page_text", return_value=mock_fetch_result):
            result = extract_public_web_intel_with_fetch({
                "raw_website_text": "OSHA safety training program in place. Multi-crew roofing operations.",
                "company_name": "Test Roofing",
            })

        intel = result["public_web_intel"]
        assert len(intel["safety_signals"]) >= 1

    def test_combined_fetch_and_manual(self):
        from app.services.public_web_intel import extract_public_web_intel_with_fetch

        mock_fetch_result = {
            "source_url": "https://example.com",
            "fetched_urls": ["https://example.com"],
            "raw_text": "Residential roof replacement services.",
            "fetch_warnings": [],
            "success": True,
        }

        with patch("app.services.web_fetcher.fetch_public_page_text", return_value=mock_fetch_result):
            result = extract_public_web_intel_with_fetch({
                "website_url": "https://example.com",
                "raw_website_text": "OSHA safety training for all crews.",
                "company_name": "Test Co",
            })

        intel = result["public_web_intel"]
        # Should have both roofing ops and safety signals
        assert len(intel["operations_signals"]) >= 1
        assert len(intel["safety_signals"]) >= 1

    def test_fetch_failure_graceful(self):
        from app.services.public_web_intel import extract_public_web_intel_with_fetch

        mock_fetch_result = {
            "source_url": "https://down-site.com",
            "fetched_urls": [],
            "raw_text": "",
            "fetch_warnings": ["Timeout fetching https://down-site.com"],
            "success": False,
        }

        with patch("app.services.web_fetcher.fetch_public_page_text", return_value=mock_fetch_result):
            result = extract_public_web_intel_with_fetch({
                "website_url": "https://down-site.com",
                "company_name": "Down Site Inc",
            })

        assert result["fetch_summary"]["success"] is False
        assert result["public_web_intel"] is not None


# ============================================================
# ACCOUNT REFRESH SERVICE TESTS
# ============================================================


class TestAccountRefreshService:

    def test_refresh_saves_artifact(self, mock_db):
        from app.services.account_refresh_service import refresh_account_public_intel

        account = _make_account_obj()

        mock_fetch_result = {
            "public_web_intel": {
                "company_identity": {"company_name": "Apex Roofing", "founded_year": 2012, "service_area": []},
                "operations_signals": ["Roof replacement/repair/installation services"],
                "safety_signals": ["References OSHA compliance or procedures"],
                "scale_signals": [],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": ["Public content may reflect marketing language"],
            },
            "fetch_summary": {
                "source_url": "https://apexroofing.com",
                "fetched_urls": ["https://apexroofing.com"],
                "fetch_warnings": [],
                "success": True,
                "fetched_char_count": 500,
            },
        }

        with patch("app.services.account_refresh_service.get_account", return_value=account), \
             patch("app.services.account_refresh_service.extract_public_web_intel_with_fetch", return_value=mock_fetch_result), \
             patch("app.services.account_refresh_service.save_artifact") as mock_save, \
             patch("app.services.account_refresh_service.update_account") as mock_update, \
             patch("app.services.account_refresh_service.log_event"):

            result = refresh_account_public_intel(mock_db, account.id)

        assert result["artifact_saved"] is True
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][1]
        assert saved_data["artifact_type"] == "public_web_intel"
        assert saved_data["account_id"] == account.id

    def test_refresh_account_not_found(self, mock_db):
        from app.services.account_refresh_service import refresh_account_public_intel

        with patch("app.services.account_refresh_service.get_account", return_value=None):
            result = refresh_account_public_intel(mock_db, uuid.uuid4())

        assert result["artifact_saved"] is False
        assert result["error"] == "Account not found"

    def test_refresh_no_website_url(self, mock_db):
        from app.services.account_refresh_service import refresh_account_public_intel

        account = _make_account_obj(website_url=None)

        with patch("app.services.account_refresh_service.get_account", return_value=account):
            result = refresh_account_public_intel(mock_db, account.id)

        assert result["artifact_saved"] is False
        assert "no website_url" in result["error"].lower()

    def test_get_latest_public_intel(self, mock_db):
        from app.services.account_refresh_service import get_latest_public_intel

        artifact = _make_artifact_obj()
        other_artifact = _make_artifact_obj(artifact_type="renewal_brief")

        with patch("app.services.account_refresh_service.list_artifacts_for_account",
                    return_value=[artifact, other_artifact]):
            result = get_latest_public_intel(mock_db, artifact.account_id)

        assert result is not None
        assert result["artifact_id"] == str(artifact.id)

    def test_get_latest_public_intel_none(self, mock_db):
        from app.services.account_refresh_service import get_latest_public_intel

        with patch("app.services.account_refresh_service.list_artifacts_for_account",
                    return_value=[]):
            result = get_latest_public_intel(mock_db, uuid.uuid4())

        assert result is None


# ============================================================
# ENDPOINT TESTS
# ============================================================


class TestFetchEndpoint:

    def test_fetch_endpoint_200(self, client, mock_db):
        mock_result = {
            "public_web_intel": {
                "company_identity": {"company_name": "Apex", "founded_year": None, "service_area": []},
                "operations_signals": ["Roof replacement/repair/installation services"],
                "safety_signals": [],
                "scale_signals": [],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": [],
            },
            "fetch_summary": {
                "source_url": "https://apexroofing.com",
                "fetched_urls": ["https://apexroofing.com"],
                "fetch_warnings": [],
                "success": True,
                "fetched_char_count": 500,
            },
        }

        with patch("app.api.routes.extract_public_web_intel_with_fetch", return_value=mock_result):
            response = client.post("/api/v1/intel/public-web-intel/fetch", json={
                "website_url": "https://apexroofing.com",
                "company_name": "Apex Roofing",
                "industry": "roofing",
                "state": "NC",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["public_web_intel"]["company_identity"]["company_name"] == "Apex"
        assert data["fetch_summary"]["success"] is True
        assert len(data["public_web_intel"]["operations_signals"]) >= 1

    def test_fetch_endpoint_response_shape(self, client, mock_db):
        mock_result = {
            "public_web_intel": {
                "company_identity": {"company_name": "", "founded_year": None, "service_area": []},
                "operations_signals": [],
                "safety_signals": [],
                "scale_signals": [],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": ["No public web content was provided"],
            },
            "fetch_summary": {
                "source_url": "https://example.com",
                "fetched_urls": [],
                "fetch_warnings": ["Timeout"],
                "success": False,
                "fetched_char_count": 0,
            },
        }

        with patch("app.api.routes.extract_public_web_intel_with_fetch", return_value=mock_result):
            response = client.post("/api/v1/intel/public-web-intel/fetch", json={
                "website_url": "https://example.com",
            })

        assert response.status_code == 200
        data = response.json()
        assert "public_web_intel" in data
        assert "fetch_summary" in data
        assert isinstance(data["fetch_summary"]["fetch_warnings"], list)


class TestRefreshEndpoint:

    def test_refresh_endpoint_200(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "account_id": str(aid),
            "artifact_saved": True,
            "error": None,
            "public_web_intel": {
                "company_identity": {"company_name": "Apex", "founded_year": None, "service_area": []},
                "operations_signals": [],
                "safety_signals": [],
                "scale_signals": [],
                "carrier_relevant_signals": [],
                "observed_public_signals": [],
                "cautions": [],
            },
            "fetch_summary": {
                "source_url": "https://apexroofing.com",
                "fetched_urls": ["https://apexroofing.com"],
                "fetch_warnings": [],
                "success": True,
                "fetched_char_count": 300,
            },
            "account_updates": ["last_public_intel_refresh_at"],
        }

        with patch("app.api.routes.refresh_account_public_intel", return_value=mock_result):
            response = client.post(f"/api/v1/accounts/{aid}/refresh-public-intel", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == str(aid)
        assert data["artifact_saved"] is True

    def test_refresh_endpoint_404(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "account_id": str(aid),
            "artifact_saved": False,
            "error": "Account not found",
            "public_web_intel": None,
            "fetch_summary": None,
            "account_updates": [],
        }

        with patch("app.api.routes.refresh_account_public_intel", return_value=mock_result):
            response = client.post(f"/api/v1/accounts/{aid}/refresh-public-intel", json={})

        assert response.status_code == 404


class TestLatestIntelEndpoint:

    def test_latest_intel_200(self, client, mock_db):
        aid = uuid.uuid4()
        mock_result = {
            "artifact_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content": {"public_web_intel": {"company_identity": {"company_name": "Apex"}}},
        }

        with patch("app.api.routes.get_latest_public_intel", return_value=mock_result):
            response = client.get(f"/api/v1/accounts/{aid}/public-intel/latest")

        assert response.status_code == 200
        data = response.json()
        assert "artifact_id" in data
        assert "content" in data

    def test_latest_intel_404(self, client, mock_db):
        aid = uuid.uuid4()

        with patch("app.api.routes.get_latest_public_intel", return_value=None):
            response = client.get(f"/api/v1/accounts/{aid}/public-intel/latest")

        assert response.status_code == 404


# ============================================================
# REGRESSION TESTS
# ============================================================


class TestRegressions:

    def test_existing_public_web_intel_unchanged(self):
        from app.services.public_web_intel import extract_public_web_intel
        result = extract_public_web_intel({
            "raw_website_text": "OSHA safety training program. Residential roof replacement services.",
            "company_name": "Test Co",
        })
        assert result["company_identity"]["company_name"] == "Test Co"
        assert len(result["safety_signals"]) >= 1
        assert len(result["operations_signals"]) >= 1

    def test_existing_public_web_intel_endpoint(self, client, mock_db):
        response = client.post("/api/v1/intel/public-web-intel", json={
            "company_name": "Apex Roofing",
            "raw_website_text": "OSHA safety training for crews.",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["company_identity"]["company_name"] == "Apex Roofing"

    def test_renewal_brief_still_works(self):
        from app.services.renewal_brief_generator import generate_renewal_brief
        result = generate_renewal_brief({"industry": "roofing", "state": "TX"})
        assert "account_summary" in result

    def test_narrative_still_works(self):
        from app.services.underwriter_narrative_generator import generate_underwriter_narrative
        result = generate_underwriter_narrative({"industry": "roofing"})
        assert "email_version" in result

    def test_coverage_gap_still_works(self):
        from app.services.coverage_gap_detector import detect_coverage_gaps
        result = detect_coverage_gaps({"industry": "roofing", "state": "TX"})
        assert len(result["coverage_gaps"]) >= 1
