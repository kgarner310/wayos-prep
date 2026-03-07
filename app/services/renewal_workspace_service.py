"""Renewal Workspace Service — orchestrates WAYOS engines into a unified renewal workflow.

Guides a producer through renewal preparation:
Account → Public Web Intel → Renewal Risk Brief → Coverage Gaps →
Underwriter Narrative → Assembled Workspace

Reuses existing services; does not duplicate logic.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.account_service import get_account
from app.services.account_refresh_service import get_latest_public_intel
from app.services.renewal_brief_generator import generate_renewal_brief
from app.services.coverage_gap_detector import detect_coverage_gaps
from app.services.producer_ammo import generate_producer_ammo
from app.services.underwriter_narrative_generator import generate_underwriter_narrative
from app.services.instrumentation import log_event

logger = logging.getLogger(__name__)


def build_renewal_workspace(
    db: Session,
    account_id: UUID,
    options: dict | None = None,
) -> dict:
    """Build a unified renewal workspace for an account.

    Orchestrates:
    1. Load account
    2. Retrieve latest public web intel artifact
    3. Generate renewal risk brief
    4. Detect coverage gaps
    5. Generate producer ammo
    6. Generate underwriter narrative
    7. Assemble unified response

    Gracefully handles missing components — skips sections when data is absent.

    Args:
        db: database session
        account_id: UUID of the account
        options: optional dict with overrides (e.g. narrative_type, producer_id)

    Returns:
        Unified workspace dict
    """
    options = options or {}

    log_event(db, "renewal_workspace_requested", payload={
        "account_id": str(account_id),
    })

    # --- 1. Load account ---
    account = get_account(db, account_id)
    if not account:
        return {"error": "Account not found", "account_id": str(account_id)}

    # Build profile dict from account
    profile = _account_to_profile(account, options)

    # --- 2. Retrieve latest public web intel ---
    public_intel = None
    operations_signals = {}
    try:
        latest = get_latest_public_intel(db, account_id)
        if latest and latest.get("content"):
            content = latest["content"]
            public_intel = content.get("public_web_intel")
            if public_intel:
                operations_signals = {
                    "company_identity": public_intel.get("company_identity", {}),
                    "operations_signals": public_intel.get("operations_signals", []),
                    "safety_signals": public_intel.get("safety_signals", []),
                    "scale_signals": public_intel.get("scale_signals", []),
                    "carrier_relevant_signals": public_intel.get("carrier_relevant_signals", []),
                }
                # Inject public intel into profile for narrative generation
                profile["public_web_intel"] = public_intel
    except Exception:
        logger.warning("Failed to load public intel for account=%s", account_id, exc_info=True)

    # --- 3. Generate renewal risk brief ---
    renewal_brief = {}
    try:
        renewal_brief = generate_renewal_brief(profile)
        profile["renewal_brief"] = renewal_brief
    except Exception:
        logger.warning("Failed to generate renewal brief for account=%s", account_id, exc_info=True)

    # --- 4. Coverage gaps (already computed inside renewal brief, extract) ---
    coverage_gaps = renewal_brief.get("coverage_gaps", [])

    # --- 5. Producer questions (already computed inside renewal brief, extract) ---
    producer_questions = renewal_brief.get("producer_questions", [])

    # --- 6. Generate underwriter narrative ---
    underwriter_narrative = {}
    try:
        narrative_profile = dict(profile)
        narrative_profile["narrative_type"] = options.get("narrative_type", "renewal")
        if options.get("producer_id"):
            narrative_profile["producer_id"] = options["producer_id"]
        underwriter_narrative = generate_underwriter_narrative(narrative_profile, db=db)
    except Exception:
        logger.warning("Failed to generate narrative for account=%s", account_id, exc_info=True)

    # --- 7. Assemble workspace ---
    account_summary = renewal_brief.get("account_summary", {
        "account_name": getattr(account, "account_name", ""),
        "industry": getattr(account, "industry", ""),
        "state": getattr(account, "state", ""),
    })

    risk_overview = renewal_brief.get("risk_overview", {})
    recommended_actions = renewal_brief.get("recommended_actions", [])

    workspace = {
        "account_id": str(account_id),
        "account_summary": account_summary,
        "operations_signals": operations_signals,
        "risk_overview": risk_overview,
        "coverage_gaps": coverage_gaps,
        "producer_questions": producer_questions,
        "underwriter_narrative": {
            "email_version": underwriter_narrative.get("email_version", ""),
            "memo_version": underwriter_narrative.get("memo_version", ""),
            "style_applied": underwriter_narrative.get("style_applied", {}),
        },
        "recommended_actions": recommended_actions,
        "sections_available": _list_available_sections(
            operations_signals, renewal_brief, coverage_gaps,
            underwriter_narrative, recommended_actions,
        ),
    }

    log_event(db, "renewal_workspace_generated", payload={
        "account_id": str(account_id),
        "sections_available": workspace["sections_available"],
    })

    logger.info(
        "Renewal workspace built: account=%s sections=%s",
        account_id, workspace["sections_available"],
    )

    return workspace


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _account_to_profile(account, options: dict) -> dict:
    """Convert an Account ORM object to a profile dict for service consumption."""
    return {
        "account_name": getattr(account, "account_name", ""),
        "industry": getattr(account, "industry", "") or "",
        "state": getattr(account, "state", "") or "",
        "employee_count": getattr(account, "employee_count", None) or 0,
        "annual_revenue": float(getattr(account, "annual_revenue", None) or 0),
        "vehicle_count": getattr(account, "vehicle_count", None) or 0,
        "uses_subcontractors": getattr(account, "uses_subcontractors", False),
        "current_coverages": getattr(account, "current_coverages", None) or [],
        "website_url": getattr(account, "website_url", None),
        "notes": getattr(account, "notes", "") or "",
        "account_stage": options.get("account_stage", "renewal"),
        "experience_mod": options.get("experience_mod"),
        "loss_run_data": options.get("loss_run_data"),
        "experience_mod_data": options.get("experience_mod_data"),
    }


def _list_available_sections(
    operations_signals: dict,
    renewal_brief: dict,
    coverage_gaps: list,
    underwriter_narrative: dict,
    recommended_actions: list,
) -> list[str]:
    """List which workspace sections have content."""
    sections = []
    if operations_signals:
        sections.append("operations_signals")
    if renewal_brief:
        sections.append("risk_overview")
    if coverage_gaps:
        sections.append("coverage_gaps")
    if underwriter_narrative.get("email_version"):
        sections.append("underwriter_narrative")
    if recommended_actions:
        sections.append("recommended_actions")
    return sections
