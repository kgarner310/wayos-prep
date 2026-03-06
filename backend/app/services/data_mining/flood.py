"""FEMA National Flood Hazard Layer (NFHL) lookup.

Queries the FEMA ArcGIS REST service to determine flood zone at a point.
Free, no API key required.
"""
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("wayos.data_mining.flood")

NFHL_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
TIMEOUT = 10.0


@dataclass
class FloodZoneResult:
    zone: str              # e.g., "X", "AE", "VE", "A"
    is_sfha: bool          # Special Flood Hazard Area (high risk)
    zone_subtype: str      # e.g., "FLOODWAY", "0.2 PCT ANNUAL CHANCE"
    description: str       # human-readable summary

    @property
    def risk_level(self) -> str:
        if self.zone.startswith("V"):
            return "very high (coastal)"
        if self.zone in ("A", "AE", "AH", "AO", "AR"):
            return "high"
        if self.zone_subtype and "0.2" in self.zone_subtype:
            return "moderate"
        return "minimal"


_ZONE_DESCRIPTIONS = {
    "A": "100-year floodplain — high risk, flood insurance required for federally-backed mortgages",
    "AE": "100-year floodplain with base flood elevation — high risk",
    "AH": "100-year floodplain with shallow flooding (1-3 ft) — high risk",
    "AO": "100-year floodplain with sheet flow flooding — high risk",
    "AR": "Special flood hazard area formerly protected by levee — high risk",
    "VE": "Coastal high hazard area with storm wave action — very high risk",
    "V": "Coastal flood zone with velocity hazard — very high risk",
    "X": "Minimal flood risk — outside 500-year floodplain",
    "D": "Undetermined risk — no flood hazard analysis performed",
}


async def get_flood_zone(lat: float, lng: float) -> FloodZoneResult | None:
    """Query FEMA NFHL for flood zone at the given coordinates."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                NFHL_URL,
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "FLD_ZONE,SFHA_TF,ZONE_SUBTY",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        features = data.get("features", [])
        if not features:
            return FloodZoneResult(
                zone="X",
                is_sfha=False,
                zone_subtype="",
                description="No FEMA flood data available at this location — likely minimal risk",
            )

        attrs = features[0].get("attributes", {})
        zone = attrs.get("FLD_ZONE", "X")
        sfha = attrs.get("SFHA_TF", "F") == "T"
        subtype = attrs.get("ZONE_SUBTY", "") or ""

        desc = _ZONE_DESCRIPTIONS.get(zone, f"Flood zone {zone}")
        if subtype and "0.2" in subtype:
            desc = "500-year floodplain (0.2% annual chance) — moderate risk"

        return FloodZoneResult(
            zone=zone,
            is_sfha=sfha,
            zone_subtype=subtype,
            description=desc,
        )

    except Exception:
        logger.exception("FEMA flood zone lookup failed for %.4f, %.4f", lat, lng)
        return None
