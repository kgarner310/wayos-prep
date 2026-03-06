"""Tagging service using rules + lightweight LLM extraction."""

import json
import logging
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import (
    TagType, STARTER_INDUSTRY_TAGS, STARTER_COVERAGE_TAGS,
    STARTER_RISK_THEME_TAGS, STARTER_ACCOUNT_TRAIT_TAGS,
    STARTER_JURISDICTION_TAGS,
)
from app.models.models import Source, SourceTag, SourceChunk, ChunkTag

logger = logging.getLogger(__name__)

# Rule-based keyword maps
INDUSTRY_KEYWORDS = {
    "roofing": ["roofing", "roofer", "roof replacement", "shingle", "rooftop"],
    "trucking": ["trucking", "trucker", "cdl", "freight", "long-haul", "fleet", "tractor-trailer", "dot compliance"],
    "manufacturing": ["manufacturing", "factory", "production line", "assembly", "fabrication", "machine shop"],
    "habitational": ["habitational", "apartment", "multi-family", "rental property", "landlord", "tenant"],
    "restaurant": ["restaurant", "food service", "kitchen", "dining", "chef", "food prep"],
    "retail": ["retail", "store", "storefront", "merchandise", "point of sale"],
    "artisan_contractor": ["artisan", "plumber", "electrician", "hvac", "handyman", "subcontractor"],
    "auto_service": ["auto repair", "mechanic", "body shop", "auto service", "tire shop"],
    "landscaping": ["landscaping", "lawn care", "tree service", "grounds maintenance", "mowing"],
    "wholesale": ["wholesale", "distribution", "warehouse", "distributor"],
}

COVERAGE_KEYWORDS = {
    "workers_comp": ["workers comp", "workers' comp", "work comp", "wc claim", "workplace injury", "osha"],
    "general_liability": ["general liability", "gl ", "slip and fall", "bodily injury", "premises liability"],
    "commercial_auto": ["commercial auto", "fleet insurance", "vehicle coverage", "auto liability", "trucking insurance"],
    "umbrella": ["umbrella", "excess liability"],
    "property": ["property insurance", "building coverage", "business personal property", "bpp"],
    "builders_risk": ["builders risk", "course of construction"],
    "inland_marine": ["inland marine", "equipment floater", "contractors equipment"],
    "cyber": ["cyber liability", "data breach", "cyber insurance", "ransomware"],
    "epli": ["epli", "employment practices", "wrongful termination", "discrimination claim"],
    "professional_liability": ["professional liability", "e&o", "errors and omissions", "malpractice"],
}

RISK_THEME_KEYWORDS = {
    "falls_from_height": ["fall from height", "fall protection", "ladder", "scaffold", "rooftop fall"],
    "fleet_accidents": ["fleet accident", "vehicle collision", "truck crash", "mvr", "driver safety"],
    "driver_turnover": ["driver turnover", "driver shortage", "driver retention"],
    "subcontractor_transfer": ["subcontractor", "sub transfer", "certificate of insurance", "coi"],
    "certificate_tracking": ["certificate tracking", "coi management", "certificate compliance"],
    "residential_exposure": ["residential", "homeowner", "residential work"],
    "equipment_theft": ["equipment theft", "tool theft", "stolen equipment"],
    "slip_and_fall": ["slip and fall", "trip and fall", "wet floor"],
    "machine_guarding": ["machine guarding", "lockout tagout", "loto", "machine safety"],
    "combustible_dust": ["combustible dust", "dust explosion", "dust collection"],
    "improper_classification": ["misclassification", "class code", "improper classification", "audit"],
    "hired_non_owned_auto": ["hired and non-owned", "hnoa", "hired auto", "non-owned auto"],
}

ACCOUNT_TRAIT_KEYWORDS = {
    "uses_subcontractors": ["subcontractor", "sub", "1099 worker"],
    "multi_state_operations": ["multi-state", "multiple states", "interstate"],
    "high_mod": ["high mod", "experience mod above", "mod over 1"],
    "young_fleet": ["new vehicles", "young fleet"],
    "heavy_equipment": ["heavy equipment", "crane", "excavator", "backhoe", "forklift"],
    "residential_work": ["residential work", "residential project", "home construction"],
    "habitational_exposure": ["apartment", "tenant", "rental unit", "multi-family"],
    "delivery_operations": ["delivery", "last mile", "courier"],
    "seasonal_payroll": ["seasonal", "seasonal worker", "peak season"],
    "high_turnover": ["turnover", "high turnover", "retention problem"],
}

US_STATES = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
    "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
    "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
    "new hampshire": "nh", "new jersey": "nj", "new mexico": "nm", "new york": "ny",
    "north carolina": "nc", "north dakota": "nd", "ohio": "oh", "oklahoma": "ok",
    "oregon": "or", "pennsylvania": "pa", "rhode island": "ri", "south carolina": "sc",
    "south dakota": "sd", "tennessee": "tn", "texas": "tx", "utah": "ut",
    "vermont": "vt", "virginia": "va", "washington": "wa", "west virginia": "wv",
    "wisconsin": "wi", "wyoming": "wy",
}
STATE_ABBREVS = set(US_STATES.values())


def tag_source(db: Session, source: Source) -> list[SourceTag]:
    """Apply rule-based tags to a source."""
    text = (source.raw_text or "").lower()
    title = (source.title or "").lower()
    combined = f"{title} {text}"

    tags = []

    # Industry tags
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 2 or (score >= 1 and industry in title):
            tags.append(_create_tag(db, source.id, TagType.INDUSTRY, industry, min(score / len(keywords), 1.0)))

    # Coverage tags
    for coverage, keywords in COVERAGE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.COVERAGE, coverage, min(score / len(keywords), 1.0)))

    # Risk theme tags
    for theme, keywords in RISK_THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.RISK_THEME, theme, min(score / len(keywords), 1.0)))

    # Account trait tags
    for trait, keywords in ACCOUNT_TRAIT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.ACCOUNT_TRAIT, trait, min(score / len(keywords), 1.0)))

    # Jurisdiction tags
    for state_name, state_code in US_STATES.items():
        if state_name in combined or f" {state_code} " in f" {combined} ":
            tags.append(_create_tag(db, source.id, TagType.JURISDICTION, state_code, 0.8))

    if "federal" in combined:
        tags.append(_create_tag(db, source.id, TagType.JURISDICTION, "federal", 0.9))
    if "nationwide" in combined or "national" in combined:
        tags.append(_create_tag(db, source.id, TagType.JURISDICTION, "national", 0.8))

    db.commit()
    return tags


def tag_chunk(db: Session, chunk: SourceChunk) -> list[ChunkTag]:
    """Apply rule-based tags to a chunk."""
    text = (chunk.text_content or "").lower()
    heading = (chunk.heading or "").lower()
    combined = f"{heading} {text}"

    tags = []

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.INDUSTRY, industry, 0.8))

    for coverage, keywords in COVERAGE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.COVERAGE, coverage, 0.8))

    for theme, keywords in RISK_THEME_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.RISK_THEME, theme, 0.8))

    for trait, keywords in ACCOUNT_TRAIT_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.ACCOUNT_TRAIT, trait, 0.7))

    for state_name, state_code in US_STATES.items():
        if state_name in combined or f" {state_code} " in f" {combined} ":
            tags.append(_create_chunk_tag(db, chunk.id, TagType.JURISDICTION, state_code, 0.7))

    db.commit()
    return tags


def llm_tag_source(db: Session, source: Source) -> list[SourceTag]:
    """Use LLM for additional tag extraction. Falls back gracefully."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
        logger.info("Skipping LLM tagging - no API key configured")
        return []

    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Use first 3000 chars for tagging
        text_sample = (source.raw_text or "")[:3000]

        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": """Extract insurance-related tags from this text. Return JSON with these arrays:
- industries: from [roofing, trucking, manufacturing, habitational, restaurant, retail, artisan_contractor, auto_service, landscaping, wholesale]
- coverages: from [workers_comp, general_liability, commercial_auto, umbrella, property, builders_risk, inland_marine, cyber, epli, professional_liability]
- risk_themes: from [falls_from_height, fleet_accidents, driver_turnover, subcontractor_transfer, certificate_tracking, residential_exposure, equipment_theft, slip_and_fall, machine_guarding, combustible_dust, improper_classification, hired_non_owned_auto]
- jurisdictions: US state codes (lowercase 2-letter) or "federal", "national"

Only include tags clearly supported by the text. Be conservative."""},
                {"role": "user", "content": text_sample}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        result = json.loads(response.choices[0].message.content)
        tags = []

        for industry in result.get("industries", []):
            if industry in [v for v in STARTER_INDUSTRY_TAGS]:
                # Only add if not already tagged by rules
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.INDUSTRY,
                    SourceTag.tag_value == industry
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.INDUSTRY, industry, 0.7))

        for coverage in result.get("coverages", []):
            if coverage in STARTER_COVERAGE_TAGS:
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.COVERAGE,
                    SourceTag.tag_value == coverage
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.COVERAGE, coverage, 0.7))

        for theme in result.get("risk_themes", []):
            if theme in STARTER_RISK_THEME_TAGS:
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.RISK_THEME,
                    SourceTag.tag_value == theme
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.RISK_THEME, theme, 0.6))

        for jur in result.get("jurisdictions", []):
            jur_lower = jur.lower()
            if jur_lower in STATE_ABBREVS or jur_lower in ("federal", "national", "multi_state"):
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.JURISDICTION,
                    SourceTag.tag_value == jur_lower
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.JURISDICTION, jur_lower, 0.6))

        db.commit()
        return tags

    except Exception as e:
        logger.warning(f"LLM tagging failed: {e}")
        return []


def _create_tag(db: Session, source_id, tag_type: str, tag_value: str, confidence: float) -> SourceTag:
    tag = SourceTag(
        source_id=source_id,
        tag_type=tag_type,
        tag_value=tag_value,
        confidence=round(confidence, 2),
    )
    db.add(tag)
    return tag


def _create_chunk_tag(db: Session, chunk_id, tag_type: str, tag_value: str, confidence: float) -> ChunkTag:
    tag = ChunkTag(
        chunk_id=chunk_id,
        tag_type=tag_type,
        tag_value=tag_value,
        confidence=round(confidence, 2),
    )
    db.add(tag)
    return tag
