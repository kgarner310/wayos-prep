"""Tests for Artifact Engine.

Tests cover:
- Deterministic generation for all artifact types
- Schema validation of generated artifacts
- DB record creation (generate_artifact, generate_all_artifacts)
- Error handling for unknown types and missing accounts
- Deterministic fallback when LLM enrichment fails
"""

import uuid
from unittest.mock import MagicMock, patch
from decimal import Decimal

import pytest

from app.services.artifact_engine import (
    generate_artifact,
    generate_all_artifacts,
    _generate_coverage_gap_deterministic,
    _generate_meeting_brief_deterministic,
    _generate_workers_comp_deterministic,
    _generate_winnability_deterministic,
)
from app.schemas.artifact_schemas import (
    CoverageGapArtifact,
    MeetingBriefArtifact,
    WorkersCompSnapshotArtifact,
    WinnabilityArtifact,
    ARTIFACT_SCHEMA_MAP,
    ARTIFACT_PRIORITY,
)


def _make_account(**kwargs):
    """Create a mock Account for artifact generation."""
    obj = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "account_name": "Test Roofing LLC",
        "named_insured": "Test Roofing LLC",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 30,
        "annual_revenue": Decimal("4000000"),
        "vehicle_count": 10,
        "uses_subcontractors": True,
        "current_coverages": ["workers_comp", "general_liability", "commercial_auto"],
        "current_carriers": ["Travelers", "Cincinnati"],
        "workers_comp_mod": Decimal("1.10"),
        "claims_summary": {"open_claims": 1, "total_claims_3yr": 2},
        "payroll_estimate": Decimal("1500000"),
        "notes": "Test account for artifact generation.",
        "extracted_text": None,
        "website_url": "https://example.com",
        "social_urls": None,
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ============================================================
# DETERMINISTIC GENERATORS
# ============================================================


class TestCoverageGapDeterministic:
    def test_coverage_gap_deterministic(self):
        """Generate deterministic coverage gap and validate against schema."""
        account = _make_account()
        result = _generate_coverage_gap_deterministic(account)

        # Validate against schema
        artifact = CoverageGapArtifact(**result)
        assert artifact.artifact_type == "coverage_gap"
        assert artifact.risk_level in ("low", "moderate", "elevated", "high", "unknown")
        assert isinstance(artifact.gaps, list)
        assert isinstance(artifact.recommended_coverages, list)
        assert isinstance(artifact.duty_to_advise_flags, list)


class TestMeetingBriefDeterministic:
    def test_meeting_brief_deterministic(self):
        """Generate deterministic meeting brief and validate against schema."""
        account = _make_account()
        result = _generate_meeting_brief_deterministic(account)

        artifact = MeetingBriefArtifact(**result)
        assert artifact.artifact_type == "meeting_brief"
        assert artifact.client_summary != ""
        assert isinstance(artifact.key_risks, list)
        assert isinstance(artifact.questions_for_client, list)


class TestWorkersCompDeterministic:
    def test_workers_comp_deterministic_with_mod(self):
        """Generate WC snapshot with mod and validate against schema."""
        account = _make_account(workers_comp_mod=Decimal("1.15"))
        result = _generate_workers_comp_deterministic(account)

        artifact = WorkersCompSnapshotArtifact(**result)
        assert artifact.artifact_type == "workers_comp_snapshot"
        assert artifact.mod != "unknown"
        assert artifact.premium_signal == "unfavorable"
        assert len(artifact.risk_drivers) > 0

    def test_workers_comp_deterministic_without_mod(self):
        """Generate WC snapshot without mod and validate against schema."""
        account = _make_account(workers_comp_mod=None)
        result = _generate_workers_comp_deterministic(account)

        artifact = WorkersCompSnapshotArtifact(**result)
        assert artifact.artifact_type == "workers_comp_snapshot"
        assert artifact.mod == "unknown"
        assert artifact.premium_signal == "unknown"
        assert len(artifact.unknowns) > 0


class TestWinnabilityDeterministic:
    def test_winnability_deterministic(self):
        """Generate deterministic winnability and validate against schema."""
        account = _make_account()
        result = _generate_winnability_deterministic(account)

        artifact = WinnabilityArtifact(**result)
        assert artifact.artifact_type == "winnability"
        assert 0 <= artifact.score <= 100
        assert artifact.band in ("low", "moderate", "high", "unknown")
        assert isinstance(artifact.reasons, list)
        assert isinstance(artifact.talking_points, list)
        assert isinstance(artifact.next_actions, list)


# ============================================================
# ALL ARTIFACT TYPES VALID
# ============================================================


class TestAllArtifactTypesValid:
    def test_all_artifact_types_valid(self):
        """For each artifact type in ARTIFACT_PRIORITY, generate deterministic and validate."""
        account = _make_account()

        generators = {
            "coverage_gap": _generate_coverage_gap_deterministic,
            "meeting_brief": _generate_meeting_brief_deterministic,
            "workers_comp_snapshot": _generate_workers_comp_deterministic,
            "winnability": _generate_winnability_deterministic,
        }

        for artifact_type in ARTIFACT_PRIORITY:
            gen = generators[artifact_type]
            result = gen(account)

            schema_cls = ARTIFACT_SCHEMA_MAP[artifact_type]
            validated = schema_cls(**result)
            assert validated.artifact_type == artifact_type


# ============================================================
# GENERATE ARTIFACT CREATES RECORD
# ============================================================


class TestGenerateArtifactCreatesRecord:
    def test_generate_artifact_creates_record(self):
        """generate_artifact with use_llm=False should call db.add and db.flush."""
        account = _make_account()
        account_id = account.id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = account

        result = generate_artifact(account_id, "coverage_gap", mock_db, use_llm=False)

        assert mock_db.add.called
        assert mock_db.flush.called
        assert result.artifact_type == "coverage_gap"
        assert result.status == "ready"
        assert result.content_json is not None


# ============================================================
# GENERATE ALL ARTIFACTS CREATES ALL
# ============================================================


class TestGenerateAllArtifactsCreatesAll:
    def test_generate_all_artifacts_creates_all(self):
        """generate_all_artifacts should create one artifact per type."""
        account = _make_account()
        account_id = account.id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = account

        artifacts = generate_all_artifacts(account_id, mock_db, use_llm=False)

        assert len(artifacts) == len(ARTIFACT_PRIORITY)
        types_created = {a.artifact_type for a in artifacts}
        assert types_created == set(ARTIFACT_PRIORITY)


# ============================================================
# UNKNOWN ARTIFACT TYPE RAISES
# ============================================================


class TestUnknownArtifactTypeRaises:
    def test_unknown_artifact_type_raises(self):
        """generate_artifact with unknown type should raise ValueError."""
        account = _make_account()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = account

        with pytest.raises(ValueError, match="Unknown artifact type"):
            generate_artifact(account.id, "nonexistent_type", mock_db, use_llm=False)


# ============================================================
# ACCOUNT NOT FOUND RAISES
# ============================================================


class TestAccountNotFoundRaises:
    def test_account_not_found_raises(self):
        """generate_artifact with missing account should raise ValueError."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            generate_artifact(uuid.uuid4(), "coverage_gap", mock_db, use_llm=False)


# ============================================================
# DETERMINISTIC FALLBACK ON LLM FAILURE
# ============================================================


class TestDeterministicFallbackOnLlmFailure:
    def test_deterministic_fallback_on_llm_failure(self):
        """If LLM enrichment fails, deterministic content should still be valid."""
        account = _make_account()
        account_id = account.id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = account

        with patch(
            "app.services.artifact_engine._try_llm_enrichment",
            side_effect=Exception("LLM unavailable"),
        ):
            result = generate_artifact(account_id, "coverage_gap", mock_db, use_llm=True)

        # Should still have valid content from deterministic fallback
        assert result.content_json is not None
        validated = CoverageGapArtifact(**result.content_json)
        assert validated.artifact_type == "coverage_gap"
