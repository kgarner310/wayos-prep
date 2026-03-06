"""Account Risk Scoring service.

Deterministic, explainable scoring framework that produces:
- exposure-based account scoring
- confidence-aware reasoning
- coverage gap alerts
- missing-information alerts
- structured explainability

NOT a pricing model, actuarial model, or underwriting engine.
"""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.models import (
    RiskScoreRun, RiskScoreComponent, CoverageGapAlert, MissingInformationAlert,
)
from app.services.graph_expansion import expand_risk_graph, get_expansion_seeds

logger = logging.getLogger(__name__)

SCORING_VERSION = "v1.0"

# ============================================================
# INDUSTRY BASELINE SCORES
# ============================================================
# Conservative heuristic baselines — not actuarial.
INDUSTRY_BASELINES = {
    "roofing": 62.0,
    "trucking": 60.0,
    "manufacturing": 48.0,
    "restaurant": 38.0,
    "landscaping": 45.0,
    "hvac": 50.0,
}
DEFAULT_INDUSTRY_BASELINE = 40.0

# Public entity baselines by department
DEPARTMENT_BASELINES = {
    "law_enforcement": 68.0,
    "fire_department": 55.0,
    "public_works": 52.0,
    "utilities": 48.0,
    "parks_recreation": 42.0,
    "administration": 45.0,
    "sanitation": 44.0,
    "street_maintenance": 50.0,
    "fleet_services": 52.0,
    "water_treatment": 46.0,
}
DEFAULT_PUBLIC_BASELINE = 45.0

# ============================================================
# TRAIT AMPLIFIERS
# ============================================================
TRAIT_AMPLIFIERS = {
    "uses_subcontractors": {"themes": ["subcontractor_transfer", "certificate_tracking"], "boost": 4.0},
    "young_fleet": {"themes": ["fleet_accidents", "fleet_liability"], "boost": 3.5},
    "high_mod": {"themes": ["falls_from_height", "fleet_accidents", "machine_guarding", "burns_and_scalds"], "boost": 3.0},
    "multi_state_operations": {"themes": ["compliance_complexity"], "boost": 2.5},
    "heavy_equipment": {"themes": ["struck_by_object", "machine_guarding"], "boost": 3.0},
    "residential_work": {"themes": ["falls_from_height"], "boost": 2.0},
    "habitational_exposure": {"themes": ["slip_and_fall"], "boost": 2.0},
    "delivery_operations": {"themes": ["fleet_accidents", "hired_non_owned_auto"], "boost": 3.0},
    "seasonal_payroll": {"themes": ["improper_classification"], "boost": 1.5},
    "high_turnover": {"themes": ["driver_turnover", "lifting_ergonomic"], "boost": 2.5},
}

# ============================================================
# COVERAGE GAP MAP: risk_theme -> required coverage
# ============================================================
COVERAGE_REQUIREMENTS = {
    "falls_from_height": ["workers_comp", "general_liability"],
    "fleet_accidents": ["commercial_auto", "umbrella"],
    "fleet_liability": ["municipal_auto"],
    "driver_turnover": ["commercial_auto"],
    "subcontractor_transfer": ["general_liability", "umbrella"],
    "machine_guarding": ["workers_comp"],
    "combustible_dust": ["property", "workers_comp"],
    "burns_and_scalds": ["workers_comp"],
    "slip_and_fall": ["general_liability"],
    "food_contamination": ["general_liability"],
    "heat_illness": ["workers_comp"],
    "chemical_exposure": ["workers_comp"],
    "hired_non_owned_auto": ["commercial_auto"],
    "police_liability": ["law_enforcement_liability"],
    "civil_rights_claims": ["law_enforcement_liability", "governmental_immunity"],
    "excessive_force": ["law_enforcement_liability"],
    "public_officials_liability": ["public_officials_liability_cov"],
    "road_maintenance_liability": ["general_liability"],
    "playground_injury": ["general_liability"],
    "public_event_liability": ["general_liability"],
    "sewer_backup_claims": ["environmental_liability_public"],
    "water_quality_claims": ["environmental_liability_public"],
    "volunteer_liability": ["general_liability", "workers_comp"],
    "cyber_records_breach": ["cyber"],
}

# ============================================================
# MISSING INFORMATION RULES
# ============================================================
MISSING_INFO_RULES = [
    {
        "field": "subcontractor_usage",
        "severity": "medium",
        "reason": "Subcontractor use materially affects risk transfer exposure",
        "question": "Do you subcontract any installation or tear-off work?",
        "relevant_industries": ["roofing", "hvac", "landscaping"],
        "relevant_traits": ["uses_subcontractors"],
    },
    {
        "field": "vehicle_count",
        "severity": "medium",
        "reason": "Vehicle fleet size determines auto liability exposure",
        "question": "How many vehicles are in your fleet, and who drives them?",
        "relevant_themes": ["fleet_accidents", "fleet_liability"],
    },
    {
        "field": "take_home_vehicles",
        "severity": "low",
        "reason": "Take-home vehicles expand hired/non-owned auto exposure",
        "question": "Do any employees take company vehicles home?",
        "relevant_themes": ["fleet_accidents", "hired_non_owned_auto"],
    },
    {
        "field": "osha_citation_history",
        "severity": "high",
        "reason": "OSHA citation history is a leading indicator of workplace safety culture",
        "question": "Has the company received any OSHA citations in the past 3 years?",
        "relevant_industries": ["roofing", "manufacturing", "trucking", "hvac"],
    },
    {
        "field": "playground_inspection_logs",
        "severity": "high",
        "reason": "Playground inspection compliance directly affects injury liability",
        "question": "How often are playground equipment inspections conducted and documented?",
        "relevant_departments": ["parks_recreation"],
    },
    {
        "field": "sewer_infrastructure_age",
        "severity": "medium",
        "reason": "Aging sewer infrastructure increases backup claim frequency",
        "question": "What percentage of sewer lines are past their expected useful life?",
        "relevant_departments": ["utilities", "public_works"],
    },
    {
        "field": "body_camera_policy",
        "severity": "high",
        "reason": "Body camera programs reduce civil rights claim costs and improve defense",
        "question": "Does the department operate body-worn cameras on all patrol officers?",
        "relevant_departments": ["law_enforcement"],
    },
    {
        "field": "use_of_force_policy_date",
        "severity": "high",
        "reason": "Outdated use-of-force policies increase excessive force liability",
        "question": "When was the department's use-of-force policy last reviewed and updated?",
        "relevant_departments": ["law_enforcement"],
    },
    {
        "field": "safety_program",
        "severity": "medium",
        "reason": "Formal safety programs reduce WC claim frequency",
        "question": "What is your current safety training program?",
        "relevant_industries": ["roofing", "manufacturing", "trucking", "landscaping", "hvac", "restaurant"],
    },
    {
        "field": "mvr_screening",
        "severity": "medium",
        "reason": "MVR screening prevents high-risk drivers from operating fleet vehicles",
        "question": "Do you run MVR checks on all drivers at hire and annually?",
        "relevant_themes": ["fleet_accidents", "fleet_liability", "driver_turnover"],
    },
]


# ============================================================
# LAYER A — BASE EXPOSURE SCORE
# ============================================================

def derive_base_exposure_score(
    industry: str,
    entity_type: str,
    department: str | None,
    retrieved_themes: list[dict],
    graph_themes: list[dict],
) -> tuple[float, list[dict]]:
    """Compute base exposure from industry/department baseline + risk themes.

    Returns (score, components list).
    """
    components = []

    # Start with industry/department baseline
    if entity_type == "public_entity" and department:
        baseline = DEPARTMENT_BASELINES.get(department, DEFAULT_PUBLIC_BASELINE)
        components.append({
            "type": "base_exposure", "key": f"department_baseline_{department}",
            "label": f"Department baseline ({department.replace('_', ' ').title()})",
            "raw": baseline, "weighted": baseline * 0.40,
            "explanation": f"Public entity department baseline for {department.replace('_', ' ')}",
        })
    else:
        baseline = INDUSTRY_BASELINES.get(industry.lower(), DEFAULT_INDUSTRY_BASELINE)
        components.append({
            "type": "base_exposure", "key": f"industry_baseline_{industry}",
            "label": f"Industry baseline ({industry.title()})",
            "raw": baseline, "weighted": baseline * 0.40,
            "explanation": f"Industry baseline for {industry}",
        })

    # Weight retrieved (source-backed) themes more heavily than graph-only
    theme_score = 0.0
    for theme in retrieved_themes:
        slug = theme.get("slug", "")
        strength = theme.get("strength", 0.5)
        contribution = strength * 15.0  # Max ~15 per theme
        theme_score += contribution
        components.append({
            "type": "base_exposure", "key": f"retrieved_theme_{slug}",
            "label": slug.replace("_", " ").title(),
            "raw": strength, "weighted": round(contribution, 2),
            "explanation": f"Source-supported risk theme (strength={strength:.2f})",
        })

    # Graph-expanded themes contribute less (0.5x weight)
    for theme in graph_themes:
        name = theme.get("name", "")
        weight = theme.get("weight", 0.3)
        if theme.get("node_type") != "risk_theme":
            continue
        # Skip if already in retrieved themes
        if any(t.get("slug") == name for t in retrieved_themes):
            continue
        contribution = weight * 7.5  # Max ~7.5 per graph theme
        theme_score += contribution
        components.append({
            "type": "base_exposure", "key": f"graph_theme_{name}",
            "label": name.replace("_", " ").title(),
            "raw": weight, "weighted": round(contribution, 2),
            "explanation": f"Graph-expanded risk theme (weight={weight:.2f})",
        })

    # Combine baseline (40%) + theme contributions (60%), capped
    score = baseline * 0.40 + min(theme_score, 60.0)
    return round(score, 2), components


# ============================================================
# LAYER B — TRAIT AMPLIFIERS
# ============================================================

def apply_trait_amplifiers(
    account_traits: list[str],
    active_themes: set[str],
) -> tuple[float, list[dict]]:
    """Amplify score based on account traits that elevate specific risks."""
    total_boost = 0.0
    components = []

    for trait in account_traits:
        amp = TRAIT_AMPLIFIERS.get(trait)
        if not amp:
            continue
        # Boost is stronger if the trait's related themes are already active
        overlapping = [t for t in amp["themes"] if t in active_themes]
        if overlapping:
            boost = amp["boost"]
            total_boost += boost
            components.append({
                "type": "trait_amplifier", "key": f"trait_{trait}",
                "label": trait.replace("_", " ").title(),
                "raw": amp["boost"], "weighted": round(boost, 2),
                "explanation": f"Trait '{trait}' amplifies {', '.join(overlapping)}",
            })
        else:
            # Partial boost even without theme overlap
            boost = amp["boost"] * 0.3
            total_boost += boost
            components.append({
                "type": "trait_amplifier", "key": f"trait_{trait}",
                "label": trait.replace("_", " ").title(),
                "raw": amp["boost"], "weighted": round(boost, 2),
                "explanation": f"Trait '{trait}' present but related themes not retrieved",
            })

    return round(min(total_boost, 15.0), 2), components


# ============================================================
# LAYER C — ACCOUNT DETAIL MODIFIERS
# ============================================================

def apply_account_detail_modifiers(
    employee_count: int,
    current_mod: float | None,
    department: str | None,
    entity_type: str,
) -> tuple[float, list[dict]]:
    """Adjust score for account-level details."""
    modifier = 0.0
    components = []

    # Employee count — gradual complexity scaling
    if employee_count > 100:
        emp_mod = 4.0
        explanation = "Large operation (100+ employees) — elevated operational complexity"
    elif employee_count > 50:
        emp_mod = 2.5
        explanation = "Mid-size operation (50-100 employees)"
    elif employee_count > 25:
        emp_mod = 1.0
        explanation = "Growing operation (25-50 employees)"
    else:
        emp_mod = 0.0
        explanation = "Small operation — minimal size-based adjustment"

    if emp_mod > 0:
        modifier += emp_mod
        components.append({
            "type": "account_detail", "key": "employee_count",
            "label": f"Employee Count ({employee_count})",
            "raw": float(employee_count), "weighted": emp_mod,
            "explanation": explanation,
        })

    # Current mod
    if current_mod is not None:
        if current_mod > 1.20:
            mod_adj = 5.0
            explanation = f"High mod ({current_mod:.3f}) — significant loss history"
        elif current_mod > 1.00:
            mod_adj = 2.5
            explanation = f"Above-unity mod ({current_mod:.3f}) — loss history concern"
        elif current_mod < 0.80:
            mod_adj = -3.0
            explanation = f"Low mod ({current_mod:.3f}) — favorable loss history"
        elif current_mod < 1.00:
            mod_adj = -1.0
            explanation = f"Below-unity mod ({current_mod:.3f}) — slightly favorable"
        else:
            mod_adj = 0.0
            explanation = f"Unity mod ({current_mod:.3f}) — neutral"

        if mod_adj != 0:
            modifier += mod_adj
            components.append({
                "type": "account_detail", "key": "current_mod",
                "label": f"Experience Mod ({current_mod:.3f})",
                "raw": current_mod, "weighted": mod_adj,
                "explanation": explanation,
            })

    return round(modifier, 2), components


# ============================================================
# LAYER D — EVIDENCE CONFIDENCE
# ============================================================

def calculate_confidence_score(
    source_confidence: float,
    retrieved_theme_count: int,
    question_signal_count: int,
    graph_support_count: int,
) -> tuple[float, list[str]]:
    """Calculate a confidence score (0-100) based on evidence quality."""
    notes = []

    # Source confidence (40% weight)
    source_component = source_confidence * 40.0

    # Theme coverage (25% weight)
    theme_component = min(retrieved_theme_count / 5.0, 1.0) * 25.0
    if retrieved_theme_count < 2:
        notes.append("Limited source-backed risk themes — score may understate exposure")
    elif retrieved_theme_count >= 4:
        notes.append("Score supported by multiple source-backed risk themes")

    # Question coverage (15% weight)
    question_component = min(question_signal_count / 4.0, 1.0) * 15.0

    # Graph support (20% weight)
    graph_component = min(graph_support_count / 8.0, 1.0) * 20.0
    if graph_support_count >= 5:
        notes.append("Strong graph support for risk theme connections")

    confidence = source_component + theme_component + question_component + graph_component
    confidence = round(min(max(confidence, 5.0), 100.0), 1)

    if confidence < 40:
        notes.append("Low overall confidence — additional sources and information needed")
    elif confidence < 60:
        notes.append("Moderate confidence — state-specific or domain-specific sources would improve")

    return confidence, notes


# ============================================================
# LAYER E — COVERAGE GAP DETECTION
# ============================================================

def detect_coverage_gaps(
    active_themes: set[str],
    known_coverages: list[str],
    theme_strengths: dict[str, float],
) -> list[dict]:
    """Detect coverage gaps where strong risk themes lack corresponding coverage."""
    gaps = []
    known_set = set(c.lower() for c in known_coverages)

    for theme, required_coverages in COVERAGE_REQUIREMENTS.items():
        if theme not in active_themes:
            continue
        strength = theme_strengths.get(theme, 0.3)
        for coverage in required_coverages:
            if coverage not in known_set:
                severity = "high" if strength >= 0.7 else "medium" if strength >= 0.4 else "low"
                gaps.append({
                    "risk_theme": theme,
                    "suggested_coverage": coverage,
                    "alert_severity": severity,
                    "alert_reason": (
                        f"{theme.replace('_', ' ').title()} exposure appears present "
                        f"(strength={strength:.2f}) but {coverage.replace('_', ' ')} "
                        f"coverage is missing or unknown"
                    ),
                })

    # Deduplicate by (theme, coverage)
    seen = set()
    unique_gaps = []
    for g in gaps:
        key = (g["risk_theme"], g["suggested_coverage"])
        if key not in seen:
            seen.add(key)
            unique_gaps.append(g)

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    unique_gaps.sort(key=lambda g: severity_order.get(g["alert_severity"], 3))
    return unique_gaps[:10]


# ============================================================
# LAYER F — MISSING INFORMATION ALERTS
# ============================================================

def detect_missing_information(
    industry: str,
    entity_type: str,
    department: str | None,
    account_traits: list[str],
    active_themes: set[str],
) -> list[dict]:
    """Detect important missing information that would improve scoring."""
    alerts = []

    for rule in MISSING_INFO_RULES:
        relevant = False

        # Check industry relevance
        if "relevant_industries" in rule and industry.lower() in rule["relevant_industries"]:
            relevant = True

        # Check department relevance
        if "relevant_departments" in rule and department and department in rule["relevant_departments"]:
            relevant = True

        # Check trait relevance
        if "relevant_traits" in rule:
            if any(t in account_traits for t in rule["relevant_traits"]):
                relevant = True

        # Check theme relevance
        if "relevant_themes" in rule:
            if any(t in active_themes for t in rule["relevant_themes"]):
                relevant = True

        if relevant:
            alerts.append({
                "missing_field": rule["field"],
                "alert_severity": rule["severity"],
                "alert_reason": rule["reason"],
                "recommended_question": rule.get("question"),
            })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a["alert_severity"], 3))
    return alerts[:8]


# ============================================================
# RISK BAND ASSIGNMENT
# ============================================================

def assign_risk_band(score: float) -> str:
    """Assign risk band from clamped score."""
    if score < 25:
        return "low"
    elif score < 50:
        return "moderate"
    elif score < 75:
        return "elevated"
    else:
        return "high"


# ============================================================
# ORCHESTRATOR
# ============================================================

def score_account(
    db: Session,
    industry: str,
    state: str,
    employee_count: int = 10,
    current_mod: float | None = None,
    entity_type: str = "private_business",
    public_entity_type: str | None = None,
    department: str | None = None,
    account_traits: list[str] | None = None,
    retrieved_risk_themes: list[dict] | None = None,
    known_coverages: list[str] | None = None,
    question_signals: list[dict] | None = None,
    source_confidence: float = 0.5,
    query_id=None,
    brief_id=None,
) -> dict:
    """Run the full scoring pipeline and return structured result.

    Returns the RiskScoreOutput-compatible dict.
    """
    account_traits = account_traits or []
    retrieved_risk_themes = retrieved_risk_themes or []
    known_coverages = known_coverages or []
    question_signals = question_signals or []

    # Graph expansion for additional context
    seeds = get_expansion_seeds(
        industry=industry,
        state=state,
        entity_type=entity_type,
        public_entity_type=public_entity_type,
        department=department,
        account_traits=account_traits,
    )
    graph_result = expand_risk_graph(db, seeds, depth=1)
    graph_themes = graph_result.get("expanded_themes", [])

    # Build active theme set (all themes in play)
    active_themes = set()
    theme_strengths = {}
    for t in retrieved_risk_themes:
        slug = t.get("slug", "")
        active_themes.add(slug)
        theme_strengths[slug] = t.get("strength", 0.5)
    for t in graph_themes:
        if t.get("node_type") == "risk_theme":
            name = t.get("name", "")
            active_themes.add(name)
            if name not in theme_strengths:
                theme_strengths[name] = t.get("weight", 0.3) * 0.5  # Graph themes lower strength

    # Layer A — Base exposure
    base_score, base_components = derive_base_exposure_score(
        industry=industry,
        entity_type=entity_type,
        department=department,
        retrieved_themes=retrieved_risk_themes,
        graph_themes=graph_themes,
    )

    # Layer B — Trait amplifiers
    trait_score, trait_components = apply_trait_amplifiers(
        account_traits=account_traits,
        active_themes=active_themes,
    )

    # Layer C — Account detail modifiers
    detail_score, detail_components = apply_account_detail_modifiers(
        employee_count=employee_count,
        current_mod=current_mod,
        department=department,
        entity_type=entity_type,
    )

    # Final adjusted score (clamped 0-100)
    final_score = round(min(max(base_score + trait_score + detail_score, 0.0), 100.0), 1)
    risk_band = assign_risk_band(final_score)

    # Layer D — Confidence
    confidence, confidence_notes = calculate_confidence_score(
        source_confidence=source_confidence,
        retrieved_theme_count=len(retrieved_risk_themes),
        question_signal_count=len(question_signals),
        graph_support_count=len(graph_themes),
    )

    # Layer E — Coverage gaps
    coverage_gaps = detect_coverage_gaps(
        active_themes=active_themes,
        known_coverages=known_coverages,
        theme_strengths=theme_strengths,
    )

    # Layer F — Missing information
    missing_info = detect_missing_information(
        industry=industry,
        entity_type=entity_type,
        department=department,
        account_traits=account_traits,
        active_themes=active_themes,
    )

    # Top risk themes (sorted by contribution)
    all_theme_components = [
        c for c in base_components
        if c["type"] == "base_exposure" and c["key"].startswith(("retrieved_theme_", "graph_theme_"))
    ]
    all_theme_components.sort(key=lambda c: c["weighted"], reverse=True)
    top_risk_themes = [
        {
            "risk_theme": c["key"].replace("retrieved_theme_", "").replace("graph_theme_", ""),
            "score_contribution": c["weighted"],
            "reason": c["explanation"],
        }
        for c in all_theme_components[:5]
    ]

    # All components
    all_components = base_components + trait_components + detail_components

    # Build result
    result = {
        "overall_risk_score": final_score,
        "risk_band": risk_band,
        "confidence_score": confidence,
        "top_risk_themes": top_risk_themes,
        "coverage_gap_alerts": coverage_gaps,
        "missing_information_alerts": missing_info,
        "score_explanation": {
            "base_exposure_score": base_score,
            "trait_amplifier_score": trait_score,
            "account_detail_modifier_score": detail_score,
            "final_adjusted_score": final_score,
            "confidence_notes": confidence_notes,
        },
        "components": [
            {
                "component_type": c["type"],
                "component_key": c["key"],
                "component_label": c.get("label"),
                "raw_value": c.get("raw"),
                "weighted_value": c.get("weighted"),
                "explanation": c.get("explanation"),
            }
            for c in all_components
        ],
    }

    # Persist to database
    score_run = RiskScoreRun(
        query_id=query_id,
        brief_id=brief_id,
        scoring_version=SCORING_VERSION,
        overall_risk_score=Decimal(str(final_score)),
        risk_band=risk_band,
        confidence_score=Decimal(str(confidence)),
        score_json=result,
    )
    db.add(score_run)
    db.flush()

    # Persist components
    for c in all_components:
        comp = RiskScoreComponent(
            risk_score_run_id=score_run.id,
            component_type=c["type"],
            component_key=c["key"],
            component_label=c.get("label"),
            raw_value=Decimal(str(c["raw"])) if c.get("raw") is not None else None,
            weighted_value=Decimal(str(c["weighted"])) if c.get("weighted") is not None else None,
            explanation=c.get("explanation"),
        )
        db.add(comp)

    # Persist coverage gaps
    for gap in coverage_gaps:
        alert = CoverageGapAlert(
            risk_score_run_id=score_run.id,
            risk_theme=gap["risk_theme"],
            suggested_coverage=gap["suggested_coverage"],
            alert_severity=gap["alert_severity"],
            alert_reason=gap["alert_reason"],
        )
        db.add(alert)

    # Persist missing info
    for mi in missing_info:
        alert = MissingInformationAlert(
            risk_score_run_id=score_run.id,
            missing_field=mi["missing_field"],
            alert_severity=mi["alert_severity"],
            alert_reason=mi["alert_reason"],
            recommended_question=mi.get("recommended_question"),
        )
        db.add(alert)

    db.commit()
    db.refresh(score_run)

    result["risk_score_run_id"] = str(score_run.id)
    return result
