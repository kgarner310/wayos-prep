"""Service Triage — AI-powered service request triage and draft generation.

Takes raw service requests (text, voice transcripts, file extractions),
triages them with AI, and generates draft messages for three audiences:
insured, carrier, and AMS documentation.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import Account, ServiceTriageRequest

logger = logging.getLogger(__name__)

VALID_STATUSES = {"pending", "triaged", "approved", "rejected"}
VALID_URGENCIES = {"urgent", "high", "medium", "low"}
VALID_REQUEST_TYPES = {
    "certificate_request", "endorsement_change", "claim_report",
    "billing_inquiry", "policy_question", "renewal", "cancellation",
    "audit", "new_business", "other",
}


def create_triage_request(
    db: Session,
    input_text: str,
    input_type: str = "text",
    account_id: Optional[UUID] = None,
    agency_id: Optional[UUID] = None,
    created_by_user_id: Optional[UUID] = None,
    input_filename: Optional[str] = None,
    input_extracted_text: Optional[str] = None,
) -> ServiceTriageRequest:
    """Create a new triage request and persist it."""
    triage = ServiceTriageRequest(
        input_type=input_type,
        input_text=input_text,
        input_filename=input_filename,
        input_extracted_text=input_extracted_text,
        account_id=account_id,
        agency_id=agency_id,
        created_by_user_id=created_by_user_id,
        status="pending",
    )
    db.add(triage)
    db.flush()
    return triage


def run_ai_triage(db: Session, triage_id: UUID) -> ServiceTriageRequest:
    """Run AI triage on a pending request. Updates the record in place."""
    triage = db.query(ServiceTriageRequest).filter(
        ServiceTriageRequest.id == triage_id
    ).first()
    if not triage:
        raise ValueError(f"Triage request {triage_id} not found")

    # Build context
    account_context = ""
    if triage.account_id:
        account = db.query(Account).filter(Account.id == triage.account_id).first()
        if account:
            account_context = _build_account_context(account)

    # Combine all input text
    full_text = triage.input_text
    if triage.input_extracted_text:
        full_text += f"\n\n[Extracted from attached file: {triage.input_filename or 'unknown'}]\n{triage.input_extracted_text}"

    prompt = _build_triage_prompt(full_text, account_context)

    # Try LLM triage
    try:
        result = _call_llm(prompt)
        if result:
            _apply_triage_result(triage, result)
            triage.status = "triaged"
            logger.info("AI triage completed for %s", triage_id)
        else:
            _apply_fallback_triage(triage, full_text)
            triage.status = "triaged"
            logger.info("Fallback triage applied for %s", triage_id)
    except Exception:
        logger.exception("AI triage failed for %s, applying fallback", triage_id)
        _apply_fallback_triage(triage, full_text)
        triage.status = "triaged"

    db.flush()
    return triage


def approve_triage(db: Session, triage_id: UUID, approved_by: UUID) -> ServiceTriageRequest:
    """Mark a triage request as approved and trigger PIT dispatch orchestration."""
    triage = db.query(ServiceTriageRequest).filter(
        ServiceTriageRequest.id == triage_id
    ).first()
    if not triage:
        raise ValueError(f"Triage request {triage_id} not found")

    triage.status = "approved"
    triage.approved_at = datetime.now(timezone.utc)
    triage.approved_by_user_id = approved_by
    db.flush()

    # Trigger PIT orchestrator: creates dispatch records + account memory entry
    from app.services.pit_orchestrator import on_triage_approved
    on_triage_approved(db, triage_id, approved_by)

    return triage


def update_triage_drafts(
    db: Session,
    triage_id: UUID,
    updates: dict,
) -> ServiceTriageRequest:
    """Update triage drafts or metadata (AM editing before approval)."""
    triage = db.query(ServiceTriageRequest).filter(
        ServiceTriageRequest.id == triage_id
    ).first()
    if not triage:
        raise ValueError(f"Triage request {triage_id} not found")

    for key, value in updates.items():
        if value is not None and hasattr(triage, key):
            setattr(triage, key, value)

    db.flush()
    return triage


def list_triage_requests(
    db: Session,
    agency_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ServiceTriageRequest], int]:
    """List triage requests with optional filters."""
    q = db.query(ServiceTriageRequest)

    if agency_id:
        q = q.filter(ServiceTriageRequest.agency_id == agency_id)
    if status:
        q = q.filter(ServiceTriageRequest.status == status)

    total = q.count()
    results = q.order_by(ServiceTriageRequest.created_at.desc()).offset(offset).limit(limit).all()
    return results, total


def get_triage_request(db: Session, triage_id: UUID) -> Optional[ServiceTriageRequest]:
    """Get a single triage request by ID."""
    return db.query(ServiceTriageRequest).filter(
        ServiceTriageRequest.id == triage_id
    ).first()


# ============================================================
# Internal helpers
# ============================================================


def _build_account_context(account: Account) -> str:
    """Build account context string for the AI prompt."""
    parts = [f"Account: {account.account_name}"]
    if account.named_insured:
        parts.append(f"Named Insured: {account.named_insured}")
    if account.industry:
        parts.append(f"Industry: {account.industry}")
    if account.state:
        parts.append(f"State: {account.state}")
    if account.current_carriers:
        parts.append(f"Current Carriers: {', '.join(account.current_carriers)}")
    if account.current_coverages:
        parts.append(f"Current Coverages: {', '.join(account.current_coverages)}")
    return "\n".join(parts)


def _build_triage_prompt(request_text: str, account_context: str) -> str:
    """Build the user prompt for triage."""
    parts = ["SERVICE REQUEST:"]
    parts.append(request_text)
    if account_context:
        parts.append(f"\nACCOUNT CONTEXT:\n{account_context}")
    return "\n".join(parts)


def _call_llm(prompt: str) -> Optional[dict]:
    """Call the LLM for triage. Returns parsed JSON dict or None."""
    try:
        from app.ai.model_router import get_model_router

        system_prompt = _load_system_prompt()
        router = get_model_router()
        result = router.generate_text(
            task_type="service_triage",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=1500,
        )

        text = result.get("text", "")
        if not text:
            return None

        # Parse JSON from response (handle markdown code blocks)
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed = json.loads(text)

        # Store model info for later
        parsed["_model_name"] = result.get("model", "unknown")
        parsed["_confidence"] = 0.85

        return parsed

    except (json.JSONDecodeError, ImportError, Exception) as e:
        logger.warning("LLM triage parse failed: %s", e)
        return None


def _load_system_prompt() -> str:
    """Load the service triage system prompt."""
    import os
    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts", "service_triage_system.txt"
    )
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Service triage prompt not found at %s", prompt_path)
        return "You are an insurance service triage assistant. Respond with valid JSON."


def _apply_triage_result(triage: ServiceTriageRequest, result: dict):
    """Apply parsed AI triage result to the request."""
    triage.request_type = result.get("request_type", "other")
    triage.urgency = result.get("urgency", "medium")
    triage.summary = result.get("summary", "")
    triage.draft_insured = result.get("draft_insured")
    triage.draft_carrier = result.get("draft_carrier")
    triage.draft_ams_note = result.get("draft_ams_note")
    triage.model_name = result.get("_model_name", "unknown")
    triage.confidence = Decimal(str(result.get("_confidence", 0.85)))


def _apply_fallback_triage(triage: ServiceTriageRequest, full_text: str):
    """Apply deterministic fallback triage when AI is unavailable."""
    text_lower = full_text.lower()

    # Simple keyword-based classification
    if any(w in text_lower for w in ["certificate", "coi", "cert of insurance", "proof of insurance"]):
        request_type = "certificate_request"
        urgency = "high"
    elif any(w in text_lower for w in ["claim", "accident", "injury", "incident"]):
        request_type = "claim_report"
        urgency = "urgent"
    elif any(w in text_lower for w in ["endorsement", "add coverage", "change policy", "add vehicle", "remove"]):
        request_type = "endorsement_change"
        urgency = "medium"
    elif any(w in text_lower for w in ["billing", "payment", "invoice", "premium due"]):
        request_type = "billing_inquiry"
        urgency = "low"
    elif any(w in text_lower for w in ["renew", "renewal"]):
        request_type = "renewal"
        urgency = "medium"
    elif any(w in text_lower for w in ["cancel", "cancellation"]):
        request_type = "cancellation"
        urgency = "high"
    elif any(w in text_lower for w in ["quote", "new policy", "new coverage"]):
        request_type = "new_business"
        urgency = "medium"
    else:
        request_type = "other"
        urgency = "medium"

    # Truncate for summary
    summary = full_text[:200].strip()
    if len(full_text) > 200:
        summary += "..."

    triage.request_type = request_type
    triage.urgency = urgency
    triage.summary = summary
    triage.confidence = Decimal("0.4")
    triage.model_name = "deterministic_fallback"

    # Simple draft templates
    triage.draft_insured = {
        "subject": f"Re: Your {request_type.replace('_', ' ').title()} Request",
        "body": (
            f"Thank you for reaching out regarding your {request_type.replace('_', ' ')}. "
            "We've received your request and our team is reviewing it now. "
            "We'll follow up shortly with next steps.\n\n"
            "Please don't hesitate to reach out if you have any questions in the meantime."
        ),
    }
    triage.draft_carrier = {
        "subject": f"{request_type.replace('_', ' ').title()} Request — [NEED: Account Name / Policy #]",
        "body": (
            f"We have a {request_type.replace('_', ' ')} request for the above-referenced account.\n\n"
            f"Details:\n{summary}\n\n"
            "Please advise on next steps. Thank you."
        ),
    }
    triage.draft_ams_note = {
        "summary": f"{request_type.replace('_', ' ').title()} request received. {summary}",
        "action_items": [f"Process {request_type.replace('_', ' ')} request", "Follow up with insured"],
        "category": request_type.replace("_", " ").title(),
    }
