"""Telemetry models for rendered output tracking and feedback capture.

These models capture how producers interact with rendered WAYOS outputs:
which modes/tones are shown, copied, rated, or edited. This is observability
only — telemetry never mutates canonical knowledge automatically.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


VALID_EVENT_TYPES = {
    "rendered_output_shown",
    "rendered_output_copied",
    "rendered_output_feedback",
    "rendered_output_edited",
}

VALID_FEEDBACK_TYPES = {"up", "down", "useful", "not_useful", "edited"}


@dataclass
class RenderedOutputEvent:
    """A single telemetry event for a rendered output."""

    event_id: str
    event_type: str
    office_id: Optional[str] = None
    industry: Optional[str] = None
    endpoint: str = ""
    response_type: str = ""
    mode: str = ""
    tone: str = ""
    session_id: Optional[str] = None
    output_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RenderedOutputFeedback:
    """Producer feedback on a specific rendered output."""

    output_id: str
    office_id: Optional[str] = None
    industry: Optional[str] = None
    endpoint: str = ""
    response_type: str = ""
    mode: str = ""
    tone: str = ""
    feedback_type: str = ""  # up | down | useful | not_useful | edited
    feedback_note: Optional[str] = None
    edited_text: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
