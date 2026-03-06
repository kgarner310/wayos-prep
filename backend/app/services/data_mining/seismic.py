"""USGS seismic risk lookup via design maps API.

Queries ASCE 7-22 seismic design parameters at a lat/lng.
Free, no API key required.
"""
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("wayos.data_mining.seismic")

USGS_DESIGN_URL = "https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"
TIMEOUT = 10.0


@dataclass
class SeismicResult:
    sds: float | None       # Short-period design spectral acceleration
    sd1: float | None       # 1-second design spectral acceleration
    pga: float | None       # Peak ground acceleration
    design_category: str     # Seismic Design Category (A-F)
    risk_level: str          # human-readable: low, moderate, high, very high
    description: str


def _classify_risk(sds: float | None, design_cat: str) -> tuple[str, str]:
    """Classify seismic risk from design parameters."""
    if not sds or sds < 0.167:
        return "low", "Low seismic risk — minimal earthquake considerations for underwriting"
    if sds < 0.33:
        return "low-moderate", f"Low-moderate seismic risk (SDS={sds:.3f}) — standard construction practices sufficient"
    if sds < 0.50:
        return "moderate", f"Moderate seismic risk (SDS={sds:.3f}, Category {design_cat}) — seismic building code compliance important"
    if sds < 1.0:
        return "high", f"High seismic risk (SDS={sds:.3f}, Category {design_cat}) — earthquake coverage critical, retrofit status matters"
    return "very high", f"Very high seismic risk (SDS={sds:.3f}, Category {design_cat}) — major earthquake exposure, verify structural engineering"


async def get_seismic_risk(lat: float, lng: float) -> SeismicResult | None:
    """Query USGS for seismic design parameters at the given coordinates."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                USGS_DESIGN_URL,
                params={
                    "latitude": lat,
                    "longitude": lng,
                    "riskCategory": "II",
                    "siteClass": "D",
                    "title": "wayos-query",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        response_data = data.get("response", {}).get("data", {})
        sds = response_data.get("sds")
        sd1 = response_data.get("sd1")
        pga = response_data.get("pga")

        # Extract seismic design category
        design_cat = response_data.get("sdc", "")
        if not design_cat:
            sdcs = response_data.get("sdcs", "")
            sdc1 = response_data.get("sdc1", "")
            design_cat = max(sdcs, sdc1) if sdcs and sdc1 else sdcs or sdc1 or "Unknown"

        risk_level, description = _classify_risk(sds, design_cat)

        return SeismicResult(
            sds=sds,
            sd1=sd1,
            pga=pga,
            design_category=str(design_cat),
            risk_level=risk_level,
            description=description,
        )

    except Exception:
        logger.exception("USGS seismic lookup failed for %.4f, %.4f", lat, lng)
        return None
