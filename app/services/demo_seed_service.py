"""Demo Seed Service — realistic seeded accounts for demo and pilot use.

Provides four demo accounts with enough data to demonstrate the full workflow:
account summary → public intel → coverage gaps → workspace → narrative → submission packet.

Internal-only. Not exposed to production users.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Account, EventLog, DemoFeedback, SavedArtifact
from app.services.instrumentation import log_event

logger = logging.getLogger(__name__)

# Tag to identify demo-seeded accounts
DEMO_NOTES_TAG = "[DEMO-SEED]"

DEMO_ACCOUNTS = [
    {
        "account_name": "Summit Ridge Roofing LLC",
        "industry": "roofing",
        "state": "NC",
        "employee_count": 38,
        "annual_revenue": 4200000,
        "vehicle_count": 12,
        "uses_subcontractors": True,
        "current_coverages": ["general_liability", "workers_comp", "commercial_auto"],
        "website_url": "https://www.summitridgeroofing.com",
        "notes": f"{DEMO_NOTES_TAG} Full-service residential and commercial roofing. "
                 "Crews work at heights daily. Uses 1099 subs for large commercial jobs. "
                 "Experience mod 1.12. Two WC claims in last 3 years (fall from scaffold, knee injury). "
                 "Renewal in 60 days. Producer suspects missing inland marine and umbrella.",
    },
    {
        "account_name": "GreenScape Landscapes Inc",
        "industry": "landscaping",
        "state": "TX",
        "employee_count": 22,
        "annual_revenue": 1800000,
        "vehicle_count": 8,
        "uses_subcontractors": False,
        "current_coverages": ["general_liability", "workers_comp", "commercial_auto"],
        "website_url": "https://www.greenscapetx.com",
        "notes": f"{DEMO_NOTES_TAG} Commercial and residential landscaping, hardscaping, irrigation. "
                 "Seasonal workforce doubles in spring/summer. Operates mowers, skid steers. "
                 "Experience mod 0.92. Clean loss history. "
                 "Renewal in 45 days. No inland marine or EPLI currently.",
    },
    {
        "account_name": "Precision Air HVAC Services",
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
        "website_url": "https://www.precisionairhvac.com",
        "notes": f"{DEMO_NOTES_TAG} Commercial HVAC installation, maintenance, and repair. "
                 "Technicians handle refrigerants (EPA certified). Roof-mounted unit installs. "
                 "Experience mod 1.04. One auto claim (rear-end accident, $22k). "
                 "Renewal in 30 days. Well-insured but may need cyber and pollution.",
    },
    {
        "account_name": "Bella Cucina Restaurant Group",
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
            industry=acct_data["industry"],
            state=acct_data["state"],
            employee_count=acct_data["employee_count"],
            annual_revenue=acct_data["annual_revenue"],
            vehicle_count=acct_data["vehicle_count"],
            uses_subcontractors=acct_data["uses_subcontractors"],
            current_coverages=acct_data["current_coverages"],
            website_url=acct_data["website_url"],
            notes=acct_data["notes"],
        )
        db.add(account)
        db.flush()

        results.append({
            "account_id": str(account.id),
            "account_name": account.account_name,
            "status": "created",
        })

    db.commit()

    log_event(db, "demo_accounts_seeded", payload={
        "count": len(results),
        "created": sum(1 for r in results if r["status"] == "created"),
    })

    logger.info(
        "Demo accounts seeded: %d total, %d new",
        len(results),
        sum(1 for r in results if r["status"] == "created"),
    )
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
    if demo_account_ids:
        artifacts_deleted = (
            db.query(SavedArtifact)
            .filter(SavedArtifact.account_id.in_(demo_account_ids))
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
        "feedback_deleted": feedback_deleted,
        "events_deleted": demo_events_deleted,
    })

    summary = {
        "accounts_deleted": accounts_deleted,
        "artifacts_deleted": artifacts_deleted,
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
