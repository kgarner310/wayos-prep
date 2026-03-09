"""Tests for Model Router and AI Provider abstraction.

Tests cover:
- Base provider interface
- Claude provider (mocked)
- Model router routing and fallback
- AI usage telemetry recording
- Deterministic rewrite still works (use_llm=False)
- use_llm=True triggers router (mocked)
- API endpoints with use_llm flag
- Regressions
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.ai.providers.base_provider import AIProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.model_router import ModelRouter, get_model_router
from app.telemetry.ai_usage import (
    AI_USAGE_EVENTS,
    record_ai_usage,
    list_ai_usage,
    summarize_ai_usage,
)
from app.services.response_rewriter import (
    rewrite_meeting_brief,
    rewrite_coverage_gaps,
    rewrite_submission_readiness,
    render_with_llm,
)
from app.presentation.presentation_models import RewriteOptions
from app.main import app
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clear_ai_usage():
    AI_USAGE_EVENTS.clear()
    yield
    AI_USAGE_EVENTS.clear()


# ============================================================
# SAMPLE DATA
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


# ============================================================
# MOCK PROVIDER
# ============================================================


class MockProvider(AIProvider):
    """Test provider that returns canned responses."""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-v1"

    def generate_text(self, prompt, system_prompt=None, temperature=0.2, max_tokens=500):
        return {
            "text": "This is a mock LLM response.\n- Bullet one\n- Bullet two",
            "provider": "mock",
            "model": "mock-v1",
            "token_usage": {
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70,
            },
        }


# ============================================================
# BASE PROVIDER
# ============================================================


class TestBaseProvider:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            AIProvider()

    def test_mock_provider_implements_interface(self):
        p = MockProvider()
        assert p.provider_name == "mock"
        assert p.default_model == "mock-v1"
        result = p.generate_text("test prompt")
        assert result["text"] == "This is a mock LLM response.\n- Bullet one\n- Bullet two"


# ============================================================
# CLAUDE PROVIDER
# ============================================================


class TestClaudeProvider:
    def test_provider_name(self):
        p = ClaudeProvider()
        assert p.provider_name == "claude"

    def test_no_api_key_returns_error(self):
        p = ClaudeProvider(api_key="")
        result = p.generate_text("test")
        assert "not available" in result["text"].lower() or "error" in result["text"].lower()

    def test_empty_response_helper(self):
        p = ClaudeProvider()
        r = p._empty_response("test error")
        assert r["text"] == "test error"
        assert r["provider"] == "claude"


# ============================================================
# MODEL ROUTER
# ============================================================


class TestModelRouter:
    def test_router_creation(self):
        router = ModelRouter()
        assert router is not None

    def test_register_custom_provider(self):
        router = ModelRouter()
        mock = MockProvider()
        router.register_provider("mock", mock)
        router.set_route("rewrite_response", "mock")
        assert router.get_provider("rewrite_response") is mock

    def test_router_generates_with_mock(self):
        router = ModelRouter()
        mock = MockProvider()
        router.register_provider("mock", mock)
        router.set_route("rewrite_response", "mock")

        result = router.generate_text(
            task_type="rewrite_response",
            prompt="test prompt",
        )
        assert result["text"] == "This is a mock LLM response.\n- Bullet one\n- Bullet two"
        assert result["provider"] == "mock"

    def test_router_logs_ai_usage(self):
        router = ModelRouter()
        mock = MockProvider()
        router.register_provider("mock", mock)
        router.set_route("rewrite_response", "mock")

        router.generate_text(
            task_type="rewrite_response",
            prompt="test",
            office_id="test-office",
            endpoint="/meeting/brief",
        )
        assert len(AI_USAGE_EVENTS) == 1
        assert AI_USAGE_EVENTS[0].provider == "mock"
        assert AI_USAGE_EVENTS[0].task_type == "rewrite_response"

    def test_unknown_task_type_returns_error(self):
        router = ModelRouter()
        # Remove all providers
        router._providers = {}
        result = router.generate_text(task_type="nonexistent", prompt="test")
        assert "error" in result

    def test_singleton(self):
        r1 = get_model_router()
        r2 = get_model_router()
        assert r1 is r2


# ============================================================
# AI USAGE TELEMETRY
# ============================================================


class TestAIUsageTelemetry:
    def test_record_usage(self):
        result = record_ai_usage(
            provider="mock", model="mock-v1", task_type="rewrite_response",
            token_usage={"total_tokens": 70},
        )
        assert result["provider"] == "mock"
        assert len(AI_USAGE_EVENTS) == 1

    def test_list_usage(self):
        record_ai_usage("mock", "mock-v1", "rewrite_response")
        record_ai_usage("claude", "claude-3", "explanation")
        assert len(list_ai_usage()) == 2
        assert len(list_ai_usage(provider="mock")) == 1
        assert len(list_ai_usage(task_type="explanation")) == 1

    def test_summarize_usage(self):
        record_ai_usage("mock", "mock-v1", "rewrite_response", {"total_tokens": 50})
        record_ai_usage("mock", "mock-v1", "explanation", {"total_tokens": 30})
        summary = summarize_ai_usage()
        assert summary["total_calls"] == 2
        assert summary["total_tokens"] == 80
        assert summary["by_provider"]["mock"] == 2


# ============================================================
# DETERMINISTIC REWRITE STILL WORKS
# ============================================================


class TestDeterministicRewrite:
    def test_default_uses_templates(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions())
        assert "rendered" in result
        assert "original" in result
        assert result["original"] is SAMPLE_BRIEF

    def test_use_llm_false_uses_templates(self):
        result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(), use_llm=False)
        assert "roofing contractor" in result["rendered"]["rendered_text"]

    def test_coverage_gaps_deterministic(self):
        result = rewrite_coverage_gaps(SAMPLE_GAPS, RewriteOptions(), use_llm=False)
        assert "high" in result["rendered"]["rendered_text"].lower()


# ============================================================
# LLM RENDERING (MOCKED)
# ============================================================


class TestLLMRendering:
    def test_use_llm_true_calls_router(self):
        mock_response = {
            "text": "LLM rewritten summary.\n- Key point one\n- Key point two",
            "provider": "mock",
            "model": "mock-v1",
            "token_usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        }
        with patch("app.ai.model_router.get_model_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate_text.return_value = mock_response
            mock_get.return_value = mock_router

            result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(), use_llm=True)
            assert "LLM rewritten summary" in result["rendered"]["rendered_text"]
            assert "Key point one" in result["rendered"]["rendered_bullets"]
            mock_router.generate_text.assert_called_once()

    def test_llm_failure_falls_back_to_templates(self):
        mock_response = {
            "text": "",
            "provider": "mock",
            "model": "mock-v1",
            "token_usage": {},
            "error": "Provider unavailable",
        }
        with patch("app.ai.model_router.get_model_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate_text.return_value = mock_response
            mock_get.return_value = mock_router

            result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(), use_llm=True)
            # Should fall back to template
            assert "roofing contractor" in result["rendered"]["rendered_text"]

    def test_use_llm_preserves_original(self):
        mock_response = {
            "text": "LLM text.\n- Bullet",
            "provider": "mock",
            "model": "mock-v1",
            "token_usage": {"total_tokens": 30},
        }
        with patch("app.ai.model_router.get_model_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate_text.return_value = mock_response
            mock_get.return_value = mock_router

            result = rewrite_coverage_gaps(SAMPLE_GAPS, RewriteOptions(), use_llm=True)
            assert result["original"] is SAMPLE_GAPS

    def test_use_llm_has_output_id(self):
        mock_response = {
            "text": "LLM text.\n- Bullet",
            "provider": "mock",
            "model": "mock-v1",
            "token_usage": {},
        }
        with patch("app.ai.model_router.get_model_router") as mock_get:
            mock_router = MagicMock()
            mock_router.generate_text.return_value = mock_response
            mock_get.return_value = mock_router

            result = rewrite_meeting_brief(SAMPLE_BRIEF, RewriteOptions(), use_llm=True)
            assert result["rendered"]["output_id"].startswith("out_")


# ============================================================
# API ENDPOINTS WITH use_llm
# ============================================================


class TestAPIWithUseLLM:
    def test_meeting_brief_use_llm_false(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor&render=true&use_llm=false")
        assert resp.status_code == 200
        data = resp.json()
        assert "rendered" in data
        # Template rendering — deterministic
        assert "roofing contractor" in data["rendered"]["rendered_text"]

    def test_gaps_use_llm_false(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability&render=true&use_llm=false")
        assert resp.status_code == 200
        assert "rendered" in resp.json()

    def test_submission_use_llm_false(self):
        resp = client.post(
            "/api/v1/submission/readiness?render=true&use_llm=false",
            json={"industry": "roofing contractor", "submission_data": {"legal_entity_name": "Test"}},
        )
        assert resp.status_code == 200
        assert "rendered" in resp.json()

    def test_no_render_ignores_use_llm(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor&use_llm=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_exposures" in data
        assert "rendered" not in data


# ============================================================
# REGRESSIONS
# ============================================================


class TestRegressions:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_meeting_brief_default(self):
        resp = client.get("/api/v1/meeting/brief?industry=roofing+contractor")
        assert resp.status_code == 200
        assert "top_exposures" in resp.json()

    def test_risk_gaps_default(self):
        resp = client.get("/api/v1/risk/gaps?industry=roofing+contractor&current_policies=general+liability")
        assert resp.status_code == 200
        assert "missing_coverages" in resp.json()

    def test_submission_default(self):
        resp = client.post("/api/v1/submission/readiness", json={
            "industry": "restaurant", "submission_data": {},
        })
        assert resp.status_code == 200
        assert resp.json()["readiness_level"] == "poor"

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12

    def test_telemetry_endpoints_still_work(self):
        resp = client.get("/api/v1/telemetry/rendered-output/summary")
        assert resp.status_code == 200
