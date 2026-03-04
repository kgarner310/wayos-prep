"""Seed the database with 20 industry risk profiles."""
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.industry import IndustryRiskProfile

INDUSTRIES = [
    {
        "industry_name": "Roofing",
        "synonyms": ["roofer", "roofing contractor", "roof repair", "roof installation"],
        "top_workers_comp_claims": [
            "Falls from height — leading cause of fatalities and permanent disability",
            "Heat-related illness during summer months",
            "Repetitive strain injuries from nail guns and lifting",
            "Burns from hot tar and torch-down applications",
        ],
        "commercial_auto_claims": [
            "Material hauling accidents with loaded trucks",
            "Trailer detachment on highways",
            "Backing accidents at job sites",
        ],
        "general_liability_exposures": [
            "Property damage from leaks after completed work",
            "Completed operations claims (faulty installation)",
            "Falling debris injuring pedestrians or adjacent property",
            "Subcontractor liability gaps",
        ],
        "conversation_prompts": [
            "How do you manage fall protection compliance on every job?",
            "What's your subcontractor vetting and certificate process?",
            "Have you had any completed operations claims in the past 3 years?",
            "How do you handle storm chasing or emergency repair work?",
        ],
        "regional_risk_notes": "Hail belt states (TX, CO, OK) see surge pricing and claim spikes. Hurricane-prone coastal areas carry wind/debris exposure. OSHA fall protection enforcement is aggressive in this class.",
    },
    {
        "industry_name": "Landscaping",
        "synonyms": ["landscaper", "lawn care", "grounds maintenance", "lawn service", "yard maintenance"],
        "top_workers_comp_claims": [
            "Lacerations from mowers, trimmers, and edgers",
            "Heat exhaustion and heat stroke",
            "Repetitive motion injuries (shoulders, back)",
            "Chemical exposure from pesticides and herbicides",
        ],
        "commercial_auto_claims": [
            "Trailer sway accidents hauling equipment",
            "Accidents with crew trucks towing trailers",
            "Equipment falling from trailers on roadways",
        ],
        "general_liability_exposures": [
            "Property damage to irrigation systems and utilities",
            "Herbicide overspray damaging neighboring properties",
            "Trip and fall hazards from incomplete work",
            "Tree trimming damage to structures or power lines",
        ],
        "conversation_prompts": [
            "How many crew vehicles and trailers are on the road daily?",
            "Do you carry a pesticide applicator license?",
            "What safety training do seasonal workers receive?",
            "Any tree removal or work above 10 feet?",
        ],
        "regional_risk_notes": "Southern and Sun Belt states have year-round exposure. Cold-weather states add snow removal liability. Pesticide regulations vary dramatically by state.",
    },
    {
        "industry_name": "Restaurants",
        "synonyms": ["restaurant", "food service", "dining", "eatery", "cafe", "diner", "bar and grill"],
        "top_workers_comp_claims": [
            "Burns and scalds from cooking equipment",
            "Slip and fall injuries in kitchen areas",
            "Cuts and lacerations from knives and slicers",
            "Repetitive strain from food preparation tasks",
        ],
        "commercial_auto_claims": [
            "Delivery driver accidents",
            "Catering vehicle incidents",
            "Employee commute accidents (if employer-provided transport)",
        ],
        "general_liability_exposures": [
            "Foodborne illness claims (E. coli, salmonella)",
            "Customer slip and fall on premises",
            "Liquor liability (if serving alcohol)",
            "Allergen-related injury claims",
        ],
        "conversation_prompts": [
            "Do you serve alcohol and carry liquor liability?",
            "What food safety certifications does your kitchen staff hold?",
            "Do you handle delivery with your own drivers or third party?",
            "How often are kitchen suppression systems inspected?",
        ],
        "regional_risk_notes": "Liquor liability requirements vary by state. Health department inspection frequency differs regionally. States like CA have aggressive employment practices liability exposure.",
    },
    {
        "industry_name": "Trucking",
        "synonyms": ["trucking company", "freight hauler", "long haul", "OTR", "transportation", "carrier"],
        "top_workers_comp_claims": [
            "Back injuries from loading/unloading",
            "Injuries from slips off cab and trailer",
            "Fatigue-related incidents during long hauls",
            "Repetitive strain from extended driving",
        ],
        "commercial_auto_claims": [
            "Rear-end collisions with loaded trailers",
            "Jackknife accidents in adverse weather",
            "Cargo spills causing third-party damage",
            "Intersection accidents with passenger vehicles",
        ],
        "general_liability_exposures": [
            "Cargo damage or loss liability",
            "Environmental contamination from fuel or cargo spills",
            "Loading dock property damage",
            "Pollution liability for hazmat loads",
        ],
        "conversation_prompts": [
            "What radius do your drivers typically operate in?",
            "What's your driver turnover rate and hiring standards?",
            "Do you haul any hazmat or specialized cargo?",
            "How are driver MVRs monitored after hire?",
        ],
        "regional_risk_notes": "Nuclear verdicts are reshaping trucking liability nationwide. DOT compliance and CSA scores directly impact insurability. Winter states add significant seasonal exposure.",
    },
    {
        "industry_name": "Manufacturing",
        "synonyms": ["manufacturer", "factory", "production facility", "industrial production", "fabrication"],
        "top_workers_comp_claims": [
            "Machine-related amputations and crush injuries",
            "Hearing loss from prolonged noise exposure",
            "Repetitive motion injuries on assembly lines",
            "Chemical burns and respiratory illness",
        ],
        "commercial_auto_claims": [
            "Forklift accidents in loading areas",
            "Delivery truck incidents",
            "Product transport accidents",
        ],
        "general_liability_exposures": [
            "Product liability from defective goods",
            "Environmental contamination claims",
            "Visitor injuries on factory floor",
            "Recall-related financial exposure",
        ],
        "conversation_prompts": [
            "What's your machine guarding and lockout/tagout compliance status?",
            "Do you carry product liability and what are your biggest product lines?",
            "Any environmental permits or EPA exposure?",
            "How do you manage quality control and defect tracking?",
        ],
        "regional_risk_notes": "States with heavy manufacturing (OH, MI, IN, TX) have higher frequency. OSHA enforcement intensity varies by region. Environmental regulations are strictest in CA, NJ, and Northeast.",
    },
    {
        "industry_name": "Construction",
        "synonyms": ["general contractor", "GC", "builder", "construction company", "building contractor"],
        "top_workers_comp_claims": [
            "Falls from scaffolding and ladders",
            "Struck-by injuries from falling objects",
            "Trench collapse and excavation accidents",
            "Electrocution from power line contact",
        ],
        "commercial_auto_claims": [
            "Heavy equipment transport accidents",
            "Work truck collisions at or near job sites",
            "Equipment trailer incidents on public roads",
        ],
        "general_liability_exposures": [
            "Structural defects in completed work",
            "Property damage to adjacent structures",
            "Subcontractor liability gaps",
            "Construction defect litigation (long-tail claims)",
        ],
        "conversation_prompts": [
            "What percentage of work is subcontracted and how do you verify insurance?",
            "What's your safety program and EMR trend?",
            "Do you do any residential work (construction defect exposure)?",
            "What types of contracts do you typically sign — who holds risk?",
        ],
        "regional_risk_notes": "Construction defect statutes of repose vary by state (2-12 years). Coastal and seismic zones carry additional structural risk. Prevailing wage requirements affect payroll in many states.",
    },
    {
        "industry_name": "Auto Repair",
        "synonyms": ["auto shop", "mechanic", "auto body", "collision repair", "car repair", "automotive repair"],
        "top_workers_comp_claims": [
            "Crush injuries from vehicle lifts and jacks",
            "Chemical exposure (solvents, paints, brake dust)",
            "Burns from exhaust systems and welding",
            "Back injuries from working under vehicles",
        ],
        "commercial_auto_claims": [
            "Test drive accidents with customer vehicles",
            "Tow truck incidents",
            "Customer vehicle damage during road tests",
        ],
        "general_liability_exposures": [
            "Faulty repair leading to customer accident",
            "Customer vehicle damage while in custody",
            "Environmental contamination from fluid disposal",
            "Garage keepers legal liability",
        ],
        "conversation_prompts": [
            "Do you carry garagekeepers coverage for customer vehicles?",
            "How do you handle hazardous waste disposal?",
            "Do employees test drive customer vehicles on public roads?",
            "Any paint booth or body work operations?",
        ],
        "regional_risk_notes": "Environmental cleanup liability varies by state. Garagekeepers requirements differ. States with vehicle inspection mandates create different liability profiles.",
    },
    {
        "industry_name": "Retail",
        "synonyms": ["retail store", "shop", "retail business", "storefront", "merchant"],
        "top_workers_comp_claims": [
            "Lifting and stocking injuries (back, shoulder)",
            "Slip and fall in stockrooms",
            "Box cutter and utility knife lacerations",
            "Repetitive motion from checkout operations",
        ],
        "commercial_auto_claims": [
            "Delivery vehicle accidents",
            "Employee errand driving incidents",
        ],
        "general_liability_exposures": [
            "Customer slip and fall on premises",
            "Product liability for sold goods",
            "Assault or crime on premises",
            "ADA compliance failures",
        ],
        "conversation_prompts": [
            "What's your foot traffic volume and premises maintenance routine?",
            "Do you sell any products that could create product liability exposure?",
            "What security measures are in place (cameras, guards)?",
            "Any delivery operations using company vehicles?",
        ],
        "regional_risk_notes": "Urban locations carry higher crime and premises liability. Mall vs standalone locations have different exposure profiles. State consumer protection laws vary significantly.",
    },
    {
        "industry_name": "Assisted Living",
        "synonyms": ["senior care", "nursing home", "elder care", "assisted living facility", "memory care", "senior living"],
        "top_workers_comp_claims": [
            "Back injuries from patient lifting and transfers",
            "Needle sticks and bloodborne pathogen exposure",
            "Workplace violence from residents",
            "Slip and fall during patient care",
        ],
        "commercial_auto_claims": [
            "Patient transport vehicle accidents",
            "Staff shuttle incidents",
        ],
        "general_liability_exposures": [
            "Abuse and neglect allegations",
            "Medication errors",
            "Elopement (resident wandering)",
            "Professional liability / malpractice",
        ],
        "conversation_prompts": [
            "What's your staff-to-resident ratio?",
            "How do you manage medication administration and documentation?",
            "What elopement prevention measures are in place?",
            "Do you carry abuse and molestation coverage?",
        ],
        "regional_risk_notes": "State licensing requirements vary dramatically. Staffing ratio mandates differ by state. Tort reform states vs plaintiff-friendly states create vastly different liability landscapes.",
    },
    {
        "industry_name": "Plumbing",
        "synonyms": ["plumber", "plumbing contractor", "pipe fitter", "plumbing service"],
        "top_workers_comp_claims": [
            "Back injuries from working in confined spaces",
            "Burns from soldering and torch work",
            "Exposure to sewage and biological hazards",
            "Knee injuries from prolonged kneeling",
        ],
        "commercial_auto_claims": [
            "Service van accidents while responding to emergencies",
            "Equipment-laden vehicle handling issues",
        ],
        "general_liability_exposures": [
            "Water damage from faulty installations",
            "Property damage during excavation or pipe work",
            "Completed operations failures (leaks after project)",
            "Cross-contamination of water supply",
        ],
        "conversation_prompts": [
            "Do you do any excavation or sewer line work?",
            "What's your callback rate on completed jobs?",
            "How many service vehicles are on the road?",
            "Any commercial or new construction work?",
        ],
        "regional_risk_notes": "Freeze-thaw regions see seasonal claim spikes. Licensing requirements vary by state and municipality. Older building stock in Northeast increases exposure.",
    },
    {
        "industry_name": "Electrical Contractors",
        "synonyms": ["electrician", "electrical contractor", "electrical service", "electric company"],
        "top_workers_comp_claims": [
            "Electrocution and electrical burns",
            "Falls from ladders and lifts",
            "Arc flash injuries",
            "Eye injuries from debris and sparks",
        ],
        "commercial_auto_claims": [
            "Service van accidents",
            "Bucket truck incidents near power lines",
        ],
        "general_liability_exposures": [
            "Fire caused by faulty wiring installation",
            "Property damage from electrical work",
            "Code violation liability",
            "Completed operations (electrical fires post-completion)",
        ],
        "conversation_prompts": [
            "What voltage levels does your crew work with?",
            "Do you do any utility or high-voltage work?",
            "What's your arc flash safety program?",
            "How do you handle permit and inspection compliance?",
        ],
        "regional_risk_notes": "NEC adoption varies by jurisdiction. States with older infrastructure have higher rewiring exposure. Solar installation work is growing rapidly and carries unique risks.",
    },
    {
        "industry_name": "HVAC",
        "synonyms": ["HVAC contractor", "heating and cooling", "air conditioning", "HVAC service", "heating ventilation"],
        "top_workers_comp_claims": [
            "Falls from rooftops and ladders",
            "Refrigerant burns and chemical exposure",
            "Electrical shock during unit servicing",
            "Heat illness during attic and rooftop work",
        ],
        "commercial_auto_claims": [
            "Service van accidents (high daily mileage)",
            "Refrigerant transport incidents",
        ],
        "general_liability_exposures": [
            "Property damage from refrigerant leaks",
            "Carbon monoxide incidents from faulty furnace installation",
            "Water damage from condensate line failures",
            "Completed operations liability",
        ],
        "conversation_prompts": [
            "Do you handle both residential and commercial systems?",
            "What EPA certifications does your team hold for refrigerant handling?",
            "How many service calls per day per technician?",
            "Any new construction installation work?",
        ],
        "regional_risk_notes": "Southern states have heavier AC exposure; northern states heavier heating. Refrigerant regulations (EPA Section 608) create compliance exposure. Seasonal demand creates hiring surges with less-trained workers.",
    },
    {
        "industry_name": "Painter",
        "synonyms": ["painting contractor", "house painter", "commercial painter", "paint company"],
        "top_workers_comp_claims": [
            "Falls from ladders and scaffolding",
            "Chemical inhalation from paints and solvents",
            "Repetitive strain injuries (shoulders, wrists)",
            "Eye irritation and injury from splashes",
        ],
        "commercial_auto_claims": [
            "Van accidents hauling equipment and materials",
            "Paint spills from improperly secured loads",
        ],
        "general_liability_exposures": [
            "Overspray damage to vehicles and adjacent property",
            "Lead paint disturbance in older buildings",
            "Damage to client property (floors, fixtures)",
            "VOC emission violations",
        ],
        "conversation_prompts": [
            "Do you work on any pre-1978 buildings (lead paint exposure)?",
            "Are you RRP (Renovation, Repair, and Painting) certified?",
            "What height do your crews typically work at?",
            "Interior, exterior, or both — and any industrial coatings?",
        ],
        "regional_risk_notes": "EPA RRP rule applies to pre-1978 structures nationwide. States with older building stock (Northeast, Midwest) carry heavier lead paint risk. VOC regulations are strictest in CA and Northeast.",
    },
    {
        "industry_name": "Concrete",
        "synonyms": ["concrete contractor", "concrete company", "concrete work", "flatwork", "concrete pouring"],
        "top_workers_comp_claims": [
            "Chemical burns from wet concrete (alkaline)",
            "Back and knee injuries from finishing work",
            "Silica dust inhalation",
            "Struck-by injuries from concrete trucks and pumps",
        ],
        "commercial_auto_claims": [
            "Concrete mixer truck accidents",
            "Heavy equipment transport incidents",
            "Pump truck setup and operation accidents",
        ],
        "general_liability_exposures": [
            "Structural failure of completed concrete work",
            "Property damage from concrete spills",
            "Trip hazards from incomplete flatwork",
            "Subsurface utility damage during excavation",
        ],
        "conversation_prompts": [
            "What type of concrete work — flatwork, structural, decorative?",
            "Do you operate your own batch plant or mixer trucks?",
            "What's your silica exposure control plan?",
            "Any post-tension or structural concrete work?",
        ],
        "regional_risk_notes": "Freeze-thaw cycles in northern states cause concrete failure claims. OSHA silica rule enforcement is increasing. Seismic zones require special structural concrete standards.",
    },
    {
        "industry_name": "Janitorial Services",
        "synonyms": ["janitorial", "cleaning service", "commercial cleaning", "custodial", "office cleaning"],
        "top_workers_comp_claims": [
            "Slip and fall injuries while mopping",
            "Chemical burns and respiratory issues from cleaning agents",
            "Back injuries from repetitive lifting and bending",
            "Needle stick injuries in medical facility cleaning",
        ],
        "commercial_auto_claims": [
            "Crew transport van accidents",
            "Equipment transport incidents",
        ],
        "general_liability_exposures": [
            "Client property damage (broken items, chemical damage to surfaces)",
            "Third-party slip and fall on wet floors",
            "Theft allegations by client employees",
            "Key holder and access liability",
        ],
        "conversation_prompts": [
            "What types of facilities do you clean (office, medical, industrial)?",
            "How do you handle key access and security for client sites?",
            "What's your employee screening and background check process?",
            "Do you use any biohazard or specialty cleaning chemicals?",
        ],
        "regional_risk_notes": "Medical facility cleaning carries heightened bloodborne pathogen exposure. Minimum wage variations by state affect payroll-based premiums. High employee turnover is common in this class.",
    },
    {
        "industry_name": "Pest Control",
        "synonyms": ["pest control company", "exterminator", "pest management", "fumigation", "bug spray"],
        "top_workers_comp_claims": [
            "Chemical exposure and poisoning from pesticides",
            "Animal and insect bites and stings",
            "Injuries in crawl spaces and attics",
            "Ladder falls during exterior treatments",
        ],
        "commercial_auto_claims": [
            "Service vehicle accidents (high daily route mileage)",
            "Chemical spills from vehicle-mounted tanks",
        ],
        "general_liability_exposures": [
            "Property damage from fumigation chemicals",
            "Pet injury or death from pesticide exposure",
            "Failure to control infestation (breach of contract)",
            "Environmental contamination from chemical runoff",
        ],
        "conversation_prompts": [
            "Do you perform fumigation or just spray treatments?",
            "What chemicals and application methods do you use?",
            "How many service routes operate daily?",
            "Any wildlife removal or exclusion work?",
        ],
        "regional_risk_notes": "Termite exposure is highest in the South and Southeast. State pesticide licensing varies significantly. EPA regulations on restricted-use pesticides create compliance risk.",
    },
    {
        "industry_name": "Daycare",
        "synonyms": ["daycare center", "child care", "preschool", "childcare", "nursery school", "early childhood"],
        "top_workers_comp_claims": [
            "Back injuries from lifting children",
            "Slip and fall injuries on play areas",
            "Bites and scratches from children",
            "Infectious disease exposure",
        ],
        "commercial_auto_claims": [
            "Child transport vehicle accidents",
            "Liability for children left in vehicles",
        ],
        "general_liability_exposures": [
            "Abuse and molestation allegations",
            "Child injury during activities",
            "Playground equipment injuries",
            "Failure to supervise claims",
        ],
        "conversation_prompts": [
            "What's your staff-to-child ratio and how is it maintained?",
            "Do you transport children in facility vehicles?",
            "What's your background check and hiring process?",
            "Do you carry abuse and molestation coverage?",
        ],
        "regional_risk_notes": "State licensing ratios and requirements vary dramatically. Background check requirements differ by jurisdiction. Playground safety standards (CPSC/ASTM) apply nationwide.",
    },
    {
        "industry_name": "Dental Clinic",
        "synonyms": ["dentist", "dental office", "dental practice", "orthodontist", "oral surgery"],
        "top_workers_comp_claims": [
            "Needle stick and sharps injuries",
            "Repetitive strain from dental procedures",
            "Mercury and chemical exposure",
            "Back and neck injuries from sustained positioning",
        ],
        "commercial_auto_claims": [
            "Mobile dental unit accidents",
            "Employee commute incidents",
        ],
        "general_liability_exposures": [
            "Professional malpractice (wrong tooth, nerve damage)",
            "Anesthesia complications",
            "Patient slip and fall on premises",
            "HIPAA breach liability",
        ],
        "conversation_prompts": [
            "Do you perform any oral surgery or sedation dentistry?",
            "What's your sterilization protocol and compliance record?",
            "How do you handle patient records and HIPAA compliance?",
            "Any specialty services (implants, orthodontics)?",
        ],
        "regional_risk_notes": "Malpractice rates vary dramatically by state. Tort reform states have lower premiums. Sedation dentistry carries significantly higher professional liability.",
    },
    {
        "industry_name": "Warehousing",
        "synonyms": ["warehouse", "distribution center", "fulfillment center", "storage facility", "logistics"],
        "top_workers_comp_claims": [
            "Forklift accidents and pedestrian strikes",
            "Back injuries from manual material handling",
            "Falls from racking and loading docks",
            "Crush injuries from falling inventory",
        ],
        "commercial_auto_claims": [
            "Delivery truck accidents",
            "Loading dock backing incidents",
            "Forklift operations in shared traffic areas",
        ],
        "general_liability_exposures": [
            "Stored goods damage or loss (bailee liability)",
            "Visitor injuries in warehouse",
            "Fire and sprinkler damage to stored goods",
            "Environmental exposure from stored chemicals",
        ],
        "conversation_prompts": [
            "What types of goods do you store — any hazmat or temperature-sensitive?",
            "How many forklift operators and what's your training program?",
            "Do you carry bailee coverage for customer goods?",
            "What fire suppression systems are in place?",
        ],
        "regional_risk_notes": "Distribution hubs (Memphis, Louisville, Chicago) see higher frequency. Cold storage operations carry unique ammonia exposure. E-commerce growth is driving rapid expansion with newer, less-trained workers.",
    },
    {
        "industry_name": "Towing",
        "synonyms": ["tow company", "towing service", "wrecker service", "roadside assistance", "tow truck"],
        "top_workers_comp_claims": [
            "Struck-by injuries on roadside (passing traffic)",
            "Back injuries from hooking and loading vehicles",
            "Crush injuries from winch and cable operations",
            "Injuries from working in adverse weather and darkness",
        ],
        "commercial_auto_claims": [
            "Accidents while responding to calls (emergency driving)",
            "Damage to towed vehicles",
            "Collisions with tow truck and loaded vehicle",
            "Incidents in highway emergency lanes",
        ],
        "general_liability_exposures": [
            "Damage to customer vehicles during towing",
            "Garage keepers liability for stored vehicles",
            "On-hook coverage gaps",
            "Property damage at accident scenes",
        ],
        "conversation_prompts": [
            "What's your mix of consent vs non-consent tows?",
            "Do you carry on-hook and garage keepers coverage?",
            "How do you manage driver fatigue for after-hours calls?",
            "What training do drivers receive for highway safety?",
        ],
        "regional_risk_notes": "Move Over laws vary by state and affect roadside exposure. Non-consent towing creates additional legal exposure. Winter states see seasonal volume spikes with higher accident rates.",
    },
]


def seed_industries():
    db = SessionLocal()
    try:
        existing = db.query(IndustryRiskProfile).count()
        if existing > 0:
            print(f"Database already has {existing} industries. Skipping seed.")
            return

        for data in INDUSTRIES:
            profile = IndustryRiskProfile(**data)
            db.add(profile)

        db.commit()
        print(f"Seeded {len(INDUSTRIES)} industry risk profiles.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_industries()
