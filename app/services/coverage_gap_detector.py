"""Coverage Gap Detector — deterministic producer reasoning layer.

Analyzes account inputs (industry, state, mod, employee count, traits, themes)
and returns structured coverage gaps with severity, reasoning, and suggested actions.

NOT carrier-accurate quoting logic. This is a producer preparation tool.
"""

import logging

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
