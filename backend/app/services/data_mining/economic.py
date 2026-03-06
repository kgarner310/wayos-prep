"""BLS Quarterly Census of Employment and Wages (QCEW) lookup.

Queries county-level employment and payroll data by industry.
Free, no API key required.
"""
import csv
import io
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("wayos.data_mining.economic")

# BLS QCEW open data API — returns CSV for a county FIPS code
QCEW_URL = "https://data.bls.gov/cew/data/api/{year}/{qtr}/area/{fips}.csv"

TIMEOUT = 15.0


@dataclass
class EconomicResult:
    county_name: str
    state_code: str
    total_establishments: int
    total_employment: int
    avg_weekly_wage: int
    top_industries: list[str] = field(default_factory=list)
    construction_employment: int = 0
    manufacturing_employment: int = 0
    description: str = ""


# NAICS sector codes and names
_NAICS_SECTORS = {
    "10": "All Industries",
    "1011": "Natural Resources & Mining",
    "1012": "Construction",
    "1013": "Manufacturing",
    "1021": "Trade, Transportation & Utilities",
    "1022": "Information",
    "1023": "Financial Activities",
    "1024": "Professional & Business Services",
    "1025": "Education & Health Services",
    "1026": "Leisure & Hospitality",
    "1027": "Other Services",
    "1028": "Public Administration",
    "1029": "Unclassified",
}


async def get_economic_summary(
    county_fips: str, county_name: str, state_code: str
) -> EconomicResult | None:
    """Get county-level employment and industry data from BLS QCEW."""
    try:
        # Try current year Q1, fall back to previous year
        from datetime import datetime
        current_year = datetime.now().year
        data_rows = None

        for year in [current_year - 1, current_year - 2]:
            for qtr in ["a", "1"]:  # "a" = annual, "1" = Q1
                url = QCEW_URL.format(year=year, qtr=qtr, fips=county_fips)
                try:
                    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                        resp = await client.get(url)
                        if resp.status_code == 200 and len(resp.text) > 100:
                            data_rows = list(csv.DictReader(io.StringIO(resp.text)))
                            break
                except Exception:
                    continue
            if data_rows:
                break

        if not data_rows:
            logger.info("No QCEW data available for FIPS %s", county_fips)
            return None

        total_estab = 0
        total_emp = 0
        avg_wage = 0
        construction_emp = 0
        manufacturing_emp = 0
        sector_employment: dict[str, int] = {}

        for row in data_rows:
            industry_code = row.get("industry_code", "")
            own_code = row.get("own_code", "")

            # Only look at private sector (own_code=5) and total (own_code=0)
            if own_code not in ("0", "5"):
                continue

            try:
                emp = int(row.get("annual_avg_emplvl", 0) or row.get("month1_emplvl", 0) or 0)
                estab = int(row.get("annual_avg_estabs", 0) or row.get("qtrly_estabs", 0) or 0)
                wage = int(row.get("annual_avg_wkly_wage", 0) or row.get("avg_wkly_wage", 0) or 0)
            except (ValueError, TypeError):
                continue

            # Total all industries
            if industry_code == "10" and own_code == "0":
                total_estab = estab
                total_emp = emp
                avg_wage = wage

            # Sector-level breakdown (private)
            if industry_code in _NAICS_SECTORS and own_code == "5" and emp > 0:
                sector_employment[_NAICS_SECTORS[industry_code]] = emp

            if industry_code == "1012" and own_code == "5":
                construction_emp = emp
            if industry_code == "1013" and own_code == "5":
                manufacturing_emp = emp

        # Sort sectors by employment
        top = sorted(sector_employment.items(), key=lambda x: x[1], reverse=True)
        top_industries = [
            f"{name}: {emp:,} employees"
            for name, emp in top[:5]
            if name != "All Industries"
        ]

        desc = (
            f"{county_name} County, {state_code}: "
            f"{total_estab:,} establishments, {total_emp:,} total employment, "
            f"${avg_wage:,}/week avg wage"
        )

        return EconomicResult(
            county_name=county_name,
            state_code=state_code,
            total_establishments=total_estab,
            total_employment=total_emp,
            avg_weekly_wage=avg_wage,
            top_industries=top_industries,
            construction_employment=construction_emp,
            manufacturing_employment=manufacturing_emp,
            description=desc,
        )

    except Exception:
        logger.exception("BLS QCEW lookup failed for FIPS %s", county_fips)
        return None
