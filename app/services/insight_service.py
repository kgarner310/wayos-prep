"""Insight Feed Service — rule-driven insights for account dashboards.

Generates short, actionable insight items from account data and health card.
No LLM calls — purely deterministic.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Account, AccountHealth, DealOutcome
from app.services.coverage_gap_detector import INDUSTRY_EXPECTED_COVERAGES

logger = logging.getLogger(__name__)


def generate_insights(
    account: Account,
    health: Optional[AccountHealth],
    db: Session,
) -> list[dict]:
    """Generate insight feed items for an account.

    Returns list of dicts with: insight_type, title, subtitle,
    suggested_action, severity, timestamp.
    """
    insights = []
    now = datetime.now(timezone.utc)

    # Coverage alerts from health card
    if health and health.top_issues_json:
        for issue in health.top_issues_json[:3]:
            if "No " in issue and "detected" in issue:
                insights.append({
                    "insight_type": "duty_to_advise",
                    "title": issue,
                    "subtitle": "This is a duty-to-advise concern",
                    "suggested_action": "Discuss with client and document recommendation",
                    "severity": "critical",
                    "timestamp": now.isoformat(),
                })
            elif "Missing" in issue:
                insights.append({
                    "insight_type": "coverage_alert",
                    "title": issue,
                    "subtitle": "Gap vs industry standard coverage program",
                    "suggested_action": "Recommend adding this coverage at next review",
                    "severity": "high",
                    "timestamp": now.isoformat(),
                })

    # Workers comp signals
    mod = float(account.workers_comp_mod) if account.workers_comp_mod is not None else None
    if mod is not None and mod > 1.10:
        insights.append({
            "insight_type": "workers_comp_signal",
            "title": f"Experience mod elevated at {mod:.2f}",
            "subtitle": "Mod above 1.10 indicates adverse loss experience",
            "suggested_action": "Review loss control program and return-to-work protocols",
            "severity": "high" if mod > 1.20 else "medium",
            "timestamp": now.isoformat(),
        })

    # Safety / claims signal
    claims = account.claims_summary or {}
    open_claims = claims.get("open_claims", 0)
    if open_claims and open_claims > 0:
        insights.append({
            "insight_type": "workers_comp_signal",
            "title": f"{open_claims} open claim(s) on file",
            "subtitle": "Open claims affect renewal pricing and carrier appetite",
            "suggested_action": "Request claims detail and discuss loss control measures",
            "severity": "medium",
            "timestamp": now.isoformat(),
        })

    # Market signals from outcomes
    industry = (account.industry or "").lower()
    if industry:
        recent_outcomes = (
            db.query(DealOutcome)
            .filter(DealOutcome.industry == industry)
            .order_by(DealOutcome.created_at.desc())
            .limit(5)
            .all()
        )
        lost_count = sum(1 for o in recent_outcomes if o.outcome == "lost")
        if lost_count >= 2:
            insights.append({
                "insight_type": "market_signal",
                "title": f"Competitive pressure in {industry}",
                "subtitle": f"{lost_count} recent lost deals in this industry",
                "suggested_action": "Review pricing strategy and carrier relationships",
                "severity": "medium",
                "timestamp": now.isoformat(),
            })

    # Opportunity signals
    current = set(c.lower() for c in (account.current_coverages or []))
    if "cyber" not in current and account.employee_count and account.employee_count >= 10:
        insights.append({
            "insight_type": "opportunity",
            "title": "Cyber liability cross-sell opportunity",
            "subtitle": "No cyber coverage detected for business with 10+ employees",
            "suggested_action": "Introduce cyber liability discussion at next meeting",
            "severity": "low",
            "timestamp": now.isoformat(),
        })

    if "epli" not in current and account.employee_count and account.employee_count >= 15:
        insights.append({
            "insight_type": "opportunity",
            "title": "EPLI cross-sell opportunity",
            "subtitle": "No employment practices coverage for business with 15+ employees",
            "suggested_action": "Discuss EPLI at next renewal review",
            "severity": "low",
            "timestamp": now.isoformat(),
        })

    # Low confidence warning
    if health and float(health.confidence) < 0.3:
        insights.append({
            "insight_type": "coverage_alert",
            "title": "Limited account data available",
            "subtitle": "Health scores may be unreliable with current information",
            "suggested_action": "Gather additional account details to improve analysis",
            "severity": "info",
            "timestamp": now.isoformat(),
        })

    return insights
