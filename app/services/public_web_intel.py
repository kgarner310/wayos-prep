"""Public Web Intelligence Extractor.

Extracts structured underwriting-relevant signals from public-facing
company content (website text, social text).

Supports two input paths:
1. Manual: raw_website_text / raw_social_text provided directly
2. Live fetch: website_url provided, text fetched via web_fetcher

Both paths feed into the same signal extraction pipeline.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# --- Keyword pattern groups for signal extraction ---

_OPERATIONS_PATTERNS: list[tuple[str, str]] = [
    (r"roof\w*\s+(?:replace|repair|install|restor)", "Roof replacement/repair/installation services"),
    (r"storm\s+(?:damage|restor|response|repair)", "Storm restoration work"),
    (r"steep[- ]slope", "Steep-slope roofing operations"),
    (r"flat\s+roof", "Flat roof operations"),
    (r"commercial\s+(?:roof|build|construct)", "Commercial roofing/construction"),
    (r"residential\s+(?:roof|build|construct|home)", "Residential construction/roofing"),
    (r"(?:long|short)\s*haul", "Long/short haul trucking operations"),
    (r"(?:hazmat|hazardous\s+material)", "Hazardous materials handling"),
    (r"(?:refrigerat|temperature[- ]control|reefer)", "Temperature-controlled freight operations"),
    (r"(?:cnc|machin|fabricat|weld)", "Manufacturing/fabrication operations"),
    (r"(?:food\s+(?:prep|service|handling)|catering)", "Food preparation/service operations"),
    (r"(?:tree\s+(?:remov|trim|service)|stump\s+grind)", "Tree removal/trimming services"),
    (r"(?:pesticide|herbicide|chemical\s+(?:application|spray))", "Chemical application services"),
    (r"(?:hvac|heating|cooling|air\s+condition)", "HVAC services"),
    (r"(?:plumb|electr|mechanical)\s+(?:service|contract|install)", "Mechanical/trade contracting"),
    (r"(?:excavat|grading|earth\s*work|demolit)", "Excavation/earthwork/demolition"),
    (r"(?:deliver|courier|dispatch|fleet)", "Delivery/fleet operations"),
    (r"(?:24[/ ]7|emergency|after[- ]hours)", "24/7 or emergency service operations"),
]

_SAFETY_PATTERNS: list[tuple[str, str]] = [
    (r"osha", "References OSHA compliance or procedures"),
    (r"(?:fall\s+protect|harness|tie[- ]off)", "Fall protection measures referenced"),
    (r"(?:ladder\s+safety|ladder\s+train)", "Ladder safety training mentioned"),
    (r"(?:safety\s+(?:program|train|committee|meeting|culture))", "Formal safety program or training referenced"),
    (r"(?:drug\s+(?:test|free|screen))", "Drug testing/screening program mentioned"),
    (r"(?:dot[- ]?(?:complia|certif|inspect))", "DOT compliance referenced"),
    (r"(?:return[- ]to[- ]work|modified\s+duty|light\s+duty)", "Return-to-work/modified duty program referenced"),
    (r"(?:ppe|personal\s+protective\s+equipment)", "PPE requirements referenced"),
    (r"(?:safety\s+officer|safety\s+director|safety\s+manager)", "Dedicated safety personnel mentioned"),
    (r"(?:incident\s+report|near[- ]miss|safety\s+record)", "Safety record or incident reporting mentioned"),
]

_SCALE_PATTERNS: list[tuple[str, str]] = [
    (r"(?:multi[- ](?:crew|team|location|state|site))", "Multi-crew/location operations"),
    (r"(?:nationwide|national|coast[- ]to[- ]coast)", "Nationwide operations"),
    (r"(?:regional|multi[- ]county|tri[- ]state)", "Regional operations"),
    (r"(?:fleet\s+of|vehicle|truck)\s*\d+", "Fleet size referenced"),
    (r"(?:\d+\s+(?:employee|crew|team|worker|staff))", "Employee count referenced"),
    (r"(?:million|M)\s*(?:in\s+)?(?:revenue|sales|annual)", "Revenue scale referenced"),
    (r"(?:since|founded|established|serving\s+since)\s*(\d{4})", "Company founding year"),
]

_CARRIER_PATTERNS: list[tuple[str, str]] = [
    (r"(?:certif(?:ied|ication)|licensed|accredit)", "Professional certifications/licensing"),
    (r"(?:manufacturer|brand)\s*(?:certif|authoriz|approv)", "Manufacturer certifications/authorizations"),
    (r"(?:subcontract|sub[- ]contract)", "Subcontractor usage referenced"),
    (r"(?:bond|bonded|surety)", "Bonding/surety referenced"),
    (r"(?:insur(?:ed|ance)|liability\s+cover)", "Insurance/liability coverage mentioned"),
    (r"(?:award|recognition|top\s+\d+)", "Industry awards or recognition"),
    (r"(?:BBB|better\s+business|chamber\s+of\s+commerce)", "Business association membership"),
    (r"(?:union|apprentice|journeyman)", "Union/apprenticeship affiliation"),
]

_YEAR_PATTERN = re.compile(r"(?:since|founded|established|serving\s+since)\s*(\d{4})", re.IGNORECASE)
_LOCATION_PATTERN = re.compile(
    r"(?:serving|service\s+area|located\s+in|based\s+in|covering)\s*:?\s*"
    r"(.+?)(?:\s+(?:since|for|with|our|we|the|\d{4})|\.|$)",
    re.IGNORECASE,
)


def extract_public_web_intel(input_data: dict) -> dict:
    """Extract structured underwriting-relevant signals from public content.

    Args:
        input_data: dict with optional keys:
            company_name, website_url, social_urls, raw_website_text,
            raw_social_text, industry, state

    Returns:
        Structured intelligence dict with company_identity, operations_signals,
        safety_signals, scale_signals, carrier_relevant_signals,
        observed_public_signals, cautions
    """
    company_name = input_data.get("company_name", "").strip()
    raw_website = input_data.get("raw_website_text", "").strip()
    raw_social = input_data.get("raw_social_text", "").strip()
    industry = input_data.get("industry", "")
    state = input_data.get("state", "")

    # Combine all available text for analysis
    combined_text = f"{raw_website}\n{raw_social}".strip()

    # --- Company identity ---
    company_identity = _extract_company_identity(company_name, combined_text)

    # --- Extract signals ---
    operations_signals = _extract_signals(combined_text, _OPERATIONS_PATTERNS)
    safety_signals = _extract_signals(combined_text, _SAFETY_PATTERNS)
    scale_signals = _extract_signals(combined_text, _SCALE_PATTERNS)
    carrier_relevant_signals = _extract_signals(combined_text, _CARRIER_PATTERNS)

    # --- Observed public signals (social-specific) ---
    observed_public_signals = []
    if raw_social:
        observed_public_signals = _extract_observed_signals(raw_social)

    # --- Cautions ---
    cautions = _build_cautions(raw_website, raw_social)

    logger.info(
        "Public web intel extracted: company=%s ops=%d safety=%d scale=%d carrier=%d",
        company_name, len(operations_signals), len(safety_signals),
        len(scale_signals), len(carrier_relevant_signals),
    )

    return {
        "company_identity": company_identity,
        "operations_signals": operations_signals[:8],
        "safety_signals": safety_signals[:5],
        "scale_signals": scale_signals[:5],
        "carrier_relevant_signals": carrier_relevant_signals[:5],
        "observed_public_signals": observed_public_signals[:5],
        "cautions": cautions,
    }


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _extract_company_identity(company_name: str, text: str) -> dict:
    """Extract company identity facts from text."""
    identity: dict = {
        "company_name": company_name or "",
        "founded_year": None,
        "service_area": [],
    }

    if not text:
        return identity

    # Founded year
    year_match = _YEAR_PATTERN.search(text)
    if year_match:
        year = int(year_match.group(1))
        if 1900 <= year <= 2026:
            identity["founded_year"] = year

    # Service area
    loc_match = _LOCATION_PATTERN.search(text)
    if loc_match:
        raw_areas = loc_match.group(1)
        areas = [a.strip() for a in re.split(r",\s*|\s+and\s+", raw_areas) if a.strip()]
        identity["service_area"] = areas[:5]

    return identity


def _extract_signals(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    """Extract signals by matching patterns against text."""
    if not text:
        return []

    text_lower = text.lower()
    signals = []
    seen = set()

    for pattern, description in patterns:
        if re.search(pattern, text_lower):
            if description not in seen:
                seen.add(description)
                signals.append(description)

    return signals


def _extract_observed_signals(social_text: str) -> list[str]:
    """Extract observed signals from social media text."""
    signals = []
    text_lower = social_text.lower()

    # Look for activity indicators
    activity_patterns = [
        (r"(?:new|recent|latest)\s+(?:project|job|contract)", "Recent project activity posted"),
        (r"(?:hiring|looking\s+for|now\s+hiring|join\s+our)", "Active hiring activity"),
        (r"(?:storm|weather|disaster)\s+(?:response|work|damage)", "Storm/weather response activity"),
        (r"(?:award|won|recognized|thank)", "Recent awards or recognition posted"),
        (r"(?:training|certif|safety\s+(?:day|week))", "Training or safety event activity"),
        (r"(?:expand|growth|new\s+(?:location|office|branch))", "Expansion or growth signals"),
        (r"(?:community|volunteer|charit|donat)", "Community involvement activity"),
    ]

    seen = set()
    for pattern, description in activity_patterns:
        if re.search(pattern, text_lower):
            if description not in seen:
                seen.add(description)
                signals.append(description)

    return signals


def _build_cautions(raw_website: str, raw_social: str) -> list[str]:
    """Build caution notes about data sourcing and reliability."""
    cautions = []

    if raw_website or raw_social:
        cautions.append(
            "Public content may reflect marketing language and should not be "
            "treated as independently verified fact"
        )

    if raw_social:
        cautions.append(
            "Social media signals are summarized from observed public posts "
            "and may not reflect current operational reality"
        )

    if not raw_website and not raw_social:
        cautions.append(
            "No public web content was provided — intelligence extraction "
            "is limited to account profile data"
        )

    return cautions


# ============================================================
# LIVE-FETCH VARIANT
# ============================================================


def extract_public_web_intel_with_fetch(input_data: dict) -> dict:
    """Fetch website content live, then extract public web intel.

    Combines web_fetcher.fetch_public_page_text with extract_public_web_intel.
    If raw_website_text is also provided, it is appended to fetched content.

    Args:
        input_data: dict with keys:
            - website_url (str): URL to fetch
            - company_name, industry, state: context
            - raw_website_text (str, optional): additional manual text
            - raw_social_text (str, optional): social text
            - fetch_timeout_seconds, max_pages, max_chars: fetch options

    Returns:
        dict with:
            - public_web_intel: the standard extraction result
            - fetch_summary: fetch metadata (source_url, fetched_urls, warnings, success)
    """
    from app.services.web_fetcher import fetch_public_page_text

    website_url = (input_data.get("website_url") or "").strip()

    # --- Attempt live fetch if URL provided ---
    fetch_result = {"source_url": "", "fetched_urls": [], "raw_text": "",
                    "fetch_warnings": [], "success": False}
    if website_url:
        fetch_result = fetch_public_page_text(input_data)

    # --- Combine fetched text with any manual text ---
    fetched_text = fetch_result.get("raw_text", "")
    manual_text = (input_data.get("raw_website_text") or "").strip()
    combined_website_text = "\n\n".join(
        part for part in [fetched_text, manual_text] if part
    )

    # --- Run standard extraction ---
    extraction_input = {
        "company_name": input_data.get("company_name", ""),
        "website_url": website_url,
        "raw_website_text": combined_website_text,
        "raw_social_text": input_data.get("raw_social_text", ""),
        "industry": input_data.get("industry", ""),
        "state": input_data.get("state", ""),
    }
    intel = extract_public_web_intel(extraction_input)

    # Add fetch-sourced caution if live content was used
    if fetch_result.get("success"):
        intel["cautions"].append(
            "Content was fetched from a live public website and may have "
            "changed since the time of retrieval"
        )

    fetch_summary = {
        "source_url": fetch_result.get("source_url", ""),
        "fetched_urls": fetch_result.get("fetched_urls", []),
        "fetch_warnings": fetch_result.get("fetch_warnings", []),
        "success": fetch_result.get("success", False),
        "fetched_char_count": len(fetched_text),
    }

    logger.info(
        "Public web intel with fetch: url=%s fetch_success=%s signals_extracted=%s",
        website_url, fetch_summary["success"],
        len(intel.get("operations_signals", [])) > 0,
    )

    return {
        "public_web_intel": intel,
        "fetch_summary": fetch_summary,
    }
