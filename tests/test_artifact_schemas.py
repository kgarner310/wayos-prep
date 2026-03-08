"""Tests for Artifact Pydantic Schemas.

Tests cover:
- Safe defaults for all artifact schemas
- Score bounds validation (winnability)
- Full data population
- Schema map completeness
- All schemas have artifact_type field
- model_dump() produces valid dicts
"""

import pytest
from pydantic import ValidationError

from app.schemas.artifact_schemas import (
    CoverageGapArtifact,
    MeetingBriefArtifact,
    WorkersCompSnapshotArtifact,
    WinnabilityArtifact,
    ARTIFACT_SCHEMA_MAP,
    ARTIFACT_PRIORITY,
)


# ============================================================
# SAFE DEFAULTS
# ============================================================


class TestCoverageGapDefaults:
    def test_coverage_gap_defaults(self):
        """CoverageGapArtifact with no args should have safe defaults."""
        artifact = CoverageGapArtifact()
        assert artifact.artifact_type == "coverage_gap"
        assert artifact.risk_level == "unknown"
        assert artifact.gaps == []
        assert artifact.recommended_coverages == []
        assert artifact.duty_to_advise_flags == []
        assert artifact.producer_talking_points == []
        assert artifact.unknowns == []


class TestMeetingBriefDefaults:
    def test_meeting_brief_defaults(self):
        """MeetingBriefArtifact with no args should have safe defaults."""
        artifact = MeetingBriefArtifact()
        assert artifact.artifact_type == "meeting_brief"
        assert artifact.client_summary == ""
        assert artifact.key_risks == []
        assert artifact.coverage_concerns == []
        assert artifact.questions_for_client == []
        assert artifact.conversation_strategy == []


class TestWorkersCompDefaults:
    def test_workers_comp_defaults(self):
        """WorkersCompSnapshotArtifact with no args should have safe defaults."""
        artifact = WorkersCompSnapshotArtifact()
        assert artifact.artifact_type == "workers_comp_snapshot"
        assert artifact.mod == "unknown"
        assert artifact.industry_average_mod == "unknown"
        assert artifact.premium_signal == "unknown"
        assert artifact.risk_drivers == []
        assert artifact.improvement_opportunities == []
        assert artifact.unknowns == []


class TestWinnabilityDefaults:
    def test_winnability_defaults(self):
        """WinnabilityArtifact with no args should have safe defaults."""
        artifact = WinnabilityArtifact()
        assert artifact.artifact_type == "winnability"
        assert artifact.score == 0
        assert artifact.band == "unknown"
        assert artifact.reasons == []
        assert artifact.talking_points == []
        assert artifact.next_actions == []


# ============================================================
# WINNABILITY SCORE BOUNDS
# ============================================================


class TestWinnabilityScoreBounds:
    def test_score_in_range(self):
        """Winnability score must be 0-100."""
        artifact = WinnabilityArtifact(score=50)
        assert artifact.score == 50

        artifact = WinnabilityArtifact(score=0)
        assert artifact.score == 0

        artifact = WinnabilityArtifact(score=100)
        assert artifact.score == 100

    def test_score_above_100_rejected(self):
        """Score above 100 should be rejected."""
        with pytest.raises(ValidationError):
            WinnabilityArtifact(score=101)

    def test_score_below_0_rejected(self):
        """Score below 0 should be rejected."""
        with pytest.raises(ValidationError):
            WinnabilityArtifact(score=-1)


# ============================================================
# COVERAGE GAP WITH DATA
# ============================================================


class TestCoverageGapWithData:
    def test_coverage_gap_with_data(self):
        """Create CoverageGapArtifact with full data. Verify all fields populated."""
        artifact = CoverageGapArtifact(
            risk_level="elevated",
            gaps=["No umbrella coverage", "No inland marine"],
            recommended_coverages=["umbrella", "inland_marine"],
            duty_to_advise_flags=["No workers comp detected"],
            producer_talking_points=["Ask about subcontractor certificates"],
            unknowns=["Full policy schedule not available"],
        )
        assert artifact.risk_level == "elevated"
        assert len(artifact.gaps) == 2
        assert len(artifact.recommended_coverages) == 2
        assert len(artifact.duty_to_advise_flags) == 1
        assert len(artifact.producer_talking_points) == 1
        assert len(artifact.unknowns) == 1


# ============================================================
# SCHEMA MAP COMPLETENESS
# ============================================================


class TestSchemaMapComplete:
    def test_schema_map_complete(self):
        """All ARTIFACT_PRIORITY types are in ARTIFACT_SCHEMA_MAP."""
        for artifact_type in ARTIFACT_PRIORITY:
            assert artifact_type in ARTIFACT_SCHEMA_MAP, (
                f"{artifact_type} missing from ARTIFACT_SCHEMA_MAP"
            )


# ============================================================
# ALL SCHEMAS HAVE ARTIFACT TYPE
# ============================================================


class TestAllSchemasHaveArtifactType:
    def test_all_schemas_have_artifact_type(self):
        """Every schema class in ARTIFACT_SCHEMA_MAP should have an artifact_type field."""
        for name, schema_cls in ARTIFACT_SCHEMA_MAP.items():
            instance = schema_cls()
            assert hasattr(instance, "artifact_type"), (
                f"{schema_cls.__name__} missing artifact_type field"
            )
            assert instance.artifact_type == name


# ============================================================
# MODEL DUMP PRODUCES VALID DICT
# ============================================================


class TestModelDumpProducesJson:
    def test_model_dump_produces_json(self):
        """Each schema's model_dump() should produce a valid dict."""
        for name, schema_cls in ARTIFACT_SCHEMA_MAP.items():
            instance = schema_cls()
            dumped = instance.model_dump()
            assert isinstance(dumped, dict), f"{schema_cls.__name__}.model_dump() did not return dict"
            assert "artifact_type" in dumped
            assert dumped["artifact_type"] == name

            # Verify round-trip: construct from dump
            reconstructed = schema_cls(**dumped)
            assert reconstructed.artifact_type == name
