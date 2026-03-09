"""Renewal Risk Brief Generator — orchestrates WAYOS intelligence into a producer-ready renewal brief.

Combines account profile, industry intelligence, loss run analysis,
experience mod analysis, coverage gap insights, producer ammo, and
agency-level peer insights into one structured briefing.
"""

from __future__ import annotations

import logging

from app.services.coverage_gap_detector import detect_coverage_gaps
from app.services.producer_ammo import generate_producer_ammo
from app.services.agency_ammo_feed import build_agency_ammo_feed
from app.services.industry_loader import resolve, get_enrichment

logger = logging.getLogger(__name__)


def generate_renewal_brief(profile: dict) -> dict:
    """Generate a structured renewal risk brief from an account profile.

    Orchestrates existing WAYOS services and assembles their output into
    a unified producer-facing briefing document.

    Args:
        profile: dict with optional keys:
            account_name, industry, state, employee_count, annual_revenue,
            vehicle_count, uses_subcontractors, current_coverages,
            experience_mod, account_stage, claims_summary, notes,
            loss_run_data, experience_mod_data

    Returns:
        Structured brief dict with sections:
            account_summary, risk_overview, underwriter_concerns,
            coverage_gaps, loss_patterns, mod_trends, producer_questions,
            defense_strategy, peer_insights, recommended_actions
    """

    # --- 1. Normalize inputs ---
    account_name = profile.get("account_name", "").strip() or "Unnamed Account"
    industry_raw = profile.get("industry", "")
    state = (profile.get("state") or "").upper().strip()
    employee_count = profile.get("employee_count") or 0
    annual_revenue = profile.get("annual_revenue") or 0
    vehicle_count = profile.get("vehicle_count") or 0
    uses_subcontractors = profile.get("uses_subcontractors", False)
    current_coverages = profile.get("current_coverages") or []
    experience_mod = profile.get("experience_mod")
    account_stage = (profile.get("account_stage") or "renewal").strip().lower()
    claims_summary = profile.get("claims_summary", "")
    notes = profile.get("notes", "")
    loss_run_data = profile.get("loss_run_data")
    experience_mod_data = profile.get("experience_mod_data")

    slug, source = resolve(industry_raw)

    # --- 2. Build account summary ---
    key_facts = _build_key_facts(
        employee_count, annual_revenue, vehicle_count,
        uses_subcontractors, experience_mod, current_coverages,
    )
    account_summary = {
        "account_name": account_name,
        "industry": industry_raw or slug,
        "state": state,
        "account_stage": account_stage,
        "key_facts": key_facts,
    }

    # --- 3. Run coverage gap detector ---
    gap_profile = {
        "industry": industry_raw,
        "state": state,
        "employee_count": employee_count,
        "annual_revenue": annual_revenue,
        "vehicle_count": vehicle_count,
        "uses_subcontractors": uses_subcontractors,
        "current_coverages": current_coverages,
        "experience_mod": experience_mod,
    }
    if loss_run_data:
        gap_profile["loss_run_data"] = loss_run_data
    if experience_mod_data:
        gap_profile["experience_mod_data"] = experience_mod_data

    gap_result = detect_coverage_gaps(gap_profile)
    coverage_gaps = gap_result.get("coverage_gaps", [])

    # --- 4. Run producer ammo ---
    ammo_profile = dict(gap_profile)
    ammo_profile["account_stage"] = account_stage
    ammo_profile["claims_summary"] = claims_summary
    ammo_profile["notes"] = notes
    if loss_run_data:
        ammo_profile["loss_run_data"] = loss_run_data
    if experience_mod_data:
        ammo_profile["experience_mod_data"] = experience_mod_data

    ammo_result = generate_producer_ammo(ammo_profile)
    ammo = ammo_result.get("ammo_questions", {})

    # --- 5. Run agency ammo feed (peer insights) ---
    agency_result = build_agency_ammo_feed(
        {"industry": industry_raw, "state": state, "date_range_days": 30},
        db=None,
    )
    agency_summary = agency_result.get("summary", {})

    # --- 6. Extract loss patterns ---
    loss_patterns = []
    if loss_run_data and isinstance(loss_run_data, dict):
        loss_patterns.extend(loss_run_data.get("patterns", [])[:5])
        for flag in loss_run_data.get("underwriting_flags", [])[:3]:
            if flag not in loss_patterns:
                loss_patterns.append(flag)

    # --- 7. Extract mod trends ---
    mod_trends = []
    if experience_mod_data and isinstance(experience_mod_data, dict):
        mod_trend = experience_mod_data.get("mod_trend")
        if mod_trend and isinstance(mod_trend, dict):
            direction = mod_trend.get("direction", "")
            current = mod_trend.get("current")
            prior = mod_trend.get("prior")
            if direction == "worsening" and current and prior:
                mod_trends.append(
                    f"Experience mod increased from {prior:.2f} to {current:.2f}"
                )
            elif direction == "improving" and current and prior:
                mod_trends.append(
                    f"Experience mod improved from {prior:.2f} to {current:.2f}"
                )
            elif direction == "flat" and current:
                mod_trends.append(f"Experience mod stable at {current:.2f}")

        for flag in experience_mod_data.get("flags", [])[:3]:
            if flag not in mod_trends:
                mod_trends.append(flag)

        for insight in experience_mod_data.get("insights", [])[:2]:
            if insight not in mod_trends:
                mod_trends.append(insight)

    # --- 8. Build underwriter concerns ---
    underwriter_concerns = _build_underwriter_concerns(
        ammo.get("underwriting_flags", []),
        loss_patterns,
        mod_trends,
        coverage_gaps,
    )

    # --- 9. Build producer questions ---
    producer_questions = _build_producer_questions(
        ammo.get("top_questions", []),
        gap_result.get("confirmation_questions", []),
        ammo.get("operational_change_questions", []),
    )

    # --- 10. Build defense strategy ---
    defense_strategy = _build_defense_strategy(
        coverage_gaps, loss_patterns, mod_trends,
        uses_subcontractors, experience_mod,
    )

    # --- 11. Build peer insights ---
    peer_insights = _build_peer_insights(agency_summary)

    # --- 12. Build recommended actions ---
    recommended_actions = _build_recommended_actions(
        coverage_gaps, loss_run_data, experience_mod_data,
        uses_subcontractors, account_stage,
    )

    # --- 13. Compute risk overview ---
    risk_overview = _compute_risk_overview(
        coverage_gaps, underwriter_concerns, loss_patterns,
        mod_trends, experience_mod, industry_raw or slug,
    )

    logger.info(
        "Renewal brief generated: account=%s industry=%s gaps=%d concerns=%d questions=%d",
        account_name, industry_raw or slug, len(coverage_gaps),
        len(underwriter_concerns), len(producer_questions),
    )

    return {
        "account_summary": account_summary,
        "risk_overview": risk_overview,
        "underwriter_concerns": underwriter_concerns[:7],
        "coverage_gaps": coverage_gaps[:5],
        "loss_patterns": loss_patterns[:5],
        "mod_trends": mod_trends[:5],
        "producer_questions": producer_questions[:7],
        "defense_strategy": defense_strategy[:5],
        "peer_insights": peer_insights[:5],
        "recommended_actions": recommended_actions[:5],
    }


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _build_key_facts(
    employee_count: int,
    annual_revenue: float,
    vehicle_count: int,
    uses_subcontractors: bool,
    experience_mod: float | None,
    current_coverages: list[str],
) -> list[str]:
    """Build concise key facts list for the account summary."""
    facts = []
    if employee_count:
        facts.append(f"{employee_count} employees")
    if annual_revenue:
        if annual_revenue >= 1_000_000:
            facts.append(f"${annual_revenue / 1_000_000:.1f}M annual revenue")
        else:
            facts.append(f"${annual_revenue:,.0f} annual revenue")
    if vehicle_count:
        facts.append(f"{vehicle_count} vehicles")
    if uses_subcontractors:
        facts.append("Uses subcontractors")
    if experience_mod is not None:
        facts.append(f"Experience mod: {experience_mod:.2f}")
    if current_coverages:
        facts.append(f"{len(current_coverages)} current coverage lines")
    return facts


def _build_underwriter_concerns(
    underwriting_flags: list[str],
    loss_patterns: list[str],
    mod_trends: list[str],
    coverage_gaps: list[dict],
) -> list[str]:
    """Assemble underwriter concerns from multiple intelligence sources."""
    concerns = []

    # Mod-driven concerns first (most impactful for underwriters)
    for trend in mod_trends[:2]:
        if trend not in concerns:
            concerns.append(trend)

    # Loss-driven concerns
    for pattern in loss_patterns[:2]:
        if pattern not in concerns:
            concerns.append(pattern)

    # Underwriting flags from producer ammo
    for flag in underwriting_flags[:3]:
        if flag not in concerns:
            concerns.append(flag)

    # High-severity coverage gaps
    for gap in coverage_gaps:
        if gap.get("risk_level") == "high" and len(concerns) < 7:
            concern = f"Missing {gap['coverage']}: {gap['reason']}"
            if concern not in concerns:
                concerns.append(concern)

    return concerns


def _build_producer_questions(
    top_questions: list[str],
    confirmation_questions: list[str],
    operational_questions: list[str],
) -> list[str]:
    """Assemble deduplicated producer questions from multiple sources."""
    seen = set()
    questions = []

    for q in top_questions[:3]:
        if q not in seen:
            seen.add(q)
            questions.append(q)

    for q in confirmation_questions[:2]:
        if q not in seen:
            seen.add(q)
            questions.append(q)

    for q in operational_questions[:2]:
        if q not in seen:
            seen.add(q)
            questions.append(q)

    return questions


def _build_defense_strategy(
    coverage_gaps: list[dict],
    loss_patterns: list[str],
    mod_trends: list[str],
    uses_subcontractors: bool,
    experience_mod: float | None,
) -> list[str]:
    """Build actionable defense strategies based on identified risks."""
    strategies = []

    # Address coverage gaps
    high_gaps = [g for g in coverage_gaps if g.get("risk_level") == "high"]
    if high_gaps:
        gap_names = ", ".join(g["coverage"] for g in high_gaps[:3])
        strategies.append(f"Address missing coverage: {gap_names}")

    # Address mod concerns
    if mod_trends:
        worsening = any("increased" in t or "worsening" in t.lower() for t in mod_trends)
        if worsening:
            strategies.append(
                "Prepare explanation for upward mod trend and document loss control improvements"
            )
        elif experience_mod is not None and experience_mod < 1.0:
            strategies.append(
                "Leverage favorable mod as proof of safety program effectiveness"
            )

    # Address loss patterns
    if loss_patterns:
        strategies.append(
            "Prepare loss narrative addressing open claims and corrective actions taken"
        )

    # Subcontractor risk
    if uses_subcontractors:
        strategies.append(
            "Document subcontractor certificate compliance and risk transfer agreements"
        )

    # General renewal prep
    if not strategies:
        strategies.append(
            "Review expiring program against current operations for material changes"
        )

    return strategies


def _build_peer_insights(agency_summary: dict) -> list[str]:
    """Extract peer insights from agency ammo feed summary."""
    insights = []

    themes = agency_summary.get("top_question_themes", [])
    for theme in themes[:2]:
        insights.append(f"Producers working similar risks frequently ask about {theme}")

    gaps = agency_summary.get("common_coverage_gaps", [])
    for gap in gaps[:2]:
        if not any(gap.lower() in i.lower() for i in insights):
            insights.append(f"{gap} is a common coverage gap in this class")

    rising = agency_summary.get("rising_risk_topics", [])
    for topic in rising[:1]:
        if not any(topic.lower() in i.lower() for i in insights):
            insights.append(f"Rising topic among similar accounts: {topic}")

    return insights


def _build_recommended_actions(
    coverage_gaps: list[dict],
    loss_run_data: dict | None,
    experience_mod_data: dict | None,
    uses_subcontractors: bool,
    account_stage: str,
) -> list[str]:
    """Build concrete recommended actions for the producer."""
    actions = []

    # Coverage gap actions
    for gap in coverage_gaps[:2]:
        if gap.get("risk_level") in ("high", "medium"):
            actions.append(f"Review {gap['coverage']} exposure before renewal marketing")

    # Loss run actions
    if loss_run_data and isinstance(loss_run_data, dict):
        flags = loss_run_data.get("underwriting_flags", [])
        if flags:
            actions.append("Prepare underwriting narrative addressing loss history concerns")
        if loss_run_data.get("summary", {}).get("open_claims", 0) > 0:
            actions.append("Obtain updated reserve and status information on open claims")

    # Mod actions
    if experience_mod_data and isinstance(experience_mod_data, dict):
        mod_trend = experience_mod_data.get("mod_trend")
        if mod_trend and isinstance(mod_trend, dict):
            if mod_trend.get("direction") == "worsening":
                actions.append(
                    "Document loss control changes and return-to-work programs for underwriter submission"
                )

    # Subcontractor actions
    if uses_subcontractors:
        actions.append("Confirm subcontractor insurance and contract requirements are current")

    # Stage-specific
    if account_stage == "remarket":
        actions.append("Assemble complete submission package: 5 years loss runs, mod worksheet, current payroll by class")

    if not actions:
        actions.append("Review expiring program against current operations and prepare clean submission")

    return actions


def _compute_risk_overview(
    coverage_gaps: list[dict],
    underwriter_concerns: list[str],
    loss_patterns: list[str],
    mod_trends: list[str],
    experience_mod: float | None,
    industry: str,
) -> dict:
    """Compute risk level, confidence, and headline from available signals.

    Scoring approach (explainable, not ML):
    - Start with base score of 0.3
    - Add signal-based increments
    - Map final score to risk_level thresholds
    - Confidence based on signal density (more data = higher confidence)
    """
    score = 0.3
    signal_count = 0
    reasons = []

    # Coverage gap signals
    high_gaps = sum(1 for g in coverage_gaps if g.get("risk_level") == "high")
    medium_gaps = sum(1 for g in coverage_gaps if g.get("risk_level") == "medium")
    if high_gaps >= 2:
        score += 0.20
        reasons.append("multiple high-severity coverage gaps")
    elif high_gaps == 1:
        score += 0.10
        reasons.append("high-severity coverage gap identified")
    if medium_gaps >= 2:
        score += 0.05
    signal_count += len(coverage_gaps)

    # Mod signals
    if experience_mod is not None:
        signal_count += 1
        if experience_mod > 1.25:
            score += 0.20
            reasons.append("experience mod significantly above unity")
        elif experience_mod > 1.0:
            score += 0.10
            reasons.append("experience mod above unity")
        elif experience_mod < 0.85:
            score -= 0.10

    worsening_mod = any("increased" in t or "worsening" in t.lower() for t in mod_trends)
    if worsening_mod:
        score += 0.10
        reasons.append("upward mod trend")
        signal_count += 1

    # Loss pattern signals
    if loss_patterns:
        score += min(len(loss_patterns) * 0.03, 0.15)
        if len(loss_patterns) >= 3:
            reasons.append("multiple loss patterns identified")
        signal_count += len(loss_patterns)

    # Underwriter concern density
    if len(underwriter_concerns) >= 5:
        score += 0.05
    signal_count += len(underwriter_concerns)

    # Clamp score
    score = max(0.0, min(score, 1.0))

    # Map to risk level
    if score >= 0.65:
        risk_level = "high"
    elif score >= 0.40:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # Confidence: based on how many signals we had to work with
    # More data = more confident in the assessment
    if signal_count >= 8:
        confidence = 0.85
    elif signal_count >= 5:
        confidence = 0.70
    elif signal_count >= 2:
        confidence = 0.55
    else:
        confidence = 0.40

    # Build headline
    if reasons:
        reason_text = ", ".join(reasons[:3])
        if risk_level == "high":
            headline = f"Elevated renewal attention recommended due to {reason_text}."
        elif risk_level == "moderate":
            headline = f"Moderate renewal complexity — monitor {reason_text}."
        else:
            headline = "Standard renewal — no significant risk indicators flagged."
    else:
        headline = "Limited data available — recommend gathering additional account information."

    return {
        "risk_level": risk_level,
        "confidence": round(confidence, 2),
        "headline": headline,
        "contributing_factors": reasons[:5],
        "signal_count": signal_count,
    }
