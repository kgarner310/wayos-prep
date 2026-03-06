"""Retrieval service for prep flow."""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import SourceStatus
from app.models.models import (
    Source, SourceChunk, ChunkEmbedding, ChunkTag, SourceTag,
    Query, RetrievalRun, RetrievalResult,
)
from app.services.embeddings import get_query_embedding

logger = logging.getLogger(__name__)

# Scoring weights
W_VECTOR = 0.45
W_TAG_OVERLAP = 0.20
W_AUTHORITY = 0.15
W_FRESHNESS = 0.10
W_JURISDICTION = 0.10

MIN_AUTHORITY_THRESHOLD = 3.0
MIN_FRESHNESS_THRESHOLD = 2.0
TOP_K_CANDIDATES = 50
TOP_K_SELECTED = 8


def run_retrieval(
    db: Session,
    query: Query,
    industry: str,
    state: str,
    employee_count: int | None = None,
    current_mod: float | None = None,
    raw_query: str | None = None,
) -> tuple[RetrievalRun, list[dict]]:
    """Run full retrieval pipeline.

    Returns (retrieval_run, list of scored chunk dicts).
    """
    # Build the query text for embedding
    query_text = _build_query_text(industry, state, employee_count, current_mod, raw_query)

    # Get query embedding
    query_embedding = get_query_embedding(query_text)

    # Determine jurisdiction matches
    jurisdiction_matches = _get_jurisdiction_matches(state)

    # Build filters
    filters = {
        "industry": industry,
        "state": state,
        "jurisdictions": jurisdiction_matches,
        "min_authority": MIN_AUTHORITY_THRESHOLD,
        "min_freshness": MIN_FRESHNESS_THRESHOLD,
    }

    if query_embedding:
        candidates = _vector_search(db, query_embedding, industry, jurisdiction_matches, TOP_K_CANDIDATES)
    else:
        # Fallback: tag-based retrieval without vector search
        candidates = _tag_based_search(db, industry, jurisdiction_matches, TOP_K_CANDIDATES)

    # Score and rerank
    scored = _rerank(candidates, industry, state, jurisdiction_matches)

    # Select top results
    selected = scored[:TOP_K_SELECTED]

    # Store retrieval run
    retrieval_run = RetrievalRun(
        query_id=query.id,
        embedding_model=settings.EMBEDDING_MODEL if query_embedding else None,
        reranker_name="blended_score_v1",
        filters_json=filters,
        candidate_count=len(candidates),
        selected_count=len(selected),
        status="complete",
    )
    db.add(retrieval_run)
    db.flush()

    # Store retrieval results
    for i, item in enumerate(scored):
        result = RetrievalResult(
            retrieval_run_id=retrieval_run.id,
            chunk_id=item["chunk_id"],
            rank_position=i + 1,
            similarity_score=item.get("similarity_score"),
            rerank_score=item.get("final_score"),
            selected=(i < TOP_K_SELECTED),
        )
        db.add(result)

    db.commit()
    db.refresh(retrieval_run)

    return retrieval_run, selected


def _build_query_text(industry: str, state: str, employee_count: int | None,
                      current_mod: float | None, raw_query: str | None) -> str:
    parts = [
        f"{industry} commercial insurance",
        f"in {state}",
    ]
    if employee_count:
        parts.append(f"{employee_count} employees")
    if current_mod:
        parts.append(f"experience mod {current_mod}")
    if raw_query:
        parts.append(raw_query)

    return " ".join(parts)


def _get_jurisdiction_matches(state: str) -> list[str]:
    matches = [state.lower()]
    # Always include federal and national scope
    matches.extend(["federal", "national", "multi_state"])
    return matches


def _vector_search(db: Session, query_embedding: list[float], industry: str,
                   jurisdictions: list[str], limit: int) -> list[dict]:
    """Run vector similarity search with metadata filters."""
    # Use raw SQL for pgvector cosine distance
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Pre-filter: only consider chunks tagged with the requested industry
    # or with a matching jurisdiction. Vector similarity alone is not enough
    # to ensure topical relevance for insurance content.
    sql = text("""
        SELECT
            sc.id as chunk_id,
            sc.source_id,
            sc.text_content,
            sc.heading,
            sc.authority_score,
            sc.freshness_score,
            sc.jurisdiction_state,
            s.title as source_title,
            s.url as source_url,
            s.source_type,
            s.authority_level,
            1 - (ce.embedding <=> :query_embedding::vector) as similarity
        FROM chunk_embeddings ce
        JOIN source_chunks sc ON sc.id = ce.chunk_id
        JOIN sources s ON s.id = sc.source_id
        WHERE s.status = :status
          AND s.authority_score >= :min_authority
          AND s.freshness_score >= :min_freshness
          AND (
            EXISTS (
              SELECT 1 FROM chunk_tags ct
              WHERE ct.chunk_id = sc.id AND ct.tag_type = 'industry' AND ct.tag_value = :industry
            )
            OR EXISTS (
              SELECT 1 FROM chunk_tags ct
              WHERE ct.chunk_id = sc.id AND ct.tag_type = 'jurisdiction' AND ct.tag_value = ANY(:jurisdictions)
            )
          )
        ORDER BY ce.embedding <=> :query_embedding::vector
        LIMIT :limit
    """)

    results = db.execute(sql, {
        "query_embedding": embedding_str,
        "status": SourceStatus.READY,
        "min_authority": MIN_AUTHORITY_THRESHOLD,
        "min_freshness": MIN_FRESHNESS_THRESHOLD,
        "industry": industry,
        "jurisdictions": jurisdictions,
        "limit": limit,
    }).fetchall()

    candidates = []
    for row in results:
        # Get tags for this chunk
        chunk_tags = db.query(ChunkTag).filter(ChunkTag.chunk_id == row.chunk_id).all()
        tag_set = {(t.tag_type, t.tag_value) for t in chunk_tags}

        candidates.append({
            "chunk_id": row.chunk_id,
            "source_id": row.source_id,
            "text_content": row.text_content,
            "heading": row.heading,
            "authority_score": float(row.authority_score),
            "freshness_score": float(row.freshness_score),
            "jurisdiction_state": row.jurisdiction_state,
            "source_title": row.source_title,
            "source_url": row.source_url,
            "similarity_score": float(row.similarity) if row.similarity else 0.0,
            "tags": tag_set,
        })

    return candidates


def _tag_based_search(db: Session, industry: str, jurisdictions: list[str],
                      limit: int) -> list[dict]:
    """Fallback retrieval using tag matching when embeddings unavailable.

    Filters to chunks that have an industry or jurisdiction tag matching the query.
    """
    # Find chunk IDs that have a matching industry tag
    industry_chunk_ids = (
        db.query(ChunkTag.chunk_id)
        .filter(ChunkTag.tag_type == "industry", ChunkTag.tag_value == industry)
        .subquery()
    )

    # Find chunk IDs that have a matching jurisdiction tag
    jurisdiction_chunk_ids = (
        db.query(ChunkTag.chunk_id)
        .filter(ChunkTag.tag_type == "jurisdiction", ChunkTag.tag_value.in_(jurisdictions))
        .subquery()
    )

    # Get chunks that match industry OR jurisdiction (prefer those matching both via rerank)
    from sqlalchemy import or_
    chunks = (
        db.query(SourceChunk)
        .join(Source, Source.id == SourceChunk.source_id)
        .filter(Source.status == SourceStatus.READY)
        .filter(Source.authority_score >= MIN_AUTHORITY_THRESHOLD)
        .filter(
            or_(
                SourceChunk.id.in_(industry_chunk_ids),
                SourceChunk.id.in_(jurisdiction_chunk_ids),
            )
        )
        .limit(limit)
        .all()
    )

    candidates = []
    for chunk in chunks:
        chunk_tags = db.query(ChunkTag).filter(ChunkTag.chunk_id == chunk.id).all()
        tag_set = {(t.tag_type, t.tag_value) for t in chunk_tags}

        source = chunk.source
        candidates.append({
            "chunk_id": chunk.id,
            "source_id": chunk.source_id,
            "text_content": chunk.text_content,
            "heading": chunk.heading,
            "authority_score": float(chunk.authority_score),
            "freshness_score": float(chunk.freshness_score),
            "jurisdiction_state": chunk.jurisdiction_state,
            "source_title": source.title if source else "",
            "source_url": source.url if source else None,
            "similarity_score": 0.0,  # no vector similarity for tag-only results
            "tags": tag_set,
        })

    return candidates


def _rerank(candidates: list[dict], industry: str, state: str,
            jurisdictions: list[str]) -> list[dict]:
    """Rerank candidates using blended scoring."""
    if not candidates:
        return []

    # Normalize scores
    max_authority = max(c["authority_score"] for c in candidates) or 1
    max_freshness = max(c["freshness_score"] for c in candidates) or 1

    for c in candidates:
        # Tag overlap score
        tag_overlap = 0.0
        tags = c.get("tags", set())
        if ("industry", industry) in tags:
            tag_overlap += 0.5
        if any(("jurisdiction", j) in tags for j in jurisdictions):
            tag_overlap += 0.3
        # Check for coverage/risk theme tags (any match is good)
        coverage_tags = [t for t in tags if t[0] == "coverage"]
        risk_tags = [t for t in tags if t[0] == "risk_theme"]
        if coverage_tags:
            tag_overlap += 0.1
        if risk_tags:
            tag_overlap += 0.1
        tag_overlap = min(tag_overlap, 1.0)

        # Jurisdiction match score
        jur_match = 0.0
        chunk_state = (c.get("jurisdiction_state") or "").lower()
        if chunk_state == state.lower():
            jur_match = 1.0
        elif chunk_state in ("federal", "national", "multi_state"):
            jur_match = 0.6
        elif any(("jurisdiction", j) in tags for j in jurisdictions):
            jur_match = 0.4

        # Normalized scores
        authority_norm = c["authority_score"] / max_authority
        freshness_norm = c["freshness_score"] / max_freshness

        # Blended final score
        final_score = (
            W_VECTOR * c["similarity_score"] +
            W_TAG_OVERLAP * tag_overlap +
            W_AUTHORITY * authority_norm +
            W_FRESHNESS * freshness_norm +
            W_JURISDICTION * jur_match
        )

        c["final_score"] = round(final_score, 6)
        c["tag_overlap_score"] = tag_overlap
        c["jurisdiction_match_score"] = jur_match

    # Sort by final score descending
    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return candidates
