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


# ============================================================
# MARKET EDGE — account-level intelligence panel
# ============================================================

MIN_SAMPLE_SIZE = 5


def get_market_edge(
    db: Session,
    industry: str,
    state: str,
) -> dict:
    """Build a Market Edge intelligence payload for an industry + state.

    Deterministic aggregation over deal_outcomes. Returns carrier win rates
    (with win/loss counts) and top loss reasons, gated by a minimum sample
    size for confidence.
    """
    query = db.query(DealOutcome)
    if industry:
        query = query.filter(DealOutcome.industry == industry.lower())
    if state:
        query = query.filter(DealOutcome.state == state.upper())

    outcomes = query.all()
    sample_size = len(outcomes)

    result: dict = {
        "industry": industry,
        "state": state,
        "sample_size": sample_size,
        "carrier_win_rates": [],
        "top_loss_reasons": [],
        "confidence": "low" if sample_size < MIN_SAMPLE_SIZE else "normal",
    }

    if sample_size < MIN_SAMPLE_SIZE:
        return result

    # --- carrier win rates ---
    carrier_wins: Counter = Counter()
    carrier_losses: Counter = Counter()
    for o in outcomes:
        carrier = o.carrier
        if not carrier:
            continue
        if o.outcome == "won":
            carrier_wins[carrier] += 1
        elif o.outcome == "lost":
            carrier_losses[carrier] += 1

    carrier_entries = []
    all_carriers = set(carrier_wins.keys()) | set(carrier_losses.keys())
    for carrier in sorted(all_carriers):
        wins = carrier_wins[carrier]
        losses = carrier_losses[carrier]
        total = wins + losses
        if total > 0:
            carrier_entries.append({
                "carrier": carrier,
                "win_rate": round(wins / total, 2),
                "wins": wins,
                "losses": losses,
            })

    # Sort by win rate descending
    carrier_entries.sort(key=lambda x: x["win_rate"], reverse=True)
    result["carrier_win_rates"] = carrier_entries

    # --- top loss reasons ---
    loss_reasons: Counter = Counter()
    for o in outcomes:
        if o.outcome == "lost":
            reason = o.outcome_reason or "UNKNOWN"
            loss_reasons[reason] += 1

    result["top_loss_reasons"] = [
        {"reason": reason, "count": count}
        for reason, count in loss_reasons.most_common(10)
    ]

    return result
