"""Live Website Fetch Service.

Fetches public website content safely for underwriting intelligence extraction.
Does NOT build a general-purpose crawler — fetches a controlled set of pages,
extracts readable text, normalizes whitespace/noise, and returns structured results.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.url_guard import validate_external_url

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

    # Normalize URL before validation (validate_external_url requires a scheme)
    if not website_url.startswith(("http://", "https://")):
        website_url = f"https://{website_url}"

    # SECURITY: SSRF protection — validate_external_url() MUST run before any
    # outbound request. Redirects are rejected in _fetch_single_page. Do not set
    # follow_redirects=True unless every redirect target is also revalidated.
    try:
        validate_external_url(website_url)
    except ValueError as e:
        result["fetch_warnings"].append(str(e))
        return result

    # --- Build list of URLs to fetch ---
    urls_to_fetch = [website_url]
    parsed = urlparse(website_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    for subpath in _USEFUL_SUBPATHS:
        candidate = urljoin(base_url, subpath)
        if candidate not in urls_to_fetch and len(urls_to_fetch) < max_pages:
            # Subpaths share the same validated origin, no re-validation needed
            urls_to_fetch.append(candidate)

    # --- Fetch pages ---
    all_text_parts: list[str] = []
    total_chars = 0

    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
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

    # Reject redirects explicitly — do not follow to unvalidated targets
    if response.is_redirect or response.status_code in (301, 302, 303, 307, 308):
        return None, f"URL returned redirect ({response.status_code}). Redirects disabled for security."

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
