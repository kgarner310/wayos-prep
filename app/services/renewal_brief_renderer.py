"""Render a renewal brief as structured text or markdown.

Lightweight rendering helper — JSON response is primary,
this provides a producer-readable text alternative.
"""

from __future__ import annotations


def render_renewal_brief_text(brief: dict) -> str:
    """Render a renewal brief dict as readable text for producers."""
    lines: list[str] = []

    # Header
    summary = brief.get("account_summary", {})
    name = summary.get("account_name", "Account")
    lines.append(f"WAYOS PREP — RENEWAL RISK BRIEF: {name.upper()}")
    lines.append("")

    industry = summary.get("industry", "")
    state = summary.get("state", "")
    stage = summary.get("account_stage", "renewal")
    if industry or state:
        lines.append(f"Industry: {industry}  |  State: {state}  |  Stage: {stage}")
        lines.append("")

    # Key facts
    facts = summary.get("key_facts", [])
    if facts:
        for fact in facts:
            lines.append(f"  • {fact}")
        lines.append("")

    lines.append("─" * 50)
    lines.append("")

    # Risk overview
    overview = brief.get("risk_overview", {})
    if overview:
        risk = overview.get("risk_level", "").upper()
        conf = overview.get("confidence", 0)
        headline = overview.get("headline", "")
        lines.append(f"RISK LEVEL: {risk}  (confidence: {conf:.0%})")
        if headline:
            lines.append(f"  {headline}")
        lines.append("")

    # Underwriter concerns
    concerns = brief.get("underwriter_concerns", [])
    if concerns:
        lines.append("UNDERWRITER CONCERNS")
        lines.append("")
        for c in concerns:
            lines.append(f"  ! {c}")
        lines.append("")

    # Coverage gaps
    gaps = brief.get("coverage_gaps", [])
    if gaps:
        lines.append("COVERAGE GAPS")
        lines.append("")
        for g in gaps:
            risk = g.get("risk_level", "?").upper()
            conf = g.get("confidence", 0)
            lines.append(f"  [{risk}] {g.get('coverage', '')} (confidence: {conf:.0%})")
            lines.append(f"        {g.get('reason', '')}")
        lines.append("")

    # Loss patterns
    patterns = brief.get("loss_patterns", [])
    if patterns:
        lines.append("LOSS PATTERNS")
        lines.append("")
        for p in patterns:
            lines.append(f"  • {p}")
        lines.append("")

    # Mod trends
    trends = brief.get("mod_trends", [])
    if trends:
        lines.append("MOD TRENDS")
        lines.append("")
        for t in trends:
            lines.append(f"  • {t}")
        lines.append("")

    # Producer questions
    questions = brief.get("producer_questions", [])
    if questions:
        lines.append("PRODUCER QUESTIONS")
        lines.append("")
        for i, q in enumerate(questions, 1):
            lines.append(f"  {i}. {q}")
        lines.append("")

    # Defense strategy
    strategy = brief.get("defense_strategy", [])
    if strategy:
        lines.append("DEFENSE STRATEGY")
        lines.append("")
        for s in strategy:
            lines.append(f"  → {s}")
        lines.append("")

    # Peer insights
    peers = brief.get("peer_insights", [])
    if peers:
        lines.append("PEER INSIGHTS")
        lines.append("")
        for p in peers:
            lines.append(f"  ○ {p}")
        lines.append("")

    # Recommended actions
    actions = brief.get("recommended_actions", [])
    if actions:
        lines.append("RECOMMENDED ACTIONS")
        lines.append("")
        for a in actions:
            lines.append(f"  ☐ {a}")
        lines.append("")

    lines.append("─" * 50)
    lines.append("Prepared with WAYOS PREP")

    return "\n".join(lines)
