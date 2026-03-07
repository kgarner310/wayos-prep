"""Industry Loader — unified lookup across Nkb2E core industries and ported tier profiles.

Provides a single entry point for resolving industry names, fetching risk data,
and enriching coverage gap / producer ammo responses with deeper industry intelligence.

Resolution order:
  1. Nkb2E core industries (roofing, trucking, manufacturing, restaurant, landscaping, hvac)
  2. Ported 80-industry tier profiles (synonym matching)
  3. None if no match
"""

import logging

from app.data.industry_profiles import (
    INDUSTRY_PROFILES,
    resolve_industry as _resolve_tier,
    get_profile as _get_tier_profile,
)

logger = logging.getLogger(__name__)

# Nkb2E's original 6 core industries — these have deep coverage gap / ammo data
CORE_INDUSTRIES = {"roofing", "trucking", "manufacturing", "restaurant", "landscaping", "hvac"}

# Map core aliases to core slugs (superset of coverage_gap_detector._INDUSTRY_ALIASES)
_CORE_ALIASES = {
    "roofing contractor": "roofing",
    "roofing contractors": "roofing",
    "roofer": "roofing",
    "roofers": "roofing",
    "truck": "trucking",
    "trucking company": "trucking",
    "trucking companies": "trucking",
    "mfg": "manufacturing",
    "manufacturer": "manufacturing",
    "manufacturers": "manufacturing",
    "food service": "restaurant",
    "restaurants": "restaurant",
    "dining": "restaurant",
    "lawn care": "landscaping",
    "landscape": "landscaping",
    "landscapers": "landscaping",
    "heating and cooling": "hvac",
    "hvac contractor": "hvac",
    "hvac contractors": "hvac",
    "heating ventilation": "hvac",
}


def resolve(raw: str) -> tuple[str, str]:
    """Resolve a raw industry string to a canonical slug and source.

    Returns:
        (slug, source) where source is "core", "tier", or "unknown"
    """
    key = raw.strip().lower()

    # 1. Direct core match
    if key in CORE_INDUSTRIES:
        return key, "core"

    # 2. Core alias match
    core_slug = _CORE_ALIASES.get(key)
    if core_slug:
        return core_slug, "core"

    # 3. Tier profile match (synonym index)
    tier_slug = _resolve_tier(key)
    if tier_slug:
        return tier_slug, "tier"

    return key, "unknown"


def get_enrichment(raw_industry: str) -> dict:
    """Get enrichment data for an industry.

    Returns a dict with available enrichment fields. Always returns at least
    an empty dict — never None.

    For core industries: returns tier profile if a matching tier profile exists.
    For tier industries: returns the full tier profile.
    For unknown industries: returns empty dict.
    """
    slug, source = resolve(raw_industry)

    if source == "unknown":
        logger.debug("No enrichment for unknown industry: %s", raw_industry)
        return {}

    # For core industries, try to find matching tier profile
    # (e.g. "roofing" might match a tier profile via synonyms)
    if source == "core":
        tier_slug = _resolve_tier(raw_industry)
        if tier_slug:
            profile = _get_tier_profile(tier_slug)
            if profile:
                return profile
        return {}

    # For tier industries, return the full profile
    profile = _get_tier_profile(slug)
    return profile or {}


def get_conversation_prompts(raw_industry: str) -> list[str]:
    """Get conversation prompts for an industry from tier data."""
    enrichment = get_enrichment(raw_industry)
    return list(enrichment.get("conversation_prompts", []))


def get_wc_claims(raw_industry: str) -> list[str]:
    """Get top workers comp claim types for an industry."""
    enrichment = get_enrichment(raw_industry)
    return list(enrichment.get("wc_claims", []))


def get_gl_exposures(raw_industry: str) -> list[str]:
    """Get key GL exposures for an industry."""
    enrichment = get_enrichment(raw_industry)
    return list(enrichment.get("gl_exposures", []))


def get_auto_claims(raw_industry: str) -> list[str]:
    """Get common auto claim scenarios for an industry."""
    enrichment = get_enrichment(raw_industry)
    return list(enrichment.get("auto_claims", []))


def get_regional_notes(raw_industry: str) -> str:
    """Get regional risk notes for an industry."""
    enrichment = get_enrichment(raw_industry)
    return enrichment.get("regional_notes", "")


def list_all_industries() -> list[dict]:
    """List all known industries (core + tier) with slug, name, tier, and source."""
    result = []

    # Core industries first
    for slug in sorted(CORE_INDUSTRIES):
        result.append({
            "slug": slug,
            "display_name": slug.replace("_", " ").title(),
            "tier": 0,
            "source": "core",
        })

    # Tier industries
    for slug, profile in sorted(INDUSTRY_PROFILES.items()):
        result.append({
            "slug": slug,
            "display_name": profile["display_name"],
            "tier": profile["tier"],
            "source": "tier",
        })

    return result
