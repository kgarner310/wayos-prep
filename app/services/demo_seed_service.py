"""Demo Seed Service — realistic seeded accounts for demo and pilot use.

Provides four demo accounts with enough data to demonstrate the full workflow:
account summary → public intel → coverage gaps → workspace → narrative → submission packet.

Internal-only. Not exposed to production users.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.models.models import Account, EventLog, DemoFeedback, SavedArtifact, DealOutcome, AccountHealth
from app.services.instrumentation import log_event
from app.services.health_service import compute_account_health
from app.services.artifact_engine import generate_all_artifacts
from app.services.artifact_service import save_artifact

logger = logging.getLogger(__name__)

# Tag to identify demo-seeded accounts
DEMO_NOTES_TAG = "[DEMO-SEED]"

DEMO_ACCOUNTS = [
    {
        "account_name": "Summit Ridge Roofing LLC",
        "named_insured": "Summit Ridge Roofing LLC",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 38,
        "annual_revenue": 4200000,
        "vehicle_count": 12,
        "uses_subcontractors": True,
        "current_coverages": ["general_liability", "workers_comp", "commercial_auto"],
        "workers_comp_mod": 1.12,
        "payroll_estimate": 1900000,
        "current_carriers": ["Travelers", "Builders Mutual"],
        "claims_summary": {"open_claims": 1, "total_claims_3yr": 2, "details": "Fall from scaffold ($45k), knee injury ($12k)"},
        "website_url": "https://www.summitridgeroofing.com",
        "notes": f"{DEMO_NOTES_TAG} Full-service residential and commercial roofing. "
                 "Crews work at heights daily. Uses 1099 subs for large commercial jobs. "
                 "Experience mod 1.12. Two WC claims in last 3 years (fall from scaffold, knee injury). "
                 "Renewal in 60 days. Producer suspects missing inland marine and umbrella.",
    },
    {
        "account_name": "GreenScape Landscapes Inc",
        "named_insured": "GreenScape Landscapes Inc",
        "industry": "landscaping",
        "state": "TX",
        "employee_count": 22,
        "annual_revenue": 1800000,
        "vehicle_count": 8,
        "uses_subcontractors": False,
        "current_coverages": ["general_liability", "workers_comp", "commercial_auto"],
        "workers_comp_mod": 0.92,
        "payroll_estimate": 880000,
        "current_carriers": ["Cincinnati", "Guard Insurance"],
        "claims_summary": {"open_claims": 0, "total_claims_3yr": 0},
        "website_url": "https://www.greenscapetx.com",
        "notes": f"{DEMO_NOTES_TAG} Commercial and residential landscaping, hardscaping, irrigation. "
                 "Seasonal workforce doubles in spring/summer. Operates mowers, skid steers. "
                 "Experience mod 0.92. Clean loss history. "
                 "Renewal in 45 days. No inland marine or EPLI currently.",
    },
    {
        "account_name": "Precision Air HVAC Services",
        "named_insured": "Precision Air HVAC Services LLC",
        "industry": "hvac",
        "state": "FL",
        "employee_count": 45,
        "annual_revenue": 6500000,
        "vehicle_count": 18,
        "uses_subcontractors": True,
        "current_coverages": [
            "general_liability", "workers_comp", "commercial_auto",
            "inland_marine", "professional_liability",
        ],
        "workers_comp_mod": 1.04,
        "payroll_estimate": 2400000,
        "current_carriers": ["Hartford", "Zurich", "Employers"],
        "claims_summary": {"open_claims": 0, "total_claims_3yr": 1, "details": "Auto rear-end accident ($22k)"},
        "website_url": "https://www.precisionairhvac.com",
        "notes": f"{DEMO_NOTES_TAG} Commercial HVAC installation, maintenance, and repair. "
                 "Technicians handle refrigerants (EPA certified). Roof-mounted unit installs. "
                 "Experience mod 1.04. One auto claim (rear-end accident, $22k). "
                 "Renewal in 30 days. Well-insured but may need cyber and pollution.",
    },
    {
        "account_name": "Bella Cucina Restaurant Group",
        "named_insured": "Bella Cucina Restaurant Group Inc",
        "industry": "restaurant",
        "state": "CA",
        "employee_count": 65,
        "annual_revenue": 3800000,
        "vehicle_count": 2,
        "uses_subcontractors": False,
        "current_coverages": [
            "general_liability", "workers_comp", "commercial_property",
            "liquor_liability",
        ],
        "workers_comp_mod": 1.08,
        "payroll_estimate": 1600000,
        "current_carriers": ["State Fund", "Zenith"],
        "claims_summary": {"open_claims": 1, "total_claims_3yr": 2, "details": "Slip-and-fall ($15k), kitchen burn ($8k)"},
        "website_url": "https://www.bellacucinagroup.com",
        "notes": f"{DEMO_NOTES_TAG} Three-location Italian restaurant group. Full bar service. "
                 "Catering operations with delivery. High employee turnover. "
                 "Experience mod 1.08. Slip-and-fall claim ($15k) and kitchen burn ($8k). "
                 "Renewal in 90 days. No EPLI, cyber, or commercial auto for catering van.",
    },
]


def seed_demo_accounts(db: Session) -> list[dict]:
    """Seed demo accounts into the database.

    Returns list of created account summaries. Skips accounts that already
    exist (matched by name + DEMO_NOTES_TAG in notes).
    """
    results = []

    for acct_data in DEMO_ACCOUNTS:
        # Check if already exists
        existing = (
            db.query(Account)
            .filter(Account.account_name == acct_data["account_name"])
            .filter(Account.notes.contains(DEMO_NOTES_TAG))
            .first()
        )
        if existing:
            results.append({
                "account_id": str(existing.id),
                "account_name": existing.account_name,
                "status": "already_exists",
            })
            continue

        account = Account(
            account_name=acct_data["account_name"],
            named_insured=acct_data.get("named_insured"),
            industry=acct_data["industry"],
            state=acct_data["state"],
            employee_count=acct_data["employee_count"],
            annual_revenue=acct_data["annual_revenue"],
            vehicle_count=acct_data["vehicle_count"],
            uses_subcontractors=acct_data["uses_subcontractors"],
            current_coverages=acct_data["current_coverages"],
            workers_comp_mod=acct_data.get("workers_comp_mod"),
            payroll_estimate=acct_data.get("payroll_estimate"),
            current_carriers=acct_data.get("current_carriers"),
            claims_summary=acct_data.get("claims_summary"),
            website_url=acct_data["website_url"],
            notes=acct_data["notes"],
        )
        db.add(account)
        db.flush()

        # Seed public web intel so Operations Signals show on first workspace load
        intel_seeded = _seed_public_intel(db, account)

        results.append({
            "account_id": str(account.id),
            "account_name": account.account_name,
            "status": "created",
            "public_intel_seeded": intel_seeded,
        })

    db.commit()

    # Generate health cards, artifacts, and outcomes for demo accounts
    created_count = sum(1 for r in results if r["status"] == "created")
    if created_count > 0:
        try:
            seed_demo_artifacts(db)
        except Exception:
            logger.exception("Failed to seed demo artifacts")

        try:
            seed_demo_outcomes(db)
        except Exception:
            logger.exception("Failed to seed demo outcomes")

    log_event(db, "demo_accounts_seeded", payload={
        "count": len(results),
        "created": created_count,
    })

    logger.info(
        "Demo accounts seeded: %d total, %d new",
        len(results),
        created_count,
    )
    return results


def seed_demo_artifacts(db: Session) -> list[dict]:
    """Generate health cards and artifacts for all demo accounts.

    For each demo account:
    1. Computes health card via compute_account_health
    2. Generates all artifacts via generate_all_artifacts (deterministic, no LLM)

    Returns summary of what was created.
    """
    demo_accounts = (
        db.query(Account)
        .filter(Account.notes.contains(DEMO_NOTES_TAG))
        .all()
    )

    results = []
    for account in demo_accounts:
        try:
            # Compute health card
            health = compute_account_health(account, db)

            # Generate all artifacts (deterministic only)
            artifacts = generate_all_artifacts(account.id, db, use_llm=False)

            results.append({
                "account_id": str(account.id),
                "account_name": account.account_name,
                "health_score": health.overall_score,
                "artifacts_created": len(artifacts),
                "artifact_types": [a.artifact_type for a in artifacts],
            })
        except Exception:
            logger.exception("Failed to seed artifacts for %s", account.account_name)
            results.append({
                "account_id": str(account.id),
                "account_name": account.account_name,
                "status": "failed",
            })

    db.commit()

    logger.info(
        "Demo artifacts seeded: %d accounts processed",
        len(results),
    )
    return results


def seed_demo_outcomes(db: Session) -> list[dict]:
    """Create demo DealOutcome records for market intelligence.

    Creates 5 demo outcomes across different industries, carriers, and results
    to populate market signals and win rate data.

    Returns summary of created outcomes.
    """
    demo_outcomes = [
        {
            "account_id": "demo-roofing-001",
            "industry": "roofing",
            "state": "NC",
            "carrier": "Travelers",
            "premium": 68000,
            "outcome": "won",
            "outcome_reason": "COVERAGE",
            "competitor": "Builders Mutual",
            "notes": "Won with broader sub coverage and competitive mod credit.",
        },
        {
            "account_id": "demo-roofing-002",
            "industry": "roofing",
            "state": "NC",
            "carrier": "Builders Mutual",
            "premium": 55000,
            "outcome": "lost",
            "outcome_reason": "PRICE",
            "competitor": "Employers",
            "notes": "Lost by 12% on price. Incumbent relationship strong.",
        },
        {
            "account_id": "demo-landscaping-001",
            "industry": "landscaping",
            "state": "TX",
            "carrier": "Cincinnati",
            "premium": 32000,
            "outcome": "won",
            "outcome_reason": "RELATIONSHIP",
            "competitor": None,
            "notes": "Clean account. Won on service and relationship.",
        },
        {
            "account_id": "demo-hvac-001",
            "industry": "hvac",
            "state": "FL",
            "carrier": "Hartford",
            "premium": 95000,
            "outcome": "won",
            "outcome_reason": "COVERAGE",
            "competitor": "Zurich",
            "notes": "Won with pollution coverage inclusion that competitor excluded.",
        },
        {
            "account_id": "demo-restaurant-001",
            "industry": "restaurant",
            "state": "CA",
            "carrier": "State Fund",
            "premium": 42000,
            "outcome": "lost",
            "outcome_reason": "APPETITE",
            "competitor": "EMPLOYERS",
            "notes": "Carrier declined due to claims frequency concerns.",
        },
    ]

    results = []
    for outcome_data in demo_outcomes:
        try:
            outcome = DealOutcome(**outcome_data)
            db.add(outcome)
            db.flush()
            results.append({
                "outcome_id": str(outcome.id),
                "industry": outcome.industry,
                "carrier": outcome.carrier,
                "outcome": outcome.outcome,
                "status": "created",
            })
        except Exception:
            logger.exception("Failed to seed demo outcome: %s", outcome_data)

    db.commit()

    logger.info("Demo outcomes seeded: %d created", len(results))
    return results


def reset_demo_data(db: Session) -> dict:
    """Reset demo data: delete demo-seeded accounts and their artifacts.

    Also clears demo feedback and demo session events. Returns summary of
    what was cleaned up.
    """
    # Find demo accounts
    demo_accounts = (
        db.query(Account)
        .filter(Account.notes.contains(DEMO_NOTES_TAG))
        .all()
    )
    demo_account_ids = [a.id for a in demo_accounts]

    # Delete artifacts for demo accounts
    artifacts_deleted = 0
    health_deleted = 0
    if demo_account_ids:
        artifacts_deleted = (
            db.query(SavedArtifact)
            .filter(SavedArtifact.account_id.in_(demo_account_ids))
            .delete(synchronize_session="fetch")
        )
        health_deleted = (
            db.query(AccountHealth)
            .filter(AccountHealth.account_id.in_(demo_account_ids))
            .delete(synchronize_session="fetch")
        )

    # Delete demo deal outcomes
    demo_outcomes_deleted = (
        db.query(DealOutcome)
        .filter(DealOutcome.account_id.like("demo-%"))
        .delete(synchronize_session="fetch")
    )

    # Delete demo accounts
    accounts_deleted = 0
    for acct in demo_accounts:
        db.delete(acct)
        accounts_deleted += 1

    # Clear demo feedback
    feedback_deleted = db.query(DemoFeedback).delete()

    # Clear demo session events (events with session_id starting with "demo_")
    demo_events_deleted = (
        db.query(EventLog)
        .filter(EventLog.event_type.in_([
            "demo_accounts_seeded", "demo_data_reset",
            "demo_session_started", "demo_feedback_submitted",
        ]))
        .delete(synchronize_session="fetch")
    )

    db.commit()

    log_event(db, "demo_data_reset", payload={
        "accounts_deleted": accounts_deleted,
        "artifacts_deleted": artifacts_deleted,
        "health_deleted": health_deleted,
        "outcomes_deleted": demo_outcomes_deleted,
        "feedback_deleted": feedback_deleted,
        "events_deleted": demo_events_deleted,
    })

    summary = {
        "accounts_deleted": accounts_deleted,
        "artifacts_deleted": artifacts_deleted,
        "health_deleted": health_deleted,
        "outcomes_deleted": demo_outcomes_deleted,
        "feedback_deleted": feedback_deleted,
        "events_deleted": demo_events_deleted,
    }
    logger.info("Demo data reset: %s", summary)
    return summary


def list_demo_scenarios() -> list[dict]:
    """Return available demo scenarios with descriptions."""
    scenarios = []
    for acct in DEMO_ACCOUNTS:
        scenarios.append({
            "account_name": acct["account_name"],
            "industry": acct["industry"],
            "state": acct["state"],
            "employee_count": acct["employee_count"],
            "annual_revenue": acct["annual_revenue"],
            "key_exposures": _get_key_exposures(acct["industry"]),
            "likely_gaps": _get_likely_gaps(acct),
            "demo_story": _get_demo_story(acct["industry"]),
        })
    return scenarios


def get_demo_accounts(db: Session) -> list[dict]:
    """List all demo-seeded accounts currently in the database."""
    accounts = (
        db.query(Account)
        .filter(Account.notes.contains(DEMO_NOTES_TAG))
        .order_by(Account.account_name)
        .all()
    )
    return [
        {
            "account_id": str(a.id),
            "account_name": a.account_name,
            "industry": a.industry,
            "state": a.state,
            "employee_count": a.employee_count,
            "has_website": bool(a.website_url),
            "coverage_count": len(a.current_coverages) if a.current_coverages else 0,
            "has_intel": a.last_public_intel_refresh_at is not None,
        }
        for a in accounts
    ]


# ============================================================
# PRE-BUILT PUBLIC WEB INTEL FOR DEMO ACCOUNTS
# ============================================================
# Synthetic intel that would normally come from a live website fetch.
# Keyed by account_name to match DEMO_ACCOUNTS entries.

_DEMO_PUBLIC_INTEL: dict[str, dict] = {
    "Summit Ridge Roofing LLC": {
        "company_identity": {
            "company_name": "Summit Ridge Roofing LLC",
            "founded_year": 2011,
            "service_area": ["Charlotte metro", "Raleigh-Durham", "Western NC"],
        },
        "operations_signals": [
            "Offers residential and commercial roofing services",
            "Performs full tear-off and re-roof projects",
            "Provides emergency storm damage repairs",
            "Advertises metal roofing and standing seam installation",
            "Uses subcontractors for large commercial projects",
        ],
        "safety_signals": [
            "OSHA 10-hour training referenced for all crew members",
            "Fall protection program mentioned on careers page",
            "Ladder safety and harness protocols highlighted",
        ],
        "scale_signals": [
            "12 service vehicles listed on fleet page",
            "Serves 3-county region from single office location",
            "Seasonal crews scale to 50+ during storm season",
        ],
        "carrier_relevant_signals": [
            "Uses 1099 subcontractors for commercial tear-off work",
            "Recent storm damage repair volume suggests CAT exposure",
            "Height work across all project types — consistent fall risk",
            "Tool and material staging on-site — inland marine exposure",
        ],
        "observed_signals": [
            "Recent project activity posted",
            "Active hiring activity",
            "Storm/weather response activity",
        ],
        "cautions": [
            "Public content may reflect marketing language and should not be treated as independently verified fact",
        ],
    },
    "GreenScape Landscapes Inc": {
        "company_identity": {
            "company_name": "GreenScape Landscapes Inc",
            "founded_year": 2016,
            "service_area": ["Dallas-Fort Worth", "North Texas"],
        },
        "operations_signals": [
            "Commercial and residential landscape design and installation",
            "Hardscaping services including retaining walls and patios",
            "Irrigation system installation and maintenance",
            "Seasonal lawn care and mowing programs",
            "Tree trimming and removal services advertised",
        ],
        "safety_signals": [
            "Pesticide applicator licensing mentioned",
            "Heat illness prevention program referenced",
        ],
        "scale_signals": [
            "8 trucks and trailers listed on about page",
            "Workforce doubles in spring/summer per careers page",
            "Serves residential HOAs and commercial property managers",
        ],
        "carrier_relevant_signals": [
            "Operates heavy equipment (skid steers, mini excavators) on client sites",
            "Chemical application for weed and pest control — pollution exposure",
            "Seasonal workforce surge creates hiring/training risk",
            "Equipment transported on open trailers — theft and transit exposure",
        ],
        "observed_signals": [
            "Recent project activity posted",
            "Community involvement activity",
        ],
        "cautions": [
            "Public content may reflect marketing language and should not be treated as independently verified fact",
        ],
    },
    "Precision Air HVAC Services": {
        "company_identity": {
            "company_name": "Precision Air HVAC Services LLC",
            "founded_year": 2008,
            "service_area": ["South Florida", "Miami-Dade", "Broward", "Palm Beach"],
        },
        "operations_signals": [
            "Commercial HVAC installation for office and retail buildings",
            "Rooftop unit (RTU) installation and replacement",
            "Refrigeration system service for restaurants and cold storage",
            "24/7 emergency repair service advertised",
            "Preventive maintenance contracts offered",
        ],
        "safety_signals": [
            "EPA Section 608 Universal certification required for all techs",
            "Rooftop safety protocols mentioned for RTU work",
            "Electrical lockout/tagout procedures referenced",
        ],
        "scale_signals": [
            "18 service vans in branded fleet",
            "45 employees across installation and service divisions",
            "3 locations across South Florida",
        ],
        "carrier_relevant_signals": [
            "Refrigerant handling creates pollution/environmental liability exposure",
            "Rooftop work on commercial buildings — fall exposure",
            "Fleet of 18 vehicles with daily windshield time — auto frequency risk",
            "Subcontractors used for ductwork fabrication — sub default exposure",
            "Customer data from maintenance contracts — potential cyber exposure",
        ],
        "observed_signals": [
            "Active hiring activity",
            "Expansion or growth signals",
            "Training or safety event activity",
        ],
        "cautions": [
            "Public content may reflect marketing language and should not be treated as independently verified fact",
        ],
    },
    "Bella Cucina Restaurant Group": {
        "company_identity": {
            "company_name": "Bella Cucina Restaurant Group Inc",
            "founded_year": 2014,
            "service_area": ["Los Angeles", "Santa Monica", "Pasadena"],
        },
        "operations_signals": [
            "Three full-service Italian restaurant locations",
            "Full bar and cocktail program at all locations",
            "Catering services with on-site delivery offered",
            "Private event and banquet hosting advertised",
            "Online ordering and delivery partnerships active",
        ],
        "safety_signals": [
            "Food safety certifications mentioned (ServSafe)",
            "Kitchen fire suppression systems referenced",
        ],
        "scale_signals": [
            "65 employees across three locations",
            "2 catering/delivery vehicles",
            "Open 7 days with lunch and dinner service",
        ],
        "carrier_relevant_signals": [
            "Full liquor service at 3 locations — dram shop exposure",
            "Catering delivery creates off-premises auto and GL exposure",
            "High employee turnover in food service — EPLI exposure",
            "Customer credit card processing — PCI/cyber exposure",
            "Commercial cooking at scale — fire and property damage risk",
        ],
        "observed_signals": [
            "Recent project activity posted",
            "Community involvement activity",
            "Awards or recognition posted",
        ],
        "cautions": [
            "Public content may reflect marketing language and should not be treated as independently verified fact",
        ],
    },
}


def _seed_public_intel(db: Session, account) -> bool:
    """Seed pre-built public web intel artifact for a demo account.

    Creates a SavedArtifact with artifact_type='public_web_intel' containing
    realistic pre-built intel, so the workspace Operations Signals section
    is populated immediately without requiring a live web fetch.

    Returns True if artifact was created, False otherwise.
    """
    intel_data = _DEMO_PUBLIC_INTEL.get(account.account_name)
    if not intel_data:
        return False

    try:
        save_artifact(db, {
            "account_id": account.id,
            "artifact_type": "public_web_intel",
            "artifact_subtype": "demo_seed",
            "title": f"Public Web Intel — {account.account_name}",
            "content_json": {
                "public_web_intel": intel_data,
                "fetch_metadata": {
                    "source_url": account.website_url or "",
                    "fetched_urls": [account.website_url] if account.website_url else [],
                    "fetch_warnings": ["Pre-seeded demo data — not from live web fetch"],
                    "refresh_timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        })
        return True
    except Exception:
        logger.warning(
            "Failed to seed public intel artifact for %s",
            account.account_name, exc_info=True,
        )
        return False


def _get_key_exposures(industry: str) -> list[str]:
    """Return key exposure areas for an industry."""
    exposures = {
        "roofing": ["falls from height", "subcontractor liability", "property damage", "tool/equipment theft"],
        "landscaping": ["equipment operation", "chemical application", "seasonal workforce", "vehicle accidents"],
        "hvac": ["refrigerant handling", "rooftop work", "electrical hazards", "vehicle fleet"],
        "restaurant": ["slip-and-fall", "foodborne illness", "liquor liability", "employee injuries"],
    }
    return exposures.get(industry, ["general operations"])


def _get_likely_gaps(acct: dict) -> list[str]:
    """Return likely coverage gaps based on industry and current coverages."""
    current = set(acct.get("current_coverages", []))
    gaps = {
        "roofing": ["inland_marine", "umbrella", "professional_liability", "cyber_liability"],
        "landscaping": ["inland_marine", "epli", "pollution_liability", "umbrella"],
        "hvac": ["cyber_liability", "pollution_liability", "umbrella"],
        "restaurant": ["epli", "cyber_liability", "commercial_auto", "umbrella"],
    }
    industry_gaps = gaps.get(acct.get("industry", ""), [])
    return [g for g in industry_gaps if g not in current]


def _get_demo_story(industry: str) -> str:
    """Return a brief demo narrative for the industry."""
    stories = {
        "roofing": "Roofer with sub exposure and recent WC claims — classic gap discovery scenario.",
        "landscaping": "Clean landscaper missing equipment and employment practices coverage.",
        "hvac": "Well-insured HVAC contractor that still needs cyber and pollution.",
        "restaurant": "Multi-location restaurant group with catering ops and coverage blind spots.",
    }
    return stories.get(industry, "General commercial account for demo.")
