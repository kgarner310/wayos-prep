"""OSHA inspection/citation data lookup.

Queries the DOL enforcement data API for OSHA inspection summaries
by state and industry (SIC/NAICS).
Free, requires no API key for the bulk data approach.
"""
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("wayos.data_mining.osha")

# DOL OSHA enforcement data API
OSHA_API_URL = "https://enforcedata.dol.gov/api/enforcement/osha_inspection"

TIMEOUT = 15.0


@dataclass
class OshaResult:
    total_inspections: int
    total_violations: int
    serious_violations: int
    top_standards_cited: list[str] = field(default_factory=list)
    description: str = ""


# Common NAICS-to-SIC mapping for our top industries
_INDUSTRY_SIC_MAP: dict[str, str] = {
    "roofing": "1761",
    "landscaping": "0782",
    "restaurant": "5812",
    "trucking": "4213",
    "manufacturing": "3999",
    "construction": "1522",
    "plumbing": "1711",
    "electrical": "1731",
    "hvac": "1711",
    "painting": "1721",
    "concrete": "1771",
    "warehousing": "4226",
}

# Top OSHA citations by industry (pre-computed from OSHA data)
# This provides instant results while the API call may timeout
_TOP_CITATIONS: dict[str, list[str]] = {
    "roofing": [
        "1926.501 — Fall Protection (consistently #1 most-cited in construction)",
        "1926.503 — Fall Protection Training",
        "1926.451 — Scaffolding requirements",
        "1926.20 — Safety and Health Programs",
    ],
    "construction": [
        "1926.501 — Fall Protection",
        "1926.1053 — Ladders",
        "1926.451 — Scaffolding",
        "1926.651 — Excavations — specific requirements",
        "1910.1200 — Hazard Communication",
    ],
    "manufacturing": [
        "1910.212 — Machine Guarding",
        "1910.147 — Lockout/Tagout",
        "1910.1200 — Hazard Communication",
        "1910.305 — Electrical (wiring methods)",
        "1910.178 — Powered Industrial Trucks (forklifts)",
    ],
    "warehousing": [
        "1910.178 — Powered Industrial Trucks (forklifts)",
        "1910.1200 — Hazard Communication",
        "1910.303 — Electrical (general requirements)",
        "1910.22 — Walking-Working Surfaces",
    ],
    "trucking": [
        "DOT/FMCSA hours-of-service violations (primary regulator, not OSHA)",
        "1910.1200 — Hazard Communication (for hazmat haulers)",
        "1910.178 — Powered Industrial Trucks (loading dock operations)",
    ],
    "restaurant": [
        "1910.1200 — Hazard Communication (cleaning chemicals)",
        "1910.303 — Electrical (general requirements)",
        "1910.22 — Walking-Working Surfaces",
        "1910.37 — Means of Egress (exit routes)",
    ],
}


async def get_osha_summary(
    state_code: str, industry_name: str
) -> OshaResult | None:
    """Get OSHA inspection summary for an industry in a state.

    Uses pre-computed top citation data for instant results, supplemented
    by live API queries when available.
    """
    try:
        # Determine industry key for lookup
        industry_lower = industry_name.lower()
        industry_key = None
        for key in _TOP_CITATIONS:
            if key in industry_lower:
                industry_key = key
                break

        top_standards = []
        if industry_key:
            top_standards = _TOP_CITATIONS[industry_key]
        else:
            # Generic top citations
            top_standards = [
                "1910.1200 — Hazard Communication",
                "1910.134 — Respiratory Protection",
                "1926.501 — Fall Protection",
                "1910.147 — Lockout/Tagout",
            ]

        # Try live API for state-specific inspection counts
        total_inspections = 0
        total_violations = 0
        serious_violations = 0

        sic = _INDUSTRY_SIC_MAP.get(industry_key or "", "")
        if sic:
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    resp = await client.get(
                        OSHA_API_URL,
                        params={
                            "p_sic": sic,
                            "p_state": state_code,
                            "p_start_date": "01/01/2022",
                            "p_end_date": "12/31/2025",
                        },
                    )
                    if resp.status_code == 200:
                        records = resp.json()
                        if isinstance(records, list):
                            total_inspections = len(records)
                            for rec in records:
                                total_violations += int(rec.get("total_violations", 0) or 0)
                                serious_violations += int(rec.get("serious_violations", 0) or 0)
            except Exception:
                logger.debug("OSHA live API unavailable, using cached citation data")

        desc_parts = [f"OSHA profile for {industry_name} in {state_code}"]
        if total_inspections > 0:
            desc_parts.append(
                f"{total_inspections} inspections (2022-2025), "
                f"{total_violations} violations ({serious_violations} serious)"
            )
        desc_parts.append(f"Top cited standards: {', '.join(s.split(' — ')[0] for s in top_standards[:3])}")

        return OshaResult(
            total_inspections=total_inspections,
            total_violations=total_violations,
            serious_violations=serious_violations,
            top_standards_cited=top_standards,
            description=" | ".join(desc_parts),
        )

    except Exception:
        logger.exception("OSHA lookup failed for %s in %s", industry_name, state_code)
        return None
