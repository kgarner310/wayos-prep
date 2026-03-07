"""Coverage Gap Detector — deterministic producer reasoning layer.

Analyzes account inputs (industry, state, mod, employee count, traits, themes)
and returns structured coverage gaps with severity, reasoning, and suggested actions.

NOT carrier-accurate quoting logic. This is a producer preparation tool.
"""

import logging

from app.services.industry_loader import resolve, get_enrichment

logger = logging.getLogger(__name__)


# ============================================================
# INDUSTRY → EXPECTED COVERAGE MAP
# ============================================================
# What coverages a well-rounded account in this industry typically carries.

INDUSTRY_EXPECTED_COVERAGES = {
    "roofing": [
        "workers_comp", "general_liability", "commercial_auto", "umbrella",
        "inland_marine", "builders_risk", "property",
    ],
    "trucking": [
        "workers_comp", "general_liability", "commercial_auto", "umbrella",
        "cargo", "property",
    ],
    "manufacturing": [
        "workers_comp", "general_liability", "commercial_auto", "umbrella",
        "property", "inland_marine", "cyber",
    ],
    "restaurant": [
        "workers_comp", "general_liability", "commercial_auto", "property",
        "umbrella", "epli",
    ],
    "landscaping": [
        "workers_comp", "general_liability", "commercial_auto", "umbrella",
        "inland_marine",
    ],
    "hvac": [
        "workers_comp", "general_liability", "commercial_auto", "umbrella",
        "inland_marine", "professional_liability",
    ],
}

# State-level property/cat exposure flags
HIGH_WIND_STATES = {"FL", "TX", "LA", "SC", "NC", "AL", "MS", "GA"}
EARTHQUAKE_STATES = {"CA", "WA", "OR", "AK", "MO"}
FLOOD_RISK_STATES = {"FL", "TX", "LA", "NC", "SC", "MS", "AL"}

# Industry → typical risk themes that drive gap logic
INDUSTRY_GL_HEAVY = {"roofing", "landscaping", "hvac", "manufacturing"}
INDUSTRY_FLEET_HEAVY = {"trucking", "landscaping", "hvac", "roofing"}
INDUSTRY_PROPERTY_HEAVY = {"manufacturing", "restaurant"}


def detect_gaps(
    industry: str,
    state: str,
    employee_count: int = 10,
    current_mod: float | None = None,
    entity_type: str = "private_business",
    department: str | None = None,
    account_traits: list[str] | None = None,
    active_risk_themes: set[str] | None = None,
    known_coverages: list[str] | None = None,
) -> list[dict]:
    """Run deterministic coverage gap detection.

    Returns list of gap dicts with: title, severity, reason, why_now,
    suggested_question, suggested_coverage_or_action, evidence_source.
    """
    account_traits = account_traits or []
    active_risk_themes = active_risk_themes or set()
    known_coverages = set(c.lower() for c in (known_coverages or []))
    industry_lower = industry.lower()
    state_upper = state.upper()
    gaps = []

    # --- Fleet / Auto Gaps ---
    fleet_themes = {"fleet_accidents", "fleet_liability", "hired_non_owned_auto", "driver_turnover"}
    has_fleet_exposure = (
        industry_lower in INDUSTRY_FLEET_HEAVY
        or bool(fleet_themes & active_risk_themes)
        or "young_fleet" in account_traits
        or "delivery_operations" in account_traits
    )

    if has_fleet_exposure and "commercial_auto" not in known_coverages:
        gaps.append({
            "title": "Commercial Auto Coverage Gap",
            "severity": "high",
            "reason": f"Fleet/vehicle exposure detected for {industry} operations but no commercial auto coverage confirmed.",
            "why_now": "Auto liability claims are rising nationally. Uninsured fleet exposure is a top E&O risk for producers.",
            "suggested_question": "Walk me through your fleet — how many vehicles, who drives, and what are your take-home policies?",
            "suggested_coverage_or_action": "Confirm commercial auto limits, hired/non-owned auto, and driver eligibility controls.",
            "evidence_source": "industry",
        })

    if has_fleet_exposure and "umbrella" not in known_coverages:
        gaps.append({
            "title": "Umbrella / Excess Over Auto",
            "severity": "medium",
            "reason": "Fleet operations create excess liability exposure beyond primary auto limits.",
            "why_now": "Nuclear verdicts in commercial auto continue to exceed primary limits. Umbrella is the baseline protection.",
            "suggested_question": "What are your current umbrella limits, and does it schedule commercial auto?",
            "suggested_coverage_or_action": "Review umbrella adequacy and confirm auto is scheduled.",
            "evidence_source": "industry",
        })

    if has_fleet_exposure and "hired_non_owned_auto" not in known_coverages:
        gaps.append({
            "title": "Hired & Non-Owned Auto Exposure",
            "severity": "medium",
            "reason": "Employees may use personal vehicles for work errands, creating uninsured auto liability.",
            "why_now": "Personal vehicle use for business continues to grow. HNOA fills the gap when employees drive their own cars.",
            "suggested_question": "Do any employees use personal vehicles for company business — deliveries, errands, site visits?",
            "suggested_coverage_or_action": "Add hired and non-owned auto coverage to the commercial auto policy.",
            "evidence_source": "account_input",
        })

    # --- Mod-Driven Gaps ---
    if current_mod is not None and current_mod > 1.0:
        severity = "high" if current_mod > 1.20 else "medium"
        gaps.append({
            "title": "Experience Mod Trending Unfavorably",
            "severity": severity,
            "reason": f"Current mod of {current_mod:.3f} is above unity — indicating loss history worse than expected for this class.",
            "why_now": "A rising mod increases premium and may limit carrier appetite. Addressing root causes now affects 3 years of mod calculations.",
            "suggested_question": "Your mod is moving the wrong direction. What changed operationally in the last 12 months?",
            "suggested_coverage_or_action": "Review loss control program, return-to-work protocols, and consider large deductible or retrospective rating.",
            "evidence_source": "mod",
        })

    if current_mod is not None and current_mod > 1.15:
        gaps.append({
            "title": "Deductible Program Review",
            "severity": "medium",
            "reason": f"With a {current_mod:.3f} mod, premium is elevated. A deductible program could reduce net cost while incentivizing loss control.",
            "why_now": "High-mod accounts benefit most from deductible programs because the premium savings compound against the elevated mod.",
            "suggested_question": "Have you explored a deductible or retro program to manage your WC cost?",
            "suggested_coverage_or_action": "Model deductible options ($1K–$5K per claim) against current loss frequency.",
            "evidence_source": "mod",
        })

    # --- GL / Subcontractor Gaps ---
    has_sub_exposure = (
        "uses_subcontractors" in account_traits
        or "subcontractor_transfer" in active_risk_themes
        or "certificate_tracking" in active_risk_themes
    )

    if has_sub_exposure:
        gaps.append({
            "title": "Subcontractor Risk Transfer Gap",
            "severity": "high",
            "reason": "Subcontractor usage detected but no confirmed certificate compliance or additional insured requirements.",
            "why_now": "Subcontractor claims are among the most expensive GL losses. Upstream liability flows to the GC without proper transfer.",
            "suggested_question": "Show me how you verify AI/Waiver/COI compliance before subs start work on a job.",
            "suggested_coverage_or_action": "Implement mandatory COI collection with AI/WOS endorsements. Review contractual hold-harmless language.",
            "evidence_source": "account_input",
        })

    if industry_lower in INDUSTRY_GL_HEAVY and "general_liability" not in known_coverages:
        gaps.append({
            "title": "General Liability Adequacy",
            "severity": "high",
            "reason": f"{industry.title()} operations carry significant GL exposure from completed operations, premises, and products.",
            "why_now": "Carriers are tightening GL terms for high-hazard classes. Confirm limits and exclusions before renewal.",
            "suggested_question": "When was the last time your GL limits were reviewed relative to your revenue and contract requirements?",
            "suggested_coverage_or_action": "Review GL limits, completed operations coverage, and contractual requirements.",
            "evidence_source": "industry",
        })

    # --- Property / Catastrophe Gaps ---
    if state_upper in HIGH_WIND_STATES:
        gaps.append({
            "title": "Wind / Named Storm Exposure",
            "severity": "medium",
            "reason": f"{state_upper} is a high-wind state. Property policies may carry separate named-storm deductibles or wind exclusions.",
            "why_now": "Coastal and wind-exposed property rates are hardening. Producers need to discuss deductible levels and coverage certainty.",
            "suggested_question": "What is your current named-storm deductible, and have you stress-tested a wind loss against your balance sheet?",
            "suggested_coverage_or_action": "Review named-storm deductible percentage, business income waiting periods, and excess property options.",
            "evidence_source": "state",
        })

    if state_upper in FLOOD_RISK_STATES and industry_lower in INDUSTRY_PROPERTY_HEAVY:
        gaps.append({
            "title": "Flood Coverage Review",
            "severity": "medium",
            "reason": f"Property-intensive {industry} operations in {state_upper} face flood exposure that standard property policies typically exclude.",
            "why_now": "FEMA flood maps are being updated and private flood markets have expanded. Now is a good time to review options.",
            "suggested_question": "Is your property in a flood zone, and do you carry separate flood coverage?",
            "suggested_coverage_or_action": "Evaluate NFIP vs. private flood options. Confirm business personal property is covered.",
            "evidence_source": "state",
        })

    if state_upper in EARTHQUAKE_STATES:
        gaps.append({
            "title": "Earthquake Exposure",
            "severity": "low",
            "reason": f"{state_upper} has earthquake exposure. Standard property policies exclude earthquake damage.",
            "why_now": "Many businesses are unaware of the earthquake exclusion until after a loss.",
            "suggested_question": "Do you carry earthquake coverage, and have you reviewed your building's seismic vulnerability?",
            "suggested_coverage_or_action": "Quote standalone earthquake coverage or DIC policy.",
            "evidence_source": "state",
        })

    # --- Business Income Gap ---
    if industry_lower in INDUSTRY_PROPERTY_HEAVY or employee_count > 50:
        gaps.append({
            "title": "Business Income / Extra Expense Review",
            "severity": "medium",
            "reason": "Operations of this size depend on continuity. A major property or equipment loss could halt revenue for weeks.",
            "why_now": "Supply chain delays have lengthened restoration periods. Many BI limits are set years ago and may be inadequate.",
            "suggested_question": "If a large property loss hit this location, how long could you operate before business income becomes painful?",
            "suggested_coverage_or_action": "Recalculate business income needs based on current revenue. Review waiting period and extended period of indemnity.",
            "evidence_source": "industry",
        })

    # --- Employee-Count-Driven Gaps ---
    if employee_count >= 50 and "epli" not in known_coverages:
        gaps.append({
            "title": "Employment Practices Liability (EPLI)",
            "severity": "medium",
            "reason": f"With {employee_count} employees, employment practices claims (discrimination, harassment, wrongful termination) become statistically likely.",
            "why_now": "EEOC filings have increased. Companies above 50 employees face federal reporting requirements and higher litigation risk.",
            "suggested_question": "Do you have an employee handbook, and when was it last reviewed by employment counsel?",
            "suggested_coverage_or_action": "Quote EPLI coverage. Review HR practices and handbook adequacy.",
            "evidence_source": "account_input",
        })

    if employee_count >= 25 and "cyber" not in known_coverages:
        gaps.append({
            "title": "Cyber Liability Exposure",
            "severity": "low" if employee_count < 50 else "medium",
            "reason": f"A {employee_count}-employee operation stores employee PII (SSNs, bank info) and likely processes customer data electronically.",
            "why_now": "Ransomware attacks increasingly target mid-market businesses. The average breach cost continues to climb.",
            "suggested_question": "How do you handle employee and customer data? Do you have a breach response plan?",
            "suggested_coverage_or_action": "Quote cyber liability with breach response, business interruption, and ransomware coverage.",
            "evidence_source": "account_input",
        })

    # --- Public Entity Gaps ---
    if entity_type == "public_entity":
        if department == "law_enforcement" and "law_enforcement_liability" not in known_coverages:
            gaps.append({
                "title": "Law Enforcement Liability Coverage",
                "severity": "high",
                "reason": "Law enforcement operations carry significant civil rights and excessive force exposure.",
                "why_now": "Section 1983 claims and excessive force verdicts are escalating nationally. Coverage adequacy is critical.",
                "suggested_question": "What are your current law enforcement liability limits, and do you have a use-of-force policy review schedule?",
                "suggested_coverage_or_action": "Review LE liability limits, retention levels, and coverage for individual officer defense.",
                "evidence_source": "industry",
            })

        if "public_officials_liability" not in known_coverages:
            gaps.append({
                "title": "Public Officials Liability",
                "severity": "medium",
                "reason": "Elected and appointed officials face personal liability for decisions made in their official capacity.",
                "why_now": "Land-use decisions, employment actions, and policy changes all create D&O-style exposure for public entities.",
                "suggested_question": "Do your elected officials and department heads have adequate D&O / public officials coverage?",
                "suggested_coverage_or_action": "Confirm public officials liability with adequate limits and defense cost coverage.",
                "evidence_source": "industry",
            })

    # --- Industry-Specific Gaps ---
    if industry_lower == "roofing" and "inland_marine" not in known_coverages:
        gaps.append({
            "title": "Inland Marine / Tools & Equipment",
            "severity": "medium",
            "reason": "Roofing operations move expensive tools and materials between job sites. Standard property may not cover mobile equipment.",
            "why_now": "Tool theft from job sites is a growing problem. Contractors' equipment floaters fill this gap.",
            "suggested_question": "What is the total value of tools and equipment you move between job sites?",
            "suggested_coverage_or_action": "Quote contractors equipment floater / inland marine for mobile tools and materials.",
            "evidence_source": "industry",
        })

    if industry_lower == "roofing" and "builders_risk" not in known_coverages:
        gaps.append({
            "title": "Builders Risk for Active Projects",
            "severity": "low",
            "reason": "Roofing projects in progress may not be covered under the property owner's policy until completion.",
            "why_now": "A storm or fire during an active re-roof can create disputes about who carries the risk.",
            "suggested_question": "Do your contracts specify who carries builders risk during the project?",
            "suggested_coverage_or_action": "Review builders risk requirements in your standard contract. Consider project-specific or annual builders risk.",
            "evidence_source": "industry",
        })

    if industry_lower == "manufacturing" and "workers_comp" in known_coverages:
        if "machine_guarding" in active_risk_themes or "struck_by_object" in active_risk_themes:
            gaps.append({
                "title": "Safety Program Adequacy",
                "severity": "medium",
                "reason": "Machine guarding and struck-by hazards are active risk themes — safety program maturity directly impacts loss frequency.",
                "why_now": "OSHA is increasing penalties for machine guarding violations. A documented safety program reduces both claims and citations.",
                "suggested_question": "Walk me through your lockout/tagout and machine guarding program. When was the last safety audit?",
                "suggested_coverage_or_action": "Request loss control visit. Review LOTO compliance and machine guarding inventory.",
                "evidence_source": "industry",
            })

    # Sort by severity, limit to 10
    severity_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: severity_order.get(g["severity"], 3))
    return gaps[:10]


# ============================================================
# COVERAGE GAP INSIGHT ENGINE
# ============================================================
# Standalone function accepting an account profile dict and
# returning structured coverage gaps + suggested producer questions.

# Normalize common industry name variants to canonical keys
_INDUSTRY_ALIASES = {
    "roofing contractor": "roofing",
    "roofing contractors": "roofing",
    "roofer": "roofing",
    "truck": "trucking",
    "trucking company": "trucking",
    "mfg": "manufacturing",
    "manufacturer": "manufacturing",
    "food service": "restaurant",
    "restaurants": "restaurant",
    "lawn care": "landscaping",
    "landscape": "landscaping",
    "heating and cooling": "hvac",
    "hvac contractor": "hvac",
}


def _normalize_industry(raw: str) -> str:
    """Map common industry aliases to canonical INDUSTRY_EXPECTED_COVERAGES keys."""
    key = raw.strip().lower()
    return _INDUSTRY_ALIASES.get(key, key)


# Coverage display names for human-readable output
_COVERAGE_DISPLAY = {
    "workers_comp": "Workers' Compensation",
    "general_liability": "General Liability",
    "commercial_auto": "Commercial Auto",
    "umbrella": "Umbrella / Excess Liability",
    "inland_marine": "Inland Marine / Equipment Floater",
    "builders_risk": "Builders Risk",
    "property": "Commercial Property",
    "cargo": "Motor Truck Cargo",
    "cyber": "Cyber Liability",
    "epli": "Employment Practices Liability (EPLI)",
    "professional_liability": "Professional Liability / E&O",
    "hired_non_owned_auto": "Hired and Non-Owned Auto",
}

# Reasons why each coverage is important, keyed by coverage slug
_COVERAGE_REASONS = {
    "workers_comp": "State-mandated coverage for employee injuries; missing it exposes the employer to personal liability and penalties",
    "general_liability": "Covers third-party bodily injury and property damage claims arising from operations",
    "commercial_auto": "Required when company-owned or leased vehicles are used; personal auto policies exclude business use",
    "umbrella": "Provides excess limits above primary GL, auto, and employer's liability to protect against catastrophic verdicts",
    "inland_marine": "Covers tools, equipment, and materials in transit or at job sites — standard property often excludes mobile assets",
    "builders_risk": "Protects structures under construction or renovation from damage before project completion",
    "property": "Covers owned or leased buildings, contents, and business personal property against covered perils",
    "cargo": "Covers goods in transit; motor carriers face liability for freight damage",
    "cyber": "Covers data breach response, ransomware, and business interruption from cyber events",
    "epli": "Covers employment-related claims including discrimination, harassment, and wrongful termination",
    "professional_liability": "Covers errors, omissions, and faulty workmanship claims in professional services",
    "hired_non_owned_auto": "Employees may use personal vehicles for job activities",
}

# Risk levels for missing coverages based on how critical they typically are
_COVERAGE_RISK_LEVELS = {
    "workers_comp": "high",
    "general_liability": "high",
    "commercial_auto": "high",
    "umbrella": "medium",
    "inland_marine": "medium",
    "builders_risk": "low",
    "property": "medium",
    "cargo": "high",
    "cyber": "low",
    "epli": "medium",
    "professional_liability": "medium",
    "hired_non_owned_auto": "medium",
}

# Contextual questions organized by coverage and account attribute
_SUGGESTED_QUESTIONS_BY_COVERAGE = {
    "workers_comp": "What is your current experience modification rate, and how do you manage return-to-work?",
    "general_liability": "What types of contracts do you sign, and do they require specific GL limits or AI endorsements?",
    "commercial_auto": "How many vehicles are in your fleet, and who is authorized to drive them?",
    "umbrella": "What are your current underlying limits, and have you reviewed umbrella adequacy against contract requirements?",
    "inland_marine": "What is the total value of tools and equipment you move between locations?",
    "builders_risk": "Do your contracts specify who carries builders risk during active projects?",
    "property": "When was the last time your property values were appraised for insurance purposes?",
    "cargo": "What is the maximum value of a single load, and do you carry refrigerated or hazmat freight?",
    "cyber": "How do you store employee PII and customer payment data?",
    "epli": "Do you have an employee handbook reviewed by employment counsel?",
    "professional_liability": "Have you had any professional liability or E&O claims in the past 5 years?",
    "hired_non_owned_auto": "Do any employees drive personal vehicles to job sites?",
}

_SUGGESTED_QUESTIONS_BY_ATTRIBUTE = {
    "uses_subcontractors": "Are subcontractors required to provide certificates of insurance before starting work?",
    "high_employee_count": "Do you have formal HR policies covering hiring, termination, and anti-harassment?",
    "high_vehicle_count": "Do you run MVR checks on all drivers at hire and annually?",
    "high_revenue": "Have you reviewed your liability limits relative to your annual revenue and contractual requirements?",
    "high_mod": "Your experience mod suggests elevated losses — what loss control measures have you implemented?",
    "wind_state": "What is your current named-storm deductible, and have you stress-tested a wind loss?",
    "flood_state": "Is your property in a flood zone, and do you carry separate flood coverage?",
    "earthquake_state": "Do you carry earthquake coverage, and has your building's seismic vulnerability been assessed?",
}

# Confidence scores: how likely this coverage is truly missing/needed
# Based on industry data certainty (1.0 = very certain, 0.5 = speculative)
_COVERAGE_CONFIDENCE = {
    "workers_comp": 0.95,
    "general_liability": 0.93,
    "commercial_auto": 0.90,
    "umbrella": 0.78,
    "inland_marine": 0.72,
    "builders_risk": 0.60,
    "property": 0.80,
    "cargo": 0.88,
    "cyber": 0.55,
    "epli": 0.65,
    "professional_liability": 0.62,
    "hired_non_owned_auto": 0.75,
}

# Endorsements commonly missed by industry
_INDUSTRY_ENDORSEMENTS = {
    "roofing": [
        {"endorsement": "Waiver of Subrogation", "reason": "Frequently required by contract in this industry"},
        {"endorsement": "Additional Insured — Ongoing & Completed Operations", "reason": "GC contracts typically require AI coverage for both ongoing and completed operations"},
        {"endorsement": "Per Project Aggregate", "reason": "Multiple active job sites need per-project aggregate to avoid exhausting limits"},
    ],
    "trucking": [
        {"endorsement": "Motor Carrier MCS-90", "reason": "Required by federal regulation for for-hire carriers"},
        {"endorsement": "Trailer Interchange Agreement", "reason": "Borrowed or interchanged trailers need separate coverage"},
        {"endorsement": "Pollution Liability — Broadened", "reason": "Standard auto excludes fuel spill cleanup and environmental response"},
    ],
    "manufacturing": [
        {"endorsement": "Product Recall Expense", "reason": "Standard GL excludes recall costs; must be added separately"},
        {"endorsement": "Equipment Breakdown", "reason": "Standard property excludes mechanical/electrical breakdown of machinery"},
        {"endorsement": "Waiver of Subrogation — WC", "reason": "Customer contracts often require WC waivers"},
    ],
    "restaurant": [
        {"endorsement": "Liquor Liability", "reason": "Excluded from standard GL; required if alcohol is served"},
        {"endorsement": "Food Contamination / Spoilage", "reason": "Not automatic on property policies; covers inventory loss from equipment failure"},
        {"endorsement": "Assault & Battery", "reason": "Often excluded on GL in hospitality; separate endorsement needed for late-night operations"},
    ],
    "landscaping": [
        {"endorsement": "Pesticide / Herbicide Application", "reason": "Chemical application liability may be excluded without specific endorsement"},
        {"endorsement": "Waiver of Subrogation", "reason": "Commercial property clients frequently require WOS endorsements"},
        {"endorsement": "Additional Insured — Blanket", "reason": "Multiple property management clients require AI coverage"},
    ],
    "hvac": [
        {"endorsement": "Professional Liability / E&O", "reason": "Design or engineering services alongside installation require E&O coverage"},
        {"endorsement": "Waiver of Subrogation", "reason": "GC and property owner contracts frequently require WOS"},
        {"endorsement": "Additional Insured — Blanket", "reason": "GC contracts typically require blanket AI endorsement"},
    ],
}

_GENERIC_ENDORSEMENTS = [
    {"endorsement": "Waiver of Subrogation", "reason": "Commonly required by contracts across most commercial lines"},
    {"endorsement": "Additional Insured", "reason": "Contractual requirements often mandate AI endorsements on GL and auto policies"},
]


# ============================================================
# CONFIDENCE RULE DEFINITIONS
# ============================================================
# Each rule records why a confidence score was assigned or adjusted.

RULE_INDUSTRY_EXPECTED = {
    "code": "industry_expected",
    "description": "Coverage expected for this industry class based on standard program benchmarks",
}
RULE_VEHICLE_EXPOSURE = {
    "code": "vehicle_exposure",
    "description": "Account operates vehicles; commercial auto or HNOA coverage expected",
}
RULE_EMPLOYEE_COUNT = {
    "code": "employee_count",
    "description": "Employee headcount triggers coverage expectation threshold",
}
RULE_SUBCONTRACTOR_EXPOSURE = {
    "code": "subcontractor_exposure",
    "description": "Subcontractor usage creates upstream liability and excess exposure",
}
RULE_LOSS_RUN_WC_FREQUENCY = {
    "code": "loss_run_wc_frequency",
    "description": "Loss run data confirms elevated Workers Comp claim frequency",
}
RULE_LOSS_RUN_AUTO_CLAIMS = {
    "code": "loss_run_auto_claims",
    "description": "Loss run data confirms vehicle-related claim activity",
}


def _make_rule(rule: dict, confidence_delta: float) -> dict:
    """Create an applied_rules entry with a confidence delta."""
    return {
        "code": rule["code"],
        "description": rule["description"],
        "confidence_delta": confidence_delta,
    }


def detect_coverage_gaps(account_profile: dict) -> dict:
    """Coverage Gap Insight Engine.

    Given an industry profile and basic account attributes, return likely
    insurance coverage gaps and suggested producer questions.

    Args:
        account_profile: dict with optional keys:
            industry, state, employee_count, vehicle_count,
            annual_revenue, experience_mod, uses_subcontractors,
            current_coverages

    Returns:
        {
            "coverage_gaps": [
                {"coverage": str, "reason": str, "risk_level": str},
                ...
            ],
            "suggested_questions": [str, ...]
        }
    """
    industry_raw = account_profile.get("industry", "")
    industry = _normalize_industry(industry_raw)
    state = (account_profile.get("state") or "").upper()
    employee_count = account_profile.get("employee_count") or account_profile.get("employees") or 0
    vehicle_count = account_profile.get("vehicle_count") or account_profile.get("vehicles") or 0
    annual_revenue = account_profile.get("annual_revenue") or 0
    experience_mod = account_profile.get("experience_mod") or account_profile.get("current_mod")
    uses_subcontractors = account_profile.get("uses_subcontractors", False)
    current_coverages = set(
        c.strip().lower() for c in (account_profile.get("current_coverages") or [])
    )

    logger.info(
        "Coverage gap analysis: industry=%s state=%s employees=%d vehicles=%d",
        industry, state, employee_count, vehicle_count,
    )

    coverage_gaps = []
    questions = []

    # 1. Compare expected coverages vs declared coverages
    expected = INDUSTRY_EXPECTED_COVERAGES.get(industry, [])
    for cov in expected:
        if cov not in current_coverages:
            base_confidence = _COVERAGE_CONFIDENCE.get(cov, 0.60)
            coverage_gaps.append({
                "coverage": _COVERAGE_DISPLAY.get(cov, cov.replace("_", " ").title()),
                "reason": _COVERAGE_REASONS.get(cov, f"Standard coverage for {industry} operations is missing"),
                "risk_level": _COVERAGE_RISK_LEVELS.get(cov, "medium"),
                "confidence": base_confidence,
                "applied_rules": [_make_rule(RULE_INDUSTRY_EXPECTED, base_confidence)],
            })
            q = _SUGGESTED_QUESTIONS_BY_COVERAGE.get(cov)
            if q and q not in questions:
                questions.append(q)

    # 2. Vehicle-driven gaps
    if vehicle_count > 0 and "commercial_auto" not in current_coverages:
        auto_gap = {
            "coverage": _COVERAGE_DISPLAY["commercial_auto"],
            "reason": f"Account operates {vehicle_count} vehicles but has no commercial auto coverage",
            "risk_level": "high",
            "confidence": 0.92,
            "applied_rules": [_make_rule(RULE_VEHICLE_EXPOSURE, 0.92)],
        }
        if not any(g["coverage"] == auto_gap["coverage"] for g in coverage_gaps):
            coverage_gaps.append(auto_gap)

    if vehicle_count > 0 and "hired_non_owned_auto" not in current_coverages:
        hnoa_gap = {
            "coverage": _COVERAGE_DISPLAY["hired_non_owned_auto"],
            "reason": "Employees may use personal vehicles for job activities",
            "risk_level": "medium",
            "confidence": 0.75,
            "applied_rules": [_make_rule(RULE_VEHICLE_EXPOSURE, 0.75)],
        }
        if not any(g["coverage"] == hnoa_gap["coverage"] for g in coverage_gaps):
            coverage_gaps.append(hnoa_gap)
            q = _SUGGESTED_QUESTIONS_BY_COVERAGE["hired_non_owned_auto"]
            if q not in questions:
                questions.append(q)

    # 3. Employee-count-driven gaps
    if employee_count >= 50 and "epli" not in current_coverages:
        epli_gap = {
            "coverage": _COVERAGE_DISPLAY["epli"],
            "reason": f"With {employee_count} employees, employment practices claims become statistically likely",
            "risk_level": "medium",
            "confidence": 0.70,
            "applied_rules": [_make_rule(RULE_EMPLOYEE_COUNT, 0.70)],
        }
        if not any(g["coverage"] == epli_gap["coverage"] for g in coverage_gaps):
            coverage_gaps.append(epli_gap)
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["high_employee_count"]
        if q not in questions:
            questions.append(q)

    if employee_count >= 25 and "cyber" not in current_coverages:
        cyber_confidence = 0.55 if employee_count < 50 else 0.65
        cyber_gap = {
            "coverage": _COVERAGE_DISPLAY["cyber"],
            "reason": f"A {employee_count}-employee operation stores employee PII and likely processes data electronically",
            "risk_level": "low" if employee_count < 50 else "medium",
            "confidence": cyber_confidence,
            "applied_rules": [_make_rule(RULE_EMPLOYEE_COUNT, cyber_confidence)],
        }
        if not any(g["coverage"] == cyber_gap["coverage"] for g in coverage_gaps):
            coverage_gaps.append(cyber_gap)

    # 4. Subcontractor exposure
    if uses_subcontractors:
        if "general_liability" not in current_coverages:
            gl_gap = {
                "coverage": _COVERAGE_DISPLAY["general_liability"],
                "reason": "Subcontractor usage without confirmed GL creates upstream liability risk",
                "risk_level": "high",
                "confidence": 0.90,
                "applied_rules": [_make_rule(RULE_SUBCONTRACTOR_EXPOSURE, 0.90)],
            }
            if not any(g["coverage"] == gl_gap["coverage"] for g in coverage_gaps):
                coverage_gaps.append(gl_gap)

        if "umbrella" not in current_coverages:
            umb_gap = {
                "coverage": _COVERAGE_DISPLAY["umbrella"],
                "reason": "Subcontractor operations amplify excess liability exposure beyond primary limits",
                "risk_level": "medium",
                "confidence": 0.78,
                "applied_rules": [_make_rule(RULE_SUBCONTRACTOR_EXPOSURE, 0.78)],
            }
            if not any(g["coverage"] == umb_gap["coverage"] for g in coverage_gaps):
                coverage_gaps.append(umb_gap)

        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["uses_subcontractors"]
        if q not in questions:
            questions.append(q)

    # 5. Experience mod concerns
    if experience_mod is not None and experience_mod > 1.0:
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["high_mod"]
        if q not in questions:
            questions.append(q)

    # 6. State-based exposure questions
    if state in HIGH_WIND_STATES:
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["wind_state"]
        if q not in questions:
            questions.append(q)

    if state in FLOOD_RISK_STATES:
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["flood_state"]
        if q not in questions:
            questions.append(q)

    if state in EARTHQUAKE_STATES:
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["earthquake_state"]
        if q not in questions:
            questions.append(q)

    # 7. Revenue-driven question
    if annual_revenue and annual_revenue > 1_000_000:
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE["high_revenue"]
        if q not in questions:
            questions.append(q)

    # 8. Vehicle-driven question
    if vehicle_count > 0:
        q = _SUGGESTED_QUESTIONS_BY_ATTRIBUTE.get("high_vehicle_count")
        if q and q not in questions:
            questions.append(q)

    # 9. Loss run integration — boost confidence on gaps confirmed by loss patterns
    loss_run_data = account_profile.get("loss_run_data")
    if loss_run_data and isinstance(loss_run_data, dict):
        loss_patterns = " ".join(loss_run_data.get("patterns", [])).lower()
        loss_flags = " ".join(loss_run_data.get("underwriting_flags", [])).lower()

        # Boost confidence on WC gaps if loss data shows WC frequency
        if "workers comp" in loss_flags:
            delta = 0.10
            for gap in coverage_gaps:
                if "workers" in gap["coverage"].lower():
                    gap["confidence"] = min(gap.get("confidence", 0.6) + delta, 1.0)
                    gap.setdefault("applied_rules", []).append(
                        _make_rule(RULE_LOSS_RUN_WC_FREQUENCY, delta)
                    )

        # Boost auto gaps if vehicle claims present
        if "vehicle" in loss_patterns or "auto" in loss_flags:
            delta = 0.10
            for gap in coverage_gaps:
                if "auto" in gap["coverage"].lower():
                    gap["confidence"] = min(gap.get("confidence", 0.6) + delta, 1.0)
                    gap.setdefault("applied_rules", []).append(
                        _make_rule(RULE_LOSS_RUN_AUTO_CLAIMS, delta)
                    )

        # Add loss-derived questions
        for point in loss_run_data.get("producer_talking_points", [])[:2]:
            if point not in questions:
                questions.append(point)

    # Sort gaps: high > medium > low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    coverage_gaps.sort(key=lambda g: severity_order.get(g["risk_level"], 3))

    # Missing endorsements
    endorsements = list(_INDUSTRY_ENDORSEMENTS.get(industry, _GENERIC_ENDORSEMENTS))
    if uses_subcontractors and not any(e["endorsement"] == "Waiver of Subrogation" for e in endorsements):
        endorsements.insert(0, {"endorsement": "Waiver of Subrogation", "reason": "Subcontractor relationships typically require WOS endorsements"})

    # Confirmation questions — practical questions that confirm or deny a gap
    confirmation_questions = list(questions[:5])
    if uses_subcontractors:
        cq = "Do your contracts require waiver of subrogation or additional insured wording?"
        if cq not in confirmation_questions:
            confirmation_questions.append(cq)
    if vehicle_count > 0:
        cq = "Are tools stored overnight in trucks or trailers?"
        if cq not in confirmation_questions:
            confirmation_questions.append(cq)
    if employee_count >= 25:
        cq = "How is employee and customer data stored and protected?"
        if cq not in confirmation_questions:
            confirmation_questions.append(cq)

    # 9. Tier profile enrichment — inject conversation prompts and GL exposures
    tier_slug, tier_source = resolve(industry_raw or industry)
    enrichment = get_enrichment(industry_raw or industry)
    tier_prompts = enrichment.get("conversation_prompts", [])
    gl_exposures = enrichment.get("gl_exposures", [])
    regional_notes = enrichment.get("regional_notes", "")

    # Add tier conversation prompts as additional suggested questions
    for prompt in tier_prompts:
        if prompt not in questions:
            questions.append(prompt)

    logger.info(
        "Coverage gap analysis complete: %d gaps, %d endorsements, %d questions (tier=%s)",
        len(coverage_gaps), len(endorsements), len(confirmation_questions), tier_source,
    )

    result = {
        "industry": industry_raw or industry,
        "coverage_gaps": coverage_gaps,
        "missing_endorsements": endorsements[:5],
        "confirmation_questions": confirmation_questions[:6],
        "suggested_questions": questions,
    }

    # Include tier enrichment when available
    if enrichment:
        result["tier_enrichment"] = {
            "gl_exposures": gl_exposures[:5],
            "wc_claims": enrichment.get("wc_claims", [])[:5],
            "auto_claims": enrichment.get("auto_claims", [])[:3],
            "regional_notes": regional_notes,
            "tier": enrichment.get("tier"),
            "display_name": enrichment.get("display_name", ""),
        }

    return result
