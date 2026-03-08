"""Artifact Engine — unified artifact generation with dispatch, validation, and fallback.

Generates structured artifacts for accounts using deterministic scoring
plus optional LLM enrichment. Each artifact type has a strict schema.
"""

import json
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import Account, SavedArtifact
from app.schemas.artifact_schemas import (
    ARTIFACT_PRIORITY,
    ARTIFACT_SCHEMA_MAP,
    CoverageGapArtifact,
    MeetingBriefArtifact,
    WorkersCompSnapshotArtifact,
    WinnabilityArtifact,
)
from app.services.coverage_gap_detector import detect_gaps
from app.services.meeting_brief import generate_meeting_brief
from app.services.prompt_service import build_artifact_prompt

logger = logging.getLogger(__name__)


def _account_to_dict(account: Account) -> dict:
    """Convert Account ORM model to dict for prompt building."""
    return {
        "account_name": account.account_name,
        "named_insured": account.named_insured,
        "industry": account.industry,
        "state": account.state,
        "employee_count": account.employee_count,
        "annual_revenue": float(account.annual_revenue) if account.annual_revenue else None,
        "payroll_estimate": float(account.payroll_estimate) if account.payroll_estimate else None,
        "vehicle_count": account.vehicle_count,
        "uses_subcontractors": account.uses_subcontractors,
        "current_coverages": account.current_coverages or [],
        "current_carriers": account.current_carriers or [],
        "workers_comp_mod": float(account.workers_comp_mod) if account.workers_comp_mod else None,
        "claims_summary": account.claims_summary,
        "notes": account.notes,
    }


# ============================================================
# DETERMINISTIC GENERATORS (fast path)
# ============================================================


def _generate_coverage_gap_deterministic(account: Account) -> dict:
    """Generate coverage gap artifact using existing deterministic detector."""
    industry = (account.industry or "").lower()
    state = (account.state or "").upper() or "OH"
    mod = float(account.workers_comp_mod) if account.workers_comp_mod else None

    gaps_raw = detect_gaps(
        industry=industry or "general",
        state=state,
        employee_count=account.employee_count or 10,
        current_mod=mod,
        known_coverages=account.current_coverages,
        account_traits=["uses_subcontractors"] if account.uses_subcontractors else [],
    )

    # Map to artifact schema
    gap_titles = [g["title"] for g in gaps_raw]
    recommended = list(set(g.get("suggested_coverage_or_action", "") for g in gaps_raw if g.get("suggested_coverage_or_action")))
    duty_flags = [g["title"] for g in gaps_raw if g.get("severity") == "high"]
    talking_points = [g.get("suggested_question", "") for g in gaps_raw if g.get("suggested_question")]

    # Determine risk level
    high_count = sum(1 for g in gaps_raw if g.get("severity") == "high")
    if high_count >= 3:
        risk_level = "high"
    elif high_count >= 1:
        risk_level = "elevated"
    elif len(gaps_raw) >= 2:
        risk_level = "moderate"
    elif gaps_raw:
        risk_level = "low"
    else:
        risk_level = "low"

    return CoverageGapArtifact(
        risk_level=risk_level,
        gaps=gap_titles,
        recommended_coverages=recommended[:5],
        duty_to_advise_flags=duty_flags[:5],
        producer_talking_points=talking_points[:5],
        unknowns=["Full policy schedule not available"] if not account.current_coverages else [],
    ).model_dump()


def _generate_meeting_brief_deterministic(account: Account) -> dict:
    """Generate meeting brief using existing industry profiles."""
    industry = (account.industry or "").lower()
    brief_data = generate_meeting_brief(industry)

    # Map to artifact schema
    name = account.named_insured or account.account_name
    summary_parts = [f"{name}"]
    if industry:
        summary_parts.append(f"({industry})")
    if account.state:
        summary_parts.append(f"in {account.state}")
    if account.employee_count:
        summary_parts.append(f"with {account.employee_count} employees")

    return MeetingBriefArtifact(
        client_summary=" ".join(summary_parts),
        key_risks=brief_data.get("top_exposures", [])[:5],
        coverage_concerns=brief_data.get("coverage_watchouts", [])[:5],
        questions_for_client=brief_data.get("discovery_questions", [])[:5],
        conversation_strategy=brief_data.get("recommended_talking_points", [])[:5],
    ).model_dump()


def _generate_workers_comp_deterministic(account: Account) -> dict:
    """Generate workers comp snapshot from account data."""
    mod = float(account.workers_comp_mod) if account.workers_comp_mod else None
    industry = (account.industry or "").lower()

    # Industry average mods
    avg_mods = {
        "roofing": "1.08", "trucking": "1.05", "manufacturing": "0.98",
        "restaurant": "0.95", "landscaping": "0.97", "hvac": "1.02",
    }
    industry_avg = avg_mods.get(industry, "unknown")

    # Premium signal
    if mod is None:
        premium_signal = "unknown"
    elif mod <= 0.85:
        premium_signal = "favorable"
    elif mod <= 1.05:
        premium_signal = "stable"
    else:
        premium_signal = "unfavorable"

    # Risk drivers
    risk_drivers = []
    unknowns = []

    if mod is not None and mod > 1.0:
        risk_drivers.append(f"Mod of {mod:.2f} indicates loss experience above class average")
    if mod is None:
        unknowns.append("Experience mod not provided")

    claims = account.claims_summary or {}
    if claims.get("total_claims_3yr"):
        risk_drivers.append(f"{claims['total_claims_3yr']} claims in last 3 years")
    if claims.get("open_claims"):
        risk_drivers.append(f"{claims['open_claims']} open claim(s)")
    if not claims:
        unknowns.append("Claims history not available")

    if account.uses_subcontractors:
        risk_drivers.append("Subcontractor exposure may affect WC classification")

    # Improvement opportunities
    improvements = []
    if mod is not None and mod > 1.0:
        improvements.append("Implement or strengthen formal safety program")
        improvements.append("Review return-to-work protocols")
    if account.employee_count and account.employee_count >= 50:
        improvements.append("Consider large deductible or retrospective rating plan")
    improvements.append("Request loss runs for detailed claims analysis")

    return WorkersCompSnapshotArtifact(
        mod=f"{mod:.2f}" if mod is not None else "unknown",
        industry_average_mod=industry_avg,
        premium_signal=premium_signal,
        risk_drivers=risk_drivers[:5],
        improvement_opportunities=improvements[:5],
        unknowns=unknowns,
    ).model_dump()


def _generate_winnability_deterministic(account: Account) -> dict:
    """Generate winnability score from available signals."""
    score = 50  # baseline
    reasons = []

    # Positive signals
    if account.current_coverages and len(account.current_coverages) >= 3:
        score += 10
        reasons.append("Multiple coverage lines suggest engaged insurance buyer")

    if account.workers_comp_mod and float(account.workers_comp_mod) < 1.0:
        score += 10
        reasons.append("Favorable mod makes account attractive to carriers")

    if account.annual_revenue and float(account.annual_revenue) > 2_000_000:
        score += 5
        reasons.append("Revenue size supports competitive quoting")

    # Negative signals
    if account.workers_comp_mod and float(account.workers_comp_mod) > 1.20:
        score -= 15
        reasons.append("High mod may limit carrier appetite")

    claims = account.claims_summary or {}
    if claims.get("total_claims_3yr", 0) >= 3:
        score -= 10
        reasons.append("Active claims history creates carrier concern")

    # Confidence adjustment
    has_coverages = bool(account.current_coverages)
    has_mod = account.workers_comp_mod is not None
    if not has_coverages and not has_mod:
        score = min(score, 40)
        reasons.append("Limited data available to assess winnability")

    score = max(0, min(100, score))

    if score >= 66:
        band = "high"
    elif score >= 36:
        band = "moderate"
    else:
        band = "low"

    talking_points = []
    if score >= 50:
        talking_points.append("Lead with coverage expertise and risk advisory value")
    if account.workers_comp_mod and float(account.workers_comp_mod) > 1.0:
        talking_points.append("Demonstrate mod improvement strategies as a differentiator")
    talking_points.append("Ask about current service satisfaction to identify openings")

    next_actions = [
        "Request current policy declarations for detailed analysis",
        "Prepare coverage comparison showing gaps vs industry standard",
    ]
    if account.current_carriers:
        next_actions.append("Research incumbent carrier strengths and weaknesses")

    return WinnabilityArtifact(
        score=score,
        band=band,
        reasons=reasons[:5],
        talking_points=talking_points[:5],
        next_actions=next_actions[:5],
    ).model_dump()


# ============================================================
# LLM ENRICHMENT (enrichment path)
# ============================================================


def _try_llm_enrichment(artifact_type: str, account: Account) -> Optional[dict]:
    """Attempt LLM-based artifact generation. Returns None on failure."""
    try:
        from app.ai.model_router import ModelRouter
        router = ModelRouter()
        provider = router.get_provider("artifact_generation")
        if provider is None:
            return None

        system_prompt, user_prompt = build_artifact_prompt(
            artifact_type, _account_to_dict(account)
        )
        if not system_prompt:
            return None

        result = provider.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=1500,
        )

        text = result.get("text", "")
        if not text:
            return None

        # Try to parse JSON from response
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        parsed = json.loads(text)

        # Validate against schema
        schema_cls = ARTIFACT_SCHEMA_MAP.get(artifact_type)
        if schema_cls:
            validated = schema_cls(**parsed)
            return validated.model_dump()

        return parsed

    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON for %s", artifact_type)
        return None
    except Exception:
        logger.warning("LLM enrichment failed for %s", artifact_type, exc_info=True)
        return None


# ============================================================
# MAIN GENERATION API
# ============================================================

# Deterministic generator registry
_DETERMINISTIC_GENERATORS = {
    "coverage_gap": _generate_coverage_gap_deterministic,
    "meeting_brief": _generate_meeting_brief_deterministic,
    "workers_comp_snapshot": _generate_workers_comp_deterministic,
    "winnability": _generate_winnability_deterministic,
}


def generate_artifact(
    account_id: UUID,
    artifact_type: str,
    db: Session,
    use_llm: bool = True,
) -> SavedArtifact:
    """Generate a single artifact for an account.

    1. Creates SavedArtifact with status=pending
    2. Runs deterministic generator (fast)
    3. Optionally attempts LLM enrichment
    4. Validates and persists
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise ValueError(f"Account {account_id} not found")

    if artifact_type not in _DETERMINISTIC_GENERATORS:
        raise ValueError(f"Unknown artifact type: {artifact_type}")

    # Create pending artifact
    artifact = SavedArtifact(
        account_id=account_id,
        artifact_type=artifact_type,
        title=artifact_type.replace("_", " ").title(),
        content_json={},
        status="pending",
    )
    db.add(artifact)
    db.flush()

    try:
        # Fast path: deterministic generation
        content = _DETERMINISTIC_GENERATORS[artifact_type](account)
        model_name = "deterministic"
        confidence = 0.6

        # Enrichment path: try LLM
        if use_llm:
            llm_content = _try_llm_enrichment(artifact_type, account)
            if llm_content:
                content = llm_content
                model_name = "claude"
                confidence = 0.85

        artifact.content_json = content
        artifact.status = "ready"
        artifact.model_name = model_name
        artifact.confidence = Decimal(str(confidence))
        db.flush()

        # Record durable memory for coverage gap conclusions
        if artifact_type == "coverage_gap" and content.get("gaps"):
            _record_coverage_memory(db, account, content)

    except Exception:
        logger.exception("Artifact generation failed for %s/%s", account_id, artifact_type)
        artifact.status = "failed"
        artifact.content_json = _DETERMINISTIC_GENERATORS[artifact_type](account)
        artifact.model_name = "deterministic_fallback"
        artifact.confidence = Decimal("0.4")
        db.flush()

    return artifact


def _record_coverage_memory(db: Session, account: Account, content: dict) -> None:
    """Record durable memory entries from coverage gap analysis."""
    from app.services.account_memory_service import record_memory

    gaps = content.get("gaps", [])
    if not gaps:
        return

    top_gaps = gaps[:3]
    summary = f"Coverage gaps identified: {', '.join(top_gaps)}"

    record_memory(
        db,
        account_id=str(account.id),
        entry_type="brief_generated",
        summary=summary,
        category="coverage_history",
        confidence="high" if len(gaps) <= 3 else "medium",
        industry=account.industry,
        payload_json={"gaps": gaps, "risk_level": content.get("risk_level")},
    )


def generate_all_artifacts(
    account_id: UUID,
    db: Session,
    use_llm: bool = True,
) -> list[SavedArtifact]:
    """Generate all artifact types for an account in priority order."""
    artifacts = []
    for artifact_type in ARTIFACT_PRIORITY:
        try:
            artifact = generate_artifact(account_id, artifact_type, db, use_llm=use_llm)
            artifacts.append(artifact)
        except Exception:
            logger.exception("Failed to generate %s for account %s", artifact_type, account_id)
    return artifacts
