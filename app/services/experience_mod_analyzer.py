"""Analyze experience modification rate worksheets.

Produces structured insights and producer talking points
from submitted mod worksheet data.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def analyze_experience_mod(
    current_mod: float,
    prior_mod: float | None = None,
    expected_losses: float | None = None,
    actual_primary_losses: float | None = None,
    actual_excess_losses: float | None = None,
    total_payroll: float | None = None,
    class_code_entries: list[dict] | None = None,
    mod_claims: list[dict] | None = None,
) -> dict:
    """Analyze experience mod worksheet data and return structured analysis."""

    flags: list[str] = []
    insights: list[str] = []

    # --- Mod trending ---
    mod_trend = None
    if prior_mod is not None:
        mod_change = current_mod - prior_mod
        mod_trend = {
            "current": current_mod,
            "prior": prior_mod,
            "change": round(mod_change, 4),
            "direction": (
                "improving" if mod_change < 0
                else ("worsening" if mod_change > 0 else "flat")
            ),
        }

        if mod_change > 0.05:
            flags.append(
                f"Mod increased from {prior_mod:.2f} to {current_mod:.2f} "
                f"(+{mod_change:.2f}) — claims are driving costs up"
            )
        elif mod_change < -0.05:
            insights.append(
                f"Mod improved from {prior_mod:.2f} to {current_mod:.2f} "
                f"({mod_change:+.2f}) — safety investments are paying off"
            )

    # --- Mod classification ---
    if current_mod > 1.25:
        flags.append(
            f"Mod at {current_mod:.2f} — significantly above unity, expect carrier scrutiny"
        )
    elif current_mod > 1.00:
        flags.append(
            f"Mod at {current_mod:.2f} — above unity, room for improvement"
        )
    elif current_mod < 0.85:
        insights.append(
            f"Mod at {current_mod:.2f} — well below unity, strong safety record"
        )
    elif current_mod <= 1.00:
        insights.append(
            f"Mod at {current_mod:.2f} — at or below unity"
        )

    # --- Expected vs actual losses ---
    loss_analysis = None
    if expected_losses and actual_primary_losses is not None:
        actual_total = (actual_primary_losses or 0) + (actual_excess_losses or 0)
        deviation = actual_total - expected_losses
        deviation_pct = (deviation / expected_losses) if expected_losses > 0 else 0

        loss_analysis = {
            "expected_losses": round(expected_losses, 2),
            "actual_primary": round(actual_primary_losses or 0, 2),
            "actual_excess": round(actual_excess_losses or 0, 2),
            "actual_total": round(actual_total, 2),
            "deviation": round(deviation, 2),
            "deviation_pct": round(deviation_pct, 4),
        }

        if deviation_pct > 0.20:
            flags.append(
                f"Actual losses exceed expected by {deviation_pct:.0%} "
                f"(${deviation:,.0f}) — this is the primary mod driver"
            )
        elif deviation_pct < -0.10:
            insights.append(
                f"Actual losses {abs(deviation_pct):.0%} below expected — "
                f"favorable experience supporting the mod"
            )

        # Primary vs excess split
        if actual_total > 0:
            primary_pct = (actual_primary_losses or 0) / actual_total
            if primary_pct > 0.70:
                flags.append(
                    f"Primary losses are {primary_pct:.0%} of total — "
                    f"frequency of smaller claims is the issue, not severity"
                )
            elif actual_excess_losses and (actual_excess_losses / actual_total) > 0.60:
                flags.append(
                    "Excess losses dominate — a few large claims are driving the mod. "
                    "Focus on those specific claims."
                )

    # --- Claims analysis ---
    claims_analysis = []
    if mod_claims:
        total_claim_incurred = sum(c.get("incurred", 0) or 0 for c in mod_claims)
        medical_only_count = sum(1 for c in mod_claims if c.get("medical_only"))
        indemnity_count = len(mod_claims) - medical_only_count

        for claim in mod_claims:
            inc = claim.get("incurred", 0) or 0
            impact = (
                "high" if inc > 50_000
                else ("medium" if inc > 15_000 else "low")
            )
            claims_analysis.append({
                "description": claim.get("description", ""),
                "incurred": inc,
                "medical_only": claim.get("medical_only", False),
                "mod_impact": impact,
                "pct_of_total": (
                    round(inc / total_claim_incurred, 4)
                    if total_claim_incurred > 0 else 0
                ),
                "date_of_loss": claim.get("date_of_loss"),
                "claim_status": claim.get("claim_status", "Closed"),
            })

        if medical_only_count > 0 and indemnity_count > 0:
            insights.append(
                f"{medical_only_count} medical-only vs {indemnity_count} indemnity claims — "
                f"medical-only claims have 70% less mod impact"
            )

        # Sort by incurred descending
        claims_analysis.sort(
            key=lambda c: c.get("incurred", 0) or 0, reverse=True
        )

        if claims_analysis:
            top = claims_analysis[0]
            if top.get("incurred", 0) > 25_000:
                desc = top.get("description") or "largest claim"
                flags.append(
                    f"Top claim ({desc}) at ${top.get('incurred', 0):,.0f} — "
                    f"closing or reducing this would have the biggest mod impact"
                )

    # --- Class code analysis ---
    class_analysis = []
    if class_code_entries:
        for entry in class_code_entries:
            code = entry.get("class_code", "")
            payroll = entry.get("payroll", 0) or 0
            rate = entry.get("expected_loss_rate", 0) or 0
            expected = payroll * rate / 100 if payroll and rate else None
            class_analysis.append({
                "class_code": code,
                "description": entry.get("description", ""),
                "payroll": round(payroll, 2),
                "expected_loss_rate": round(rate, 4),
                "expected_losses": round(expected, 2) if expected else None,
            })

    # --- Build talking points ---
    talking_points = _build_mod_talking_points(
        current_mod, prior_mod, mod_trend, loss_analysis,
        flags, insights, claims_analysis, class_analysis,
    )

    logger.info(
        "Experience mod analysis: mod=%.2f flags=%d insights=%d claims=%d talking_points=%d",
        current_mod, len(flags), len(insights), len(claims_analysis), len(talking_points),
    )

    return {
        "current_mod": current_mod,
        "prior_mod": prior_mod,
        "mod_trend": mod_trend,
        "loss_analysis": loss_analysis,
        "claims_analysis": claims_analysis[:10],
        "class_code_analysis": class_analysis,
        "flags": flags[:5],
        "insights": insights[:5],
        "talking_points": talking_points[:5],
    }


def _build_mod_talking_points(
    current_mod: float,
    prior_mod: float | None,
    mod_trend: dict | None,
    loss_analysis: dict | None,
    flags: list[str],
    insights: list[str],
    claims_analysis: list[dict],
    class_analysis: list[dict],
) -> list[str]:
    """Generate producer-ready talking points from mod analysis."""
    points: list[str] = []

    # Opening framing
    if current_mod > 1.10:
        points.append(
            f"The mod is at {current_mod:.2f} — open by acknowledging you've reviewed the worksheet "
            f"and understand the drivers. Clients respect producers who know their numbers."
        )
    elif current_mod < 0.90:
        points.append(
            f"Mod at {current_mod:.2f} is a strength. Lead with this as proof their safety program works "
            f"and use it to negotiate better terms."
        )
    else:
        points.append(
            f"Mod at {current_mod:.2f} is near unity. Focus the conversation on what programs "
            f"they have in place and opportunities to push it lower."
        )

    # Trend
    if mod_trend:
        if mod_trend["direction"] == "improving":
            points.append(
                f"Mod is trending down ({prior_mod:.2f} → {current_mod:.2f}). "
                f"Ask what they changed — this is your story for underwriters."
            )
        elif mod_trend["direction"] == "worsening":
            points.append(
                f"Mod moved up ({prior_mod:.2f} → {current_mod:.2f}). "
                f"Be prepared to explain the why — was it one bad claim or a pattern?"
            )

    # Claims impact
    if claims_analysis:
        high_impact = [c for c in claims_analysis if c.get("mod_impact") == "high"]
        if high_impact:
            points.append(
                f"{len(high_impact)} high-impact claim(s) on the worksheet. "
                f"Get status updates — if any are closing, the mod will improve next year."
            )

        med_only = [c for c in claims_analysis if c.get("medical_only")]
        if med_only:
            points.append(
                f"{len(med_only)} medical-only claim(s) have reduced mod impact (70% discount). "
                f"Confirm these haven't converted to lost-time claims."
            )

    # Loss analysis
    if loss_analysis:
        if loss_analysis.get("deviation_pct", 0) > 0.15:
            points.append(
                "Actual losses exceed expected — ask about return-to-work programs, "
                "safety committees, and whether they've engaged a loss control consultant."
            )

    # Actionable recommendations
    if current_mod > 1.00:
        points.append(
            "Key mod reduction strategies to discuss: formal return-to-work program, "
            "safety committee, regular driver training, and aggressive claims management "
            "with the carrier."
        )

    # Cross-reference
    points.append(
        "Cross-reference with the loss runs to validate which claims are still open "
        "and verify reserve accuracy."
    )

    return points
