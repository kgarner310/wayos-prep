"""SSRF protection: validate URLs before outbound HTTP requests."""

import ipaddress
import socket
from urllib.parse import urlparse


_BLOCKED_HOSTNAME_SUFFIXES = (".internal", ".local")
_BLOCKED_HOSTNAMES = {"localhost"}


def validate_external_url(url: str) -> str:
    """Validate that a URL points to an external host, not internal infrastructure.

    Returns the validated URL string.
    Raises ValueError if the URL is unsafe.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname.")

    # Block known internal hostnames
    hostname_lower = hostname.lower()
    if hostname_lower in _BLOCKED_HOSTNAMES:
        raise ValueError(f"Blocked hostname: {hostname!r}")
    for suffix in _BLOCKED_HOSTNAME_SUFFIXES:
        if hostname_lower.endswith(suffix):
            raise ValueError(f"Blocked hostname: {hostname!r}")

    # Resolve hostname and check all resulting IPs
    try:
        addrinfo = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise ValueError(f"Cannot resolve hostname {hostname!r}: {e}")

    if not addrinfo:
        raise ValueError(f"No addresses found for hostname {hostname!r}")

    for family, _type, _proto, _canonname, sockaddr in addrinfo:
        ip_str = sockaddr[0]
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError(
                f"URL resolves to blocked IP {ip_str} (private/loopback/link-local/reserved)."
            )

    return url
