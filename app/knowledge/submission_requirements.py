"""Submission Requirements — structured underwriting readiness templates per industry.

Defines what information is needed for a quality submission, organized by
industry vertical. Used by the readiness scoring service to evaluate
completeness and quality of submission inputs.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# MODELS
# ============================================================


@dataclass
class SubmissionRequirement:
    """A single field/item needed for a quality submission."""

    field_name: str
    label: str
    required_for: list[str] = field(default_factory=list)
    recommended_for: list[str] = field(default_factory=list)
    importance: str = "medium"  # critical | high | medium | low
    description: str = ""
    examples: list[str] = field(default_factory=list)
    applies_when: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IndustrySubmissionTemplate:
    """Complete submission readiness template for an industry vertical."""

    industry: str
    jurisdiction: str
    required_fields: list[SubmissionRequirement] = field(default_factory=list)
    recommended_fields: list[SubmissionRequirement] = field(default_factory=list)
    source_version: str = "2026-03"
    last_updated: str = "2026-03-07"

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# REGISTRY
# ============================================================

INDUSTRY_SUBMISSION_TEMPLATES: dict[str, IndustrySubmissionTemplate] = {}


def get_submission_template(industry: str) -> Optional[IndustrySubmissionTemplate]:
    """Look up a submission template by normalized key with suffix fallback."""
    key = industry.lower().strip()
    if key in INDUSTRY_SUBMISSION_TEMPLATES:
        return INDUSTRY_SUBMISSION_TEMPLATES[key]
    for suffix in [" contractor", " shop", " store", " owner", " company"]:
        alt = key + suffix
        if alt in INDUSTRY_SUBMISSION_TEMPLATES:
            return INDUSTRY_SUBMISSION_TEMPLATES[alt]
    return None


def list_submission_templates() -> list[str]:
    """Return sorted list of available template industry keys."""
    return sorted(INDUSTRY_SUBMISSION_TEMPLATES.keys())


# ============================================================
# COMMON FIELD DEFINITIONS (reused across industries)
# ============================================================

def _common_required() -> list[SubmissionRequirement]:
    """Fields required for virtually every commercial submission."""
    return [
        SubmissionRequirement(
            field_name="legal_entity_name",
            label="Legal Entity Name",
            required_for=["all"],
            importance="critical",
            description="Full legal name of the insured entity",
            examples=["Summit Ridge Roofing LLC", "GreenScape Landscapes Inc."],
        ),
        SubmissionRequirement(
            field_name="operations_description",
            label="Operations Description",
            required_for=["all"],
            importance="critical",
            description="Clear description of what the business does, scope of work, and primary activities",
            examples=["Commercial and residential roof installation and repair, primarily shingle and flat roof systems"],
        ),
        SubmissionRequirement(
            field_name="years_in_business",
            label="Years in Business",
            required_for=["all"],
            importance="high",
            description="Number of years the business has been operating",
            examples=["8", "15"],
        ),
        SubmissionRequirement(
            field_name="annual_revenue",
            label="Annual Revenue",
            required_for=["all"],
            importance="critical",
            description="Annual gross revenue",
            examples=["2400000", "850000"],
        ),
        SubmissionRequirement(
            field_name="payroll",
            label="Total Payroll",
            required_for=["workers_compensation", "general_liability"],
            importance="critical",
            description="Total annual payroll broken down by classification if possible",
            examples=["850000", "320000"],
        ),
        SubmissionRequirement(
            field_name="employee_count",
            label="Employee Count",
            required_for=["workers_compensation"],
            importance="high",
            description="Total number of employees including full-time, part-time, and seasonal",
            examples=["14", "8"],
        ),
        SubmissionRequirement(
            field_name="loss_runs",
            label="Loss Runs",
            required_for=["all"],
            importance="critical",
            description="5-year loss run history from current and prior carriers",
            examples=["provided", "3 years available", "requested from prior carrier"],
        ),
        SubmissionRequirement(
            field_name="current_coverages",
            label="Current Coverages",
            required_for=["all"],
            importance="high",
            description="List of current insurance coverages and limits",
            examples=["GL $1M/$2M, WC statutory, Auto $1M CSL"],
        ),
        SubmissionRequirement(
            field_name="requested_coverages",
            label="Requested Coverages",
            required_for=["all"],
            importance="high",
            description="Coverages being requested for this submission",
            examples=["GL, WC, Commercial Auto, Umbrella"],
        ),
    ]


def _common_recommended() -> list[SubmissionRequirement]:
    """Fields recommended for most commercial submissions."""
    return [
        SubmissionRequirement(
            field_name="prior_carrier",
            label="Prior Carrier",
            recommended_for=["all"],
            importance="medium",
            description="Name of current/prior insurance carrier",
            examples=["Hartford", "Travelers"],
        ),
        SubmissionRequirement(
            field_name="reason_for_change",
            label="Reason for Change",
            recommended_for=["all"],
            importance="medium",
            description="Why the insured is shopping or changing carriers",
            examples=["Rate increase", "Non-renewal", "Better coverage needed"],
        ),
        SubmissionRequirement(
            field_name="effective_date",
            label="Effective Date",
            recommended_for=["all"],
            importance="medium",
            description="Desired policy effective date",
            examples=["2026-04-01", "2026-07-15"],
        ),
    ]


# ============================================================
# INDUSTRY-SPECIFIC TEMPLATES
# ============================================================

def _build_roofing_template() -> IndustrySubmissionTemplate:
    required = _common_required() + [
        SubmissionRequirement(
            field_name="subcontractor_usage",
            label="Subcontractor Usage",
            required_for=["general_liability", "workers_compensation"],
            importance="critical",
            description="Whether subs are used, percentage of work, certificate tracking process",
            examples=["yes, approx 30 percent of labor", "no subcontractors used"],
        ),
        SubmissionRequirement(
            field_name="vehicle_count",
            label="Vehicle Count",
            required_for=["commercial_auto"],
            importance="high",
            description="Number of owned, leased, and hired vehicles",
            examples=["6", "12"],
        ),
        SubmissionRequirement(
            field_name="fall_protection_program",
            label="Fall Protection Program",
            required_for=["workers_compensation", "general_liability"],
            importance="critical",
            description="Documented fall protection program with training records",
            examples=["yes, OSHA-compliant program with quarterly training", "informal safety practices"],
        ),
        SubmissionRequirement(
            field_name="safety_program",
            label="Safety Program",
            required_for=["workers_compensation"],
            importance="high",
            description="Written safety program and training documentation",
            examples=["formal written program", "weekly toolbox talks"],
        ),
    ]
    recommended = _common_recommended() + [
        SubmissionRequirement(
            field_name="roof_types",
            label="Roof Types",
            recommended_for=["general_liability"],
            importance="medium",
            description="Types of roofing work performed (shingle, flat, metal, etc.)",
            examples=["residential shingle, commercial flat roof, TPO"],
        ),
        SubmissionRequirement(
            field_name="max_height",
            label="Maximum Working Height",
            recommended_for=["workers_compensation"],
            importance="medium",
            description="Maximum height typically worked at",
            examples=["3 stories", "40 feet"],
        ),
        SubmissionRequirement(
            field_name="tool_equipment_values",
            label="Tool & Equipment Values",
            recommended_for=["inland_marine"],
            importance="low",
            description="Total value of owned tools and equipment",
            examples=["75000", "150000"],
        ),
    ]
    return IndustrySubmissionTemplate(
        industry="roofing contractor",
        jurisdiction="general",
        required_fields=required,
        recommended_fields=recommended,
    )


def _build_landscaping_template() -> IndustrySubmissionTemplate:
    required = _common_required() + [
        SubmissionRequirement(
            field_name="subcontractor_usage",
            label="Subcontractor Usage",
            required_for=["general_liability"],
            importance="high",
            description="Whether subcontractors are used and for what work",
            examples=["yes, for hardscape installations", "no subcontractors"],
        ),
        SubmissionRequirement(
            field_name="vehicle_count",
            label="Vehicle Count",
            required_for=["commercial_auto"],
            importance="high",
            description="Number of trucks, trailers, and other vehicles",
            examples=["4 trucks, 3 trailers"],
        ),
        SubmissionRequirement(
            field_name="safety_program",
            label="Safety Program",
            required_for=["workers_compensation"],
            importance="high",
            description="Written safety program covering equipment and chemical use",
            examples=["formal program with chemical handling procedures"],
        ),
    ]
    recommended = _common_recommended() + [
        SubmissionRequirement(
            field_name="pesticide_herbicide_use",
            label="Pesticide/Herbicide Use",
            recommended_for=["general_liability"],
            importance="medium",
            description="Whether chemical treatments are applied and licensing held",
            examples=["licensed applicator, limited herbicide use"],
        ),
        SubmissionRequirement(
            field_name="tool_equipment_values",
            label="Tool & Equipment Values",
            recommended_for=["inland_marine"],
            importance="low",
            description="Total value of mowers, trimmers, and other equipment",
            examples=["45000", "80000"],
        ),
        SubmissionRequirement(
            field_name="seasonal_employees",
            label="Seasonal Employees",
            recommended_for=["workers_compensation"],
            importance="medium",
            description="Number and duration of seasonal workers",
            examples=["6 seasonal from April-October"],
        ),
    ]
    return IndustrySubmissionTemplate(
        industry="landscaping contractor",
        jurisdiction="general",
        required_fields=required,
        recommended_fields=recommended,
    )


def _build_hvac_template() -> IndustrySubmissionTemplate:
    required = _common_required() + [
        SubmissionRequirement(
            field_name="subcontractor_usage",
            label="Subcontractor Usage",
            required_for=["general_liability"],
            importance="high",
            description="Subcontractor use for installation or ductwork",
            examples=["yes, licensed electricians for wiring", "no subs"],
        ),
        SubmissionRequirement(
            field_name="vehicle_count",
            label="Vehicle Count",
            required_for=["commercial_auto"],
            importance="high",
            description="Service vans and trucks in fleet",
            examples=["8 service vans"],
        ),
        SubmissionRequirement(
            field_name="safety_program",
            label="Safety Program",
            required_for=["workers_compensation"],
            importance="high",
            description="Safety program covering refrigerant handling, confined spaces, electrical",
            examples=["written program with EPA 608 compliance"],
        ),
    ]
    recommended = _common_recommended() + [
        SubmissionRequirement(
            field_name="refrigerant_handling",
            label="Refrigerant Handling",
            recommended_for=["general_liability"],
            importance="medium",
            description="EPA certifications and refrigerant management procedures",
            examples=["All techs EPA 608 certified"],
        ),
        SubmissionRequirement(
            field_name="new_construction_vs_service",
            label="New Construction vs Service",
            recommended_for=["general_liability"],
            importance="medium",
            description="Percentage split between new install and service/repair",
            examples=["70% service, 30% new construction"],
        ),
        SubmissionRequirement(
            field_name="tool_equipment_values",
            label="Tool & Equipment Values",
            recommended_for=["inland_marine"],
            importance="low",
            description="Value of diagnostic tools, recovery machines, etc.",
            examples=["60000"],
        ),
    ]
    return IndustrySubmissionTemplate(
        industry="hvac contractor",
        jurisdiction="general",
        required_fields=required,
        recommended_fields=recommended,
    )


def _build_restaurant_template() -> IndustrySubmissionTemplate:
    required = _common_required() + [
        SubmissionRequirement(
            field_name="cooking_exposure",
            label="Cooking Exposure",
            required_for=["property", "general_liability"],
            importance="critical",
            description="Type of cooking (grilling, frying, open flame), hood/suppression system details",
            examples=["deep frying, commercial grill, Ansul suppression system"],
        ),
        SubmissionRequirement(
            field_name="building_ownership",
            label="Building Ownership",
            required_for=["property"],
            importance="high",
            description="Whether building is owned or leased, square footage",
            examples=["leased, 3200 sq ft", "owned, 4500 sq ft"],
        ),
        SubmissionRequirement(
            field_name="liquor_exposure",
            label="Liquor Exposure",
            required_for=["liquor_liability"],
            importance="high",
            description="Whether alcohol is served, percentage of revenue from alcohol",
            examples=["yes, 25% of revenue", "beer and wine only, 10% of revenue", "no alcohol"],
        ),
    ]
    recommended = _common_recommended() + [
        SubmissionRequirement(
            field_name="delivery_exposure",
            label="Delivery Exposure",
            recommended_for=["commercial_auto", "general_liability"],
            importance="medium",
            description="Whether delivery is offered, own drivers vs third-party",
            examples=["third-party only (DoorDash)", "own drivers, 2 vehicles"],
        ),
        SubmissionRequirement(
            field_name="safety_program",
            label="Safety Program",
            recommended_for=["workers_compensation"],
            importance="medium",
            description="Kitchen safety training and documentation",
            examples=["formal training program", "informal"],
        ),
        SubmissionRequirement(
            field_name="hours_of_operation",
            label="Hours of Operation",
            recommended_for=["general_liability"],
            importance="low",
            description="Business hours and days of operation",
            examples=["Mon-Sat 11am-10pm, Sun 12-8pm"],
        ),
        SubmissionRequirement(
            field_name="seating_capacity",
            label="Seating Capacity",
            recommended_for=["general_liability"],
            importance="low",
            description="Indoor and outdoor seating capacity",
            examples=["85 indoor, 24 patio"],
        ),
    ]
    return IndustrySubmissionTemplate(
        industry="restaurant",
        jurisdiction="general",
        required_fields=required,
        recommended_fields=recommended,
    )


def _build_auto_repair_template() -> IndustrySubmissionTemplate:
    required = _common_required() + [
        SubmissionRequirement(
            field_name="garagekeepers_exposure",
            label="Garagekeepers Exposure",
            required_for=["garagekeepers"],
            importance="critical",
            description="Max number of customer vehicles on premises, highest value vehicle",
            examples=["up to 20 vehicles, max value $80,000"],
        ),
        SubmissionRequirement(
            field_name="building_ownership",
            label="Building Ownership",
            required_for=["property"],
            importance="high",
            description="Owned or leased, building details",
            examples=["owned, 4-bay shop, 5000 sq ft"],
        ),
        SubmissionRequirement(
            field_name="vehicle_count",
            label="Vehicle Count",
            required_for=["commercial_auto"],
            importance="high",
            description="Tow trucks, service vehicles, customer loaners",
            examples=["2 tow trucks, 1 parts runner"],
        ),
    ]
    recommended = _common_recommended() + [
        SubmissionRequirement(
            field_name="services_offered",
            label="Services Offered",
            recommended_for=["general_liability"],
            importance="medium",
            description="Types of repair work performed",
            examples=["general mechanical, brakes, tires, oil changes — no body work"],
        ),
        SubmissionRequirement(
            field_name="safety_program",
            label="Safety Program",
            recommended_for=["workers_compensation"],
            importance="medium",
            description="Shop safety procedures and training",
            examples=["written safety manual, annual training"],
        ),
        SubmissionRequirement(
            field_name="tool_equipment_values",
            label="Tool & Equipment Values",
            recommended_for=["inland_marine"],
            importance="low",
            description="Lifts, diagnostic equipment, specialty tools",
            examples=["120000"],
        ),
    ]
    return IndustrySubmissionTemplate(
        industry="auto repair shop",
        jurisdiction="general",
        required_fields=required,
        recommended_fields=recommended,
    )


def _build_trucking_template() -> IndustrySubmissionTemplate:
    required = _common_required() + [
        SubmissionRequirement(
            field_name="vehicle_count",
            label="Vehicle/Unit Count",
            required_for=["commercial_auto"],
            importance="critical",
            description="Total power units, trailers, and vehicle schedule",
            examples=["18 power units, 24 trailers"],
        ),
        SubmissionRequirement(
            field_name="driver_information",
            label="Driver Information",
            required_for=["commercial_auto"],
            importance="critical",
            description="Number of drivers, CDL status, years of experience, violation history",
            examples=["22 CDL drivers, all 3+ years experience"],
        ),
        SubmissionRequirement(
            field_name="fleet_radius",
            label="Fleet Radius",
            required_for=["commercial_auto"],
            importance="critical",
            description="Operating radius — local, intermediate, or long haul",
            examples=["regional, 500-mile radius", "long haul, 48 states"],
        ),
        SubmissionRequirement(
            field_name="garaging_address",
            label="Garaging Address",
            required_for=["commercial_auto"],
            importance="high",
            description="Where vehicles are garaged overnight",
            examples=["123 Industrial Blvd, Raleigh, NC 27601"],
        ),
        SubmissionRequirement(
            field_name="cargo_types",
            label="Cargo Types",
            required_for=["motor_truck_cargo"],
            importance="critical",
            description="Types of cargo hauled and max load value",
            examples=["general freight, max load $150,000", "refrigerated food products"],
        ),
        SubmissionRequirement(
            field_name="mvr_review_process",
            label="MVR Review Process",
            required_for=["commercial_auto"],
            importance="high",
            description="How motor vehicle records are reviewed and how often",
            examples=["annual MVR review, pre-hire check"],
        ),
    ]
    recommended = _common_recommended() + [
        SubmissionRequirement(
            field_name="safety_program",
            label="Safety Program",
            recommended_for=["workers_compensation", "commercial_auto"],
            importance="medium",
            description="DOT compliance program, safety training, dash cams",
            examples=["full DOT compliance program, ELD equipped, dash cams"],
        ),
        SubmissionRequirement(
            field_name="dot_number",
            label="DOT Number",
            recommended_for=["commercial_auto"],
            importance="medium",
            description="USDOT number and MC authority if applicable",
            examples=["DOT 1234567, MC 654321"],
        ),
        SubmissionRequirement(
            field_name="maintenance_program",
            label="Maintenance Program",
            recommended_for=["commercial_auto"],
            importance="medium",
            description="Preventive maintenance schedule and records",
            examples=["quarterly PM schedule, all records maintained"],
        ),
    ]
    return IndustrySubmissionTemplate(
        industry="trucking company",
        jurisdiction="general",
        required_fields=required,
        recommended_fields=recommended,
    )


# ============================================================
# SEED LOADER
# ============================================================

_TEMPLATE_BUILDERS = [
    _build_roofing_template,
    _build_landscaping_template,
    _build_hvac_template,
    _build_restaurant_template,
    _build_auto_repair_template,
    _build_trucking_template,
]


def _load_seed_templates():
    """Load all industry submission templates into the registry."""
    for builder in _TEMPLATE_BUILDERS:
        template = builder()
        INDUSTRY_SUBMISSION_TEMPLATES[template.industry] = template
    logger.info(
        "Submission templates loaded: %d industries",
        len(INDUSTRY_SUBMISSION_TEMPLATES),
    )


# Auto-load on import
_load_seed_templates()
