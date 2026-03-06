"""Census Bureau geocoder — converts address/city/state to lat/lng + FIPS codes.

Uses the free Census Geocoding API. No API key required.
https://geocoding.geo.census.gov/geocoder/
"""
import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger("wayos.data_mining.geocoder")

GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/address"
GEOCODER_ONELINEADDRESS_URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"

TIMEOUT = 10.0


@dataclass
class GeoResult:
    latitude: float
    longitude: float
    county_fips: str       # 5-digit county FIPS (state + county)
    state_fips: str        # 2-digit state FIPS
    county_name: str
    state_code: str        # 2-letter state abbreviation
    matched_address: str

    @property
    def state_county_fips(self) -> str:
        return self.county_fips


# FIPS to state code mapping (2-digit FIPS → 2-letter state abbreviation)
_FIPS_TO_STATE = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY",
}


async def geocode_location(location: str) -> GeoResult | None:
    """Geocode a location string to coordinates and FIPS codes.

    Accepts formats like:
      - "Asheville, NC"
      - "123 Main St, Asheville, NC 28801"
      - "Franklin, North Carolina"
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                GEOCODER_ONELINEADDRESS_URL,
                params={
                    "address": location,
                    "benchmark": "Public_AR_Current",
                    "vintage": "Current_Current",
                    "format": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        matches = data.get("result", {}).get("addressMatches", [])
        if not matches:
            logger.info("No geocode match for: %s", location)
            return None

        match = matches[0]
        coords = match.get("coordinates", {})
        geographies = match.get("geographies", {})

        # Extract county info from Census geographies
        counties = geographies.get("Counties", [])
        if not counties:
            logger.warning("Geocode matched but no county geography for: %s", location)
            return None

        county = counties[0]
        state_fips = county.get("STATE", "")
        county_fips_part = county.get("COUNTY", "")
        county_name = county.get("NAME", "")
        full_fips = f"{state_fips}{county_fips_part}"

        state_code = _FIPS_TO_STATE.get(state_fips, "")

        return GeoResult(
            latitude=float(coords.get("y", 0)),
            longitude=float(coords.get("x", 0)),
            county_fips=full_fips,
            state_fips=state_fips,
            county_name=county_name,
            state_code=state_code,
            matched_address=match.get("matchedAddress", location),
        )

    except Exception:
        logger.exception("Geocoding failed for: %s", location)
        return None
