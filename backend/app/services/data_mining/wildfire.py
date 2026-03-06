"""USDA Forest Service wildfire risk lookup.

Queries the Wildfire Risk to Communities ImageServer for burn probability
and wildfire hazard potential at a lat/lng.
Free, no API key required.
"""
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("wayos.data_mining.wildfire")

# Wildfire Hazard Potential (WHP) — classified raster
WHP_URL = "https://apps.fs.usda.gov/fsgisx01/rest/services/RDW_Wildfire/RMRS_WRC_WildfireHazardPotential/ImageServer/identify"

# Risk to Potential Structures — quantitative risk index
RISK_URL = "https://apps.fs.usda.gov/fsgisx01/rest/services/RDW_Wildfire/RMRS_WRC_ConditionalRiskToPotentialStructures/ImageServer/identify"

TIMEOUT = 10.0


@dataclass
class WildfireResult:
    hazard_level: str        # very low, low, moderate, high, very high
    risk_score: float | None # quantitative risk index (if available)
    description: str

    @property
    def risk_level(self) -> str:
        return self.hazard_level


_WHP_CLASSES = {
    1: "very low",
    2: "low",
    3: "moderate",
    4: "high",
    5: "very high",
}


async def _query_imageserver(url: str, lat: float, lng: float) -> dict | None:
    """Query a USFS ArcGIS ImageServer identify endpoint."""
    geometry = f'{{"x":{lng},"y":{lat},"spatialReference":{{"wkid":4326}}}}'
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                url,
                params={
                    "geometry": geometry,
                    "geometryType": "esriGeometryPoint",
                    "returnGeometry": "false",
                    "returnCatalogItems": "false",
                    "f": "json",
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.exception("USFS ImageServer query failed: %s", url)
        return None


async def get_wildfire_risk(lat: float, lng: float) -> WildfireResult | None:
    """Query USFS for wildfire hazard potential at the given coordinates."""
    try:
        whp_data = await _query_imageserver(WHP_URL, lat, lng)

        hazard_level = "unknown"
        if whp_data:
            pixel_value = whp_data.get("value")
            if pixel_value is not None and pixel_value != "NoData":
                try:
                    whp_class = int(float(pixel_value))
                    hazard_level = _WHP_CLASSES.get(whp_class, "unknown")
                except (ValueError, TypeError):
                    pass

        # Try to get quantitative risk score
        risk_score = None
        risk_data = await _query_imageserver(RISK_URL, lat, lng)
        if risk_data:
            pixel_value = risk_data.get("value")
            if pixel_value is not None and pixel_value != "NoData":
                try:
                    risk_score = float(pixel_value)
                except (ValueError, TypeError):
                    pass

        descriptions = {
            "very low": "Very low wildfire hazard — minimal fire risk considerations",
            "low": "Low wildfire hazard — standard fire prevention measures sufficient",
            "moderate": "Moderate wildfire hazard — review defensible space and fire-resistant construction",
            "high": "High wildfire hazard — WUI zone exposure, fire-resistant construction and defensible space critical",
            "very high": "Very high wildfire hazard — severe WUI exposure, may impact insurability and pricing",
            "unknown": "Wildfire hazard data not available for this location",
        }

        return WildfireResult(
            hazard_level=hazard_level,
            risk_score=risk_score,
            description=descriptions.get(hazard_level, descriptions["unknown"]),
        )

    except Exception:
        logger.exception("Wildfire risk lookup failed for %.4f, %.4f", lat, lng)
        return None
