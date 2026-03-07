"""Tests for Telemetry Store — rendered output tracking and feedback capture.

Tests cover:
- Telemetry models
- Event recording (shown, copied)
- Feedback recording (up, down, edited)
- Edit capture stores edited_text
- Summary counts
- Filtering by office_id, endpoint, etc.
- Auto-record shown events on render=true
- Telemetry API endpoints
- Learning store bridge for negative feedback
- Regressions
"""

import pytest
from fastapi.testclient import TestClient

from app.telemetry.telemetry_models import (
    RenderedOutputEvent,
    RenderedOutputFeedback,
    VALID_EVENT_TYPES,
    VALID_FEEDBACK_TYPES,
)
from app.services.telemetry_store import (
    RENDERED_OUTPUT_EVENTS,
    RENDERED_OUTPUT_FEEDBACK,
    record_rendered_output_event,
    record_rendered_output_feedback,
    list_rendered_output_events,
    list_rendered_output_feedback,
    summarize_rendered_output_telemetry,
    count_by_key,
    safe_feedback_sentiment,
    summarize_endpoint_usage,
    summarize_mode_usage,
)
from app.services.response_rewriter import (
    rewrite_meeting_brief,
    rewrite_coverage_gaps,
    rewrite_submission_readiness,
)
from app.presentation.presentation_models import RewriteOptions
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_telemetry():
    """Clear telemetry stores before and after each test."""
    RENDERED_OUTPUT_EVENTS.clear()
    RENDERED_OUTPUT_FEEDBACK.clear()
    yield
    RENDERED_OUTPUT_EVENTS.clear()
    RENDERED_OUTPUT_FEEDBACK.clear()


# ============================================================
# MODELS
# ============================================================


class TestTelemetryModels:
    def test_event_to_dict(self):
        e = RenderedOutputEvent(event_id="e1", event_type="rendered_output_shown")
        d = e.to_dict()
        assert d["event_id"] == "e1"
        assert d["event_type"] == "rendered_output_shown"

    def test_feedback_to_dict(self):
        f = RenderedOutputFeedback(output_id="o1", feedback_type="up")
        d = f.to_dict()
        assert d["output_id"] == "o1"
        assert d["feedback_type"] == "up"

    def test_valid_event_types(self):
        assert "rendered_output_shown" in VALID_EVENT_TYPES
        assert "rendered_output_copied" in VALID_EVENT_TYPES
        assert "rendered_output_edited" in VALID_EVENT_TYPES

    def test_valid_feedback_types(self):
        assert "up" in VALID_FEEDBACK_TYPES
        assert "down" in VALID_FEEDBACK_TYPES
        assert "edited" in VALID_FEEDBACK_TYPES


# ============================================================
# EVENT RECORDING
# ============================================================


class TestRecordEvent:
    def test_record_shown_event(self):
        result = record_rendered_output_event(
            event_type="rendered_output_shown",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
        )
        assert result["event_type"] == "rendered_output_shown"
        assert result["endpoint"] == "/meeting/brief"
        assert len(RENDERED_OUTPUT_EVENTS) == 1

    def test_record_copied_event(self):
        result = record_rendered_output_event(
            event_type="rendered_output_copied",
            endpoint="/risk/gaps",
            response_type="coverage_gaps",
            mode="consultative",
            tone="practical",
            office_id="demo-roofing-nc",
            industry="roofing contractor",
            output_id="out_abc123",
        )
        assert result["event_type"] == "rendered_output_copied"
        assert result["office_id"] == "demo-roofing-nc"
        assert result["output_id"] == "out_abc123"

    def test_event_has_uuid_id(self):
        result = record_rendered_output_event(
            event_type="rendered_output_shown",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
        )
        assert result["event_id"]  # not empty

    def test_event_has_timestamp(self):
        result = record_rendered_output_event(
            event_type="rendered_output_shown",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
        )
        assert result["created_at"]

    def test_invalid_event_type_defaults(self):
        result = record_rendered_output_event(
            event_type="invalid_type",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
        )
        assert result["event_type"] == "rendered_output_shown"

    def test_metadata_stored(self):
        result = record_rendered_output_event(
            event_type="rendered_output_shown",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
            metadata={"bullet_count": 3, "text_length": 120},
        )
        assert result["metadata"]["bullet_count"] == 3


# ============================================================
# FEEDBACK RECORDING
# ============================================================


class TestRecordFeedback:
    def test_record_up_feedback(self):
        result = record_rendered_output_feedback(
            output_id="out_123",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
            feedback_type="up",
        )
        assert result["feedback_type"] == "up"
        assert result["output_id"] == "out_123"
        assert len(RENDERED_OUTPUT_FEEDBACK) == 1

    def test_record_down_feedback(self):
        result = record_rendered_output_feedback(
            output_id="out_456",
            endpoint="/risk/gaps",
            response_type="coverage_gaps",
            mode="technical",
            tone="neutral",
            feedback_type="down",
            feedback_note="Too vague",
        )
        assert result["feedback_type"] == "down"
        assert result["feedback_note"] == "Too vague"

    def test_edited_feedback_stores_text(self):
        result = record_rendered_output_feedback(
            output_id="out_789",
            endpoint="/submission/readiness",
            response_type="submission_readiness",
            mode="consultative",
            tone="practical",
            feedback_type="edited",
            edited_text="I rewrote this section to be clearer.",
        )
        assert result["feedback_type"] == "edited"
        assert result["edited_text"] == "I rewrote this section to be clearer."

    def test_non_edited_ignores_edited_text(self):
        result = record_rendered_output_feedback(
            output_id="out_111",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
            feedback_type="up",
            edited_text="This should be ignored",
        )
        assert result["edited_text"] is None

    def test_feedback_has_timestamp(self):
        result = record_rendered_output_feedback(
            output_id="out_222",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
            feedback_type="useful",
        )
        assert result["created_at"]


# ============================================================
# FILTERING
# ============================================================


class TestFiltering:
    def setup_method(self):
        record_rendered_output_event(
            "rendered_output_shown", "/meeting/brief", "meeting_brief", "concise", "neutral",
            office_id="office-a", industry="roofing contractor",
        )
        record_rendered_output_event(
            "rendered_output_copied", "/risk/gaps", "coverage_gaps", "consultative", "practical",
            office_id="office-b", industry="restaurant",
        )
        record_rendered_output_event(
            "rendered_output_shown", "/meeting/brief", "meeting_brief", "technical", "confident",
            office_id="office-a", industry="roofing contractor",
        )

    def test_filter_by_office_id(self):
        events = list_rendered_output_events(office_id="office-a")
        assert len(events) == 2

    def test_filter_by_industry(self):
        events = list_rendered_output_events(industry="restaurant")
        assert len(events) == 1

    def test_filter_by_endpoint(self):
        events = list_rendered_output_events(endpoint="/meeting/brief")
        assert len(events) == 2

    def test_filter_by_event_type(self):
        events = list_rendered_output_events(event_type="rendered_output_copied")
        assert len(events) == 1

    def test_no_filter_returns_all(self):
        events = list_rendered_output_events()
        assert len(events) == 3


class TestFeedbackFiltering:
    def setup_method(self):
        record_rendered_output_feedback(
            "o1", "/meeting/brief", "meeting_brief", "concise", "neutral",
            "up", office_id="office-a", industry="roofing contractor",
        )
        record_rendered_output_feedback(
            "o2", "/risk/gaps", "coverage_gaps", "technical", "neutral",
            "down", office_id="office-b", industry="restaurant",
        )

    def test_filter_feedback_by_office(self):
        fb = list_rendered_output_feedback(office_id="office-a")
        assert len(fb) == 1

    def test_filter_feedback_by_type(self):
        fb = list_rendered_output_feedback(feedback_type="down")
        assert len(fb) == 1


# ============================================================
# ANALYTICS HELPERS
# ============================================================


class TestAnalyticsHelpers:
    def test_count_by_key(self):
        events = [
            RenderedOutputEvent(event_id="1", event_type="shown", endpoint="/a", mode="concise"),
            RenderedOutputEvent(event_id="2", event_type="shown", endpoint="/a", mode="technical"),
            RenderedOutputEvent(event_id="3", event_type="shown", endpoint="/b", mode="concise"),
        ]
        result = count_by_key(events, "endpoint")
        assert result["/a"] == 2
        assert result["/b"] == 1

    def test_safe_feedback_sentiment(self):
        fb_list = [
            RenderedOutputFeedback(output_id="1", feedback_type="up"),
            RenderedOutputFeedback(output_id="2", feedback_type="useful"),
            RenderedOutputFeedback(output_id="3", feedback_type="down"),
            RenderedOutputFeedback(output_id="4", feedback_type="edited"),
        ]
        result = safe_feedback_sentiment(fb_list)
        assert result["positive"] == 2
        assert result["negative"] == 1
        assert result["edited"] == 1

    def test_summarize_endpoint_usage(self):
        events = [
            RenderedOutputEvent(event_id="1", event_type="shown", endpoint="/a"),
            RenderedOutputEvent(event_id="2", event_type="shown", endpoint="/a"),
        ]
        result = summarize_endpoint_usage(events)
        assert result["/a"] == 2

    def test_summarize_mode_usage(self):
        events = [
            RenderedOutputEvent(event_id="1", event_type="shown", mode="concise"),
            RenderedOutputEvent(event_id="2", event_type="shown", mode="consultative"),
            RenderedOutputEvent(event_id="3", event_type="shown", mode="concise"),
        ]
        result = summarize_mode_usage(events)
        assert result["concise"] == 2
        assert result["consultative"] == 1


# ============================================================
# SUMMARY
# ============================================================


class TestSummary:
    def test_summary_empty(self):
        result = summarize_rendered_output_telemetry()
        assert result["total_render_events"] == 0
        assert result["total_feedback_events"] == 0

    def test_summary_with_data(self):
        record_rendered_output_event(
            "rendered_output_shown", "/meeting/brief", "meeting_brief",
            "concise", "neutral", industry="roofing contractor",
        )
        record_rendered_output_event(
            "rendered_output_copied", "/meeting/brief", "meeting_brief",
            "consultative", "practical", industry="roofing contractor",
        )
        record_rendered_output_feedback(
            "o1", "/meeting/brief", "meeting_brief", "concise", "neutral",
            "up", industry="roofing contractor",
        )
        record_rendered_output_feedback(
            "o2", "/meeting/brief", "meeting_brief", "concise", "neutral",
            "down", industry="roofing contractor",
        )

        result = summarize_rendered_output_telemetry()
        assert result["total_render_events"] == 2
        assert result["total_feedback_events"] == 2
        assert result["positive_feedback_count"] == 1
        assert result["negative_feedback_count"] == 1
        assert result["by_endpoint"]["/meeting/brief"] == 2
        assert "concise" in result["by_mode"]

    def test_summary_filtered_by_industry(self):
        record_rendered_output_event(
            "rendered_output_shown", "/meeting/brief", "meeting_brief",
            "concise", "neutral", industry="roofing contractor",
        )
        record_rendered_output_event(
            "rendered_output_shown", "/meeting/brief", "meeting_brief",
            "concise", "neutral", industry="restaurant",
        )

        result = summarize_rendered_output_telemetry(industry="restaurant")
        assert result["total_render_events"] == 1


# ============================================================
# AUTO-RECORD SHOWN ON RENDER
# ============================================================


SAMPLE_BRIEF = {
    "industry": "roofing contractor",
    "top_exposures": ["falls from height"],
    "common_claims": ["worker fall injuries"],
    "recommended_talking_points": ["Ask about fall protection"],
    "discovery_questions": ["Do you have a safety program?"],
    "coverage_watchouts": [],
    "office_learnings": [],
}

SAMPLE_GAPS = {
    "industry": "roofing contractor",
    "missing_coverages": ["workers compensation"],
    "risk_level": "high",
    "recommended_questions": [],
    "top_exposures": [],
    "office_learnings": [],
}

SAMPLE_READINESS = {
    "industry": "roofing contractor",
    "readiness_score": 54,
    "readiness_level": "fair",
    "missing_critical_fields": ["Total Payroll"],
    "missing_recommended_fields": [],
    "weak_fields": [],
    "strengths": [],
    "next_steps": ["Obtain Total Payroll"],
    "office_learnings": [],
    "explanation": "Fair.",
}


class TestAutoRecordShown:
    def test_meeting_brief_render_records_event(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions())
        assert "output_id" in result["rendered"]
        assert result["rendered"]["output_id"].startswith("out_")
        assert len(RENDERED_OUTPUT_EVENTS) == 1
        assert RENDERED_OUTPUT_EVENTS[0].event_type == "rendered_output_shown"

    def test_coverage_gaps_render_records_event(self):
        result = rewrite_coverage_gaps(SAMPLE_GAPS, RewriteOptions())
        assert "output_id" in result["rendered"]
        assert len(RENDERED_OUTPUT_EVENTS) == 1

    def test_submission_readiness_render_records_event(self):
        result = rewrite_submission_readiness(SAMPLE_READINESS, RewriteOptions())
        assert "output_id" in result["rendered"]
        assert len(RENDERED_OUTPUT_EVENTS) == 1

    def test_shown_event_captures_metadata(self):
        rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions())
        event = RENDERED_OUTPUT_EVENTS[0]
        assert "bullet_count" in event.metadata
        assert "text_length" in event.metadata

    def test_shown_event_captures_industry(self):
        rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions())
        assert RENDERED_OUTPUT_EVENTS[0].industry == "roofing contractor"

    def test_shown_event_captures_office_id(self):
        rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(), office_id="test-office")
        assert RENDERED_OUTPUT_EVENTS[0].office_id == "test-office"

    def test_original_unchanged(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions())
        assert result["original"] is SAMPLE_BRIEF


# ============================================================
# API ENDPOINTS
# ============================================================


class TestTelemetryEventEndpoint:
    def test_post_event(self):
        resp = client.post("/api/v1/telemetry/rendered-output/event", json={
            "event_type": "rendered_output_copied",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
            "output_id": "out_abc123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["event"]["event_type"] == "rendered_output_copied"

    def test_post_event_missing_fields(self):
        resp = client.post("/api/v1/telemetry/rendered-output/event", json={
            "mode": "concise",
        })
        assert resp.status_code == 400

    def test_list_events(self):
        client.post("/api/v1/telemetry/rendered-output/event", json={
            "event_type": "rendered_output_shown",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
        })
        resp = client.get("/api/v1/telemetry/rendered-output/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1


class TestTelemetryFeedbackEndpoint:
    def test_post_feedback(self):
        resp = client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "output_id": "out_123",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
            "feedback_type": "up",
            "feedback_note": "Very useful",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["feedback"]["feedback_type"] == "up"

    def test_post_edited_feedback(self):
        resp = client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "output_id": "out_456",
            "endpoint": "/risk/gaps",
            "response_type": "coverage_gaps",
            "mode": "consultative",
            "tone": "practical",
            "feedback_type": "edited",
            "edited_text": "My revised version of the output.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["feedback"]["edited_text"] == "My revised version of the output."

    def test_post_feedback_missing_fields(self):
        resp = client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "feedback_note": "no output_id",
        })
        assert resp.status_code == 400

    def test_list_feedback(self):
        client.post("/api/v1/telemetry/rendered-output/feedback", json={
            "output_id": "out_999",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
            "feedback_type": "useful",
        })
        resp = client.get("/api/v1/telemetry/rendered-output/feedback")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1


class TestTelemetrySummaryEndpoint:
    def test_summary_empty(self):
        resp = client.get("/api/v1/telemetry/rendered-output/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_render_events"] == 0

    def test_summary_with_events(self):
        client.post("/api/v1/telemetry/rendered-output/event", json={
            "event_type": "rendered_output_shown",
            "endpoint": "/meeting/brief",
            "response_type": "meeting_brief",
            "mode": "concise",
            "tone": "neutral",
            "industry": "roofing contractor",
        })
        resp = client.get("/api/v1/telemetry/rendered-output/summary")
        assert resp.status_code == 200
        assert resp.json()["total_render_events"] >= 1


class TestRenderEndpointsRecordEvents:
    def test_meeting_brief_render_true(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor&render=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "output_id" in data["rendered"]
        # Check event was auto-recorded
        events = list_rendered_output_events()
        assert any(e["event_type"] == "rendered_output_shown" for e in events)

    def test_meeting_brief_render_false_no_event(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor")
        assert resp.status_code == 200
        # No render, no telemetry event
        events = list_rendered_output_events()
        assert len(events) == 0

    def test_gaps_render_true(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability&render=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "output_id" in data["rendered"]

    def test_submission_render_true(self):
        resp = client.post(
            "/api/v1/submission/readiness?render=true",
            json={
                "industry": "roofing contractor",
                "submission_data": {"legal_entity_name": "Test"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "output_id" in data["rendered"]


# ============================================================
# LEARNING STORE BRIDGE
# ============================================================


class TestLearningStoreBridge:
    def test_negative_feedback_bridges(self):
        from app.services.learning_store import PRODUCER_FEEDBACK
        PRODUCER_FEEDBACK.clear()

        record_rendered_output_feedback(
            output_id="out_bridge",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
            feedback_type="down",
            office_id="test-office",
            industry="roofing contractor",
            feedback_note="Not useful for this client",
        )
        # Should have bridged to learning store
        assert any(
            f.feedback_type == "down" and f.office_id == "test-office"
            for f in PRODUCER_FEEDBACK
        )
        PRODUCER_FEEDBACK.clear()

    def test_positive_feedback_does_not_bridge(self):
        from app.services.learning_store import PRODUCER_FEEDBACK
        PRODUCER_FEEDBACK.clear()

        record_rendered_output_feedback(
            output_id="out_pos",
            endpoint="/meeting/brief",
            response_type="meeting_brief",
            mode="concise",
            tone="neutral",
            feedback_type="up",
            office_id="test-office",
            industry="roofing contractor",
        )
        # Positive feedback should NOT bridge
        bridged = [f for f in PRODUCER_FEEDBACK if f.office_id == "test-office"]
        assert len(bridged) == 0
        PRODUCER_FEEDBACK.clear()


# ============================================================
# REGRESSIONS
# ============================================================


class TestRegressions:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_meeting_brief_unchanged(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_exposures" in data
        assert "rendered" not in data

    def test_risk_gaps_unchanged(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability")
        assert resp.status_code == 200
        data = resp.json()
        assert "missing_coverages" in data
        assert "rendered" not in data

    def test_submission_readiness_unchanged(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "industry": "restaurant",
            "submission_data": {},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["readiness_level"] == "poor"
        assert "rendered" not in data

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12
