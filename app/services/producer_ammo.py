"""Producer Ammo — sharp, meeting-ready talking points for producers.

Generates deterministic, specific ammo organized into:
- renewal_pressure_points: leverage for renewal conversations
- underwriting_hot_buttons: what underwriters will focus on
- cross_sell_openings: account-rounding and new line opportunities
- hard_questions_to_ask: direct, specific questions that show expertise

NOT generic conversation starters. These should feel usable in a real meeting.
"""

import logging

from app.services.coverage_gap_detector import (
    INDUSTRY_EXPECTED_COVERAGES,
    HIGH_WIND_STATES,
    EARTHQUAKE_STATES,
    FLOOD_RISK_STATES,
    INDUSTRY_FLEET_HEAVY,
    INDUSTRY_GL_HEAVY,
    _normalize_industry,
)
from app.services.industry_loader import get_enrichment

logger = logging.getLogger(__name__)


def generate_ammo(
    industry: str,
    state: str,
    employee_count: int = 10,
    current_mod: float | None = None,
    entity_type: str = "private_business",
    department: str | None = None,
    account_traits: list[str] | None = None,
    risk_themes: set[str] | None = None,
    coverage_tags: set[str] | None = None,
) -> dict:
    """Generate producer ammo from account inputs.

    Returns dict with: renewal_pressure_points, underwriting_hot_buttons,
    cross_sell_openings, hard_questions_to_ask.
    """
    account_traits = account_traits or []
    risk_themes = risk_themes or set()
    coverage_tags = coverage_tags or set()
    industry_lower = industry.lower()
    state_upper = state.upper()

    renewal = []
    underwriting = []
    cross_sell = []
    hard_questions = []

    # ============================================================
    # RENEWAL PRESSURE POINTS
    # ============================================================

    if current_mod is not None:
        if current_mod > 1.10:
            renewal.append(
                f"Your mod is {current_mod:.3f} — that means you're paying "
                f"{int((current_mod - 1.0) * 100)}% more than the average for your class. "
                f"What changed operationally in the last 12 months?"
            )
        elif current_mod < 0.85:
            renewal.append(
                f"Your mod is {current_mod:.3f} — you're running better than average. "
                f"Are you leveraging that in your renewal negotiations? "
                f"Carriers should be competing for this account."
            )

    if employee_count > 75:
        renewal.append(
            f"With {employee_count} employees, you're large enough for "
            f"experience-rated programs, retro plans, or captive options. "
            f"Have those been modeled?"
        )

    if "high_turnover" in account_traits:
        renewal.append(
            "High turnover is a leading indicator of first-year injury claims. "
            "What does your onboarding and safety training look like for new hires?"
        )

    if industry_lower == "trucking":
        renewal.append(
            "Auto liability rates are hardening across the board for trucking. "
            "What's your strategy if your incumbent carrier non-renews or pushes a 20%+ increase?"
        )

    if industry_lower == "roofing":
        renewal.append(
            "Roofing WC rates remain elevated in most states. "
            "A documented safety program and return-to-work protocol are your best leverage for rate relief."
        )

    if entity_type == "public_entity":
        renewal.append(
            "Public entity pools are tightening eligibility. "
            "Have you benchmarked pool coverage against the commercial market recently?"
        )

    # ============================================================
    # UNDERWRITING HOT BUTTONS
    # ============================================================

    if "fleet_accidents" in risk_themes or "fleet_liability" in risk_themes:
        underwriting.append(
            "Underwriters will ask about your fleet — vehicle list, driver MVR screening, "
            "and telematics. Have those ready before the submission goes in."
        )

    if "falls_from_height" in risk_themes:
        underwriting.append(
            "Falls from height is the #1 loss driver for this class. "
            "Underwriters want to see: fall protection program, OSHA 10/30 training records, "
            "and equipment inspection logs."
        )

    if current_mod is not None and current_mod > 1.0:
        underwriting.append(
            f"A {current_mod:.3f} mod will be the first thing underwriters flag. "
            f"Come prepared with a loss narrative: what happened, what's changed, "
            f"and what controls are now in place."
        )

    if "uses_subcontractors" in account_traits:
        underwriting.append(
            "Subcontractor usage is a GL underwriting trigger. "
            "Have your sub list, COI compliance process, and hold-harmless agreements ready."
        )

    if "heavy_equipment" in account_traits:
        underwriting.append(
            "Heavy equipment operations flag inland marine and auto underwriting. "
            "Have an equipment schedule with values, maintenance records, and operator certifications."
        )

    if employee_count > 100:
        underwriting.append(
            "At this size, underwriters will want a formal safety manual, "
            "dedicated safety personnel, and documented incident investigation procedures."
        )

    if industry_lower == "manufacturing":
        underwriting.append(
            "Manufacturing underwriters focus on machine guarding, LOTO compliance, "
            "and housekeeping. A recent loss control report is your strongest submission tool."
        )

    if department == "law_enforcement":
        underwriting.append(
            "LE liability underwriters will scrutinize use-of-force policy dates, "
            "body camera adoption, and training frequency. Have those documented."
        )

    # ============================================================
    # CROSS-SELL OPENINGS
    # ============================================================

    if "cyber" not in coverage_tags and employee_count >= 15:
        cross_sell.append(
            f"A {employee_count}-employee operation handles PII and processes payments electronically. "
            f"Cyber liability is a natural add — and the premium is often modest."
        )

    if "epli" not in coverage_tags and employee_count >= 25:
        cross_sell.append(
            "No EPLI on the account? With 25+ employees, "
            "wrongful termination and harassment claims become a real exposure. "
            "This is a straightforward cross-sell."
        )

    if "umbrella" not in coverage_tags:
        cross_sell.append(
            "No umbrella coverage confirmed. Given the operations profile, "
            "excess liability should be part of every renewal conversation."
        )

    if industry_lower in ("roofing", "hvac", "landscaping") and "inland_marine" not in coverage_tags:
        cross_sell.append(
            f"{industry.title()} operations move tools and equipment between sites. "
            f"A contractors equipment floater is an easy add that fills a real gap."
        )

    if "professional_liability" not in coverage_tags and industry_lower in ("hvac", "manufacturing"):
        cross_sell.append(
            "Professional liability / errors & omissions may apply if you provide design, "
            "engineering, or consulting services alongside installation."
        )

    if entity_type == "public_entity" and "cyber" not in coverage_tags:
        cross_sell.append(
            "Public entities are prime targets for ransomware and data breaches. "
            "Cyber coverage with breach response is critical for protecting citizen data."
        )

    # ============================================================
    # HARD QUESTIONS TO ASK
    # ============================================================

    if "uses_subcontractors" in account_traits:
        hard_questions.append(
            "You use subs. Show me how you verify AI/Waiver/COI compliance "
            "before work starts — not after."
        )

    if "young_fleet" in account_traits or "fleet_accidents" in risk_themes:
        hard_questions.append(
            "You have mobile crews and auto exposure. "
            "Walk me through driver eligibility and vehicle take-home rules."
        )

    if industry_lower in ("manufacturing", "roofing", "hvac"):
        hard_questions.append(
            "When was your last OSHA inspection, and what was the result? "
            "Any open citations or abatement deadlines?"
        )

    if current_mod is not None and current_mod > 1.0:
        hard_questions.append(
            "What specific loss control changes have you made since your largest claim? "
            "I need the specifics for the underwriting submission."
        )

    if industry_lower in ("manufacturing", "restaurant"):
        hard_questions.append(
            "If a large property loss hit this location, how long could you operate "
            "before business income becomes painful? Have you tested that number?"
        )

    if "multi_state_operations" in account_traits:
        hard_questions.append(
            "You operate in multiple states. Walk me through how you handle "
            "state-specific WC filings, monopolistic state requirements, and payroll allocation."
        )

    if entity_type == "public_entity" and department == "law_enforcement":
        hard_questions.append(
            "When was the department's use-of-force policy last reviewed? "
            "Does every patrol officer wear a body camera?"
        )

    if entity_type == "public_entity" and department == "public_works":
        hard_questions.append(
            "How do you document road maintenance and pothole repair timelines? "
            "That documentation is your primary defense in road liability claims."
        )

    if "seasonal_payroll" in account_traits:
        hard_questions.append(
            "You have seasonal payroll swings. How are you classifying seasonal workers, "
            "and does your carrier audit reconcile quarterly or annually?"
        )

    if employee_count > 50:
        hard_questions.append(
            "Do you have a formal return-to-work / modified duty program? "
            "That's the single biggest lever for mod improvement."
        )

    # Default items if sections are empty
    if not renewal:
        renewal.append(
            "Review the expiring program against current operations. "
            "Have revenues, payroll, or operations changed materially since the last renewal?"
        )

    if not underwriting:
        underwriting.append(
            f"Prepare a clean submission: 5 years of loss runs, current payroll by class code, "
            f"and a narrative on any large claims."
        )

    if not hard_questions:
        hard_questions.append(
            "What keeps you up at night about your business? "
            "That's usually where the uninsured exposure lives."
        )

    return {
        "renewal_pressure_points": renewal[:5],
        "underwriting_hot_buttons": underwriting[:5],
        "cross_sell_openings": cross_sell[:5],
        "hard_questions_to_ask": hard_questions[:5],
    }


# ============================================================
# PRODUCER AMMO QUESTIONS ENGINE
# ============================================================
# Standalone function for pre-call planning, discovery meetings,
# renewals, and account reviews. Stage-aware, industry-tailored.

_VALID_STAGES = {"prospect", "renewal", "remarket", "service_review"}

# --- Industry-specific question banks ---

_INDUSTRY_TOP_QUESTIONS = {
    "roofing": [
        "Have any employees begun using personal vehicles between job sites?",
        "How are subcontractor certificates and additional insured requirements being tracked today?",
        "Have you taken on any larger or steeper-slope jobs since the last renewal?",
        "What is your fall protection program, and who conducts safety audits?",
        "Do you carry separate builders risk, or does the property owner handle that contractually?",
    ],
    "trucking": [
        "How many drivers are on your roster today versus last renewal?",
        "What is the maximum cargo value per load, and do you haul any hazmat or temperature-sensitive freight?",
        "Do you run MVR checks at hire and annually on all drivers?",
        "What telematics or dashcam systems are installed in the fleet?",
        "Have you had any DOT violations or out-of-service orders in the past 12 months?",
    ],
    "manufacturing": [
        "Walk me through your lockout/tagout program — who manages compliance?",
        "Has any new machinery been added or processes changed since last renewal?",
        "What is your approach to machine guarding inspections and documentation?",
        "How do you handle temporary or staffing-agency workers on the floor?",
        "Have you received any OSHA citations in the past 3 years?",
    ],
    "restaurant": [
        "Have you added delivery, catering, or food truck operations since last year?",
        "What is your approach to slip-and-fall prevention in the kitchen and dining areas?",
        "How many employees handle alcohol service, and are they TIPS/ServSafe certified?",
        "Do you use any third-party delivery platforms, and how does liability work under those contracts?",
        "Has your menu or cooking equipment changed in ways that affect fire suppression?",
    ],
    "landscaping": [
        "How many crews are running simultaneously, and who supervises each?",
        "What is the total value of tools and equipment you move between job sites?",
        "Do any employees operate heavy equipment like skid-steers or excavators?",
        "How are herbicide and pesticide applications managed and documented?",
        "Have you expanded into tree removal, irrigation, or hardscaping?",
    ],
    "hvac": [
        "Do you perform design or engineering work in addition to installation?",
        "How many service vehicles run daily, and who is authorized to drive?",
        "What is your refrigerant handling and EPA 608 compliance process?",
        "Have you taken on any commercial or industrial jobs that differ from your typical residential work?",
        "Do you use subcontractors for electrical, plumbing, or ductwork?",
    ],
}

_INDUSTRY_COVERAGE_TRAPS = {
    "roofing": [
        "Hired/non-owned auto often gets missed when estimators or supervisors use personal vehicles.",
        "Tools and equipment coverage may be inadequate if theft from trucks is increasing.",
        "Waiver of subrogation and additional insured wording can create contract problems if not reviewed.",
        "Completed operations exclusions can leave the contractor exposed after project handoff.",
    ],
    "trucking": [
        "Motor truck cargo limits may not match the actual max load value being hauled.",
        "Trailer interchange coverage is frequently overlooked for owner-operators pulling borrowed trailers.",
        "Non-trucking liability gaps appear when drivers use rigs for personal errands.",
        "Pollution liability from fuel spills is excluded on standard auto policies.",
    ],
    "manufacturing": [
        "Product recall expense is rarely covered under standard GL and must be added separately.",
        "Equipment breakdown coverage fills gaps left by standard property policies for mechanical failure.",
        "Pollution liability from chemical processes or waste disposal is typically excluded.",
        "Business income limits may not reflect current revenue if set during a lower-volume year.",
    ],
    "restaurant": [
        "Liquor liability is often excluded from standard GL and requires a separate endorsement.",
        "Food contamination / spoilage coverage is not automatic on property policies.",
        "Third-party delivery contracts may shift liability back to the restaurant without clear coverage.",
        "Employment practices exposure increases sharply with tip-pool disputes and wage claims.",
    ],
    "landscaping": [
        "Pesticide and herbicide application liability may be excluded without a specific endorsement.",
        "Inland marine limits may not cover newer, more expensive equipment purchases.",
        "Tree removal operations carry higher GL and WC exposure than general landscaping.",
        "Damage to customer property (irrigation lines, underground utilities) can exceed GL sub-limits.",
    ],
    "hvac": [
        "Professional liability / E&O is missed when HVAC contractors provide design or engineering services.",
        "Refrigerant leak liability and EPA fines are not covered under standard GL.",
        "Faulty workmanship exclusions in GL can leave callbacks and redo work uninsured.",
        "Indoor air quality claims from mold or contamination may trigger pollution exclusions.",
    ],
}

_INDUSTRY_UNDERWRITING_FLAGS = {
    "roofing": [
        "High-mod or recent claims may trigger loss control scrutiny.",
        "Mixed residential/commercial work may create class code or appetite issues.",
        "Steep-slope work (>6:12 pitch) is a hard market trigger for many carriers.",
    ],
    "trucking": [
        "Radius of operations beyond 500 miles changes carrier appetite significantly.",
        "Owner-operator models versus W-2 drivers affect class code and underwriting treatment.",
        "DOT safety scores and CSA data are reviewed by every underwriter.",
    ],
    "manufacturing": [
        "Combustible dust exposure triggers OSHA NEP and carrier scrutiny.",
        "Foreign-sourced components may introduce product liability gaps.",
        "Temp labor usage above 20% of workforce raises WC classification questions.",
    ],
    "restaurant": [
        "Late-night hours and alcohol service raise GL and assault/battery concerns.",
        "Multiple locations with different menus or concepts may need separate class codes.",
        "High employee turnover drives WC frequency and training adequacy questions.",
    ],
    "landscaping": [
        "Tree removal and stump grinding operations trigger different class codes and carrier appetite.",
        "Pesticide application licensing and compliance affect GL underwriting.",
        "Seasonal workforce fluctuation creates payroll audit and classification risk.",
    ],
    "hvac": [
        "New construction versus service/repair split affects class code assignment.",
        "Rooftop unit work on commercial buildings raises falls-from-height exposure.",
        "Subcontractor use for electrical or plumbing work introduces risk transfer questions.",
    ],
}

# --- Stage-specific operational change questions ---

_STAGE_OPERATIONAL_QUESTIONS = {
    "prospect": [
        "What does your current insurance program look like, and what's working or not?",
        "What types of contracts do you sign, and what insurance requirements do they impose?",
        "How have operations changed in the past 2 years — new services, locations, or headcount?",
        "Who handles your safety program, and is it documented?",
        "What is your biggest operational concern heading into next year?",
    ],
    "renewal": [
        "Any changes in payroll, headcount, territory, or job mix since last renewal?",
        "Any new services, locations, or operational shifts?",
        "Any change in subcontractor usage or labor sourcing?",
        "Have your contract requirements changed — new AI/WOS requirements from GCs or clients?",
        "Any open claims or incidents that haven't been reported yet?",
    ],
    "remarket": [
        "What is driving the remarket — rate, service, coverage gaps, or carrier appetite?",
        "What documentation do you have ready: loss runs, mod worksheets, payroll by class?",
        "Are there any claims in litigation or reserve increases the current carrier has flagged?",
        "What coverage terms or endorsements are must-haves versus nice-to-haves?",
        "Is the current carrier willing to re-quote, or have they given a firm non-renewal?",
    ],
    "service_review": [
        "Have there been any operational changes since the policy was bound — fleet, headcount, revenue?",
        "Are there any pending contract bids that require higher limits or specific endorsements?",
        "Have any claims been filed since inception, and how were they handled?",
        "Are vehicle schedules and driver lists current on the policy?",
        "Have you added or removed any locations, equipment, or business activities?",
    ],
}

# --- Generic fallback questions for unknown industries ---

_GENERIC_TOP_QUESTIONS = [
    "Walk me through your operations — what does a typical week look like?",
    "How many employees do you have, and has headcount changed recently?",
    "Do you use subcontractors or temporary workers for any part of your operations?",
    "What vehicles or mobile equipment does your business operate?",
    "What are your biggest concerns about your current insurance program?",
]

_GENERIC_COVERAGE_TRAPS = [
    "Hired and non-owned auto is frequently missing when employees use personal vehicles for work.",
    "Business income limits are often set years ago and may not reflect current revenue.",
    "Umbrella coverage may not schedule all underlying policies, creating gaps at the excess layer.",
    "Cyber liability is increasingly relevant but absent from most small commercial accounts.",
]

_GENERIC_UNDERWRITING_FLAGS = [
    "Experience mod above unity will be the first thing underwriters review.",
    "Incomplete loss runs or missing prior carrier information slows the submission process.",
    "Operations changes since the last policy period may require class code reclassification.",
]


def generate_producer_ammo(profile: dict) -> dict:
    """Producer Ammo Questions Engine.

    Given an industry and account context, generate sharp, practical producer
    questions for pre-call planning, discovery, renewals, and account reviews.

    Args:
        profile: dict with optional keys:
            industry, state, employee_count, annual_revenue, vehicle_count,
            experience_mod, uses_subcontractors, current_coverages,
            claims_summary, account_stage, notes

    Returns:
        {
            "industry": str,
            "account_stage": str,
            "ammo_questions": {
                "top_questions": [...],
                "coverage_traps": [...],
                "operational_change_questions": [...],
                "underwriting_flags": [...]
            }
        }
    """
    industry_raw = profile.get("industry", "")
    industry = _normalize_industry(industry_raw)
    state = (profile.get("state") or "").upper()
    employee_count = profile.get("employee_count") or profile.get("employees") or 0
    annual_revenue = profile.get("annual_revenue") or 0
    vehicle_count = profile.get("vehicle_count") or profile.get("vehicles") or 0
    experience_mod = profile.get("experience_mod") or profile.get("current_mod")
    uses_subcontractors = profile.get("uses_subcontractors", False)
    current_coverages = set(
        c.strip().lower() for c in (profile.get("current_coverages") or [])
    )
    claims_summary = profile.get("claims_summary") or ""
    account_stage = (profile.get("account_stage") or "renewal").strip().lower()
    if account_stage not in _VALID_STAGES:
        account_stage = "renewal"

    logger.info(
        "Producer ammo generation: industry=%s state=%s stage=%s employees=%d",
        industry, state, account_stage, employee_count,
    )

    # --- Tier profile enrichment ---
    enrichment = get_enrichment(industry_raw or industry)
    tier_prompts = enrichment.get("conversation_prompts", [])
    tier_gl = enrichment.get("gl_exposures", [])
    tier_wc = enrichment.get("wc_claims", [])

    # --- Top Questions ---
    # For core industries, use curated questions; for tier industries, use tier prompts
    if industry in _INDUSTRY_TOP_QUESTIONS:
        top_questions = list(_INDUSTRY_TOP_QUESTIONS[industry])
    elif tier_prompts:
        top_questions = list(tier_prompts[:5])
    else:
        top_questions = list(_GENERIC_TOP_QUESTIONS)

    # Add context-driven questions
    if uses_subcontractors and not any("subcontract" in q.lower() for q in top_questions):
        top_questions.insert(0, "How are subcontractor certificates and additional insured requirements being tracked today?")

    if vehicle_count > 0 and not any("vehicle" in q.lower() or "fleet" in q.lower() for q in top_questions):
        top_questions.insert(0, f"You operate {vehicle_count} vehicles — who is authorized to drive, and what are your take-home policies?")

    if experience_mod is not None and experience_mod > 1.0:
        mod_q = f"Your experience mod is {experience_mod:.2f} — what loss control changes have been implemented since the largest claim?"
        top_questions.insert(0, mod_q)

    if employee_count >= 50 and "epli" not in current_coverages:
        top_questions.append("Do you have an employee handbook, and when was it last reviewed by employment counsel?")

    # --- Coverage Traps ---
    # For core industries, use curated traps; for tier industries, derive from GL exposures
    if industry in _INDUSTRY_COVERAGE_TRAPS:
        coverage_traps = list(_INDUSTRY_COVERAGE_TRAPS[industry])
    elif tier_gl:
        coverage_traps = [f"GL exposure: {exp}" for exp in tier_gl[:4]]
    else:
        coverage_traps = list(_GENERIC_COVERAGE_TRAPS)

    # Add coverage-specific traps based on missing coverages
    expected = INDUSTRY_EXPECTED_COVERAGES.get(industry, [])
    missing = [c for c in expected if c not in current_coverages]
    if "umbrella" in missing and not any("umbrella" in t.lower() for t in coverage_traps):
        coverage_traps.append("Umbrella coverage is missing — excess liability above primary GL and auto is baseline protection for this class.")
    if "cyber" in missing and not any("cyber" in t.lower() for t in coverage_traps):
        coverage_traps.append("Cyber liability is increasingly essential but absent from the current program.")

    # State-specific traps (insert near top for visibility)
    if state in EARTHQUAKE_STATES:
        coverage_traps.insert(0, f"Earthquake is excluded from standard property in {state}. DIC or standalone EQ should be discussed.")
    if state in FLOOD_RISK_STATES:
        coverage_traps.insert(0, f"Standard property excludes flood in {state}. Separate flood coverage should be confirmed.")
    if state in HIGH_WIND_STATES:
        coverage_traps.insert(0, f"Named-storm deductibles in {state} can be 2-5% of insured value — confirm the client understands their retention.")

    # --- Operational Change Questions ---
    operational_questions = list(_STAGE_OPERATIONAL_QUESTIONS.get(account_stage, _STAGE_OPERATIONAL_QUESTIONS["renewal"]))

    # Add industry-specific operational questions
    if industry in INDUSTRY_FLEET_HEAVY and not any("fleet" in q.lower() or "vehicle" in q.lower() for q in operational_questions):
        operational_questions.append("Any changes to the fleet — new vehicles, different drivers, expanded delivery radius?")

    if uses_subcontractors and not any("subcontract" in q.lower() for q in operational_questions):
        operational_questions.append("Any change in subcontractor usage or labor sourcing?")

    if annual_revenue and annual_revenue > 1_000_000:
        operational_questions.append("Has revenue changed materially? Liability limits and BI coverage should reflect current operations.")

    # --- Underwriting Flags ---
    underwriting_flags = list(_INDUSTRY_UNDERWRITING_FLAGS.get(industry, _GENERIC_UNDERWRITING_FLAGS))

    if experience_mod is not None and experience_mod > 1.0:
        flag = f"Experience mod of {experience_mod:.2f} will be scrutinized — prepare a loss narrative with corrective actions."
        if not any("mod" in f.lower() for f in underwriting_flags):
            underwriting_flags.insert(0, flag)

    if claims_summary:
        underwriting_flags.append("Active or recent claims history noted — ensure loss runs are current and narratives are ready.")

    if employee_count > 100:
        underwriting_flags.append("100+ employees — underwriters will expect a formal safety manual and dedicated safety personnel.")

    if uses_subcontractors and industry in INDUSTRY_GL_HEAVY:
        if not any("subcontract" in f.lower() for f in underwriting_flags):
            underwriting_flags.append("Subcontractor usage in a GL-heavy class triggers certificate compliance and risk transfer review.")

    # --- Loss run integration ---
    loss_run_data = profile.get("loss_run_data")
    if loss_run_data and isinstance(loss_run_data, dict):
        loss_patterns = loss_run_data.get("patterns", [])
        loss_flags = loss_run_data.get("underwriting_flags", [])
        loss_points = loss_run_data.get("producer_talking_points", [])

        # Inject loss-driven underwriting flags
        for flag in loss_flags[:2]:
            if flag not in underwriting_flags:
                underwriting_flags.insert(0, flag)

        # Inject loss-driven talking points as top questions
        for point in loss_points[:2]:
            if point not in top_questions:
                top_questions.append(point)

        # Inject loss pattern observations as coverage traps (near top for visibility)
        for pattern in reversed(loss_patterns[:2]):
            if pattern not in coverage_traps:
                coverage_traps.insert(0, pattern)

    # --- Experience mod integration ---
    experience_mod_data = profile.get("experience_mod_data")
    if experience_mod_data and isinstance(experience_mod_data, dict):
        mod_flags = experience_mod_data.get("flags", [])
        mod_points = experience_mod_data.get("talking_points", [])
        mod_trend = experience_mod_data.get("mod_trend")

        # Inject mod-driven underwriting flags
        for flag in mod_flags[:2]:
            if flag not in underwriting_flags:
                underwriting_flags.insert(0, flag)

        # Inject mod talking points as top questions
        for point in mod_points[:2]:
            if point not in top_questions:
                top_questions.append(point)

        # Add operational question if mod is worsening
        if mod_trend and isinstance(mod_trend, dict) and mod_trend.get("direction") == "worsening":
            worsening_q = (
                "Your experience mod is trending upward — what loss control changes "
                "have been implemented since the largest claim?"
            )
            if worsening_q not in operational_questions:
                operational_questions.insert(0, worsening_q)

    logger.info(
        "Producer ammo generated: top=%d traps=%d ops=%d flags=%d",
        len(top_questions), len(coverage_traps),
        len(operational_questions), len(underwriting_flags),
    )

    result = {
        "industry": industry_raw or industry,
        "account_stage": account_stage,
        "ammo_questions": {
            "top_questions": top_questions[:5],
            "coverage_traps": coverage_traps[:5],
            "operational_change_questions": operational_questions[:5],
            "underwriting_flags": underwriting_flags[:5],
        },
    }

    # Include tier enrichment when available
    if enrichment:
        result["tier_enrichment"] = {
            "wc_claims": tier_wc[:5],
            "gl_exposures": tier_gl[:5],
            "regional_notes": enrichment.get("regional_notes", ""),
            "display_name": enrichment.get("display_name", ""),
        }

    return result
