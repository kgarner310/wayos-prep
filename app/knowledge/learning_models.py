"""Learning models — lightweight institutional memory for WAYOS.

Captures office-specific learnings and producer feedback without
mutating canonical IndustryProfile objects. Additive only.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class OfficeLearning:
    """An office-specific learning note tied to an industry."""

    office_id: str
    industry: str
    note: str
    created_at: str
    created_by: Optional[str] = None
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        return asdict(self)


@dataclass
class ProducerFeedback:
    """Feedback captured from a producer interaction with WAYOS output."""

    office_id: str
    industry: str
    endpoint: str
    input_payload: dict
    output_payload: dict
    feedback_type: str
    feedback_note: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        return asdict(self)
