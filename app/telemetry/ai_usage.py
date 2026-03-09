"""AI Usage Telemetry — tracks model provider calls for observability.

Records every AI provider call with provider, model, task type,
token usage, and context. Additive only — never auto-modifies behavior.
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AIUsageEvent:
    """A single AI provider usage event."""

    timestamp: str
    provider: str
    model: str
    task_type: str
    token_usage: dict = field(default_factory=dict)
    office_id: Optional[str] = None
    endpoint: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# In-memory store
AI_USAGE_EVENTS: list[AIUsageEvent] = []


def record_ai_usage(
    provider: str,
    model: str,
    task_type: str,
    token_usage: Optional[dict] = None,
    office_id: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> dict:
    """Record an AI usage event."""
    event = AIUsageEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        provider=provider,
        model=model,
        task_type=task_type,
        token_usage=token_usage or {},
        office_id=office_id,
        endpoint=endpoint,
    )
    AI_USAGE_EVENTS.append(event)
    return event.to_dict()


def list_ai_usage(
    provider: Optional[str] = None,
    task_type: Optional[str] = None,
) -> list[dict]:
    """List AI usage events with optional filters."""
    results = AI_USAGE_EVENTS
    if provider:
        results = [e for e in results if e.provider == provider]
    if task_type:
        results = [e for e in results if e.task_type == task_type]
    return [e.to_dict() for e in results]


def summarize_ai_usage() -> dict:
    """Summarize AI usage across all events."""
    total_tokens = 0
    by_provider: dict[str, int] = {}
    by_task: dict[str, int] = {}

    for event in AI_USAGE_EVENTS:
        t = event.token_usage.get("total_tokens") or 0
        total_tokens += t
        by_provider[event.provider] = by_provider.get(event.provider, 0) + 1
        by_task[event.task_type] = by_task.get(event.task_type, 0) + 1

    return {
        "total_calls": len(AI_USAGE_EVENTS),
        "total_tokens": total_tokens,
        "by_provider": by_provider,
        "by_task_type": by_task,
    }
