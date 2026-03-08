"""Tests for SSRF protection in url_guard module."""

import socket
from unittest.mock import patch

import pytest

from app.services.url_guard import validate_external_url


class TestBlockedURLs:
    """URLs that must be rejected."""

    def test_rejects_localhost(self):
        with pytest.raises(ValueError, match="Blocked hostname"):
            validate_external_url("http://localhost/admin")

    def test_rejects_localhost_https(self):
        with pytest.raises(ValueError, match="Blocked hostname"):
            validate_external_url("https://localhost:8080/secret")

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_rejects_127_0_0_1(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_external_url("http://127.0.0.1/admin")

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_rejects_10_network(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443)),
        ]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_external_url("http://10.0.0.1/internal")

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_rejects_172_16_network(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("172.16.5.10", 443)),
        ]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_external_url("http://172.16.5.10/data")

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_rejects_192_168_network(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 443)),
        ]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_external_url("http://192.168.1.1/router")

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_rejects_metadata_endpoint(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80)),
        ]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_external_url("http://169.254.169.254/latest/meta-data/")

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_rejects_ipv6_loopback(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 443, 0, 0)),
        ]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_external_url("http://[::1]/admin")

    def test_rejects_internal_hostname(self):
        with pytest.raises(ValueError, match="Blocked hostname"):
            validate_external_url("http://db.internal/query")

    def test_rejects_local_hostname(self):
        with pytest.raises(ValueError, match="Blocked hostname"):
            validate_external_url("http://printer.local/config")

    def test_rejects_ftp_scheme(self):
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            validate_external_url("ftp://files.example.com/data")

    def test_rejects_file_scheme(self):
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            validate_external_url("file:///etc/passwd")

    def test_rejects_empty_hostname(self):
        with pytest.raises(ValueError):
            validate_external_url("http:///path")


class TestAllowedURLs:
    """URLs that must be accepted."""

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_allows_external_http(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
        ]
        result = validate_external_url("http://example.com/article")
        assert result == "http://example.com/article"

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_allows_external_https(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ]
        result = validate_external_url("https://example.com/article")
        assert result == "https://example.com/article"

    @patch("app.services.url_guard.socket.getaddrinfo")
    def test_allows_url_with_path_and_query(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ]
        url = "https://news.example.com/articles/2024?topic=insurance"
        assert validate_external_url(url) == url


class TestDNSResolutionFailure:
    """DNS failures should raise ValueError."""

    @patch("app.services.url_guard.socket.getaddrinfo", side_effect=socket.gaierror("Name resolution failed"))
    def test_raises_on_dns_failure(self, _mock):
        with pytest.raises(ValueError, match="Cannot resolve hostname"):
            validate_external_url("http://nonexistent.example.invalid/page")
