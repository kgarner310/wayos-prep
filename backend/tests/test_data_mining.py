"""Tests for data mining services — unit tests that don't hit external APIs."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.data_mining.flood import FloodZoneResult, _ZONE_DESCRIPTIONS
from app.services.data_mining.seismic import SeismicResult, _classify_risk
from app.services.data_mining.wildfire import WildfireResult
from app.services.data_mining.weather import (
    get_severe_weather_summary,
    _classify_tornado_risk,
    _classify_hail_risk,
    _classify_hurricane_risk,
    _classify_flood_risk,
)
from app.services.data_mining.osha import get_osha_summary, _TOP_CITATIONS
from app.services.data_mining.orchestrator import LocationIntel
from app.services.data_mining.geocoder import GeoResult
from app.services.brief_renderer import build_brief_json, render_brief_text


class TestFloodZone:
    def test_sfha_zone_ae(self):
        result = FloodZoneResult(zone="AE", is_sfha=True, zone_subtype="", description="High risk")
        assert result.risk_level == "high"

    def test_zone_x_minimal(self):
        result = FloodZoneResult(zone="X", is_sfha=False, zone_subtype="", description="Minimal")
        assert result.risk_level == "minimal"

    def test_zone_ve_coastal(self):
        result = FloodZoneResult(zone="VE", is_sfha=True, zone_subtype="", description="Coastal")
        assert result.risk_level == "very high (coastal)"

    def test_zone_500yr(self):
        result = FloodZoneResult(zone="X", is_sfha=False, zone_subtype="0.2 PCT ANNUAL CHANCE", description="")
        assert result.risk_level == "moderate"


class TestSeismic:
    def test_low_risk(self):
        level, desc = _classify_risk(0.1, "A")
        assert level == "low"

    def test_moderate_risk(self):
        level, desc = _classify_risk(0.4, "C")
        assert level == "moderate"
        assert "0.400" in desc

    def test_high_risk(self):
        level, desc = _classify_risk(0.8, "D")
        assert level == "high"

    def test_very_high_risk(self):
        level, desc = _classify_risk(1.5, "E")
        assert level == "very high"

    def test_none_sds(self):
        level, desc = _classify_risk(None, "A")
        assert level == "low"


class TestWeather:
    def test_tornado_alley_very_high(self):
        assert _classify_tornado_risk("OK", 35.0) == "very high"

    def test_tornado_moderate(self):
        assert _classify_tornado_risk("GA", 33.0) == "moderate"

    def test_tornado_low(self):
        assert _classify_tornado_risk("CA", 37.0) == "low"

    def test_hail_very_high(self):
        assert _classify_hail_risk("TX") == "very high"

    def test_hail_low(self):
        assert _classify_hail_risk("ME") == "low"

    def test_hurricane_very_high(self):
        assert _classify_hurricane_risk("FL", 25.0, -80.0) == "very high"

    def test_hurricane_low(self):
        assert _classify_hurricane_risk("CO", 39.0, -105.0) == "low"

    def test_flood_very_high(self):
        assert _classify_flood_risk("LA") == "very high"

    def test_flood_low(self):
        assert _classify_flood_risk("AZ") == "low"

    @pytest.mark.asyncio
    async def test_weather_summary_returns_result(self):
        result = await get_severe_weather_summary(35.5, -83.5, "NC", "Buncombe")
        assert result is not None
        assert result.tornado_risk in ("low", "moderate", "high", "very high")
        assert result.description is not None


class TestOsha:
    def test_top_citations_exist_for_key_industries(self):
        assert "roofing" in _TOP_CITATIONS
        assert "construction" in _TOP_CITATIONS
        assert "manufacturing" in _TOP_CITATIONS
        assert len(_TOP_CITATIONS["roofing"]) >= 3

    @pytest.mark.asyncio
    async def test_osha_summary_returns_cached_data(self):
        """OSHA should return cached citation data even if API is unreachable."""
        result = await get_osha_summary("NC", "Roofing")
        assert result is not None
        assert len(result.top_standards_cited) > 0
        assert "Fall Protection" in result.top_standards_cited[0]


class TestLocationIntel:
    def test_to_brief_dict_empty(self):
        intel = LocationIntel()
        result = intel.to_brief_dict()
        assert "data_sources" in result
        assert result["query_time_ms"] == 0

    def test_to_brief_dict_with_flood(self):
        intel = LocationIntel(
            geo=GeoResult(
                latitude=35.5, longitude=-82.5,
                county_fips="37021", state_fips="37",
                county_name="Buncombe", state_code="NC",
                matched_address="Asheville, NC",
            ),
            flood=FloodZoneResult(zone="X", is_sfha=False, zone_subtype="", description="Minimal"),
            sources_queried=["Census Geocoder", "FEMA NFHL"],
        )
        result = intel.to_brief_dict()
        assert result["flood_zone"] == "X"
        assert result["flood_risk"] == "minimal"
        assert result["geocoded_address"] == "Asheville, NC"

    def test_to_brief_dict_hazards(self):
        intel = LocationIntel(
            geo=GeoResult(
                latitude=35.5, longitude=-82.5,
                county_fips="37021", state_fips="37",
                county_name="Buncombe", state_code="NC",
                matched_address="Asheville, NC",
            ),
            flood=FloodZoneResult(zone="AE", is_sfha=True, zone_subtype="", description="High risk flood zone"),
            wildfire=WildfireResult(hazard_level="high", risk_score=0.05, description="High wildfire hazard"),
            sources_queried=["Census Geocoder", "FEMA NFHL", "USFS Wildfire"],
        )
        result = intel.to_brief_dict()
        assert "location_hazards" in result
        assert len(result["location_hazards"]) >= 1


class TestBriefWithLocationIntel:
    def test_brief_json_includes_location_intel(self):
        intel_dict = {
            "flood_zone": "X",
            "flood_risk": "minimal",
            "seismic_risk": "low",
            "wildfire_risk": "moderate",
            "tornado_risk": "moderate",
            "hail_risk": "low",
            "hurricane_risk": "high",
            "osha_top_citations": ["1926.501 — Fall Protection"],
            "data_sources": ["Census Geocoder", "FEMA NFHL"],
            "query_time_ms": 1500,
        }

        result = build_brief_json(
            industry_name="Roofing",
            location="Asheville, NC",
            employee_count=50,
            mod=None,
            vehicle_exposure=None,
            top_claims=["Falls"],
            regional_notes="Notes.",
            coverage_exposures=["GL"],
            conversation_starters=["Q1"],
            location_intel=intel_dict,
        )
        assert "location_intel" in result
        assert result["location_intel"]["flood_zone"] == "X"

    def test_rendered_brief_includes_location_intel(self):
        intel_dict = {
            "geocoded_address": "Asheville, NC 28801",
            "flood_zone": "AE",
            "flood_risk": "high",
            "seismic_risk": "low",
            "wildfire_risk": "high",
            "tornado_risk": "moderate",
            "hail_risk": "moderate",
            "hurricane_risk": "high",
            "location_hazards": ["High wildfire hazard — WUI zone"],
            "osha_top_citations": ["1926.501 — Fall Protection"],
            "county_employment": 150000,
            "county_establishments": 12000,
            "county_avg_weekly_wage": 950,
            "data_sources": ["Census Geocoder", "FEMA NFHL", "USGS Seismic"],
            "query_time_ms": 2000,
        }

        brief_json = build_brief_json(
            industry_name="Roofing",
            location="Asheville, NC",
            employee_count=50,
            mod=None,
            vehicle_exposure=None,
            top_claims=["Falls"],
            regional_notes="Notes.",
            coverage_exposures=["GL"],
            conversation_starters=["Q1"],
            location_intel=intel_dict,
        )
        text = render_brief_text(brief_json)
        assert "LOCATION INTELLIGENCE" in text
        assert "Flood Zone: AE" in text
        assert "Wildfire: high" in text
        assert "OSHA" in text
        assert "Fall Protection" in text

    def test_rendered_brief_without_intel(self):
        brief_json = build_brief_json(
            industry_name="Roofing",
            location="Somewhere",
            employee_count=None,
            mod=None,
            vehicle_exposure=None,
            top_claims=["Falls"],
            regional_notes="Notes.",
            coverage_exposures=["GL"],
            conversation_starters=["Q1"],
        )
        text = render_brief_text(brief_json)
        assert "LOCATION INTELLIGENCE" not in text
