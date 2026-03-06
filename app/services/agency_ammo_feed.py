"""Agency Ammo Feed — aggregated intelligence from producer usage patterns.

Turns individual producer queries, coverage gap outputs, and ammo questions
into agency-level insight: top question themes, rising risk topics, common
coverage gaps, and suggested conversation openers.

Designed for future dashboard/UI consumption with per-agency scoping,
trend deltas, and cross-user analytics.
"""

import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.models import Query
from app.services.coverage_gap_detector import (
    INDUSTRY_EXPECTED_COVERAGES,
    _normalize_industry,
    _COVERAGE_DISPLAY,
)
from app.services.producer_ammo import (
    _INDUSTRY_TOP_QUESTIONS,
    _INDUSTRY_COVERAGE_TRAPS,
    _INDUSTRY_UNDERWRITING_FLAGS,
    _GENERIC_TOP_QUESTIONS,
    _GENERIC_COVERAGE_TRAPS,
    _GENERIC_UNDERWRITING_FLAGS,
)

logger = logging.getLogger(__name__)


# ============================================================
# QUESTION THEME NORMALIZATION
# ============================================================
# Maps common question keywords/phrases to canonical theme labels.

_THEME_KEYWORDS = [
    (r"subcontract|certificate|additional insured|coi|ai\b", "subcontractor certificate tracking"),
    (r"personal vehicle|hired.?non.?owned|hnoa|employee.+vehicle", "personal vehicle use on company business"),
    (r"tool|equipment.+theft|inland marine|floater", "tools and equipment theft"),
    (r"fall.+protection|falls?.+height|harness|scaffold", "fall protection and height safety"),
    (r"mvr|motor vehicle|driver.+eligib|driver.+screen", "driver eligibility and MVR concerns"),
    (r"lockout.?tagout|loto|machine guard", "lockout/tagout and machine guarding"),
    (r"mod\b|experience mod|modification rate", "experience modification concerns"),
    (r"fleet|vehicle.+count|take.?home.+vehicle|telematics", "fleet management and auto exposure"),
    (r"waiver.+subrogation|wos\b", "waiver of subrogation requirements"),
    (r"umbrella|excess.+liab", "umbrella and excess liability adequacy"),
    (r"cyber|data breach|ransomware|pii", "cyber liability exposure"),
    (r"epli|employment.+practice|wrongful.+termination|harassment", "employment practices liability"),
    (r"builders?.+risk|construction.+progress", "builders risk and project coverage"),
    (r"business.+income|extra.+expense|bi\b.+coverage", "business income adequacy"),
    (r"osha|citation|safety.+program|safety.+audit", "OSHA compliance and safety programs"),
    (r"slope|steep|roof.+type|residential.+commercial", "mixed residential/commercial operations"),
    (r"cargo|load.+value|hazmat|freight", "cargo and freight exposure"),
    (r"liquor|alcohol|tips.+cert|servsafe", "liquor liability and alcohol service"),
    (r"delivery|food.+truck|catering", "delivery and off-premise operations"),
    (r"property.+value|apprais|replacement.+cost", "property valuation adequacy"),
    (r"claim|loss.+run|loss.+history|incident", "claims history and loss narrative"),
    (r"contract.+requirement|contract.+limit|ai.+endorsement", "contract insurance requirements"),
    (r"payroll|headcount|territory|job.+mix", "operational changes and payroll"),
    (r"storm|wind|hurricane|named.?storm|deductible", "wind and named-storm exposure"),
    (r"flood|fema|flood.+zone", "flood coverage"),
    (r"earthquake|seismic", "earthquake exposure"),
]


def normalize_question_theme(question: str) -> str | None:
    """Map a question string to a canonical theme label using keyword matching."""
    q_lower = question.lower()
    for pattern, theme in _THEME_KEYWORDS:
        if re.search(pattern, q_lower):
            return theme
    return None


def _extract_themes_from_questions(questions: list[str]) -> list[str]:
    """Extract all matching themes from a list of questions."""
    themes = []
    for q in questions:
        theme = normalize_question_theme(q)
        if theme:
            themes.append(theme)
    return themes


# ============================================================
# SEEDED INDUSTRY INTELLIGENCE
# ============================================================
# Pre-built intelligence derived from existing service data for
# when query logs are sparse or empty.

# Industry → common question themes (seeded from producer ammo questions)
_SEEDED_QUESTION_THEMES: dict[str, list[str]] = {}

# Industry → common coverage gaps (seeded from expected coverage maps)
_SEEDED_COVERAGE_GAPS: dict[str, list[str]] = {}

# Industry → rising risk topics (seeded from underwriting flags + coverage traps)
_SEEDED_RISING_TOPICS: dict[str, list[str]] = {}

# Industry → suggested openers (seeded from top questions)
_SEEDED_OPENERS: dict[str, list[str]] = {}


def _build_seeded_data():
    """One-time build of seeded data from existing service constants."""
    if _SEEDED_QUESTION_THEMES:
        return  # Already built

    for industry, questions in _INDUSTRY_TOP_QUESTIONS.items():
        themes = _extract_themes_from_questions(questions)
        _SEEDED_QUESTION_THEMES[industry] = themes or [
            "subcontractor certificate tracking",
            "fleet management and auto exposure",
            "experience modification concerns",
        ]
        _SEEDED_OPENERS[industry] = questions[:4]

    for industry, traps in _INDUSTRY_COVERAGE_TRAPS.items():
        gaps = []
        for trap in traps:
            theme = normalize_question_theme(trap)
            if theme:
                gaps.append(theme)
            else:
                # Use a cleaned-up version of the trap as a gap label
                gaps.append(trap.split(".")[0].strip().lower())
        _SEEDED_COVERAGE_GAPS[industry] = gaps[:4]

    for industry, flags in _INDUSTRY_UNDERWRITING_FLAGS.items():
        topics = []
        for flag in flags:
            theme = normalize_question_theme(flag)
            if theme:
                topics.append(theme)
            else:
                topics.append(flag.split(".")[0].strip().lower())
        # Also pull from coverage traps for rising topics
        if industry in _INDUSTRY_COVERAGE_TRAPS:
            for trap in _INDUSTRY_COVERAGE_TRAPS[industry]:
                theme = normalize_question_theme(trap)
                if theme and theme not in topics:
                    topics.append(theme)
        _SEEDED_RISING_TOPICS[industry] = topics[:4]


# ============================================================
# QUERY LOG AGGREGATION
# ============================================================

def _query_recent_logs(
    db: Session | None,
    industry: str,
    state: str,
    date_range_days: int,
) -> list[dict]:
    """Pull recent query logs matching filters. Returns list of log dicts."""
    if db is None:
        return []

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=date_range_days)
        q = db.query(Query).filter(Query.created_at >= cutoff)

        if industry:
            q = q.filter(Query.requested_industry == industry)
        if state:
            q = q.filter(Query.requested_state == state.lower())

        q = q.order_by(Query.created_at.desc()).limit(500)
        rows = q.all()

        return [
            {
                "industry": row.requested_industry,
                "state": row.requested_state,
                "query": row.raw_query or "",
                "created_at": row.created_at,
            }
            for row in rows
        ]
    except Exception:
        logger.warning("Failed to query logs for agency feed, falling back to seeded data")
        return []


# ============================================================
# AGGREGATION HELPERS
# ============================================================

def summarize_top_themes(
    log_entries: list[dict],
    industry: str,
    max_items: int = 5,
) -> list[str]:
    """Identify top question themes from logs, or fall back to seeded data."""
    _build_seeded_data()

    if log_entries:
        queries = [entry["query"] for entry in log_entries if entry.get("query")]
        themes = _extract_themes_from_questions(queries)
        if themes:
            counter = Counter(themes)
            return [theme for theme, _ in counter.most_common(max_items)]

    # Fallback to seeded data
    return list(_SEEDED_QUESTION_THEMES.get(industry, [
        "subcontractor certificate tracking",
        "personal vehicle use on company business",
        "fleet management and auto exposure",
    ]))[:max_items]


def summarize_rising_topics(
    log_entries: list[dict],
    industry: str,
    date_range_days: int,
    max_items: int = 5,
) -> list[str]:
    """Identify rising topics by comparing recent vs prior frequency."""
    _build_seeded_data()

    if len(log_entries) >= 10:
        midpoint = len(log_entries) // 2
        recent = log_entries[:midpoint]
        older = log_entries[midpoint:]

        recent_themes = Counter(_extract_themes_from_questions(
            [e["query"] for e in recent if e.get("query")]
        ))
        older_themes = Counter(_extract_themes_from_questions(
            [e["query"] for e in older if e.get("query")]
        ))

        rising = []
        for theme, count in recent_themes.most_common():
            old_count = older_themes.get(theme, 0)
            if count > old_count:
                rising.append(theme)
        if rising:
            return rising[:max_items]

        # If no clear trend, use repeated recent appearances
        if recent_themes:
            return [t for t, _ in recent_themes.most_common(max_items)]

    # Fallback to seeded data
    return list(_SEEDED_RISING_TOPICS.get(industry, [
        "mixed residential/commercial operations",
        "waiver of subrogation requirements",
        "driver eligibility and MVR concerns",
    ]))[:max_items]


def summarize_common_gaps(
    industry: str,
    max_items: int = 5,
) -> list[str]:
    """Return common coverage gaps for an industry."""
    _build_seeded_data()

    # Start with industry-expected coverages that are commonly missed
    expected = INDUSTRY_EXPECTED_COVERAGES.get(industry, [])
    # Pick coverages that are commonly overlooked (not the obvious ones)
    commonly_missed = [
        cov for cov in expected
        if cov in ("inland_marine", "hired_non_owned_auto", "umbrella",
                    "builders_risk", "cargo", "epli", "cyber",
                    "professional_liability")
    ]
    gap_labels = [
        _COVERAGE_DISPLAY.get(cov, cov.replace("_", " ").title())
        for cov in commonly_missed
    ]

    # Add seeded gaps
    seeded = _SEEDED_COVERAGE_GAPS.get(industry, [])
    for g in seeded:
        if g not in gap_labels:
            gap_labels.append(g)

    if not gap_labels:
        gap_labels = [
            "hired and non-owned auto",
            "cyber liability",
            "umbrella / excess liability",
        ]

    return gap_labels[:max_items]


def suggest_openers_from_patterns(
    industry: str,
    top_themes: list[str],
    max_items: int = 4,
) -> list[str]:
    """Generate suggested openers based on top themes and industry data."""
    _build_seeded_data()

    # Pull from seeded openers for the industry
    openers = list(_SEEDED_OPENERS.get(industry, []))

    if not openers:
        # Use generic openers
        openers = list(_GENERIC_TOP_QUESTIONS[:4])

    # If we have themes, ensure openers cover them
    # Pick openers that relate to top themes
    themed_openers = []
    remaining_openers = []
    for opener in openers:
        theme = normalize_question_theme(opener)
        if theme and theme in top_themes:
            themed_openers.append(opener)
        else:
            remaining_openers.append(opener)

    # Prioritize themed openers, then fill with remaining
    result = themed_openers + remaining_openers
    return result[:max_items]


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def build_agency_ammo_feed(filters: dict, db: Session | None = None) -> dict:
    """Build the Agency Ammo Feed.

    Args:
        filters: dict with optional keys:
            industry, state, date_range_days, account_stage
        db: Optional SQLAlchemy session for query log access

    Returns:
        Structured feed dict with summary containing:
        top_question_themes, rising_risk_topics, common_coverage_gaps,
        suggested_openers
    """
    industry_raw = filters.get("industry", "")
    industry = _normalize_industry(industry_raw)
    state = (filters.get("state") or "").upper()
    date_range_days = int(filters.get("date_range_days", 30))
    if date_range_days < 1:
        date_range_days = 30

    logger.info(
        "Agency ammo feed: industry=%s state=%s date_range=%d days",
        industry, state, date_range_days,
    )

    # Query logs for aggregation
    log_entries = _query_recent_logs(db, industry, state, date_range_days)

    # Build aggregations
    top_themes = summarize_top_themes(log_entries, industry)
    rising_topics = summarize_rising_topics(log_entries, industry, date_range_days)
    common_gaps = summarize_common_gaps(industry)
    openers = suggest_openers_from_patterns(industry, top_themes)

    logger.info(
        "Agency ammo feed generated: themes=%d rising=%d gaps=%d openers=%d log_entries=%d",
        len(top_themes), len(rising_topics), len(common_gaps), len(openers),
        len(log_entries),
    )

    return {
        "industry": industry_raw or industry,
        "state": state,
        "date_range_days": date_range_days,
        "summary": {
            "top_question_themes": top_themes,
            "rising_risk_topics": rising_topics,
            "common_coverage_gaps": common_gaps,
            "suggested_openers": openers,
        },
    }
