"""Seed the database with state-specific risk profiles for Southeast states."""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.state_profile import StateProfile

STATE_PROFILES = [
    {
        "state_code": "NC",
        "state_name": "North Carolina",
        "wc_monopolistic": False,
        "wc_competitive": True,
        "wc_notes": (
            "NC Industrial Commission administers workers comp. Employers with 3+ employees must carry coverage. "
            "NC uses NCCI class codes with state-specific deviations. Experience rating applies at $7,500+ premium. "
            "Second Injury Fund helps offset costs for hiring previously injured workers. "
            "NC has mandatory employer reporting within 5 days of injury knowledge."
        ),
        "regulatory_notes": (
            "NC Department of Insurance regulates all P&C. Rate filings go through NC Rate Bureau (NCRB), which is "
            "separate from NCCI for WC. NC is a file-and-use state for most commercial lines. "
            "Contractor licensing required through NC Licensing Board for General Contractors (above $30K). "
            "NC Building Code Council adopts statewide codes. Coastal Area Management Act (CAMA) governs coastal "
            "development permits. NC requires certificates of insurance for most public contracts."
        ),
        "tort_environment": "moderate",
        "cat_exposures": [
            "Hurricane — Outer Banks through Wilmington corridor; Florence (2018) caused $22B+ damage",
            "Tropical storms and inland flooding — Piedmont and foothills vulnerable to remnant moisture",
            "Severe convective storms — hail and tornadoes across Piedmont and Sandhills",
            "Winter storms — ice storms in Piedmont, heavy snow in mountains (Asheville, Boone, Banner Elk)",
            "Wildfire — increasing risk in western NC mountain communities",
            "Mudslides and landslides — western NC steep terrain after heavy rain",
        ],
        "compliance_items": [
            "NC General Contractor License (NCGS 87-1) required for projects over $30,000",
            "NC Electrical, Plumbing, and Mechanical licenses through respective state boards",
            "NC OSHA (OSH Division of NC DOL) — state-plan state with own enforcement",
            "NC Pollution Prevention Act — environmental compliance for manufacturers",
            "NC Coastal Area Management Act (CAMA) permits for coastal construction",
            "NC Sediment and Erosion Control Act — land-disturbing permits required",
            "NC Fire Prevention Code — local fire marshal inspections",
            "Short-term rental registration required in many NC municipalities (Asheville, Outer Banks, etc.)",
            "NC Mine Safety and Health Act — MSHA plus NC-specific requirements",
            "NC requires 30-day notice of cancellation for commercial policies",
        ],
        "market_notes": (
            "NC is the 9th largest state by population with a diverse economy. Charlotte is a major banking/finance hub. "
            "Research Triangle (Raleigh-Durham-Chapel Hill) drives tech and biotech. Asheville and mountain region "
            "experiencing rapid growth in tourism, short-term rentals, and high-value residential. Outer Banks and "
            "coastal communities are heavily tourism-dependent with significant wind/flood exposure. "
            "Eastern NC has strong agriculture (tobacco, sweet potatoes, hog farming). "
            "Western NC has growing craft brewery, outdoor recreation, and retirement community markets. "
            "Mining (primarily aggregates, lithium, feldspar, mica) concentrated in Spruce Pine and mountain regions. "
            "Tribal operations (Eastern Band of Cherokee Indians) include casino, hospitality, construction, and "
            "government services in Qualla Boundary (Jackson/Swain counties). "
            "NC Beach and Coastal Rental market is massive — Outer Banks alone has 5,000+ vacation rental properties. "
            "Municipal insurance pools (NC Interlocal Risk Management Agency — IRMA) serve many local governments."
        ),
        "top_industries": [
            "Construction", "Manufacturing", "Healthcare", "Agriculture", "Tourism/Hospitality",
            "Banking/Finance", "Technology", "Short-Term Rentals", "Mining", "Municipal Government",
            "High-Value Residential", "Contractors", "Trucking", "Food Processing", "Forestry",
        ],
    },
    {
        "state_code": "GA",
        "state_name": "Georgia",
        "wc_monopolistic": False,
        "wc_competitive": True,
        "wc_notes": (
            "GA State Board of Workers Compensation oversees the system. Employers with 3+ employees must carry "
            "coverage. GA uses NCCI class codes. Experience rating at $7,500+ premium. "
            "GA has a 400-week cap on income benefits for most injuries. "
            "Catastrophic injuries have no time limit. GA requires employer posting of WC panel of physicians."
        ),
        "regulatory_notes": (
            "GA Office of Insurance and Safety Fire Commissioner regulates P&C. GA is a file-and-use state. "
            "Contractor licensing is handled at county/city level — no statewide general contractor license. "
            "Some trades (electrical, plumbing, conditioned air) require state licenses. "
            "GA requires certificates for public works. GA Fire Safety Division enforces fire codes."
        ),
        "tort_environment": "moderate",
        "cat_exposures": [
            "Hurricane — coastal Georgia (Savannah, Brunswick, Golden Isles) vulnerable",
            "Severe convective storms — tornadoes and hail across central and north GA",
            "Flooding — flash flooding in metro Atlanta and mountain streams in north GA",
            "Ice storms — north Georgia mountains and Piedmont",
            "Drought — agricultural exposure in south Georgia",
            "Wildfire — increasing risk in north GA mountains",
        ],
        "compliance_items": [
            "GA trade-specific licenses (electrical, plumbing, conditioned air) through Secretary of State",
            "GA OSHA — federal OSHA state (no state plan for private sector)",
            "GA Environmental Protection Division (EPD) permits for emissions and discharge",
            "GA Mine Safety requirements (MSHA federal plus state oversight)",
            "Coastal Marshlands Protection Act — permits for coastal development",
            "Short-term rental regulations vary by municipality (Atlanta, Savannah have specific ordinances)",
            "GA requires 45-day notice of cancellation for homeowners in coastal counties",
        ],
        "market_notes": (
            "GA is the 8th largest state. Metro Atlanta dominates the economy (logistics hub, Hartsfield-Jackson). "
            "Savannah is a major port city with warehousing, logistics, and manufacturing growth. "
            "North GA mountains (Blue Ridge, Ellijay, Helen) have growing vacation rental and retirement markets. "
            "South GA is agricultural (pecans, cotton, peanuts, poultry). "
            "GA has a growing film industry (Pinewood Studios) creating unique entertainment liability needs. "
            "Significant military installations (Fort Moore, Kings Bay, Robins AFB) create contractor demand. "
            "GA tribal operations limited but Cherokee heritage tourism exists in north GA. "
            "Mining includes kaolin (world's largest deposits), granite, and marble. "
            "Poultry processing is massive — GA is the #1 broiler-producing state."
        ),
        "top_industries": [
            "Logistics/Warehousing", "Construction", "Poultry/Agriculture", "Manufacturing",
            "Film/Entertainment", "Healthcare", "Trucking", "Hospitality", "Mining/Kaolin",
            "Military Contracting", "Technology", "Short-Term Rentals", "Forestry",
        ],
    },
    {
        "state_code": "SC",
        "state_name": "South Carolina",
        "wc_monopolistic": False,
        "wc_competitive": True,
        "wc_notes": (
            "SC Workers Compensation Commission administers the system. Employers with 4+ employees must carry "
            "coverage (agricultural employers: 1+ employees if >$3K quarterly payroll). SC uses NCCI class codes. "
            "SC has a 500-week cap on temporary total disability. "
            "SC allows employers to establish self-insured workers comp programs."
        ),
        "regulatory_notes": (
            "SC Department of Insurance regulates P&C. SC is a file-and-use state. "
            "SC Contractors Licensing Board requires licensure for general and mechanical contractors. "
            "SC has a Residential Builders Commission for residential contractors. "
            "Coastal Tidelands and Wetlands Act governs coastal construction. "
            "SC Beachfront Management Act restricts construction seaward of setback lines."
        ),
        "tort_environment": "moderate",
        "cat_exposures": [
            "Hurricane — entire coastline (Charleston, Myrtle Beach, Hilton Head); Hugo (1989), Matthew (2016)",
            "Flooding — catastrophic inland flooding (2015 floods caused $12B+ damage statewide)",
            "Severe convective storms — hail and tornadoes across Upstate and Midlands",
            "Earthquake — Charleston seismic zone is most active on East Coast",
            "Ice storms — Upstate and mountain areas",
        ],
        "compliance_items": [
            "SC General Contractor License through SC Contractors Licensing Board",
            "SC Residential Builder License through SC Residential Builders Commission",
            "SC OSHA — federal OSHA state (no state plan for private sector)",
            "SC DHEC permits for environmental compliance",
            "SC Beachfront Management Act compliance for coastal construction",
            "Short-term rental regulations vary — Myrtle Beach, Charleston, Hilton Head have specific rules",
            "SC requires 30-day notice of cancellation for commercial policies",
        ],
        "market_notes": (
            "SC coastal tourism is massive — Myrtle Beach, Charleston, Hilton Head drive hospitality and rental markets. "
            "Charleston is a growing tech hub and major port. Greenville-Spartanburg (Upstate) is a manufacturing "
            "powerhouse (BMW, Michelin, automotive suppliers). SC has strong military presence (Fort Jackson, "
            "Charleston Naval Weapons Station, Shaw AFB). Hilton Head and Kiawah Island have significant high-value "
            "residential exposure. SC mountains (Table Rock, Caesars Head) have growing vacation rental market. "
            "SC has no Catawba Indian tribal casino but the Catawba Nation is building one near Kings Mountain. "
            "Agriculture includes tobacco, soybeans, and significant timber/forestry."
        ),
        "top_industries": [
            "Tourism/Hospitality", "Manufacturing", "Construction", "Short-Term Rentals",
            "Healthcare", "Military Contracting", "Automotive Manufacturing", "Agriculture",
            "Port/Logistics", "High-Value Residential", "Forestry", "Trucking",
        ],
    },
    {
        "state_code": "TN",
        "state_name": "Tennessee",
        "wc_monopolistic": False,
        "wc_competitive": True,
        "wc_notes": (
            "TN Bureau of Workers Compensation administers the system. Employers with 5+ employees must carry "
            "coverage (construction: 1+ employees, mining: 1+ employees, coal mining: all). "
            "TN uses NCCI class codes with state-specific modifications. "
            "TN has significant reforms limiting benefit duration. Pre-authorization required for medical treatment."
        ),
        "regulatory_notes": (
            "TN Department of Commerce and Insurance regulates P&C. TN is a file-and-use state. "
            "TN Board for Licensing Contractors requires licensure for projects over $25,000. "
            "TN has state-specific plumbing, electrical, and HVAC license requirements. "
            "TN Environmental Protection Act governs industrial discharge and pollution."
        ),
        "tort_environment": "tort-reform",
        "cat_exposures": [
            "Severe convective storms — TN is in Dixie Alley for tornadoes (Nashville 2020 tornado was catastrophic)",
            "Flooding — flash floods in Nashville basin and mountain valleys (2010 Nashville flood: $2B+)",
            "Earthquake — New Madrid Seismic Zone affects western TN (Memphis area)",
            "Winter storms — ice storms across middle TN, heavy snow in Smokies",
            "Wildfire — Gatlinburg fire (2016) destroyed 2,400+ structures",
            "Landslides — eastern TN mountain areas after heavy rain",
        ],
        "compliance_items": [
            "TN Contractor License through TN Board for Licensing Contractors (projects >$25K)",
            "TN OSHA (TOSHA) — state-plan state with own enforcement",
            "TN mining requires 1+ employee WC coverage — no exceptions",
            "TN Department of Environment and Conservation (TDEC) permits",
            "Short-term rental regulations — Nashville has specific permit requirements",
            "TN Smokies and mountain communities have vacation rental ordinances",
            "TN requires 30-day notice of cancellation for commercial policies",
        ],
        "market_notes": (
            "TN has no state income tax, driving massive business relocation and growth. Nashville is booming — "
            "healthcare industry HQ (HCA, Community Health), entertainment, and construction. Memphis is a global "
            "logistics hub (FedEx HQ) with warehousing and distribution. Knoxville/East TN has manufacturing, "
            "energy (TVA), and Smoky Mountain tourism. Chattanooga is a growing tech city. "
            "Great Smoky Mountains tourism drives massive short-term rental and hospitality markets in Gatlinburg, "
            "Pigeon Forge, and Sevierville. TN has strong auto manufacturing (Nissan, VW, GM). "
            "Mining includes zinc, limestone, and coal in East TN. "
            "Tribal: no federally recognized tribes with land in TN, but Cherokee heritage tourism is significant. "
            "TN tort reform (2011) capped non-economic damages, making it insurer-friendly."
        ),
        "top_industries": [
            "Healthcare", "Logistics/Warehousing", "Construction", "Auto Manufacturing",
            "Tourism/Hospitality", "Short-Term Rentals", "Music/Entertainment", "Trucking",
            "Mining", "Energy", "Agriculture", "Technology", "Food Processing",
        ],
    },
]


def seed_states():
    db = SessionLocal()
    try:
        existing = db.query(StateProfile).count()
        if existing > 0:
            print(f"Database already has {existing} state profiles. Skipping seed.")
            return

        for data in STATE_PROFILES:
            profile = StateProfile(**data)
            db.add(profile)

        db.commit()
        print(f"Seeded {len(STATE_PROFILES)} state profiles.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_states()
