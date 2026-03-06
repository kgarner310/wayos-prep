"""API endpoints for WAYOS PREP."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.enums import SourceStatus
from app.models.models import (
    Source, SourceChunk, ChunkEmbedding, Query,
    GeneratedBrief, FeedbackEvent, RetrievalRun, RetrievalResult,
)
from app.schemas.schemas import (
    SourceIngestText, SourceIngestURL, SourceResponse, SourceDetailResponse,
    TagResponse, ChunkResponse, PrepQueryRequest, PrepQueryResponse,
    FeedbackRequest, FeedbackResponse,
    RetrievalDebugResponse, RetrievalDebugResult,
)
from app.services.ingestion import ingest_raw_text, ingest_url, ingest_file
from app.services.parser import clean_text
from app.services.chunker import chunk_text
from app.services.tagging import tag_source, tag_chunk, llm_tag_source
from app.services.embeddings import embed_chunks
from app.services.retrieval import run_retrieval
from app.services.brief_generator import generate_brief

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Source Ingestion ---

@router.post("/sources/ingest", response_model=SourceResponse, tags=["sources"])
def ingest_source(
    payload: SourceIngestText | None = None,
    db: Session = Depends(get_db),
):
    """Ingest a source from raw text."""
    if not payload:
        raise HTTPException(400, "Provide text payload")

    source = ingest_raw_text(
        db=db,
        title=payload.title,
        raw_text=payload.raw_text,
        source_type=payload.source_type,
        authority_level=payload.authority_level,
        jurisdiction_state=payload.jurisdiction_state,
        published_at=payload.published_at,
        publisher=payload.publisher,
        author=payload.author,
    )
    return source


@router.post("/sources/ingest/url", response_model=SourceResponse, tags=["sources"])
def ingest_source_url(payload: SourceIngestURL, db: Session = Depends(get_db)):
    """Ingest a source from URL."""
    try:
        source = ingest_url(
            db=db,
            url=payload.url,
            source_type=payload.source_type,
            authority_level=payload.authority_level,
            jurisdiction_state=payload.jurisdiction_state,
        )
        return source
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/sources/ingest/file", response_model=SourceResponse, tags=["sources"])
def ingest_source_file(
    file: UploadFile = File(...),
    source_type: str = Form("article"),
    authority_level: str = Form("trade"),
    jurisdiction_state: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Ingest a source from file upload."""
    content = file.file.read().decode("utf-8", errors="replace")
    source = ingest_file(
        db=db,
        filename=file.filename or "uploaded_file.txt",
        content=content,
        source_type=source_type,
        authority_level=authority_level,
        jurisdiction_state=jurisdiction_state,
    )
    return source


# --- Source Operations ---

@router.post("/sources/{source_id}/parse", response_model=SourceResponse, tags=["sources"])
def parse_source(source_id: UUID, db: Session = Depends(get_db)):
    """Parse and clean raw text for a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    if not source.raw_text:
        raise HTTPException(400, "Source has no raw text")

    source.raw_text = clean_text(source.raw_text)
    source.status = SourceStatus.PARSED

    # Apply tags
    tag_source(db, source)
    llm_tag_source(db, source)

    db.commit()
    db.refresh(source)
    return source


@router.post("/sources/{source_id}/chunk", response_model=SourceResponse, tags=["sources"])
def chunk_source(source_id: UUID, db: Session = Depends(get_db)):
    """Create chunks for a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    if not source.raw_text:
        raise HTTPException(400, "Source has no text to chunk")

    # Remove existing chunks
    db.query(SourceChunk).filter(SourceChunk.source_id == source.id).delete()

    chunks_data = chunk_text(
        source.raw_text,
        source_jurisdiction=source.jurisdiction,
        source_jurisdiction_state=source.jurisdiction_state,
        authority_score=float(source.authority_score),
        freshness_score=float(source.freshness_score),
    )

    for cd in chunks_data:
        chunk = SourceChunk(
            source_id=source.id,
            chunk_index=cd["chunk_index"],
            heading=cd.get("heading"),
            text_content=cd["text_content"],
            token_count=cd["token_count"],
            char_count=cd["char_count"],
            chunk_hash=cd["chunk_hash"],
            jurisdiction=cd.get("jurisdiction"),
            jurisdiction_state=cd.get("jurisdiction_state"),
            authority_score=cd["authority_score"],
            freshness_score=cd["freshness_score"],
        )
        db.add(chunk)
        db.flush()
        # Tag each chunk
        tag_chunk(db, chunk)

    source.status = SourceStatus.CHUNKED
    db.commit()
    db.refresh(source)
    return source


@router.post("/sources/{source_id}/embed", response_model=SourceResponse, tags=["sources"])
def embed_source(source_id: UUID, db: Session = Depends(get_db)):
    """Create embeddings for source chunks."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    chunks = db.query(SourceChunk).filter(SourceChunk.source_id == source.id).all()
    if not chunks:
        raise HTTPException(400, "Source has no chunks. Run /chunk first.")

    count = embed_chunks(db, chunks)
    source.status = SourceStatus.READY if count > 0 else SourceStatus.EMBEDDED
    db.commit()
    db.refresh(source)
    return source


@router.get("/sources", tags=["sources"])
def list_sources(
    status: str | None = None,
    source_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all sources."""
    q = db.query(Source)
    if status:
        q = q.filter(Source.status == status)
    if source_type:
        q = q.filter(Source.source_type == source_type)
    q = q.order_by(Source.created_at.desc())
    total = q.count()
    sources = q.offset(skip).limit(limit).all()
    return {"total": total, "sources": [SourceResponse.model_validate(s) for s in sources]}


@router.get("/sources/{source_id}", tags=["sources"])
def get_source(source_id: UUID, db: Session = Depends(get_db)):
    """Get source detail with tags and chunks."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source not found")

    tags = [TagResponse.model_validate(t) for t in source.tags]
    chunks = []
    for c in sorted(source.chunks, key=lambda x: x.chunk_index):
        has_emb = db.query(ChunkEmbedding).filter(ChunkEmbedding.chunk_id == c.id).first() is not None
        chunk_tags = [TagResponse.model_validate(t) for t in c.tags]
        chunks.append({
            "id": c.id,
            "chunk_index": c.chunk_index,
            "heading": c.heading,
            "text_content": c.text_content,
            "token_count": c.token_count,
            "char_count": c.char_count,
            "has_embedding": has_emb,
            "tags": chunk_tags,
        })

    return {
        "id": source.id,
        "source_type": source.source_type,
        "title": source.title,
        "publisher": source.publisher,
        "author": source.author,
        "url": source.url,
        "jurisdiction_state": source.jurisdiction_state,
        "authority_level": source.authority_level,
        "authority_score": float(source.authority_score),
        "freshness_score": float(source.freshness_score),
        "status": source.status,
        "raw_text": source.raw_text,
        "document_hash": source.document_hash,
        "created_at": source.created_at,
        "tags": tags,
        "chunks": chunks,
    }


# --- Prep Query ---

@router.post("/prep/query", response_model=PrepQueryResponse, tags=["prep"])
def prep_query(payload: PrepQueryRequest, db: Session = Depends(get_db)):
    """Submit a prep query and get a brief."""
    raw_query = payload.raw_query or f"{payload.employee_count}-person {payload.industry} in {payload.state}"

    query = Query(
        product_surface="prep",
        raw_query=raw_query,
        normalized_query=raw_query.lower().strip(),
        requested_industry=payload.industry.lower().strip(),
        requested_state=payload.state.lower().strip(),
        employee_count=payload.employee_count,
        current_mod=payload.current_mod,
    )
    db.add(query)
    db.flush()

    retrieval_run, selected_chunks = run_retrieval(
        db=db,
        query=query,
        industry=payload.industry,
        state=payload.state,
        employee_count=payload.employee_count,
        current_mod=payload.current_mod,
        raw_query=payload.raw_query,
    )

    brief = generate_brief(
        db=db,
        query=query,
        retrieval_run=retrieval_run,
        chunks=selected_chunks,
        industry=payload.industry,
        state=payload.state,
        employee_count=payload.employee_count,
        current_mod=payload.current_mod,
        raw_query=payload.raw_query,
    )

    return PrepQueryResponse(
        query_id=query.id,
        brief_id=brief.id,
        brief=brief.brief_json,
        rendered_markdown=brief.rendered_markdown,
    )


@router.get("/prep/brief/{brief_id}", tags=["prep"])
def get_brief(brief_id: UUID, db: Session = Depends(get_db)):
    """Get a stored brief."""
    brief = db.query(GeneratedBrief).filter(GeneratedBrief.id == brief_id).first()
    if not brief:
        raise HTTPException(404, "Brief not found")

    return {
        "id": brief.id,
        "query_id": brief.query_id,
        "model_name": brief.model_name,
        "brief_json": brief.brief_json,
        "rendered_markdown": brief.rendered_markdown,
        "quality_status": brief.quality_status,
        "created_at": brief.created_at,
    }


# --- Feedback ---

@router.post("/feedback", response_model=FeedbackResponse, tags=["feedback"])
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    """Submit feedback on a brief."""
    event = FeedbackEvent(
        brief_id=payload.brief_id,
        query_id=payload.query_id,
        event_type=payload.event_type,
        event_value=payload.event_value,
        event_json=payload.event_json,
        user_id=payload.user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# --- Retrieval Debug ---

@router.get("/retrieval/debug/{query_id}", tags=["debug"])
def retrieval_debug(query_id: UUID, db: Session = Depends(get_db)):
    """Get retrieval debug info for a query."""
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(404, "Query not found")

    run = db.query(RetrievalRun).filter(RetrievalRun.query_id == query_id).order_by(
        RetrievalRun.created_at.desc()
    ).first()

    if not run:
        return RetrievalDebugResponse(query_id=query_id)

    results = db.query(RetrievalResult).filter(
        RetrievalResult.retrieval_run_id == run.id
    ).order_by(RetrievalResult.rank_position).all()

    debug_results = []
    for r in results:
        chunk = db.query(SourceChunk).filter(SourceChunk.id == r.chunk_id).first()
        source = db.query(Source).filter(Source.id == chunk.source_id).first() if chunk else None
        debug_results.append(RetrievalDebugResult(
            chunk_id=r.chunk_id,
            rank_position=r.rank_position,
            similarity_score=float(r.similarity_score) if r.similarity_score else None,
            rerank_score=float(r.rerank_score) if r.rerank_score else None,
            selected=r.selected,
            text_preview=(chunk.text_content[:200] + "...") if chunk else "",
            source_title=source.title if source else "",
        ))

    return RetrievalDebugResponse(
        query_id=query_id,
        retrieval_run_id=run.id,
        embedding_model=run.embedding_model,
        filters=run.filters_json,
        candidate_count=run.candidate_count,
        selected_count=run.selected_count,
        results=debug_results,
    )
