from sqlalchemy.orm import Session

from app.models.industry import IndustryRiskProfile
from app.config import settings


def match_industry(query: str, db: Session) -> IndustryRiskProfile | None:
    """Match a user query to an industry using 3-tier matching."""
    normalized = query.strip().lower()

    # 1. Direct name match
    profile = db.query(IndustryRiskProfile).filter(
        IndustryRiskProfile.industry_name.ilike(f"%{normalized}%")
    ).first()
    if profile:
        return profile

    # 2. Synonym match
    all_profiles = db.query(IndustryRiskProfile).all()
    for p in all_profiles:
        for syn in (p.synonyms or []):
            if syn.lower() in normalized or normalized in syn.lower():
                return p

    # 3. Fallback LLM classification
    if settings.llm_provider != "none":
        industry_names = [p.industry_name for p in all_profiles]
        classified = _llm_classify(normalized, industry_names)
        if classified:
            for p in all_profiles:
                if p.industry_name.lower() == classified.lower():
                    return p

    return None


def _llm_classify(query: str, industry_names: list[str]) -> str | None:
    """Use LLM to classify a query into one of the known industries."""
    prompt = (
        f"Given this user question about insurance risks: \"{query}\"\n"
        f"Which of these industries best matches? Return ONLY the industry name, nothing else.\n"
        f"Industries: {', '.join(industry_names)}\n"
        f"If none match well, return 'NONE'."
    )

    try:
        if settings.llm_provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0,
            )
            result = resp.choices[0].message.content.strip()
        elif settings.llm_provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )
            result = resp.content[0].text.strip()
        else:
            return None

        if result.upper() == "NONE":
            return None
        return result
    except Exception:
        return None
