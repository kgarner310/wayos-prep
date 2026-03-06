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
# node_type: industry | risk_theme | coverage | department | entity_type | public_entity_type

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

    # Coverages (both scope — used across entity types)
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
]


# --- Graph Edges ---
# (from_name, to_name, edge_type, weight)

GRAPH_EDGES = [
    # Industry -> Risk Theme (causes / exposes_to)
    ("roofing", "falls_from_height", "causes", 0.95),
    ("roofing", "subcontractor_transfer", "causes", 0.80),
    ("roofing", "heat_illness", "causes", 0.70),
    ("roofing", "struck_by_object", "causes", 0.65),
    ("roofing", "certificate_tracking", "causes", 0.75),

    ("trucking", "fleet_accidents", "causes", 0.95),
    ("trucking", "driver_turnover", "causes", 0.85),
    ("trucking", "hired_non_owned_auto", "causes", 0.70),
    ("trucking", "improper_classification", "causes", 0.60),

    ("manufacturing", "machine_guarding", "causes", 0.90),
    ("manufacturing", "combustible_dust", "causes", 0.70),
    ("manufacturing", "chemical_exposure", "causes", 0.75),
    ("manufacturing", "lifting_ergonomic", "causes", 0.65),

    ("restaurant", "burns_and_scalds", "causes", 0.90),
    ("restaurant", "slip_and_fall", "causes", 0.85),
    ("restaurant", "food_contamination", "causes", 0.80),
    ("restaurant", "lifting_ergonomic", "causes", 0.55),

    ("landscaping", "heat_illness", "causes", 0.85),
    ("landscaping", "struck_by_object", "causes", 0.70),
    ("landscaping", "chemical_exposure", "causes", 0.60),
    ("landscaping", "hired_non_owned_auto", "causes", 0.65),
    ("landscaping", "subcontractor_transfer", "causes", 0.55),

    ("hvac", "falls_from_height", "causes", 0.70),
    ("hvac", "chemical_exposure", "causes", 0.80),
    ("hvac", "burns_and_scalds", "causes", 0.65),
    ("hvac", "subcontractor_transfer", "causes", 0.60),

    # Risk Theme -> Coverage (requires_coverage)
    ("falls_from_height", "workers_comp", "requires_coverage", 0.95),
    ("falls_from_height", "general_liability", "requires_coverage", 0.70),
    ("falls_from_height", "umbrella", "requires_coverage", 0.60),

    ("fleet_accidents", "commercial_auto", "requires_coverage", 0.95),
    ("fleet_accidents", "workers_comp", "requires_coverage", 0.70),
    ("fleet_accidents", "umbrella", "requires_coverage", 0.65),

    ("driver_turnover", "commercial_auto", "requires_coverage", 0.75),
    ("driver_turnover", "workers_comp", "requires_coverage", 0.60),

    ("subcontractor_transfer", "general_liability", "requires_coverage", 0.85),
    ("subcontractor_transfer", "umbrella", "requires_coverage", 0.70),

    ("machine_guarding", "workers_comp", "requires_coverage", 0.90),
    ("combustible_dust", "property", "requires_coverage", 0.85),
    ("combustible_dust", "workers_comp", "requires_coverage", 0.75),

    ("burns_and_scalds", "workers_comp", "requires_coverage", 0.90),
    ("slip_and_fall", "general_liability", "requires_coverage", 0.85),
    ("slip_and_fall", "workers_comp", "requires_coverage", 0.75),

    ("food_contamination", "general_liability", "requires_coverage", 0.90),
    ("food_contamination", "professional_liability", "requires_coverage", 0.50),

    ("heat_illness", "workers_comp", "requires_coverage", 0.90),
    ("chemical_exposure", "workers_comp", "requires_coverage", 0.85),
    ("chemical_exposure", "general_liability", "requires_coverage", 0.55),

    ("hired_non_owned_auto", "commercial_auto", "requires_coverage", 0.90),

    # Risk Theme co-occurrence
    ("falls_from_height", "struck_by_object", "co_occurs", 0.65),
    ("fleet_accidents", "driver_turnover", "co_occurs", 0.70),
    ("subcontractor_transfer", "certificate_tracking", "co_occurs", 0.80),
    ("burns_and_scalds", "chemical_exposure", "co_occurs", 0.50),
    ("machine_guarding", "struck_by_object", "co_occurs", 0.55),

    # Department -> Risk Theme (public entity)
    ("law_enforcement", "police_liability", "causes", 0.95),
    ("law_enforcement", "civil_rights_claims", "causes", 0.90),
    ("law_enforcement", "excessive_force", "causes", 0.85),
    ("law_enforcement", "fleet_liability", "causes", 0.60),

    ("fire_department", "volunteer_liability", "causes", 0.75),
    ("fire_department", "fleet_liability", "causes", 0.70),

    ("public_works", "road_maintenance_liability", "causes", 0.90),
    ("public_works", "fleet_liability", "causes", 0.75),
    ("public_works", "sewer_backup_claims", "causes", 0.65),

    ("utilities", "water_quality_claims", "causes", 0.85),
    ("utilities", "sewer_backup_claims", "causes", 0.80),
    ("utilities", "cyber_records_breach", "causes", 0.50),

    ("parks_recreation", "playground_injury", "causes", 0.90),
    ("parks_recreation", "public_event_liability", "causes", 0.75),
    ("parks_recreation", "volunteer_liability", "causes", 0.65),

    ("administration", "public_officials_liability", "causes", 0.90),
    ("administration", "zoning_decisions", "causes", 0.80),
    ("administration", "cyber_records_breach", "causes", 0.70),
    ("administration", "grant_compliance", "causes", 0.75),
    ("administration", "procurement_disputes", "causes", 0.70),

    ("sanitation", "fleet_liability", "causes", 0.80),
    ("sanitation", "lifting_ergonomic", "causes", 0.65),

    ("street_maintenance", "road_maintenance_liability", "causes", 0.90),
    ("street_maintenance", "fleet_liability", "causes", 0.75),
    ("street_maintenance", "struck_by_object", "causes", 0.55),

    ("fleet_services", "fleet_liability", "causes", 0.95),
    ("fleet_services", "fleet_accidents", "causes", 0.70),

    ("water_treatment", "water_quality_claims", "causes", 0.95),
    ("water_treatment", "chemical_exposure", "causes", 0.70),

    # Public entity risk theme -> coverage
    ("police_liability", "law_enforcement_liability", "requires_coverage", 0.95),
    ("police_liability", "governmental_immunity", "requires_coverage", 0.80),

    ("civil_rights_claims", "law_enforcement_liability", "requires_coverage", 0.85),
    ("civil_rights_claims", "governmental_immunity", "requires_coverage", 0.90),
    ("civil_rights_claims", "employment_practices_public", "requires_coverage", 0.60),

    ("excessive_force", "law_enforcement_liability", "requires_coverage", 0.95),
    ("excessive_force", "umbrella", "requires_coverage", 0.70),

    ("public_officials_liability", "public_officials_liability_cov", "requires_coverage", 0.95),
    ("public_officials_liability", "epli", "requires_coverage", 0.55),

    ("zoning_decisions", "public_officials_liability_cov", "requires_coverage", 0.85),

    ("road_maintenance_liability", "general_liability", "requires_coverage", 0.85),
    ("road_maintenance_liability", "municipal_auto", "requires_coverage", 0.60),

    ("playground_injury", "general_liability", "requires_coverage", 0.90),
    ("playground_injury", "property", "requires_coverage", 0.50),

    ("public_event_liability", "general_liability", "requires_coverage", 0.90),
    ("public_event_liability", "umbrella", "requires_coverage", 0.65),

    ("sewer_backup_claims", "general_liability", "requires_coverage", 0.80),
    ("sewer_backup_claims", "environmental_liability_public", "requires_coverage", 0.70),

    ("water_quality_claims", "environmental_liability_public", "requires_coverage", 0.90),
    ("water_quality_claims", "general_liability", "requires_coverage", 0.60),

    ("fleet_liability", "municipal_auto", "requires_coverage", 0.95),
    ("fleet_liability", "workers_comp", "requires_coverage", 0.65),

    ("volunteer_liability", "general_liability", "requires_coverage", 0.80),
    ("volunteer_liability", "workers_comp", "requires_coverage", 0.70),

    ("cyber_records_breach", "cyber", "requires_coverage", 0.95),

    ("grant_compliance", "public_officials_liability_cov", "requires_coverage", 0.60),
    ("procurement_disputes", "public_officials_liability_cov", "requires_coverage", 0.65),

    # Public entity co-occurrences
    ("police_liability", "civil_rights_claims", "co_occurs", 0.85),
    ("civil_rights_claims", "excessive_force", "co_occurs", 0.80),
    ("road_maintenance_liability", "fleet_liability", "co_occurs", 0.60),
    ("sewer_backup_claims", "water_quality_claims", "co_occurs", 0.55),
    ("public_officials_liability", "zoning_decisions", "co_occurs", 0.65),
    ("grant_compliance", "procurement_disputes", "co_occurs", 0.50),

    # Entity type -> department connections
    ("public_entity", "law_enforcement", "has_department", 0.85),
    ("public_entity", "fire_department", "has_department", 0.80),
    ("public_entity", "public_works", "has_department", 0.90),
    ("public_entity", "utilities", "has_department", 0.75),
    ("public_entity", "parks_recreation", "has_department", 0.70),
    ("public_entity", "administration", "has_department", 0.95),
    ("public_entity", "sanitation", "has_department", 0.65),
    ("public_entity", "street_maintenance", "has_department", 0.70),
    ("public_entity", "fleet_services", "has_department", 0.65),
    ("public_entity", "water_treatment", "has_department", 0.60),

    # Public entity type -> department
    ("municipality", "law_enforcement", "has_department", 0.90),
    ("municipality", "fire_department", "has_department", 0.85),
    ("municipality", "public_works", "has_department", 0.90),
    ("municipality", "administration", "has_department", 0.95),
    ("municipality", "parks_recreation", "has_department", 0.80),

    ("county", "law_enforcement", "has_department", 0.95),
    ("county", "public_works", "has_department", 0.85),
    ("county", "administration", "has_department", 0.90),
]


def seed_graph(db):
    """Insert graph nodes and edges."""
    # Check if already seeded
    existing = db.query(RiskTheme).count()
    if existing > 0:
        print(f"  Graph already seeded ({existing} nodes). Skipping.")
        return

    # Insert nodes
    node_map = {}
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
        node_map[node_data["name"]] = node.id

    print(f"  Inserted {len(node_map)} graph nodes.")

    # Insert edges
    edge_count = 0
    skipped = 0
    for from_name, to_name, edge_type, weight in GRAPH_EDGES:
        from_id = node_map.get(from_name)
        to_id = node_map.get(to_name)
        if not from_id or not to_id:
            skipped += 1
            continue

        edge = RiskThemeEdge(
            from_theme_id=from_id,
            to_theme_id=to_id,
            edge_type=edge_type,
            weight=weight,
        )
        db.add(edge)
        edge_count += 1

    db.commit()
    print(f"  Inserted {edge_count} graph edges ({skipped} skipped).")


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
