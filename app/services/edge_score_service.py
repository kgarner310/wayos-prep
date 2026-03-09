"""Edge Score Engine — competitive positioning score for accounts.

Calculates a 0-100 score representing how competitive a producer's
position is on a given account. Considers risk score, premium
competitiveness, carrier appetite, and coverage completeness.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Strength bands
STRENGTH_BANDS = [
    (0, 29, "Weak"),
    (30, 49, "Below Average"),
    (50, 64, "Competitive"),
    (65, 79, "Strong"),
    (80, 100, "Dominant"),
]


def _get_strength(score: int) -> str:
    for low, high, label in STRENGTH_BANDS:
        if low <= score <= high:
            return label
    return "Unknown"


def calculate_edge_score(
    account: dict,
    market_signals: Optional[dict] = None,
) -> dict:
    """Calculate competitive edge score for an account.

    Args:
        account: dict with optional keys:
            - risk_score: float (0-100, lower = better)
            - premium: float
            - estimated_median_premium: float
            - carrier_appetite: str ("positive", "neutral", "negative")
            - coverage_completeness: float (0-1.0)
            - loss_ratio: float
            - mod: float (experience mod)
        market_signals: optional dict of pre-computed market context

    Returns:
        {
            "edge_score": int,
            "strength": str,
            "drivers": list[str],
            "drags": list[str],
        }
    """
    score = 50
    drivers = []
    drags = []

    # --- Risk score factor ---
    risk_score = account.get("risk_score")
    if risk_score is not None:
        if risk_score <= 35:
            score += 10
            drivers.append("Low risk score")
        elif risk_score <= 55:
            score += 5
            drivers.append("Moderate risk score")
        elif risk_score >= 75:
            score -= 10
            drags.append("High risk score")

    # --- Premium competitiveness ---
    premium = account.get("premium")
    median = account.get("estimated_median_premium")
    if premium is not None and median is not None and median > 0:
        ratio = premium / median
        if ratio < 0.85:
            score += 10
            drivers.append("Premium below regional median")
        elif ratio < 0.95:
            score += 5
            drivers.append("Premium slightly below median")
        elif ratio > 1.15:
            score -= 10
            drags.append("Premium above regional median")
        elif ratio > 1.05:
            score -= 5
            drags.append("Premium slightly above median")

    # --- Carrier appetite ---
    appetite = (account.get("carrier_appetite") or "").lower()
    if appetite == "positive":
        score += 5
        drivers.append("Carrier appetite strong")
    elif appetite == "negative":
        score -= 5
        drags.append("Carrier appetite weak")

    # --- Coverage completeness ---
    completeness = account.get("coverage_completeness")
    if completeness is not None:
        if completeness >= 0.9:
            score += 5
            drivers.append("Coverage program comprehensive")
        elif completeness < 0.5:
            score -= 5
            drags.append("Significant coverage gaps")

    # --- Experience mod ---
    mod = account.get("mod")
    if mod is not None:
        if mod < 0.85:
            score += 5
            drivers.append("Favorable experience mod")
        elif mod > 1.2:
            score -= 5
            drags.append("Elevated experience mod")

    # --- Loss ratio ---
    loss_ratio = account.get("loss_ratio")
    if loss_ratio is not None:
        if loss_ratio < 0.4:
            score += 5
            drivers.append("Low loss ratio")
        elif loss_ratio > 0.7:
            score -= 5
            drags.append("High loss ratio")

    # Clamp
    score = max(0, min(100, score))

    return {
        "edge_score": score,
        "strength": _get_strength(score),
        "drivers": drivers,
        "drags": drags,
    }
