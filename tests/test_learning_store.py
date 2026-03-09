"""Tests for Learning Store — office learnings and producer feedback."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.knowledge.learning_models import OfficeLearning, ProducerFeedback
from app.services.learning_store import (
    OFFICE_LEARNINGS,
    PRODUCER_FEEDBACK,
    add_office_learning,
    list_office_learnings,
    add_producer_feedback,
    list_producer_feedback,
    get_office_context,
    seed_demo_learnings,
)


@pytest.fixture(autouse=True)
def clean_store():
    """Clear in-memory stores before each test."""
    OFFICE_LEARNINGS.clear()
    PRODUCER_FEEDBACK.clear()
    yield
    OFFICE_LEARNINGS.clear()
    PRODUCER_FEEDBACK.clear()


# ============================================================
# DATACLASS MODELS
# ============================================================


class TestLearningModels:

    def test_office_learning_to_dict(self):
        ol = OfficeLearning(
            office_id="test", industry="roofing", note="test note",
            created_at="2026-01-01T00:00:00", confidence=0.7, tags=["a"],
        )
        d = ol.to_dict()
        assert d["office_id"] == "test"
        assert d["industry"] == "roofing"
        assert d["note"] == "test note"
        assert d["confidence"] == 0.7
        assert d["tags"] == ["a"]

    def test_producer_feedback_to_dict(self):
        pf = ProducerFeedback(
            office_id="test", industry="roofing", endpoint="/risk/gaps",
            input_payload={"a": 1}, output_payload={"b": 2},
            feedback_type="up", feedback_note="good",
            created_at="2026-01-01T00:00:00",
        )
        d = pf.to_dict()
        assert d["office_id"] == "test"
        assert d["feedback_type"] == "up"
        assert d["input_payload"] == {"a": 1}

    def test_office_learning_defaults(self):
        ol = OfficeLearning(
            office_id="x", industry="y", note="z", created_at="now",
        )
        assert ol.created_by is None
        assert ol.confidence == 0.5
        assert ol.tags == []

    def test_producer_feedback_defaults(self):
        pf = ProducerFeedback(
            office_id="x", industry="y", endpoint="/test",
            input_payload={}, output_payload={}, feedback_type="up",
        )
        assert pf.feedback_note is None
        assert pf.created_at == ""


# ============================================================
# OFFICE LEARNINGS STORE
# ============================================================


class TestOfficeLearnings:

    def test_add_learning(self):
        result = add_office_learning("office1", "roofing", "Test note")
        assert result["office_id"] == "office1"
        assert result["industry"] == "roofing"
        assert result["note"] == "Test note"
        assert result["created_at"]
        assert len(OFFICE_LEARNINGS) == 1

    def test_add_with_metadata(self):
        result = add_office_learning(
            "office1", "roofing", "Note",
            created_by="jane", confidence=0.9, tags=["safety"],
        )
        assert result["created_by"] == "jane"
        assert result["confidence"] == 0.9
        assert result["tags"] == ["safety"]

    def test_list_all(self):
        add_office_learning("office1", "roofing", "Note 1")
        add_office_learning("office2", "hvac", "Note 2")
        results = list_office_learnings()
        assert len(results) == 2

    def test_filter_by_office(self):
        add_office_learning("office1", "roofing", "Note 1")
        add_office_learning("office2", "hvac", "Note 2")
        results = list_office_learnings(office_id="office1")
        assert len(results) == 1
        assert results[0]["office_id"] == "office1"

    def test_filter_by_industry(self):
        add_office_learning("office1", "roofing", "Note 1")
        add_office_learning("office1", "hvac", "Note 2")
        results = list_office_learnings(industry="roofing")
        assert len(results) == 1
        assert results[0]["industry"] == "roofing"

    def test_filter_by_both(self):
        add_office_learning("office1", "roofing", "A")
        add_office_learning("office1", "hvac", "B")
        add_office_learning("office2", "roofing", "C")
        results = list_office_learnings(office_id="office1", industry="roofing")
        assert len(results) == 1
        assert results[0]["note"] == "A"

    def test_industry_normalized(self):
        add_office_learning("o1", "  ROOFING  ", "Note")
        results = list_office_learnings(industry="roofing")
        assert len(results) == 1


# ============================================================
# PRODUCER FEEDBACK STORE
# ============================================================


class TestProducerFeedback:

    def test_add_feedback(self):
        result = add_producer_feedback(
            "office1", "roofing", "/risk/gaps",
            {"industry": "roofing"}, {"risk_level": "high"},
            "up",
        )
        assert result["office_id"] == "office1"
        assert result["feedback_type"] == "up"
        assert len(PRODUCER_FEEDBACK) == 1

    def test_add_with_note(self):
        result = add_producer_feedback(
            "office1", "roofing", "/meeting/brief",
            {}, {}, "down", feedback_note="Missing local context",
        )
        assert result["feedback_note"] == "Missing local context"

    def test_list_all(self):
        add_producer_feedback("o1", "roofing", "/a", {}, {}, "up")
        add_producer_feedback("o2", "hvac", "/b", {}, {}, "down")
        results = list_producer_feedback()
        assert len(results) == 2

    def test_filter_by_office(self):
        add_producer_feedback("o1", "roofing", "/a", {}, {}, "up")
        add_producer_feedback("o2", "hvac", "/b", {}, {}, "down")
        results = list_producer_feedback(office_id="o1")
        assert len(results) == 1

    def test_filter_by_industry(self):
        add_producer_feedback("o1", "roofing", "/a", {}, {}, "up")
        add_producer_feedback("o1", "hvac", "/b", {}, {}, "down")
        results = list_producer_feedback(industry="hvac")
        assert len(results) == 1


# ============================================================
# OFFICE CONTEXT
# ============================================================


class TestOfficeContext:

    def test_empty_context(self):
        ctx = get_office_context("unknown", "roofing")
        assert ctx["office_id"] == "unknown"
        assert ctx["learning_count"] == 0
        assert ctx["feedback_count"] == 0

    def test_context_with_data(self):
        add_office_learning("o1", "roofing", "Note 1")
        add_office_learning("o1", "roofing", "Note 2")
        add_producer_feedback("o1", "roofing", "/a", {}, {}, "up")
        add_producer_feedback("o1", "roofing", "/b", {}, {}, "down")
        add_producer_feedback("o1", "roofing", "/c", {}, {}, "useful")

        ctx = get_office_context("o1", "roofing")
        assert ctx["learning_count"] == 2
        assert ctx["feedback_count"] == 3
        assert ctx["positive_feedback_count"] == 2  # up + useful
        assert ctx["negative_feedback_count"] == 1  # down
        assert len(ctx["learnings"]) == 2

    def test_context_filters_by_office_and_industry(self):
        add_office_learning("o1", "roofing", "A")
        add_office_learning("o2", "roofing", "B")
        add_office_learning("o1", "hvac", "C")

        ctx = get_office_context("o1", "roofing")
        assert ctx["learning_count"] == 1
        assert ctx["learnings"][0]["note"] == "A"


# ============================================================
# DEMO SEED
# ============================================================


class TestDemoSeed:

    def test_seed_demo_learnings(self):
        count = seed_demo_learnings()
        assert count == 3
        assert len(OFFICE_LEARNINGS) == 3

    def test_seed_idempotent(self):
        seed_demo_learnings()
        count2 = seed_demo_learnings()
        assert count2 == 0
        assert len(OFFICE_LEARNINGS) == 3

    def test_seed_content(self):
        seed_demo_learnings()
        offices = {l.office_id for l in OFFICE_LEARNINGS}
        assert "demo-roofing-nc" in offices
        assert "demo-landscaping-tx" in offices
        assert "demo-restaurant-ca" in offices


# ============================================================
# API ENDPOINTS
# ============================================================


class TestLearningEndpoints:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_post_office_learning(self, client):
        resp = client.post("/api/v1/learning/office", json={
            "office_id": "test-office",
            "industry": "roofing",
            "note": "Test note from API",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["learning"]["note"] == "Test note from API"

    def test_post_office_learning_with_metadata(self, client):
        resp = client.post("/api/v1/learning/office", json={
            "office_id": "test-office",
            "industry": "roofing",
            "note": "With metadata",
            "created_by": "jane",
            "confidence": 0.9,
            "tags": ["safety", "training"],
        })
        assert resp.status_code == 200
        data = resp.json()["learning"]
        assert data["created_by"] == "jane"
        assert data["confidence"] == 0.9
        assert data["tags"] == ["safety", "training"]

    def test_post_office_learning_missing_fields(self, client):
        resp = client.post("/api/v1/learning/office", json={"office_id": "x"})
        assert resp.status_code == 400

    def test_get_office_learnings(self, client):
        client.post("/api/v1/learning/office", json={
            "office_id": "o1", "industry": "roofing", "note": "N1",
        })
        resp = client.get("/api/v1/learning/office?office_id=o1")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_post_feedback(self, client):
        resp = client.post("/api/v1/learning/feedback", json={
            "office_id": "o1",
            "industry": "roofing",
            "endpoint": "/meeting/brief",
            "input_payload": {"industry": "roofing"},
            "output_payload": {"top_exposures": ["falls"]},
            "feedback_type": "up",
            "feedback_note": "Very helpful",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_post_feedback_missing_fields(self, client):
        resp = client.post("/api/v1/learning/feedback", json={"office_id": "x"})
        assert resp.status_code == 400

    def test_get_feedback(self, client):
        client.post("/api/v1/learning/feedback", json={
            "office_id": "o1", "industry": "roofing",
            "endpoint": "/a", "input_payload": {}, "output_payload": {},
            "feedback_type": "up",
        })
        resp = client.get("/api/v1/learning/feedback?office_id=o1")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_get_context(self, client):
        client.post("/api/v1/learning/office", json={
            "office_id": "o1", "industry": "roofing", "note": "Note",
        })
        resp = client.get("/api/v1/learning/context?office_id=o1&industry=roofing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["office_id"] == "o1"
        assert data["learning_count"] >= 1

    def test_get_context_missing_params(self, client):
        resp = client.get("/api/v1/learning/context?office_id=o1")
        assert resp.status_code == 400

    def test_seed_demo_endpoint(self, client):
        resp = client.post("/api/v1/learning/seed-demo")
        assert resp.status_code == 200
        assert resp.json()["learnings_added"] == 3


# ============================================================
# MEETING BRIEF INTEGRATION
# ============================================================


class TestMeetingBriefWithLearnings:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_brief_without_office_id(self, client):
        resp = client.get("/api/v1/meeting/brief?industry=roofing")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_exposures" in data
        assert "office_learnings" in data

    def test_brief_with_office_id(self, client):
        # Add a learning first
        add_office_learning("test-office", "roofing contractor", "Custom roofing note")
        resp = client.get("/api/v1/meeting/brief?industry=roofing&office_id=test-office")
        assert resp.status_code == 200
        data = resp.json()
        assert "Custom roofing note" in data["office_learnings"]
        # Canonical data still present
        assert len(data["top_exposures"]) >= 3
        assert len(data["discovery_questions"]) >= 3

    def test_brief_canonical_unchanged_with_office(self, client):
        """Office learnings do not overwrite canonical fields."""
        resp_no_office = client.get("/api/v1/meeting/brief?industry=restaurant")
        resp_with_office = client.get("/api/v1/meeting/brief?industry=restaurant&office_id=unknown")
        d1 = resp_no_office.json()
        d2 = resp_with_office.json()
        assert d1["top_exposures"] == d2["top_exposures"]
        assert d1["common_claims"] == d2["common_claims"]
        assert d1["policy_lines"] == d2["policy_lines"]


# ============================================================
# GAP DETECTOR INTEGRATION
# ============================================================


class TestGapDetectorWithLearnings:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_gaps_without_office_id(self, client):
        resp = client.get("/api/v1/risk/gaps?industry=roofing&current_policies=")
        assert resp.status_code == 200
        data = resp.json()
        assert "office_learnings" in data
        assert data["office_learnings"] == []

    def test_gaps_with_office_id(self, client):
        add_office_learning("gap-office", "roofing contractor", "Check sub certs on every job")
        resp = client.get("/api/v1/risk/gaps?industry=roofing&office_id=gap-office")
        assert resp.status_code == 200
        data = resp.json()
        assert "Check sub certs on every job" in data["office_learnings"]
        # Canonical gap detection still works
        assert data["risk_level"] == "high"
        assert len(data["missing_coverages"]) > 0

    def test_gaps_canonical_unchanged_with_office(self, client):
        """Office learnings do not change risk_level or missing_coverages."""
        resp1 = client.get("/api/v1/risk/gaps?industry=roofing&current_policies=")
        resp2 = client.get("/api/v1/risk/gaps?industry=roofing&current_policies=&office_id=unknown")
        d1 = resp1.json()
        d2 = resp2.json()
        assert d1["risk_level"] == d2["risk_level"]
        assert d1["missing_coverages"] == d2["missing_coverages"]
        assert d1["top_exposures"] == d2["top_exposures"]


# ============================================================
# REGRESSIONS
# ============================================================


class TestLearningRegressions:

    @pytest.fixture
    def client(self):
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_existing_coverage_gaps_unchanged(self, client):
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing", "state": "NC", "current_coverages": [],
        })
        assert resp.status_code == 200

    def test_industry_profiles_intact(self):
        from app.knowledge.industry_profiles import INDUSTRY_PROFILES
        assert len(INDUSTRY_PROFILES) >= 12
