"""Live Website Fetch Service.

Fetches public website content safely for underwriting intelligence extraction.
Does NOT build a general-purpose crawler — fetches a controlled set of pages,
extracts readable text, normalizes whitespace/noise, and returns structured results.
"""

from __future__ import annotations

import logging
import re
from ipaddress import ip_address
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Defaults
_DEFAULT_TIMEOUT = 15
_DEFAULT_MAX_PAGES = 3
_DEFAULT_MAX_CHARS = 20_000
_USER_AGENT = "WAYOS-Prep/1.0 (Insurance Intelligence; +https://wayos.ai)"

# Subpaths worth checking for additional content (about/services pages)
_USEFUL_SUBPATHS = ["/about", "/services", "/about-us", "/our-services"]

# Patterns to strip from extracted text (nav clutter, cookie banners, etc.)
_NOISE_PATTERNS = [
    re.compile(r"skip\s+to\s+(main\s+)?content", re.IGNORECASE),
    re.compile(r"accept\s+(all\s+)?cookies?", re.IGNORECASE),
    re.compile(r"privacy\s+policy", re.IGNORECASE),
    re.compile(r"terms\s+(of\s+|&\s*)?(service|use)", re.IGNORECASE),
    re.compile(r"©\s*\d{4}", re.IGNORECASE),
    re.compile(r"all\s+rights\s+reserved", re.IGNORECASE),
]

# Private/internal network ranges to block (SSRF protection)
_BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}


def fetch_public_page_text(input_data: dict) -> dict:
    """Fetch public website content and return normalized text.

    Args:
        input_data: dict with keys:
            - website_url (str, required): primary URL to fetch
            - fetch_timeout_seconds (int, optional): per-request timeout (default 15)
            - max_pages (int, optional): max pages to fetch (default 3)
            - max_chars (int, optional): max total chars to return (default 20000)

    Returns:
        dict with:
            - source_url: the original URL
            - fetched_urls: list of URLs successfully fetched
            - raw_text: normalized extracted text
            - fetch_warnings: list of warning strings
            - success: bool
    """
    website_url = (input_data.get("website_url") or "").strip()
    timeout = input_data.get("fetch_timeout_seconds", _DEFAULT_TIMEOUT)
    max_pages = input_data.get("max_pages", _DEFAULT_MAX_PAGES)
    max_chars = input_data.get("max_chars", _DEFAULT_MAX_CHARS)

    result: dict = {
        "source_url": website_url,
        "fetched_urls": [],
        "raw_text": "",
        "fetch_warnings": [],
        "success": False,
    }

    # --- Validate URL ---
    if not website_url:
        result["fetch_warnings"].append("No website_url provided")
        return result

    validation_error = _validate_url(website_url)
    if validation_error:
        result["fetch_warnings"].append(validation_error)
        return result

    # Normalize URL
    if not website_url.startswith(("http://", "https://")):
        website_url = f"https://{website_url}"

    # --- Build list of URLs to fetch ---
    urls_to_fetch = [website_url]
    parsed = urlparse(website_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    for subpath in _USEFUL_SUBPATHS:
        candidate = urljoin(base_url, subpath)
        if candidate not in urls_to_fetch and len(urls_to_fetch) < max_pages:
            urls_to_fetch.append(candidate)

    # --- Fetch pages ---
    all_text_parts: list[str] = []
    total_chars = 0

    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        for url in urls_to_fetch:
            if total_chars >= max_chars:
                result["fetch_warnings"].append(
                    f"Character limit ({max_chars}) reached, stopped fetching"
                )
                break

            page_text, warning = _fetch_single_page(client, url)
            if warning:
                result["fetch_warnings"].append(warning)
            if page_text:
                result["fetched_urls"].append(url)
                all_text_parts.append(page_text)
                total_chars += len(page_text)

    if not all_text_parts:
        result["fetch_warnings"].append("No readable content could be extracted")
        return result

    # --- Combine and truncate ---
    combined = "\n\n".join(all_text_parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars]
        result["fetch_warnings"].append(
            f"Text truncated to {max_chars} characters"
        )

    result["raw_text"] = combined
    result["success"] = True

    logger.info(
        "Web fetch completed: url=%s pages=%d chars=%d",
        result["source_url"],
        len(result["fetched_urls"]),
        len(combined),
    )

    return result


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _validate_url(url: str) -> str | None:
    """Validate URL for safety. Returns error string or None if valid."""
    try:
        parsed = urlparse(url)
    except Exception:
        return f"Invalid URL format: {url}"

    # If URL has an explicit scheme, it must be http or https
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return f"URL scheme must be http or https, got: {parsed.scheme}"

    # Re-parse with scheme for hostname extraction if no scheme was given
    check_url = url if url.startswith(("http://", "https://")) else f"https://{url}"
    parsed = urlparse(check_url)

    hostname = parsed.hostname or ""

    # Block empty hostname
    if not hostname:
        return "URL has no hostname"

    # Block known internal hostnames
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        return f"Internal/private hostname blocked: {hostname}"

    # Block private IP ranges (SSRF protection)
    try:
        addr = ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            return f"Private/internal IP address blocked: {hostname}"
    except ValueError:
        # Not an IP address — that's fine, it's a domain name
        pass

    # Block common internal patterns
    if any(
        pattern in hostname.lower()
        for pattern in ("internal", "intranet", "169.254", "10.", "192.168")
    ):
        return f"Potentially internal hostname blocked: {hostname}"

    return None


def _fetch_single_page(client: httpx.Client, url: str) -> tuple[str | None, str | None]:
    """Fetch a single page and extract text. Returns (text, warning)."""
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.TimeoutException:
        return None, f"Timeout fetching {url}"
    except httpx.HTTPStatusError as e:
        return None, f"HTTP {e.response.status_code} fetching {url}"
    except httpx.RequestError as e:
        return None, f"Request error fetching {url}: {type(e).__name__}"

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        return None, f"Non-HTML content-type from {url}: {content_type}"

    text = _extract_text_from_html(response.text)
    if not text or len(text.strip()) < 50:
        return None, f"Insufficient readable content from {url}"

    return text, None


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML, stripping scripts/styles/nav noise."""
    soup = BeautifulSoup(html, "lxml")

    # Remove non-content elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    # Extract text
    text = soup.get_text(separator="\n")

    # Normalize whitespace
    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)

    text = "\n".join(lines)

    # Remove noise patterns
    for pattern in _NOISE_PATTERNS:
        text = pattern.sub("", text)

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text
