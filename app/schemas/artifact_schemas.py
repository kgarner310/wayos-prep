"""Strict Pydantic schemas for each artifact type.

These enforce the exact contract between the artifact engine and consumers.
Safe defaults ensure partial/failed generation still produces valid output.
"""

from typing import Optional

from pydantic import BaseModel, Field


class CoverageGapArtifact(BaseModel):
    artifact_type: str = "coverage_gap"
    risk_level: str = "unknown"  # low|moderate|elevated|high|unknown
    gaps: list[str] = []
    recommended_coverages: list[str] = []
    duty_to_advise_flags: list[str] = []
    producer_talking_points: list[str] = []
    unknowns: list[str] = []


class MeetingBriefArtifact(BaseModel):
    artifact_type: str = "meeting_brief"
    client_summary: str = ""
    key_risks: list[str] = []
    coverage_concerns: list[str] = []
    questions_for_client: list[str] = []
    conversation_strategy: list[str] = []


class WorkersCompSnapshotArtifact(BaseModel):
    artifact_type: str = "workers_comp_snapshot"
    mod: str = "unknown"
    industry_average_mod: str = "unknown"
    premium_signal: str = "unknown"
    risk_drivers: list[str] = []
    improvement_opportunities: list[str] = []
    unknowns: list[str] = []


class WinnabilityArtifact(BaseModel):
    artifact_type: str = "winnability"
    score: int = Field(default=0, ge=0, le=100)
    band: str = "unknown"  # low|moderate|high|unknown
    reasons: list[str] = []
    talking_points: list[str] = []
    next_actions: list[str] = []


# Registry for validation
ARTIFACT_SCHEMA_MAP = {
    "coverage_gap": CoverageGapArtifact,
    "meeting_brief": MeetingBriefArtifact,
    "workers_comp_snapshot": WorkersCompSnapshotArtifact,
    "winnability": WinnabilityArtifact,
}

ARTIFACT_TYPES = list(ARTIFACT_SCHEMA_MAP.keys())

# Priority order for generation
ARTIFACT_PRIORITY = [
    "coverage_gap",
    "meeting_brief",
    "workers_comp_snapshot",
    "winnability",
]
