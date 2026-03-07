"""Telemetry Store — in-memory event and feedback capture for rendered outputs.

Records how producers interact with rendered WAYOS outputs. All data is
additive and observational — it never mutates canonical knowledge.

Optionally bridges negative/edited feedback into the learning store
for future human review, but never auto-updates profiles.
"""

import logging
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from app.telemetry.telemetry_models import (
    RenderedOutputEvent,
    RenderedOutputFeedback,
    VALID_EVENT_TYPES,
    VALID_FEEDBACK_TYPES,
)

logger = logging.getLogger(__name__)

# ============================================================
# IN-MEMORY STORES
# ============================================================

RENDERED_OUTPUT_EVENTS: list[RenderedOutputEvent] = []
RENDERED_OUTPUT_FEEDBACK: list[RenderedOutputFeedback] = []


# ============================================================
# RECORD FUNCTIONS
# ============================================================


def record_rendered_output_event(
    event_type: str,
    endpoint: str,
    response_type: str,
    mode: str,
    tone: str,
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
    session_id: Optional[str] = None,
    output_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Record a rendered output telemetry event."""
    event = RenderedOutputEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type if event_type in VALID_EVENT_TYPES else "rendered_output_shown",
        office_id=office_id,
        industry=industry,
        endpoint=endpoint,
        response_type=response_type,
        mode=mode,
        tone=tone,
        session_id=session_id,
        output_id=output_id,
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    RENDERED_OUTPUT_EVENTS.append(event)
    return event.to_dict()


def record_rendered_output_feedback(
    output_id: str,
    endpoint: str,
    response_type: str,
    mode: str,
    tone: str,
    feedback_type: str,
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
    feedback_note: Optional[str] = None,
    edited_text: Optional[str] = None,
) -> dict:
    """Record producer feedback on a rendered output."""
    fb = RenderedOutputFeedback(
        output_id=output_id,
        office_id=office_id,
        industry=industry,
        endpoint=endpoint,
        response_type=response_type,
        mode=mode,
        tone=tone,
        feedback_type=feedback_type if feedback_type in VALID_FEEDBACK_TYPES else "up",
        feedback_note=feedback_note,
        edited_text=edited_text if feedback_type == "edited" else None,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    RENDERED_OUTPUT_FEEDBACK.append(fb)

    # Bridge negative/edited feedback to learning store (additive, non-blocking)
    if feedback_type in ("down", "not_useful", "edited") and office_id and industry:
        _bridge_to_learning_store(fb)

    return fb.to_dict()


def _bridge_to_learning_store(fb: RenderedOutputFeedback):
    """Optionally store negative feedback in learning store for human review.

    Non-blocking — failures are logged, never raised.
    """
    try:
        from app.services.learning_store import add_producer_feedback as store_feedback
        store_feedback(
            office_id=fb.office_id or "",
            industry=fb.industry or "",
            endpoint=fb.endpoint,
            input_payload={"output_id": fb.output_id, "mode": fb.mode, "tone": fb.tone},
            output_payload={},
            feedback_type=fb.feedback_type,
            feedback_note=fb.feedback_note,
        )
    except Exception:
        logger.debug("Failed to bridge telemetry feedback to learning store", exc_info=True)


# ============================================================
# QUERY FUNCTIONS
# ============================================================


def list_rendered_output_events(
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
    endpoint: Optional[str] = None,
    event_type: Optional[str] = None,
) -> list[dict]:
    """List rendered output events with optional filters."""
    results = RENDERED_OUTPUT_EVENTS
    if office_id:
        results = [e for e in results if e.office_id == office_id]
    if industry:
        results = [e for e in results if e.industry and e.industry.lower() == industry.lower()]
    if endpoint:
        results = [e for e in results if e.endpoint == endpoint]
    if event_type:
        results = [e for e in results if e.event_type == event_type]
    return [e.to_dict() for e in results]


def list_rendered_output_feedback(
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
    endpoint: Optional[str] = None,
    feedback_type: Optional[str] = None,
) -> list[dict]:
    """List rendered output feedback with optional filters."""
    results = RENDERED_OUTPUT_FEEDBACK
    if office_id:
        results = [f for f in results if f.office_id == office_id]
    if industry:
        results = [f for f in results if f.industry and f.industry.lower() == industry.lower()]
    if endpoint:
        results = [f for f in results if f.endpoint == endpoint]
    if feedback_type:
        results = [f for f in results if f.feedback_type == feedback_type]
    return [f.to_dict() for f in results]


# ============================================================
# ANALYTICS HELPERS
# ============================================================


def count_by_key(items: list, key: str) -> dict[str, int]:
    """Count items grouped by a given attribute name."""
    counter: Counter = Counter()
    for item in items:
        val = getattr(item, key, None) or "unknown"
        counter[val] += 1
    return dict(counter.most_common())


def safe_feedback_sentiment(feedback_list: list[RenderedOutputFeedback]) -> dict:
    """Classify feedback into positive/negative/neutral counts."""
    positive = {"up", "useful"}
    negative = {"down", "not_useful"}
    pos = sum(1 for f in feedback_list if f.feedback_type in positive)
    neg = sum(1 for f in feedback_list if f.feedback_type in negative)
    edited = sum(1 for f in feedback_list if f.feedback_type == "edited")
    return {"positive": pos, "negative": neg, "edited": edited}


def summarize_endpoint_usage(events: list[RenderedOutputEvent]) -> dict[str, int]:
    """Count events by endpoint."""
    return count_by_key(events, "endpoint")


def summarize_mode_usage(events: list[RenderedOutputEvent]) -> dict[str, int]:
    """Count events by mode."""
    return count_by_key(events, "mode")


def summarize_rendered_output_telemetry(
    office_id: Optional[str] = None,
    industry: Optional[str] = None,
) -> dict:
    """Produce an aggregated telemetry summary."""
    events = RENDERED_OUTPUT_EVENTS
    feedback = RENDERED_OUTPUT_FEEDBACK

    if office_id:
        events = [e for e in events if e.office_id == office_id]
        feedback = [f for f in feedback if f.office_id == office_id]
    if industry:
        key = industry.lower()
        events = [e for e in events if e.industry and e.industry.lower() == key]
        feedback = [f for f in feedback if f.industry and f.industry.lower() == key]

    sentiment = safe_feedback_sentiment(feedback)

    return {
        "total_render_events": len(events),
        "total_feedback_events": len(feedback),
        "by_endpoint": count_by_key(events, "endpoint"),
        "by_mode": count_by_key(events, "mode"),
        "by_tone": count_by_key(events, "tone"),
        "by_event_type": count_by_key(events, "event_type"),
        "positive_feedback_count": sentiment["positive"],
        "negative_feedback_count": sentiment["negative"],
        "edited_count": sentiment["edited"],
    }
