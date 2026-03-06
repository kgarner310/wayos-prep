"""Analyze loss run data across all lines of business.

Produces structured insights, flags, and producer talking points
from submitted loss run entries.
"""

from __future__ import annotations


# Lines of business we recognize
ALL_LINES = [
    "Workers Comp", "WC",
    "General Liability", "GL",
    "Commercial Auto", "Auto",
    "Property",
    "Umbrella", "Excess",
    "Professional Liability", "E&O",
    "D&O",
    "Cyber",
    "BOP",
    "Inland Marine",
]

_LINE_NORMALIZE = {
    "wc": "Workers Comp",
    "workers comp": "Workers Comp",
    "workers compensation": "Workers Comp",
    "gl": "General Liability",
    "general liability": "General Liability",
    "auto": "Commercial Auto",
    "commercial auto": "Commercial Auto",
    "property": "Property",
    "umbrella": "Umbrella",
    "excess": "Umbrella",
    "professional liability": "Professional Liability",
    "e&o": "Professional Liability",
    "d&o": "D&O",
    "cyber": "Cyber",
    "bop": "BOP",
    "inland marine": "Inland Marine",
}


def _normalize_line(name: str) -> str:
    return _LINE_NORMALIZE.get(name.lower().strip(), name.strip())


def analyze_loss_runs(line_entries: list[dict]) -> dict:
    """Analyze loss run entries and return structured analysis.

    Each entry in line_entries should have:
      - line_of_business: str
      - policy_year: str | None
      - premium: float | None
      - num_claims: int | None
      - total_incurred: float | None
      - total_paid: float | None
      - open_reserves: float | None
      - large_claims: list[str] | None
    """
    if not line_entries:
        return {"error": "No line entries provided"}

    # Aggregate by line of business
    by_line: dict[str, dict] = {}
    total_premium = 0.0
    total_incurred = 0.0
    total_paid = 0.0
    total_reserves = 0.0
    total_claims = 0
    all_large_claims: list[dict] = []

    for entry in line_entries:
        line = _normalize_line(entry.get("line_of_business", "Unknown"))
        if line not in by_line:
            by_line[line] = {
                "premium": 0.0,
                "incurred": 0.0,
                "paid": 0.0,
                "reserves": 0.0,
                "claims": 0,
                "years": [],
                "large_claims": [],
            }

        agg = by_line[line]
        premium = entry.get("premium") or 0.0
        incurred = entry.get("total_incurred") or 0.0
        paid = entry.get("total_paid") or 0.0
        reserves = entry.get("open_reserves") or 0.0
        claims = entry.get("num_claims") or 0
        year = entry.get("policy_year")

        agg["premium"] += premium
        agg["incurred"] += incurred
        agg["paid"] += paid
        agg["reserves"] += reserves
        agg["claims"] += claims
        if year:
            agg["years"].append(year)

        total_premium += premium
        total_incurred += incurred
        total_paid += paid
        total_reserves += reserves
        total_claims += claims

        for lc in (entry.get("large_claims") or []):
            all_large_claims.append({"line": line, "year": year, "description": lc})

    # Calculate loss ratios per line
    line_summaries = []
    flags: list[str] = []
    worst_line = None
    worst_ratio = 0.0

    for line, agg in sorted(by_line.items()):
        ratio = (agg["incurred"] / agg["premium"]) if agg["premium"] > 0 else None
        summary = {
            "line": line,
            "premium": round(agg["premium"], 2),
            "total_incurred": round(agg["incurred"], 2),
            "total_paid": round(agg["paid"], 2),
            "open_reserves": round(agg["reserves"], 2),
            "num_claims": agg["claims"],
            "loss_ratio": round(ratio, 4) if ratio is not None else None,
            "years_covered": sorted(set(agg["years"])),
            "large_claims": agg["large_claims"],
        }
        line_summaries.append(summary)

        if ratio is not None:
            if ratio > 0.60:
                flags.append(f"{line}: loss ratio {ratio:.0%} — above 60% threshold")
            if ratio > worst_ratio:
                worst_ratio = ratio
                worst_line = line

        if agg["reserves"] > 0 and agg["incurred"] > 0:
            reserve_pct = agg["reserves"] / agg["incurred"]
            if reserve_pct > 0.40:
                flags.append(
                    f"{line}: {reserve_pct:.0%} of incurred still in open reserves — "
                    f"claims may develop"
                )

        if agg["claims"] > 0 and agg["premium"] > 0:
            freq = agg["claims"] / (agg["premium"] / 100_000)
            if freq > 5:
                flags.append(f"{line}: high claim frequency ({agg['claims']} claims)")

    overall_ratio = (total_incurred / total_premium) if total_premium > 0 else None

    if overall_ratio is not None and overall_ratio > 0.65:
        flags.insert(0, f"Overall loss ratio {overall_ratio:.0%} — account is running hot")

    if len(all_large_claims) > 0:
        flags.append(f"{len(all_large_claims)} large/notable claim(s) flagged across lines")

    # Build talking points
    talking_points = _build_talking_points(
        line_summaries, flags, overall_ratio, worst_line, worst_ratio,
        total_incurred, total_claims, all_large_claims,
    )

    return {
        "line_summaries": line_summaries,
        "totals": {
            "premium": round(total_premium, 2),
            "incurred": round(total_incurred, 2),
            "paid": round(total_paid, 2),
            "reserves": round(total_reserves, 2),
            "claims": total_claims,
            "loss_ratio": round(overall_ratio, 4) if overall_ratio is not None else None,
        },
        "flags": flags,
        "large_claims": all_large_claims,
        "talking_points": talking_points,
    }


def _build_talking_points(
    line_summaries: list[dict],
    flags: list[str],
    overall_ratio: float | None,
    worst_line: str | None,
    worst_ratio: float,
    total_incurred: float,
    total_claims: int,
    large_claims: list[dict],
) -> list[str]:
    """Generate producer-ready talking points from the analysis."""
    points: list[str] = []

    # Overall picture
    if overall_ratio is not None:
        if overall_ratio <= 0.40:
            points.append(
                f"Strong loss history — overall loss ratio at {overall_ratio:.0%}. "
                f"Use this as leverage for competitive pricing."
            )
        elif overall_ratio <= 0.60:
            points.append(
                f"Loss ratio at {overall_ratio:.0%} — acceptable but watch trending. "
                f"Ask what safety programs they've implemented recently."
            )
        else:
            points.append(
                f"Loss ratio is running at {overall_ratio:.0%} — this will be an underwriting concern. "
                f"Come prepared with the insured's remediation story."
            )

    # Worst line
    if worst_line and worst_ratio > 0.50:
        points.append(
            f"{worst_line} is the biggest exposure at {worst_ratio:.0%} loss ratio. "
            f"Dig into claim details and ask what's changed."
        )

    # Clean lines
    clean_lines = [s["line"] for s in line_summaries if s["num_claims"] == 0]
    if clean_lines:
        points.append(
            f"Clean loss history on {', '.join(clean_lines)} — "
            f"highlight this when marketing to carriers."
        )

    # Open reserves
    reserve_lines = [
        s for s in line_summaries
        if s["open_reserves"] > 0 and s["total_incurred"] > 0
        and (s["open_reserves"] / s["total_incurred"]) > 0.30
    ]
    if reserve_lines:
        names = ", ".join(s["line"] for s in reserve_lines)
        points.append(
            f"Significant open reserves on {names} — ask for claim status updates "
            f"and get narratives on open claims before going to market."
        )

    # Large claims
    if large_claims:
        points.append(
            f"{len(large_claims)} large claim(s) noted — prepare narratives explaining "
            f"circumstances and what steps the insured took to prevent recurrence."
        )

    # Frequency
    if total_claims > 10:
        points.append(
            f"Frequency is a story here ({total_claims} total claims). "
            f"Ask about return-to-work programs, safety committees, and driver training."
        )

    # Mod connection
    points.append(
        "Cross-reference this loss history with the experience mod worksheet "
        "to see which claims are actually driving the mod."
    )

    return points


def render_loss_run_text(analysis: dict, account_name: str) -> str:
    """Render loss run analysis as readable text for the producer."""
    lines = [f"WAYOS PREP — LOSS RUN REVIEW: {account_name.upper()}", ""]

    totals = analysis.get("totals", {})
    lines.append(f"Total Premium: ${totals.get('premium', 0):,.0f}")
    lines.append(f"Total Incurred: ${totals.get('incurred', 0):,.0f}")
    lines.append(f"Total Claims: {totals.get('claims', 0)}")
    ratio = totals.get("loss_ratio")
    lines.append(f"Overall Loss Ratio: {ratio:.0%}" if ratio else "Overall Loss Ratio: N/A")
    lines.append("")

    lines.append("─" * 40)
    lines.append("")

    # Per-line summaries
    lines.append("BY LINE OF BUSINESS")
    lines.append("")
    for s in analysis.get("line_summaries", []):
        lr = f"{s['loss_ratio']:.0%}" if s.get("loss_ratio") is not None else "N/A"
        lines.append(f"  {s['line']}")
        lines.append(f"    Premium: ${s['premium']:,.0f}  |  Incurred: ${s['total_incurred']:,.0f}  |  Claims: {s['num_claims']}  |  Loss Ratio: {lr}")
        if s.get("open_reserves", 0) > 0:
            lines.append(f"    Open Reserves: ${s['open_reserves']:,.0f}")
        if s.get("large_claims"):
            for lc in s["large_claims"]:
                lines.append(f"    ** {lc}")
        lines.append("")

    # Flags
    flags = analysis.get("flags", [])
    if flags:
        lines.append("FLAGS & CONCERNS")
        lines.append("")
        for f in flags:
            lines.append(f"  ! {f}")
        lines.append("")

    # Talking points
    tp = analysis.get("talking_points", [])
    if tp:
        lines.append("PRODUCER TALKING POINTS")
        lines.append("")
        for p in tp:
            lines.append(f"  • {p}")
        lines.append("")

    lines.append("─" * 40)
    lines.append("Prepared with WAYOS PREP • wayosprep.app")

    return "\n".join(lines)
