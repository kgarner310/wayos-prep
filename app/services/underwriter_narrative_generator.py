"""Underwriter Narrative Generator.

Generates underwriter-facing renewal and new business narratives using:
- account profile
- renewal brief (from renewal_brief_generator)
- optional public web intelligence (from public_web_intel)

Produces concise, factual, strategically framed narratives in email
and memo formats. Does NOT regenerate coverage gaps, loss analysis,
or mod analysis — consumes existing outputs.
"""

from __future__ import annotations

import logging

from app.services.renewal_brief_generator import generate_renewal_brief

logger = logging.getLogger(__name__)

_VALID_NARRATIVE_TYPES = {"renewal", "new_business"}
_VALID_POSITIONING = {"standard", "favorable", "defensive"}


def generate_underwriter_narrative(profile: dict) -> dict:
    """Generate underwriter-facing narrative from account data and intelligence.

    Args:
        profile: dict with optional keys:
            account_name, industry, state, employee_count, annual_revenue,
            vehicle_count, uses_subcontractors, current_coverages,
            experience_mod, account_stage, claims_summary, notes,
            loss_run_data, experience_mod_data,
            narrative_type, intended_market_positioning,
            renewal_brief, public_web_intel

    Returns:
        Structured narrative dict with email_version, memo_version,
        supporting_points, fact_sources, cautions
    """

    # --- Normalize inputs ---
    account_name = profile.get("account_name", "").strip() or "Unnamed Account"
    industry = profile.get("industry", "")
    state = (profile.get("state") or "").upper().strip()
    narrative_type = profile.get("narrative_type", "renewal").strip().lower()
    if narrative_type not in _VALID_NARRATIVE_TYPES:
        narrative_type = "renewal"
    positioning = profile.get("intended_market_positioning", "standard").strip().lower()
    if positioning not in _VALID_POSITIONING:
        positioning = "standard"

    # --- Obtain or use renewal brief ---
    renewal_brief = profile.get("renewal_brief")
    if not renewal_brief or not isinstance(renewal_brief, dict):
        renewal_brief = generate_renewal_brief(profile)

    brief_used = True

    # --- Obtain public web intel ---
    public_intel = profile.get("public_web_intel")
    intel_used = bool(public_intel and isinstance(public_intel, dict))

    # --- Build fact sources ---
    fact_sources = {
        "account_profile_used": True,
        "renewal_brief_used": brief_used,
        "public_web_intel_used": intel_used,
    }

    # --- Extract data from brief ---
    account_summary = renewal_brief.get("account_summary", {})
    risk_overview = renewal_brief.get("risk_overview", {})
    coverage_gaps = renewal_brief.get("coverage_gaps", [])
    underwriter_concerns = renewal_brief.get("underwriter_concerns", [])
    loss_patterns = renewal_brief.get("loss_patterns", [])
    mod_trends = renewal_brief.get("mod_trends", [])
    defense_strategy = renewal_brief.get("defense_strategy", [])
    recommended_actions = renewal_brief.get("recommended_actions", [])
    key_facts = account_summary.get("key_facts", [])

    # --- Extract public intel signals ---
    ops_signals = []
    safety_signals = []
    carrier_signals = []
    intel_cautions = []
    if intel_used:
        ops_signals = public_intel.get("operations_signals", [])
        safety_signals = public_intel.get("safety_signals", [])
        carrier_signals = public_intel.get("carrier_relevant_signals", [])
        intel_cautions = public_intel.get("cautions", [])

    # --- Generate narratives ---
    if narrative_type == "renewal":
        email_version = _build_renewal_email(
            account_name, industry, state, key_facts,
            risk_overview, underwriter_concerns, mod_trends,
            loss_patterns, defense_strategy, positioning,
            safety_signals, carrier_signals,
        )
        memo_version = _build_renewal_memo(
            account_name, industry, state, key_facts,
            risk_overview, underwriter_concerns, coverage_gaps,
            mod_trends, loss_patterns, defense_strategy,
            recommended_actions, positioning,
            ops_signals, safety_signals, carrier_signals,
        )
    else:
        email_version = _build_new_business_email(
            account_name, industry, state, key_facts,
            risk_overview, positioning,
            ops_signals, safety_signals, carrier_signals,
        )
        memo_version = _build_new_business_memo(
            account_name, industry, state, key_facts,
            risk_overview, coverage_gaps, recommended_actions,
            positioning,
            ops_signals, safety_signals, carrier_signals,
        )

    # --- Supporting points ---
    supporting_points = _build_supporting_points(
        defense_strategy, safety_signals, carrier_signals,
        ops_signals, mod_trends,
    )

    # --- Cautions ---
    cautions = list(intel_cautions)
    if not cautions and intel_used:
        cautions.append(
            "Public website/social signals are summarized from observed "
            "marketing content and may require verification"
        )

    logger.info(
        "Underwriter narrative generated: account=%s type=%s positioning=%s intel=%s",
        account_name, narrative_type, positioning, intel_used,
    )

    return {
        "account_name": account_name,
        "narrative_type": narrative_type,
        "email_version": email_version,
        "memo_version": memo_version,
        "supporting_points": supporting_points[:7],
        "fact_sources": fact_sources,
        "cautions": cautions,
    }


# ============================================================
# RENEWAL NARRATIVE BUILDERS
# ============================================================


def _build_renewal_email(
    account_name: str,
    industry: str,
    state: str,
    key_facts: list[str],
    risk_overview: dict,
    concerns: list[str],
    mod_trends: list[str],
    loss_patterns: list[str],
    defense_strategy: list[str],
    positioning: str,
    safety_signals: list[str],
    carrier_signals: list[str],
) -> dict:
    """Build concise email-ready renewal narrative."""
    subject = f"Renewal Submission – {account_name}"

    paragraphs = []

    # Opening
    facts_text = ", ".join(key_facts[:3]) if key_facts else f"{industry} account in {state}"
    paragraphs.append(
        f"Submitting the renewal for {account_name}, a {industry} "
        f"operation based in {state}. {facts_text}."
    )

    # Risk framing
    risk_level = risk_overview.get("risk_level", "moderate")
    if positioning == "defensive" and concerns:
        paragraphs.append(
            f"We want to address the risk profile directly. "
            f"{concerns[0]}."
        )
        if len(concerns) > 1:
            paragraphs[-1] += f" Additionally, {concerns[1].lower()}."
    elif positioning == "favorable":
        if mod_trends and any("improved" in t.lower() for t in mod_trends):
            paragraphs.append(
                f"The account shows positive momentum. {mod_trends[0]}."
            )
        else:
            paragraphs.append(
                "The account presents a clean risk profile with no significant adverse indicators."
            )
    else:
        if concerns:
            paragraphs.append(
                f"Key considerations: {concerns[0].lower()}."
            )

    # Defense/controls
    if defense_strategy:
        actions = "; ".join(s.lower() for s in defense_strategy[:2])
        paragraphs.append(f"We have {actions}.")

    # Safety signals from public intel
    if safety_signals:
        sig = safety_signals[0]
        paragraphs.append(
            f"The company's public-facing materials suggest relevant controls: {sig.lower()}."
        )

    # Close
    paragraphs.append(
        "Please review and advise on appetite and any additional information needed."
    )

    body = "\n\n".join(paragraphs)

    return {"subject": subject, "title": "", "body": body}


def _build_renewal_memo(
    account_name: str,
    industry: str,
    state: str,
    key_facts: list[str],
    risk_overview: dict,
    concerns: list[str],
    coverage_gaps: list[dict],
    mod_trends: list[str],
    loss_patterns: list[str],
    defense_strategy: list[str],
    recommended_actions: list[str],
    positioning: str,
    ops_signals: list[str],
    safety_signals: list[str],
    carrier_signals: list[str],
) -> dict:
    """Build structured renewal memo narrative."""
    title = f"Renewal Narrative – {account_name}"

    sections = []

    # Account overview
    sections.append("ACCOUNT OVERVIEW")
    facts_text = ". ".join(key_facts[:5]) if key_facts else f"{industry} account in {state}"
    sections.append(
        f"{account_name} is a {industry} operation based in {state}. {facts_text}."
    )

    # Risk assessment
    risk_level = risk_overview.get("risk_level", "moderate")
    headline = risk_overview.get("headline", "")
    sections.append("")
    sections.append("RISK ASSESSMENT")
    if headline:
        sections.append(headline)

    # Underwriter concerns
    if concerns:
        sections.append("")
        sections.append("UNDERWRITER CONSIDERATIONS")
        for c in concerns[:5]:
            sections.append(f"- {c}")

    # Loss and mod context
    if mod_trends or loss_patterns:
        sections.append("")
        sections.append("LOSS AND MOD CONTEXT")
        for t in mod_trends[:3]:
            sections.append(f"- {t}")
        for p in loss_patterns[:3]:
            if p not in mod_trends:
                sections.append(f"- {p}")

    # Coverage considerations
    if coverage_gaps:
        sections.append("")
        sections.append("COVERAGE CONSIDERATIONS")
        for gap in coverage_gaps[:3]:
            risk = gap.get("risk_level", "").upper()
            sections.append(f"- [{risk}] {gap.get('coverage', '')}: {gap.get('reason', '')}")

    # Operations profile from public intel
    if ops_signals:
        sections.append("")
        sections.append("OPERATIONS PROFILE (PUBLIC SOURCES)")
        for sig in ops_signals[:4]:
            sections.append(f"- Public-facing materials indicate: {sig.lower()}")

    # Controls and safety
    if safety_signals or defense_strategy:
        sections.append("")
        sections.append("CONTROLS AND RISK MANAGEMENT")
        for sig in safety_signals[:3]:
            sections.append(f"- Website references: {sig.lower()}")
        for strat in defense_strategy[:3]:
            sections.append(f"- {strat}")

    # Carrier-relevant signals
    if carrier_signals:
        sections.append("")
        sections.append("ADDITIONAL UNDERWRITING SIGNALS")
        for sig in carrier_signals[:3]:
            sections.append(f"- {sig}")

    body = "\n".join(sections)

    return {"subject": "", "title": title, "body": body}


# ============================================================
# NEW BUSINESS NARRATIVE BUILDERS
# ============================================================


def _build_new_business_email(
    account_name: str,
    industry: str,
    state: str,
    key_facts: list[str],
    risk_overview: dict,
    positioning: str,
    ops_signals: list[str],
    safety_signals: list[str],
    carrier_signals: list[str],
) -> dict:
    """Build concise email-ready new business narrative."""
    subject = f"New Business Submission – {account_name}"

    paragraphs = []

    # Introduction
    facts_text = ", ".join(key_facts[:3]) if key_facts else f"{industry} account"
    paragraphs.append(
        f"Submitting {account_name} for new business consideration. "
        f"This is a {industry} operation based in {state}. {facts_text}."
    )

    # Operations
    if ops_signals:
        ops_text = "; ".join(s.lower() for s in ops_signals[:3])
        paragraphs.append(
            f"Public-facing materials suggest the following operations: {ops_text}."
        )

    # Favorable framing
    if positioning == "favorable" and safety_signals:
        sig_text = "; ".join(s.lower() for s in safety_signals[:2])
        paragraphs.append(
            f"The company website references relevant controls: {sig_text}."
        )
    elif safety_signals:
        paragraphs.append(
            f"The company's public-facing materials suggest: {safety_signals[0].lower()}."
        )

    # Carrier-relevant
    if carrier_signals:
        paragraphs.append(
            f"Additional signals: {carrier_signals[0].lower()}."
        )

    # Close
    paragraphs.append(
        "Please review for appetite and advise on any additional information required for quoting."
    )

    body = "\n\n".join(paragraphs)

    return {"subject": subject, "title": "", "body": body}


def _build_new_business_memo(
    account_name: str,
    industry: str,
    state: str,
    key_facts: list[str],
    risk_overview: dict,
    coverage_gaps: list[dict],
    recommended_actions: list[str],
    positioning: str,
    ops_signals: list[str],
    safety_signals: list[str],
    carrier_signals: list[str],
) -> dict:
    """Build structured new business memo narrative."""
    title = f"New Business Narrative – {account_name}"

    sections = []

    # Account introduction
    sections.append("ACCOUNT INTRODUCTION")
    facts_text = ". ".join(key_facts[:5]) if key_facts else f"{industry} account"
    sections.append(
        f"{account_name} is a {industry} operation based in {state}. {facts_text}."
    )

    # Operations overview
    if ops_signals:
        sections.append("")
        sections.append("OPERATIONS OVERVIEW (PUBLIC SOURCES)")
        for sig in ops_signals[:4]:
            sections.append(f"- Public-facing materials indicate: {sig.lower()}")

    # Risk assessment
    headline = risk_overview.get("headline", "")
    if headline:
        sections.append("")
        sections.append("RISK ASSESSMENT")
        sections.append(headline)

    # Safety and controls
    if safety_signals or carrier_signals:
        sections.append("")
        sections.append("CONTROLS AND QUALIFICATIONS")
        for sig in safety_signals[:3]:
            sections.append(f"- Website references: {sig.lower()}")
        for sig in carrier_signals[:3]:
            sections.append(f"- {sig}")

    # Coverage needs
    if coverage_gaps:
        sections.append("")
        sections.append("ANTICIPATED COVERAGE NEEDS")
        for gap in coverage_gaps[:3]:
            sections.append(f"- {gap.get('coverage', '')}: {gap.get('reason', '')}")

    body = "\n".join(sections)

    return {"subject": "", "title": title, "body": body}


# ============================================================
# SUPPORTING POINTS
# ============================================================


def _build_supporting_points(
    defense_strategy: list[str],
    safety_signals: list[str],
    carrier_signals: list[str],
    ops_signals: list[str],
    mod_trends: list[str],
) -> list[str]:
    """Build list of supporting points that back up the narrative."""
    points = []

    for strat in defense_strategy[:2]:
        points.append(strat)

    for sig in safety_signals[:2]:
        points.append(f"Public website references: {sig.lower()}")

    for sig in carrier_signals[:1]:
        points.append(sig)

    for trend in mod_trends[:1]:
        if "improved" in trend.lower() or "below unity" in trend.lower():
            points.append(trend)

    for sig in ops_signals[:1]:
        if sig not in points:
            points.append(f"Operations profile includes: {sig.lower()}")

    return points
