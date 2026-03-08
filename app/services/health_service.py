"""Account Health Card Engine — fast, deterministic health scoring.

Produces an instant health card for any account, even with partial data.
Reuses industry-level gap detection from coverage_gap_detector.py.
"""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Account, AccountHealth
from app.services.coverage_gap_detector import (
    INDUSTRY_EXPECTED_COVERAGES,
    detect_gaps,
)

logger = logging.getLogger(__name__)

# Workers comp mod thresholds
MOD_UNITY = 1.0
MOD_ELEVATED = 1.10
MOD_HIGH = 1.25

# Industry average mods (approximate)
INDUSTRY_AVG_MODS = {
    "roofing": 1.08,
    "trucking": 1.05,
    "manufacturing": 0.98,
    "restaurant": 0.95,
    "landscaping": 0.97,
    "hvac": 1.02,
}

# Critical coverages that trigger duty-to-advise alerts if missing
DUTY_TO_ADVISE_COVERAGES = {
    "workers_comp",
    "general_liability",
    "commercial_auto",
}

# Data fields used for confidence calculation
CONFIDENCE_FIELDS = [
    "industry",
    "state",
    "employee_count",
    "current_coverages",
    "workers_comp_mod",
    "current_carriers",
    "claims_summary",
    "annual_revenue",
]


def _compute_coverage_score(account: Account) -> tuple[int, list[str], int]:
    """Score coverage completeness. Returns (score, issues, duty_alerts)."""
    industry = (account.industry or "").lower()
    expected = INDUSTRY_EXPECTED_COVERAGES.get(industry, [])
    current = set(c.lower() for c in (account.current_coverages or []))

    if not expected:
        # Unknown industry — can't score
        return 50, ["Industry not recognized for coverage benchmarking"], 0

    if not current:
        return 20, ["No current coverages on file"], len(DUTY_TO_ADVISE_COVERAGES)

    missing = [c for c in expected if c not in current]
    coverage_ratio = (len(expected) - len(missing)) / len(expected)
    score = int(coverage_ratio * 100)

    issues = []
    duty_alerts = 0
    for cov in missing:
        label = cov.replace("_", " ").title()
        if cov in DUTY_TO_ADVISE_COVERAGES:
            issues.append(f"No {label} detected")
            duty_alerts += 1
        else:
            issues.append(f"Missing {label} coverage")

    return max(score, 10), issues, duty_alerts


def _compute_workers_comp_score(account: Account) -> tuple[int, list[str]]:
    """Score workers comp health. Returns (score, issues)."""
    mod = float(account.workers_comp_mod) if account.workers_comp_mod is not None else None
    issues = []

    if mod is None:
        return 50, ["Workers comp mod not available"]

    if mod <= 0.85:
        score = 95
    elif mod <= MOD_UNITY:
        score = 85
    elif mod <= MOD_ELEVATED:
        score = 65
        issues.append(f"Elevated workers comp mod ({mod:.2f})")
    elif mod <= MOD_HIGH:
        score = 45
        issues.append(f"High workers comp mod ({mod:.2f})")
    else:
        score = 25
        issues.append(f"Very high workers comp mod ({mod:.2f})")

    # Claims signal
    claims = account.claims_summary or {}
    open_claims = claims.get("open_claims", 0)
    if open_claims and open_claims > 0:
        issues.append(f"{open_claims} open claim(s)")
        score = max(score - 10, 10)

    total_3yr = claims.get("total_claims_3yr", 0)
    if total_3yr and total_3yr >= 3:
        issues.append(f"{total_3yr} claims in last 3 years")
        score = max(score - 5, 10)

    return score, issues


def _compute_carrier_fit_score(account: Account) -> tuple[int, list[str]]:
    """Score carrier fit. Returns (score, issues)."""
    carriers = account.current_carriers or []
    if not carriers:
        return 50, ["Current carriers not on file"]

    # Basic heuristic: having multiple carriers suggests good market strategy
    if len(carriers) >= 3:
        return 80, []
    elif len(carriers) >= 2:
        return 70, []
    else:
        return 60, ["Single carrier relationship — limited market leverage"]


def _compute_confidence(account: Account) -> float:
    """Calculate data confidence as fraction of available fields."""
    available = 0
    for field in CONFIDENCE_FIELDS:
        val = getattr(account, field, None)
        if val is not None and val != "" and val != []:
            available += 1
    return round(available / len(CONFIDENCE_FIELDS), 3)


def compute_account_health(account: Account, db: Session) -> AccountHealth:
    """Compute and persist account health card.

    This is deterministic and fast — no LLM calls. Safe to call synchronously
    during account creation.
    """
    coverage_score, coverage_issues, duty_alerts = _compute_coverage_score(account)
    wc_score, wc_issues = _compute_workers_comp_score(account)
    carrier_score, carrier_issues = _compute_carrier_fit_score(account)
    confidence = _compute_confidence(account)

    # Weighted overall score: coverage 40%, WC 30%, carrier 30%
    overall = int(coverage_score * 0.4 + wc_score * 0.3 + carrier_score * 0.3)

    # Partial data penalty
    if confidence < 0.3:
        overall = min(overall, 50)
        coverage_issues.append("Limited information available")

    top_issues = coverage_issues + wc_issues + carrier_issues

    # Upsert health record
    health = db.query(AccountHealth).filter(AccountHealth.account_id == account.id).first()
    if health is None:
        health = AccountHealth(account_id=account.id)
        db.add(health)

    health.overall_score = overall
    health.coverage_score = coverage_score
    health.workers_comp_score = wc_score
    health.carrier_fit_score = carrier_score
    health.confidence = Decimal(str(confidence))
    health.top_issues_json = top_issues[:10]  # Cap at 10
    health.duty_to_advise_alert_count = duty_alerts

    db.flush()
    return health
