import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.industry import IndustryRiskProfile
from app.models.query_log import QueryLog
from app.models.feedback import Feedback
from app.schemas import (
    IndustryOut,
    IndustryListItem,
    AskRequest,
    PrepRequest,
    BriefResponse,
    FeedbackRequest,
    FeedbackOut,
)
from app.services.industry_matcher import match_industry
from app.services.brief_generator import generate_brief

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(sa.text("SELECT 1"))
        return {"status": "ok", "service": "wayos-prep", "database": "connected"}
    except Exception:
        return {"status": "degraded", "service": "wayos-prep", "database": "unavailable"}


@router.get("/industries", response_model=list[IndustryListItem])
def list_industries(db: Session = Depends(get_db)):
    return db.query(IndustryRiskProfile).order_by(IndustryRiskProfile.industry_name).all()


@router.get("/industries/{industry_id}", response_model=IndustryOut)
def get_industry(industry_id: int, db: Session = Depends(get_db)):
    profile = db.query(IndustryRiskProfile).filter(IndustryRiskProfile.id == industry_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Industry not found")
    return profile


@router.post("/briefs/ask", response_model=BriefResponse)
def ask_brief(req: AskRequest, db: Session = Depends(get_db)):
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
def prep_brief(req: PrepRequest, db: Session = Depends(get_db)):
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
def get_brief(brief_id: int, db: Session = Depends(get_db)):
    log = db.query(QueryLog).filter(QueryLog.id == brief_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Brief not found")
    return _log_to_response(log)


@router.post("/feedback", response_model=FeedbackOut)
def create_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
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


def _log_to_response(log: QueryLog) -> dict:
    return {
        "id": log.id,
        "brief_json": log.brief_json,
        "brief_text": log.brief_text,
        "underwriter_email_text": log.underwriter_email_text,
        "internal_note_text": log.internal_note_text,
    }
