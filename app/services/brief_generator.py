"""Brief generation service using OpenAI (with deterministic fallback)."""

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import TagType
from app.models.models import GeneratedBrief, BriefSource, Query, RetrievalRun, ChunkTag
from app.schemas.schemas import BriefOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are WAYOS PREP, an insurance meeting-brief engine for commercial producers.
Your job is to generate a concise, decision-useful pre-meeting brief using ONLY the provided source context.

Rules:
1. Do not invent laws, exclusions, trends, or state-specific rules not supported by the supplied context.
2. Prefer regulator, court, or higher-authority sources when conflicts exist.
3. If the context is weak or mixed, say so clearly.
4. Tailor the brief to the requested industry and state.
5. Focus on practical producer usefulness:
   - likely loss drivers
   - likely coverage blind spots
   - smart questions to ask
   - operational watchouts
6. Do not give legal advice.
7. Return valid JSON matching the schema exactly.
8. Every substantive claim must map to one or more provided source IDs.

Developer guidance:
- Keep loss drivers specific, not generic.
- Questions should help a producer uncover underwriting, safety, payroll, fleet, subcontractor, or operational risk.
- If a state-specific point is unsupported, mark it as general rather than state-specific.
- Do not mention sources in prose; use source_ids in the JSON fields.

Return JSON matching this exact schema:
{
  "industry": "string",
  "state": "string",
  "employee_count": 0,
  "current_mod": null,
  "top_loss_drivers": [
    {"title": "string", "why_it_matters": "string", "confidence": "high|medium|low", "source_ids": ["string"]}
  ],
  "coverage_blind_spots": [
    {"title": "string", "why_it_matters": "string", "source_ids": ["string"]}
  ],
  "questions_to_ask": [
    {"question": "string", "purpose": "string", "source_ids": ["string"]}
  ],
  "watchouts": [
    {"note": "string", "source_ids": ["string"]}
  ],
  "confidence_notes": [
    {"note": "string", "severity": "info|warning|critical"}
  ],
  "citation_map": [
    {"source_id": "string", "title": "string", "url": "string or null"}
  ]
}"""


def _has_openai_key() -> bool:
    return bool(settings.OPENAI_API_KEY) and not settings.OPENAI_API_KEY.startswith("sk-your")


def generate_brief(
    db: Session,
    query: Query,
    retrieval_run: RetrievalRun,
    chunks: list[dict],
    industry: str,
    state: str,
    employee_count: int | None = None,
    current_mod: float | None = None,
    raw_query: str | None = None,
) -> GeneratedBrief:
    """Generate a brief from retrieved chunks."""

    # Build source context
    context_parts = []
    source_map = {}

    for chunk in chunks:
        source_id = str(chunk["source_id"])
        source_map[source_id] = {
            "title": chunk.get("source_title", "Unknown"),
            "url": chunk.get("source_url"),
        }
        heading = chunk.get("heading") or ""
        context_parts.append(
            f"[SOURCE {source_id}] (Title: {chunk.get('source_title', 'Unknown')})\n"
            f"{heading}\n{chunk['text_content']}\n"
        )

    context_text = "\n---\n".join(context_parts)

    # Try LLM, then fall back
    brief_dict = None
    model_used = "fallback"

    if _has_openai_key() and chunks:
        brief_dict = _call_llm(context_text, industry, state, employee_count, current_mod, raw_query)
        if brief_dict:
            model_used = settings.LLM_MODEL

    if brief_dict is None:
        brief_dict = _fallback_brief(db, chunks, industry, state, employee_count, current_mod, source_map)

    # Strict schema validation — fail loud, then retry with fallback
    try:
        validated = BriefOutput(**brief_dict)
        brief_dict = validated.model_dump()
    except Exception as e:
        logger.error(f"Brief schema validation failed: {e}")
        brief_dict = _fallback_brief(db, chunks, industry, state, employee_count, current_mod, source_map)
        validated = BriefOutput(**brief_dict)
        brief_dict = validated.model_dump()
        model_used = "fallback"

    rendered_md = render_brief_markdown(brief_dict)

    brief = GeneratedBrief(
        query_id=query.id,
        retrieval_run_id=retrieval_run.id,
        model_name=model_used,
        brief_json=brief_dict,
        rendered_markdown=rendered_md,
    )
    db.add(brief)
    db.flush()

    # Store brief sources
    seen_sources = set()
    for chunk in chunks:
        source_id = chunk["source_id"]
        if source_id not in seen_sources:
            bs = BriefSource(
                brief_id=brief.id,
                source_id=source_id,
                chunk_id=chunk["chunk_id"],
                citation_label=source_map.get(str(source_id), {}).get("title", ""),
            )
            db.add(bs)
            seen_sources.add(source_id)

    db.commit()
    db.refresh(brief)
    return brief


def _call_llm(context_text: str, industry: str, state: str,
              employee_count: int | None, current_mod: float | None,
              raw_query: str | None) -> dict | None:
    """Call OpenAI to generate brief. Returns None on failure."""
    try:
        import openai
    except ImportError:
        logger.warning("openai package not installed")
        return None

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    user_prompt = f"""Generate a pre-meeting brief for:
- Industry: {industry}
- State: {state}
- Employee count: {employee_count or 'unknown'}
- Current mod: {current_mod or 'unknown'}
{f'- Additional context: {raw_query}' if raw_query else ''}

SOURCE CONTEXT:
{context_text}"""

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=3000,
            )

            result = json.loads(response.choices[0].message.content)
            validated = BriefOutput(**result)
            return validated.model_dump()

        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.warning(f"LLM brief generation failed (attempt {attempt + 1}): {e}")

    return None


def _fallback_brief(db: Session, chunks: list[dict], industry: str, state: str,
                    employee_count: int | None, current_mod: float | None,
                    source_map: dict) -> dict:
    """Generate a deterministic brief from chunk tags and content. No LLM needed."""
    source_ids = list(dict.fromkeys(str(c["source_id"]) for c in chunks))[:5]

    # Extract tag-based intelligence from chunks
    loss_drivers = []
    coverage_tags = set()
    risk_themes = set()
    account_traits = set()

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk_id and db:
            tags = db.query(ChunkTag).filter(ChunkTag.chunk_id == chunk_id).all()
            for t in tags:
                if t.tag_type == TagType.COVERAGE:
                    coverage_tags.add(t.tag_value)
                elif t.tag_type == TagType.RISK_THEME:
                    risk_themes.add(t.tag_value)
                elif t.tag_type == TagType.ACCOUNT_TRAIT:
                    account_traits.add(t.tag_value)

    # Build loss drivers from risk themes found in source data
    _theme_labels = {
        "falls_from_height": ("Falls from Height", "Leading cause of severe injury and death in this industry"),
        "fleet_accidents": ("Fleet/Vehicle Accidents", "Major liability and WC exposure from vehicle operations"),
        "driver_turnover": ("Driver Turnover", "High turnover leads to inexperienced operators and increased accident frequency"),
        "machine_guarding": ("Machine Guarding Hazards", "OSHA's most-cited standard — amputations and crush injuries drive severe claims"),
        "combustible_dust": ("Combustible Dust", "Explosion risk from dust accumulation in manufacturing environments"),
        "slip_and_fall": ("Slip and Fall", "Common premises and workplace injury driving WC and GL claims"),
        "subcontractor_transfer": ("Subcontractor Risk Transfer", "Coverage gaps from uninsured or underinsured subcontractors"),
        "improper_classification": ("Improper Classification", "Employee misclassification creates audit exposure and premium disputes"),
        "certificate_tracking": ("Certificate Tracking Gaps", "Missing or expired COIs expose the employer to uninsured losses"),
        "hired_non_owned_auto": ("Hired/Non-Owned Auto Exposure", "Personal vehicle use on company business without proper coverage"),
    }

    for theme in risk_themes:
        if theme in _theme_labels:
            label, desc = _theme_labels[theme]
            loss_drivers.append({
                "title": label,
                "why_it_matters": desc,
                "confidence": "medium",
                "source_ids": source_ids[:2],
            })

    if not loss_drivers:
        loss_drivers.append({
            "title": f"Review {industry} loss patterns",
            "why_it_matters": f"Based on {len(chunks)} source documents — review typical loss drivers for {industry} in {state}.",
            "confidence": "low",
            "source_ids": source_ids[:2],
        })

    # Build coverage blind spots from coverage tags
    _coverage_labels = {
        "workers_comp": "Workers Compensation",
        "general_liability": "General Liability",
        "commercial_auto": "Commercial Auto",
        "umbrella": "Umbrella/Excess",
        "property": "Property",
        "builders_risk": "Builders Risk",
        "inland_marine": "Inland Marine",
        "cyber": "Cyber Liability",
        "epli": "EPLI",
        "professional_liability": "Professional Liability",
    }
    blind_spots = []
    for cov in coverage_tags:
        label = _coverage_labels.get(cov, cov.replace("_", " ").title())
        blind_spots.append({
            "title": f"Review {label} Coverage",
            "why_it_matters": f"Source materials reference {label} exposure for this type of operation.",
            "source_ids": source_ids[:2],
        })

    if not blind_spots:
        blind_spots.append({
            "title": "Coverage gap analysis needed",
            "why_it_matters": f"Review available source materials for {industry}-specific coverage in {state}.",
            "source_ids": source_ids[:1],
        })

    # Standard questions
    questions = [
        {"question": "What is your current safety program?", "purpose": "Assess risk management maturity", "source_ids": []},
        {"question": "Do you use subcontractors? How do you manage certificates?", "purpose": "Evaluate subcontractor exposure and certificate compliance", "source_ids": []},
        {"question": "What does your fleet look like and who drives?", "purpose": "Assess commercial auto and hired/non-owned exposure", "source_ids": []},
    ]

    if "high_mod" in account_traits or (current_mod and current_mod > 1.0):
        questions.append({
            "question": "What loss control measures have you implemented in the last 12 months?",
            "purpose": "Identify mod improvement opportunities",
            "source_ids": [],
        })

    # Watchouts
    watchouts = []
    if "uses_subcontractors" in account_traits:
        watchouts.append({"note": "Subcontractor usage detected — verify certificate tracking and additional insured status.", "source_ids": source_ids[:1]})
    if "multi_state_operations" in account_traits:
        watchouts.append({"note": "Multi-state operations — check WC filing requirements by state.", "source_ids": source_ids[:1]})

    # Confidence notes
    confidence_notes = []
    if not _has_openai_key():
        confidence_notes.append({"note": "Brief generated from tag-based analysis (no LLM). Add OPENAI_API_KEY for richer briefs.", "severity": "info"})
    if len(chunks) < 3:
        confidence_notes.append({"note": f"Only {len(chunks)} source chunks available. Ingest more sources for better coverage.", "severity": "warning"})

    citation_map = [
        {"source_id": sid, "title": source_map.get(sid, {}).get("title", "Unknown"), "url": source_map.get(sid, {}).get("url")}
        for sid in source_ids
    ]

    return {
        "industry": industry,
        "state": state,
        "employee_count": employee_count or 0,
        "current_mod": current_mod,
        "top_loss_drivers": loss_drivers[:5],
        "coverage_blind_spots": blind_spots[:5],
        "questions_to_ask": questions[:5],
        "watchouts": watchouts[:5],
        "confidence_notes": confidence_notes,
        "citation_map": citation_map,
    }


def render_brief_markdown(brief: dict) -> str:
    """Render brief JSON to producer-friendly markdown."""
    lines = []
    lines.append("# WAYOS PREP Brief")
    lines.append(f"**Industry:** {brief.get('industry', 'N/A')}  ")
    lines.append(f"**State:** {brief.get('state', 'N/A')}  ")
    if brief.get("employee_count"):
        lines.append(f"**Employees:** {brief['employee_count']}  ")
    if brief.get("current_mod"):
        lines.append(f"**Current Mod:** {brief['current_mod']}  ")
    lines.append("")

    drivers = brief.get("top_loss_drivers", [])
    if drivers:
        lines.append("## Top Loss Drivers")
        for d in drivers:
            conf = f" ({d.get('confidence', 'medium')} confidence)" if d.get('confidence') else ""
            lines.append(f"### {d['title']}{conf}")
            lines.append(d.get("why_it_matters", ""))
            lines.append("")

    spots = brief.get("coverage_blind_spots", [])
    if spots:
        lines.append("## Coverage Blind Spots")
        for s in spots:
            lines.append(f"### {s['title']}")
            lines.append(s.get("why_it_matters", ""))
            lines.append("")

    questions = brief.get("questions_to_ask", [])
    if questions:
        lines.append("## Questions to Ask")
        for q in questions:
            lines.append(f"- **{q['question']}**")
            if q.get("purpose"):
                lines.append(f"  *Purpose: {q['purpose']}*")
        lines.append("")

    watchouts = brief.get("watchouts", [])
    if watchouts:
        lines.append("## Watchouts")
        for w in watchouts:
            lines.append(f"- {w['note']}")
        lines.append("")

    notes = brief.get("confidence_notes", [])
    if notes:
        lines.append("## Confidence Notes")
        for n in notes:
            severity = n.get("severity", "info").upper()
            lines.append(f"- [{severity}] {n['note']}")
        lines.append("")

    citations = brief.get("citation_map", [])
    if citations:
        lines.append("## Sources")
        for c in citations:
            url = c.get("url")
            if url:
                lines.append(f"- [{c.get('title', 'Source')}]({url})")
            else:
                lines.append(f"- {c.get('title', 'Source')} (ID: {c.get('source_id', 'N/A')})")
        lines.append("")

    return "\n".join(lines)
