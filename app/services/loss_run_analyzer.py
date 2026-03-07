"""Loss Run Analyzer — structured analysis of claim-level loss data.

Ported from kXyJC and adapted to Nkb2E per-claim input format.
Produces summary statistics, patterns, underwriting flags, and
producer talking points from submitted loss run entries.
"""

import logging
from collections import Counter

from app.services.industry_loader import get_enrichment

logger = logging.getLogger(__name__)


# Line-of-business normalization
_LINE_NORMALIZE = {
    "wc": "Workers Comp",
    "workers comp": "Workers Comp",
    "workers compensation": "Workers Comp",
    "work comp": "Workers Comp",
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
    "epli": "EPLI",
    "employment practices": "EPLI",
    "cargo": "Cargo",
}


def _normalize_line(name: str) -> str:
    return _LINE_NORMALIZE.get(name.lower().strip(), name.strip().title())


# Cause-of-loss pattern grouping
_CAUSE_PATTERNS = [
    ("vehicle", ["vehicle", "collision", "backing", "rear-end", "rollover", "mvr"]),
    ("struck_by", ["struck by", "hit by", "crush", "caught"]),
    ("fall", ["fall", "fell", "ladder", "scaffold", "height", "slip", "trip"]),
    ("strain", ["strain", "sprain", "lift", "overexertion", "repetitive", "back injury"]),
    ("cut_laceration", ["cut", "laceration", "puncture", "amputation"]),
    ("burn", ["burn", "scald", "fire", "explosion"]),
    ("property_damage", ["water damage", "wind", "hail", "storm", "theft", "vandalism"]),
]


def _classify_cause(cause: str) -> str | None:
    """Classify a cause-of-loss string into a pattern group."""
    if not cause:
        return None
    lower = cause.lower()
    for pattern, keywords in _CAUSE_PATTERNS:
        if any(kw in lower for kw in keywords):
            return pattern
    return None


def analyze_loss_run(data: dict) -> dict:
    """Analyze loss run data and return structured insights.

    Args:
        data: dict with keys:
            claims: list of claim dicts (date_of_loss, line_of_business,
                    cause_of_loss, paid_amount, reserve_amount, claim_status)
            industry: optional str for enrichment
            state: optional str
            policy_period: optional str

    Returns:
        {
            "summary": {...},
            "by_line": [...],
            "patterns": [...],
            "underwriting_flags": [...],
            "producer_talking_points": [...]
        }
    """
    claims = data.get("claims", [])
    industry = data.get("industry")

    if not claims:
        return {
            "summary": {
                "total_claims": 0,
                "open_claims": 0,
                "total_incurred": 0.0,
                "total_paid": 0.0,
                "total_reserves": 0.0,
                "loss_ratio": None,
            },
            "by_line": [],
            "patterns": [],
            "underwriting_flags": [],
            "producer_talking_points": [
                "No loss history provided — request 5 years of loss runs before going to market."
            ],
        }

    # --- Aggregate ---
    total_paid = 0.0
    total_reserves = 0.0
    open_claims = 0
    by_line: dict[str, dict] = {}
    cause_counter: Counter = Counter()
    cause_groups: Counter = Counter()

    for claim in claims:
        line = _normalize_line(claim.get("line_of_business", "Unknown"))
        paid = claim.get("paid_amount", 0.0) or 0.0
        reserve = claim.get("reserve_amount", 0.0) or 0.0
        status = (claim.get("claim_status") or "closed").lower()
        cause = claim.get("cause_of_loss") or ""

        total_paid += paid
        total_reserves += reserve

        if status == "open":
            open_claims += 1

        if line not in by_line:
            by_line[line] = {
                "claim_count": 0,
                "total_paid": 0.0,
                "total_reserves": 0.0,
                "causes": [],
            }
        agg = by_line[line]
        agg["claim_count"] += 1
        agg["total_paid"] += paid
        agg["total_reserves"] += reserve
        if cause:
            agg["causes"].append(cause)
            cause_counter[cause.lower()] += 1

        group = _classify_cause(cause)
        if group:
            cause_groups[group] += 1

    total_incurred = total_paid + total_reserves
    total_claims = len(claims)

    # --- By-line details ---
    line_details = []
    for line, agg in sorted(by_line.items()):
        line_incurred = agg["total_paid"] + agg["total_reserves"]
        unique_causes = list(dict.fromkeys(agg["causes"]))
        line_details.append({
            "line": line,
            "claim_count": agg["claim_count"],
            "total_incurred": round(line_incurred, 2),
            "total_paid": round(agg["total_paid"], 2),
            "open_reserves": round(agg["total_reserves"], 2),
            "causes": unique_causes[:5],
        })

    # --- Pattern detection ---
    patterns = []
    for group, count in cause_groups.most_common():
        if count >= 2:
            label = group.replace("_", " ").title()
            patterns.append(f"{count} {label.lower()}-related claims detected")

    # Concentration by line
    for detail in line_details:
        if detail["claim_count"] >= 3 and total_claims >= 4:
            pct = detail["claim_count"] / total_claims
            if pct >= 0.5:
                patterns.append(
                    f"{detail['line']} accounts for {pct:.0%} of all claims "
                    f"({detail['claim_count']} of {total_claims})"
                )

    # --- Underwriting flags ---
    flags = []

    if total_claims >= 5:
        flags.append(f"High claim frequency: {total_claims} claims in the loss run period")

    if open_claims >= 2:
        flags.append(f"{open_claims} open claims with ${total_reserves:,.0f} in outstanding reserves")

    if total_incurred > 0 and total_reserves / total_incurred > 0.40:
        flags.append(
            f"{total_reserves / total_incurred:.0%} of total incurred is still in reserves — "
            f"claims may develop further"
        )

    # Large individual claims
    large_threshold = max(total_incurred * 0.25, 25_000) if total_incurred > 0 else 25_000
    large_claims = []
    for claim in claims:
        incurred = (claim.get("paid_amount") or 0) + (claim.get("reserve_amount") or 0)
        if incurred >= large_threshold:
            cause = claim.get("cause_of_loss") or "unspecified"
            large_claims.append(f"${incurred:,.0f} — {cause}")
    if large_claims:
        flags.append(f"{len(large_claims)} large claim(s): {'; '.join(large_claims[:3])}")

    # WC-specific flags
    wc_detail = next((d for d in line_details if d["line"] == "Workers Comp"), None)
    if wc_detail and wc_detail["claim_count"] >= 3:
        flags.append(
            f"Workers Comp frequency ({wc_detail['claim_count']} claims) will impact "
            f"experience mod — prepare loss control narrative"
        )

    # --- Producer talking points ---
    talking_points = _build_talking_points(
        total_claims, total_incurred, total_reserves, open_claims,
        line_details, patterns, cause_groups, industry,
    )

    logger.info(
        "Loss run analysis: %d claims, $%,.0f incurred, %d flags, %d patterns",
        total_claims, total_incurred, len(flags), len(patterns),
    )

    return {
        "summary": {
            "total_claims": total_claims,
            "open_claims": open_claims,
            "total_incurred": round(total_incurred, 2),
            "total_paid": round(total_paid, 2),
            "total_reserves": round(total_reserves, 2),
            "loss_ratio": None,  # No premium data in per-claim format
        },
        "by_line": line_details,
        "patterns": patterns[:5],
        "underwriting_flags": flags[:5],
        "producer_talking_points": talking_points[:5],
    }


def _build_talking_points(
    total_claims: int,
    total_incurred: float,
    total_reserves: float,
    open_claims: int,
    line_details: list[dict],
    patterns: list[str],
    cause_groups: Counter,
    industry: str | None,
) -> list[str]:
    """Generate producer-ready talking points from the analysis."""
    points: list[str] = []

    # Overall picture
    if total_claims == 0:
        points.append("No loss history provided — request 5 years of loss runs before going to market.")
        return points

    if total_incurred <= 10_000 and total_claims <= 2:
        points.append(
            "Clean loss history — use this as leverage for competitive pricing and broader carrier appetite."
        )
    elif total_incurred > 100_000:
        points.append(
            f"${total_incurred:,.0f} in total incurred losses — come prepared with the insured's "
            f"remediation story and corrective actions taken."
        )

    # Open reserves
    if open_claims >= 2 and total_reserves > 0:
        points.append(
            f"{open_claims} open claims with ${total_reserves:,.0f} in reserves — "
            f"get status updates and narratives before going to market."
        )

    # Pattern-driven points
    if "fall" in cause_groups and cause_groups["fall"] >= 2:
        points.append(
            "Multiple fall-related claims — discuss fall protection program, "
            "ladder safety, and OSHA compliance."
        )
    if "strain" in cause_groups and cause_groups["strain"] >= 2:
        points.append(
            "Repeated strain/overexertion claims — review ergonomic programs, "
            "return-to-work policies, and modified duty availability."
        )
    if "vehicle" in cause_groups and cause_groups["vehicle"] >= 2:
        points.append(
            "Multiple vehicle-related claims — review driver eligibility, MVR checks, "
            "telematics, and fleet safety program."
        )

    # Clean lines
    clean_lines = [d["line"] for d in line_details if d["claim_count"] == 0]
    if clean_lines:
        points.append(
            f"Clean loss history on {', '.join(clean_lines)} — "
            f"highlight when marketing to carriers."
        )

    # Mod cross-reference
    wc_detail = next((d for d in line_details if d["line"] == "Workers Comp"), None)
    if wc_detail and wc_detail["claim_count"] >= 1:
        points.append(
            "Cross-reference WC losses with the experience mod worksheet "
            "to identify which claims are driving the mod."
        )

    # Industry enrichment
    if industry:
        enrichment = get_enrichment(industry)
        wc_claims = enrichment.get("wc_claims", [])
        if wc_claims and wc_detail and wc_detail["claim_count"] >= 2:
            points.append(
                f"Industry data shows common WC risks for this class — verify safety programs "
                f"address: {wc_claims[0].lower()[:80]}."
            )

    # Frequency point
    if total_claims >= 5:
        points.append(
            f"Frequency is a concern ({total_claims} claims) — "
            f"ask about safety committees, training programs, and loss control visits."
        )

    return points
