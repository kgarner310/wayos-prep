"""Data mining orchestrator — fans out parallel queries to all data sources.

Flow:
  1. Geocode location → lat/lng + county FIPS
  2. Fan out parallel queries to: FEMA, USGS, USFS, NOAA, OSHA, BLS
  3. Collect results into a unified LocationIntel object
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field

from app.services.data_mining.geocoder import geocode_location, GeoResult
from app.services.data_mining.flood import get_flood_zone, FloodZoneResult
from app.services.data_mining.seismic import get_seismic_risk, SeismicResult
from app.services.data_mining.wildfire import get_wildfire_risk, WildfireResult
from app.services.data_mining.weather import get_severe_weather_summary, WeatherSummary
from app.services.data_mining.osha import get_osha_summary, OshaResult
from app.services.data_mining.economic import get_economic_summary, EconomicResult

logger = logging.getLogger("wayos.data_mining.orchestrator")


@dataclass
class LocationIntel:
    """Unified location intelligence from all public data sources."""
    geo: GeoResult | None = None
    flood: FloodZoneResult | None = None
    seismic: SeismicResult | None = None
    wildfire: WildfireResult | None = None
    weather: WeatherSummary | None = None
    osha: OshaResult | None = None
    economic: EconomicResult | None = None
    query_time_ms: int = 0
    sources_queried: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)

    def to_brief_dict(self) -> dict:
        """Convert to a dict suitable for inclusion in brief JSON."""
        result: dict = {}

        if self.geo:
            result["geocoded_address"] = self.geo.matched_address
            result["county"] = f"{self.geo.county_name} County, {self.geo.state_code}"

        hazards = []

        if self.flood:
            result["flood_zone"] = self.flood.zone
            result["flood_risk"] = self.flood.risk_level
            result["flood_description"] = self.flood.description
            if self.flood.is_sfha:
                hazards.append(f"FEMA flood zone {self.flood.zone} — {self.flood.description}")

        if self.seismic:
            result["seismic_risk"] = self.seismic.risk_level
            result["seismic_description"] = self.seismic.description
            if self.seismic.risk_level not in ("low",):
                hazards.append(self.seismic.description)

        if self.wildfire:
            result["wildfire_risk"] = self.wildfire.hazard_level
            result["wildfire_description"] = self.wildfire.description
            if self.wildfire.hazard_level in ("high", "very high"):
                hazards.append(self.wildfire.description)

        if self.weather:
            result["tornado_risk"] = self.weather.tornado_risk
            result["hail_risk"] = self.weather.hail_risk
            result["hurricane_risk"] = self.weather.hurricane_risk
            result["flood_climate_risk"] = self.weather.flood_risk
            if self.weather.notable_events:
                hazards.extend(self.weather.notable_events)

        if hazards:
            result["location_hazards"] = hazards

        if self.osha:
            result["osha_top_citations"] = self.osha.top_standards_cited
            if self.osha.total_inspections > 0:
                result["osha_inspection_summary"] = (
                    f"{self.osha.total_inspections} inspections, "
                    f"{self.osha.total_violations} violations "
                    f"({self.osha.serious_violations} serious)"
                )

        if self.economic:
            result["county_establishments"] = self.economic.total_establishments
            result["county_employment"] = self.economic.total_employment
            result["county_avg_weekly_wage"] = self.economic.avg_weekly_wage
            if self.economic.top_industries:
                result["county_top_industries"] = self.economic.top_industries

        result["data_sources"] = self.sources_queried
        result["query_time_ms"] = self.query_time_ms

        return result


async def gather_location_intel(
    location: str, industry_name: str = ""
) -> LocationIntel | None:
    """Geocode a location and fan out parallel queries to all data sources.

    Returns None if geocoding fails (can't determine coordinates).
    Individual data source failures are captured but don't fail the whole operation.
    """
    start = time.time()
    intel = LocationIntel()

    # Step 1: Geocode
    geo = await geocode_location(location)
    if not geo:
        logger.info("Cannot gather intel — geocoding failed for: %s", location)
        return None

    intel.geo = geo
    intel.sources_queried.append("Census Geocoder")

    # Step 2: Fan out parallel queries
    tasks = {
        "FEMA NFHL": get_flood_zone(geo.latitude, geo.longitude),
        "USGS Seismic": get_seismic_risk(geo.latitude, geo.longitude),
        "USFS Wildfire": get_wildfire_risk(geo.latitude, geo.longitude),
        "NOAA Weather": get_severe_weather_summary(
            geo.latitude, geo.longitude, geo.state_code, geo.county_name
        ),
        "BLS QCEW": get_economic_summary(
            geo.county_fips, geo.county_name, geo.state_code
        ),
    }

    if industry_name:
        tasks["OSHA"] = get_osha_summary(geo.state_code, industry_name)

    # Run all in parallel
    results = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True,
    )

    source_names = list(tasks.keys())
    for name, result in zip(source_names, results):
        if isinstance(result, Exception):
            logger.warning("Data source %s failed: %s", name, result)
            intel.sources_failed.append(name)
            continue

        intel.sources_queried.append(name)

        if name == "FEMA NFHL":
            intel.flood = result
        elif name == "USGS Seismic":
            intel.seismic = result
        elif name == "USFS Wildfire":
            intel.wildfire = result
        elif name == "NOAA Weather":
            intel.weather = result
        elif name == "BLS QCEW":
            intel.economic = result
        elif name == "OSHA":
            intel.osha = result

    intel.query_time_ms = int((time.time() - start) * 1000)
    logger.info(
        "Location intel gathered in %dms: %d sources ok, %d failed",
        intel.query_time_ms,
        len(intel.sources_queried),
        len(intel.sources_failed),
    )

    return intel
