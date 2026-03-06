from datetime import datetime, timezone


def _bullets(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def _val_or_na(val) -> str:
    if val is None or val == "":
        return "N/A"
    return str(val)


DOCS_TO_REQUEST = [
    "Loss runs (5 yrs) + claim narratives",
    "Payroll by class code / subcontractor usage",
    "Auto schedule + driver list + MVR policy",
    "Certificates / contractual requirements if applicable",
]


def build_brief_json(
    industry_name: str,
    location: str,
    employee_count: int | None,
    mod: float | None,
    vehicle_exposure: str | None,
    top_claims: list[str],
    regional_notes: str,
    coverage_exposures: list[str],
    conversation_starters: list[str],
    state_wc_notes: str | None = None,
    state_compliance_items: list[str] | None = None,
    tort_environment: str | None = None,
    cat_exposures: list[str] | None = None,
) -> dict:
    result = {
        "industry": industry_name,
        "location": location,
        "employee_count": employee_count,
        "mod": mod,
        "vehicle_exposure": vehicle_exposure,
        "generated_at": datetime.now(timezone.utc).strftime("%B %d, %Y %I:%M %p UTC"),
        "top_claim_drivers": top_claims,
        "regional_risk_notes": regional_notes,
        "coverage_exposures": coverage_exposures,
        "conversation_starters": conversation_starters,
        "docs_to_request": DOCS_TO_REQUEST,
    }

    if state_wc_notes:
        result["state_wc_notes"] = state_wc_notes
    if state_compliance_items:
        result["state_compliance_items"] = state_compliance_items
    if tort_environment:
        result["tort_environment"] = tort_environment
    if cat_exposures:
        result["cat_exposures"] = cat_exposures

    return result


def _render_state_sections(bj: dict) -> str:
    """Render state-specific sections if state data is present."""
    sections = []

    if bj.get("state_wc_notes"):
        sections.append(f"STATE WORKERS COMP NOTES\n\n{bj['state_wc_notes']}")

    if bj.get("cat_exposures"):
        sections.append(f"CATASTROPHE EXPOSURES\n\n{_bullets(bj['cat_exposures'])}")

    if bj.get("state_compliance_items"):
        sections.append(f"STATE-SPECIFIC COMPLIANCE\n\n{_bullets(bj['state_compliance_items'])}")

    if bj.get("tort_environment"):
        sections.append(f"TORT ENVIRONMENT: {bj['tort_environment'].upper()}")

    return "\n\n".join(sections)


def render_brief_text(brief_json: dict, metadata: dict | None = None) -> str:
    bj = brief_json

    state_block = _render_state_sections(bj)
    state_section = f"\n\n{state_block}" if state_block else ""

    return f"""WAYOS PREP — CLIENT BRIEF

Industry: {bj['industry']}
Location: {bj['location']}
Employees: {_val_or_na(bj.get('employee_count'))}  MOD: {_val_or_na(bj.get('mod'))}  Vehicle Exposure: {_val_or_na(bj.get('vehicle_exposure'))}
Generated: {bj['generated_at']}

─────────────────────────────────────

TOP CLAIM DRIVERS (what actually hurts)

{_bullets(bj['top_claim_drivers'])}

REGIONAL / LOCAL RISK NOTES

{bj['regional_risk_notes']}

COVERAGE EXPOSURES (what to stress-test)

{_bullets(bj['coverage_exposures'])}{state_section}

CONVERSATION STARTERS (producer ammo)

{_bullets(bj['conversation_starters'])}

QUICK DOCS TO REQUEST

{_bullets(bj['docs_to_request'])}

─────────────────────────────────────
Prepared with WAYOS PREP • wayosprep.app • "Better meetings. Better coverage.\""""


def render_underwriter_email(brief_json: dict) -> str:
    bj = brief_json

    state_lines = ""
    if bj.get("state_wc_notes"):
        state_lines += f"\nSTATE WC NOTES\n{bj['state_wc_notes']}\n"
    if bj.get("state_compliance_items"):
        state_lines += f"\nKEY COMPLIANCE ITEMS\n{_bullets(bj['state_compliance_items'])}\n"

    return f"""Subject: {bj['industry']} Risk Notes and Questions

Hi,

I'm preparing for a meeting with a {bj['industry']} operation in {bj['location']} (approx {_val_or_na(bj.get('employee_count'))} employees, MOD {_val_or_na(bj.get('mod'))}).

Before finalizing markets or coverage structure I wanted to flag the major exposure areas and confirm underwriting expectations.

TOP CLAIM DRIVERS
{_bullets(bj['top_claim_drivers'])}

REGIONAL RISK NOTES
{bj['regional_risk_notes']}

COVERAGE EXPOSURES
{_bullets(bj['coverage_exposures'])}
{state_lines}
QUESTIONS I PLAN TO ASK
{_bullets(bj['conversation_starters'])}

DOCUMENTS I WILL REQUEST
• Loss runs (5 yrs) + narratives
• Payroll by class code / subcontractor usage
• Auto schedule + driver list + MVR policy
• Contracts or certificates if applicable

Prepared with WAYOS PREP • wayosprep.app"""


def render_internal_note(brief_json: dict) -> str:
    bj = brief_json

    compliance_block = ""
    if bj.get("state_compliance_items"):
        compliance_block = f"\n\nCompliance watch\n{_bullets(bj['state_compliance_items'])}"

    return f"""WAYOS PREP — ACCOUNT PREP

Industry: {bj['industry']}
Location: {bj['location']}

Big exposures
{_bullets(bj['coverage_exposures'])}

Claim patterns
{_bullets(bj['top_claim_drivers'])}

Questions for insured
{_bullets(bj['conversation_starters'])}
{compliance_block}
Docs to request
• Loss runs
• Payroll by class code
• Auto schedule + drivers
• Certificates or contracts

Prepared with WAYOS PREP • wayosprep.app"""
