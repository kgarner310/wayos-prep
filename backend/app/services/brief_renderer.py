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
    location_intel: dict | None = None,
    loss_run_data: dict | None = None,
    mod_data: dict | None = None,
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
    if location_intel:
        result["location_intel"] = location_intel
    if loss_run_data:
        result["loss_run_summary"] = _build_loss_run_summary(loss_run_data)
    if mod_data:
        result["mod_summary"] = _build_mod_summary(mod_data)

    return result


def _build_loss_run_summary(data: dict) -> dict:
    """Extract key loss run metrics for the brief."""
    totals = data.get("totals", {})
    return {
        "overall_loss_ratio": totals.get("loss_ratio"),
        "total_premium": totals.get("premium"),
        "total_incurred": totals.get("incurred"),
        "total_claims": totals.get("claims"),
        "flags": data.get("flags", []),
        "talking_points": data.get("talking_points", []),
        "line_summaries": [
            {
                "line": s.get("line"),
                "loss_ratio": s.get("loss_ratio"),
                "num_claims": s.get("num_claims"),
            }
            for s in data.get("line_summaries", [])
        ],
    }


def _build_mod_summary(data: dict) -> dict:
    """Extract key mod metrics for the brief."""
    return {
        "current_mod": data.get("current_mod"),
        "prior_mod": data.get("prior_mod"),
        "mod_trend": data.get("mod_trend"),
        "flags": data.get("flags", []),
        "insights": data.get("insights", []),
        "talking_points": data.get("talking_points", []),
    }


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


def _render_location_intel(bj: dict) -> str:
    """Render location intelligence from public data sources."""
    intel = bj.get("location_intel")
    if not intel:
        return ""

    sections = []

    # Header with geocoded address
    if intel.get("geocoded_address"):
        sections.append(f"LOCATION INTELLIGENCE — {intel['geocoded_address']}")
    else:
        sections.append("LOCATION INTELLIGENCE")

    # Natural hazards summary
    hazard_lines = []
    if intel.get("flood_zone"):
        risk = intel.get("flood_risk", "unknown")
        hazard_lines.append(f"Flood Zone: {intel['flood_zone']} ({risk} risk)")
    if intel.get("seismic_risk"):
        hazard_lines.append(f"Seismic: {intel['seismic_risk']} risk")
    if intel.get("wildfire_risk"):
        hazard_lines.append(f"Wildfire: {intel['wildfire_risk']} hazard")
    if intel.get("tornado_risk"):
        hazard_lines.append(f"Tornado: {intel['tornado_risk']} risk")
    if intel.get("hail_risk"):
        hazard_lines.append(f"Hail: {intel['hail_risk']} risk")
    if intel.get("hurricane_risk"):
        hazard_lines.append(f"Hurricane: {intel['hurricane_risk']} risk")

    if hazard_lines:
        sections.append("Natural Hazards\n" + "\n".join(f"  {h}" for h in hazard_lines))

    # Location-specific hazard alerts
    if intel.get("location_hazards"):
        sections.append("Hazard Alerts\n" + _bullets(intel["location_hazards"]))

    # OSHA
    if intel.get("osha_top_citations"):
        osha_block = "OSHA — Top Cited Standards\n" + _bullets(intel["osha_top_citations"])
        if intel.get("osha_inspection_summary"):
            osha_block += f"\n  Recent activity: {intel['osha_inspection_summary']}"
        sections.append(osha_block)

    # Economic
    econ_lines = []
    if intel.get("county_employment"):
        econ_lines.append(f"County employment: {intel['county_employment']:,}")
    if intel.get("county_establishments"):
        econ_lines.append(f"Establishments: {intel['county_establishments']:,}")
    if intel.get("county_avg_weekly_wage"):
        econ_lines.append(f"Avg weekly wage: ${intel['county_avg_weekly_wage']:,}")
    if intel.get("county_top_industries"):
        econ_lines.append("Top sectors:\n" + _bullets(intel["county_top_industries"]))

    if econ_lines:
        sections.append("Market / Economic Data\n" + "\n".join(f"  {e}" for e in econ_lines[:3]))
        if intel.get("county_top_industries"):
            sections.append("County Industry Mix\n" + _bullets(intel["county_top_industries"]))

    # Data sources attribution
    if intel.get("data_sources"):
        sources = ", ".join(intel["data_sources"])
        query_ms = intel.get("query_time_ms", 0)
        sections.append(f"Sources: {sources} ({query_ms}ms)")

    return "\n\n".join(sections)


def _render_loss_run_section(bj: dict) -> str:
    """Render loss run summary if present in brief."""
    lr = bj.get("loss_run_summary")
    if not lr:
        return ""

    lines = ["LOSS RUN SUMMARY"]
    lines.append("")

    ratio = lr.get("overall_loss_ratio")
    if ratio is not None:
        lines.append(f"  Overall Loss Ratio: {ratio:.0%}")
    if lr.get("total_premium"):
        lines.append(f"  Total Premium: ${lr['total_premium']:,.0f}")
    if lr.get("total_incurred"):
        lines.append(f"  Total Incurred: ${lr['total_incurred']:,.0f}")
    if lr.get("total_claims"):
        lines.append(f"  Total Claims: {lr['total_claims']}")

    # Per-line highlights
    problem_lines = [
        s for s in lr.get("line_summaries", [])
        if s.get("loss_ratio") is not None and s["loss_ratio"] > 0.60
    ]
    if problem_lines:
        lines.append("")
        lines.append("  Problem Lines:")
        for s in problem_lines:
            lines.append(f"    {s['line']}: {s['loss_ratio']:.0%} loss ratio ({s.get('num_claims', '?')} claims)")

    flags = lr.get("flags", [])
    if flags:
        lines.append("")
        for f in flags[:3]:
            lines.append(f"  ! {f}")

    return "\n".join(lines)


def _render_mod_section(bj: dict) -> str:
    """Render mod summary if present in brief."""
    ms = bj.get("mod_summary")
    if not ms:
        return ""

    lines = ["EXPERIENCE MOD SUMMARY"]
    lines.append("")

    if ms.get("current_mod") is not None:
        lines.append(f"  Current Mod: {ms['current_mod']:.2f}")
    if ms.get("prior_mod") is not None:
        lines.append(f"  Prior Mod: {ms['prior_mod']:.2f}")

    trend = ms.get("mod_trend")
    if trend:
        lines.append(f"  Trend: {trend['direction'].upper()} ({trend['change']:+.2f})")

    flags = ms.get("flags", [])
    if flags:
        lines.append("")
        for f in flags[:3]:
            lines.append(f"  ! {f}")

    insights = ms.get("insights", [])
    if insights:
        lines.append("")
        for i in insights[:2]:
            lines.append(f"  + {i}")

    return "\n".join(lines)


def render_brief_text(brief_json: dict, metadata: dict | None = None) -> str:
    bj = brief_json

    state_block = _render_state_sections(bj)
    state_section = f"\n\n{state_block}" if state_block else ""

    intel_block = _render_location_intel(bj)
    intel_section = f"\n\n{intel_block}" if intel_block else ""

    lr_block = _render_loss_run_section(bj)
    lr_section = f"\n\n{lr_block}" if lr_block else ""

    mod_block = _render_mod_section(bj)
    mod_section = f"\n\n{mod_block}" if mod_block else ""

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

{_bullets(bj['coverage_exposures'])}{state_section}{intel_section}{lr_section}{mod_section}

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

    # Location intel for underwriter
    intel_lines = ""
    intel = bj.get("location_intel")
    if intel:
        parts = []
        if intel.get("flood_zone"):
            parts.append(f"Flood Zone: {intel['flood_zone']} ({intel.get('flood_risk', 'unknown')} risk)")
        if intel.get("seismic_risk") and intel["seismic_risk"] != "low":
            parts.append(f"Seismic risk: {intel['seismic_risk']}")
        if intel.get("wildfire_risk") and intel["wildfire_risk"] not in ("very low", "low", "unknown"):
            parts.append(f"Wildfire hazard: {intel['wildfire_risk']}")
        if intel.get("osha_top_citations"):
            parts.append("Top OSHA citations: " + ", ".join(
                s.split(" — ")[0] for s in intel["osha_top_citations"][:3]
            ))
        if parts:
            intel_lines = "\nLOCATION DATA (public sources)\n" + _bullets(parts) + "\n"

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
{state_lines}{intel_lines}
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

    # Location intel summary for CSR
    intel_block = ""
    intel = bj.get("location_intel")
    if intel:
        lines = []
        if intel.get("flood_zone"):
            lines.append(f"Flood: Zone {intel['flood_zone']} ({intel.get('flood_risk', '?')})")
        if intel.get("wildfire_risk") and intel["wildfire_risk"] not in ("very low", "low", "unknown"):
            lines.append(f"Wildfire: {intel['wildfire_risk']}")
        if intel.get("location_hazards"):
            lines.extend(intel["location_hazards"][:2])
        if lines:
            intel_block = f"\n\nLocation flags\n{_bullets(lines)}"

    return f"""WAYOS PREP — ACCOUNT PREP

Industry: {bj['industry']}
Location: {bj['location']}

Big exposures
{_bullets(bj['coverage_exposures'])}

Claim patterns
{_bullets(bj['top_claim_drivers'])}

Questions for insured
{_bullets(bj['conversation_starters'])}
{compliance_block}{intel_block}
Docs to request
• Loss runs
• Payroll by class code
• Auto schedule + drivers
• Certificates or contracts

Prepared with WAYOS PREP • wayosprep.app"""
