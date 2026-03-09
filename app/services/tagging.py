"""Tagging service using rules + lightweight LLM extraction."""

import json
import logging
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import (
    TagType, STARTER_INDUSTRY_TAGS, STARTER_COVERAGE_TAGS,
    STARTER_RISK_THEME_TAGS, STARTER_ACCOUNT_TRAIT_TAGS,
    STARTER_JURISDICTION_TAGS, STARTER_ENTITY_TYPE_TAGS,
    STARTER_PUBLIC_ENTITY_TYPE_TAGS, STARTER_DEPARTMENT_TAGS,
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
    "hvac": ["hvac", "heating and cooling", "air conditioning", "refrigeration", "furnace", "ductwork"],
}

COVERAGE_KEYWORDS = {
    "workers_comp": ["workers comp", "workers' comp", "work comp", "wc claim", "workplace injury"],
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
    "residential_exposure": ["residential exposure", "residential work", "residential construction"],
    "equipment_theft": ["equipment theft", "tool theft", "stolen equipment"],
    "slip_and_fall": ["slip and fall", "trip and fall", "wet floor"],
    "machine_guarding": ["machine guarding", "lockout tagout", "loto", "machine safety"],
    "combustible_dust": ["combustible dust", "dust explosion", "dust collection"],
    "improper_classification": ["misclassification", "class code", "improper classification", "employee misclassification"],
    "hired_non_owned_auto": ["hired and non-owned", "hnoa", "hired auto", "non-owned auto"],
    "burns_and_scalds": ["burn", "scald", "grease fire", "hot surface", "thermal burn", "fryer"],
    "heat_illness": ["heat illness", "heat stroke", "heat exhaustion", "heat stress", "outdoor heat"],
    "struck_by_object": ["struck by", "falling object", "falling branch", "tree limb", "falling debris"],
    "food_contamination": ["foodborne", "food contamination", "food safety", "food poisoning", "health inspection"],
    "chemical_exposure": ["refrigerant", "chemical exposure", "chemical burn", "toxic exposure", "r-410a"],
    "lifting_ergonomic": ["lifting injury", "back injury", "ergonomic", "manual handling", "repetitive strain"],
}

ACCOUNT_TRAIT_KEYWORDS = {
    "uses_subcontractors": ["subcontractor", "1099 worker", "sub-contractor"],
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

# Entity type keyword maps
ENTITY_TYPE_KEYWORDS = {
    "public_entity": ["municipality", "municipal", "county government", "city government", "town government", "public entity", "government agency", "governmental"],
    "private_business": ["private company", "private business", "commercial business"],
    "nonprofit": ["nonprofit", "non-profit", "501c3", "charitable organization"],
    "educational_entity": ["school district", "university", "community college", "educational institution"],
    "religious_entity": ["church", "religious organization", "house of worship"],
    "tribal_entity": ["tribal government", "tribal nation", "tribal entity"],
}

# Public entity subtype keyword maps
PUBLIC_ENTITY_TYPE_KEYWORDS = {
    "municipality": ["municipality", "municipal", "city government", "town government", "city council", "mayor"],
    "county": ["county government", "county commission", "board of commissioners", "county manager"],
    "school_system": ["school district", "school system", "school board", "public school"],
    "fire_district": ["fire district", "fire department", "fire protection district", "volunteer fire"],
    "utility_authority": ["utility authority", "public utility", "electric authority", "gas authority"],
    "water_sewer_authority": ["water authority", "sewer authority", "water district", "water and sewer"],
    "transit_authority": ["transit authority", "public transit", "bus system", "transportation authority"],
    "parks_recreation_department": ["parks and recreation", "parks department", "recreation department"],
    "public_housing_authority": ["housing authority", "public housing", "section 8"],
    "special_tax_district": ["special district", "tax district", "improvement district"],
}

# Municipal department keyword maps
DEPARTMENT_KEYWORDS = {
    "law_enforcement": ["police", "law enforcement", "sheriff", "police department", "officer", "patrol"],
    "fire_department": ["fire department", "firefighter", "fire station", "fire chief", "fire service"],
    "public_works": ["public works", "road maintenance", "street repair", "infrastructure", "stormwater"],
    "utilities": ["utility department", "water plant", "sewer plant", "electric department"],
    "parks_recreation": ["parks and recreation", "playground", "recreation center", "athletic field", "public pool"],
    "administration": ["city administration", "town administration", "city manager", "finance department", "clerk"],
    "sanitation": ["sanitation", "solid waste", "trash collection", "refuse", "recycling"],
    "street_maintenance": ["street maintenance", "road crew", "pothole", "paving", "street department"],
    "planning_zoning": ["planning and zoning", "zoning board", "building inspector", "code enforcement"],
    "water_treatment": ["water treatment", "water quality", "drinking water", "water testing"],
    "wastewater": ["wastewater", "wastewater treatment", "sewer system", "sewer line"],
    "fleet_services": ["fleet services", "fleet maintenance", "vehicle maintenance", "motor pool"],
}

# Public entity risk theme keyword maps (extend existing RISK_THEME_KEYWORDS)
PUBLIC_RISK_THEME_KEYWORDS = {
    "police_liability": ["police liability", "law enforcement liability", "officer misconduct", "use of force"],
    "civil_rights_claims": ["civil rights", "section 1983", "constitutional rights", "civil rights claim"],
    "excessive_force": ["excessive force", "use of force", "police brutality", "force complaint"],
    "public_officials_liability": ["public official liability", "elected official", "board member liability", "official misconduct"],
    "zoning_decisions": ["zoning decision", "zoning variance", "land use decision", "zoning appeal"],
    "road_maintenance_liability": ["road maintenance", "pothole claim", "road defect", "highway liability", "road condition"],
    "playground_injury": ["playground injury", "playground equipment", "playground safety", "playground inspection"],
    "public_event_liability": ["public event", "festival", "parade", "community event", "public gathering"],
    "sewer_backup_claims": ["sewer backup", "sewer overflow", "sewer claim", "sanitary sewer"],
    "water_quality_claims": ["water quality", "water contamination", "boil water", "drinking water violation"],
    "fleet_liability": ["fleet liability", "government vehicle", "municipal vehicle", "city vehicle accident"],
    "volunteer_liability": ["volunteer liability", "volunteer injury", "volunteer worker", "volunteer firefighter"],
    "cyber_records_breach": ["data breach", "public records breach", "cyber attack", "ransomware attack", "government cyber"],
    "grant_compliance": ["grant compliance", "federal grant", "grant audit", "grant reporting"],
    "procurement_disputes": ["procurement dispute", "bid protest", "public bidding", "procurement violation"],
}

# Public entity coverage keyword maps (extend existing COVERAGE_KEYWORDS)
PUBLIC_COVERAGE_KEYWORDS = {
    "public_officials_liability": ["public officials liability", "public officials e&o", "elected officials coverage"],
    "law_enforcement_liability": ["law enforcement liability", "police professional liability", "officer liability"],
    "governmental_immunity": ["governmental immunity", "sovereign immunity", "tort claims act", "government tort"],
    "employment_practices_public": ["public employment practices", "government epli", "public employee claims"],
    "municipal_auto": ["municipal auto", "government fleet", "city vehicle", "municipal vehicle insurance"],
    "public_entity_property": ["municipal property", "government building", "public entity property"],
    "infrastructure_property": ["infrastructure coverage", "bridge insurance", "road coverage", "public infrastructure"],
    "environmental_liability_public": ["environmental liability", "municipal pollution", "stormwater liability", "public environmental"],
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

    # Entity type tags
    for entity, keywords in ENTITY_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.ENTITY_TYPE, entity, min(score / len(keywords), 1.0)))

    # Public entity subtype tags
    for pet, keywords in PUBLIC_ENTITY_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.PUBLIC_ENTITY_TYPE, pet, min(score / len(keywords), 1.0)))

    # Department tags
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.DEPARTMENT, dept, min(score / len(keywords), 1.0)))

    # Public entity risk themes
    for theme, keywords in PUBLIC_RISK_THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.RISK_THEME, theme, min(score / len(keywords), 1.0)))

    # Public entity coverages
    for coverage, keywords in PUBLIC_COVERAGE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score >= 1:
            tags.append(_create_tag(db, source.id, TagType.COVERAGE, coverage, min(score / len(keywords), 1.0)))

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

    for entity, keywords in ENTITY_TYPE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.ENTITY_TYPE, entity, 0.7))

    for pet, keywords in PUBLIC_ENTITY_TYPE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.PUBLIC_ENTITY_TYPE, pet, 0.7))

    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.DEPARTMENT, dept, 0.7))

    for theme, keywords in PUBLIC_RISK_THEME_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.RISK_THEME, theme, 0.7))

    for coverage, keywords in PUBLIC_COVERAGE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            tags.append(_create_chunk_tag(db, chunk.id, TagType.COVERAGE, coverage, 0.7))

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
- industries: from [roofing, trucking, manufacturing, habitational, restaurant, retail, artisan_contractor, auto_service, landscaping, wholesale, hvac]
- coverages: from [workers_comp, general_liability, commercial_auto, umbrella, property, builders_risk, inland_marine, cyber, epli, professional_liability, public_officials_liability, law_enforcement_liability, governmental_immunity, employment_practices_public, municipal_auto, public_entity_property, infrastructure_property, environmental_liability_public]
- risk_themes: from [falls_from_height, fleet_accidents, driver_turnover, subcontractor_transfer, certificate_tracking, residential_exposure, equipment_theft, slip_and_fall, machine_guarding, combustible_dust, improper_classification, hired_non_owned_auto, burns_and_scalds, heat_illness, struck_by_object, food_contamination, chemical_exposure, lifting_ergonomic, police_liability, civil_rights_claims, excessive_force, public_officials_liability, zoning_decisions, road_maintenance_liability, playground_injury, public_event_liability, sewer_backup_claims, water_quality_claims, fleet_liability, volunteer_liability, cyber_records_breach, grant_compliance, procurement_disputes]
- entity_types: from [private_business, public_entity, nonprofit, educational_entity, religious_entity, tribal_entity]
- public_entity_types: from [municipality, county, school_system, fire_district, utility_authority, water_sewer_authority, transit_authority, parks_recreation_department, public_housing_authority, special_tax_district]
- departments: from [law_enforcement, fire_department, public_works, utilities, parks_recreation, administration, sanitation, street_maintenance, planning_zoning, water_treatment, wastewater, fleet_services]
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

        for et in result.get("entity_types", []):
            if et in STARTER_ENTITY_TYPE_TAGS:
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.ENTITY_TYPE,
                    SourceTag.tag_value == et
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.ENTITY_TYPE, et, 0.7))

        for pet in result.get("public_entity_types", []):
            if pet in STARTER_PUBLIC_ENTITY_TYPE_TAGS:
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.PUBLIC_ENTITY_TYPE,
                    SourceTag.tag_value == pet
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.PUBLIC_ENTITY_TYPE, pet, 0.6))

        for dept in result.get("departments", []):
            if dept in STARTER_DEPARTMENT_TAGS:
                existing = db.query(SourceTag).filter(
                    SourceTag.source_id == source.id,
                    SourceTag.tag_type == TagType.DEPARTMENT,
                    SourceTag.tag_value == dept
                ).first()
                if not existing:
                    tags.append(_create_tag(db, source.id, TagType.DEPARTMENT, dept, 0.6))

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
