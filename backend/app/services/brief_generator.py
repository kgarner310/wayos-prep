import time

from sqlalchemy.orm import Session

from app.models.industry import IndustryRiskProfile
from app.models.query_log import QueryLog
from app.services.brief_renderer import (
    build_brief_json,
    render_brief_text,
    render_underwriter_email,
    render_internal_note,
)
from app.config import settings


def _enhance_with_llm(profile: IndustryRiskProfile, location: str | None) -> str | None:
    """Optionally enhance regional notes using LLM."""
    if settings.llm_provider == "none" or not location:
        return None

    prompt = (
        f"In 2-3 sentences, describe specific insurance risk considerations for "
        f"a {profile.industry_name} business located in {location}. "
        f"Focus on regional weather, regulations, or market conditions. Be concise."
    )

    try:
        if settings.llm_provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        elif settings.llm_provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
    except Exception:
        return None
    return None


def generate_brief(
    profile: IndustryRiskProfile,
    location: str,
    employee_count: int | None,
    mod: float | None,
    vehicle_exposure: str | None,
    query_type: str,
    raw_question: str | None,
    db: Session,
) -> QueryLog:
    start = time.time()

    regional_notes = profile.regional_risk_notes or "No specific regional notes available."
    llm_used = None

    enhanced = _enhance_with_llm(profile, location)
    if enhanced:
        regional_notes = enhanced
        llm_used = settings.llm_provider

    brief_json = build_brief_json(
        industry_name=profile.industry_name,
        location=location,
        employee_count=employee_count,
        mod=mod,
        vehicle_exposure=vehicle_exposure,
        top_claims=profile.top_workers_comp_claims + profile.commercial_auto_claims,
        regional_notes=regional_notes,
        coverage_exposures=profile.general_liability_exposures,
        conversation_starters=profile.conversation_prompts,
    )

    brief_text = render_brief_text(brief_json)
    underwriter_email = render_underwriter_email(brief_json)
    internal_note = render_internal_note(brief_json)

    latency_ms = int((time.time() - start) * 1000)

    log = QueryLog(
        query_type=query_type,
        raw_question=raw_question,
        industry_id=profile.id,
        location=location,
        employee_count=employee_count,
        mod=mod,
        vehicle_exposure=vehicle_exposure,
        brief_json=brief_json,
        brief_text=brief_text,
        underwriter_email_text=underwriter_email,
        internal_note_text=internal_note,
        llm_used=llm_used,
        latency_ms=latency_ms,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return log
