import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import api_key_auth
from app.models.industry import IndustryRiskProfile
from app.models.query_log import QueryLog
from app.models.feedback import Feedback
from app.models.state_profile import StateProfile
from app.models.loss_run import LossRunReview
from app.models.experience_mod import ExperienceModReview
from app.models.account import Account
from app.schemas import (
    IndustryOut,
    IndustryListItem,
    AskRequest,
    PrepRequest,
    BriefResponse,
    FeedbackRequest,
    FeedbackOut,
    StateProfileListItem,
    StateProfileOut,
    LossRunRequest,
    LossRunAnalysis,
    ExperienceModRequest,
    ExperienceModAnalysis,
    AccountCreate,
    AccountUpdate,
    AccountListItem,
    AccountOut,
    AccountDetail,
)
from app.services.industry_matcher import match_industry
from app.services.brief_generator import generate_brief
from app.services.loss_run_analyzer import analyze_loss_runs, render_loss_run_text
from app.services.experience_mod_analyzer import analyze_experience_mod, render_experience_mod_text

router = APIRouter()


def _find_or_create_account(account_name: str, db: Session) -> Account:
    """Find an existing account by name or create a new one."""
    account = db.query(Account).filter(
        sa.func.lower(Account.name) == account_name.lower().strip()
    ).first()
    if not account:
        account = Account(name=account_name.strip())
        db.add(account)
        db.flush()
    return account


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(sa.text("SELECT 1"))
        return {"status": "ok", "service": "wayos-prep", "database": "connected"}
    except Exception:
        return {"status": "degraded", "service": "wayos-prep", "database": "unavailable"}


@router.get("/industries", response_model=list[IndustryListItem])
def list_industries(
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    return db.query(IndustryRiskProfile).order_by(IndustryRiskProfile.industry_name).all()


@router.get("/industries/{industry_id}", response_model=IndustryOut)
def get_industry(
    industry_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    profile = db.query(IndustryRiskProfile).filter(IndustryRiskProfile.id == industry_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Industry not found")
    return profile


@router.post("/briefs/ask", response_model=BriefResponse)
def ask_brief(
    req: AskRequest,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    profile = match_industry(req.question, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Could not identify an industry from your question. Try being more specific.")

    location = req.location or "Not specified"
    log = generate_brief(
        profile=profile,
        location=location,
        employee_count=None,
        mod=None,
        vehicle_exposure=None,
        query_type="ask",
        raw_question=req.question,
        db=db,
    )
    return _log_to_response(log)


@router.post("/briefs/prep", response_model=BriefResponse)
def prep_brief(
    req: PrepRequest,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    profile = match_industry(req.industry, db)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Industry '{req.industry}' not found.")

    log = generate_brief(
        profile=profile,
        location=req.location,
        employee_count=req.employee_count,
        mod=req.mod,
        vehicle_exposure=req.vehicle_exposure,
        query_type="prep",
        raw_question=None,
        db=db,
    )
    return _log_to_response(log)


@router.get("/briefs/{brief_id}", response_model=BriefResponse)
def get_brief(
    brief_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    log = db.query(QueryLog).filter(QueryLog.id == brief_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Brief not found")
    return _log_to_response(log)


@router.post("/feedback", response_model=FeedbackOut)
def create_feedback(
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    log = db.query(QueryLog).filter(QueryLog.id == req.query_log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Query log not found")

    fb = Feedback(
        query_log_id=req.query_log_id,
        helpful_bool=req.helpful_bool,
        note_text=req.note_text,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("/states", response_model=list[StateProfileListItem])
def list_states(
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    return db.query(StateProfile).order_by(StateProfile.state_name).all()


@router.get("/states/{state_code}", response_model=StateProfileOut)
def get_state(
    state_code: str,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    profile = db.query(StateProfile).filter(
        StateProfile.state_code == state_code.upper()
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"State '{state_code}' not found")
    return profile


# --- Accounts ---


@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(
    req: AccountCreate,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    existing = db.query(Account).filter(
        sa.func.lower(Account.name) == req.name.lower().strip()
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Account '{req.name}' already exists")

    account = Account(**req.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts", response_model=list[AccountListItem])
def list_accounts(
    renewal_status: str | None = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    q = db.query(Account).order_by(Account.name)
    if renewal_status:
        q = q.filter(Account.renewal_status == renewal_status)
    return q.all()


@router.get("/accounts/renewals", response_model=list[AccountListItem])
def list_upcoming_renewals(
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    return (
        db.query(Account)
        .filter(Account.policy_expiration.isnot(None))
        .order_by(Account.policy_expiration)
        .all()
    )


@router.get("/accounts/{account_id}", response_model=AccountDetail)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/accounts/{account_id}", response_model=AccountOut)
def update_account(
    account_id: int,
    req: AccountUpdate,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()


# --- Account Review (combined brief with loss run + mod data) ---


@router.post("/accounts/{account_id}/review", response_model=BriefResponse)
def generate_account_review(
    account_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    """Generate a full account review brief that incorporates loss run and mod data."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not account.industry:
        raise HTTPException(status_code=400, detail="Account must have an industry set to generate a review")
    if not account.location:
        raise HTTPException(status_code=400, detail="Account must have a location set to generate a review")

    profile = match_industry(account.industry, db)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Industry '{account.industry}' not found")

    # Get latest loss run and mod reviews for this account
    latest_loss_run = (
        db.query(LossRunReview)
        .filter(LossRunReview.account_id == account_id)
        .order_by(LossRunReview.timestamp.desc())
        .first()
    )
    latest_mod = (
        db.query(ExperienceModReview)
        .filter(ExperienceModReview.account_id == account_id)
        .order_by(ExperienceModReview.timestamp.desc())
        .first()
    )

    # Use account mod or latest mod review
    mod = account.current_mod
    if latest_mod and latest_mod.current_mod:
        mod = latest_mod.current_mod

    log = generate_brief(
        profile=profile,
        location=account.location,
        employee_count=account.employee_count,
        mod=mod,
        vehicle_exposure=account.vehicle_exposure,
        query_type="account_review",
        raw_question=None,
        db=db,
        loss_run_data=latest_loss_run.analysis_json if latest_loss_run else None,
        mod_data=latest_mod.analysis_json if latest_mod else None,
    )

    # Link to account
    log.account_id = account_id
    db.commit()

    return _log_to_response(log)


# --- Loss Runs ---


@router.post("/loss-runs", response_model=LossRunAnalysis)
def create_loss_run_review(
    req: LossRunRequest,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    entries = [e.model_dump() for e in req.line_entries]
    analysis = analyze_loss_runs(entries)

    totals = analysis.get("totals", {})
    analysis_text = render_loss_run_text(analysis, req.account_name)
    talking_points = "\n".join(f"• {p}" for p in analysis.get("talking_points", []))

    industry_id = None
    if req.industry:
        profile = match_industry(req.industry, db)
        if profile:
            industry_id = profile.id

    # Auto-link to account
    account = _find_or_create_account(req.account_name, db)

    review = LossRunReview(
        account_name=req.account_name,
        account_id=account.id,
        policy_period_start=req.policy_period_start,
        policy_period_end=req.policy_period_end,
        industry_id=industry_id,
        location=req.location,
        line_entries=entries,
        analysis_json=analysis,
        analysis_text=analysis_text,
        talking_points=talking_points,
        total_incurred=totals.get("incurred"),
        total_claims=totals.get("claims"),
        loss_ratio=totals.get("loss_ratio"),
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get("/loss-runs/{review_id}", response_model=LossRunAnalysis)
def get_loss_run_review(
    review_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    review = db.query(LossRunReview).filter(LossRunReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Loss run review not found")
    return review


# --- Experience Mod ---


@router.post("/experience-mod", response_model=ExperienceModAnalysis)
def create_experience_mod_review(
    req: ExperienceModRequest,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    analysis = analyze_experience_mod(
        current_mod=req.current_mod,
        prior_mod=req.prior_mod,
        expected_losses=req.expected_losses,
        actual_primary_losses=req.actual_primary_losses,
        actual_excess_losses=req.actual_excess_losses,
        total_payroll=req.total_payroll,
        class_code_entries=[e.model_dump() for e in req.class_code_entries] if req.class_code_entries else None,
        mod_claims=[c.model_dump() for c in req.mod_claims] if req.mod_claims else None,
    )

    analysis_text = render_experience_mod_text(analysis, req.account_name)
    talking_points = "\n".join(f"• {p}" for p in analysis.get("talking_points", []))

    # Auto-link to account
    account = _find_or_create_account(req.account_name, db)

    review = ExperienceModReview(
        account_name=req.account_name,
        account_id=account.id,
        state_code=req.state_code.upper() if req.state_code else None,
        effective_date=req.effective_date,
        current_mod=req.current_mod,
        prior_mod=req.prior_mod,
        expected_losses=req.expected_losses,
        actual_primary_losses=req.actual_primary_losses,
        actual_excess_losses=req.actual_excess_losses,
        total_payroll=req.total_payroll,
        class_code_entries=[e.model_dump() for e in req.class_code_entries] if req.class_code_entries else None,
        mod_claims=[c.model_dump() for c in req.mod_claims] if req.mod_claims else None,
        analysis_json=analysis,
        analysis_text=analysis_text,
        talking_points=talking_points,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get("/experience-mod/{review_id}", response_model=ExperienceModAnalysis)
def get_experience_mod_review(
    review_id: int,
    db: Session = Depends(get_db),
    _auth: str | None = Depends(api_key_auth),
):
    review = db.query(ExperienceModReview).filter(ExperienceModReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Experience mod review not found")
    return review


def _log_to_response(log: QueryLog) -> dict:
    return {
        "id": log.id,
        "brief_json": log.brief_json,
        "brief_text": log.brief_text,
        "underwriter_email_text": log.underwriter_email_text,
        "internal_note_text": log.internal_note_text,
    }
