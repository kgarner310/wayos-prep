"""Tests for Response Rewriter — thin presentation layer.

Tests cover:
- Presentation models (RewriteOptions, RenderedResponse)
- Meeting brief rewrite in all modes
- Coverage gap rewrite with priority ordering
- Submission readiness rewrite with score and next steps
- render=true preserves original unchanged
- Mode and tone fallback safety
- Truncation and max_bullets
- API endpoint integration with render param
- Regressions
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.presentation.presentation_models import (
    RewriteOptions,
    RenderedResponse,
    VALID_MODES,
    VALID_TONES,
    DEFAULT_MODE,
    DEFAULT_TONE,
)
from app.services.response_rewriter import (
    rewrite_meeting_brief,
    rewrite_coverage_gaps,
    rewrite_submission_readiness,
    prioritize_items,
    truncate_sentences,
    build_bullet_list,
    build_source_summary,
)
from app.main import app
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


# ============================================================
# SAMPLE DATA
# ============================================================

SAMPLE_BRIEF = {
    "industry": "roofing contractor",
    "top_exposures": ["falls from height", "property damage", "vehicle accidents"],
    "common_claims": ["worker fall injuries", "roof leak callbacks"],
    "recommended_talking_points": [
        "Ask about fall protection program",
        "Confirm subcontractor certificate tracking",
        "Review vehicle fleet maintenance",
    ],
    "discovery_questions": [
        "What percentage of work is done by subcontractors?",
        "Do you have a written safety program?",
    ],
    "coverage_watchouts": ["inland marine gap", "umbrella limits too low"],
    "office_learnings": ["NC carriers want 3-year loss runs minimum"],
}

SAMPLE_GAPS = {
    "industry": "roofing contractor",
    "missing_coverages": ["workers compensation", "inland marine", "umbrella / excess"],
    "risk_level": "high",
    "recommended_questions": [
        "Has workers comp been quoted separately?",
        "What is the total tool/equipment value?",
    ],
    "top_exposures": ["falls from height", "property damage"],
    "office_learnings": [],
}

SAMPLE_READINESS = {
    "industry": "roofing contractor",
    "jurisdiction": "NC",
    "readiness_score": 54,
    "readiness_level": "fair",
    "missing_critical_fields": ["Total Payroll", "Loss Runs"],
    "missing_recommended_fields": ["Roof Types", "Maximum Working Height"],
    "weak_fields": ["Operations Description"],
    "strengths": ["Legal Entity Name provided", "Annual Revenue disclosed"],
    "next_steps": [
        "Obtain Total Payroll — this is critical for submission",
        "Obtain Loss Runs — this is critical for submission",
        "Clarify or expand Operations Description — current detail is thin",
    ],
    "office_learnings": [],
    "explanation": "This roofing contractor submission scores 54/100 (fair).",
}


# ============================================================
# PRESENTATION MODELS
# ============================================================


class TestRewriteOptions:
    def test_defaults(self):
        opts = RewriteOptions()
        assert opts.mode == DEFAULT_MODE
        assert opts.tone == DEFAULT_TONE
        assert opts.max_bullets is None

    def test_invalid_mode_falls_back(self):
        opts = RewriteOptions(mode="invalid")
        assert opts.mode == DEFAULT_MODE

    def test_invalid_tone_falls_back(self):
        opts = RewriteOptions(tone="invalid")
        assert opts.tone == DEFAULT_TONE

    def test_to_dict(self):
        opts = RewriteOptions(mode="consultative", tone="practical")
        d = opts.to_dict()
        assert d["mode"] == "consultative"
        assert d["tone"] == "practical"

    def test_valid_modes(self):
        for m in VALID_MODES:
            opts = RewriteOptions(mode=m)
            assert opts.mode == m

    def test_valid_tones(self):
        for t in VALID_TONES:
            opts = RewriteOptions(tone=t)
            assert opts.tone == t


class TestRenderedResponse:
    def test_construction(self):
        r = RenderedResponse(
            response_type="test",
            mode="concise",
            tone="neutral",
            rendered_text="Hello.",
            rendered_bullets=["bullet 1"],
            source_summary={"key": "val"},
        )
        assert r.response_type == "test"
        assert r.rendered_text == "Hello."

    def test_to_dict(self):
        r = RenderedResponse(
            response_type="test", mode="concise", tone="neutral",
            rendered_text="text",
        )
        d = r.to_dict()
        assert d["response_type"] == "test"
        assert isinstance(d["rendered_bullets"], list)


# ============================================================
# HELPERS
# ============================================================


class TestPrioritizeItems:
    def test_basic_truncation(self):
        items = ["a", "b", "c", "d"]
        assert len(prioritize_items(items, 2)) == 2

    def test_priority_sorting(self):
        items = ["umbrella gap", "workers comp missing", "tool coverage"]
        result = prioritize_items(items)
        # workers comp should sort first due to priority keywords
        assert "workers comp" in result[0].lower()

    def test_none_max_returns_all(self):
        items = ["a", "b", "c"]
        assert len(prioritize_items(items)) == 3


class TestTruncateSentences:
    def test_truncate_to_one(self):
        text = "First sentence. Second sentence. Third sentence."
        result = truncate_sentences(text, 1)
        assert result == "First sentence."

    def test_truncate_to_two(self):
        text = "First. Second. Third."
        result = truncate_sentences(text, 2)
        assert "First." in result
        assert "Second." in result
        assert "Third." not in result

    def test_none_returns_all(self):
        text = "A. B. C."
        assert truncate_sentences(text, None) == text

    def test_zero_returns_all(self):
        text = "A. B. C."
        assert truncate_sentences(text, 0) == text


class TestBuildBulletList:
    def test_basic(self):
        result = build_bullet_list(["a", "b", "c"], max_items=2)
        assert result == ["a", "b"]

    def test_with_prefix(self):
        result = build_bullet_list(["item"], prefix="- ")
        assert result == ["- item"]


class TestBuildSourceSummary:
    def test_coverage_gaps_summary(self):
        s = build_source_summary(SAMPLE_GAPS, "coverage_gaps")
        assert s["response_type"] == "coverage_gaps"
        assert s["industry"] == "roofing contractor"
        assert s["risk_level"] == "high"
        assert s["missing_coverage_count"] == 3

    def test_readiness_summary(self):
        s = build_source_summary(SAMPLE_READINESS, "submission_readiness")
        assert s["readiness_score"] == 54
        assert s["missing_critical_count"] == 2


# ============================================================
# MEETING BRIEF REWRITE
# ============================================================


class TestMeetingBriefConcise:
    def setup_method(self):
        self.result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(mode="concise"))

    def test_has_rendered_and_original(self):
        assert "rendered" in self.result
        assert "original" in self.result

    def test_original_unchanged(self):
        assert self.result["original"] is SAMPLE_BRIEF

    def test_rendered_type(self):
        assert self.result["rendered"]["response_type"] == "meeting_brief"
        assert self.result["rendered"]["mode"] == "concise"

    def test_rendered_text_mentions_industry(self):
        assert "roofing contractor" in self.result["rendered"]["rendered_text"]

    def test_has_bullets(self):
        assert len(self.result["rendered"]["rendered_bullets"]) > 0

    def test_has_source_summary(self):
        assert "industry" in self.result["rendered"]["source_summary"]


class TestMeetingBriefConsultative:
    def setup_method(self):
        self.result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(mode="consultative"))

    def test_mode(self):
        assert self.result["rendered"]["mode"] == "consultative"

    def test_includes_talking_points(self):
        bullets = self.result["rendered"]["rendered_bullets"]
        assert any("Talking point" in b for b in bullets)

    def test_includes_questions(self):
        bullets = self.result["rendered"]["rendered_bullets"]
        assert any("Ask" in b for b in bullets)


class TestMeetingBriefTechnical:
    def test_mode(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(mode="technical"))
        assert result["rendered"]["mode"] == "technical"
        assert "exposure" in result["rendered"]["rendered_text"].lower() or \
               "Exposure" in " ".join(result["rendered"]["rendered_bullets"])


class TestMeetingBriefMeeting:
    def test_mode(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(mode="meeting_brief"))
        assert result["rendered"]["mode"] == "meeting_brief"
        text = result["rendered"]["rendered_text"]
        assert "meeting" in text.lower() or "Meeting" in text


# ============================================================
# COVERAGE GAPS REWRITE
# ============================================================


class TestCoverageGapsConcise:
    def setup_method(self):
        self.result = rewrite_coverage_gaps(SAMPLE_GAPS, RewriteOptions(mode="concise"))

    def test_rendered_type(self):
        assert self.result["rendered"]["response_type"] == "coverage_gaps"

    def test_mentions_risk_level(self):
        assert "high" in self.result["rendered"]["rendered_text"].lower()

    def test_prioritizes_workers_comp(self):
        text = self.result["rendered"]["rendered_text"]
        assert "Workers Compensation" in text

    def test_original_unchanged(self):
        assert self.result["original"]["missing_coverages"] == SAMPLE_GAPS["missing_coverages"]


class TestCoverageGapsConsultative:
    def test_mode(self):
        result = rewrite_coverage_gaps(SAMPLE_GAPS, RewriteOptions(mode="consultative"))
        assert result["rendered"]["mode"] == "consultative"
        assert "client" in result["rendered"]["rendered_text"].lower() or \
               "discuss" in " ".join(result["rendered"]["rendered_bullets"]).lower()


class TestCoverageGapsNoGaps:
    def test_no_gaps_message(self):
        data = {**SAMPLE_GAPS, "missing_coverages": []}
        result = rewrite_coverage_gaps(data, RewriteOptions(mode="concise"))
        assert "no identified coverage gaps" in result["rendered"]["rendered_text"].lower()


# ============================================================
# SUBMISSION READINESS REWRITE
# ============================================================


class TestReadinessConcise:
    def setup_method(self):
        self.result = rewrite_submission_readiness(SAMPLE_READINESS, RewriteOptions(mode="concise"))

    def test_includes_score(self):
        assert "54/100" in self.result["rendered"]["rendered_text"]

    def test_includes_next_steps_in_bullets(self):
        assert len(self.result["rendered"]["rendered_bullets"]) > 0

    def test_original_preserved(self):
        assert self.result["original"]["readiness_score"] == 54


class TestReadinessConsultative:
    def test_consultative_phrasing(self):
        result = rewrite_submission_readiness(SAMPLE_READINESS, RewriteOptions(mode="consultative"))
        text = result["rendered"]["rendered_text"]
        assert "fair" in text.lower()
        assert "Tighten" in text or "market" in text.lower()


class TestReadinessTechnical:
    def test_technical_mode(self):
        result = rewrite_submission_readiness(SAMPLE_READINESS, RewriteOptions(mode="technical"))
        assert result["rendered"]["mode"] == "technical"
        text = result["rendered"]["rendered_text"]
        assert "deficien" in text.lower() or "54/100" in text


# ============================================================
# TONE VARIATIONS
# ============================================================


class TestToneVariations:
    def test_confident_tone(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(tone="confident"))
        assert result["rendered"]["tone"] == "confident"

    def test_practical_tone(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(tone="practical"))
        assert result["rendered"]["tone"] == "practical"

    def test_neutral_tone(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(tone="neutral"))
        assert result["rendered"]["tone"] == "neutral"


# ============================================================
# OPTIONS EDGE CASES
# ============================================================


class TestOptionsEdgeCases:
    def test_none_options_uses_defaults(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, None)
        assert result["rendered"]["mode"] == DEFAULT_MODE
        assert result["rendered"]["tone"] == DEFAULT_TONE

    def test_max_bullets_truncates(self):
        opts = RewriteOptions(mode="consultative", max_bullets=2)
        result = rewrite_meeting_brief(SAMPLE_BRIEF, opts)
        assert len(result["rendered"]["rendered_bullets"]) <= 2

    def test_max_sentences_truncates(self):
        opts = RewriteOptions(mode="concise", max_sentences=1)
        result = rewrite_coverage_gaps(SAMPLE_GAPS, opts)
        text = result["rendered"]["rendered_text"]
        # Should have at most 1 sentence ending
        assert text.count(".") <= 2  # period at end of sentence + possible trailing

    def test_include_disclaimer(self):
        opts = RewriteOptions(include_disclaimer=True)
        result = rewrite_meeting_brief(SAMPLE_BRIEF, opts)
        assert "does not guarantee" in result["rendered"]["rendered_text"].lower()

    def test_invalid_mode_falls_back(self):
        opts = RewriteOptions(mode="banana")
        result = rewrite_meeting_brief(SAMPLE_BRIEF, opts)
        assert result["rendered"]["mode"] == DEFAULT_MODE


# ============================================================
# API ENDPOINTS WITH RENDER
# ============================================================


class TestMeetingBriefEndpointRender:
    def test_render_false_returns_original(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor")
        assert resp.status_code == 200
        data = resp.json()
        # Original response — no "rendered" key
        assert "top_exposures" in data
        assert "rendered" not in data

    def test_render_true_returns_both(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor&render=true&mode=concise")
        assert resp.status_code == 200
        data = resp.json()
        assert "rendered" in data
        assert "original" in data
        assert data["rendered"]["response_type"] == "meeting_brief"
        assert data["original"]["industry"] == "roofing contractor"

    def test_render_consultative(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor&render=true&mode=consultative&tone=practical")
        assert resp.status_code == 200
        data = resp.json()
        assert data["rendered"]["mode"] == "consultative"
        assert data["rendered"]["tone"] == "practical"


class TestCoverageGapsEndpointRender:
    def test_render_false_returns_original(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability")
        assert resp.status_code == 200
        data = resp.json()
        assert "missing_coverages" in data
        assert "rendered" not in data

    def test_render_true_returns_both(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability&render=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "rendered" in data
        assert "original" in data
        assert data["rendered"]["response_type"] == "coverage_gaps"


class TestSubmissionReadinessEndpointRender:
    def test_render_false_returns_original(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "industry": "roofing contractor",
            "submission_data": {"legal_entity_name": "Test Roofing LLC"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "readiness_score" in data
        assert "rendered" not in data

    def test_render_true_returns_both(self):
        resp = client.post(
            "/api/v1/submission/readiness?render=true&mode=consultative&tone=confident",
            json={
                "industry": "roofing contractor",
                "submission_data": {
                    "legal_entity_name": "Test Roofing LLC",
                    "annual_revenue": 1000000,
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rendered" in data
        assert "original" in data
        assert data["rendered"]["mode"] == "consultative"
        assert data["rendered"]["tone"] == "confident"
        assert data["original"]["readiness_score"] >= 0


# ============================================================
# REGRESSIONS
# ============================================================


class TestRegressions:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_meeting_brief_without_render(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_exposures" in data

    def test_risk_gaps_without_render(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability")
        assert resp.status_code == 200
        data = resp.json()
        assert "missing_coverages" in data

    def test_submission_readiness_without_render(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "industry": "restaurant",
            "submission_data": {},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_level"] == "poor"

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12

    def test_submission_templates_intact(self):
        from app.knowledge.submission_requirements import INDUSTRY_SUBMISSION_TEMPLATES
        assert len(INDUSTRY_SUBMISSION_TEMPLATES) >= 6
