"""Producer Ammo — sharp, meeting-ready talking points for producers.

Generates deterministic, specific ammo organized into:
- renewal_pressure_points: leverage for renewal conversations
- underwriting_hot_buttons: what underwriters will focus on
- cross_sell_openings: account-rounding and new line opportunities
- hard_questions_to_ask: direct, specific questions that show expertise

NOT generic conversation starters. These should feel usable in a real meeting.
"""

import logging

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
