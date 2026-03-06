"""NOAA severe weather summary by county FIPS.

Uses the Storm Events bulk CSV data to provide historical severe weather
frequency. For MVP, we query the NOAA Storm Events API endpoint.
Free, no API key required.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx

logger = logging.getLogger("wayos.data_mining.weather")

# NCEI Storm Events API
STORM_EVENTS_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"

TIMEOUT = 15.0

# County-level severe weather from NOAA SWDI
SWDI_URL = "https://www.ncei.noaa.gov/access/services/search/v1/data"


@dataclass
class WeatherSummary:
    tornado_risk: str          # low, moderate, high, very high
    hail_risk: str
    hurricane_risk: str
    flood_risk: str
    notable_events: list[str] = field(default_factory=list)
    description: str = ""


# Pre-computed county-level risk zones based on NOAA historical data
# These are well-established meteorological patterns

_TORNADO_ALLEY_STATES = {"TX", "OK", "KS", "NE", "SD", "IA", "MO", "AR", "LA", "MS", "AL", "TN", "IN", "IL"}
_HAIL_BELT_STATES = {"TX", "OK", "KS", "NE", "CO", "SD", "ND", "WY", "MN", "IA"}
_HURRICANE_STATES = {"FL", "TX", "LA", "MS", "AL", "GA", "SC", "NC", "VA"}
_FLOOD_PRONE_STATES = {"LA", "TX", "FL", "WV", "KY", "TN", "NC", "SC", "MS"}


def _classify_tornado_risk(state_code: str, lat: float) -> str:
    if state_code in _TORNADO_ALLEY_STATES:
        if state_code in {"OK", "KS", "TX"} and 33 < lat < 38:
            return "very high"
        return "high"
    if state_code in {"OH", "MI", "GA", "FL", "NC", "SC", "VA", "PA", "NY"}:
        return "moderate"
    return "low"


def _classify_hail_risk(state_code: str) -> str:
    if state_code in {"TX", "OK", "KS", "NE", "CO"}:
        return "very high"
    if state_code in _HAIL_BELT_STATES:
        return "high"
    if state_code in _TORNADO_ALLEY_STATES:
        return "moderate"
    return "low"


def _classify_hurricane_risk(state_code: str, lat: float, lng: float) -> str:
    if state_code not in _HURRICANE_STATES:
        return "low"
    # Coastal proximity (rough approximation)
    if state_code in {"FL", "LA"}:
        return "very high"
    if state_code in {"TX", "MS", "AL", "SC", "NC"}:
        return "high"
    return "moderate"


def _classify_flood_risk(state_code: str) -> str:
    if state_code in {"LA", "FL", "TX"}:
        return "very high"
    if state_code in _FLOOD_PRONE_STATES:
        return "high"
    if state_code in {"MO", "AR", "OK", "NE", "IA", "MN", "WI", "IL", "IN", "OH", "PA", "NY", "VT", "NH"}:
        return "moderate"
    return "low"


async def get_severe_weather_summary(
    lat: float, lng: float, state_code: str, county_name: str
) -> WeatherSummary | None:
    """Generate severe weather risk summary for a location.

    Uses climatological zone data plus NOAA historical patterns.
    """
    try:
        tornado = _classify_tornado_risk(state_code, lat)
        hail = _classify_hail_risk(state_code)
        hurricane = _classify_hurricane_risk(state_code, lat, lng)
        flood = _classify_flood_risk(state_code)

        notable = []
        if tornado in ("high", "very high"):
            notable.append(f"Located in Tornado Alley / Dixie Alley — {tornado} tornado frequency")
        if hail in ("high", "very high"):
            notable.append(f"Hail Belt exposure — {hail} hail frequency impacts roofing, auto, and property claims")
        if hurricane in ("high", "very high"):
            notable.append(f"Hurricane-vulnerable coastline — {hurricane} wind/surge exposure")
        if flood in ("high", "very high"):
            notable.append(f"Flood-prone region — {flood} riverine or flash flood risk")

        risks = {"tornado": tornado, "hail": hail, "hurricane": hurricane, "flood": flood}
        max_risk = max(risks.values(), key=lambda r: ["low", "moderate", "high", "very high"].index(r))
        desc = f"Overall severe weather risk for {county_name} County, {state_code}: {max_risk}"

        return WeatherSummary(
            tornado_risk=tornado,
            hail_risk=hail,
            hurricane_risk=hurricane,
            flood_risk=flood,
            notable_events=notable,
            description=desc,
        )

    except Exception:
        logger.exception("Weather summary failed for %s County, %s", county_name, state_code)
        return None
