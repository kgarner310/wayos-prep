"""Presentation models for the thin rewrite / answer variation layer.

These models control how structured WAYOS outputs are rendered into
producer-facing language. The presentation layer is optional and additive —
it never changes scoring, facts, or canonical knowledge.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


VALID_MODES = {"concise", "consultative", "technical", "meeting_brief"}
VALID_TONES = {"neutral", "confident", "practical"}

DEFAULT_MODE = "concise"
DEFAULT_TONE = "neutral"


@dataclass
class RewriteOptions:
    """Controls how a structured output is rendered into producer-facing text."""

    mode: str = DEFAULT_MODE        # concise | consultative | technical | meeting_brief
    tone: str = DEFAULT_TONE        # neutral | confident | practical
    max_bullets: Optional[int] = None
    max_sentences: Optional[int] = None
    include_disclaimer: bool = False

    def __post_init__(self):
        if self.mode not in VALID_MODES:
            self.mode = DEFAULT_MODE
        if self.tone not in VALID_TONES:
            self.tone = DEFAULT_TONE

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RenderedResponse:
    """The rendered presentation output alongside metadata."""

    response_type: str
    mode: str
    tone: str
    rendered_text: str
    rendered_bullets: list[str] = field(default_factory=list)
    source_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
