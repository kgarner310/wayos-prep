TIER_3_INDUSTRIES = [
    {
        "industry_name": "Poultry Farming / Processing",
        "synonyms": ["Chicken Farm", "Broiler Operation", "Poultry Plant", "Egg Production Facility"],
        "top_workers_comp_claims": [
            "Repetitive motion injuries from deboning and processing line work",
            "Lacerations and amputations from mechanical processing equipment",
            "Respiratory illness from dust, ammonia, and dander exposure in enclosed houses",
            "Slips and falls on wet processing floors"
        ],
        "commercial_auto_claims": [
            "Live haul truck rollovers on rural roads during transport to processing plants",
            "Collisions involving refrigerated delivery trucks on tight loading dock approaches",
            "Feed delivery truck accidents on unpaved farm roads"
        ],
        "general_liability_exposures": [
            "Environmental contamination from waste lagoons and litter runoff",
            "Foodborne illness claims tied to salmonella or campylobacter contamination",
            "Odor and nuisance complaints from neighboring properties",
            "Contract grower disputes over animal welfare standards"
        ],
        "conversation_prompts": [
            "Are you a contract grower for an integrator or an independent operation?",
            "How many houses do you operate and what is your flock capacity per cycle?",
            "Do you handle processing on-site or only live bird production?",
            "What waste management systems are in place for litter and wastewater?"
        ],
        "regional_risk_notes": "The Southeast U.S. — particularly Arkansas, Georgia, Alabama, and Mississippi — dominates U.S. poultry production. Operations face heightened scrutiny on environmental runoff into waterways and seasonal heat stress risks for both workers and flocks."
    },
    {
        "industry_name": "Cattle Ranching",
        "synonyms": ["Beef Cattle Operation", "Cow-Calf Operation", "Livestock Ranch", "Cattle Farm"],
        "top_workers_comp_claims": [
            "Crush injuries and fractures from cattle handling in chutes and pens",
            "Kicks, goring, and trampling during sorting and loading operations",
            "Horseback riding injuries sustained during herding activities",
            "Heat-related illness during summer pasture work"
        ],
        "commercial_auto_claims": [
            "Livestock trailer accidents during transport to auction or feedlots",
            "Collisions with animals that escape onto public roadways",
            "Pickup truck accidents on rural highways during fence-line checks"
        ],
        "general_liability_exposures": [
            "Escaped livestock causing vehicle accidents on adjacent roadways",
            "Visitor injuries during ranch tours or agritourism events",
            "Fence line disputes and trespass damage to neighboring crop land",
            "Water contamination from concentrated feeding areas"
        ],
        "conversation_prompts": [
            "What is your herd size and do you run a cow-calf, stocker, or feedlot operation?",
            "Do you offer any agritourism activities such as ranch tours or hunting leases?",
            "How many miles of fencing do you maintain and along how many public roads?",
            "Do employees work on horseback or use ATVs for herding?"
        ],
        "regional_risk_notes": "Southeast cattle operations often run on mixed-use land with timber and hay production, creating overlapping exposures. Hurricane and flood risk to pastureland and livestock is a significant concern in Gulf Coast states."
    },
    {
        "industry_name": "Row Crop Farming",
        "synonyms": ["Cash Crop Operation", "Grain Farm", "Field Crop Agriculture", "Commercial Farming"],
        "top_workers_comp_claims": [
            "Tractor rollovers and PTO entanglement fatalities and amputations",
            "Grain bin engulfment and suffocation during storage operations",
            "Pesticide and herbicide exposure causing chemical burns or systemic illness",
            "Musculoskeletal injuries from prolonged equipment operation"
        ],
        "commercial_auto_claims": [
            "Slow-moving farm equipment struck by vehicles on public roads",
            "Grain truck collisions during harvest season transport to elevators",
            "Hired labor transport van accidents on rural routes"
        ],
        "general_liability_exposures": [
            "Pesticide drift causing damage to neighboring properties or organic farms",
            "Crop dusting overspray claims from aerial application",
            "Environmental liability from fertilizer runoff into waterways",
            "Injuries to seasonal or migrant workers housed on the property"
        ],
        "conversation_prompts": [
            "What crops do you grow and how many acres are in production?",
            "Do you use aerial application services or apply chemicals with your own equipment?",
            "How do you manage seasonal labor — do you use H-2A workers or local crews?",
            "Do you have grain storage on-site and what is the bin capacity?"
        ],
        "regional_risk_notes": "Southeast row crop operations face unique risks from extended growing seasons, high humidity promoting fungal disease, and frequent severe weather events including hurricanes and tornadoes during harvest season."
    },
    {
        "industry_name": "Timber / Logging Operations",
        "synonyms": ["Logging Company", "Timber Harvesting", "Forestry Contractor", "Log Cutting Operation", "Pulpwood Operation"],
        "top_workers_comp_claims": [
            "Struck-by injuries from falling trees, limbs, and rolling logs",
            "Chainsaw lacerations and kickback injuries during felling and bucking",
            "Heavy equipment crush injuries from skidders, feller bunchers, and loaders",
            "Falls from steep terrain and log decks"
        ],
        "commercial_auto_claims": [
            "Loaded log truck rollovers on mountain and rural roads",
            "Unsecured load incidents where logs shift or fall from trailers",
            "Skidder and equipment transport accidents on public highways"
        ],
        "general_liability_exposures": [
            "Property damage to landowner timber stands from harvesting errors",
            "Erosion and stream sedimentation from improper best management practices",
            "Road damage to county and private roads from heavy truck traffic",
            "Damage to underground utilities during site clearing operations"
        ],
        "conversation_prompts": [
            "Are you harvesting on your own land or contracting for private and corporate landowners?",
            "What types of equipment do you operate — mechanized or hand-felling crews?",
            "How many log trucks do you run and what are your primary haul routes?",
            "Do you carry completed operations coverage for reforestation obligations?"
        ],
        "regional_risk_notes": "Logging is consistently one of the most hazardous industries in the U.S. by fatality rate. In the Southeast, year-round harvesting seasons and pine plantation management create sustained exposure, and many operations are small crews with limited safety programs."
    },
    {
        "industry_name": "Sawmills and Wood Products",
        "synonyms": ["Lumber Mill", "Wood Processing Facility", "Sawmill Operation", "Timber Mill"],
        "top_workers_comp_claims": [
            "Amputations and severe lacerations from saw blades, planers, and edgers",
            "Hearing loss from prolonged exposure to high-decibel milling equipment",
            "Struck-by injuries from lumber kickback and material handling",
            "Respiratory disease from chronic wood dust inhalation"
        ],
        "commercial_auto_claims": [
            "Lumber delivery truck accidents during transit to customers",
            "Forklift-to-vehicle collisions in shared yard areas",
            "Log truck incidents during inbound raw material deliveries"
        ],
        "general_liability_exposures": [
            "Product liability for structural lumber that fails to meet grade specifications",
            "Fire and explosion risk from accumulated wood dust and kiln operations",
            "Noise complaints from nearby residential areas",
            "Environmental violations from sawdust, bark, and wastewater discharge"
        ],
        "conversation_prompts": [
            "What is your daily board-foot production capacity and primary product mix?",
            "Do you operate dry kilns and what fire suppression systems are in place?",
            "What dust collection and ventilation systems are installed in the mill?",
            "How do you manage the log yard — is it paved or unpaved and how is traffic controlled?"
        ],
        "regional_risk_notes": "Southeast sawmills benefit from proximity to the largest softwood timber resource in the U.S. but face significant fire risk in dry seasons and OSHA scrutiny on machine guarding and dust explosion prevention."
    },
    {
        "industry_name": "Pulp and Paper Mills",
        "synonyms": ["Paper Manufacturing", "Pulp Mill", "Paper Plant", "Cellulose Processing Facility"],
        "top_workers_comp_claims": [
            "Chemical burns from caustic soda, chlorine dioxide, and bleaching agents",
            "Confined space incidents in digesters, tanks, and recovery boilers",
            "Steam and hot surface burns from high-pressure process equipment",
            "Musculoskeletal injuries from roll handling and paper converting operations"
        ],
        "commercial_auto_claims": [
            "Heavy roll transport truck accidents during finished goods delivery",
            "Chemical tanker incidents during inbound caustic and bleaching agent deliveries",
            "Chip truck collisions on plant access roads"
        ],
        "general_liability_exposures": [
            "Air quality violations from sulfur compound and particulate emissions",
            "Water pollution from effluent discharge into rivers and streams",
            "Odor complaints from kraft pulping processes affecting surrounding communities",
            "Product liability for contaminated or off-spec paper products"
        ],
        "conversation_prompts": [
            "What pulping process do you use — kraft, sulfite, or mechanical?",
            "What is your facility's wastewater treatment capacity and discharge permit status?",
            "How do you manage recovery boiler maintenance and shutdown schedules?",
            "Do you have on-site chemical storage for bleaching agents and what are the volumes?"
        ],
        "regional_risk_notes": "The Southeast is the largest paper-producing region in the U.S., with major operations in Georgia, Alabama, and the Carolinas. These facilities have high environmental compliance costs and significant property values at risk from boiler explosions and fires."
    },
    {
        "industry_name": "Commercial Fishing",
        "synonyms": ["Charter Fishing", "Commercial Shrimping", "Fishing Vessel Operation", "Offshore Fishing"],
        "top_workers_comp_claims": [
            "Drowning and man-overboard incidents in rough seas",
            "Crush injuries from winches, cables, and heavy nets during hauling",
            "Severe lacerations from knives, hooks, and wire rigging",
            "Hypothermia and weather exposure during extended offshore trips"
        ],
        "commercial_auto_claims": [
            "Refrigerated truck accidents transporting catch to processors and markets",
            "Trailer backing incidents at boat ramps and marina loading areas",
            "Vehicle accidents during early morning crew transport to docks"
        ],
        "general_liability_exposures": [
            "Passenger injury claims on charter and for-hire fishing vessels",
            "Fuel spill and pollution liability in harbors and coastal waters",
            "Product liability for contaminated or improperly stored seafood",
            "Dock and pier damage during vessel mooring operations"
        ],
        "conversation_prompts": [
            "Are you a commercial harvester or do you run charter and for-hire trips?",
            "What is your vessel size and how far offshore do you typically operate?",
            "Do you carry Jones Act coverage for crew members?",
            "How do you handle cold chain management from catch to sale?"
        ],
        "regional_risk_notes": "Gulf Coast commercial fishing operations face extreme hurricane exposure and must account for vessel haul-out and layup periods. Jones Act and maritime law create unique liability frameworks that differ significantly from standard workers comp."
    },
    {
        "industry_name": "Aquaculture / Fish Farming",
        "synonyms": ["Fish Hatchery", "Catfish Farm", "Shrimp Farm", "Aquaculture Operation", "Fish Production Facility"],
        "top_workers_comp_claims": [
            "Drowning and near-drowning incidents around ponds and raceways",
            "Electrical shock from aerators, pumps, and submersible equipment",
            "Repetitive strain injuries from net hauling and fish grading",
            "Skin infections and allergic reactions from prolonged water contact"
        ],
        "commercial_auto_claims": [
            "Live fish transport truck accidents and spills during haul to processors",
            "Feed delivery vehicle incidents on levee roads and pond banks",
            "Collisions involving aeration equipment trailers on rural highways"
        ],
        "general_liability_exposures": [
            "Water discharge violations from pond effluent affecting downstream properties",
            "Escaped non-native species creating invasive species liability",
            "Visitor injuries at farm-to-table retail operations on site",
            "Chemical overapplication of therapeutants contaminating adjacent waterways"
        ],
        "conversation_prompts": [
            "What species do you raise and what is your total pond acreage or tank volume?",
            "Do you process on-site or transport live fish to a separate processing plant?",
            "What is your water source and do you hold any discharge permits?",
            "Do you have any direct-to-consumer or agritourism components to your operation?"
        ],
        "regional_risk_notes": "Mississippi Delta catfish farming and Gulf Coast shrimp aquaculture are major Southeast operations. Water rights, disease outbreaks like columnaris, and competition from imported seafood create unique business continuity risks."
    },
    {
        "industry_name": "Hotels and Resorts",
        "synonyms": ["Hospitality Property", "Hotel Management", "Resort Operation", "Lodging Facility", "Inn and Bed and Breakfast"],
        "top_workers_comp_claims": [
            "Housekeeping musculoskeletal injuries from repetitive lifting, bending, and pushing",
            "Slips and falls on wet lobby, kitchen, and pool deck surfaces",
            "Burns and cuts in hotel kitchen and laundry operations",
            "Needle stick and biohazard exposures during room cleaning"
        ],
        "commercial_auto_claims": [
            "Shuttle van and airport transport accidents involving guests",
            "Valet parking damage and collision claims",
            "Maintenance vehicle incidents on resort property roads"
        ],
        "general_liability_exposures": [
            "Guest slip-and-fall injuries in common areas, bathrooms, and pool decks",
            "Swimming pool drowning and diving injury claims",
            "Foodborne illness from on-site restaurant and banquet operations",
            "Premises security failures leading to assault or theft claims"
        ],
        "conversation_prompts": [
            "How many rooms do you operate and do you have on-site food and beverage?",
            "Do you offer shuttle or transportation services for guests?",
            "What recreational amenities do you provide — pool, spa, fitness center, waterfront?",
            "What is your security program — cameras, key card access, on-site personnel?"
        ],
        "regional_risk_notes": "Southeast hotels and resorts face significant hurricane and tropical storm exposure, particularly along the Gulf and Atlantic coasts. Seasonal tourism creates staffing fluctuations that can increase injury rates among temporary workers."
    },
    {
        "industry_name": "Amusement Parks and Attractions",
        "synonyms": ["Theme Park", "Water Park", "Family Entertainment Center", "Tourist Attraction"],
        "top_workers_comp_claims": [
            "Heat-related illness for outdoor ride operators and costumed performers",
            "Musculoskeletal injuries from ride loading, restraint checks, and guest assistance",
            "Slips and falls in water park environments and during cleaning operations",
            "Electrical injuries during ride maintenance and inspection"
        ],
        "commercial_auto_claims": [
            "Tram and parking lot shuttle accidents involving guests",
            "Delivery truck incidents in congested backstage service areas",
            "Go-kart and ride vehicle maintenance transport accidents on property"
        ],
        "general_liability_exposures": [
            "Ride malfunction injuries and mechanical failure claims",
            "Guest injuries from slips, falls, and crowd crush incidents",
            "Drowning and spinal injury claims at water attractions",
            "Food allergy and foodborne illness claims from concession operations"
        ],
        "conversation_prompts": [
            "What types of rides and attractions do you operate and what is your annual attendance?",
            "Who performs ride inspections and what is your maintenance and testing schedule?",
            "Do you have water features and what are your lifeguard staffing ratios?",
            "What is your emergency action plan for severe weather and guest medical events?"
        ],
        "regional_risk_notes": "Southeast amusement parks operate in a long season due to mild winters but face severe thunderstorm and lightning risks requiring robust weather monitoring and evacuation protocols. Florida and the Carolinas have the highest concentration of attractions."
    },
    {
        "industry_name": "Marinas and Boat Storage",
        "synonyms": ["Boat Marina", "Yacht Club", "Boat Yard", "Marine Storage Facility", "Dry Stack Storage"],
        "top_workers_comp_claims": [
            "Crush and pinch injuries during boat launching, hauling, and dry dock operations",
            "Drowning and fall-into-water incidents from docks and seawalls",
            "Back injuries from manual handling of marine equipment and supplies",
            "Electrical shock from shore power connections and underwater lighting"
        ],
        "commercial_auto_claims": [
            "Forklift and travel lift accidents during boat movement in storage yards",
            "Boat trailer backing and launching incidents at public ramps",
            "Customer vehicle damage in congested marina parking areas"
        ],
        "general_liability_exposures": [
            "Fuel spill and pollution liability from on-water fueling operations",
            "Vessel damage during storage, launching, and hauling operations",
            "Dock collapse or failure causing injury or property damage",
            "Slip-and-fall injuries on wet docks, ramps, and gangways"
        ],
        "conversation_prompts": [
            "How many wet slips and dry storage spaces do you operate?",
            "Do you offer fuel sales, boat repair, or haul-out services?",
            "What is your hurricane preparation plan for stored vessels?",
            "Do you require proof of insurance from boat owners using your facility?"
        ],
        "regional_risk_notes": "Southeast marinas face extreme hurricane and storm surge exposure requiring comprehensive vessel haul-out plans. Environmental liability from fuel handling is heavily regulated by state and federal agencies along the Gulf and Atlantic coastlines."
    },
    {
        "industry_name": "Campgrounds and RV Parks",
        "synonyms": ["RV Resort", "Camping Facility", "Outdoor Recreation Park", "KOA Campground"],
        "top_workers_comp_claims": [
            "Tree limb and falling tree injuries during grounds maintenance",
            "Repetitive strain from mowing, trimming, and facility upkeep",
            "Electrical shock from campsite hookup pedestal maintenance",
            "Insect stings, snake bites, and wildlife encounter injuries"
        ],
        "commercial_auto_claims": [
            "Utility cart and maintenance vehicle collisions with guests on park roads",
            "Guest vehicle accidents on narrow internal campground roads",
            "Supply delivery truck damage to low-clearance structures and utilities"
        ],
        "general_liability_exposures": [
            "Tree fall injuries to guests and damage to RVs during storms",
            "Drowning in on-site swimming areas, ponds, or adjacent waterways",
            "Electrical fire and shock from aging campsite power pedestals",
            "Trip-and-fall injuries on uneven terrain, tree roots, and unlit pathways"
        ],
        "conversation_prompts": [
            "How many sites do you operate and do you offer full hookup with electric, water, and sewer?",
            "Do you have recreational amenities like pools, lakes, playgrounds, or trails?",
            "What is your tree maintenance program for hazard limbs and dead trees?",
            "Are your electrical pedestals up to current NEC code and on what inspection cycle?"
        ],
        "regional_risk_notes": "Southeast campgrounds benefit from year-round occupancy in many areas but face severe weather risks including tornadoes, hurricanes, and flash flooding. Tree management is a critical liability concern given the prevalence of pine and hardwood canopy."
    },
    {
        "industry_name": "Golf Courses",
        "synonyms": ["Country Club", "Golf Club", "Golf Resort", "Public Golf Course"],
        "top_workers_comp_claims": [
            "Heat-related illness among groundskeeping and maintenance crews",
            "Pesticide and herbicide exposure during turf chemical application",
            "Mowing equipment injuries including rollovers on slopes and lacerations",
            "Lightning strike injuries during course maintenance and play"
        ],
        "commercial_auto_claims": [
            "Golf cart accidents involving guests on course paths and crossings",
            "Maintenance vehicle collisions on shared cart paths",
            "Beverage cart incidents on steep terrain"
        ],
        "general_liability_exposures": [
            "Errant golf ball injuries to players, spectators, and adjacent property owners",
            "Golf cart accident injuries to guests and members",
            "Chemical runoff from fairway and green treatments into waterways",
            "Slip-and-fall injuries in clubhouse, locker room, and pro shop areas"
        ],
        "conversation_prompts": [
            "Is this a private club, semi-private, or public daily fee operation?",
            "Do you host tournaments and events and what is your peak daily round count?",
            "What is your chemical application program and do you hold any environmental permits?",
            "Do you have food and beverage, banquet, or event facilities on the property?"
        ],
        "regional_risk_notes": "Southeast golf courses operate year-round but face significant turf disease pressure from humidity and heat, driving higher chemical usage and associated environmental liability. Lightning is a leading safety concern during the summer storm season."
    },
    {
        "industry_name": "Hunting and Fishing Outfitters",
        "synonyms": ["Hunting Lodge", "Fishing Guide Service", "Sporting Camp", "Outdoor Outfitter", "Wildlife Guide Service"],
        "top_workers_comp_claims": [
            "Accidental firearm discharge injuries during guided hunts",
            "ATV and UTV rollovers on rough terrain during client transport",
            "Drowning and cold water immersion during guided fishing trips",
            "Animal bites, insect stings, and venomous snake encounters"
        ],
        "commercial_auto_claims": [
            "Truck and trailer accidents transporting boats, ATVs, and hunting gear",
            "Client shuttle vehicle accidents on unpaved lease roads",
            "Boat trailer launch and retrieval incidents at public ramps"
        ],
        "general_liability_exposures": [
            "Client firearm injuries and accidental shooting claims during hunts",
            "Treestand fall injuries on leased hunting properties",
            "Boating accident injuries during guided fishing excursions",
            "Premises liability for lodge, cabin, and camp facilities"
        ],
        "conversation_prompts": [
            "What activities do you guide — hunting, fishing, or both — and in what settings?",
            "Do you own the land and waterways or operate on leased or public property?",
            "Do you require signed waivers and what safety briefings do you provide clients?",
            "Do you provide lodging, meals, or alcohol service as part of your packages?"
        ],
        "regional_risk_notes": "The Southeast has a major hunting and fishing outfitter market driven by deer, waterfowl, turkey, and bass fishing. Many operations span multiple leased properties creating complex premises liability, and alcohol service at lodges adds significant exposure."
    },
    {
        "industry_name": "Oil and Gas Extraction",
        "synonyms": ["Drilling Operation", "Oil Field Services", "Petroleum Extraction", "Upstream Oil and Gas"],
        "top_workers_comp_claims": [
            "Struck-by injuries from pipe, tongs, and rig equipment during drilling",
            "Explosions and burns from well blowouts and hydrocarbon releases",
            "Falls from derricks, platforms, and elevated rig structures",
            "Hydrogen sulfide gas exposure causing respiratory distress and fatalities"
        ],
        "commercial_auto_claims": [
            "Oilfield service truck accidents on rural lease roads and highways",
            "Heavy equipment transport collisions with oversized rig components",
            "Water and frac tank truck rollovers on unpaved well pad access roads"
        ],
        "general_liability_exposures": [
            "Environmental contamination from spills, blowouts, and produced water discharge",
            "Subsurface trespass and mineral rights disputes with adjacent landowners",
            "Groundwater contamination claims from drilling and fracturing operations",
            "Road damage and noise complaints from drilling operations near communities"
        ],
        "conversation_prompts": [
            "Are you an operator, contractor, or service company and what is your role on the well?",
            "How many active wells do you operate and in what formations?",
            "What is your environmental compliance program for spill prevention and response?",
            "Do you carry control-of-well coverage and at what limits?"
        ],
        "regional_risk_notes": "Gulf Coast oil and gas operations face hurricane-related production shutdowns and offshore platform evacuation risks. Subsidence and saltwater intrusion in Louisiana and Texas coastal areas create additional long-tail environmental liabilities."
    },
    {
        "industry_name": "Natural Gas Pipeline Operations",
        "synonyms": ["Gas Pipeline Company", "Pipeline Transmission", "Midstream Gas Operations", "Gas Distribution"],
        "top_workers_comp_claims": [
            "Explosion and burn injuries from pipeline ruptures and gas releases",
            "Trench collapse and excavation cave-in injuries during construction",
            "Confined space asphyxiation during pipeline inspection and maintenance",
            "Musculoskeletal injuries from manual pipe handling and welding positions"
        ],
        "commercial_auto_claims": [
            "Pipeline patrol vehicle accidents on highway and right-of-way roads",
            "Heavy equipment transport collisions during construction and repair projects",
            "Utility locate crew vehicle accidents in urban and suburban areas"
        ],
        "general_liability_exposures": [
            "Explosion and fire damage to third-party properties along the pipeline route",
            "Right-of-way encroachment disputes with landowners",
            "Environmental contamination from condensate spills and compressor station leaks",
            "Third-party excavation damage leading to gas release incidents"
        ],
        "conversation_prompts": [
            "How many miles of pipeline do you operate and at what pressures — transmission or distribution?",
            "What is your integrity management program and inspection frequency?",
            "Do you perform your own construction and maintenance or use third-party contractors?",
            "What is your emergency response plan for line ruptures and uncontrolled releases?"
        ],
        "regional_risk_notes": "Southeast pipeline operations must contend with hurricane and flood-related ground movement that threatens pipeline integrity. The rapid expansion of natural gas infrastructure in the region has increased regulatory scrutiny and third-party damage incidents."
    },
    {
        "industry_name": "Solar Farm Installation",
        "synonyms": ["Solar Energy Contractor", "Photovoltaic Installer", "Solar Panel Farm", "Solar EPC Contractor"],
        "top_workers_comp_claims": [
            "Electrical shock and arc flash burns during panel wiring and inverter connection",
            "Falls from rooftop and elevated racking systems during installation",
            "Heat-related illness from prolonged outdoor work on exposed solar fields",
            "Musculoskeletal injuries from repetitive panel lifting and mounting"
        ],
        "commercial_auto_claims": [
            "Truck accidents transporting panels, racking, and transformers to remote sites",
            "Crew van and pickup collisions during multi-site daily travel",
            "Equipment trailer incidents on rural roads accessing solar farm locations"
        ],
        "general_liability_exposures": [
            "Property damage to roofing systems during rooftop installations",
            "Glare and reflection complaints from neighboring properties and airports",
            "Completed operations defects causing fire or electrical failure post-installation",
            "Environmental disturbance claims from utility-scale site clearing and grading"
        ],
        "conversation_prompts": [
            "Do you focus on residential, commercial rooftop, or utility-scale ground mount installations?",
            "What is your annual megawatt installation capacity and typical project size?",
            "Do you self-perform electrical work or subcontract to licensed electricians?",
            "What post-installation warranty and maintenance obligations do you carry?"
        ],
        "regional_risk_notes": "The Southeast is experiencing rapid solar growth, especially in North Carolina, Florida, and Georgia. Hurricane and hail damage to installed panels is a major property risk, and the fast-growing workforce creates experience gap safety concerns."
    },
    {
        "industry_name": "Wind Energy Operations",
        "synonyms": ["Wind Farm", "Wind Turbine Operation", "Wind Power Generation", "Wind Energy Maintenance"],
        "top_workers_comp_claims": [
            "Falls from turbine towers and nacelles during maintenance at extreme heights",
            "Confined space and rescue difficulties inside tower and nacelle structures",
            "Electrical shock from generator, transformer, and collection system work",
            "Musculoskeletal injuries from climbing and working in awkward nacelle positions"
        ],
        "commercial_auto_claims": [
            "Service truck accidents on wind farm access roads in remote locations",
            "Oversized blade and tower transport collisions on public highways",
            "Crane mobilization accidents during major component replacements"
        ],
        "general_liability_exposures": [
            "Blade throw and tower collapse causing property damage or injury",
            "Ice throw from turbine blades in winter conditions striking nearby property",
            "Noise and shadow flicker complaints from neighboring landowners",
            "Bird and bat mortality claims from environmental advocacy groups"
        ],
        "conversation_prompts": [
            "How many turbines do you operate and what is the nameplate capacity of the farm?",
            "Do you self-perform maintenance or contract with the turbine OEM?",
            "What is your emergency rescue plan for stranded workers at nacelle height?",
            "Do you have any FAA lighting or aviation-related compliance requirements?"
        ],
        "regional_risk_notes": "Offshore wind development is emerging along the Southeast Atlantic coast, introducing marine construction and operational risks. Onshore wind in the region is limited but growing in the western portions of the Gulf states, where tornado and severe thunderstorm exposure is significant."
    },
    {
        "industry_name": "Electric Utility Companies",
        "synonyms": ["Power Company", "Electric Cooperative", "Energy Utility", "Electric Distribution Company"],
        "top_workers_comp_claims": [
            "Electrocution and arc flash burns from high-voltage line and substation work",
            "Falls from utility poles, bucket trucks, and transmission towers",
            "Vehicle accidents during storm restoration with fatigued lineworkers",
            "Struck-by injuries from falling conductors, poles, and cross-arms"
        ],
        "commercial_auto_claims": [
            "Bucket truck and line truck accidents during emergency storm response",
            "Rear-end collisions at roadside work zones during line repair",
            "Crew transport vehicle accidents during long-distance mutual aid deployments"
        ],
        "general_liability_exposures": [
            "Wildfire ignition from downed power lines and equipment failure",
            "Power surge damage to customer property from switching and restoration errors",
            "Electromagnetic field exposure claims from transmission line proximity",
            "Tree trimming damage to customer property during right-of-way maintenance"
        ],
        "conversation_prompts": [
            "Are you an investor-owned utility, cooperative, or municipal provider?",
            "How many miles of transmission and distribution line do you maintain?",
            "What is your vegetation management program and budget for right-of-way clearing?",
            "What is your mutual aid agreement participation for hurricane and storm restoration?"
        ],
        "regional_risk_notes": "Southeast utilities face among the highest storm restoration costs in the nation due to frequent hurricanes, ice storms, and severe thunderstorms. Wildfire liability from line contact is an emerging concern as drought patterns shift in the region."
    },
    {
        "industry_name": "Tobacco Farming",
        "synonyms": ["Tobacco Grower", "Tobacco Plantation", "Tobacco Production", "Leaf Tobacco Operation"],
        "top_workers_comp_claims": [
            "Green tobacco sickness from dermal nicotine absorption during wet leaf handling",
            "Heat-related illness during summer harvest and curing barn work",
            "Musculoskeletal injuries from stooping, lifting, and hanging tobacco in barns",
            "Pesticide exposure from sucker control and pest management applications"
        ],
        "commercial_auto_claims": [
            "Farm truck accidents transporting cured leaf to auction or buying stations",
            "Tractor-trailer collisions with farm equipment on public roads during harvest",
            "Crew transport incidents carrying seasonal workers to fields"
        ],
        "general_liability_exposures": [
            "Barn fire claims from curing operations using gas or wood heat",
            "Chemical drift from pesticide applications affecting neighboring properties",
            "Seasonal worker housing liability for on-farm labor camps",
            "Environmental claims from heavy fertilizer and chemical use"
        ],
        "conversation_prompts": [
            "What type of tobacco do you grow — flue-cured, burley, or dark?",
            "How many acres are in production and what is your curing infrastructure?",
            "Do you contract directly with manufacturers or sell at auction?",
            "How do you manage harvest labor and do you provide worker housing?"
        ],
        "regional_risk_notes": "North Carolina, Kentucky, Virginia, and Georgia remain the core tobacco-producing states. Curing barn fires are a significant property exposure, and green tobacco sickness is an occupational hazard unique to this crop that many carriers underwrite carefully."
    },
    {
        "industry_name": "Cotton Farming",
        "synonyms": ["Cotton Plantation", "Cotton Grower", "Cotton Production", "Cotton Gin Operation"],
        "top_workers_comp_claims": [
            "Cotton picker and module builder mechanical entanglement injuries",
            "Pesticide and defoliant exposure during aerial and ground application",
            "Heat exhaustion during late-summer field scouting and harvest operations",
            "Hearing loss from prolonged cotton gin equipment exposure"
        ],
        "commercial_auto_claims": [
            "Module truck and boll buggy accidents during harvest transport to gins",
            "Cotton trailer collisions on rural highways and farm-to-market roads",
            "Slow-moving harvester struck by traffic on public roads"
        ],
        "general_liability_exposures": [
            "Cotton gin fire and dust explosion causing property and bodily injury",
            "Aerial defoliant drift damaging neighboring crops and property",
            "Environmental liability from pesticide and fertilizer runoff",
            "Product contamination claims for foreign matter in cotton bales"
        ],
        "conversation_prompts": [
            "How many acres do you farm and do you operate your own gin?",
            "Do you use aerial applicators for defoliation and pest management?",
            "What is your fire prevention program at the gin — spark detection and suppression?",
            "Are you enrolled in federal crop insurance programs?"
        ],
        "regional_risk_notes": "The Southeast cotton belt spanning Georgia, Alabama, Mississippi, and the Carolinas faces volatile weather risk during the critical fall harvest window. Cotton gin fires are a frequent and costly loss, and dust explosion prevention is a key underwriting consideration."
    },
    {
        "industry_name": "Peanut and Soybean Farming",
        "synonyms": ["Peanut Grower", "Soybean Producer", "Legume Farming", "Oilseed Farm Operation"],
        "top_workers_comp_claims": [
            "Tractor and combine entanglement injuries during planting and harvest",
            "Grain bin and storage facility engulfment during soybean handling",
            "Pesticide and fungicide exposure during growing season applications",
            "Heat-related illness during summer cultivation and drying operations"
        ],
        "commercial_auto_claims": [
            "Peanut wagon and grain truck accidents during harvest transport to buying points",
            "Farm equipment slow-speed collisions on shared rural roads",
            "Bulk transport incidents during delivery to processing facilities"
        ],
        "general_liability_exposures": [
            "Peanut allergen contamination claims in farm-to-consumer direct sales",
            "Storage facility fire from spontaneous combustion in improperly dried crops",
            "Chemical drift from herbicide application affecting neighboring fields",
            "Aflatoxin contamination liability in stored peanut inventory"
        ],
        "conversation_prompts": [
            "What is your primary crop mix and total acreage under cultivation?",
            "Do you have on-farm drying and storage capacity for your harvest?",
            "Do you sell into the direct food market or through commodity channels?",
            "What irrigation systems do you use and are they center pivot or drip?"
        ],
        "regional_risk_notes": "Georgia and Alabama are the leading peanut-producing states, while the Mississippi Delta and Carolinas are major soybean producers. Aflatoxin risk in peanuts is elevated in hot, dry Southeast growing conditions and is a key quality and liability concern."
    },
    {
        "industry_name": "Nurseries and Greenhouses",
        "synonyms": ["Plant Nursery", "Garden Center", "Greenhouse Operation", "Horticulture Business", "Wholesale Grower"],
        "top_workers_comp_claims": [
            "Musculoskeletal injuries from repetitive bending, lifting, and carrying heavy pots",
            "Pesticide and chemical exposure during greenhouse fumigation and spraying",
            "Heat-related illness in greenhouse environments with limited ventilation",
            "Lacerations from pruning tools, broken pots, and greenhouse glass"
        ],
        "commercial_auto_claims": [
            "Delivery truck accidents transporting nursery stock to retailers and job sites",
            "Forklift-to-vehicle collisions in loading and staging areas",
            "Trailer rollovers from top-heavy plant loads on uneven roads"
        ],
        "general_liability_exposures": [
            "Customer slip-and-fall injuries in retail garden center areas",
            "Invasive species or disease introduction through contaminated plant stock",
            "Chemical overspray affecting neighboring residential or agricultural properties",
            "Structural collapse of greenhouse or shade structures from wind or snow load"
        ],
        "conversation_prompts": [
            "Are you a wholesale grower, retail garden center, or both?",
            "What is your total square footage under glass or poly and how many acres of field production?",
            "Do you have a retail component with public foot traffic on the property?",
            "What heating systems do you use in your greenhouses and what is your annual fuel cost?"
        ],
        "regional_risk_notes": "Southeast nurseries benefit from a long growing season but face high wind and hail risk to greenhouse structures. Florida and the Carolinas are major production centers where citrus canker and other quarantine pests create significant business interruption exposure."
    },
    {
        "industry_name": "Horse Farms and Equestrian Centers",
        "synonyms": ["Equestrian Facility", "Horse Stable", "Riding Academy", "Equine Operation", "Horse Boarding Facility"],
        "top_workers_comp_claims": [
            "Kick, bite, and trampling injuries during grooming, feeding, and turnout",
            "Rider falls during training, breaking, and exercise activities",
            "Back and shoulder injuries from hay bale handling and stall mucking",
            "Head and spinal injuries from being thrown or struck by horses"
        ],
        "commercial_auto_claims": [
            "Horse trailer accidents and rollovers during transport to shows and veterinary clinics",
            "Truck-trailer jackknife incidents on wet or curving roads",
            "Vehicle damage from horses breaking loose in trailer and striking walls"
        ],
        "general_liability_exposures": [
            "Rider injury claims during lessons, trail rides, and public events",
            "Escaped horse causing vehicle accidents on adjacent roads",
            "Care, custody, and control liability for boarded horses that are injured or become ill",
            "Spectator injuries at shows, competitions, and farm open house events"
        ],
        "conversation_prompts": [
            "What is your primary operation — boarding, breeding, training, or lessons?",
            "How many horses are on the property and how many are client-owned boarders?",
            "Do you offer public riding lessons or trail rides and do you use liability waivers?",
            "What is the value of your most valuable horse and do you carry mortality coverage?"
        ],
        "regional_risk_notes": "Kentucky, Virginia, and the Carolinas have significant equestrian industries. Many Southeast states have equine activity liability statutes that provide limited protection, but litigation from serious rider injuries remains common and can produce high-severity claims."
    },
    {
        "industry_name": "Craft Breweries and Distilleries",
        "synonyms": ["Microbrewery", "Craft Distillery", "Brewpub", "Small Batch Spirits Producer", "Taproom Operation"],
        "top_workers_comp_claims": [
            "Burns and scalds from hot wort, steam, and boiling water during brewing",
            "Slips and falls on wet brewery floors from spills and cleaning operations",
            "Struck-by injuries from kegs, barrels, and heavy grain bags during handling",
            "Chemical burns from caustic cleaning agents used in tank and line sanitation"
        ],
        "commercial_auto_claims": [
            "Delivery van and truck accidents during self-distribution runs",
            "Keg delivery incidents including hand truck injuries at customer locations",
            "Refrigerated truck collisions during time-sensitive fresh product deliveries"
        ],
        "general_liability_exposures": [
            "Liquor liability and dram shop exposure from taproom and tasting room service",
            "CO2 and nitrogen gas asphyxiation risk in poorly ventilated fermentation areas",
            "Product contamination and recall liability for packaged beverages",
            "Grain dust explosion and fire risk in malt storage and milling areas"
        ],
        "conversation_prompts": [
            "What is your annual production volume in barrels and do you self-distribute?",
            "Do you operate a taproom or tasting room with on-premises consumption?",
            "What is your CO2 monitoring and ventilation system in the fermentation area?",
            "Do you hold the appropriate federal and state alcohol production and distribution permits?"
        ],
        "regional_risk_notes": "The Southeast craft beverage industry has grown rapidly, with North Carolina, Virginia, and Tennessee leading in brewery counts. Evolving state alcohol distribution laws create compliance complexity, and taproom operations add significant liquor liability exposure."
    },
]
