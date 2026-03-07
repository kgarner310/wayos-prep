"""Outcome Learning Service — aggregation of deal outcomes for market signals.

Queries deal_outcomes table to compute carrier win rates, common outcome
reasons, and industry-level market intelligence.
"""

import logging
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import DealOutcome

logger = logging.getLogger(__name__)

VALID_OUTCOMES = {"won", "lost", "pending", "declined", "no_quote"}

VALID_OUTCOME_REASONS = {
    "PRICE", "COVERAGE", "RELATIONSHIP", "APPETITE", "SERVICE", "UNKNOWN",
}


def get_carrier_win_rates(
    db: Session,
    industry: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    """Calculate carrier win rates from deal outcomes.

    Returns: {carrier_name: win_rate_float, ...}
    """
    query = db.query(DealOutcome)
    if industry:
        query = query.filter(DealOutcome.industry == industry.lower())
    if state:
        query = query.filter(DealOutcome.state == state.upper())

    outcomes = query.all()

    carrier_totals: Counter = Counter()
    carrier_wins: Counter = Counter()

    for o in outcomes:
        carrier = o.carrier
        if not carrier:
            continue
        carrier_totals[carrier] += 1
        if o.outcome == "won":
            carrier_wins[carrier] += 1

    win_rates = {}
    for carrier, total in carrier_totals.items():
        if total > 0:
            win_rates[carrier] = round(carrier_wins[carrier] / total, 2)

    return win_rates


def get_outcome_reason_breakdown(
    db: Session,
    industry: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    """Get breakdown of outcome reasons for lost deals.

    Returns: {reason: count, ...}
    """
    query = db.query(DealOutcome).filter(DealOutcome.outcome == "lost")
    if industry:
        query = query.filter(DealOutcome.industry == industry.lower())
    if state:
        query = query.filter(DealOutcome.state == state.upper())

    outcomes = query.all()
    reasons: Counter = Counter()
    for o in outcomes:
        reason = o.outcome_reason or "UNKNOWN"
        reasons[reason] += 1

    return dict(reasons)


def get_market_signals(
    db: Session,
    industry: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    """Compile market signals from deal outcomes.

    Returns:
        {
            "carrier_win_rates": {...},
            "loss_reasons": {...},
            "total_outcomes": int,
            "win_rate_overall": float,
            "top_carrier": str | None,
        }
    """
    win_rates = get_carrier_win_rates(db, industry=industry, state=state)
    loss_reasons = get_outcome_reason_breakdown(db, industry=industry, state=state)

    query = db.query(DealOutcome)
    if industry:
        query = query.filter(DealOutcome.industry == industry.lower())
    if state:
        query = query.filter(DealOutcome.state == state.upper())

    all_outcomes = query.all()
    total = len(all_outcomes)
    wins = sum(1 for o in all_outcomes if o.outcome == "won")

    top_carrier = None
    if win_rates:
        top_carrier = max(win_rates, key=win_rates.get)

    return {
        "carrier_win_rates": win_rates,
        "loss_reasons": loss_reasons,
        "total_outcomes": total,
        "win_rate_overall": round(wins / total, 2) if total > 0 else 0.0,
        "top_carrier": top_carrier,
    }
