"""Account-Linked Public Intel Refresh Service.

Orchestrates the flow: load account -> fetch public web content ->
extract structured intel -> save as artifact -> optionally update account fields.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.account_service import get_account, update_account
from app.services.artifact_service import save_artifact, list_artifacts_for_account
from app.services.public_web_intel import extract_public_web_intel_with_fetch
from app.services.instrumentation import log_event

logger = logging.getLogger(__name__)


def refresh_account_public_intel(
    db: Session,
    account_id: UUID,
    options: dict | None = None,
) -> dict:
    """Refresh public web intel for an account.

    Flow:
    1. Load account
    2. Read website_url (and social_urls if present)
    3. Fetch public text via live fetch
    4. Extract structured public web intel
    5. Save as artifact linked to the account
    6. Optionally update safe account fields
    7. Return result summary

    Args:
        db: database session
        account_id: UUID of the account
        options: optional dict with max_pages, max_chars, fetch_timeout_seconds

    Returns:
        dict with account_id, artifact_saved, public_web_intel, fetch_summary, account_updates
    """
    options = options or {}

    account = get_account(db, account_id)
    if not account:
        return {
            "account_id": str(account_id),
            "artifact_saved": False,
            "error": "Account not found",
            "public_web_intel": None,
            "fetch_summary": None,
            "account_updates": [],
        }

    website_url = getattr(account, "website_url", None) or ""

    if not website_url:
        return {
            "account_id": str(account_id),
            "artifact_saved": False,
            "error": "Account has no website_url configured",
            "public_web_intel": None,
            "fetch_summary": None,
            "account_updates": [],
        }

    # --- Build fetch input ---
    fetch_input = {
        "website_url": website_url,
        "company_name": getattr(account, "account_name", ""),
        "industry": getattr(account, "industry", "") or "",
        "state": getattr(account, "state", "") or "",
        "max_pages": options.get("max_pages", 3),
        "max_chars": options.get("max_chars", 20_000),
        "fetch_timeout_seconds": options.get("fetch_timeout_seconds", 15),
    }

    # --- Fetch + Extract ---
    combined_result = extract_public_web_intel_with_fetch(fetch_input)
    intel = combined_result["public_web_intel"]
    fetch_summary = combined_result["fetch_summary"]

    # --- Save as artifact ---
    artifact_saved = False
    try:
        save_artifact(db, {
            "account_id": account_id,
            "artifact_type": "public_web_intel",
            "artifact_subtype": "web_fetch",
            "title": f"Public Web Intel — {account.account_name}",
            "content_json": {
                "public_web_intel": intel,
                "fetch_metadata": {
                    "source_url": fetch_summary.get("source_url", ""),
                    "fetched_urls": fetch_summary.get("fetched_urls", []),
                    "fetch_warnings": fetch_summary.get("fetch_warnings", []),
                    "refresh_timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        })
        artifact_saved = True
    except Exception:
        logger.warning(
            "Failed to save public_web_intel artifact for account=%s",
            account_id, exc_info=True,
        )

    # --- Safe account field updates ---
    account_updates = _apply_safe_account_updates(db, account_id, intel, account)

    # --- Instrumentation ---
    log_event(db, "account_public_intel_refreshed", payload={
        "account_id": str(account_id),
        "website_url": website_url,
        "fetch_success": fetch_summary.get("success", False),
        "fetched_url_count": len(fetch_summary.get("fetched_urls", [])),
        "artifact_saved": artifact_saved,
    })

    return {
        "account_id": str(account_id),
        "artifact_saved": artifact_saved,
        "public_web_intel": intel,
        "fetch_summary": fetch_summary,
        "account_updates": account_updates,
    }


def get_latest_public_intel(db: Session, account_id: UUID) -> dict | None:
    """Get the most recent public_web_intel artifact for an account."""
    artifacts = list_artifacts_for_account(db, account_id, limit=50)
    for artifact in artifacts:
        if artifact.artifact_type == "public_web_intel":
            return {
                "artifact_id": str(artifact.id),
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                "content": artifact.content_json,
            }
    return None


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _apply_safe_account_updates(
    db: Session,
    account_id: UUID,
    intel: dict,
    account,
) -> list[str]:
    """Apply safe, non-destructive updates to account based on observed intel.

    Only updates fields that are currently empty/null. Never overwrites
    existing verified account data.

    Returns list of field names that were updated.
    """
    updates: dict = {}
    update_descriptions: list[str] = []

    now = datetime.now(timezone.utc)

    # Record refresh timestamp
    updates["last_public_intel_refresh_at"] = now
    update_descriptions.append("last_public_intel_refresh_at")

    try:
        update_account(db, account_id, updates)
    except Exception:
        logger.warning(
            "Failed to update account fields for account=%s",
            account_id, exc_info=True,
        )
        return []

    return update_descriptions
