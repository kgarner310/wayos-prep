"""Seed risk theme graph and load producer questions into DB.

Run: python seed_graph.py
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.models import RiskTheme, RiskThemeEdge, ProducerQuestion


# --- Graph Nodes ---
# node_type: industry | risk_theme | coverage | department | entity_type
#             | public_entity_type | question_category | account_trait

GRAPH_NODES = [
    # Industries (private scope)
    {"name": "roofing", "node_type": "industry", "display_label": "Roofing Contractor", "entity_scope": "private"},
    {"name": "trucking", "node_type": "industry", "display_label": "Trucking Company", "entity_scope": "private"},
    {"name": "manufacturing", "node_type": "industry", "display_label": "Manufacturing", "entity_scope": "private"},
    {"name": "restaurant", "node_type": "industry", "display_label": "Restaurant", "entity_scope": "private"},
    {"name": "landscaping", "node_type": "industry", "display_label": "Landscaping Contractor", "entity_scope": "private"},
    {"name": "hvac", "node_type": "industry", "display_label": "HVAC Contractor", "entity_scope": "private"},

    # Entity types
    {"name": "private_business", "node_type": "entity_type", "display_label": "Private Business", "entity_scope": "private"},
    {"name": "public_entity", "node_type": "entity_type", "display_label": "Public Entity", "entity_scope": "public"},

    # Public entity subtypes
    {"name": "municipality", "node_type": "public_entity_type", "display_label": "Municipality", "entity_scope": "public"},
    {"name": "county", "node_type": "public_entity_type", "display_label": "County", "entity_scope": "public"},
    {"name": "school_system", "node_type": "public_entity_type", "display_label": "School System", "entity_scope": "public"},
    {"name": "fire_district", "node_type": "public_entity_type", "display_label": "Fire District", "entity_scope": "public"},
    {"name": "utility_authority", "node_type": "public_entity_type", "display_label": "Utility Authority", "entity_scope": "public"},

    # Departments (public scope)
    {"name": "law_enforcement", "node_type": "department", "display_label": "Law Enforcement", "entity_scope": "public"},
    {"name": "fire_department", "node_type": "department", "display_label": "Fire Department", "entity_scope": "public"},
    {"name": "public_works", "node_type": "department", "display_label": "Public Works", "entity_scope": "public"},
    {"name": "utilities", "node_type": "department", "display_label": "Utilities", "entity_scope": "public"},
    {"name": "parks_recreation", "node_type": "department", "display_label": "Parks & Recreation", "entity_scope": "public"},
    {"name": "administration", "node_type": "department", "display_label": "Administration", "entity_scope": "public"},
    {"name": "sanitation", "node_type": "department", "display_label": "Sanitation", "entity_scope": "public"},
    {"name": "street_maintenance", "node_type": "department", "display_label": "Street Maintenance", "entity_scope": "public"},
    {"name": "fleet_services", "node_type": "department", "display_label": "Fleet Services", "entity_scope": "public"},
    {"name": "water_treatment", "node_type": "department", "display_label": "Water Treatment", "entity_scope": "public"},

    # Private industry risk themes
    {"name": "falls_from_height", "node_type": "risk_theme", "display_label": "Falls from Height", "entity_scope": "private"},
    {"name": "fleet_accidents", "node_type": "risk_theme", "display_label": "Fleet/Vehicle Accidents", "entity_scope": "both"},
    {"name": "driver_turnover", "node_type": "risk_theme", "display_label": "Driver Turnover", "entity_scope": "private"},
    {"name": "subcontractor_transfer", "node_type": "risk_theme", "display_label": "Subcontractor Risk Transfer", "entity_scope": "private"},
    {"name": "certificate_tracking", "node_type": "risk_theme", "display_label": "Certificate Tracking Gaps", "entity_scope": "private"},
    {"name": "slip_and_fall", "node_type": "risk_theme", "display_label": "Slip and Fall", "entity_scope": "both"},
    {"name": "machine_guarding", "node_type": "risk_theme", "display_label": "Machine Guarding", "entity_scope": "private"},
    {"name": "combustible_dust", "node_type": "risk_theme", "display_label": "Combustible Dust", "entity_scope": "private"},
    {"name": "burns_and_scalds", "node_type": "risk_theme", "display_label": "Burns and Scalds", "entity_scope": "both"},
    {"name": "heat_illness", "node_type": "risk_theme", "display_label": "Heat Illness Exposure", "entity_scope": "both"},
    {"name": "struck_by_object", "node_type": "risk_theme", "display_label": "Struck-By Object", "entity_scope": "both"},
    {"name": "food_contamination", "node_type": "risk_theme", "display_label": "Food Contamination", "entity_scope": "private"},
    {"name": "chemical_exposure", "node_type": "risk_theme", "display_label": "Chemical Exposure", "entity_scope": "both"},
    {"name": "lifting_ergonomic", "node_type": "risk_theme", "display_label": "Lifting/Ergonomic Injuries", "entity_scope": "both"},
    {"name": "improper_classification", "node_type": "risk_theme", "display_label": "Improper Classification", "entity_scope": "private"},
    {"name": "hired_non_owned_auto", "node_type": "risk_theme", "display_label": "Hired/Non-Owned Auto", "entity_scope": "private"},
    {"name": "compliance_complexity", "node_type": "risk_theme", "display_label": "Regulatory Compliance Complexity", "entity_scope": "both"},

    # Public entity risk themes
    {"name": "police_liability", "node_type": "risk_theme", "display_label": "Police Liability", "entity_scope": "public"},
    {"name": "civil_rights_claims", "node_type": "risk_theme", "display_label": "Civil Rights Claims (Section 1983)", "entity_scope": "public"},
    {"name": "excessive_force", "node_type": "risk_theme", "display_label": "Excessive Force", "entity_scope": "public"},
    {"name": "public_officials_liability", "node_type": "risk_theme", "display_label": "Public Officials Liability", "entity_scope": "public"},
    {"name": "zoning_decisions", "node_type": "risk_theme", "display_label": "Zoning/Land Use Decisions", "entity_scope": "public"},
    {"name": "road_maintenance_liability", "node_type": "risk_theme", "display_label": "Road Maintenance Liability", "entity_scope": "public"},
    {"name": "playground_injury", "node_type": "risk_theme", "display_label": "Playground Injury Exposure", "entity_scope": "public"},
    {"name": "public_event_liability", "node_type": "risk_theme", "display_label": "Public Event Liability", "entity_scope": "public"},
    {"name": "sewer_backup_claims", "node_type": "risk_theme", "display_label": "Sewer Backup Claims", "entity_scope": "public"},
    {"name": "water_quality_claims", "node_type": "risk_theme", "display_label": "Water Quality Claims", "entity_scope": "public"},
    {"name": "fleet_liability", "node_type": "risk_theme", "display_label": "Municipal Fleet Liability", "entity_scope": "public"},
    {"name": "volunteer_liability", "node_type": "risk_theme", "display_label": "Volunteer Liability", "entity_scope": "public"},
    {"name": "cyber_records_breach", "node_type": "risk_theme", "display_label": "Cyber/Records Breach", "entity_scope": "public"},
    {"name": "grant_compliance", "node_type": "risk_theme", "display_label": "Grant Compliance Risk", "entity_scope": "public"},
    {"name": "procurement_disputes", "node_type": "risk_theme", "display_label": "Procurement Disputes", "entity_scope": "public"},

    # Coverages
    {"name": "workers_comp", "node_type": "coverage", "display_label": "Workers Compensation", "entity_scope": "both"},
    {"name": "general_liability", "node_type": "coverage", "display_label": "General Liability", "entity_scope": "both"},
    {"name": "commercial_auto", "node_type": "coverage", "display_label": "Commercial Auto", "entity_scope": "private"},
    {"name": "umbrella", "node_type": "coverage", "display_label": "Umbrella/Excess", "entity_scope": "both"},
    {"name": "property", "node_type": "coverage", "display_label": "Property", "entity_scope": "both"},
    {"name": "builders_risk", "node_type": "coverage", "display_label": "Builders Risk", "entity_scope": "private"},
    {"name": "inland_marine", "node_type": "coverage", "display_label": "Inland Marine", "entity_scope": "private"},
    {"name": "cyber", "node_type": "coverage", "display_label": "Cyber Liability", "entity_scope": "both"},
    {"name": "epli", "node_type": "coverage", "display_label": "EPLI", "entity_scope": "both"},
    {"name": "professional_liability", "node_type": "coverage", "display_label": "Professional Liability", "entity_scope": "private"},
    {"name": "public_officials_liability_cov", "node_type": "coverage", "display_label": "Public Officials Liability Coverage", "entity_scope": "public"},
    {"name": "law_enforcement_liability", "node_type": "coverage", "display_label": "Law Enforcement Liability", "entity_scope": "public"},
    {"name": "governmental_immunity", "node_type": "coverage", "display_label": "Governmental Immunity / Tort Claims", "entity_scope": "public"},
    {"name": "employment_practices_public", "node_type": "coverage", "display_label": "Employment Practices (Public)", "entity_scope": "public"},
    {"name": "municipal_auto", "node_type": "coverage", "display_label": "Municipal Auto", "entity_scope": "public"},
    {"name": "environmental_liability_public", "node_type": "coverage", "display_label": "Environmental Liability (Public)", "entity_scope": "public"},

    # Question categories
    {"name": "operations", "node_type": "question_category", "display_label": "Operations", "entity_scope": "both"},
    {"name": "workforce", "node_type": "question_category", "display_label": "Workforce", "entity_scope": "both"},
    {"name": "contracts", "node_type": "question_category", "display_label": "Contracts", "entity_scope": "both"},
    {"name": "fleet", "node_type": "question_category", "display_label": "Fleet", "entity_scope": "both"},
    {"name": "property_category", "node_type": "question_category", "display_label": "Property", "entity_scope": "both"},
    {"name": "compliance", "node_type": "question_category", "display_label": "Compliance", "entity_scope": "both"},
    {"name": "claims", "node_type": "question_category", "display_label": "Claims", "entity_scope": "both"},
    {"name": "public_interaction", "node_type": "question_category", "display_label": "Public Interaction", "entity_scope": "public"},
    {"name": "governance", "node_type": "question_category", "display_label": "Governance", "entity_scope": "public"},

    # Account traits
    {"name": "uses_subcontractors", "node_type": "account_trait", "display_label": "Uses Subcontractors", "entity_scope": "private"},
    {"name": "multi_state_operations", "node_type": "account_trait", "display_label": "Multi-State Operations", "entity_scope": "both"},
    {"name": "high_mod", "node_type": "account_trait", "display_label": "High Experience Mod", "entity_scope": "both"},
    {"name": "young_fleet", "node_type": "account_trait", "display_label": "Young / Inexperienced Fleet", "entity_scope": "both"},
    {"name": "heavy_equipment", "node_type": "account_trait", "display_label": "Heavy Equipment", "entity_scope": "both"},
    {"name": "residential_work", "node_type": "account_trait", "display_label": "Residential Work", "entity_scope": "private"},
    {"name": "habitational_exposure", "node_type": "account_trait", "display_label": "Habitational Exposure", "entity_scope": "private"},
    {"name": "delivery_operations", "node_type": "account_trait", "display_label": "Delivery Operations", "entity_scope": "private"},
    {"name": "seasonal_payroll", "node_type": "account_trait", "display_label": "Seasonal Payroll", "entity_scope": "both"},
    {"name": "high_turnover", "node_type": "account_trait", "display_label": "High Turnover", "entity_scope": "both"},
]


# --- Graph Edges (denormalized) ---
# (from_node_type, from_node_value, edge_type, to_node_type, to_node_value, weight, evidence_note)

GRAPH_EDGES = [
    # --------------------------------------------------------
    # ROOFING INDUSTRY EXPOSURES
    # --------------------------------------------------------
    ("industry", "roofing", "commonly_has_exposure", "risk_theme", "falls_from_height", 0.95, "Primary roofing injury driver"),
    ("industry", "roofing", "commonly_has_exposure", "risk_theme", "subcontractor_transfer", 0.85, "Subcontract labor common"),
    ("industry", "roofing", "commonly_has_exposure", "risk_theme", "fleet_accidents", 0.65, "Job site travel exposure"),
    ("industry", "roofing", "commonly_has_exposure", "risk_theme", "heat_illness", 0.70, "Outdoor work in hot conditions"),
    ("industry", "roofing", "commonly_has_exposure", "risk_theme", "struck_by_object", 0.65, "Falling materials from roof"),
    ("industry", "roofing", "commonly_has_exposure", "risk_theme", "certificate_tracking", 0.75, "Subcontractor certificate gaps"),
    ("industry", "roofing", "often_requires_coverage", "coverage", "workers_comp", 0.95, "Core coverage"),
    ("industry", "roofing", "often_requires_coverage", "coverage", "general_liability", 0.90, "Third-party injury risk"),
    ("industry", "roofing", "often_requires_coverage", "coverage", "commercial_auto", 0.75, "Fleet exposure"),

    # --------------------------------------------------------
    # TRUCKING INDUSTRY EXPOSURES
    # --------------------------------------------------------
    ("industry", "trucking", "commonly_has_exposure", "risk_theme", "fleet_accidents", 0.95, "Primary loss driver"),
    ("industry", "trucking", "commonly_has_exposure", "risk_theme", "driver_turnover", 0.70, "Driver shortage issue"),
    ("industry", "trucking", "commonly_has_exposure", "risk_theme", "hired_non_owned_auto", 0.60, "Contract drivers common"),
    ("industry", "trucking", "commonly_has_exposure", "risk_theme", "improper_classification", 0.60, "IC vs employee misclass"),
    ("industry", "trucking", "often_requires_coverage", "coverage", "commercial_auto", 0.95, "Core coverage"),
    ("industry", "trucking", "often_requires_coverage", "coverage", "umbrella", 0.80, "Catastrophic crash exposure"),
    ("industry", "trucking", "often_requires_coverage", "coverage", "workers_comp", 0.85, "Driver injury exposure"),

    # --------------------------------------------------------
    # MANUFACTURING INDUSTRY EXPOSURES
    # --------------------------------------------------------
    ("industry", "manufacturing", "commonly_has_exposure", "risk_theme", "machine_guarding", 0.85, "Equipment hazard"),
    ("industry", "manufacturing", "commonly_has_exposure", "risk_theme", "combustible_dust", 0.70, "Fire hazard"),
    ("industry", "manufacturing", "commonly_has_exposure", "risk_theme", "chemical_exposure", 0.75, "Chemical handling"),
    ("industry", "manufacturing", "commonly_has_exposure", "risk_theme", "lifting_ergonomic", 0.65, "Manual material handling"),
    ("industry", "manufacturing", "often_requires_coverage", "coverage", "property", 0.90, "Plant property risk"),
    ("industry", "manufacturing", "often_requires_coverage", "coverage", "workers_comp", 0.85, "Workforce injury exposure"),
    ("industry", "manufacturing", "often_requires_coverage", "coverage", "general_liability", 0.80, "Product/premises liability"),

    # --------------------------------------------------------
    # RESTAURANT INDUSTRY EXPOSURES
    # --------------------------------------------------------
    ("industry", "restaurant", "commonly_has_exposure", "risk_theme", "burns_and_scalds", 0.90, "Kitchen fire/heat hazard"),
    ("industry", "restaurant", "commonly_has_exposure", "risk_theme", "slip_and_fall", 0.85, "Wet kitchen/dining floors"),
    ("industry", "restaurant", "commonly_has_exposure", "risk_theme", "food_contamination", 0.80, "Foodborne illness liability"),
    ("industry", "restaurant", "commonly_has_exposure", "risk_theme", "lifting_ergonomic", 0.55, "Food/supply lifting"),
    ("industry", "restaurant", "often_requires_coverage", "coverage", "general_liability", 0.90, "Patron injury/illness"),
    ("industry", "restaurant", "often_requires_coverage", "coverage", "workers_comp", 0.85, "Kitchen worker injuries"),
    ("industry", "restaurant", "often_requires_coverage", "coverage", "property", 0.80, "Kitchen fire/equipment"),

    # --------------------------------------------------------
    # LANDSCAPING INDUSTRY EXPOSURES
    # --------------------------------------------------------
    ("industry", "landscaping", "commonly_has_exposure", "risk_theme", "heat_illness", 0.85, "Outdoor labor in heat"),
    ("industry", "landscaping", "commonly_has_exposure", "risk_theme", "struck_by_object", 0.70, "Equipment/debris hazard"),
    ("industry", "landscaping", "commonly_has_exposure", "risk_theme", "chemical_exposure", 0.60, "Pesticide/herbicide handling"),
    ("industry", "landscaping", "commonly_has_exposure", "risk_theme", "hired_non_owned_auto", 0.65, "Crew vehicle use"),
    ("industry", "landscaping", "commonly_has_exposure", "risk_theme", "subcontractor_transfer", 0.55, "Subbed work common"),
    ("industry", "landscaping", "often_requires_coverage", "coverage", "workers_comp", 0.90, "Outdoor labor injuries"),
    ("industry", "landscaping", "often_requires_coverage", "coverage", "general_liability", 0.85, "Property damage risk"),
    ("industry", "landscaping", "often_requires_coverage", "coverage", "commercial_auto", 0.80, "Truck/trailer fleet"),

    # --------------------------------------------------------
    # HVAC INDUSTRY EXPOSURES
    # --------------------------------------------------------
    ("industry", "hvac", "commonly_has_exposure", "risk_theme", "falls_from_height", 0.70, "Rooftop unit work"),
    ("industry", "hvac", "commonly_has_exposure", "risk_theme", "chemical_exposure", 0.80, "Refrigerant handling"),
    ("industry", "hvac", "commonly_has_exposure", "risk_theme", "burns_and_scalds", 0.65, "Electrical/heating burns"),
    ("industry", "hvac", "commonly_has_exposure", "risk_theme", "subcontractor_transfer", 0.60, "Sub work on new construction"),
    ("industry", "hvac", "often_requires_coverage", "coverage", "workers_comp", 0.90, "Technician injury exposure"),
    ("industry", "hvac", "often_requires_coverage", "coverage", "general_liability", 0.85, "Customer property damage"),
    ("industry", "hvac", "often_requires_coverage", "coverage", "commercial_auto", 0.75, "Service van fleet"),

    # --------------------------------------------------------
    # MUNICIPAL ENTITY EXPOSURES
    # --------------------------------------------------------
    ("public_entity_type", "municipality", "entity_specific_exposure", "risk_theme", "public_officials_liability", 0.90, "Government decisions"),
    ("public_entity_type", "municipality", "entity_specific_exposure", "risk_theme", "public_event_liability", 0.70, "Community events"),
    ("public_entity_type", "municipality", "entity_specific_exposure", "risk_theme", "cyber_records_breach", 0.60, "Public records systems"),
    ("public_entity_type", "municipality", "entity_specific_exposure", "risk_theme", "volunteer_liability", 0.65, "Volunteer programs"),
    ("public_entity_type", "municipality", "entity_specific_exposure", "risk_theme", "fleet_liability", 0.75, "Municipal fleet operations"),

    ("public_entity_type", "county", "entity_specific_exposure", "risk_theme", "public_officials_liability", 0.90, "County governance decisions"),
    ("public_entity_type", "county", "entity_specific_exposure", "risk_theme", "road_maintenance_liability", 0.85, "County road system"),
    ("public_entity_type", "county", "entity_specific_exposure", "risk_theme", "fleet_liability", 0.70, "County fleet"),

    ("public_entity_type", "school_system", "entity_specific_exposure", "risk_theme", "public_officials_liability", 0.75, "Board decisions"),
    ("public_entity_type", "school_system", "entity_specific_exposure", "risk_theme", "playground_injury", 0.85, "Student playground exposure"),

    # --------------------------------------------------------
    # MUNICIPAL DEPARTMENT EXPOSURES
    # --------------------------------------------------------
    ("department", "law_enforcement", "department_specific_exposure", "risk_theme", "civil_rights_claims", 0.95, "Police liability"),
    ("department", "law_enforcement", "department_specific_exposure", "risk_theme", "excessive_force", 0.85, "Use-of-force claims"),
    ("department", "law_enforcement", "department_specific_exposure", "risk_theme", "police_liability", 0.95, "Core police exposure"),
    ("department", "law_enforcement", "department_specific_exposure", "risk_theme", "fleet_liability", 0.60, "Patrol vehicle operations"),

    ("department", "fire_department", "department_specific_exposure", "risk_theme", "volunteer_liability", 0.75, "Volunteer firefighter exposure"),
    ("department", "fire_department", "department_specific_exposure", "risk_theme", "fleet_liability", 0.70, "Fire apparatus operations"),

    ("department", "public_works", "department_specific_exposure", "risk_theme", "road_maintenance_liability", 0.90, "Road defects"),
    ("department", "public_works", "department_specific_exposure", "risk_theme", "fleet_liability", 0.75, "Municipal fleet"),
    ("department", "public_works", "department_specific_exposure", "risk_theme", "sewer_backup_claims", 0.65, "Infrastructure failures"),

    ("department", "utilities", "department_specific_exposure", "risk_theme", "water_quality_claims", 0.80, "Utility operations"),
    ("department", "utilities", "department_specific_exposure", "risk_theme", "sewer_backup_claims", 0.75, "Infrastructure failures"),
    ("department", "utilities", "department_specific_exposure", "risk_theme", "cyber_records_breach", 0.50, "SCADA/utility systems"),

    ("department", "parks_recreation", "department_specific_exposure", "risk_theme", "playground_injury", 0.85, "Playground accidents"),
    ("department", "parks_recreation", "department_specific_exposure", "risk_theme", "public_event_liability", 0.75, "Community event exposure"),
    ("department", "parks_recreation", "department_specific_exposure", "risk_theme", "volunteer_liability", 0.65, "Park volunteer programs"),

    ("department", "administration", "department_specific_exposure", "risk_theme", "public_officials_liability", 0.90, "Policy and governance decisions"),
    ("department", "administration", "department_specific_exposure", "risk_theme", "zoning_decisions", 0.80, "Land use decisions"),
    ("department", "administration", "department_specific_exposure", "risk_theme", "cyber_records_breach", 0.70, "Public records systems"),
    ("department", "administration", "department_specific_exposure", "risk_theme", "grant_compliance", 0.75, "Federal/state grant administration"),
    ("department", "administration", "department_specific_exposure", "risk_theme", "procurement_disputes", 0.70, "Bidding and contracting"),

    ("department", "sanitation", "department_specific_exposure", "risk_theme", "fleet_liability", 0.80, "Refuse collection fleet"),
    ("department", "sanitation", "department_specific_exposure", "risk_theme", "lifting_ergonomic", 0.65, "Manual refuse handling"),

    ("department", "street_maintenance", "department_specific_exposure", "risk_theme", "road_maintenance_liability", 0.90, "Road repair liability"),
    ("department", "street_maintenance", "department_specific_exposure", "risk_theme", "fleet_liability", 0.75, "Maintenance vehicle fleet"),
    ("department", "street_maintenance", "department_specific_exposure", "risk_theme", "struck_by_object", 0.55, "Work zone hazard"),

    ("department", "fleet_services", "department_specific_exposure", "risk_theme", "fleet_liability", 0.95, "Fleet maintenance operations"),
    ("department", "fleet_services", "department_specific_exposure", "risk_theme", "fleet_accidents", 0.70, "Vehicle operations"),

    ("department", "water_treatment", "department_specific_exposure", "risk_theme", "water_quality_claims", 0.95, "Water quality responsibility"),
    ("department", "water_treatment", "department_specific_exposure", "risk_theme", "chemical_exposure", 0.70, "Treatment chemical handling"),

    # --------------------------------------------------------
    # RISK THEME TO COVERAGE RELATIONSHIPS
    # --------------------------------------------------------
    # Private industry
    ("risk_theme", "falls_from_height", "often_requires_coverage", "coverage", "workers_comp", 0.90, "Worker injury exposure"),
    ("risk_theme", "falls_from_height", "often_requires_coverage", "coverage", "general_liability", 0.70, "Third-party fall claims"),
    ("risk_theme", "falls_from_height", "often_requires_coverage", "coverage", "umbrella", 0.60, "Catastrophic fall verdicts"),

    ("risk_theme", "fleet_accidents", "often_requires_coverage", "coverage", "commercial_auto", 0.95, "Vehicle losses"),
    ("risk_theme", "fleet_accidents", "often_requires_coverage", "coverage", "workers_comp", 0.70, "Driver injury claims"),
    ("risk_theme", "fleet_accidents", "often_requires_coverage", "coverage", "umbrella", 0.65, "Catastrophic accident exposure"),

    ("risk_theme", "driver_turnover", "often_requires_coverage", "coverage", "commercial_auto", 0.75, "Inexperienced driver risk"),
    ("risk_theme", "driver_turnover", "often_requires_coverage", "coverage", "workers_comp", 0.60, "Training period injuries"),

    ("risk_theme", "subcontractor_transfer", "often_requires_coverage", "coverage", "general_liability", 0.80, "Contractual liability"),
    ("risk_theme", "subcontractor_transfer", "often_requires_coverage", "coverage", "umbrella", 0.70, "Excess liability on sub work"),

    ("risk_theme", "machine_guarding", "often_requires_coverage", "coverage", "workers_comp", 0.90, "Amputation/crush injuries"),
    ("risk_theme", "combustible_dust", "often_requires_coverage", "coverage", "property", 0.85, "Dust explosion fire risk"),
    ("risk_theme", "combustible_dust", "often_requires_coverage", "coverage", "workers_comp", 0.75, "Burn/blast injuries"),
    ("risk_theme", "burns_and_scalds", "often_requires_coverage", "coverage", "workers_comp", 0.90, "Kitchen/heat injuries"),
    ("risk_theme", "slip_and_fall", "often_requires_coverage", "coverage", "general_liability", 0.85, "Patron/visitor falls"),
    ("risk_theme", "slip_and_fall", "often_requires_coverage", "coverage", "workers_comp", 0.75, "Employee slip injuries"),
    ("risk_theme", "food_contamination", "often_requires_coverage", "coverage", "general_liability", 0.90, "Foodborne illness liability"),
    ("risk_theme", "food_contamination", "often_requires_coverage", "coverage", "professional_liability", 0.50, "Food safety standard of care"),
    ("risk_theme", "heat_illness", "often_requires_coverage", "coverage", "workers_comp", 0.90, "Heat stroke/exhaustion"),
    ("risk_theme", "chemical_exposure", "often_requires_coverage", "coverage", "workers_comp", 0.85, "Toxic exposure claims"),
    ("risk_theme", "chemical_exposure", "often_requires_coverage", "coverage", "general_liability", 0.55, "Third-party contamination"),
    ("risk_theme", "hired_non_owned_auto", "often_requires_coverage", "coverage", "commercial_auto", 0.90, "Non-owned vehicle exposure"),

    # Public entity
    ("risk_theme", "civil_rights_claims", "often_requires_coverage", "coverage", "law_enforcement_liability", 0.95, "Police exposure"),
    ("risk_theme", "civil_rights_claims", "often_requires_coverage", "coverage", "governmental_immunity", 0.90, "Sovereign immunity defense"),
    ("risk_theme", "civil_rights_claims", "often_requires_coverage", "coverage", "employment_practices_public", 0.60, "Internal discrimination claims"),

    ("risk_theme", "police_liability", "often_requires_coverage", "coverage", "law_enforcement_liability", 0.95, "Core police coverage"),
    ("risk_theme", "police_liability", "often_requires_coverage", "coverage", "governmental_immunity", 0.80, "Tort claims defense"),

    ("risk_theme", "excessive_force", "often_requires_coverage", "coverage", "law_enforcement_liability", 0.95, "Use-of-force claims"),
    ("risk_theme", "excessive_force", "often_requires_coverage", "coverage", "umbrella", 0.70, "Large verdict exposure"),

    ("risk_theme", "public_officials_liability", "often_requires_coverage", "coverage", "public_officials_liability_cov", 0.95, "Government decisions"),
    ("risk_theme", "public_officials_liability", "often_requires_coverage", "coverage", "epli", 0.55, "Employment-related decisions"),

    ("risk_theme", "zoning_decisions", "often_requires_coverage", "coverage", "public_officials_liability_cov", 0.85, "Land use decision liability"),

    ("risk_theme", "road_maintenance_liability", "often_requires_coverage", "coverage", "general_liability", 0.85, "Road defect claims"),
    ("risk_theme", "road_maintenance_liability", "often_requires_coverage", "coverage", "municipal_auto", 0.60, "Maintenance vehicle exposure"),

    ("risk_theme", "playground_injury", "often_requires_coverage", "coverage", "general_liability", 0.90, "Child injury claims"),
    ("risk_theme", "playground_injury", "often_requires_coverage", "coverage", "property", 0.50, "Equipment replacement"),

    ("risk_theme", "public_event_liability", "often_requires_coverage", "coverage", "general_liability", 0.90, "Event attendee injuries"),
    ("risk_theme", "public_event_liability", "often_requires_coverage", "coverage", "umbrella", 0.65, "Large crowd exposure"),

    ("risk_theme", "sewer_backup_claims", "often_requires_coverage", "coverage", "general_liability", 0.80, "Property damage claims"),
    ("risk_theme", "sewer_backup_claims", "often_requires_coverage", "coverage", "environmental_liability_public", 0.70, "Contamination liability"),

    ("risk_theme", "water_quality_claims", "often_requires_coverage", "coverage", "environmental_liability_public", 0.90, "Water contamination"),
    ("risk_theme", "water_quality_claims", "often_requires_coverage", "coverage", "general_liability", 0.60, "Health impact claims"),

    ("risk_theme", "fleet_liability", "often_requires_coverage", "coverage", "municipal_auto", 0.95, "Municipal vehicle losses"),
    ("risk_theme", "fleet_liability", "often_requires_coverage", "coverage", "workers_comp", 0.65, "Driver injury claims"),

    ("risk_theme", "volunteer_liability", "often_requires_coverage", "coverage", "general_liability", 0.80, "Volunteer injury claims"),
    ("risk_theme", "volunteer_liability", "often_requires_coverage", "coverage", "workers_comp", 0.70, "Volunteer WC coverage"),

    ("risk_theme", "cyber_records_breach", "often_requires_coverage", "coverage", "cyber", 0.95, "Data breach response"),
    ("risk_theme", "grant_compliance", "often_requires_coverage", "coverage", "public_officials_liability_cov", 0.60, "Grant mismanagement claims"),
    ("risk_theme", "procurement_disputes", "often_requires_coverage", "coverage", "public_officials_liability_cov", 0.65, "Bid protest liability"),

    # --------------------------------------------------------
    # RISK THEMES TRIGGER QUESTION CATEGORIES
    # --------------------------------------------------------
    ("risk_theme", "falls_from_height", "often_triggers_question_category", "question_category", "operations", 0.80, "Safety procedures"),
    ("risk_theme", "falls_from_height", "often_triggers_question_category", "question_category", "compliance", 0.70, "OSHA fall protection"),
    ("risk_theme", "fleet_accidents", "often_triggers_question_category", "question_category", "fleet", 0.90, "Vehicle management"),
    ("risk_theme", "fleet_accidents", "often_triggers_question_category", "question_category", "workforce", 0.60, "Driver hiring/training"),
    ("risk_theme", "subcontractor_transfer", "often_triggers_question_category", "question_category", "contracts", 0.85, "Risk transfer questions"),
    ("risk_theme", "machine_guarding", "often_triggers_question_category", "question_category", "operations", 0.85, "Equipment safety"),
    ("risk_theme", "machine_guarding", "often_triggers_question_category", "question_category", "compliance", 0.75, "OSHA guarding standards"),
    ("risk_theme", "food_contamination", "often_triggers_question_category", "question_category", "compliance", 0.85, "Health department compliance"),
    ("risk_theme", "food_contamination", "often_triggers_question_category", "question_category", "operations", 0.75, "Food handling procedures"),
    ("risk_theme", "burns_and_scalds", "often_triggers_question_category", "question_category", "operations", 0.80, "Kitchen safety protocols"),
    ("risk_theme", "chemical_exposure", "often_triggers_question_category", "question_category", "compliance", 0.80, "HAZCOM compliance"),
    ("risk_theme", "lifting_ergonomic", "often_triggers_question_category", "question_category", "workforce", 0.70, "Ergonomic assessment"),
    ("risk_theme", "certificate_tracking", "often_triggers_question_category", "question_category", "contracts", 0.85, "Certificate management"),

    # Public entity risk themes -> question categories
    ("risk_theme", "public_officials_liability", "often_triggers_question_category", "question_category", "governance", 0.85, "Policy decisions"),
    ("risk_theme", "civil_rights_claims", "often_triggers_question_category", "question_category", "compliance", 0.90, "Constitutional compliance"),
    ("risk_theme", "civil_rights_claims", "often_triggers_question_category", "question_category", "claims", 0.85, "Litigation history"),
    ("risk_theme", "excessive_force", "often_triggers_question_category", "question_category", "operations", 0.85, "Use-of-force policy"),
    ("risk_theme", "road_maintenance_liability", "often_triggers_question_category", "question_category", "operations", 0.80, "Road inspection procedures"),
    ("risk_theme", "playground_injury", "often_triggers_question_category", "question_category", "property_category", 0.85, "Equipment inspection"),
    ("risk_theme", "fleet_liability", "often_triggers_question_category", "question_category", "fleet", 0.90, "Vehicle management"),
    ("risk_theme", "volunteer_liability", "often_triggers_question_category", "question_category", "workforce", 0.75, "Volunteer management"),
    ("risk_theme", "cyber_records_breach", "often_triggers_question_category", "question_category", "compliance", 0.80, "Data security practices"),
    ("risk_theme", "grant_compliance", "often_triggers_question_category", "question_category", "governance", 0.80, "Grant administration"),
    ("risk_theme", "procurement_disputes", "often_triggers_question_category", "question_category", "contracts", 0.80, "Bid and procurement process"),
    ("risk_theme", "water_quality_claims", "often_triggers_question_category", "question_category", "operations", 0.80, "Treatment operations"),
    ("risk_theme", "sewer_backup_claims", "often_triggers_question_category", "question_category", "property_category", 0.75, "Infrastructure condition"),
    ("risk_theme", "public_event_liability", "often_triggers_question_category", "question_category", "public_interaction", 0.85, "Event safety planning"),

    # --------------------------------------------------------
    # RISK THEME CO-OCCURRENCES
    # --------------------------------------------------------
    ("risk_theme", "falls_from_height", "commonly_cooccurs_with", "risk_theme", "struck_by_object", 0.65, "Construction site hazard pairing"),
    ("risk_theme", "fleet_accidents", "commonly_cooccurs_with", "risk_theme", "driver_turnover", 0.70, "New driver accident risk"),
    ("risk_theme", "subcontractor_transfer", "commonly_cooccurs_with", "risk_theme", "certificate_tracking", 0.80, "Sub management gap"),
    ("risk_theme", "burns_and_scalds", "commonly_cooccurs_with", "risk_theme", "chemical_exposure", 0.50, "Kitchen/industrial heat+chemical"),
    ("risk_theme", "machine_guarding", "commonly_cooccurs_with", "risk_theme", "struck_by_object", 0.55, "Equipment ejection hazard"),
    ("risk_theme", "police_liability", "commonly_cooccurs_with", "risk_theme", "civil_rights_claims", 0.85, "Section 1983 exposure"),
    ("risk_theme", "civil_rights_claims", "commonly_cooccurs_with", "risk_theme", "excessive_force", 0.80, "Force-related civil rights"),
    ("risk_theme", "road_maintenance_liability", "commonly_cooccurs_with", "risk_theme", "fleet_liability", 0.60, "Maintenance vehicle exposure"),
    ("risk_theme", "sewer_backup_claims", "commonly_cooccurs_with", "risk_theme", "water_quality_claims", 0.55, "Infrastructure system overlap"),
    ("risk_theme", "public_officials_liability", "commonly_cooccurs_with", "risk_theme", "zoning_decisions", 0.65, "Governance decision liability"),
    ("risk_theme", "grant_compliance", "commonly_cooccurs_with", "risk_theme", "procurement_disputes", 0.50, "Federal compliance overlap"),

    # --------------------------------------------------------
    # ACCOUNT TRAITS THAT ELEVATE RISK
    # --------------------------------------------------------
    ("account_trait", "uses_subcontractors", "elevated_by_trait", "risk_theme", "subcontractor_transfer", 0.90, "Subcontract exposure"),
    ("account_trait", "uses_subcontractors", "elevated_by_trait", "risk_theme", "certificate_tracking", 0.80, "Certificate management burden"),
    ("account_trait", "young_fleet", "elevated_by_trait", "risk_theme", "fleet_accidents", 0.70, "Driver inexperience"),
    ("account_trait", "high_mod", "elevated_by_trait", "risk_theme", "falls_from_height", 0.65, "Loss history indicator"),
    ("account_trait", "multi_state_operations", "elevated_by_trait", "risk_theme", "compliance_complexity", 0.75, "Regulatory complexity"),
    ("account_trait", "heavy_equipment", "elevated_by_trait", "risk_theme", "struck_by_object", 0.70, "Heavy equipment hazard"),
    ("account_trait", "heavy_equipment", "elevated_by_trait", "risk_theme", "machine_guarding", 0.65, "Equipment safety gaps"),
    ("account_trait", "residential_work", "elevated_by_trait", "risk_theme", "falls_from_height", 0.75, "Residential roof slope risk"),
    ("account_trait", "delivery_operations", "elevated_by_trait", "risk_theme", "fleet_accidents", 0.75, "Delivery vehicle exposure"),
    ("account_trait", "delivery_operations", "elevated_by_trait", "risk_theme", "hired_non_owned_auto", 0.70, "Personal vehicle use"),
    ("account_trait", "seasonal_payroll", "elevated_by_trait", "risk_theme", "improper_classification", 0.65, "Seasonal worker classification"),
    ("account_trait", "high_turnover", "elevated_by_trait", "risk_theme", "driver_turnover", 0.80, "Workforce instability"),
    ("account_trait", "high_turnover", "elevated_by_trait", "risk_theme", "lifting_ergonomic", 0.55, "Untrained new workers"),
]


def seed_graph(db):
    """Insert graph nodes and edges (denormalized)."""
    # Check if already seeded
    existing = db.query(RiskTheme).count()
    if existing > 0:
        print(f"  Graph already seeded ({existing} nodes). Skipping.")
        return

    # Insert nodes into risk_themes (node registry)
    for node_data in GRAPH_NODES:
        node = RiskTheme(
            name=node_data["name"],
            node_type=node_data["node_type"],
            display_label=node_data.get("display_label"),
            description=node_data.get("description"),
            entity_scope=node_data.get("entity_scope"),
        )
        db.add(node)

    db.flush()
    print(f"  Inserted {len(GRAPH_NODES)} graph nodes.")

    # Insert denormalized edges
    edge_count = 0
    for edge_data in GRAPH_EDGES:
        from_node_type, from_node_value, edge_type, to_node_type, to_node_value, weight, evidence_note = edge_data
        edge = RiskThemeEdge(
            from_node_type=from_node_type,
            from_node_value=from_node_value,
            edge_type=edge_type,
            to_node_type=to_node_type,
            to_node_value=to_node_value,
            weight=weight,
            evidence_note=evidence_note,
        )
        db.add(edge)
        edge_count += 1

    db.commit()
    print(f"  Inserted {edge_count} graph edges.")


def seed_producer_questions(db):
    """Load producer questions from JSON into database."""
    existing = db.query(ProducerQuestion).count()
    if existing > 0:
        print(f"  Producer questions already seeded ({existing} questions). Skipping.")
        return

    json_path = os.path.join(os.path.dirname(__file__), "data", "municipal_question_library.json")
    if not os.path.exists(json_path):
        print(f"  Question library not found at {json_path}. Skipping.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    count = 0
    for q in questions:
        pq = ProducerQuestion(
            question_text=q["question_text"],
            category=q["category"],
            department=q.get("department"),
            risk_theme=q.get("risk_theme"),
            coverage=q.get("coverage"),
            entity_type="public_entity",
            purpose=q.get("purpose"),
            follow_up_questions=q.get("follow_up_questions"),
            importance_score=q.get("importance_score", 5.0),
            difficulty_score=q.get("difficulty_score", 5.0),
        )
        db.add(pq)
        count += 1

    db.commit()
    print(f"  Inserted {count} producer questions.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("Seeding risk theme graph...")
        seed_graph(db)

        print("Seeding producer questions...")
        seed_producer_questions(db)

        print("Done!")
    finally:
        db.close()
