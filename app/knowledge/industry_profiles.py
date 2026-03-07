"""Industry Knowledge Objects — structured risk intelligence per industry.

Powers risk intelligence, meeting briefs, coverage gap detection, and
discovery question generation. Each IndustryProfile captures the canonical
knowledge a commercial producer needs for a given industry vertical.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class IndustryProfile:
    """Structured risk intelligence for a single industry vertical."""

    industry: str
    naics: str
    jurisdiction: str
    top_exposures: list[str] = field(default_factory=list)
    common_claims: list[str] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    recommended_talking_points: list[str] = field(default_factory=list)
    discovery_questions: list[str] = field(default_factory=list)
    policy_lines: list[str] = field(default_factory=list)
    risk_score_factors: dict[str, str] = field(default_factory=dict)
    data_sources: list[str] = field(default_factory=list)
    source_version: str = "2026-03"
    last_updated: str = "2026-03-07"
    confidence: float = 0.80
    office_learnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize profile to a JSON-compatible dictionary."""
        return asdict(self)


# ============================================================
# IN-MEMORY REGISTRY
# ============================================================

INDUSTRY_PROFILES: dict[str, IndustryProfile] = {}


def get_industry_profile(industry: str) -> Optional[IndustryProfile]:
    """Look up an industry profile by normalized key.

    Tries exact match first, then lowercased/stripped match.
    Returns None if not found.
    """
    key = industry.lower().strip()
    if key in INDUSTRY_PROFILES:
        return INDUSTRY_PROFILES[key]
    # Try without trailing "contractor" or "shop" for flexibility
    for suffix in [" contractor", " shop", " store", " owner", " company"]:
        alt = key + suffix
        if alt in INDUSTRY_PROFILES:
            return INDUSTRY_PROFILES[alt]
    return None


def list_industries() -> list[str]:
    """Return sorted list of all registered industry keys."""
    return sorted(INDUSTRY_PROFILES.keys())


def add_office_learning(industry: str, note: str) -> bool:
    """Append a local office learning to an industry profile.

    Returns True if the note was added, False if the industry was not found.
    """
    profile = get_industry_profile(industry)
    if profile is None:
        return False
    profile.office_learnings.append(note)
    logger.info("Office learning added to %s: %s", industry, note[:80])
    return True


# ============================================================
# SEED DATA
# ============================================================

_SEED_PROFILES = [
    IndustryProfile(
        industry="roofing contractor",
        naics="238160",
        jurisdiction="NC",
        top_exposures=[
            "fall from height",
            "fleet auto losses",
            "tool/equipment theft",
            "subcontractor certificate issues",
        ],
        common_claims=[
            "workers comp fall injuries",
            "auto accidents involving work trucks",
            "tools stolen from job sites",
            "property damage from dropped materials",
        ],
        coverage_gaps=[
            "uninsured subcontractors",
            "hired and non-owned auto",
            "inland marine for tools",
            "insufficient workers comp classification",
        ],
        recommended_talking_points=[
            "ask about ladder and harness policy",
            "ask about vehicle count and MVR review",
            "ask where tools are stored overnight",
            "ask how subs are classified and tracked",
        ],
        discovery_questions=[
            "How many crews operate simultaneously?",
            "Do you subcontract roofing work?",
            "Where are vehicles garaged overnight?",
            "Are employees trained on fall protection?",
        ],
        policy_lines=[
            "workers compensation",
            "commercial auto",
            "general liability",
            "inland marine",
            "umbrella",
        ],
        risk_score_factors={
            "subcontractor_usage": "high impact",
            "fleet_size": "medium impact",
            "safety_program": "high impact",
            "years_in_business": "medium impact",
        },
        data_sources=[
            "OSHA roofing fall statistics",
            "workers comp claim trends",
            "industry loss reports",
        ],
        confidence=0.88,
    ),
    IndustryProfile(
        industry="landscaping contractor",
        naics="561730",
        jurisdiction="TX",
        top_exposures=[
            "equipment-related injuries",
            "chemical application liability",
            "vehicle accidents",
            "seasonal worker management",
        ],
        common_claims=[
            "mower/trimmer injuries",
            "herbicide/pesticide overspray damage",
            "auto accidents with trailers",
            "heat-related illness",
        ],
        coverage_gaps=[
            "inland marine for equipment on trailers",
            "pollution liability for chemical application",
            "employment practices liability",
            "hired and non-owned auto",
        ],
        recommended_talking_points=[
            "ask about chemical application licenses",
            "ask about equipment value on trailers",
            "ask about seasonal hiring practices",
            "ask about heat illness prevention program",
        ],
        discovery_questions=[
            "Do you apply herbicides or pesticides?",
            "What is the total value of equipment on trailers?",
            "How many seasonal employees do you hire?",
            "Do you perform tree removal or hardscaping?",
        ],
        policy_lines=[
            "workers compensation",
            "commercial auto",
            "general liability",
            "inland marine",
            "pollution liability",
            "umbrella",
        ],
        risk_score_factors={
            "chemical_application": "high impact",
            "fleet_size": "medium impact",
            "seasonal_workforce": "medium impact",
            "equipment_value": "medium impact",
        },
        data_sources=[
            "landscape industry safety reports",
            "EPA pesticide applicator data",
            "workers comp claim trends",
        ],
        confidence=0.85,
    ),
    IndustryProfile(
        industry="hvac contractor",
        naics="238220",
        jurisdiction="FL",
        top_exposures=[
            "refrigerant handling liability",
            "rooftop unit installation falls",
            "vehicle fleet accidents",
            "electrical hazards",
        ],
        common_claims=[
            "technician falls from roofs or ladders",
            "vehicle accidents between service calls",
            "refrigerant leak property damage",
            "faulty installation callbacks",
        ],
        coverage_gaps=[
            "pollution liability for refrigerant releases",
            "cyber liability for smart thermostat data",
            "professional liability for design work",
            "umbrella for excess exposure",
        ],
        recommended_talking_points=[
            "ask about EPA Section 608 certification compliance",
            "ask about rooftop unit installation procedures",
            "ask about service call volume and fleet management",
            "ask about smart/connected system installations",
        ],
        discovery_questions=[
            "Do technicians install rooftop units?",
            "How many service vehicles do you operate?",
            "Do you handle refrigerants? Which types?",
            "Do you install smart thermostats or IoT systems?",
        ],
        policy_lines=[
            "workers compensation",
            "commercial auto",
            "general liability",
            "inland marine",
            "professional liability",
            "pollution liability",
            "cyber liability",
            "umbrella",
        ],
        risk_score_factors={
            "refrigerant_handling": "high impact",
            "rooftop_work": "high impact",
            "fleet_size": "medium impact",
            "smart_system_installs": "low impact",
        },
        data_sources=[
            "EPA refrigerant management data",
            "HVAC industry loss reports",
            "OSHA fall protection statistics",
        ],
        confidence=0.86,
    ),
    IndustryProfile(
        industry="electrical contractor",
        naics="238210",
        jurisdiction="GA",
        top_exposures=[
            "electrocution and arc flash",
            "fire from faulty wiring",
            "falls from ladders and scaffolding",
            "property damage during renovation",
        ],
        common_claims=[
            "electrical burn injuries",
            "fire caused by installation error",
            "falls during overhead work",
            "damage to existing structures during wiring",
        ],
        coverage_gaps=[
            "professional liability for design-build",
            "completed operations coverage",
            "hired and non-owned auto",
            "umbrella for catastrophic fire loss",
        ],
        recommended_talking_points=[
            "ask about arc flash training and PPE",
            "ask about residential vs commercial mix",
            "ask about design-build or engineering work",
            "ask about permit and inspection failure rates",
        ],
        discovery_questions=[
            "What percentage is residential vs commercial?",
            "Do you perform design-build electrical work?",
            "What arc flash safety training is provided?",
            "Do you work on solar panel installations?",
        ],
        policy_lines=[
            "workers compensation",
            "commercial auto",
            "general liability",
            "professional liability",
            "inland marine",
            "umbrella",
        ],
        risk_score_factors={
            "work_voltage_levels": "high impact",
            "design_build_work": "high impact",
            "safety_training": "high impact",
            "solar_work": "medium impact",
        },
        data_sources=[
            "OSHA electrical safety statistics",
            "NFPA fire investigation reports",
            "electrical contractor loss data",
        ],
        confidence=0.87,
    ),
    IndustryProfile(
        industry="plumber",
        naics="238220",
        jurisdiction="OH",
        top_exposures=[
            "water damage from faulty installations",
            "confined space entry hazards",
            "vehicle accidents between job sites",
            "back injuries from heavy lifting",
        ],
        common_claims=[
            "water damage claims from burst pipes or bad joints",
            "slip and fall at customer premises",
            "vehicle accidents",
            "back and shoulder injuries",
        ],
        coverage_gaps=[
            "professional liability for design errors",
            "completed operations for latent defects",
            "inland marine for specialty tools",
            "pollution liability for sewer/drain work",
        ],
        recommended_talking_points=[
            "ask about water damage callback frequency",
            "ask about sewer and drain cleaning operations",
            "ask about new construction vs service/repair mix",
            "ask about confined space entry protocols",
        ],
        discovery_questions=[
            "Do you perform sewer line work or trenchless repair?",
            "What is your mix of new construction vs service calls?",
            "Do you carry specialty tools in service vehicles?",
            "Have you had water damage callbacks in the past 3 years?",
        ],
        policy_lines=[
            "workers compensation",
            "commercial auto",
            "general liability",
            "professional liability",
            "inland marine",
            "umbrella",
        ],
        risk_score_factors={
            "water_damage_history": "high impact",
            "sewer_work": "medium impact",
            "fleet_size": "medium impact",
            "new_construction_ratio": "medium impact",
        },
        data_sources=[
            "plumbing industry loss reports",
            "workers comp claim data",
            "water damage claim studies",
        ],
        confidence=0.84,
    ),
    IndustryProfile(
        industry="restaurant",
        naics="722511",
        jurisdiction="CA",
        top_exposures=[
            "slip-and-fall injuries (employees and patrons)",
            "foodborne illness liability",
            "kitchen fire",
            "liquor liability",
        ],
        common_claims=[
            "employee slip and fall in kitchen",
            "customer food poisoning claims",
            "grease fire damage",
            "dram shop / over-service claims",
        ],
        coverage_gaps=[
            "employment practices liability",
            "cyber liability for POS/payment data",
            "commercial auto for delivery/catering",
            "umbrella for liquor liability excess",
        ],
        recommended_talking_points=[
            "ask about delivery and catering operations",
            "ask about liquor service and training",
            "ask about kitchen suppression system maintenance",
            "ask about employee turnover and HR practices",
        ],
        discovery_questions=[
            "Do you offer delivery or catering services?",
            "What percentage of revenue is from alcohol sales?",
            "How often is the kitchen suppression system inspected?",
            "What is your annual employee turnover rate?",
        ],
        policy_lines=[
            "workers compensation",
            "general liability",
            "commercial property",
            "liquor liability",
            "employment practices liability",
            "cyber liability",
            "commercial auto",
            "umbrella",
        ],
        risk_score_factors={
            "liquor_revenue_percentage": "high impact",
            "delivery_operations": "medium impact",
            "employee_turnover": "medium impact",
            "fire_suppression_maintenance": "high impact",
        },
        data_sources=[
            "restaurant industry loss reports",
            "foodborne illness CDC data",
            "dram shop liability studies",
        ],
        confidence=0.87,
    ),
    IndustryProfile(
        industry="bar/tavern",
        naics="722410",
        jurisdiction="NY",
        top_exposures=[
            "liquor liability / over-service",
            "assault and battery on premises",
            "slip-and-fall injuries",
            "noise complaints and nuisance claims",
        ],
        common_claims=[
            "dram shop liability from intoxicated patron",
            "patron-on-patron assault",
            "slip and fall on wet floors",
            "bouncer/security use of force",
        ],
        coverage_gaps=[
            "assault and battery coverage",
            "employment practices liability",
            "cyber liability for payment systems",
            "umbrella for catastrophic liquor claims",
        ],
        recommended_talking_points=[
            "ask about bouncer/security staffing and training",
            "ask about TIPS or responsible beverage service training",
            "ask about late-night operating hours",
            "ask about live entertainment or events",
        ],
        discovery_questions=[
            "What are your operating hours?",
            "Do you employ security or bouncers?",
            "Are bartenders TIPS certified?",
            "Do you host live entertainment or DJ nights?",
        ],
        policy_lines=[
            "general liability",
            "liquor liability",
            "assault and battery",
            "workers compensation",
            "commercial property",
            "employment practices liability",
            "umbrella",
        ],
        risk_score_factors={
            "late_night_hours": "high impact",
            "security_staffing": "high impact",
            "entertainment_events": "medium impact",
            "beverage_training": "high impact",
        },
        data_sources=[
            "dram shop liability case data",
            "nightlife industry loss reports",
            "assault and battery claim studies",
        ],
        confidence=0.85,
    ),
    IndustryProfile(
        industry="auto repair shop",
        naics="811111",
        jurisdiction="MI",
        top_exposures=[
            "garage liability (customer vehicle damage)",
            "environmental contamination",
            "employee injuries from lifts and tools",
            "fire from flammable materials",
        ],
        common_claims=[
            "damage to customer vehicle during repair",
            "oil/fluid spill environmental cleanup",
            "employee crush injury from lift failure",
            "fire originating in paint booth or storage",
        ],
        coverage_gaps=[
            "garagekeepers liability",
            "pollution liability for fluid disposal",
            "inland marine for diagnostic equipment",
            "cyber liability for customer data",
        ],
        recommended_talking_points=[
            "ask about garagekeepers coverage limits",
            "ask about fluid storage and disposal practices",
            "ask about lift inspection and maintenance schedule",
            "ask about paint booth or body work operations",
        ],
        discovery_questions=[
            "How many customer vehicles are on premises at any time?",
            "Do you perform body work or painting?",
            "How are waste fluids stored and disposed?",
            "When were lifts last inspected?",
        ],
        policy_lines=[
            "garage liability",
            "garagekeepers liability",
            "workers compensation",
            "commercial property",
            "pollution liability",
            "inland marine",
            "umbrella",
        ],
        risk_score_factors={
            "vehicles_on_premises": "high impact",
            "body_paint_work": "high impact",
            "fluid_disposal": "medium impact",
            "lift_maintenance": "medium impact",
        },
        data_sources=[
            "auto repair industry loss data",
            "EPA auto shop compliance reports",
            "garagekeepers claim studies",
        ],
        confidence=0.86,
    ),
    IndustryProfile(
        industry="retail store",
        naics="452210",
        jurisdiction="PA",
        top_exposures=[
            "slip-and-fall (customer and employee)",
            "product liability",
            "theft and shoplifting",
            "employment practices",
        ],
        common_claims=[
            "customer slip and fall on wet floor",
            "product liability from sold goods",
            "employee theft or shoplifting losses",
            "wrongful termination or discrimination",
        ],
        coverage_gaps=[
            "employment practices liability",
            "cyber liability for payment card data",
            "product recall coverage",
            "business income / interruption",
        ],
        recommended_talking_points=[
            "ask about PCI compliance for card processing",
            "ask about product sourcing and import risk",
            "ask about seasonal hiring practices",
            "ask about slip-and-fall prevention programs",
        ],
        discovery_questions=[
            "Do you sell products manufactured by others?",
            "How do you process credit card payments?",
            "Do you hire seasonal employees?",
            "What is your annual shrinkage/theft rate?",
        ],
        policy_lines=[
            "general liability",
            "commercial property",
            "workers compensation",
            "employment practices liability",
            "cyber liability",
            "business income",
            "crime/fidelity",
            "umbrella",
        ],
        risk_score_factors={
            "foot_traffic_volume": "medium impact",
            "product_sourcing": "medium impact",
            "pci_compliance": "high impact",
            "employee_count": "medium impact",
        },
        data_sources=[
            "retail industry loss reports",
            "NRF shrinkage survey",
            "slip and fall claim studies",
        ],
        confidence=0.83,
    ),
    IndustryProfile(
        industry="daycare",
        naics="624410",
        jurisdiction="IL",
        top_exposures=[
            "child injury on premises",
            "abuse and molestation allegations",
            "transportation liability",
            "communicable disease outbreaks",
        ],
        common_claims=[
            "child injury during activities",
            "abuse/molestation allegations",
            "vehicle accident during transport",
            "allergic reaction to food served",
        ],
        coverage_gaps=[
            "abuse and molestation coverage",
            "professional liability for childcare",
            "hired and non-owned auto for field trips",
            "cyber liability for parent/child records",
        ],
        recommended_talking_points=[
            "ask about staff background check procedures",
            "ask about child-to-staff ratios",
            "ask about field trip transportation",
            "ask about allergy management protocols",
        ],
        discovery_questions=[
            "What is your licensed child capacity?",
            "Do you transport children for field trips?",
            "What background check process is used for staff?",
            "How are food allergies managed?",
        ],
        policy_lines=[
            "general liability",
            "professional liability",
            "abuse and molestation",
            "workers compensation",
            "commercial property",
            "commercial auto",
            "umbrella",
        ],
        risk_score_factors={
            "child_capacity": "high impact",
            "transportation": "high impact",
            "staff_screening": "high impact",
            "licensing_compliance": "high impact",
        },
        data_sources=[
            "childcare licensing data",
            "child injury statistics",
            "abuse and molestation claim studies",
        ],
        confidence=0.89,
    ),
    IndustryProfile(
        industry="apartment owner",
        naics="531110",
        jurisdiction="FL",
        top_exposures=[
            "premises liability (slip and fall)",
            "fire and water damage",
            "tenant discrimination claims",
            "swimming pool drowning",
        ],
        common_claims=[
            "tenant or visitor slip and fall",
            "fire damage from tenant negligence",
            "fair housing discrimination complaint",
            "pool or playground injury",
        ],
        coverage_gaps=[
            "employment practices liability for property staff",
            "flood insurance in coastal areas",
            "umbrella for premises liability excess",
            "ordinance or law coverage for older buildings",
        ],
        recommended_talking_points=[
            "ask about swimming pool fencing and rules",
            "ask about building age and code compliance",
            "ask about tenant screening procedures",
            "ask about maintenance staff or third-party management",
        ],
        discovery_questions=[
            "How many units are in the property?",
            "Is there a swimming pool or playground?",
            "What year were the buildings constructed?",
            "Do you self-manage or use a property management company?",
        ],
        policy_lines=[
            "commercial property",
            "general liability",
            "umbrella",
            "flood insurance",
            "ordinance or law",
            "employment practices liability",
            "workers compensation",
        ],
        risk_score_factors={
            "unit_count": "medium impact",
            "building_age": "high impact",
            "swimming_pool": "high impact",
            "coastal_location": "high impact",
        },
        data_sources=[
            "apartment industry loss data",
            "fair housing complaint statistics",
            "premises liability claim studies",
        ],
        confidence=0.85,
    ),
    IndustryProfile(
        industry="trucking company",
        naics="484110",
        jurisdiction="TX",
        top_exposures=[
            "catastrophic auto accidents",
            "cargo damage or loss",
            "driver fatigue and HOS violations",
            "environmental spills during transport",
        ],
        common_claims=[
            "multi-vehicle highway accidents",
            "cargo damage claims from shippers",
            "driver injury from loading/unloading",
            "fuel or cargo spill environmental cleanup",
        ],
        coverage_gaps=[
            "motor truck cargo coverage",
            "pollution liability for hazmat loads",
            "cyber liability for ELD/fleet systems",
            "non-trucking liability for owner-operators",
        ],
        recommended_talking_points=[
            "ask about driver qualification file compliance",
            "ask about types of cargo hauled",
            "ask about owner-operator vs company driver mix",
            "ask about ELD system and telematics usage",
        ],
        discovery_questions=[
            "What types of cargo do you haul?",
            "How many power units are in the fleet?",
            "Do you use owner-operators or only company drivers?",
            "What is your DOT safety rating?",
        ],
        policy_lines=[
            "commercial auto",
            "motor truck cargo",
            "general liability",
            "workers compensation",
            "physical damage",
            "pollution liability",
            "umbrella / excess",
        ],
        risk_score_factors={
            "fleet_size": "high impact",
            "cargo_type": "high impact",
            "driver_turnover": "high impact",
            "safety_rating": "high impact",
        },
        data_sources=[
            "FMCSA crash statistics",
            "trucking industry loss reports",
            "DOT compliance data",
        ],
        confidence=0.90,
    ),
]


def _load_seed_profiles() -> None:
    """Populate INDUSTRY_PROFILES from seed data."""
    for profile in _SEED_PROFILES:
        key = profile.industry.lower().strip()
        INDUSTRY_PROFILES[key] = profile
    logger.info("Loaded %d industry profiles", len(INDUSTRY_PROFILES))


# Load on module import
_load_seed_profiles()
