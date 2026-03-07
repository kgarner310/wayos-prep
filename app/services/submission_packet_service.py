"""Submission Packet Service — composes a complete submission from workspace data.

Reuses renewal_workspace_service; does not duplicate engine logic.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.renewal_workspace_service import build_renewal_workspace
from app.services.instrumentation import log_event

logger = logging.getLogger(__name__)


def build_submission_packet(
    db: Session,
    account_id: UUID,
    options: dict | None = None,
) -> dict:
    """Build a submission packet by composing workspace data.

    Delegates all intelligence to build_renewal_workspace, then layers
    packet-specific structure (title, sections list, rendered text).
    """
    options = options or {}

    log_event(db, "submission_packet_requested", payload={
        "account_id": str(account_id),
    })

    workspace = build_renewal_workspace(db, account_id, {
        "account_stage": options.get("account_stage", "renewal"),
        "narrative_type": options.get("narrative_type", "renewal"),
        "producer_id": options.get("producer_id"),
    })

    if workspace.get("error"):
        return workspace

    account_summary = workspace.get("account_summary", {})
    account_name = account_summary.get("account_name", "Account")
    industry = account_summary.get("industry", "")
    state = account_summary.get("state", "")

    packet_title = f"Submission Packet — {account_name}"
    if industry:
        packet_title += f" ({industry}"
        if state:
            packet_title += f", {state}"
        packet_title += ")"

    # Build sections list for structured rendering
    sections = _build_sections(workspace, options)

    # Build rendered text and markdown
    from app.services.submission_packet_renderer import render_plain_text, render_markdown
    rendered_text = render_plain_text(packet_title, sections, workspace)
    rendered_markdown = render_markdown(packet_title, sections, workspace)

    packet = {
        "account_id": workspace["account_id"],
        "packet_title": packet_title,
        "account_summary": account_summary,
        "risk_overview": workspace.get("risk_overview", {}),
        "coverage_gaps": workspace.get("coverage_gaps", []) if options.get("include_gaps", True) else [],
        "producer_questions": workspace.get("producer_questions", []) if options.get("include_questions", True) else [],
        "underwriter_narrative": workspace.get("underwriter_narrative", {}),
        "recommended_actions": workspace.get("recommended_actions", []),
        "sections": sections,
        "rendered_text": rendered_text,
        "rendered_markdown": rendered_markdown,
        "sections_available": workspace.get("sections_available", []),
    }

    if options.get("include_public_intel", True):
        packet["operations_signals"] = workspace.get("operations_signals")

    log_event(db, "submission_packet_generated", payload={
        "account_id": str(account_id),
        "section_count": len(sections),
    })

    return packet


def _build_sections(workspace: dict, options: dict) -> list[dict]:
    """Build a list of PacketSection dicts from workspace data."""
    sections = []

    # Account Summary
    acct = workspace.get("account_summary", {})
    if acct.get("account_name"):
        facts = acct.get("key_facts", [])
        body = f"Industry: {acct.get('industry', '—')} | State: {acct.get('state', '—')} | Stage: {acct.get('account_stage', 'renewal')}"
        sections.append({
            "title": "Account Summary",
            "content_type": "text",
            "body": body,
            "items": facts,
        })

    # Risk Overview
    ro = workspace.get("risk_overview", {})
    if ro.get("risk_level"):
        body = f"Risk Level: {ro['risk_level'].upper()} | Confidence: {int(ro.get('confidence', 0) * 100)}%"
        if ro.get("headline"):
            body += f"\n{ro['headline']}"
        sections.append({
            "title": "Risk Overview",
            "content_type": "text",
            "body": body,
            "items": ro.get("contributing_factors", []),
        })

    # Operations Signals
    if options.get("include_public_intel", True):
        ops = workspace.get("operations_signals", {})
        all_signals = []
        for key in ["operations_signals", "safety_signals", "scale_signals", "carrier_relevant_signals"]:
            for s in (ops.get(key) or []):
                all_signals.append(s)
        if all_signals:
            sections.append({
                "title": "Operations Signals",
                "content_type": "list",
                "body": "",
                "items": all_signals,
            })

    # Coverage Gaps
    if options.get("include_gaps", True):
        gaps = workspace.get("coverage_gaps", [])
        if gaps:
            items = []
            for g in gaps:
                line = f"{g.get('coverage', '')} ({g.get('risk_level', 'medium')}): {g.get('reason', '')}"
                items.append(line)
            sections.append({
                "title": "Coverage Gaps",
                "content_type": "list",
                "body": "",
                "items": items,
            })

    # Producer Questions
    if options.get("include_questions", True):
        questions = workspace.get("producer_questions", [])
        if questions:
            sections.append({
                "title": "Producer Questions",
                "content_type": "list",
                "body": "",
                "items": questions,
            })

    # Underwriter Narrative
    narrative = workspace.get("underwriter_narrative", {})
    email = narrative.get("email_version", "")
    if email:
        if isinstance(email, dict):
            body = ""
            if email.get("subject"):
                body = f"Subject: {email['subject']}\n\n"
            body += email.get("body", "")
        else:
            body = email
        sections.append({
            "title": "Underwriter Narrative",
            "content_type": "text",
            "body": body,
            "items": narrative.get("source_signals", []),
        })

    # Recommended Actions
    actions = workspace.get("recommended_actions", [])
    if actions:
        sections.append({
            "title": "Recommended Actions",
            "content_type": "list",
            "body": "",
            "items": actions,
        })

    return sections
