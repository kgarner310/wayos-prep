"""Tests for the ported industry profiles data and loader service."""

from app.data.industry_profiles import (
    INDUSTRY_PROFILES,
    resolve_industry,
    get_profile,
)
from app.services.industry_loader import (
    resolve,
    get_enrichment,
    get_conversation_prompts,
    get_wc_claims,
    get_gl_exposures,
    get_auto_claims,
    get_regional_notes,
    list_all_industries,
    CORE_INDUSTRIES,
)
from app.services.coverage_gap_detector import detect_coverage_gaps
from app.services.producer_ammo import generate_producer_ammo


# ============================================================
# INDUSTRY PROFILES DATA MODULE
# ============================================================

class TestIndustryProfiles:
    def test_80_profiles_loaded(self):
        assert len(INDUSTRY_PROFILES) == 80

    def test_all_profiles_have_required_fields(self):
        required = {"display_name", "tier", "synonyms", "wc_claims",
                     "auto_claims", "gl_exposures", "conversation_prompts",
                     "regional_notes"}
        for slug, profile in INDUSTRY_PROFILES.items():
            missing = required - set(profile.keys())
            assert not missing, f"{slug} missing fields: {missing}"

    def test_all_tiers_represented(self):
        tiers = {p["tier"] for p in INDUSTRY_PROFILES.values()}
        assert tiers == {1, 2, 3}

    def test_tier_counts(self):
        counts = {}
        for p in INDUSTRY_PROFILES.values():
            counts[p["tier"]] = counts.get(p["tier"], 0) + 1
        assert counts[1] == 25
        assert counts[2] == 30
        assert counts[3] == 25

    def test_all_have_synonyms(self):
        for slug, profile in INDUSTRY_PROFILES.items():
            assert isinstance(profile["synonyms"], list), f"{slug} synonyms is not a list"
            assert len(profile["synonyms"]) >= 1, f"{slug} has no synonyms"

    def test_all_have_conversation_prompts(self):
        for slug, profile in INDUSTRY_PROFILES.items():
            assert len(profile["conversation_prompts"]) >= 1, f"{slug} has no prompts"

    def test_all_have_wc_claims(self):
        for slug, profile in INDUSTRY_PROFILES.items():
            assert len(profile["wc_claims"]) >= 1, f"{slug} has no WC claims"

    def test_all_have_gl_exposures(self):
        for slug, profile in INDUSTRY_PROFILES.items():
            assert len(profile["gl_exposures"]) >= 1, f"{slug} has no GL exposures"

    def test_resolve_by_slug(self):
        assert resolve_industry("poultry_farming_processing") == "poultry_farming_processing"

    def test_resolve_by_display_name(self):
        assert resolve_industry("Poultry Farming / Processing") == "poultry_farming_processing"

    def test_resolve_by_synonym(self):
        assert resolve_industry("Chicken Farm") == "poultry_farming_processing"

    def test_resolve_case_insensitive(self):
        assert resolve_industry("chicken farm") == "poultry_farming_processing"

    def test_resolve_unknown_returns_none(self):
        assert resolve_industry("space tourism") is None

    def test_get_profile_returns_dict(self):
        profile = get_profile("cattle_ranching")
        assert profile is not None
        assert profile["display_name"] == "Cattle Ranching"

    def test_get_profile_unknown_returns_none(self):
        assert get_profile("nonexistent") is None


# ============================================================
# INDUSTRY LOADER SERVICE
# ============================================================

class TestIndustryLoader:
    def test_resolve_core_industry(self):
        slug, source = resolve("roofing")
        assert slug == "roofing"
        assert source == "core"

    def test_resolve_core_alias(self):
        slug, source = resolve("roofer")
        assert slug == "roofing"
        assert source == "core"

    def test_resolve_tier_industry(self):
        slug, source = resolve("Chicken Farm")
        assert slug == "poultry_farming_processing"
        assert source == "tier"

    def test_resolve_tier_display_name(self):
        slug, source = resolve("Environmental Consulting")
        assert source == "tier"

    def test_resolve_unknown(self):
        slug, source = resolve("space tourism")
        assert source == "unknown"
        assert slug == "space tourism"

    def test_enrichment_for_tier_industry(self):
        enrichment = get_enrichment("Cattle Ranching")
        assert enrichment
        assert "wc_claims" in enrichment
        assert "gl_exposures" in enrichment
        assert "conversation_prompts" in enrichment

    def test_enrichment_for_unknown_returns_empty(self):
        enrichment = get_enrichment("space tourism")
        assert enrichment == {}

    def test_conversation_prompts(self):
        prompts = get_conversation_prompts("Waste Management / Hauling")
        assert len(prompts) >= 1
        assert all(isinstance(p, str) for p in prompts)

    def test_wc_claims(self):
        claims = get_wc_claims("Mining Operations (Surface)")
        assert len(claims) >= 1

    def test_gl_exposures(self):
        exposures = get_gl_exposures("Hotels and Resorts")
        assert len(exposures) >= 1

    def test_auto_claims(self):
        claims = get_auto_claims("Oil and Gas Extraction")
        assert len(claims) >= 1

    def test_regional_notes(self):
        notes = get_regional_notes("Solar Farm Installation")
        assert isinstance(notes, str)
        assert len(notes) > 0

    def test_list_all_industries_includes_core(self):
        all_ind = list_all_industries()
        slugs = {i["slug"] for i in all_ind}
        for core in CORE_INDUSTRIES:
            assert core in slugs

    def test_list_all_industries_includes_tier(self):
        all_ind = list_all_industries()
        slugs = {i["slug"] for i in all_ind}
        assert "poultry_farming_processing" in slugs

    def test_list_all_industries_count(self):
        all_ind = list_all_industries()
        # 6 core + 80 tier = 86
        assert len(all_ind) == 86


# ============================================================
# COVERAGE GAP DETECTOR INTEGRATION
# ============================================================

class TestCoverageGapTierIntegration:
    def test_tier_industry_returns_gaps(self):
        """A tier industry should still return coverage gaps."""
        result = detect_coverage_gaps({
            "industry": "Waste Management / Hauling",
            "state": "TX",
            "employees": 50,
            "current_coverages": [],
        })
        assert "coverage_gaps" in result
        assert "suggested_questions" in result

    def test_tier_industry_gets_enrichment(self):
        """A tier industry should get tier_enrichment in response."""
        result = detect_coverage_gaps({
            "industry": "Cattle Ranching",
            "state": "TX",
            "current_coverages": [],
        })
        assert "tier_enrichment" in result
        enrichment = result["tier_enrichment"]
        assert enrichment["display_name"] == "Cattle Ranching"
        assert len(enrichment["wc_claims"]) >= 1

    def test_tier_industry_has_more_questions(self):
        """A tier industry should get conversation prompts as suggested questions."""
        result = detect_coverage_gaps({
            "industry": "Hotels and Resorts",
            "state": "FL",
            "current_coverages": [],
        })
        # Should have both standard questions and tier prompts
        assert len(result["suggested_questions"]) >= 1

    def test_core_industry_still_works(self):
        """Core industries should still work exactly as before."""
        result = detect_coverage_gaps({
            "industry": "roofing",
            "state": "NC",
            "current_coverages": [],
        })
        assert len(result["coverage_gaps"]) > 0
        assert result["industry"] == "roofing"

    def test_unknown_industry_no_enrichment(self):
        """Unknown industry should have no tier_enrichment."""
        result = detect_coverage_gaps({
            "industry": "space tourism",
            "state": "TX",
            "current_coverages": [],
        })
        assert "tier_enrichment" not in result or result.get("tier_enrichment", {}).get("display_name", "") == ""


# ============================================================
# PRODUCER AMMO INTEGRATION
# ============================================================

class TestProducerAmmoTierIntegration:
    def test_tier_industry_uses_tier_prompts(self):
        """A tier industry should use tier conversation prompts as top questions."""
        result = generate_producer_ammo({
            "industry": "Cattle Ranching",
            "state": "TX",
            "account_stage": "prospect",
        })
        ammo = result["ammo_questions"]
        assert len(ammo["top_questions"]) >= 1
        # Should not be generic fallback (generic starts with "Walk me through...")
        assert ammo["top_questions"][0] != "Walk me through your operations — what does a typical week look like?"

    def test_tier_industry_gl_as_coverage_traps(self):
        """A tier industry should derive coverage traps from GL exposures."""
        result = generate_producer_ammo({
            "industry": "Hotels and Resorts",
            "state": "FL",
            "account_stage": "renewal",
        })
        traps = result["ammo_questions"]["coverage_traps"]
        assert len(traps) >= 1
        # Should be GL-derived (starts with "GL exposure:")
        assert any("GL exposure:" in t for t in traps)

    def test_tier_industry_gets_enrichment(self):
        """A tier industry should get tier_enrichment in response."""
        result = generate_producer_ammo({
            "industry": "Solar Farm Installation",
            "state": "CA",
        })
        assert "tier_enrichment" in result
        assert result["tier_enrichment"]["display_name"] == "Solar Farm Installation"

    def test_core_industry_no_tier_top_questions(self):
        """Core industries should still use curated top questions."""
        result = generate_producer_ammo({
            "industry": "trucking",
            "state": "TX",
        })
        ammo = result["ammo_questions"]
        # First question should be from _INDUSTRY_TOP_QUESTIONS["trucking"]
        assert "drivers" in ammo["top_questions"][0].lower() or "driver" in ammo["top_questions"][0].lower()

    def test_synonym_resolves_to_tier_profile(self):
        """A synonym like 'Chicken Farm' should resolve to poultry profile."""
        result = generate_producer_ammo({
            "industry": "Chicken Farm",
            "state": "GA",
        })
        assert "tier_enrichment" in result
        assert "Poultry" in result["tier_enrichment"]["display_name"]
