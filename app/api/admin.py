"""Admin UI routes - server-rendered HTML pages."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import (
    Source, SourceChunk, ChunkEmbedding, Query,
    GeneratedBrief, FeedbackEvent, RetrievalRun, RetrievalResult,
)
from app.core.enums import SourceType, AuthorityLevel, SourceStatus

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def admin_home(request: Request, db: Session = Depends(get_db)):
    source_count = db.query(Source).count()
    chunk_count = db.query(SourceChunk).count()
    embedding_count = db.query(ChunkEmbedding).count()
    query_count = db.query(Query).count()
    brief_count = db.query(GeneratedBrief).count()
    ready_count = db.query(Source).filter(Source.status == SourceStatus.READY).count()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "source_count": source_count,
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
        "query_count": query_count,
        "brief_count": brief_count,
        "ready_count": ready_count,
    })


@router.get("/sources", response_class=HTMLResponse)
def admin_sources(request: Request, db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.created_at.desc()).limit(100).all()
    return templates.TemplateResponse("sources.html", {
        "request": request,
        "sources": sources,
        "source_types": SourceType.ALL,
        "authority_levels": AuthorityLevel.ALL,
    })


@router.get("/sources/{source_id}", response_class=HTMLResponse)
def admin_source_detail(source_id: UUID, request: Request, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        return HTMLResponse("<h1>Source not found</h1>", status_code=404)

    chunks = db.query(SourceChunk).filter(
        SourceChunk.source_id == source.id
    ).order_by(SourceChunk.chunk_index).all()

    chunk_data = []
    for c in chunks:
        has_emb = db.query(ChunkEmbedding).filter(ChunkEmbedding.chunk_id == c.id).first() is not None
        chunk_data.append({"chunk": c, "has_embedding": has_emb, "tags": c.tags})

    return templates.TemplateResponse("source_detail.html", {
        "request": request,
        "source": source,
        "tags": source.tags,
        "chunks": chunk_data,
    })


@router.get("/workspace", response_class=HTMLResponse)
def admin_workspace(request: Request):
    """Renewal Workspace — unified producer renewal preparation UI."""
    return templates.TemplateResponse("workspace.html", {"request": request})


@router.get("/prep", response_class=HTMLResponse)
def admin_prep_form(request: Request):
    return templates.TemplateResponse("prep.html", {"request": request})


@router.get("/briefs", response_class=HTMLResponse)
def admin_briefs(request: Request, db: Session = Depends(get_db)):
    briefs = db.query(GeneratedBrief).order_by(GeneratedBrief.created_at.desc()).limit(50).all()
    brief_data = []
    for b in briefs:
        query = db.query(Query).filter(Query.id == b.query_id).first()
        brief_data.append({"brief": b, "query": query})
    return templates.TemplateResponse("briefs.html", {
        "request": request,
        "briefs": brief_data,
    })


@router.get("/briefs/{brief_id}", response_class=HTMLResponse)
def admin_brief_detail(brief_id: UUID, request: Request, db: Session = Depends(get_db)):
    brief = db.query(GeneratedBrief).filter(GeneratedBrief.id == brief_id).first()
    if not brief:
        return HTMLResponse("<h1>Brief not found</h1>", status_code=404)

    query = db.query(Query).filter(Query.id == brief.query_id).first()

    # Get retrieval debug info
    run = None
    results = []
    if brief.retrieval_run_id:
        run = db.query(RetrievalRun).filter(RetrievalRun.id == brief.retrieval_run_id).first()
        if run:
            rr = db.query(RetrievalResult).filter(
                RetrievalResult.retrieval_run_id == run.id
            ).order_by(RetrievalResult.rank_position).all()
            for r in rr:
                chunk = db.query(SourceChunk).filter(SourceChunk.id == r.chunk_id).first()
                source = db.query(Source).filter(Source.id == chunk.source_id).first() if chunk else None
                results.append({
                    "result": r,
                    "chunk": chunk,
                    "source": source,
                })

    feedback = db.query(FeedbackEvent).filter(FeedbackEvent.brief_id == brief_id).all()

    return templates.TemplateResponse("brief_detail.html", {
        "request": request,
        "brief": brief,
        "query": query,
        "retrieval_run": run,
        "retrieval_results": results,
        "feedback": feedback,
    })
