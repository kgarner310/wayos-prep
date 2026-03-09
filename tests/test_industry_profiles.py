"""Tests for Industry Knowledge Object system."""

import pytest
from fastapi.testclient import TestClient

from app.knowledge.industry_profiles import (
    IndustryProfile,
    INDUSTRY_PROFILES,
    get_industry_profile,
    list_industries,
    add_office_learning,
)


# ============================================================
# DATACLASS
# ============================================================


class TestIndustryProfileDataclass:

    def test_create_profile(self):
        p = IndustryProfile(industry="test", naics="999999", jurisdiction="XX")
        assert p.industry == "test"
        assert p.naics == "999999"
        assert p.top_exposures == []
        assert p.confidence == 0.80

    def test_to_dict(self):
        p = IndustryProfile(
            industry="test",
            naics="123456",
            jurisdiction="CA",
            top_exposures=["fire", "flood"],
            confidence=0.75,
        )
        d = p.to_dict()
        assert isinstance(d, dict)
        assert d["industry"] == "test"
        assert d["naics"] == "123456"
        assert d["top_exposures"] == ["fire", "flood"]
        assert d["confidence"] == 0.75

    def test_to_dict_serializable(self):
        """to_dict output should be JSON-serializable."""
        import json
        p = IndustryProfile(industry="test", naics="000", jurisdiction="TX")
        json_str = json.dumps(p.to_dict())
        assert '"industry": "test"' in json_str

    def test_default_values(self):
        p = IndustryProfile(industry="x", naics="0", jurisdiction="Y")
        assert p.source_version == "2026-03"
        assert p.last_updated == "2026-03-07"
        assert p.office_learnings == []
        assert p.risk_score_factors == {}


# ============================================================
# REGISTRY
# ============================================================


class TestRegistry:

    def test_profiles_loaded(self):
        assert len(INDUSTRY_PROFILES) >= 12

    def test_all_keys_lowercase(self):
        for key in INDUSTRY_PROFILES:
            assert key == key.lower().strip()

    def test_list_industries(self):
        industries = list_industries()
        assert len(industries) >= 12
        assert industries == sorted(industries)

    def test_get_exact_match(self):
        p = get_industry_profile("roofing contractor")
        assert p is not None
        assert p.industry == "roofing contractor"

    def test_get_case_insensitive(self):
        p = get_industry_profile("ROOFING CONTRACTOR")
        assert p is not None
        assert p.industry == "roofing contractor"

    def test_get_with_suffix_fallback(self):
        p = get_industry_profile("roofing")
        assert p is not None
        assert p.industry == "roofing contractor"

    def test_get_nonexistent(self):
        p = get_industry_profile("underwater basket weaving")
        assert p is None

    def test_get_restaurant(self):
        p = get_industry_profile("restaurant")
        assert p is not None
        assert p.naics == "722511"

    def test_get_trucking(self):
        p = get_industry_profile("trucking")
        assert p is not None
        assert "commercial auto" in p.policy_lines


# ============================================================
# OFFICE LEARNINGS
# ============================================================


class TestOfficeLearnings:

    def test_add_learning(self):
        p = get_industry_profile("restaurant")
        initial_count = len(p.office_learnings)
        result = add_office_learning("restaurant", "local health dept requires quarterly inspections")
        assert result is True
        assert len(p.office_learnings) == initial_count + 1
        assert "quarterly inspections" in p.office_learnings[-1]
        # Clean up
        p.office_learnings.pop()

    def test_add_learning_nonexistent(self):
        result = add_office_learning("nonexistent_industry", "some note")
        assert result is False


# ============================================================
# PROFILE CONTENT QUALITY
# ============================================================


class TestProfileContent:

    @pytest.fixture(params=list(INDUSTRY_PROFILES.keys()))
    def profile(self, request):
        return INDUSTRY_PROFILES[request.param]

    def test_has_naics(self, profile):
        assert profile.naics
        assert len(profile.naics) >= 4

    def test_has_jurisdiction(self, profile):
        assert profile.jurisdiction
        assert len(profile.jurisdiction) == 2

    def test_has_top_exposures(self, profile):
        assert len(profile.top_exposures) >= 3

    def test_has_common_claims(self, profile):
        assert len(profile.common_claims) >= 3

    def test_has_coverage_gaps(self, profile):
        assert len(profile.coverage_gaps) >= 3

    def test_has_talking_points(self, profile):
        assert len(profile.recommended_talking_points) >= 3

    def test_has_discovery_questions(self, profile):
        assert len(profile.discovery_questions) >= 3
        for q in profile.discovery_questions:
            assert q.endswith("?"), f"Discovery question should end with '?': {q}"

    def test_has_policy_lines(self, profile):
        assert len(profile.policy_lines) >= 3

    def test_has_risk_score_factors(self, profile):
        assert len(profile.risk_score_factors) >= 3
        for factor, impact in profile.risk_score_factors.items():
            assert impact in ("high impact", "medium impact", "low impact"), \
                f"Invalid impact level '{impact}' for factor '{factor}'"

    def test_has_data_sources(self, profile):
        assert len(profile.data_sources) >= 2

    def test_confidence_range(self, profile):
        assert 0.0 < profile.confidence <= 1.0

    def test_source_version(self, profile):
        assert profile.source_version


# ============================================================
# SPECIFIC INDUSTRY PROFILES
# ============================================================


class TestSpecificProfiles:

    def test_roofing_canonical(self):
        p = get_industry_profile("roofing contractor")
        assert p.naics == "238160"
        assert "fall from height" in p.top_exposures
        assert "uninsured subcontractors" in p.coverage_gaps
        assert "workers compensation" in p.policy_lines
        assert p.confidence == 0.88

    def test_bar_tavern(self):
        p = get_industry_profile("bar/tavern")
        assert p is not None
        assert "liquor liability" in p.policy_lines
        assert any("dram" in c.lower() for c in p.common_claims)

    def test_daycare(self):
        p = get_industry_profile("daycare")
        assert p is not None
        assert any("abuse" in g.lower() or "molestation" in g.lower() for g in p.coverage_gaps)

    def test_apartment_owner(self):
        p = get_industry_profile("apartment owner")
        assert p is not None
        assert any("pool" in e.lower() or "swimming" in e.lower() for e in p.top_exposures)

    def test_auto_repair(self):
        p = get_industry_profile("auto repair shop")
        assert p is not None
        assert any("garagekeepers" in l.lower() for l in p.policy_lines)

    def test_electrical(self):
        p = get_industry_profile("electrical contractor")
        assert p is not None
        assert any("arc flash" in e.lower() or "electrocution" in e.lower() for e in p.top_exposures)

    def test_plumber(self):
        p = get_industry_profile("plumber")
        assert p is not None
        assert any("water damage" in c.lower() for c in p.common_claims)

    def test_trucking(self):
        p = get_industry_profile("trucking company")
        assert p is not None
        assert "motor truck cargo" in p.policy_lines


# ============================================================
# APP STARTUP
# ============================================================


class TestAppStartup:

    def test_health_still_works(self):
        from app.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_profiles_available_after_startup(self):
        assert len(INDUSTRY_PROFILES) >= 12


# ============================================================
# REGRESSIONS
# ============================================================


class TestIndustryProfileRegressions:

    def test_existing_coverage_gap_endpoint_unaffected(self):
        from app.main import app
        from unittest.mock import MagicMock
        from app.db.session import get_db
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        client = TestClient(app)
        resp = client.post("/api/v1/risk/coverage-gaps", json={
            "industry": "roofing",
            "state": "NC",
            "current_coverages": ["workers_comp"],
        })
        assert resp.status_code == 200
        app.dependency_overrides.clear()

    def test_demo_seed_still_works(self):
        from app.main import app
        from unittest.mock import MagicMock, patch
        from app.db.session import get_db
        db = MagicMock()
        app.dependency_overrides[get_db] = lambda: db
        client = TestClient(app)
        with patch("app.api.routes.seed_demo_accounts") as mock_seed:
            mock_seed.return_value = [{"account_id": "x", "account_name": "Test", "status": "created"}]
            resp = client.post("/api/v1/demo/seed")
            assert resp.status_code == 200
        app.dependency_overrides.clear()
