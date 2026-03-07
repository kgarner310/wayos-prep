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
from app.services.producer_ammo import generate_producer_ammo
from app.services.agency_ammo_feed import build_agency_ammo_feed
from app.services.discovery_capture import save_discovery
from app.services.instrumentation import log_event, get_product_signals
from app.services.loss_run_analyzer import analyze_loss_run
from app.schemas.loss_run import LossRunRequest, LossRunAnalysisResponse
from app.services.experience_mod_analyzer import analyze_experience_mod
from app.schemas.experience_mod import ExperienceModRequest, ExperienceModResponse
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
):
    """Detect coverage gaps using Industry Knowledge Objects.

    Compares current policies against the industry profile's expected
    policy lines to identify missing coverages and risk level.

    current_policies is a comma-separated list of policy names.
    """
    policies = [p.strip() for p in current_policies.split(",") if p.strip()]
    result = detect_knowledge_gaps(industry, policies)
    return result


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

@router.post("/accounts", response_model=AccountResponse, tags=["accounts"])
def create_account_endpoint(payload: AccountCreate, db: Session = Depends(get_db)):
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
def update_account_endpoint(account_id: UUID, payload: AccountUpdate, db: Session = Depends(get_db)):
    """Update an account."""
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    account = update_account(db, account_id, data)
    if not account:
        raise HTTPException(404, "Account not found")
    log_event(db, "account_updated", payload={"account_id": str(account_id)})
    return account


@router.delete("/accounts/{account_id}", tags=["accounts"])
def delete_account_endpoint(account_id: UUID, db: Session = Depends(get_db)):
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
def seed_demo_data_endpoint(db: Session = Depends(get_db)):
    """Seed demo accounts with realistic data. Internal-only."""
    results = seed_demo_accounts(db)
    created = sum(1 for r in results if r["status"] == "created")
    return {"accounts": results, "created": created, "total": len(results)}


@router.post("/demo/reset", tags=["demo-admin"])
def reset_demo_data_endpoint(db: Session = Depends(get_db)):
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
