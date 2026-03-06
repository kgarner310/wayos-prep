"""Brief generation service using OpenAI."""

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import GeneratedBrief, BriefSource, Query, RetrievalRun
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

    # Build source context for the LLM
    context_parts = []
    source_map = {}

    for i, chunk in enumerate(chunks):
        source_id = str(chunk["source_id"])
        source_map[source_id] = {
            "title": chunk.get("source_title", "Unknown"),
            "url": chunk.get("source_url"),
        }
        context_parts.append(
            f"[SOURCE {source_id}] (Title: {chunk.get('source_title', 'Unknown')})\n"
            f"{chunk.get('heading', '')}\n{chunk['text_content']}\n"
        )

    context_text = "\n---\n".join(context_parts)

    user_prompt = f"""Generate a pre-meeting brief for:
- Industry: {industry}
- State: {state}
- Employee count: {employee_count or 'unknown'}
- Current mod: {current_mod or 'unknown'}
{f'- Additional context: {raw_query}' if raw_query else ''}

SOURCE CONTEXT:
{context_text}"""

    # Try LLM generation
    brief_json = _call_llm(user_prompt, industry, state, employee_count, current_mod, source_map)

    if brief_json is None:
        # Fallback: generate a basic brief from the chunks
        brief_json = _fallback_brief(chunks, industry, state, employee_count, current_mod, source_map)

    # Validate with Pydantic
    try:
        validated = BriefOutput(**brief_json)
        brief_json = validated.model_dump()
    except Exception as e:
        logger.warning(f"Brief validation issue: {e}")

    # Render markdown
    rendered_md = render_brief_markdown(brief_json)

    # Store the brief
    brief = GeneratedBrief(
        query_id=query.id,
        retrieval_run_id=retrieval_run.id,
        model_name=settings.LLM_MODEL if settings.OPENAI_API_KEY else "fallback",
        brief_json=brief_json,
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


def _call_llm(user_prompt: str, industry: str, state: str,
              employee_count: int | None, current_mod: float | None,
              source_map: dict) -> dict | None:
    """Call OpenAI to generate brief. Returns None on failure."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
        logger.info("No OpenAI API key - using fallback brief generation")
        return None

    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

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

            # Validate it has the required structure
            validated = BriefOutput(**result)
            return validated.model_dump()

        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON (attempt {attempt + 1}): {e}")
            if attempt == 0:
                continue
            return None
        except Exception as e:
            logger.warning(f"LLM brief generation failed (attempt {attempt + 1}): {e}")
            if attempt == 0:
                continue
            return None

    return None


def _fallback_brief(chunks: list[dict], industry: str, state: str,
                    employee_count: int | None, current_mod: float | None,
                    source_map: dict) -> dict:
    """Generate a basic brief without LLM from chunk content."""
    source_ids = [str(c["source_id"]) for c in chunks[:3]]

    brief = {
        "industry": industry,
        "state": state,
        "employee_count": employee_count or 0,
        "current_mod": current_mod,
        "top_loss_drivers": [
            {
                "title": f"Review {industry} loss patterns",
                "why_it_matters": f"Based on {len(chunks)} source documents, review the typical loss drivers for {industry} operations in {state}.",
                "confidence": "low",
                "source_ids": source_ids,
            }
        ],
        "coverage_blind_spots": [
            {
                "title": "Coverage gap analysis needed",
                "why_it_matters": f"Review source materials for {industry}-specific coverage considerations in {state}.",
                "source_ids": source_ids,
            }
        ],
        "questions_to_ask": [
            {
                "question": "What is your current safety program?",
                "purpose": "Assess risk management maturity",
                "source_ids": [],
            },
            {
                "question": "Do you use subcontractors? If so, how do you manage certificates?",
                "purpose": "Evaluate subcontractor exposure and certificate compliance",
                "source_ids": [],
            },
        ],
        "watchouts": [
            {
                "note": f"Limited source context available for {industry} in {state}. Brief confidence is low.",
                "source_ids": [],
            }
        ],
        "confidence_notes": [
            {
                "note": "This brief was generated without LLM enhancement. Source context may be incomplete.",
                "severity": "warning",
            }
        ],
        "citation_map": [
            {
                "source_id": sid,
                "title": source_map.get(sid, {}).get("title", "Unknown"),
                "url": source_map.get(sid, {}).get("url"),
            }
            for sid in source_ids
        ],
    }
    return brief


def render_brief_markdown(brief: dict) -> str:
    """Render brief JSON to producer-friendly markdown."""
    lines = []
    lines.append(f"# WAYOS PREP Brief")
    lines.append(f"**Industry:** {brief.get('industry', 'N/A')}  ")
    lines.append(f"**State:** {brief.get('state', 'N/A')}  ")
    if brief.get("employee_count"):
        lines.append(f"**Employees:** {brief['employee_count']}  ")
    if brief.get("current_mod"):
        lines.append(f"**Current Mod:** {brief['current_mod']}  ")
    lines.append("")

    # Loss drivers
    drivers = brief.get("top_loss_drivers", [])
    if drivers:
        lines.append("## Top Loss Drivers")
        for d in drivers:
            conf = f" ({d.get('confidence', 'medium')} confidence)" if d.get('confidence') else ""
            lines.append(f"### {d['title']}{conf}")
            lines.append(d.get("why_it_matters", ""))
            lines.append("")

    # Coverage blind spots
    spots = brief.get("coverage_blind_spots", [])
    if spots:
        lines.append("## Coverage Blind Spots")
        for s in spots:
            lines.append(f"### {s['title']}")
            lines.append(s.get("why_it_matters", ""))
            lines.append("")

    # Questions
    questions = brief.get("questions_to_ask", [])
    if questions:
        lines.append("## Questions to Ask")
        for q in questions:
            lines.append(f"- **{q['question']}**")
            if q.get("purpose"):
                lines.append(f"  *Purpose: {q['purpose']}*")
        lines.append("")

    # Watchouts
    watchouts = brief.get("watchouts", [])
    if watchouts:
        lines.append("## Watchouts")
        for w in watchouts:
            lines.append(f"- {w['note']}")
        lines.append("")

    # Confidence notes
    notes = brief.get("confidence_notes", [])
    if notes:
        lines.append("## Confidence Notes")
        for n in notes:
            severity = n.get("severity", "info").upper()
            lines.append(f"- [{severity}] {n['note']}")
        lines.append("")

    # Citations
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
