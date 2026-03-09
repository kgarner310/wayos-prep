"""Seed demo data for WAYOS PREP.

Run: python seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.models import Source
from app.services.ingestion import ingest_raw_text
from app.services.parser import clean_text
from app.services.chunker import chunk_text
from app.services.tagging import tag_source, tag_chunk
from app.models.models import SourceChunk
from app.core.enums import SourceStatus

SAMPLE_SOURCES = [
    {
        "title": "Roofing Contractor Risk Guide: Workers Comp and Safety",
        "source_type": "trade_publication",
        "authority_level": "trade_association",
        "jurisdiction_state": "nc",
        "published_at": datetime(2025, 8, 15, tzinfo=timezone.utc),
        "publisher": "National Roofing Contractors Association",
        "raw_text": """# Roofing Contractor Risk Guide

## Falls From Height: The #1 Loss Driver

Falls from height remain the leading cause of death and serious injury in the roofing industry. OSHA reports that falls account for approximately 33% of all construction fatalities, with roofers facing the highest rate of fatal falls among all construction trades.

### Key Statistics
- The average workers compensation claim for a roofing fall exceeds $100,000
- Lost-time claim frequency for roofing contractors is 3-5x higher than general construction
- Residential re-roofing operations carry higher fall risk due to steep-slope work

### Risk Mitigation
- Fall protection plans are required for work above 6 feet (OSHA 29 CFR 1926.501)
- Personal fall arrest systems, guardrails, or safety nets must be used
- Regular toolbox talks on fall prevention reduce claim frequency by 40-60%

## Subcontractor Management

Many roofing contractors rely heavily on subcontractors, creating significant risk transfer challenges:
- Certificate of insurance tracking is often inconsistent
- Subcontractor workers comp coverage gaps can create employer liability for the general contractor
- Improper classification of 1099 workers vs employees is a common audit finding
- NC requires all subcontractors with 3+ employees to carry workers comp

## Experience Modification Rate

Roofing contractors typically carry experience mods above 1.0 due to high claim frequency. Key factors:
- High-severity fall claims dramatically impact the mod for 3 years
- Frequency of small claims (cuts, strains) also drives mod increases
- A mod above 1.25 signals poor loss history and may limit carrier options

## Workers Compensation in North Carolina

North Carolina is a competitive workers comp state with key considerations:
- The NC Rate Bureau sets advisory rates for roofing class codes
- Class code 5551 (roofing) carries some of the highest WC rates in the state
- NC requires workers comp for employers with 3+ employees
- The NC Industrial Commission administers claims and disputes

## Commercial Auto Exposure

Roofing contractors operate trucks, trailers, and material delivery vehicles:
- Fleet accidents are the second-largest loss driver after falls
- Hired and non-owned auto coverage is critical for contractors using personal vehicles
- Material delivery from supplier to job site creates auto liability exposure
- Driver MVR reviews should be conducted annually

## Coverage Gaps to Watch

Common coverage blind spots for roofing contractors include:
- Inland marine coverage for tools and equipment on job sites
- Builders risk coverage during active construction
- Completed operations exposure (leaks discovered after job completion)
- Pollution liability for tear-off debris and disposal
- Umbrella coverage may be required by general contractors
""",
    },
    {
        "title": "Trucking Industry Loss Trends and Fleet Risk Management",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
        "publisher": "National Insurance Risk Council",
        "raw_text": """# Trucking Industry Loss Trends 2025

## Fleet Accidents: Primary Loss Driver

Motor vehicle accidents remain the dominant loss driver for trucking operations:
- Average commercial auto liability claim exceeds $150,000
- Nuclear verdicts (jury awards exceeding $10 million) have increased 300% since 2015
- Distracted driving and driver fatigue are the leading accident causes
- DOT compliance violations correlate strongly with accident frequency

### Driver Turnover Crisis

The trucking industry faces chronic driver turnover exceeding 90% annually for large carriers:
- New/inexperienced drivers are 3x more likely to be involved in preventable accidents
- Driver recruitment pressure leads to relaxed hiring standards
- CDL training quality varies dramatically across programs
- Driver retention programs reduce accident frequency by 25-35%

## Workers Compensation for Trucking

Despite drivers spending most time on the road, workers comp claims remain significant:
- Loading/unloading injuries account for 40% of trucker WC claims
- Slips, trips, and falls at delivery locations are common
- Cumulative trauma injuries (back, neck, shoulder) from prolonged driving
- Multi-state operations complicate workers comp jurisdiction and filing

## Coverage Considerations

### Commercial Auto
- Primary liability limits of $1 million are standard; many shippers require $2-5 million
- Motor cargo coverage protects against damage to freight
- Trailer interchange agreements need specific coverage endorsement
- Non-owned trailer physical damage often overlooked

### General Liability
- Premises liability at terminal locations
- Completed operations for freight brokers
- Contractual liability for shipper agreements

### Umbrella/Excess
- Nuclear verdict exposure makes high umbrella limits essential
- $5-10 million umbrella limits are increasingly standard
- Some carriers pulling back from trucking umbrella market

## Regulatory Compliance

- FMCSA CSA scores directly impact insurance pricing
- ELD mandate compliance is now table stakes
- Drug and alcohol testing program (DOT requirements)
- Annual driver qualification file maintenance required
- Hours of service violations are a leading citation

## Fleet Management Best Practices

- Implement dash cameras (front and driver-facing)
- Monthly driver scorecard programs
- Pre-trip and post-trip inspection protocols
- Preventive maintenance scheduling reduces breakdowns and accidents
- Speed governor implementation for governed fleets
""",
    },
    {
        "title": "Manufacturing Safety: Machine Guarding and Workers Comp",
        "source_type": "article",
        "authority_level": "standards_body",
        "jurisdiction_state": "nc",
        "published_at": datetime(2025, 10, 1, tzinfo=timezone.utc),
        "publisher": "Manufacturing Safety Alliance",
        "raw_text": """# Manufacturing Safety: Essential Risk Controls

## Machine Guarding: Critical Exposure

Machine guarding violations remain OSHA's most frequently cited standard in manufacturing:
- OSHA Standard 1910.212 requires point-of-operation guards on all machines
- Amputations and crush injuries from unguarded machinery result in severe WC claims
- Average machine guarding injury claim exceeds $75,000 in workers comp costs
- Lockout/tagout (LOTO) compliance is essential during maintenance operations

### Common Machine Guarding Issues
- Missing or bypassed safety guards on presses, saws, and conveyors
- Inadequate lockout/tagout procedures during maintenance
- Failure to train employees on energy control procedures
- Emergency stop buttons not properly positioned or maintained

## Combustible Dust Hazard

Manufacturing operations that generate combustible dust face explosion risk:
- Wood, metal, plastic, and grain dusts can create explosive atmospheres
- OSHA's National Emphasis Program targets combustible dust hazards
- Dust collection systems require regular inspection and maintenance
- Housekeeping programs are the first line of defense

## Ergonomic and Repetitive Motion Injuries

- Repetitive motion injuries account for 30% of manufacturing WC claims
- Material handling (lifting, carrying, pushing) drives musculoskeletal injuries
- Assembly line work creates cumulative trauma disorder exposure
- Ergonomic assessments and job rotation programs reduce injury rates

## Workers Compensation Considerations

- Manufacturing class codes vary widely by specific operation
- NC class code 3632 (machine shops) has moderate WC rates
- Payroll verification and proper employee classification are critical
- Experience mod management through return-to-work programs
- Safety committee programs can qualify for NC premium discounts

## General Liability Exposure

- Products liability for manufactured goods
- Completed operations for custom fabrication
- Recall expense coverage increasingly important
- Contractual liability for OEM supply agreements

## Property and Equipment

- Equipment breakdown coverage (boiler and machinery)
- Business interruption from supply chain disruptions
- Inland marine for goods in transit
- Cyber liability for CNC and IoT-connected equipment
- Property valuation must account for specialized machinery

## Regulatory Environment

- OSHA general industry standards (29 CFR 1910) apply
- EPA environmental compliance for manufacturing waste
- State-specific regulations may impose additional requirements
- NC OSHA (administered by NC DOL) conducts inspections
- Violation penalties have increased significantly in recent years

## Subcontractor and Temporary Worker Risk

- Temporary staffing agencies create workers comp exposure questions
- Borrowed servant doctrine may apply in NC
- Certificate tracking for maintenance subcontractors
- Multi-employer worksite responsibilities under OSHA
""",
    },
    # ── Industry Risk Profiles ───────────────────────────────────────
    {
        "title": "Roofing Contractor Industry Risk Profile",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 11, 1, tzinfo=timezone.utc),
        "publisher": "WAYOS Risk Intelligence",
        "raw_text": """# Roofing Contractor Industry Risk Profile

## Workers Compensation

### Top Injury Types
Falls from height are the dominant workers comp loss driver for roofing contractors. OSHA consistently ranks roofing as the construction trade with the highest fatal fall rate. Other frequent injury types include:
- Lacerations and puncture wounds from tools, nails, and sheet metal
- Heat illness and heat stroke during summer roofing operations
- Lifting injury and back injury from carrying bundles of shingles up ladders
- Struck by falling debris or materials dropped from rooftop
- Repetitive strain from prolonged kneeling, bending, and overhead work

### Typical Severity Drivers
- Fall claims average $100,000-$250,000 in workers comp costs; fatalities drive costs far higher
- Steep-slope residential re-roofing carries higher severity than flat commercial work
- Inexperienced or untrained crew members are 4x more likely to sustain serious falls
- Heat illness claims spike during peak summer season, especially in southern states
- Delayed reporting of cumulative trauma (knees, back, shoulders) inflates claim costs

## General Liability

### Common Claims
- Property damage to customer structures during tear-off (broken windows, gutter damage, landscaping)
- Completed operations claims from water intrusion after project completion
- Third-party bodily injury from falling materials or debris
- Damage to adjacent structures during roofing operations

### Operational Exposures
- Subcontractor use creates vicarious liability if sub causes injury or damage
- Certificate of insurance tracking gaps leave the GC exposed
- Residential exposure increases frequency of homeowner complaints and claims
- Failure to properly protect occupied buildings during tear-off operations

## Commercial Auto

### Typical Exposures
- Trucks hauling materials and equipment between shop and job sites
- Trailer-towing exposure with material flatbeds and equipment trailers
- Hired and non-owned auto exposure when crews use personal vehicles
- Driver MVR issues—roofing crews may not be screened as rigorously as trucking drivers
- Material delivery runs to suppliers create additional road time and exposure

## Property

### Typical Equipment and Building Risks
- Equipment theft from job sites and unlocked trailers is common
- Inland marine exposure for tools, compressors, generators, and specialty equipment
- Shop/warehouse property for material storage and vehicle maintenance
- Builders risk exposure during active construction projects
- Damage to owned equipment from weather events at open job sites

## Regulatory and Safety

### OSHA and Compliance Risks
- Fall protection (29 CFR 1926.501) is OSHA's most-cited standard for roofing
- Scaffold and ladder safety violations are frequent citations
- Hazard communication for adhesives, solvents, and coatings
- Silica dust exposure from cutting concrete tiles or masonry
- Multi-employer worksite doctrine creates liability for controlling employers
- Misclassification of 1099 workers vs W-2 employees triggers audit exposure

## Suggested Producer Questions

Producers should ask roofing contractor clients these key questions during meetings:
1. What is your written fall protection plan and how often do you conduct toolbox talks?
2. What percentage of your work is residential vs commercial, and steep-slope vs flat?
3. Do you use subcontractors or 1099 workers? How do you verify their certificates of insurance?
4. What is your experience modification rate and what loss control measures are you taking to improve it?
5. How do you manage your fleet—do crews drive company vehicles or personal trucks to job sites?
6. What is your annual payroll and how is it allocated across class codes?
7. Do you have a return-to-work program for injured employees?
8. Have you had any OSHA inspections or citations in the past 3 years?
""",
    },
    {
        "title": "Landscaping Contractor Industry Risk Profile",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 11, 1, tzinfo=timezone.utc),
        "publisher": "WAYOS Risk Intelligence",
        "raw_text": """# Landscaping Contractor Industry Risk Profile

## Workers Compensation

### Top Injury Types
Landscaping contractors face a wide range of workplace injury exposures. The most frequent workers comp claims include:
- Lacerations and amputations from mowers, trimmers, chainsaws, and edgers
- Struck by falling branch or tree limb during tree service operations
- Heat illness and heat exhaustion from prolonged outdoor work in high temperatures
- Lifting injury and back injury from manual handling of soil, sod, pavers, and stone
- Slip and fall on uneven terrain, wet grass, and muddy conditions
- Insect stings, animal bites, and allergic reactions in outdoor environments
- Eye injuries from flying debris during mowing, trimming, and blowing operations

### Typical Severity Drivers
- Tree service operations carry the highest severity—chainsaw lacerations and falls from height during tree trimming
- Heat illness claims spike in summer months; employers with no written heat illness prevention program face increased severity
- Seasonal worker turnover means new hires with minimal training are constantly entering the workforce
- Heavy equipment (backhoe, skid steer, excavator) use increases severity when incidents occur
- Crews working near roadways face struck-by vehicle exposure

## General Liability

### Common Claims
- Property damage to customer landscaping, irrigation systems, underground utilities, and fences
- Damage to sidewalks, driveways, and structures from heavy equipment
- Slip and fall claims from customers or pedestrians on work areas
- Chemical application claims—herbicide overspray damaging neighbor properties
- Completed operations claims from tree removal (stump regrowth, root damage)

### Operational Exposures
- Pesticide and herbicide application creates environmental and bodily injury liability
- Working on residential properties increases frequency of property damage claims
- Subcontractor use for specialized work (irrigation, hardscaping) requires certificate tracking
- Snow removal operations (seasonal add-on) create significant slip and fall premises liability

## Commercial Auto

### Typical Exposures
- Truck and trailer combinations are the primary fleet exposure—crews tow mowers and equipment daily
- Drivers may have limited commercial driving experience; MVR screening is often lax
- Hired and non-owned auto exposure when workers drive personal vehicles between sites
- Equipment trailers create towing liability and wider turning radius risks
- Multiple daily trips between job sites increase road exposure substantially
- Seasonal payroll peaks mean temporary drivers with less experience on the road

## Property

### Typical Equipment and Building Risks
- Equipment theft is a major exposure—mowers, blowers, trimmers stored on open trailers
- Inland marine coverage needed for portable equipment and tools
- Shop/yard property for equipment storage, maintenance, and fuel storage
- Fuel storage tanks create environmental liability at the yard
- Seasonal equipment (snow plows, salt spreaders) requires year-round coverage

## Regulatory and Safety

### OSHA and Compliance Risks
- No specific OSHA landscaping standard exists, but general industry (1910) and construction (1926) standards apply
- Tree care operations fall under ANSI Z133 safety standard
- Pesticide applicator licensing required by state agriculture departments
- Heat illness prevention programs increasingly required (federal and state level)
- Eye and face protection required for trimming, mowing, and chipping operations
- Employee misclassification of seasonal workers as 1099 contractors triggers WC audit risk
- Hearing protection required for prolonged equipment operation (OSHA permissible exposure limits)

## Suggested Producer Questions

Producers should ask landscaping contractor clients these key questions:
1. Do you perform tree service work (trimming, removal)? What is the maximum height your crews work at?
2. What types of heavy equipment do you operate—backhoe, skid steer, excavator?
3. What is your seasonal payroll fluctuation? How many seasonal workers do you hire?
4. Do you apply pesticides or herbicides? Are your applicators properly licensed?
5. How do you secure equipment overnight—locked trailers, fenced yard, GPS tracking?
6. Do you offer snow removal services in winter? What is that revenue percentage?
7. How many trucks and trailers are in your fleet and how do you screen drivers?
8. Do you have a written heat illness prevention program for outdoor crews?
9. Do you use subcontractors for irrigation, hardscaping, or specialty work?
""",
    },
    {
        "title": "HVAC Contractor Industry Risk Profile",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 11, 1, tzinfo=timezone.utc),
        "publisher": "WAYOS Risk Intelligence",
        "raw_text": """# HVAC Contractor Industry Risk Profile

## Workers Compensation

### Top Injury Types
HVAC contractors face diverse workplace injury exposures spanning heating and cooling system installation, maintenance, and repair. Common workers comp claims include:
- Burns and scalds from hot surfaces, soldering/brazing torches, and steam lines
- Falls from height when working on rooftop HVAC units, ladders, and scaffolding
- Chemical exposure from refrigerant leaks (R-410A, R-22) causing frostbite or respiratory irritation
- Electrical shock and arc flash during wiring and control panel work
- Lifting injury and back injury from carrying heavy compressors, condensers, and ductwork
- Lacerations from sheet metal fabrication and ductwork installation
- Confined space incidents in crawl spaces, attics, and mechanical rooms

### Typical Severity Drivers
- Rooftop unit work combines fall from height exposure with heavy lifting—dual severity risk
- Refrigerant chemical exposure can cause cardiac sensitization in concentrated doses
- Electrical incidents carry high severity including burn and fatality potential
- Attic work in summer combines heat illness with confined space and fall hazards
- Apprentice-level workers are more likely to sustain burns and cuts from inexperience

## General Liability

### Common Claims
- Property damage from refrigerant leaks, water leaks, and system malfunctions
- Completed operations claims—faulty installation causing water damage, mold, or fire
- Bodily injury to building occupants from carbon monoxide leaks after furnace service
- Damage to customer property (flooring, ceilings, walls) during installation
- Professional liability exposure from system design errors and efficiency guarantees

### Operational Exposures
- Residential work increases claim frequency due to direct customer interaction
- New construction vs retrofit work carries different liability profiles
- Subcontractor use for electrical, plumbing, or controls work requires certificate tracking
- Warranty and callback obligations create ongoing completed operations exposure

## Commercial Auto

### Typical Exposures
- Service van fleet is the primary auto exposure—technicians driving between calls daily
- Vans loaded with heavy tools and parts increase stopping distances and damage severity
- High annual mileage per vehicle increases frequency exposure
- Hired and non-owned auto coverage needed if technicians ever drive personal vehicles
- GPS fleet tracking and telematics increasingly used for driver monitoring

## Property

### Typical Equipment and Building Risks
- Service van contents (tools, equipment, diagnostic instruments, refrigerant) need inland marine coverage
- Shop/warehouse property for parts inventory and fabrication
- Equipment theft from unlocked service vans is common
- Refrigerant inventory storage carries environmental liability
- Sheet metal fabrication shop creates fire exposure from welding and brazing

## Regulatory and Safety

### OSHA and Compliance Risks
- Electrical safety standards (NFPA 70E arc flash) apply to HVAC electrical work
- Confined space entry permits required for mechanical rooms and crawl spaces
- EPA Section 608 certification required for refrigerant handling
- Fall protection required for rooftop unit service above 6 feet
- Hazard communication for refrigerants, solvents, and brazing materials
- State licensing requirements for HVAC contractors vary significantly
- Lead and asbestos exposure during retrofit work in older buildings

## Suggested Producer Questions

Producers should ask HVAC contractor clients these key questions:
1. What percentage of your work is residential vs commercial? New construction vs service/retrofit?
2. How much rooftop unit work do you perform and what fall protection systems do you use?
3. Are all technicians EPA Section 608 certified for refrigerant handling?
4. How many service vans are in your fleet and what is the average annual mileage?
5. Do you perform sheet metal fabrication in-house or subcontract it?
6. Do you use subcontractors for electrical, plumbing, or controls work? How do you track certificates?
7. What is your experience modification rate and have you implemented a safety committee?
8. Do you work in older buildings where lead paint or asbestos may be present?
9. Do you offer energy efficiency guarantees or performance contracts?
""",
    },
    {
        "title": "Restaurant Industry Risk Profile",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 11, 1, tzinfo=timezone.utc),
        "publisher": "WAYOS Risk Intelligence",
        "raw_text": """# Restaurant Industry Risk Profile

## Workers Compensation

### Top Injury Types
Restaurants have one of the highest workers comp claim frequencies across all industries due to fast-paced kitchen environments and high employee turnover. The most common injury types include:
- Burns and scalds from grease, hot surfaces, fryer oil, ovens, and steam equipment
- Lacerations from knives, slicers, food processors, and broken glassware
- Slip and fall on wet or greasy kitchen floors—the single highest-frequency claim type
- Lifting injury and back injury from carrying heavy food containers, kegs, and supplies
- Repetitive strain from prolonged standing, chopping, and repetitive food prep motions
- Struck by falling objects from shelving and walk-in cooler storage

### Typical Severity Drivers
- Deep fryer burns are among the most severe kitchen injuries, often requiring skin grafts
- Slip and fall claims drive the highest total incurred costs due to sheer volume
- High employee turnover means constant onboarding of untrained workers who are more injury-prone
- Seasonal payroll spikes (holidays, summer) bring temporary workers with minimal training
- Late-night operations increase fatigue-related incidents
- Young workforce (under 25) has statistically higher injury rates

## General Liability

### Common Claims
- Slip and fall by customers on wet floors, parking lots, and entrance areas
- Foodborne illness and food contamination claims from improper food handling or storage
- Food safety violations leading to customer illness (norovirus, salmonella, E. coli)
- Liquor liability claims from serving intoxicated patrons (assault, DUI accidents)
- Allergic reaction claims from undisclosed allergens in menu items
- Foreign object in food claims

### Operational Exposures
- Liquor liability is a major exposure for restaurants serving alcohol—dram shop laws vary by state
- Food contamination and foodborne illness claims can trigger significant brand and legal exposure
- Delivery operations (in-house or third-party) add auto and premises liability
- Outdoor dining and patio areas expand premises liability footprint
- Live entertainment, playground equipment, and special events add liability dimensions

## Commercial Auto

### Typical Exposures
- Delivery vehicles for catering, food delivery, and supply runs
- Hired and non-owned auto exposure when employees use personal vehicles for delivery
- Third-party delivery drivers (DoorDash, Uber Eats) may or may not be covered under restaurant's policy
- Limited fleet exposure for most restaurants—typically 1-3 delivery vehicles
- Catering operations may require box truck or van

## Property

### Typical Equipment and Building Risks
- Commercial kitchen equipment (ovens, fryers, refrigeration, exhaust hoods) is high-value and specialized
- Grease fire is the leading cause of restaurant property claims—hood suppression systems are critical
- Refrigeration breakdown causing food spoilage is a common equipment breakdown claim
- Water damage from plumbing failures in dish stations and restrooms
- Business interruption exposure is high—restaurant closures from fire or health inspection failures
- Lease obligations may require specific property coverage levels

## Regulatory and Safety

### OSHA and Compliance Risks
- OSHA general industry standards (1910) apply—slip protection, hazard communication, PPE
- Health inspection failures can trigger immediate closure and significant revenue loss
- Food safety compliance (FDA Food Code, state health department regulations) is paramount
- Liquor license compliance and responsible service training requirements
- Fire code compliance for commercial kitchen hood suppression systems
- Employee misclassification of tipped workers and the impact on workers comp audits
- Child labor law compliance for restaurants employing minors (hours, equipment restrictions)

## Suggested Producer Questions

Producers should ask restaurant clients these key questions:
1. Do you serve alcohol? What is your food-to-liquor revenue split?
2. What is your annual employee turnover rate and how do you onboard new kitchen staff on safety?
3. When was your kitchen hood suppression system last inspected and serviced?
4. Do you perform any delivery operations—in-house drivers or third-party platforms?
5. What food safety training and certification do your managers hold (ServSafe, state equivalent)?
6. How do you handle customer food allergy requests?
7. What is your annual payroll and how much is tipped employee payroll?
8. Have you had any health inspection failures or critical violations in the past 2 years?
9. Do you have a written slip and fall prevention program (floor mats, non-slip shoes, cleaning schedule)?
10. Do you host special events, live entertainment, or operate a patio/outdoor dining area?
""",
    },
    {
        "title": "Trucking Company Industry Risk Profile",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": None,
        "published_at": datetime(2025, 11, 1, tzinfo=timezone.utc),
        "publisher": "WAYOS Risk Intelligence",
        "raw_text": """# Trucking Company Industry Risk Profile

## Workers Compensation

### Top Injury Types
Despite drivers spending most time behind the wheel, trucking companies generate significant workers comp claims. The most common injury types include:
- Lifting injury and back injury from loading, unloading, and securing freight
- Slip and fall at docks, terminals, fuel stops, and customer delivery locations
- Struck by falling cargo during loading and unloading operations
- Cumulative trauma to back, neck, and shoulders from prolonged seated driving
- Knee and ankle injuries from climbing in and out of cab and trailer
- Repetitive strain from coupling/uncoupling trailers and operating landing gear
- Crush injuries from being caught between vehicles during backing and coupling

### Typical Severity Drivers
- Loading and unloading injuries account for 40% of trucker workers comp claims
- Multi-state operations complicate workers comp jurisdiction and state filing requirements
- Driver turnover exceeding 90% for large carriers means constant influx of less-experienced workers
- Fatigue-related incidents carry higher severity due to impaired reaction times
- Older driver demographics increase claim severity and duration
- Delayed medical reporting when drivers are on the road inflates claim costs

## General Liability

### Common Claims
- Premises liability at terminal and yard locations (slip and fall by visitors, vendors)
- Cargo damage claims and disputes during transportation
- Environmental liability from fuel spills at terminals and during transit
- Contractual liability arising from shipper and broker agreements
- Completed operations exposure for freight brokerage services

### Operational Exposures
- Terminal and warehouse premises liability for owned or leased facilities
- Pollution liability from diesel fuel storage and transportation of hazardous materials
- Contractual risk transfer in shipper agreements often requires specific coverage terms
- Cargo liability varies dramatically by commodity type (general freight vs high-value, hazmat)
- Owner-operator relationships create subcontractor transfer and coverage gap risks

## Commercial Auto

### Typical Exposures
- Commercial auto liability is the largest single insurance cost for trucking companies
- Average commercial auto liability claim exceeds $150,000; nuclear verdicts exceed $10 million
- Distracted driving and driver fatigue are the leading preventable accident causes
- DOT compliance violations (hours of service, vehicle maintenance) correlate with accident frequency
- Tractor-trailer combinations create higher severity in collisions due to vehicle weight
- Hired and non-owned auto exposure from owner-operators and leased equipment
- Motor cargo coverage protects against freight damage during transit
- Trailer interchange agreements need specific endorsements
- Non-owned trailer physical damage is commonly overlooked
- Young fleet (newer vehicles) may reduce maintenance-related accidents but higher replacement costs

### Nuclear Verdict Exposure
- Jury awards exceeding $10 million in trucking cases have increased 300% in the last decade
- Reptile theory litigation targets safety culture and management decisions
- Dash cameras (front and driver-facing) are the strongest defense against fraudulent and inflated claims
- Umbrella/excess limits of $5-10 million are increasingly the minimum standard
- Some excess carriers are pulling back from the trucking market entirely

## Property

### Typical Equipment and Building Risks
- Terminal and warehouse property at owned or leased locations
- Fleet maintenance shop fire exposure from fuel, solvents, and welding
- Business interruption if terminal operations are disrupted
- Inland marine for trailers, containers, and specialized equipment
- Cargo storage exposure at cross-dock and warehouse facilities
- Cold storage and refrigeration breakdown for temperature-controlled carriers

## Regulatory and Safety

### OSHA and Compliance Risks
- FMCSA CSA (Compliance, Safety, Accountability) scores directly impact insurance pricing and carrier selection
- ELD (Electronic Logging Device) mandate compliance is now table stakes
- Hours of service violations remain a top citation category
- Drug and alcohol testing program (DOT requirements) must be strictly maintained
- Annual driver qualification file maintenance is a federal requirement
- FMCSA Safety Measurement System BASICs (Behavior Analysis and Safety Improvement Categories)
- Vehicle maintenance and inspection compliance (DVIR, annual DOT inspections)
- Hazardous materials endorsement and training requirements for applicable carriers
- Interstate vs intrastate operating authority distinctions affect regulatory requirements

## Suggested Producer Questions

Producers should ask trucking company clients these key questions:
1. What is your FMCSA CSA score and which BASICs are you flagged on?
2. What is your annual driver turnover rate and what retention programs do you have?
3. What types of freight do you haul and do you transport any hazardous materials?
4. Do you use owner-operators? What percentage of your fleet is owner-op vs company drivers?
5. Do you have dash cameras installed fleet-wide (front and driver-facing)?
6. What are your current commercial auto liability limits and umbrella limits?
7. How do you screen new drivers—MVR frequency, road test, background check?
8. What is your DOT inspection out-of-service rate?
9. Do you operate interstate or intrastate, and in how many states?
10. What is your fleet size, average vehicle age, and preventive maintenance program?
""",
    },
    # ── Municipal / Public Entity Risk Profile ───────────────────────
    {
        "title": "Municipal Government Risk Profile: Public Works Department",
        "source_type": "report",
        "authority_level": "carrier",
        "jurisdiction_state": "nc",
        "published_at": datetime(2025, 12, 1, tzinfo=timezone.utc),
        "publisher": "WAYOS Risk Intelligence",
        "raw_text": """# Municipal Government Risk Profile: Public Works Department

## Entity Classification

This risk profile covers public entity exposures for a municipality, specifically the public works department. Municipal governments face a unique liability environment shaped by governmental immunity statutes, public interaction, and infrastructure maintenance obligations.

## Workers Compensation

### Top Injury Types
Municipal public works departments generate significant workers comp claims across diverse operations:
- Lifting injury and back injury from manual handling of materials, equipment, and infrastructure components
- Struck by falling debris or objects during road maintenance and construction operations
- Slip and fall on wet, icy, or uneven surfaces during outdoor operations year-round
- Vehicle accidents involving municipal fleet trucks, dump trucks, and heavy equipment
- Heat illness and heat exhaustion during summer road crew and outdoor maintenance work
- Chemical exposure from water treatment chemicals, sewer gases, and road materials (asphalt, solvents)
- Trench collapse and confined space incidents during water/sewer line repair
- Repetitive strain from prolonged equipment operation and manual labor

### Typical Severity Drivers
- Heavy equipment operations (backhoe, excavator, front-end loader) create high-severity incidents
- Roadside work exposes crews to struck-by vehicle hazards from passing traffic
- Confined space entry in sewer manholes and water vaults carries fatality risk
- Seasonal payroll fluctuations bring temporary workers with less training during peak seasons
- Aging workforce in public sector increases claim duration and severity

## General Liability

### Common Claims
- Road maintenance liability: pothole claims, road defect claims, and failure-to-maintain allegations
- Sewer backup claims from blocked or failing municipal sewer systems causing property damage
- Slip and fall on public sidewalks, parking lots, and municipal buildings
- Property damage from utility work (water main breaks, sewer line repairs)
- Public event liability from city-sponsored festivals, parades, and community events
- Playground injury claims at municipal parks from equipment failures or inadequate maintenance
- Tree limb failure on public property causing injury or property damage

### Operational Exposures
- Governmental immunity varies by state — North Carolina Tort Claims Act caps damages for state entities
- Notice requirements for road defect claims create documentation obligations
- Third-party contractor oversight during capital projects creates vicarious liability
- Volunteer liability for community service workers, volunteer firefighters, and event volunteers
- Zoning decisions and planning approvals can generate inverse condemnation or takings claims

## Commercial Auto / Municipal Fleet

### Typical Exposures
- Municipal auto fleet includes dump trucks, utility trucks, backhoes, front-end loaders, and passenger vehicles
- Fleet accidents involving municipal vehicles are a top liability exposure
- Emergency vehicle response creates heightened collision risk (police, fire, EMS)
- Hired and non-owned auto exposure when employees use personal vehicles for municipal business
- Snow plow operations create collision and property damage exposure during winter
- Sanitation trucks (garbage collection) operate in residential areas with pedestrian exposure

## Property

### Typical Equipment and Building Risks
- Public entity property includes government buildings, fire stations, police stations, libraries, recreation centers
- Infrastructure property: roads, bridges, water/sewer systems, stormwater infrastructure
- Equipment breakdown for water treatment plants, wastewater treatment plants, and pumping stations
- Flood and weather damage to public infrastructure
- Vandalism and arson at public buildings and facilities
- Business interruption for critical infrastructure (water treatment, wastewater) has public health implications

## Regulatory and Safety

### OSHA and Compliance Risks
- OSHA general industry (1910) and construction (1926) standards apply to municipal workers
- Confined space entry permits required for manholes, vaults, and tanks (29 CFR 1910.146)
- Trenching and excavation safety (29 CFR 1926 Subpart P) for water/sewer work
- Hazard communication for water treatment chemicals, sewer gases, and road materials
- Traffic control and work zone safety (MUTCD standards) for road crew operations
- CDL requirements for municipal employees operating heavy equipment and commercial vehicles
- NC OSHA (administered by NC DOL) conducts inspections of public sector workplaces
- Environmental compliance for water treatment discharge and stormwater permits

## Public Entity Specific Exposures

### Civil Rights and Law Enforcement
- Police liability and excessive force claims under Section 1983 create significant exposure
- Civil rights claims against law enforcement officers and the municipality
- Public officials liability for elected officials and appointed board members
- Employment practices claims (discrimination, harassment, wrongful termination) in the public sector

### Cyber and Records
- Cyber records breach exposure from ransomware attacks targeting municipal IT systems
- Public records management obligations under state open records laws
- HIPAA exposure for municipal EMS and health departments

### Grant and Procurement
- Grant compliance risk for federal and state grants funding municipal projects
- Procurement disputes from competitive bidding processes and contract awards
- Environmental liability from historical contamination at municipal sites

## Suggested Producer Questions

Producers should ask municipal government clients these key questions:
1. What departments does the municipality operate and how many total employees across all departments?
2. What is your current governmental immunity status and tort claims cap under state law?
3. Does the municipality operate a police department? What is the use-of-force policy and training program?
4. How many vehicles are in the municipal fleet and what types (dump trucks, police cruisers, fire apparatus)?
5. What water and sewer infrastructure does the municipality own and maintain?
6. How often are road maintenance inspections performed and documented for pothole and defect liability?
7. Does the municipality sponsor public events, operate parks with playgrounds, or manage recreation facilities?
8. What is the IT security posture — has a cybersecurity assessment been conducted for ransomware risk?
9. What volunteer programs does the municipality operate (volunteer fire, community service)?
10. What is the municipality's current experience modification rate for workers comp?
11. How are confined space entries managed for sewer and water vault work?
12. What federal or state grants is the municipality managing and what are the compliance requirements?
""",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Source).count()
        if existing > 0:
            print(f"Database already has {existing} sources. Skipping seed.")
            return

        print("Seeding demo data...")
        for data in SAMPLE_SOURCES:
            data = dict(data)  # copy to avoid mutating the original
            raw_text = data.pop("raw_text")
            source = ingest_raw_text(db=db, raw_text=raw_text, **data)
            print(f"  Created source: {source.title} ({source.id})")

            # Parse
            source.raw_text = clean_text(source.raw_text)
            source.status = SourceStatus.PARSED
            tag_source(db, source)
            db.commit()
            print(f"    Parsed and tagged")

            # Chunk
            chunks_data = chunk_text(
                source.raw_text,
                source_jurisdiction=source.jurisdiction,
                source_jurisdiction_state=source.jurisdiction_state,
                authority_score=float(source.authority_score),
                freshness_score=float(source.freshness_score),
            )
            for cd in chunks_data:
                chunk = SourceChunk(
                    source_id=source.id,
                    chunk_index=cd["chunk_index"],
                    heading=cd.get("heading"),
                    text_content=cd["text_content"],
                    token_count=cd["token_count"],
                    char_count=cd["char_count"],
                    chunk_hash=cd["chunk_hash"],
                    jurisdiction=cd.get("jurisdiction"),
                    jurisdiction_state=cd.get("jurisdiction_state"),
                    authority_score=cd["authority_score"],
                    freshness_score=cd["freshness_score"],
                )
                db.add(chunk)
                db.flush()
                tag_chunk(db, chunk)

            source.status = SourceStatus.CHUNKED
            db.commit()
            print(f"    Created {len(chunks_data)} chunks")

            # Embed (only if API key is available)
            try:
                from app.services.embeddings import embed_chunks
                chunks = db.query(SourceChunk).filter(SourceChunk.source_id == source.id).all()
                count = embed_chunks(db, chunks)
                if count > 0:
                    source.status = SourceStatus.READY
                    db.commit()
                    print(f"    Embedded {count} chunks - source is READY")
                else:
                    # Mark as ready anyway for demo purposes (tag-based retrieval will work)
                    source.status = SourceStatus.READY
                    db.commit()
                    print(f"    No API key for embeddings - marked READY for tag-based retrieval")
            except Exception as e:
                source.status = SourceStatus.READY
                db.commit()
                print(f"    Embedding skipped ({e}) - marked READY for tag-based retrieval")

        print(f"\nSeed complete. {len(SAMPLE_SOURCES)} sources created.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
