import asyncio
import logging
import re
import time

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.industry import IndustryRiskProfile
from app.models.query_log import QueryLog
from app.models.state_profile import StateProfile
from app.services.brief_renderer import (
    build_brief_json,
    render_brief_text,
    render_underwriter_email,
    render_internal_note,
)
from app.config import settings

# Mapping of full state names to two-letter codes
_STATE_NAME_TO_CODE: dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}

_VALID_CODES = set(_STATE_NAME_TO_CODE.values())


def extract_state_code(location: str) -> str | None:
    """Extract a two-letter state code from a location string.

    Handles formats like: "NC", "North Carolina", "Asheville, NC",
    "Charlotte, North Carolina", "Asheville NC".
    """
    if not location:
        return None

    text = location.strip()

    # Check for two-letter code at end: "Asheville, NC" or "Asheville NC"
    match = re.search(r'\b([A-Z]{2})\s*$', text)
    if match and match.group(1) in _VALID_CODES:
        return match.group(1)

    # Check for full state name
    lower = text.lower()
    for name, code in _STATE_NAME_TO_CODE.items():
        if name in lower:
            return code

    # Check if the entire string is a two-letter code
    if text.upper() in _VALID_CODES and len(text) == 2:
        return text.upper()

    return None


def _lookup_state(state_code: str, db: Session) -> StateProfile | None:
    """Look up a state profile by code."""
    return db.query(StateProfile).filter(
        StateProfile.state_code == state_code
    ).first()


def _run_data_mining(location: str, industry_name: str) -> dict | None:
    """Run the async data mining orchestrator from sync context.

    Returns the brief-ready dict from LocationIntel, or None on failure.
    """
    if location in ("Not specified", ""):
        return None

    try:
        from app.services.data_mining.orchestrator import gather_location_intel

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
            # We're already in an async context (shouldn't happen in sync endpoints)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run,
                    gather_location_intel(location, industry_name)
                ).result(timeout=30)
        except RuntimeError:
            # No running loop — normal case for sync endpoints
            result = asyncio.run(gather_location_intel(location, industry_name))

        if result:
            return result.to_brief_dict()
        return None

    except Exception:
        logger.exception("Data mining failed for %s", location)
        return None


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
        logger.exception("LLM enhancement failed for %s in %s", profile.industry_name, location)
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

    # State enrichment
    state_wc_notes = None
    state_compliance_items = None
    tort_environment = None
    cat_exposures = None

    state_code = extract_state_code(location)
    if state_code:
        state_profile = _lookup_state(state_code, db)
        if state_profile:
            state_wc_notes = state_profile.wc_notes
            state_compliance_items = state_profile.compliance_items or []
            tort_environment = state_profile.tort_environment
            cat_exposures = state_profile.cat_exposures or []

    # Data mining — public data sources
    location_intel = _run_data_mining(location, profile.industry_name)

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
        state_wc_notes=state_wc_notes,
        state_compliance_items=state_compliance_items,
        tort_environment=tort_environment,
        cat_exposures=cat_exposures,
        location_intel=location_intel,
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
