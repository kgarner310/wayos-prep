"""Tests for SSRF protection in web_fetcher module.

Proves web_fetcher.py uses the shared url_guard with the same SSRF posture
as ingestion.py: DNS-resolved IP blocking, no redirect following.
"""

import socket
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.web_fetcher import fetch_public_page_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_input(url: str) -> dict:
    return {"website_url": url, "max_pages": 1}


def _public_addrinfo():
    """Mock getaddrinfo returning a public IP."""
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


def _loopback_addrinfo():
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]


def _private_addrinfo():
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]


def _link_local_addrinfo():
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))]


def _html_response(text="<html><body>" + "x" * 100 + "</body></html>"):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.is_redirect = False
    resp.headers = {"content-type": "text/html; charset=utf-8"}
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# DNS-resolved IP blocking (shared guard)
# ---------------------------------------------------------------------------

class TestDNSResolvedIPBlocking:
    """Hostname that resolves to a blocked IP must be rejected before fetch."""

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_loopback_addrinfo())
    @patch("app.services.web_fetcher.httpx.Client")
    def test_loopback_ip_blocked(self, mock_client_cls, _mock_dns):
        result = fetch_public_page_text(_make_input("https://evil.com/steal"))
        assert result["success"] is False
        assert any("blocked IP" in w for w in result["fetch_warnings"])
        mock_client_cls.assert_not_called()

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_private_addrinfo())
    @patch("app.services.web_fetcher.httpx.Client")
    def test_private_ip_blocked(self, mock_client_cls, _mock_dns):
        result = fetch_public_page_text(_make_input("https://attacker.com/bounce"))
        assert result["success"] is False
        assert any("blocked IP" in w for w in result["fetch_warnings"])
        mock_client_cls.assert_not_called()

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_link_local_addrinfo())
    @patch("app.services.web_fetcher.httpx.Client")
    def test_metadata_endpoint_blocked(self, mock_client_cls, _mock_dns):
        result = fetch_public_page_text(
            _make_input("https://169.254.169.254/latest/meta-data/")
        )
        assert result["success"] is False
        assert any("blocked IP" in w or "link-local" in w.lower() for w in result["fetch_warnings"])
        mock_client_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Redirect rejection
# ---------------------------------------------------------------------------

class TestRedirectRejection:
    """Redirects must be rejected, not followed."""

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_public_addrinfo())
    def test_302_redirect_rejected(self, _mock_dns):
        redirect_resp = MagicMock(spec=httpx.Response)
        redirect_resp.status_code = 302
        redirect_resp.is_redirect = True
        redirect_resp.headers = {"Location": "http://127.0.0.1/internal"}
        redirect_resp.raise_for_status = MagicMock()

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = redirect_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.web_fetcher.httpx.Client", return_value=mock_client):
            result = fetch_public_page_text(_make_input("https://example.com/page"))

        assert result["success"] is False
        assert any("Redirect" in w or "redirect" in w for w in result["fetch_warnings"])

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_public_addrinfo())
    def test_301_redirect_rejected(self, _mock_dns):
        redirect_resp = MagicMock(spec=httpx.Response)
        redirect_resp.status_code = 301
        redirect_resp.is_redirect = True
        redirect_resp.raise_for_status = MagicMock()

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = redirect_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.web_fetcher.httpx.Client", return_value=mock_client):
            result = fetch_public_page_text(_make_input("https://example.com/page"))

        assert result["success"] is False
        assert any("Redirect" in w or "redirect" in w for w in result["fetch_warnings"])


# ---------------------------------------------------------------------------
# follow_redirects=False enforcement
# ---------------------------------------------------------------------------

class TestFollowRedirectsDisabled:
    """httpx Client must be created with follow_redirects=False."""

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_public_addrinfo())
    def test_client_created_with_follow_redirects_false(self, _mock_dns):
        with patch("app.services.web_fetcher.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = _html_response()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_cls.return_value = mock_client

            fetch_public_page_text(_make_input("https://example.com"))

            _, call_kwargs = mock_client_cls.call_args
            assert call_kwargs.get("follow_redirects") is False


# ---------------------------------------------------------------------------
# Allowed public URLs still work
# ---------------------------------------------------------------------------

class TestAllowedPublicURLs:
    """Valid public URLs should fetch successfully."""

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_public_addrinfo())
    def test_public_url_succeeds(self, _mock_dns):
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _html_response()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.web_fetcher.httpx.Client", return_value=mock_client):
            result = fetch_public_page_text(_make_input("https://example.com"))

        assert result["success"] is True
        assert len(result["fetched_urls"]) >= 1
        assert result["raw_text"]

    @patch("app.services.url_guard.socket.getaddrinfo", return_value=_public_addrinfo())
    def test_url_without_scheme_gets_https(self, _mock_dns):
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = _html_response()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.services.web_fetcher.httpx.Client", return_value=mock_client):
            result = fetch_public_page_text(_make_input("example.com"))

        assert result["success"] is True
