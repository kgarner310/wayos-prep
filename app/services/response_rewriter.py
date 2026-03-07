"""Response Rewriter — thin presentation layer for WAYOS structured outputs.

Converts structured analysis results into polished producer-facing language
without changing underlying facts, scoring, or risk logic. All rendering is
deterministic and template-based.

This layer is PRESENTATION ONLY. It does not:
- Invent facts
- Change scores or risk levels
- Modify canonical knowledge
- Replace the structured output as source of truth

Internal design supports future optional LLM renderer, but current
implementation is purely deterministic template rendering.
"""

import logging
import uuid
from typing import Optional

from app.presentation.presentation_models import (
    RewriteOptions,
    RenderedResponse,
    DEFAULT_MODE,
    DEFAULT_TONE,
)

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================


def prioritize_items(items: list[str], max_items: Optional[int] = None) -> list[str]:
    """Return items in priority order, optionally truncated.

    Priority heuristic: items mentioning critical coverage lines sort first.
    """
    priority_keywords = [
        "workers comp", "general liability", "commercial auto",
        "critical", "missing", "payroll", "loss run",
    ]

    def _score(item: str) -> int:
        lower = item.lower()
        return sum(1 for kw in priority_keywords if kw in lower)

    sorted_items = sorted(items, key=_score, reverse=True)
    if max_items is not None and max_items > 0:
        return sorted_items[:max_items]
    return sorted_items


def truncate_sentences(text: str, max_sentences: Optional[int] = None) -> str:
    """Truncate text to a maximum number of sentences."""
    if max_sentences is None or max_sentences <= 0:
        return text
    sentences = []
    current = []
    for char in text:
        current.append(char)
        if char in ".!?":
            sentences.append("".join(current).strip())
            current = []
            if len(sentences) >= max_sentences:
                break
    if current and (max_sentences is None or len(sentences) < max_sentences):
        trailing = "".join(current).strip()
        if trailing:
            sentences.append(trailing)
    return " ".join(sentences)


def build_bullet_list(
    items: list[str],
    max_items: Optional[int] = None,
    prefix: str = "",
) -> list[str]:
    """Build a bullet list from items, optionally truncated and prefixed."""
    selected = items[:max_items] if max_items else items
    if prefix:
        return [f"{prefix}{item}" for item in selected]
    return list(selected)


def build_source_summary(data: dict, response_type: str) -> dict:
    """Build a compact source summary for trust/explainability."""
    summary = {"response_type": response_type}

    if "industry" in data:
        summary["industry"] = data["industry"]
    if "risk_level" in data:
        summary["risk_level"] = data["risk_level"]
    if "readiness_score" in data:
        summary["readiness_score"] = data["readiness_score"]
    if "readiness_level" in data:
        summary["readiness_level"] = data["readiness_level"]
    if "missing_critical_fields" in data:
        summary["missing_critical_count"] = len(data["missing_critical_fields"])
    if "missing_coverages" in data:
        summary["missing_coverage_count"] = len(data["missing_coverages"])
    if "office_learnings" in data:
        summary["office_learning_count"] = len(data["office_learnings"])

    return summary


def _resolve_options(options: Optional[RewriteOptions]) -> RewriteOptions:
    """Resolve None options to defaults."""
    if options is None:
        return RewriteOptions()
    return options


def _disclaimer() -> str:
    return "This analysis is based on available submission data and industry knowledge. It does not guarantee market placement or carrier acceptance."


# ============================================================
# TONE ADAPTERS
# ============================================================


def _tone_intro(tone: str, subject: str) -> str:
    """Generate a tone-appropriate introductory phrase."""
    if tone == "confident":
        return f"Here is what matters most for this {subject}."
    elif tone == "practical":
        return f"For this {subject}, here is what to focus on."
    else:  # neutral
        return f"Summary for this {subject}."


def _tone_action(tone: str, action: str) -> str:
    """Adapt an action statement to tone."""
    if tone == "confident":
        return action.replace("Consider ", "").replace("consider ", "")
    elif tone == "practical":
        return action
    else:
        return action


# ============================================================
# MEETING BRIEF RENDERER
# ============================================================


def _render_meeting_brief_concise(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    exposures = data.get("top_exposures", [])
    talking_points = data.get("recommended_talking_points", [])
    questions = data.get("discovery_questions", [])

    top_exposures = prioritize_items(exposures, 3)
    exposure_text = ", ".join(top_exposures) if top_exposures else "standard industry risks"

    text = f"{_tone_intro(opts.tone, industry)} Top exposures include {exposure_text}."

    bullets = []
    for tp in prioritize_items(talking_points, opts.max_bullets or 3):
        bullets.append(_tone_action(opts.tone, tp))
    if questions:
        bullets.append(f"Key question: {questions[0]}")

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="meeting_brief",
        mode="concise",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "meeting_brief"),
    )


def _render_meeting_brief_consultative(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    talking_points = data.get("recommended_talking_points", [])
    questions = data.get("discovery_questions", [])
    exposures = data.get("top_exposures", [])

    text = f"Preparing for a {industry} meeting. "
    if exposures:
        text += f"The primary exposures to discuss are {', '.join(exposures[:3])}. "
    text += "Use the talking points below to guide the conversation, and ask the discovery questions to uncover additional detail."

    bullets = []
    for tp in prioritize_items(talking_points, opts.max_bullets or 5):
        bullets.append(f"Talking point: {_tone_action(opts.tone, tp)}")
    for q in questions[:3]:
        bullets.append(f"Ask: {q}")
    if opts.max_bullets:
        bullets = bullets[:opts.max_bullets]

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="meeting_brief",
        mode="consultative",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "meeting_brief"),
    )


def _render_meeting_brief_technical(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    exposures = data.get("top_exposures", [])
    claims = data.get("common_claims", [])
    coverage_watchouts = data.get("coverage_watchouts", [])

    text = f"Technical risk summary for {industry}. "
    if exposures:
        text += f"Key exposures: {', '.join(exposures[:4])}. "
    if claims:
        text += f"Common claim patterns: {', '.join(claims[:3])}. "
    if coverage_watchouts:
        text += f"Coverage watchouts: {', '.join(coverage_watchouts[:3])}."

    bullets = []
    for e in prioritize_items(exposures, opts.max_bullets or 5):
        bullets.append(f"Exposure: {e}")
    for c in claims[:2]:
        bullets.append(f"Claim pattern: {c}")
    for w in coverage_watchouts[:2]:
        bullets.append(f"Watchout: {w}")

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="meeting_brief",
        mode="technical",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "meeting_brief"),
    )


def _render_meeting_brief_meeting(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    exposures = data.get("top_exposures", [])
    talking_points = data.get("recommended_talking_points", [])
    questions = data.get("discovery_questions", [])

    text = f"Meeting flow for {industry}: "
    text += "Open by acknowledging the client's business, then transition to key risk areas. "
    if exposures:
        text += f"Focus the discussion on {', '.join(exposures[:3])}. "
    text += "Close by confirming coverage needs and identifying any gaps."

    bullets = []
    bullets.append("Open: confirm business operations and recent changes")
    for tp in prioritize_items(talking_points, 3):
        bullets.append(f"Discuss: {_tone_action(opts.tone, tp)}")
    for q in questions[:2]:
        bullets.append(f"Probe: {q}")
    bullets.append("Close: confirm requested coverages and timeline")

    if opts.max_bullets:
        bullets = bullets[:opts.max_bullets]

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="meeting_brief",
        mode="meeting_brief",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "meeting_brief"),
    )


_MEETING_BRIEF_RENDERERS = {
    "concise": _render_meeting_brief_concise,
    "consultative": _render_meeting_brief_consultative,
    "technical": _render_meeting_brief_technical,
    "meeting_brief": _render_meeting_brief_meeting,
}


# ============================================================
# COVERAGE GAPS RENDERER
# ============================================================


def _render_gaps_concise(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    missing = data.get("missing_coverages", [])
    risk_level = data.get("risk_level", "unknown")

    if not missing:
        text = f"This {industry} account has no identified coverage gaps based on the industry profile."
    else:
        top = prioritize_items(missing, 3)
        text = f"This {industry} account shows a {risk_level}-risk coverage gap. "
        text += f"{top[0].title()} is the most urgent missing line"
        if len(top) > 1:
            rest = ", ".join(t.title() for t in top[1:])
            text += f", with {rest} also worth addressing"
        text += "."

    bullets = [f"Missing: {m.title()}" for m in prioritize_items(missing, opts.max_bullets or 5)]
    if risk_level:
        bullets.insert(0, f"Risk level: {risk_level}")

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="coverage_gaps",
        mode="concise",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "coverage_gaps"),
    )


def _render_gaps_consultative(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    missing = data.get("missing_coverages", [])
    risk_level = data.get("risk_level", "unknown")
    questions = data.get("recommended_questions", [])

    text = f"When speaking with this {industry} client about their coverage program, "
    if missing:
        top = prioritize_items(missing, 3)
        text += f"raise {top[0].title()} as the most important gap to address. "
        if len(top) > 1:
            text += f"Also discuss {', '.join(t.title() for t in top[1:])}. "
    else:
        text += "the current coverage appears well-aligned with industry expectations. "
    text += f"The overall gap risk level is {risk_level}."

    bullets = []
    for m in prioritize_items(missing, opts.max_bullets or 5):
        bullets.append(f"Discuss gap: {m.title()}")
    for q in questions[:2]:
        bullets.append(f"Ask: {q}")

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="coverage_gaps",
        mode="consultative",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "coverage_gaps"),
    )


def _render_gaps_technical(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    missing = data.get("missing_coverages", [])
    risk_level = data.get("risk_level", "unknown")
    exposures = data.get("top_exposures", [])

    text = f"Exposure-to-coverage analysis for {industry}: risk level {risk_level}. "
    if missing:
        text += f"Missing lines: {', '.join(m.title() for m in missing[:5])}. "
    if exposures:
        text += f"Key exposures driving this assessment: {', '.join(exposures[:3])}."

    bullets = []
    for m in prioritize_items(missing, opts.max_bullets or 5):
        bullets.append(f"Unmatched exposure: {m.title()}")
    for e in exposures[:2]:
        bullets.append(f"Driving exposure: {e}")

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="coverage_gaps",
        mode="technical",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "coverage_gaps"),
    )


def _render_gaps_meeting(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    missing = data.get("missing_coverages", [])
    risk_level = data.get("risk_level", "unknown")
    questions = data.get("recommended_questions", [])

    text = f"In your meeting with this {industry} client, coverage gaps should be a key discussion topic. "
    if missing:
        top = prioritize_items(missing, 3)
        text += f"Start with {top[0].title()} as the highest-priority gap. "
    text += f"Overall gap risk level: {risk_level}."

    bullets = []
    for m in prioritize_items(missing, 3):
        bullets.append(f"Raise in meeting: {m.title()}")
    for q in questions[:2]:
        bullets.append(f"Ask the client: {q}")

    if opts.max_bullets:
        bullets = bullets[:opts.max_bullets]

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="coverage_gaps",
        mode="meeting_brief",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "coverage_gaps"),
    )


_COVERAGE_GAPS_RENDERERS = {
    "concise": _render_gaps_concise,
    "consultative": _render_gaps_consultative,
    "technical": _render_gaps_technical,
    "meeting_brief": _render_gaps_meeting,
}


# ============================================================
# SUBMISSION READINESS RENDERER
# ============================================================


def _render_readiness_concise(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    score = data.get("readiness_score", 0)
    level = data.get("readiness_level", "unknown")
    critical = data.get("missing_critical_fields", [])
    next_steps = data.get("next_steps", [])

    text = f"This {industry} submission scores {score}/100 ({level}). "
    if critical:
        text += f"Critical gaps: {', '.join(critical[:3])}. "
    elif next_steps:
        text += f"{next_steps[0]} "

    bullets = []
    bullets.append(f"Readiness: {score}/100 ({level})")
    for c in critical[:3]:
        bullets.append(f"Missing critical: {c}")
    for ns in prioritize_items(next_steps, opts.max_bullets or 3):
        bullets.append(ns)

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="submission_readiness",
        mode="concise",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "submission_readiness"),
    )


def _render_readiness_consultative(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    score = data.get("readiness_score", 0)
    level = data.get("readiness_level", "unknown")
    critical = data.get("missing_critical_fields", [])
    weak = data.get("weak_fields", [])
    next_steps = data.get("next_steps", [])

    text = f"This {industry} submission is {level} right now. "
    if critical:
        text += f"Tighten {' and '.join(critical[:2])} first"
        if weak:
            text += f", then clarify {weak[0].lower()}"
        text += " before sending it to market. "
    elif weak:
        text += f"Strengthen {weak[0].lower()} to improve market reception. "
    else:
        text += "The submission looks solid for market. "

    text += f"Current score: {score}/100."

    bullets = []
    for ns in prioritize_items(next_steps, opts.max_bullets or 5):
        bullets.append(_tone_action(opts.tone, ns))

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="submission_readiness",
        mode="consultative",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "submission_readiness"),
    )


def _render_readiness_technical(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    score = data.get("readiness_score", 0)
    level = data.get("readiness_level", "unknown")
    critical = data.get("missing_critical_fields", [])
    recommended = data.get("missing_recommended_fields", [])
    weak = data.get("weak_fields", [])

    text = f"Submission quality assessment for {industry}: {score}/100 ({level}). "
    if critical:
        text += f"Critical deficiencies: {', '.join(critical[:4])}. "
    if weak:
        text += f"Weak fields requiring expansion: {', '.join(weak[:3])}. "
    if recommended:
        text += f"Recommended additions: {', '.join(recommended[:3])}."

    bullets = []
    for c in critical:
        bullets.append(f"Critical missing: {c}")
    for w in weak:
        bullets.append(f"Weak: {w}")
    for r in recommended[:3]:
        bullets.append(f"Recommended: {r}")

    if opts.max_bullets:
        bullets = bullets[:opts.max_bullets]

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="submission_readiness",
        mode="technical",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "submission_readiness"),
    )


def _render_readiness_meeting(data: dict, opts: RewriteOptions) -> RenderedResponse:
    industry = data.get("industry", "this account")
    score = data.get("readiness_score", 0)
    level = data.get("readiness_level", "unknown")
    critical = data.get("missing_critical_fields", [])
    next_steps = data.get("next_steps", [])

    text = f"Before sending this {industry} submission to market ({score}/100, {level}), "
    if critical:
        text += f"the producer should obtain {' and '.join(critical[:2])}. "
    else:
        text += "the key items are in place. "
    if next_steps:
        text += f"Next step: {next_steps[0].lower()}."

    bullets = []
    bullets.append(f"Readiness: {score}/100 ({level})")
    for ns in next_steps[:4]:
        bullets.append(f"Action: {ns}")

    if opts.max_bullets:
        bullets = bullets[:opts.max_bullets]

    text = truncate_sentences(text, opts.max_sentences)
    if opts.include_disclaimer:
        text += f" {_disclaimer()}"

    return RenderedResponse(
        response_type="submission_readiness",
        mode="meeting_brief",
        tone=opts.tone,
        rendered_text=text,
        rendered_bullets=bullets,
        source_summary=build_source_summary(data, "submission_readiness"),
    )


_SUBMISSION_READINESS_RENDERERS = {
    "concise": _render_readiness_concise,
    "consultative": _render_readiness_consultative,
    "technical": _render_readiness_technical,
    "meeting_brief": _render_readiness_meeting,
}


# ============================================================
# TEMPLATE-BASED RENDERER (default)
# ============================================================


def render_with_templates(
    data: dict,
    response_type: str,
    options: RewriteOptions,
) -> RenderedResponse:
    """Deterministic template-based rendering. Default renderer."""
    renderers = {
        "meeting_brief": _MEETING_BRIEF_RENDERERS,
        "coverage_gaps": _COVERAGE_GAPS_RENDERERS,
        "submission_readiness": _SUBMISSION_READINESS_RENDERERS,
    }

    type_renderers = renderers.get(response_type, {})
    renderer = type_renderers.get(options.mode, type_renderers.get("concise"))

    if renderer is None:
        return RenderedResponse(
            response_type=response_type,
            mode=options.mode,
            tone=options.tone,
            rendered_text=f"No renderer available for {response_type}/{options.mode}.",
            rendered_bullets=[],
            source_summary=build_source_summary(data, response_type),
        )

    return renderer(data, options)


# Placeholder for future LLM-based rendering.
# def render_with_llm(data: dict, response_type: str, options: RewriteOptions) -> RenderedResponse:
#     """Optional LLM-powered rendering. Not yet implemented."""
#     raise NotImplementedError("LLM rendering is not yet available")


# ============================================================
# PUBLIC API
# ============================================================


def _record_shown_event(
    rendered: RenderedResponse,
    output_id: str,
    endpoint: str,
    industry: Optional[str] = None,
    office_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """Auto-record a 'shown' telemetry event. Non-blocking."""
    try:
        from app.services.telemetry_store import record_rendered_output_event
        record_rendered_output_event(
            event_type="rendered_output_shown",
            endpoint=endpoint,
            response_type=rendered.response_type,
            mode=rendered.mode,
            tone=rendered.tone,
            office_id=office_id,
            industry=industry,
            session_id=session_id,
            output_id=output_id,
            metadata={
                "bullet_count": len(rendered.rendered_bullets),
                "text_length": len(rendered.rendered_text),
                "source_summary": rendered.source_summary,
            },
        )
    except Exception:
        logger.debug("Failed to record rendered output shown event", exc_info=True)


def rewrite_meeting_brief(
    brief_data: dict,
    options: Optional[RewriteOptions] = None,
    endpoint: str = "/meeting/brief",
    office_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """Rewrite a meeting brief into producer-facing language.

    Returns both the rendered presentation and the original unchanged data.
    """
    opts = _resolve_options(options)
    rendered = render_with_templates(brief_data, "meeting_brief", opts)
    output_id = f"out_{uuid.uuid4().hex[:12]}"
    rendered_dict = rendered.to_dict()
    rendered_dict["output_id"] = output_id

    industry = brief_data.get("industry")
    _record_shown_event(rendered, output_id, endpoint, industry, office_id, session_id)

    return {
        "rendered": rendered_dict,
        "original": brief_data,
    }


def rewrite_coverage_gaps(
    gap_data: dict,
    options: Optional[RewriteOptions] = None,
    endpoint: str = "/risk/gaps",
    office_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """Rewrite coverage gap analysis into producer-facing language.

    Returns both the rendered presentation and the original unchanged data.
    """
    opts = _resolve_options(options)
    rendered = render_with_templates(gap_data, "coverage_gaps", opts)
    output_id = f"out_{uuid.uuid4().hex[:12]}"
    rendered_dict = rendered.to_dict()
    rendered_dict["output_id"] = output_id

    industry = gap_data.get("industry")
    _record_shown_event(rendered, output_id, endpoint, industry, office_id, session_id)

    return {
        "rendered": rendered_dict,
        "original": gap_data,
    }


def rewrite_submission_readiness(
    readiness_data: dict,
    options: Optional[RewriteOptions] = None,
    endpoint: str = "/submission/readiness",
    office_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """Rewrite submission readiness into producer-facing language.

    Returns both the rendered presentation and the original unchanged data.
    """
    opts = _resolve_options(options)
    rendered = render_with_templates(readiness_data, "submission_readiness", opts)
    output_id = f"out_{uuid.uuid4().hex[:12]}"
    rendered_dict = rendered.to_dict()
    rendered_dict["output_id"] = output_id

    industry = readiness_data.get("industry")
    _record_shown_event(rendered, output_id, endpoint, industry, office_id, session_id)

    return {
        "rendered": rendered_dict,
        "original": readiness_data,
    }
