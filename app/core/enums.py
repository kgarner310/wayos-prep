"""Application-level enums and controlled values."""


class SourceType:
    ARTICLE = "article"
    BULLETIN = "bulletin"
    REPORT = "report"
    RESEARCH = "research"
    COURT_CASE = "court_case"
    REGULATORY_GUIDANCE = "regulatory_guidance"
    CARRIER_MATERIAL = "carrier_material"
    TRADE_PUBLICATION = "trade_publication"
    INTERNAL_NOTE = "internal_note"
    USER_NOTE = "user_note"

    ALL = [
        ARTICLE, BULLETIN, REPORT, RESEARCH, COURT_CASE,
        REGULATORY_GUIDANCE, CARRIER_MATERIAL, TRADE_PUBLICATION,
        INTERNAL_NOTE, USER_NOTE,
    ]


class LicenseType:
    PUBLIC = "public"
    LICENSED = "licensed"
    INTERNAL = "internal"
    USER_UPLOADED = "user_uploaded"

    ALL = [PUBLIC, LICENSED, INTERNAL, USER_UPLOADED]


class AuthorityLevel:
    REGULATOR = "regulator"
    COURT = "court"
    STANDARDS_BODY = "standards_body"
    TRADE_ASSOCIATION = "trade_association"
    CARRIER = "carrier"
    JOURNALIST = "journalist"
    RESEARCH_ORG = "research_org"
    INTERNAL = "internal"
    USER = "user"

    ALL = [
        REGULATOR, COURT, STANDARDS_BODY, TRADE_ASSOCIATION,
        CARRIER, JOURNALIST, RESEARCH_ORG, INTERNAL, USER,
    ]

    # Deterministic authority scores by level
    SCORES = {
        REGULATOR: 9.5,
        COURT: 9.0,
        STANDARDS_BODY: 8.5,
        TRADE_ASSOCIATION: 7.5,
        CARRIER: 7.0,
        RESEARCH_ORG: 7.0,
        JOURNALIST: 5.0,
        INTERNAL: 4.0,
        USER: 3.0,
    }


class SourceStatus:
    NEW = "new"
    PARSED = "parsed"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    READY = "ready"
    REJECTED = "rejected"
    ARCHIVED = "archived"

    ALL = [NEW, PARSED, CHUNKED, EMBEDDED, READY, REJECTED, ARCHIVED]


class TagType:
    INDUSTRY = "industry"
    COVERAGE = "coverage"
    RISK_THEME = "risk_theme"
    JURISDICTION = "jurisdiction"
    CLASS_CODE = "class_code"
    ENTITY_TYPE = "entity_type"
    DOCUMENT_TOPIC = "document_topic"
    LOSS_DRIVER = "loss_driver"
    ACCOUNT_TRAIT = "account_trait"

    ALL = [
        INDUSTRY, COVERAGE, RISK_THEME, JURISDICTION,
        CLASS_CODE, ENTITY_TYPE, DOCUMENT_TOPIC, LOSS_DRIVER, ACCOUNT_TRAIT,
    ]


# Starter tag values
STARTER_INDUSTRY_TAGS = [
    "roofing", "trucking", "manufacturing", "habitational", "restaurant",
    "retail", "artisan_contractor", "auto_service", "landscaping", "wholesale",
]

STARTER_COVERAGE_TAGS = [
    "workers_comp", "general_liability", "commercial_auto", "umbrella",
    "property", "builders_risk", "inland_marine", "cyber", "epli",
    "professional_liability",
]

STARTER_RISK_THEME_TAGS = [
    "falls_from_height", "fleet_accidents", "driver_turnover",
    "subcontractor_transfer", "certificate_tracking", "residential_exposure",
    "equipment_theft", "slip_and_fall", "machine_guarding", "combustible_dust",
    "improper_classification", "hired_non_owned_auto",
]

STARTER_ACCOUNT_TRAIT_TAGS = [
    "uses_subcontractors", "multi_state_operations", "high_mod", "young_fleet",
    "heavy_equipment", "residential_work", "habitational_exposure",
    "delivery_operations", "seasonal_payroll", "high_turnover",
]

STARTER_JURISDICTION_TAGS = [
    "federal", "nc", "sc", "ga", "tn", "va", "national", "multi_state",
]
