"""Account persistence service."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import Account

logger = logging.getLogger(__name__)


def create_account(db: Session, data: dict) -> Account:
    """Create a new account."""
    account = Account(
        account_name=data["account_name"],
        named_insured=data.get("named_insured"),
        industry=data.get("industry"),
        state=data.get("state"),
        employee_count=data.get("employee_count"),
        annual_revenue=data.get("annual_revenue"),
        vehicle_count=data.get("vehicle_count"),
        uses_subcontractors=data.get("uses_subcontractors", False),
        current_coverages=data.get("current_coverages"),
        payroll_estimate=data.get("payroll_estimate"),
        workers_comp_mod=data.get("workers_comp_mod"),
        current_carriers=data.get("current_carriers"),
        claims_summary=data.get("claims_summary"),
        extracted_text=data.get("extracted_text"),
        website_url=data.get("website_url"),
        social_urls=data.get("social_urls"),
        notes=data.get("notes"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    logger.info("Account created: id=%s name=%s", account.id, account.account_name)
    return account


def get_account(db: Session, account_id: UUID) -> Account | None:
    """Get an account by ID."""
    return db.query(Account).filter(Account.id == account_id).first()


def list_accounts(db: Session, limit: int = 50, offset: int = 0) -> tuple[list[Account], int]:
    """List accounts with pagination."""
    total = db.query(Account).count()
    accounts = (
        db.query(Account)
        .order_by(Account.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return accounts, total


def update_account(db: Session, account_id: UUID, data: dict) -> Account | None:
    """Update an account. Only non-None fields are updated."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return None

    for key, value in data.items():
        if value is not None and hasattr(account, key):
            setattr(account, key, value)

    db.commit()
    db.refresh(account)
    logger.info("Account updated: id=%s", account.id)
    return account


def delete_account(db: Session, account_id: UUID) -> bool:
    """Delete an account. Returns True if deleted."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return False
    db.delete(account)
    db.commit()
    logger.info("Account deleted: id=%s", account_id)
    return True
