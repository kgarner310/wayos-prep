"""Meeting Brief Generator — structured pre-meeting intelligence from Industry Knowledge Objects.

Assembles a meeting preparation brief for a given industry using the
IndustryProfile system. Designed to give producers a quick, actionable
overview before walking into a renewal or new business meeting.
"""

import logging
from typing import Optional

from app.knowledge.industry_profiles import get_industry_profile

logger = logging.getLogger(__name__)


def generate_meeting_brief(industry: str) -> dict:
    """Generate a structured meeting preparation brief for an industry.

    Args:
        industry: Industry name (e.g. "roofing", "restaurant", "trucking company")

    Returns:
        {
            "industry": str,
            "top_exposures": list[str],
            "common_claims": list[str],
            "recommended_talking_points": list[str],
            "discovery_questions": list[str],
            "coverage_watchouts": list[str],
            "policy_lines": list[str],
            "risk_score_factors": dict[str, str],
            "data_sources": list[str],
            "confidence": float,
            "office_learnings": list[str],
        }
    """
    profile = get_industry_profile(industry)
    if profile is None:
        logger.warning("No industry profile found for meeting brief: %s", industry)
        return {
            "industry": industry,
            "top_exposures": [],
            "common_claims": [],
            "recommended_talking_points": [],
            "discovery_questions": [],
            "coverage_watchouts": [],
            "policy_lines": [],
            "risk_score_factors": {},
            "data_sources": [],
            "confidence": 0.0,
            "office_learnings": [],
            "error": f"No industry profile found for '{industry}'",
        }

    brief = {
        "industry": profile.industry,
        "top_exposures": list(profile.top_exposures),
        "common_claims": list(profile.common_claims),
        "recommended_talking_points": list(profile.recommended_talking_points),
        "discovery_questions": list(profile.discovery_questions),
        "coverage_watchouts": list(profile.coverage_gaps),
        "policy_lines": list(profile.policy_lines),
        "risk_score_factors": dict(profile.risk_score_factors),
        "data_sources": list(profile.data_sources),
        "confidence": profile.confidence,
        "office_learnings": list(profile.office_learnings),
    }

    logger.info(
        "Meeting brief generated: industry=%s exposures=%d questions=%d confidence=%.2f",
        profile.industry, len(brief["top_exposures"]),
        len(brief["discovery_questions"]), brief["confidence"],
    )

    return brief
