"""Demo Session Summary Service — aggregates session activity for internal review."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import EventLog, DemoFeedback

logger = logging.getLogger(__name__)

# Events that represent key demo workflow steps (in expected order)
WORKFLOW_EVENTS = [
    "demo_session_started",
    "login_success",
    "account_created",
    "account_selected",
    "workspace_generated",
    "public_intel_refreshed",
    "submission_packet_generated",
    "narrative_copied",
    "packet_copied",
]


def build_demo_session_summary(
    db: Session,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    hours: int = 24,
) -> dict:
    """Build a summary of demo session activity.

    Filters by session_id, user_id, or time window (defaults to last 24h).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = db.query(EventLog).filter(EventLog.created_at >= cutoff)
    if session_id:
        query = query.filter(EventLog.session_id == session_id)
    elif user_id:
        query = query.filter(EventLog.user_id == user_id)

    events = query.order_by(EventLog.created_at.asc()).all()

    if not events:
        return {
            "session_id": session_id,
            "user_id": user_id,
            "event_count": 0,
            "actions_completed": [],
            "time_to_first_workspace_seconds": None,
            "time_to_first_packet_seconds": None,
            "copy_actions": 0,
            "sections_expanded": 0,
            "errors_encountered": 0,
            "public_intel_refreshed_before_packet": False,
            "feedback_count": 0,
            "timeline": [],
        }

    # Build timeline
    timeline = []
    for e in events:
        timeline.append({
            "event_type": e.event_type,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "payload": e.event_payload,
        })

    # Compute actions completed (unique workflow events)
    event_types = [e.event_type for e in events]
    actions_completed = [et for et in WORKFLOW_EVENTS if et in event_types]

    # Timing
    first_event_time = events[0].created_at
    time_to_first_workspace = _time_to_event(events, first_event_time, "workspace_generated")
    time_to_first_packet = _time_to_event(events, first_event_time, "submission_packet_generated")

    # Counts
    copy_actions = sum(1 for et in event_types if et in ("narrative_copied", "packet_copied"))
    sections_expanded = sum(1 for et in event_types if et in ("workspace_section_expanded", "trust_section_expanded"))
    errors_encountered = sum(1 for et in event_types if et == "error_shown")

    # Intel before packet
    intel_times = [e.created_at for e in events if e.event_type == "public_intel_refreshed"]
    packet_times = [e.created_at for e in events if e.event_type == "submission_packet_generated"]
    intel_before_packet = False
    if intel_times and packet_times:
        intel_before_packet = min(intel_times) < min(packet_times)

    # Feedback count
    fb_query = db.query(DemoFeedback).filter(DemoFeedback.created_at >= cutoff)
    if session_id:
        fb_query = fb_query.filter(DemoFeedback.session_id == session_id)
    elif user_id:
        fb_query = fb_query.filter(DemoFeedback.user_id == user_id)
    feedback_count = fb_query.count()

    return {
        "session_id": session_id,
        "user_id": user_id,
        "event_count": len(events),
        "actions_completed": actions_completed,
        "time_to_first_workspace_seconds": time_to_first_workspace,
        "time_to_first_packet_seconds": time_to_first_packet,
        "copy_actions": copy_actions,
        "sections_expanded": sections_expanded,
        "errors_encountered": errors_encountered,
        "public_intel_refreshed_before_packet": intel_before_packet,
        "feedback_count": feedback_count,
        "timeline": timeline,
    }


def list_recent_sessions(db: Session, hours: int = 24, limit: int = 20) -> list[dict]:
    """List recent unique sessions with basic stats."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    events = (
        db.query(EventLog)
        .filter(EventLog.created_at >= cutoff)
        .filter(EventLog.session_id.isnot(None))
        .order_by(EventLog.created_at.desc())
        .all()
    )

    sessions: dict[str, dict] = {}
    for e in events:
        sid = e.session_id
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "user_id": e.user_id,
                "event_count": 0,
                "first_event": e.created_at.isoformat() if e.created_at else None,
                "last_event": e.created_at.isoformat() if e.created_at else None,
                "event_types": set(),
            }
        sessions[sid]["event_count"] += 1
        sessions[sid]["event_types"].add(e.event_type)
        ts = e.created_at.isoformat() if e.created_at else None
        if ts and (sessions[sid]["first_event"] is None or ts < sessions[sid]["first_event"]):
            sessions[sid]["first_event"] = ts
        if ts and (sessions[sid]["last_event"] is None or ts > sessions[sid]["last_event"]):
            sessions[sid]["last_event"] = ts

    result = []
    for sid, info in sessions.items():
        info["event_types"] = sorted(info["event_types"])
        result.append(info)
        if len(result) >= limit:
            break

    return result


def _time_to_event(events: list, start_time: datetime, target_type: str) -> Optional[float]:
    """Return seconds from start_time to first occurrence of target_type."""
    for e in events:
        if e.event_type == target_type and e.created_at:
            delta = (e.created_at - start_time).total_seconds()
            return round(delta, 1)
    return None
