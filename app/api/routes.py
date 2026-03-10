"""API endpoints for WAYOS PREP."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user, get_optional_user, CurrentUser
from app.core.enums import SourceStatus
from app.models.models import (
    Account, Source, SourceChunk, ChunkEmbedding, Query,
    GeneratedBrief, FeedbackEvent, RetrievalRun, RetrievalResult,
    RiskScoreRun,
)
from app.schemas.schemas import (
    SourceIngestText, SourceIngestURL, SourceResponse,
    TagResponse, PrepQueryRequest, PrepQueryResponse,
    FeedbackRequest, FeedbackResponse,
    RetrievalDebugResponse, RetrievalDebugResult,
    RiskScoreRequest, RiskScoreResponse, RiskScoreOutput,
    CoverageGapInsightRequest, CoverageGapInsightResponse,
    ProducerAmmoRequest, ProducerAmmoResponse,
    AgencyAmmoFeedResponse,
    DiscoveryCaptureRequest, DiscoveryCaptureResponse,
    ProductSignalsResponse,
)
from app.services.ingestion import ingest_raw_text, ingest_url, ingest_file
from app.services.parser import clean_text
from app.services.chunker import chunk_text
from app.services.tagging import tag_source, tag_chunk, llm_tag_source
from app.services.embeddings import embed_chunks
from app.services.retrieval import run_retrieval
from app.services.brief_generator import generate_brief
from app.services.risk_scoring import score_account
from app.services.coverage_gap_detector import detect_coverage_gaps, detect_knowledge_gaps
from app.services.meeting_brief import generate_meeting_brief
from app.services.learning_store import (
    add_office_learning as store_office_learning,
    list_office_learnings,
    add_producer_feedback as store_producer_feedback,
    list_producer_feedback,
    get_office_context,
    seed_demo_learnings,
)
from app.services.producer_ammo import generate_producer_ammo
from app.services.agency_ammo_feed import build_agency_ammo_feed
from app.services.discovery_capture import save_discovery
from app.services.instrumentation import log_event, get_product_signals
from app.services.loss_run_analyzer import analyze_loss_run
from app.schemas.loss_run import LossRunRequest, LossRunAnalysisResponse
from app.services.experience_mod_analyzer import analyze_experience_mod
from app.schemas.experience_mod import ExperienceModRequest, ExperienceModResponse
from app.services.submission_readiness import evaluate_submission_readiness
from app.services.response_rewriter import (
    rewrite_meeting_brief,
    rewrite_coverage_gaps,
    rewrite_submission_readiness,
)
from app.presentation.presentation_models import RewriteOptions
from app.services.account_memory_service import (
    create_account_memory_entry,
    list_account_memory,
    summarize_account_memory,
    write_memory_safe,
)
from app.services.capture_service import process_capture
from app.services.edge_score_service import calculate_edge_score
from app.services.outcome_learning_service import get_market_signals
from app.models.models import DealOutcome, AccountEvent
from app.services.telemetry_store import (
    record_rendered_output_event,
    record_rendered_output_feedback,
    list_rendered_output_events,
    list_rendered_output_feedback,
    summarize_rendered_output_telemetry,
)
from app.services.renewal_brief_generator import generate_renewal_brief
from app.schemas.renewal_brief import RenewalBriefRequest, RenewalBriefResponse
from app.services.public_web_intel import extract_public_web_intel, extract_public_web_intel_with_fetch
from app.schemas.public_web_intel import (
    PublicWebIntelRequest, PublicWebIntelResponse,
    PublicWebIntelFetchRequest, PublicWebIntelFetchResponse,
    AccountRefreshRequest, AccountRefreshResponse,
    LatestPublicIntelResponse, FetchSummary,
)
from app.services.account_refresh_service import (
    refresh_account_public_intel, get_latest_public_intel,
)
from app.services.underwriter_narrative_generator import generate_underwriter_narrative
from app.schemas.underwriter_narrative import UnderwriterNarrativeRequest, UnderwriterNarrativeResponse
from app.services.renewal_workspace_service import build_renewal_workspace
from app.schemas.renewal_workspace import RenewalWorkspaceRequest, RenewalWorkspaceResponse
from app.services.submission_packet_service import build_submission_packet
from app.schemas.submission_packet import SubmissionPacketRequest, SubmissionPacketResponse
from app.services.demo_session_service import build_demo_session_summary, list_recent_sessions
from app.services.demo_seed_service import (
    seed_demo_accounts, reset_demo_data, list_demo_scenarios,
    get_demo_accounts,
)
from app.schemas.demo import (
    DemoFeedbackRequest, DemoFeedbackResponse,
    DemoSessionSummaryResponse, InstrumentEventRequest,
)
from app.services.account_service import (
    create_account, get_account, list_accounts, update_account, delete_account,
)
from app.schemas.account import (
    AccountCreate, AccountUpdate, AccountResponse, AccountListResponse,
)
from app.services.artifact_service import (
    save_artifact, get_artifact, list_artifacts_for_account,
)
from app.schemas.artifact import ArtifactCreate, ArtifactResponse, ArtifactListResponse
from app.services.producer_style_service import (
    save_style, get_style, update_style,
)
from app.schemas.producer_style import (
    ProducerStyleCreate, ProducerStyleUpdate, ProducerStyleResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# --- Source Ingestion ---

@router.post("/sources/ingest", response_model=SourceResponse, tags=["sources"])
def ingest_source(
    payload: SourceIngestText,
    db: Session = Depends(get_db),
):
    """Ingest a source from raw text."""
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
@limiter.limit("10/minute")
def ingest_source_file(
    request: Request,
    file: UploadFile = File(...),
    source_type: str = Form("article"),
    authority_level: str = Form("trade"),
    jurisdiction_state: str | None = Form(None),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
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
    if count > 0:
        source.status = SourceStatus.READY
    else:
        # No embeddings generated (no API key) — still mark ready for tag-based retrieval
        source.status = SourceStatus.READY
        logger.info(f"Source {source_id}: no embeddings generated, marked ready for tag-based retrieval")
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
        entity_type=payload.entity_type,
        public_entity_type=payload.public_entity_type,
        department=payload.department,
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
        entity_type=payload.entity_type,
        public_entity_type=payload.public_entity_type,
        department=payload.department,
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
        entity_type=payload.entity_type,
        public_entity_type=payload.public_entity_type,
        department=payload.department,
    )

    # Run risk scoring (non-blocking — errors logged, not raised)
    risk_score = None
    try:
        risk_score = score_account(
            db=db,
            industry=payload.industry,
            state=payload.state,
            employee_count=payload.employee_count,
            current_mod=payload.current_mod,
            entity_type=payload.entity_type or "private_business",
            public_entity_type=payload.public_entity_type,
            department=payload.department,
            query_id=query.id,
            brief_id=brief.id,
        )
    except Exception:
        logger.exception("Risk scoring failed for query %s", query.id)

    return PrepQueryResponse(
        query_id=query.id,
        brief_id=brief.id,
        brief=brief.brief_json,
        rendered_markdown=brief.rendered_markdown,
        risk_score=risk_score,
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


# --- Risk Scoring ---

@router.get("/risk-score/{query_id}", tags=["risk-scoring"])
def get_risk_score(query_id: UUID, db: Session = Depends(get_db)):
    """Get the most recent risk score for a query."""
    run = db.query(RiskScoreRun).filter(
        RiskScoreRun.query_id == query_id,
    ).order_by(RiskScoreRun.created_at.desc()).first()

    if not run:
        raise HTTPException(404, "No risk score found for this query")

    return RiskScoreResponse(
        risk_score_run_id=run.id,
        query_id=run.query_id,
        brief_id=run.brief_id,
        score=RiskScoreOutput(**run.score_json),
        created_at=run.created_at,
    )


@router.post("/risk-score", response_model=RiskScoreResponse, tags=["risk-scoring"])
def create_risk_score(payload: RiskScoreRequest, db: Session = Depends(get_db)):
    """Run standalone risk scoring without a prep query."""
    result = score_account(
        db=db,
        industry=payload.industry,
        state=payload.state,
        employee_count=payload.employee_count,
        current_mod=payload.current_mod,
        entity_type=payload.entity_type,
        public_entity_type=payload.public_entity_type,
        department=payload.department,
        account_traits=payload.account_traits,
        retrieved_risk_themes=[
            {"slug": t.slug, "strength": t.strength}
            for t in payload.retrieved_risk_themes
        ],
        known_coverages=payload.known_coverages,
        question_signals=[
            {"category": q.category, "weight": q.weight}
            for q in payload.question_signals
        ],
        source_confidence=payload.source_confidence,
    )

    run_id = result.pop("risk_score_run_id")
    run = db.query(RiskScoreRun).filter(RiskScoreRun.id == run_id).first()

    return RiskScoreResponse(
        risk_score_run_id=run.id,
        query_id=run.query_id,
        brief_id=run.brief_id,
        score=RiskScoreOutput(**result),
        created_at=run.created_at,
    )


# --- Coverage Gap Insight Engine ---

@router.post("/risk/coverage-gaps", response_model=CoverageGapInsightResponse, tags=["risk-scoring"])
def coverage_gap_insights(payload: CoverageGapInsightRequest):
    """Analyze an account profile and return likely coverage gaps with suggested producer questions."""
    account_profile = {
        "industry": payload.industry,
        "state": payload.state,
        "employee_count": payload.employee_count or payload.employees,
        "vehicle_count": payload.vehicle_count or payload.vehicles,
        "annual_revenue": payload.annual_revenue,
        "experience_mod": payload.experience_mod or payload.current_mod,
        "uses_subcontractors": payload.uses_subcontractors,
        "current_coverages": payload.current_coverages,
    }
    result = detect_coverage_gaps(account_profile)
    return CoverageGapInsightResponse(**result)


# --- Knowledge-Based Gap Detection ---

@router.get("/risk/gaps", tags=["risk-scoring"])
def knowledge_gap_detection(
    industry: str = "",
    current_policies: str = "",
    office_id: str | None = None,
    render: bool = False,
    mode: str = "concise",
    tone: str = "neutral",
    session_id: str | None = None,
    use_llm: bool = False,
):
    """Detect coverage gaps using Industry Knowledge Objects.

    Compares current policies against the industry profile's expected
    policy lines to identify missing coverages and risk level.

    current_policies is a comma-separated list of policy names.
    office_id optionally includes office-specific learnings.
    render=true returns both structured output and rendered presentation.
    use_llm=true routes rendering through the AI model router.
    """
    policies = [p.strip() for p in current_policies.split(",") if p.strip()]
    result = detect_knowledge_gaps(industry, policies, office_id=office_id)
    if not render:
        return result
    opts = RewriteOptions(mode=mode, tone=tone)
    return rewrite_coverage_gaps(result, options=opts, office_id=office_id, session_id=session_id, use_llm=use_llm)


# --- Meeting Brief ---

@router.get("/meeting/brief", tags=["meeting"])
def meeting_brief_endpoint(
    industry: str = "",
    office_id: str | None = None,
    render: bool = False,
    mode: str = "concise",
    tone: str = "neutral",
    session_id: str | None = None,
    use_llm: bool = False,
    account_id: str | None = None,
    include_edge_score: bool = False,
    include_market_signals: bool = False,
    db: Session = Depends(get_db),
):
    """Generate a structured meeting preparation brief for an industry.

    Uses Industry Knowledge Objects to assemble exposures, claims,
    talking points, discovery questions, and coverage watchouts.
    office_id optionally includes office-specific learnings.
    render=true returns both structured output and rendered presentation.
    use_llm=true routes rendering through the AI model router.
    include_edge_score=true adds competitive edge score section.
    include_market_signals=true adds carrier win rate signals.
    """
    result = generate_meeting_brief(industry, office_id=office_id)

    # Auto-write memory entry
    if account_id:
        write_memory_safe(
            db, account_id=account_id, entry_type="brief_generated",
            summary=f"Meeting brief generated for {industry}",
            industry=industry, session_id=session_id,
            payload_json={"mode": mode, "render": render},
        )

    # Attach edge score if requested
    if include_edge_score:
        edge_input = {"risk_score": None, "carrier_appetite": "neutral"}
        result["edge_score"] = calculate_edge_score(edge_input)

    # Attach market signals if requested
    if include_market_signals:
        try:
            signals = get_market_signals(db, industry=industry)
            result["market_signals"] = signals
        except Exception:
            logger.exception("Failed to fetch market signals for brief")
            result["market_signals"] = {"carrier_win_rates": {}, "total_outcomes": 0}

    if not render:
        return result
    opts = RewriteOptions(mode=mode, tone=tone)
    return rewrite_meeting_brief(result, options=opts, office_id=office_id, session_id=session_id, use_llm=use_llm)


# --- Producer Ammo Questions Engine ---

@router.post("/risk/producer-ammo", response_model=ProducerAmmoResponse, tags=["risk-scoring"])
def producer_ammo_questions(payload: ProducerAmmoRequest):
    """Generate sharp, practical producer questions for pre-call planning and account reviews."""
    profile = {
        "industry": payload.industry,
        "state": payload.state,
        "employee_count": payload.employee_count,
        "annual_revenue": payload.annual_revenue,
        "vehicle_count": payload.vehicle_count,
        "experience_mod": payload.experience_mod,
        "uses_subcontractors": payload.uses_subcontractors,
        "current_coverages": payload.current_coverages,
        "claims_summary": payload.claims_summary,
        "account_stage": payload.account_stage,
        "notes": payload.notes,
    }
    result = generate_producer_ammo(profile)
    return ProducerAmmoResponse(**result)


# --- Agency Ammo Feed ---

@router.get("/intel/agency-ammo-feed", response_model=AgencyAmmoFeedResponse, tags=["intel"])
def agency_ammo_feed(
    industry: str = "",
    state: str = "",
    date_range_days: int = 30,
    account_stage: str | None = None,
    db: Session = Depends(get_db),
):
    """Aggregated intelligence feed of producer question patterns, coverage gap trends, and rising risk topics."""
    filters = {
        "industry": industry,
        "state": state,
        "date_range_days": date_range_days,
        "account_stage": account_stage,
    }
    result = build_agency_ammo_feed(filters, db=db)
    return AgencyAmmoFeedResponse(**result)


# --- Discovery Capture ---

@router.post("/intel/discovery-capture", response_model=DiscoveryCaptureResponse, tags=["intel"])
def discovery_capture(payload: DiscoveryCaptureRequest, db: Session = Depends(get_db)):
    """Record a producer-discovered exposure and any coverage action taken."""
    data = {
        "industry": payload.industry,
        "state": payload.state,
        "account_stage": payload.account_stage,
        "source_type": payload.source_type,
        "source_key": payload.source_key,
        "exposure_found": payload.exposure_found,
        "exposure_type": payload.exposure_type,
        "coverage_added": payload.coverage_added,
        "notes": payload.notes,
    }
    log_event(db, "discovery_capture", payload={"industry": payload.industry, "source_type": payload.source_type})
    result = save_discovery(db, data)
    return DiscoveryCaptureResponse(**result)


# --- Product Signals ---

@router.get("/intel/product-signals", response_model=ProductSignalsResponse, tags=["intel"])
def product_signals(days: int = 7, db: Session = Depends(get_db)):
    """Aggregated product usage signals over a time window."""
    if days < 1:
        days = 7
    result = get_product_signals(db, days=days)
    return ProductSignalsResponse(**result)


# --- Loss Run Analysis ---

@router.post("/analysis/loss-run", response_model=LossRunAnalysisResponse, tags=["analysis"])
def loss_run_analysis(payload: LossRunRequest, db: Session = Depends(get_db)):
    """Analyze loss run data and return structured insights for producers."""
    data = {
        "policy_period": payload.policy_period,
        "industry": payload.industry,
        "state": payload.state,
        "claims": [c.model_dump() for c in payload.claims],
    }
    log_event(db, "loss_run_analysis", payload={"industry": payload.industry, "claim_count": len(payload.claims)})
    result = analyze_loss_run(data)
    return LossRunAnalysisResponse(**result)


# --- Experience Mod Analysis ---

@router.post("/analysis/experience-mod", response_model=ExperienceModResponse, tags=["analysis"])
def experience_mod_analysis(payload: ExperienceModRequest, db: Session = Depends(get_db)):
    """Analyze experience mod worksheet data and return structured insights for producers."""
    log_event(db, "experience_mod_analysis", payload={"current_mod": payload.current_mod})
    result = analyze_experience_mod(
        current_mod=payload.current_mod,
        prior_mod=payload.prior_mod,
        expected_losses=payload.expected_losses,
        actual_primary_losses=payload.actual_primary_losses,
        actual_excess_losses=payload.actual_excess_losses,
        total_payroll=payload.total_payroll,
        class_code_entries=[e.model_dump() for e in payload.class_code_entries],
        mod_claims=[c.model_dump() for c in payload.mod_claims],
    )
    return ExperienceModResponse(**result)


# --- Renewal Brief ---

@router.post("/brief/renewal", response_model=RenewalBriefResponse, tags=["brief"])
def renewal_brief(payload: RenewalBriefRequest, db: Session = Depends(get_db)):
    """Generate a structured renewal risk brief from account profile data."""
    log_event(
        db,
        "renewal_brief_generated",
        payload={
            "industry": payload.industry,
            "state": payload.state,
            "has_loss_run": payload.loss_run_data is not None,
            "has_mod_data": payload.experience_mod_data is not None,
        },
    )
    profile = payload.model_dump()
    result = generate_renewal_brief(profile)
    return RenewalBriefResponse(**result)


# --- Public Web Intelligence ---

@router.post("/intel/public-web-intel", response_model=PublicWebIntelResponse, tags=["intel"])
def public_web_intel(payload: PublicWebIntelRequest, db: Session = Depends(get_db)):
    """Extract structured underwriting-relevant signals from public web content."""
    log_event(
        db,
        "public_web_intel_generated",
        payload={"company_name": payload.company_name, "industry": payload.industry},
    )
    input_data = payload.model_dump()
    result = extract_public_web_intel(input_data)
    return PublicWebIntelResponse(**result)


@router.post("/intel/public-web-intel/fetch", response_model=PublicWebIntelFetchResponse, tags=["intel"])
def public_web_intel_fetch(payload: PublicWebIntelFetchRequest, db: Session = Depends(get_db)):
    """Fetch public website content live and extract underwriting-relevant signals."""
    log_event(
        db,
        "public_web_fetch_requested",
        payload={
            "website_url": payload.website_url,
            "company_name": payload.company_name,
        },
    )
    input_data = payload.model_dump()
    result = extract_public_web_intel_with_fetch(input_data)

    log_event(
        db,
        "public_web_fetch_completed",
        payload={
            "website_url": payload.website_url,
            "fetch_success": result["fetch_summary"]["success"],
            "fetched_url_count": len(result["fetch_summary"]["fetched_urls"]),
        },
    )

    return PublicWebIntelFetchResponse(
        public_web_intel=PublicWebIntelResponse(**result["public_web_intel"]),
        fetch_summary=FetchSummary(**result["fetch_summary"]),
    )


@router.post("/accounts/{account_id}/refresh-public-intel", response_model=AccountRefreshResponse, tags=["accounts"])
def refresh_public_intel_endpoint(
    account_id: UUID,
    payload: AccountRefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh public web intelligence for an account by fetching its website."""
    result = refresh_account_public_intel(db, account_id, payload.model_dump())

    if result.get("error"):
        if result["error"] == "Account not found":
            raise HTTPException(404, result["error"])

    intel_response = None
    if result.get("public_web_intel"):
        intel_response = PublicWebIntelResponse(**result["public_web_intel"])

    fetch_response = None
    if result.get("fetch_summary"):
        fetch_response = FetchSummary(**result["fetch_summary"])

    return AccountRefreshResponse(
        account_id=result["account_id"],
        artifact_saved=result["artifact_saved"],
        error=result.get("error"),
        public_web_intel=intel_response,
        fetch_summary=fetch_response,
        account_updates=result.get("account_updates", []),
    )


@router.get("/accounts/{account_id}/public-intel/latest", response_model=LatestPublicIntelResponse, tags=["accounts"])
def get_latest_public_intel_endpoint(account_id: UUID, db: Session = Depends(get_db)):
    """Get the most recent public web intel artifact for an account."""
    result = get_latest_public_intel(db, account_id)
    if not result:
        raise HTTPException(404, "No public web intel found for this account")
    return LatestPublicIntelResponse(**result)


# --- Underwriter Narrative ---

@router.post("/narrative/underwriter", response_model=UnderwriterNarrativeResponse, tags=["narrative"])
def underwriter_narrative(payload: UnderwriterNarrativeRequest, db: Session = Depends(get_db)):
    """Generate underwriter-facing renewal or new business narrative."""
    log_event(
        db,
        "underwriter_narrative_generated",
        payload={
            "industry": payload.industry,
            "state": payload.state,
            "narrative_type": payload.narrative_type,
            "has_renewal_brief": payload.renewal_brief is not None,
            "has_public_intel": payload.public_web_intel is not None,
        },
    )
    profile = payload.model_dump()
    result = generate_underwriter_narrative(profile, db=db)
    return UnderwriterNarrativeResponse(**result)


# --- Accounts ---


@router.get("/accounts/search", tags=["accounts"])
def search_accounts(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    """Search accounts by name, named insured, or industry."""
    if not q or len(q) < 2:
        return {"accounts": [], "total": 0}

    pattern = f"%{q}%"
    results = (
        db.query(Account)
        .filter(
            (Account.account_name.ilike(pattern))
            | (Account.named_insured.ilike(pattern))
            | (Account.industry.ilike(pattern))
        )
        .order_by(Account.updated_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "accounts": [AccountResponse.model_validate(a).model_dump() for a in results],
        "total": len(results),
    }


@router.post("/accounts", response_model=AccountResponse, tags=["accounts"])
@limiter.limit("60/minute")
def create_account_endpoint(
    request: Request,
    payload: AccountCreate,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Create a new account."""
    log_event(db, "account_created", payload={"account_name": payload.account_name, "industry": payload.industry})
    account = create_account(db, payload.model_dump())
    return account


@router.get("/accounts", response_model=AccountListResponse, tags=["accounts"])
def list_accounts_endpoint(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List accounts with pagination."""
    accounts, total = list_accounts(db, limit=limit, offset=offset)
    return AccountListResponse(accounts=accounts, total=total)


@router.get("/accounts/{account_id}", response_model=AccountResponse, tags=["accounts"])
def get_account_endpoint(account_id: UUID, db: Session = Depends(get_db)):
    """Get an account by ID."""
    account = get_account(db, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse, tags=["accounts"])
def update_account_endpoint(
    account_id: UUID,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Update an account."""
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    account = update_account(db, account_id, data)
    if not account:
        raise HTTPException(404, "Account not found")
    log_event(db, "account_updated", payload={"account_id": str(account_id)})

    # Record durable memory for meaningful field changes
    from app.services.account_memory_service import record_memory

    if "notes" in data and data["notes"]:
        record_memory(
            db,
            account_id=str(account_id),
            entry_type="producer_edited",
            summary=data["notes"][:200],
            category="client_behavior",
            confidence="high",
            industry=getattr(account, "industry", None),
        )
    if "current_coverages" in data:
        cov_list = data["current_coverages"] or []
        if cov_list:
            record_memory(
                db,
                account_id=str(account_id),
                entry_type="producer_edited",
                summary=f"Coverages updated: {', '.join(cov_list[:5])}",
                category="coverage_history",
                confidence="high",
                industry=getattr(account, "industry", None),
            )
    db.commit()

    return account


@router.delete("/accounts/{account_id}", tags=["accounts"])
def delete_account_endpoint(
    account_id: UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Delete an account."""
    deleted = delete_account(db, account_id)
    if not deleted:
        raise HTTPException(404, "Account not found")
    return {"status": "deleted", "account_id": str(account_id)}


# --- Saved Artifacts ---

@router.post("/artifacts", response_model=ArtifactResponse, tags=["artifacts"])
def save_artifact_endpoint(payload: ArtifactCreate, db: Session = Depends(get_db)):
    """Save a generated artifact."""
    log_event(db, "artifact_saved", payload={"artifact_type": payload.artifact_type, "account_id": str(payload.account_id) if payload.account_id else None})
    artifact = save_artifact(db, payload.model_dump())
    return artifact


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse, tags=["artifacts"])
def get_artifact_endpoint(artifact_id: UUID, db: Session = Depends(get_db)):
    """Get an artifact by ID."""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    return artifact


@router.get("/accounts/{account_id}/artifacts", response_model=ArtifactListResponse, tags=["artifacts"])
def list_account_artifacts_endpoint(account_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
    """List artifacts for an account."""
    artifacts = list_artifacts_for_account(db, account_id, limit=limit)
    return ArtifactListResponse(artifacts=artifacts, total=len(artifacts))


# --- Producer Style Preferences ---

@router.post("/producer-style/preferences", response_model=ProducerStyleResponse, tags=["producer-style"])
def save_style_endpoint(payload: ProducerStyleCreate, db: Session = Depends(get_db)):
    """Create or update producer style preferences."""
    log_event(db, "producer_style_saved", payload={"producer_id": payload.producer_id, "audience": payload.audience})
    pref = save_style(db, payload.model_dump())
    return pref


@router.get("/producer-style/preferences/{producer_id}", response_model=ProducerStyleResponse, tags=["producer-style"])
def get_style_endpoint(producer_id: str, db: Session = Depends(get_db)):
    """Get producer style preferences."""
    pref = get_style(db, producer_id)
    if not pref:
        raise HTTPException(404, "Producer style preferences not found")
    return pref


@router.put("/producer-style/preferences/{producer_id}", response_model=ProducerStyleResponse, tags=["producer-style"])
def update_style_endpoint(producer_id: str, payload: ProducerStyleUpdate, db: Session = Depends(get_db)):
    """Update producer style preferences."""
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    pref = update_style(db, producer_id, data)
    if not pref:
        raise HTTPException(404, "Producer style preferences not found")
    log_event(db, "producer_style_saved", payload={"producer_id": producer_id})
    return pref


# --- Renewal Workspace ---

@router.post("/workspace/renewal/{account_id}", response_model=RenewalWorkspaceResponse, tags=["workspace"])
def renewal_workspace_endpoint(
    account_id: UUID,
    payload: RenewalWorkspaceRequest,
    db: Session = Depends(get_db),
):
    """Build a unified renewal workspace for an account.

    Orchestrates public web intel, renewal brief, coverage gaps,
    producer ammo, and underwriter narrative into a single response.
    """
    result = build_renewal_workspace(db, account_id, payload.model_dump())

    if result.get("error") == "Account not found":
        raise HTTPException(404, result["error"])

    return RenewalWorkspaceResponse(**result)


# --- Submission Packet ---

@router.post("/packet/submission/{account_id}", response_model=SubmissionPacketResponse, tags=["packet"])
def submission_packet_endpoint(
    account_id: UUID,
    payload: SubmissionPacketRequest,
    db: Session = Depends(get_db),
):
    """Build a submission packet combining workspace data into a copyable format."""
    result = build_submission_packet(db, account_id, payload.model_dump())

    if result.get("error") == "Account not found":
        raise HTTPException(404, result["error"])

    # Auto-write memory entry
    write_memory_safe(
        db, account_id=str(account_id),
        entry_type="submission_packet_generated",
        summary=f"Submission packet generated for account {account_id}",
        payload_json={"sections": list(payload.model_dump().get("sections", {}).keys()) if hasattr(payload, "sections") else []},
    )

    return SubmissionPacketResponse(**result)


# --- Demo Instrumentation ---

@router.post("/demo/event", tags=["demo"])
def log_demo_event(payload: InstrumentEventRequest, db: Session = Depends(get_db)):
    """Log a demo/UI interaction event for session tracking."""
    log_event(
        db,
        event_type=payload.event_type,
        payload=payload.payload,
        session_id=payload.session_id,
    )
    return {"status": "ok"}


@router.post("/demo/feedback", response_model=DemoFeedbackResponse, tags=["demo"])
def submit_demo_feedback(payload: DemoFeedbackRequest, db: Session = Depends(get_db)):
    """Submit demo tester feedback."""
    from app.models.models import DemoFeedback
    fb = DemoFeedback(
        session_id=payload.session_id,
        account_id=payload.account_id if payload.account_id else None,
        would_use_before_meeting=payload.would_use_before_meeting,
        most_useful_part=payload.most_useful_part,
        unclear_or_untrustworthy=payload.unclear_or_untrustworthy,
        what_next=payload.what_next,
        overall_rating=payload.overall_rating,
        notes=payload.notes,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    log_event(db, "demo_feedback_submitted", payload={
        "session_id": payload.session_id,
        "overall_rating": payload.overall_rating,
    }, session_id=payload.session_id)
    import uuid as _uuid
    from datetime import datetime as _dt, timezone as _tz
    return DemoFeedbackResponse(
        id=fb.id or _uuid.uuid4(),
        session_id=fb.session_id,
        overall_rating=fb.overall_rating,
        created_at=fb.created_at.isoformat() if fb.created_at else _dt.now(_tz.utc).isoformat(),
    )


@router.get("/demo/session-summary", response_model=DemoSessionSummaryResponse, tags=["demo"])
def get_session_summary(
    session_id: str | None = None,
    user_id: str | None = None,
    hours: int = 24,
    db: Session = Depends(get_db),
):
    """Get a summary of demo session activity."""
    result = build_demo_session_summary(db, session_id=session_id, user_id=user_id, hours=hours)
    return DemoSessionSummaryResponse(**result)


@router.get("/demo/recent-sessions", tags=["demo"])
def get_recent_sessions(hours: int = 24, limit: int = 20, db: Session = Depends(get_db)):
    """List recent demo sessions with basic stats."""
    sessions = list_recent_sessions(db, hours=hours, limit=limit)
    return {"sessions": sessions, "count": len(sessions)}


# --- Demo Admin (Internal-Only) ---

@router.post("/demo/seed", tags=["demo-admin"])
def seed_demo_data_endpoint(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Seed demo accounts with realistic data. Internal-only."""
    results = seed_demo_accounts(db)
    created = sum(1 for r in results if r["status"] == "created")

    # Auto-write memory entries for created accounts
    for r in results:
        if r["status"] == "created" and r.get("account_id"):
            write_memory_safe(
                db, account_id=str(r["account_id"]),
                entry_type="account_created",
                summary=f"Demo account created: {r.get('account_name', 'unknown')}",
                industry=r.get("industry"),
                payload_json={"demo_seed": True},
            )

    return {"accounts": results, "created": created, "total": len(results)}


@router.post("/demo/reset", tags=["demo-admin"])
def reset_demo_data_endpoint(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Reset all demo data (accounts, artifacts, feedback, events). Internal-only."""
    summary = reset_demo_data(db)
    return {"status": "reset_complete", **summary}


@router.get("/demo/scenarios", tags=["demo-admin"])
def list_demo_scenarios_endpoint():
    """List available demo scenarios with descriptions."""
    scenarios = list_demo_scenarios()
    return {"scenarios": scenarios, "count": len(scenarios)}


@router.get("/demo/accounts", tags=["demo-admin"])
def list_demo_accounts_endpoint(db: Session = Depends(get_db)):
    """List demo-seeded accounts currently in the database."""
    accounts = get_demo_accounts(db)
    return {"accounts": accounts, "count": len(accounts)}


@router.get("/demo/feedback-list", tags=["demo-admin"])
def list_demo_feedback_endpoint(
    hours: int = 168,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List recent demo feedback entries. Defaults to last 7 days."""
    from datetime import datetime, timedelta, timezone
    from app.models.models import DemoFeedback
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    feedbacks = (
        db.query(DemoFeedback)
        .filter(DemoFeedback.created_at >= cutoff)
        .order_by(DemoFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    for fb in feedbacks:
        items.append({
            "id": str(fb.id),
            "session_id": fb.session_id,
            "overall_rating": fb.overall_rating,
            "would_use_before_meeting": fb.would_use_before_meeting,
            "most_useful_part": fb.most_useful_part,
            "unclear_or_untrustworthy": fb.unclear_or_untrustworthy,
            "what_next": fb.what_next,
            "notes": fb.notes,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        })
    return {"feedback": items, "count": len(items)}


@router.get("/demo/account-gaps/{account_id}", tags=["demo-admin"])
def demo_account_gaps(account_id: UUID, db: Session = Depends(get_db)):
    """Run knowledge-based gap detection against a demo account."""
    account = get_account(db, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    current_policies = account.current_coverages or []
    industry = account.industry or ""
    result = detect_knowledge_gaps(industry, current_policies)
    result["account_id"] = str(account_id)
    result["account_name"] = account.account_name
    return result


# --- Learning System ---

@router.post("/learning/office", tags=["learning"])
def add_learning_endpoint(payload: dict):
    """Add an office-specific learning note."""
    office_id = payload.get("office_id", "")
    industry = payload.get("industry", "")
    note = payload.get("note", "")
    if not office_id or not industry or not note:
        raise HTTPException(400, "office_id, industry, and note are required")
    result = store_office_learning(
        office_id=office_id,
        industry=industry,
        note=note,
        created_by=payload.get("created_by"),
        confidence=payload.get("confidence", 0.5),
        tags=payload.get("tags"),
    )
    return {"status": "ok", "learning": result}


@router.get("/learning/office", tags=["learning"])
def list_learnings_endpoint(
    office_id: str | None = None,
    industry: str | None = None,
):
    """List office learnings, optionally filtered."""
    learnings = list_office_learnings(office_id=office_id, industry=industry)
    return {"learnings": learnings, "count": len(learnings)}


@router.post("/learning/feedback", tags=["learning"])
def add_feedback_endpoint(payload: dict):
    """Record producer feedback on WAYOS output."""
    office_id = payload.get("office_id", "")
    industry = payload.get("industry", "")
    endpoint = payload.get("endpoint", "")
    feedback_type = payload.get("feedback_type", "")
    if not office_id or not industry or not endpoint or not feedback_type:
        raise HTTPException(400, "office_id, industry, endpoint, and feedback_type are required")
    result = store_producer_feedback(
        office_id=office_id,
        industry=industry,
        endpoint=endpoint,
        input_payload=payload.get("input_payload", {}),
        output_payload=payload.get("output_payload", {}),
        feedback_type=feedback_type,
        feedback_note=payload.get("feedback_note"),
    )
    return {"status": "ok", "feedback": result}


@router.get("/learning/feedback", tags=["learning"])
def list_feedback_endpoint(
    office_id: str | None = None,
    industry: str | None = None,
):
    """List producer feedback, optionally filtered."""
    feedback = list_producer_feedback(office_id=office_id, industry=industry)
    return {"feedback": feedback, "count": len(feedback)}


@router.get("/learning/context", tags=["learning"])
def learning_context_endpoint(office_id: str = "", industry: str = ""):
    """Get aggregated office context for an industry."""
    if not office_id or not industry:
        raise HTTPException(400, "office_id and industry are required")
    result = get_office_context(office_id, industry)
    return result


@router.post("/learning/seed-demo", tags=["learning"])
def seed_demo_learnings_endpoint():
    """Seed demo office learnings. Internal-only."""
    count = seed_demo_learnings()
    return {"status": "ok", "learnings_added": count}


# ============================================================
# SUBMISSION READINESS
# ============================================================

DEMO_SUBMISSIONS = {
    "demo-roofing-nc-strong": {
        "industry": "roofing contractor",
        "jurisdiction": "NC",
        "office_id": "demo-roofing-nc",
        "submission_data": {
            "legal_entity_name": "Summit Ridge Roofing LLC",
            "operations_description": "Commercial and residential roof installation and repair, primarily shingle and flat roof systems across central North Carolina",
            "years_in_business": 12,
            "annual_revenue": 4200000,
            "payroll": 1200000,
            "employee_count": 38,
            "subcontractor_usage": "yes, approximately 30 percent of labor on commercial jobs, certificates required and tracked",
            "loss_runs": "provided, 5-year history, 3 WC claims totaling $85,000",
            "current_coverages": "GL $1M/$2M, WC statutory, Commercial Auto $1M CSL, Umbrella $2M",
            "requested_coverages": "GL, WC, Commercial Auto, Umbrella, Inland Marine",
            "vehicle_count": 12,
            "fall_protection_program": True,
            "safety_program": True,
            "roof_types": "residential shingle, commercial flat roof, TPO, modified bitumen",
            "max_height": "4 stories",
            "tool_equipment_values": 185000,
        },
    },
    "demo-landscaping-tx-fair": {
        "industry": "landscaping contractor",
        "jurisdiction": "TX",
        "office_id": "demo-landscaping-tx",
        "submission_data": {
            "legal_entity_name": "GreenScape Landscapes Inc.",
            "operations_description": "Lawn care and landscaping",
            "years_in_business": 5,
            "annual_revenue": 850000,
            "employee_count": 12,
            "loss_runs": "unknown",
            "current_coverages": "GL only",
            "requested_coverages": "GL, WC, Auto",
        },
    },
    "demo-restaurant-ca-poor": {
        "industry": "restaurant",
        "jurisdiction": "CA",
        "office_id": "demo-restaurant-ca",
        "submission_data": {
            "legal_entity_name": "Bella Cucina",
            "annual_revenue": 980000,
            "employee_count": 18,
        },
    },
}


@router.post("/submission/readiness", tags=["submission"])
def submission_readiness_endpoint(
    body: dict,
    render: bool = False,
    mode: str = "concise",
    tone: str = "neutral",
    session_id: str | None = None,
    use_llm: bool = False,
):
    """Evaluate submission readiness against industry-specific requirements.

    Does not evaluate carrier appetite or placement fit — submission quality only.
    render=true returns both structured output and rendered presentation.
    use_llm=true routes rendering through the AI model router.
    """
    industry = body.get("industry")
    if not industry:
        raise HTTPException(status_code=422, detail="industry is required")

    submission_data = body.get("submission_data", {})
    jurisdiction = body.get("jurisdiction")
    office_id = body.get("office_id")

    result = evaluate_submission_readiness(
        industry=industry,
        submission_data=submission_data,
        jurisdiction=jurisdiction,
        office_id=office_id,
    )
    if not render:
        return result
    opts = RewriteOptions(mode=mode, tone=tone)
    return rewrite_submission_readiness(result, options=opts, office_id=office_id, session_id=session_id, use_llm=use_llm)


@router.get("/submission/demo-examples", tags=["submission"])
def submission_demo_examples():
    """List available demo submission examples."""
    return {
        "examples": {
            key: {
                "industry": val["industry"],
                "jurisdiction": val["jurisdiction"],
                "office_id": val.get("office_id"),
                "field_count": len(val["submission_data"]),
            }
            for key, val in DEMO_SUBMISSIONS.items()
        }
    }


@router.get("/submission/demo-examples/{example_id}", tags=["submission"])
def submission_demo_example(example_id: str):
    """Get a specific demo submission example with full payload."""
    example = DEMO_SUBMISSIONS.get(example_id)
    if not example:
        raise HTTPException(status_code=404, detail=f"Demo example '{example_id}' not found")
    return example


@router.post("/submission/demo-evaluate/{example_id}", tags=["submission"])
def submission_demo_evaluate(example_id: str):
    """Evaluate a demo submission example — convenience endpoint for testing."""
    example = DEMO_SUBMISSIONS.get(example_id)
    if not example:
        raise HTTPException(status_code=404, detail=f"Demo example '{example_id}' not found")

    return evaluate_submission_readiness(
        industry=example["industry"],
        submission_data=example["submission_data"],
        jurisdiction=example.get("jurisdiction"),
        office_id=example.get("office_id"),
    )


# ============================================================
# TELEMETRY — Rendered Output Tracking
# ============================================================


@router.post("/telemetry/rendered-output/event", tags=["telemetry"])
def telemetry_record_event(body: dict):
    """Record a rendered output telemetry event (shown, copied, etc.)."""
    event_type = body.get("event_type", "")
    endpoint = body.get("endpoint", "")
    if not event_type or not endpoint:
        raise HTTPException(400, "event_type and endpoint are required")
    result = record_rendered_output_event(
        event_type=event_type,
        endpoint=endpoint,
        response_type=body.get("response_type", ""),
        mode=body.get("mode", ""),
        tone=body.get("tone", ""),
        office_id=body.get("office_id"),
        industry=body.get("industry"),
        session_id=body.get("session_id"),
        output_id=body.get("output_id"),
        metadata=body.get("metadata"),
    )
    return {"status": "ok", "event": result}


@router.post("/telemetry/rendered-output/feedback", tags=["telemetry"])
def telemetry_record_feedback(body: dict, db: Session = Depends(get_db)):
    """Record producer feedback on a rendered output."""
    output_id = body.get("output_id", "")
    feedback_type = body.get("feedback_type", "")
    if not output_id or not feedback_type:
        raise HTTPException(400, "output_id and feedback_type are required")
    result = record_rendered_output_feedback(
        output_id=output_id,
        endpoint=body.get("endpoint", ""),
        response_type=body.get("response_type", ""),
        mode=body.get("mode", ""),
        tone=body.get("tone", ""),
        feedback_type=feedback_type,
        office_id=body.get("office_id"),
        industry=body.get("industry"),
        feedback_note=body.get("feedback_note"),
        edited_text=body.get("edited_text"),
    )

    # Auto-write memory entry if account_id provided
    account_id = body.get("account_id")
    if account_id:
        entry_type = "producer_edited" if feedback_type == "edited" else "producer_feedback"
        write_memory_safe(
            db, account_id=account_id, entry_type=entry_type,
            summary=f"Producer {feedback_type} on {body.get('response_type', 'output')}",
            industry=body.get("industry"), session_id=body.get("session_id"),
            payload_json={"output_id": output_id, "feedback_type": feedback_type, "mode": body.get("mode")},
        )

    return {"status": "ok", "feedback": result}


@router.get("/telemetry/rendered-output/events", tags=["telemetry"])
def telemetry_list_events(
    office_id: str | None = None,
    industry: str | None = None,
    endpoint: str | None = None,
    event_type: str | None = None,
):
    """List rendered output telemetry events with optional filters."""
    events = list_rendered_output_events(
        office_id=office_id, industry=industry,
        endpoint=endpoint, event_type=event_type,
    )
    return {"events": events, "count": len(events)}


@router.get("/telemetry/rendered-output/feedback", tags=["telemetry"])
def telemetry_list_feedback(
    office_id: str | None = None,
    industry: str | None = None,
    endpoint: str | None = None,
    feedback_type: str | None = None,
):
    """List rendered output feedback with optional filters."""
    feedback = list_rendered_output_feedback(
        office_id=office_id, industry=industry,
        endpoint=endpoint, feedback_type=feedback_type,
    )
    return {"feedback": feedback, "count": len(feedback)}


@router.get("/telemetry/rendered-output/summary", tags=["telemetry"])
def telemetry_summary(
    office_id: str | None = None,
    industry: str | None = None,
):
    """Aggregated telemetry summary for rendered outputs."""
    return summarize_rendered_output_telemetry(
        office_id=office_id, industry=industry,
    )


# ============================================================
# ACCOUNT MEMORY LEDGER
# ============================================================


@router.post("/account-memory", tags=["account-memory"])
def create_memory_entry(body: dict, db: Session = Depends(get_db)):
    """Create a new account memory entry."""
    account_id = body.get("account_id")
    entry_type = body.get("entry_type")
    summary = body.get("summary")
    if not account_id or not entry_type or not summary:
        raise HTTPException(422, "account_id, entry_type, and summary are required")
    try:
        entry = create_account_memory_entry(
            db=db,
            account_id=account_id,
            entry_type=entry_type,
            summary=summary,
            agency_id=body.get("agency_id"),
            session_id=body.get("session_id"),
            industry=body.get("industry"),
            payload_json=body.get("payload_json"),
            created_by=body.get("created_by"),
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"status": "ok", "entry": entry}


@router.get("/account-memory/{account_id}", tags=["account-memory"])
def get_account_memory(account_id: str, db: Session = Depends(get_db)):
    """List all memory entries for an account."""
    entries = list_account_memory(db, account_id)
    return {"account_id": account_id, "entries": entries, "count": len(entries)}


@router.get("/account-memory/{account_id}/summary", tags=["account-memory"])
def get_account_memory_summary(account_id: str, db: Session = Depends(get_db)):
    """Get a compact summary of the account's memory ledger."""
    return summarize_account_memory(db, account_id)


# ============================================================
# QUICKCAPTURE INGESTION
# ============================================================


@router.post("/capture", tags=["capture"])
@limiter.limit("10/minute")
async def capture_endpoint(
    request: Request,
    account_id: str | None = Form(None),
    plain_text: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Ingest a screenshot, PDF, or plain text and extract insurance signals."""
    from app.security.upload import validate_upload

    file_bytes = None
    filename = None
    content_type = None

    if file:
        validate_upload(file)
        file_bytes = await file.read()
        filename = file.filename
        content_type = file.content_type

    if not file_bytes and not plain_text:
        raise HTTPException(422, "Provide either a file upload or plain_text")

    result = process_capture(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        plain_text=plain_text,
    )

    # Store timeline event if account_id provided
    if account_id:
        try:
            event = AccountEvent(
                account_id=account_id,
                event_type="CAPTURE_UPLOADED",
                notes=f"Captured {result['source_type']} with {len(result['signals'])} signals",
            )
            db.add(event)
            db.commit()
        except Exception:
            logger.exception("Failed to record capture timeline event")

    return {
        "status": "ok",
        "source_type": result["source_type"],
        "signals": result["signals"],
        "account_id": account_id,
    }


# ============================================================
# EDGE SCORE ENGINE
# ============================================================


@router.post("/edge-score", tags=["edge-score"])
@limiter.limit("60/minute")
def edge_score_endpoint(
    request: Request,
    body: dict,
    _user: CurrentUser = Depends(get_current_user),
):
    """Calculate competitive edge score for an account."""
    logger.info("Edge score calculation requested for: %s", body.get("account_id", "unknown"))
    return calculate_edge_score(body)


# ============================================================
# DEAL OUTCOMES
# ============================================================


@router.post("/outcomes", tags=["outcomes"])
@limiter.limit("60/minute")
def create_outcome(
    request: Request,
    body: dict,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Record a deal outcome for market intelligence."""
    # Validate required fields
    account_id = body.get("account_id")
    outcome = body.get("outcome")
    if not account_id or not outcome:
        raise HTTPException(422, "account_id and outcome are required")
    if len(str(account_id)) > 500 or len(str(outcome)) > 100:
        raise HTTPException(422, "Field length exceeds limit")

    log_event(db, "outcome_submitted", payload={
        "account_id": str(account_id)[:500],
        "outcome": outcome,
        "carrier": body.get("carrier"),
    })

    deal = DealOutcome(
        account_id=str(account_id)[:500],
        industry=(body.get("industry") or "").lower()[:100] or None,
        state=(body.get("state") or "").upper()[:10] or None,
        carrier=str(body.get("carrier") or "")[:200] or None,
        premium=body.get("premium"),
        outcome=outcome.lower()[:50],
        outcome_reason=str(body.get("outcome_reason") or "")[:200] or None,
        competitor=str(body.get("competitor") or "")[:200] or None,
        notes=str(body.get("notes") or "")[:2000] or None,
    )
    db.add(deal)

    # Record timeline event
    try:
        event = AccountEvent(
            account_id=account_id,
            event_type="OUTCOME_RECORDED",
            notes=f"Deal outcome: {outcome} — {body.get('carrier', 'unknown carrier')}",
        )
        db.add(event)
    except Exception:
        logger.exception("Failed to add timeline event for outcome")

    # Record durable memory entry
    from app.services.account_memory_service import record_memory

    carrier = body.get("carrier", "unknown carrier")
    reason = body.get("outcome_reason") or body.get("notes") or ""
    competitor = body.get("competitor")
    summary_parts = [f"{outcome.capitalize()} — {carrier}"]
    if competitor:
        summary_parts.append(f"competitor: {competitor}")
    if reason:
        summary_parts.append(reason)
    memory_summary = ". ".join(summary_parts)

    record_memory(
        db,
        account_id=str(account_id),
        entry_type="outcome_logged",
        summary=memory_summary,
        category="outcome_history",
        confidence="high",
        industry=body.get("industry"),
        payload_json={
            "outcome": outcome,
            "carrier": carrier,
            "competitor": competitor,
            "premium": body.get("premium"),
        },
    )

    db.commit()

    return {
        "status": "ok",
        "outcome_id": str(deal.id),
        "account_id": account_id,
        "outcome": deal.outcome,
    }


# ============================================================
# MARKET SIGNALS (OUTCOME AGGREGATION)
# ============================================================


@router.get("/market-signals", tags=["outcomes"])
@limiter.limit("60/minute")
def market_signals_endpoint(
    request: Request,
    industry: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Get aggregated market signals from deal outcomes."""
    return get_market_signals(db, industry=industry, state=state)


@router.get("/accounts/{account_id}/market-edge", tags=["outcomes"])
@limiter.limit("60/minute")
def market_edge_endpoint(
    request: Request,
    account_id: str,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Market Edge intelligence panel for an account's industry + state."""
    from app.models.models import Account as AccountModel
    from app.services.outcome_learning_service import get_market_edge

    account = db.query(AccountModel).filter(AccountModel.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return get_market_edge(db, industry=account.industry, state=account.state)


# ============================================================
# ACCOUNT TIMELINE
# ============================================================


@router.get("/accounts/{account_id}/timeline", tags=["timeline"])
def account_timeline(account_id: str, db: Session = Depends(get_db)):
    """Get timeline of events for an account."""
    events = (
        db.query(AccountEvent)
        .filter(AccountEvent.account_id == account_id)
        .order_by(AccountEvent.created_at.desc())
        .all()
    )
    return {
        "account_id": account_id,
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "count": len(events),
    }


# ============================================================
# MVP: CAPTURE, DASHBOARD, SEARCH, INSIGHTS, ARTIFACT GENERATE
# ============================================================

from app.models.models import Account, IngestionEvent, AccountHealth, SavedArtifact as SAModel
from app.schemas.capture import CaptureResponse, ManualAccountCreate, AccountFromCaptureRequest
from app.schemas.health import AccountHealthResponse
from app.schemas.insight import InsightItem, InsightFeedResponse
from app.services.health_service import compute_account_health
from app.services.insight_service import generate_insights
from app.services.artifact_engine import generate_artifact, generate_all_artifacts
from app.schemas.artifact_schemas import ARTIFACT_PRIORITY


@router.post("/capture", tags=["capture"])
@limiter.limit("10/minute")
def capture_endpoint_mvp(
    request: Request,
    file: UploadFile | None = File(None),
    plain_text: str = Form(""),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Capture a screenshot, file, or text and extract insurance signals."""
    from app.security.upload import validate_upload

    file_bytes = None
    filename = None
    content_type = None

    if file:
        validate_upload(file)
        file_bytes = file.file.read()
        filename = file.filename
        content_type = file.content_type

    result = process_capture(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        plain_text=plain_text or None,
    )

    # Store ingestion event
    event = IngestionEvent(
        source_type=result["source_type"],
        filename=filename,
        raw_text=result["extracted_text"][:10000] if result["extracted_text"] else None,
        extraction_json=result["signals"],
    )
    db.add(event)
    db.commit()

    log_event(db, "capture_completed", payload={
        "source_type": result["source_type"],
        "signal_count": len(result["signals"]),
    })

    return {
        "ingestion_event_id": str(event.id),
        "source_type": result["source_type"],
        "extracted_text": result["extracted_text"],
        "signals": result["signals"],
    }


@router.post("/accounts/from-capture", tags=["capture"])
@limiter.limit("10/minute")
def account_from_capture(
    request: Request,
    body: AccountFromCaptureRequest,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Create an account from capture signals. Returns account + health card."""
    signals = body.signals or {}

    # If ingestion_event_id provided, load signals from it
    if body.ingestion_event_id:
        ie = db.query(IngestionEvent).filter(IngestionEvent.id == body.ingestion_event_id).first()
        if ie and ie.extraction_json:
            signals = {**ie.extraction_json, **(body.signals or {})}

    # Build account from signals + explicit fields
    account_name = body.account_name or signals.get("carrier", "New Account")
    account = Account(
        account_name=account_name,
        named_insured=body.named_insured,
        industry=(body.industry or "").lower() or None,
        state=(body.state or "").upper() or None,
        employee_count=signals.get("employee_count"),
        workers_comp_mod=signals.get("mod"),
        current_coverages=[signals["coverage"]] if signals.get("coverage") else [],
        current_carriers=[signals["carrier"]] if signals.get("carrier") else [],
        extracted_text=None,
    )
    db.add(account)
    db.flush()

    # Link ingestion event
    if body.ingestion_event_id:
        ie = db.query(IngestionEvent).filter(IngestionEvent.id == body.ingestion_event_id).first()
        if ie:
            ie.account_id = account.id
            account.extracted_text = ie.raw_text

    # Compute health card (fast, deterministic)
    health = compute_account_health(account, db)
    db.commit()

    # Try to enqueue background artifact generation
    from app.workers.artifact_worker import enqueue_artifact_generation
    enqueued = enqueue_artifact_generation(account.id)
    if not enqueued:
        # Fallback: generate artifacts synchronously (deterministic only, no LLM)
        try:
            generate_all_artifacts(account.id, db, use_llm=False)
            db.commit()
        except Exception:
            logger.exception("Sync artifact generation failed for %s", account.id)

    log_event(db, "account_from_capture", payload={
        "account_id": str(account.id),
        "account_name": account_name,
    })

    return {
        "account": AccountResponse.model_validate(account).model_dump(),
        "health": AccountHealthResponse.from_orm_model(health).model_dump(),
    }


@router.post("/accounts/manual", tags=["capture"])
@limiter.limit("60/minute")
def create_manual_account(
    request: Request,
    body: ManualAccountCreate,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Create account from manual entry. Returns account + health card."""
    account = Account(
        account_name=body.account_name,
        named_insured=body.named_insured,
        industry=(body.industry or "").lower() or None,
        state=(body.state or "").upper() or None,
        employee_count=body.employee_count,
        annual_revenue=body.annual_revenue,
        payroll_estimate=body.payroll_estimate,
        workers_comp_mod=body.workers_comp_mod,
        current_coverages=body.current_coverages or [],
        current_carriers=body.current_carriers or [],
        claims_summary=body.claims_summary,
        vehicle_count=body.vehicle_count,
        uses_subcontractors=body.uses_subcontractors,
        website_url=body.website_url,
        notes=body.notes,
    )
    db.add(account)
    db.flush()

    # Store ingestion event
    ie = IngestionEvent(
        account_id=account.id,
        source_type="manual",
    )
    db.add(ie)

    # Compute health card
    health = compute_account_health(account, db)
    db.commit()

    # Try background artifact generation
    from app.workers.artifact_worker import enqueue_artifact_generation
    enqueued = enqueue_artifact_generation(account.id)
    if not enqueued:
        try:
            generate_all_artifacts(account.id, db, use_llm=False)
            db.commit()
        except Exception:
            logger.exception("Sync artifact generation failed for %s", account.id)

    log_event(db, "account_manual_created", payload={
        "account_id": str(account.id),
        "account_name": body.account_name,
    })

    return {
        "account": AccountResponse.model_validate(account).model_dump(),
        "health": AccountHealthResponse.from_orm_model(health).model_dump(),
    }



@router.get("/accounts/{account_id}/dashboard", tags=["dashboard"])
def account_dashboard(account_id: UUID, db: Session = Depends(get_db)):
    """Get unified dashboard payload for an account.

    Returns account + health card + artifacts + insights in one call.
    Health card is computed on the fly if not cached.
    """
    # Check cache
    from app.core.cache import cache_get, cache_set

    cache_key = f"dashboard:{account_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")

    # Health card — compute if missing
    health = db.query(AccountHealth).filter(AccountHealth.account_id == account_id).first()
    if not health:
        health = compute_account_health(account, db)
        db.commit()

    # Artifacts
    artifacts = (
        db.query(SAModel)
        .filter(SAModel.account_id == account_id)
        .order_by(SAModel.created_at.desc())
        .all()
    )

    # Insights
    insight_items = generate_insights(account, health, db)

    # Memory entries
    from app.services.account_memory_service import list_account_memory

    memory_entries = list_account_memory(db, str(account_id))

    # Market Edge
    from app.services.outcome_learning_service import get_market_edge

    market_edge = get_market_edge(db, industry=account.industry, state=account.state)

    dashboard = {
        "account": AccountResponse.model_validate(account).model_dump(),
        "health": AccountHealthResponse.from_orm_model(health).model_dump(),
        "artifacts": [ArtifactResponse.model_validate(a).model_dump() for a in artifacts],
        "insights": insight_items,
        "memory": memory_entries,
        "market_edge": market_edge,
    }

    cache_set(cache_key, dashboard, ttl=120)
    return dashboard


@router.post("/artifacts/generate", tags=["artifacts"])
def generate_artifacts_endpoint(
    body: dict,
    db: Session = Depends(get_db),
):
    """Generate artifacts for an account. Enqueues background generation."""
    account_id = body.get("account_id")
    if not account_id:
        raise HTTPException(422, "account_id is required")

    account_id = UUID(account_id) if isinstance(account_id, str) else account_id
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")

    artifact_type = body.get("artifact_type")

    # Try background
    from app.workers.artifact_worker import enqueue_artifact_generation
    enqueued = enqueue_artifact_generation(account_id, artifact_type)

    if not enqueued:
        # Sync fallback
        if artifact_type:
            generate_artifact(account_id, artifact_type, db, use_llm=False)
        else:
            generate_all_artifacts(account_id, db, use_llm=False)
        db.commit()
        return {"status": "completed", "account_id": str(account_id)}

    return {"status": "queued", "account_id": str(account_id)}


@router.get("/accounts/{account_id}/insights", tags=["insights"])
def account_insights(account_id: UUID, db: Session = Depends(get_db)):
    """Get insight feed for an account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")

    health = db.query(AccountHealth).filter(AccountHealth.account_id == account_id).first()
    items = generate_insights(account, health, db)

    return {
        "account_id": str(account_id),
        "insights": items,
        "total": len(items),
    }


# ── Service Triage Inbox ─────────────────────────────────────────────────────


@router.post("/triage", tags=["triage"])
@limiter.limit("30/minute")
def create_triage_request_endpoint(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Create a new service triage request and run AI triage."""
    from app.schemas.triage import TriageRequestCreate
    from app.services.triage_service import create_triage_request, run_ai_triage
    from app.workers.triage_worker import enqueue_triage

    data = TriageRequestCreate(**payload)

    triage = create_triage_request(
        db=db,
        input_text=data.input_text,
        input_type=data.input_type,
        account_id=data.account_id,
        agency_id=_user.agency_id,
        created_by_user_id=_user.id,
        input_filename=data.input_filename,
        input_extracted_text=data.input_extracted_text,
    )
    db.flush()

    # Try background triage, fall back to sync
    enqueued = enqueue_triage(triage.id)
    if not enqueued:
        run_ai_triage(db, triage.id)

    db.commit()
    db.refresh(triage)

    from app.schemas.triage import TriageRequestResponse
    return TriageRequestResponse.model_validate(triage)


@router.post("/triage/upload", tags=["triage"])
@limiter.limit("10/minute")
def create_triage_from_file(
    request: Request,
    file: UploadFile = File(...),
    input_text: str = Form(""),
    account_id: str = Form(None),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Create a triage request from a file upload (image, PDF, text)."""
    from app.services.triage_service import create_triage_request, run_ai_triage
    from app.workers.triage_worker import enqueue_triage

    file_bytes = file.file.read()
    capture_result = process_capture(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
    )

    # Use input_text if provided, otherwise use extracted text
    final_text = input_text or capture_result.get("extracted_text", "")
    if not final_text.strip():
        raise HTTPException(400, "No text could be extracted from the file. Please provide input_text.")

    acct_id = UUID(account_id) if account_id else None

    triage = create_triage_request(
        db=db,
        input_text=final_text,
        input_type="file",
        account_id=acct_id,
        agency_id=_user.agency_id,
        created_by_user_id=_user.id,
        input_filename=file.filename,
        input_extracted_text=capture_result.get("extracted_text"),
    )
    db.flush()

    enqueued = enqueue_triage(triage.id)
    if not enqueued:
        run_ai_triage(db, triage.id)

    db.commit()
    db.refresh(triage)

    from app.schemas.triage import TriageRequestResponse
    return TriageRequestResponse.model_validate(triage)


@router.get("/triage", tags=["triage"])
def list_triage_requests_endpoint(
    request: Request,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """List triage requests for the user's agency."""
    from app.services.triage_service import list_triage_requests
    from app.schemas.triage import TriageRequestResponse, TriageRequestListResponse

    results, total = list_triage_requests(
        db=db,
        agency_id=_user.agency_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return TriageRequestListResponse(
        requests=[TriageRequestResponse.model_validate(r) for r in results],
        total=total,
    )


@router.get("/triage/{triage_id}", tags=["triage"])
def get_triage_request_endpoint(
    triage_id: UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Get a single triage request."""
    from app.services.triage_service import get_triage_request
    from app.schemas.triage import TriageRequestResponse

    triage = get_triage_request(db, triage_id)
    if not triage:
        raise HTTPException(404, "Triage request not found")
    return TriageRequestResponse.model_validate(triage)


@router.put("/triage/{triage_id}", tags=["triage"])
def update_triage_request_endpoint(
    triage_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Update triage drafts or metadata (AM editing before approval)."""
    from app.schemas.triage import TriageRequestUpdate, TriageRequestResponse
    from app.services.triage_service import update_triage_drafts

    data = TriageRequestUpdate(**payload)
    triage = update_triage_drafts(db, triage_id, data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(triage)
    return TriageRequestResponse.model_validate(triage)


@router.post("/triage/{triage_id}/approve", tags=["triage"])
def approve_triage_endpoint(
    triage_id: UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Approve a triaged request (marks as approved, records who approved)."""
    from app.services.triage_service import approve_triage
    from app.schemas.triage import TriageRequestResponse

    triage = approve_triage(db, triage_id, _user.id)
    db.commit()
    db.refresh(triage)
    return TriageRequestResponse.model_validate(triage)


@router.post("/triage/{triage_id}/retriage", tags=["triage"])
def retriage_request_endpoint(
    triage_id: UUID,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Re-run AI triage on a request (e.g., after editing input)."""
    from app.services.triage_service import run_ai_triage
    from app.schemas.triage import TriageRequestResponse

    triage = run_ai_triage(db, triage_id)
    db.commit()
    db.refresh(triage)
    return TriageRequestResponse.model_validate(triage)
