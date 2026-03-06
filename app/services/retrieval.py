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
from app.services.graph_expansion import expand_risk_graph, get_expansion_seeds

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
    entity_type: str | None = None,
    public_entity_type: str | None = None,
    department: str | None = None,
) -> tuple[RetrievalRun, list[dict]]:
    """Run full retrieval pipeline.

    Returns (retrieval_run, list of scored chunk dicts).
    """
    # Build the query text for embedding
    query_text = _build_query_text(
        industry, state, employee_count, current_mod, raw_query,
        entity_type=entity_type, public_entity_type=public_entity_type,
        department=department,
    )

    # Get query embedding
    query_embedding = get_query_embedding(query_text)

    # Determine jurisdiction matches
    jurisdiction_matches = _get_jurisdiction_matches(state)

    # Graph expansion — discover related themes/coverages
    seeds = get_expansion_seeds(
        industry, state,
        entity_type=entity_type,
        public_entity_type=public_entity_type,
        department=department,
    )
    graph_result = expand_risk_graph(db, seeds, depth=1)
    expanded_risk_themes = graph_result.get("expanded_risk_themes", [])
    expanded_coverages = graph_result.get("expanded_coverages", [])
    expanded_question_categories = graph_result.get("expanded_question_categories", [])

    # Build filters
    filters = {
        "industry": industry,
        "state": state,
        "jurisdictions": jurisdiction_matches,
        "min_authority": MIN_AUTHORITY_THRESHOLD,
        "min_freshness": MIN_FRESHNESS_THRESHOLD,
    }
    if entity_type:
        filters["entity_type"] = entity_type
    if public_entity_type:
        filters["public_entity_type"] = public_entity_type
    if department:
        filters["department"] = department
    if expanded_risk_themes:
        filters["graph_expanded_risk_themes"] = expanded_risk_themes
    if expanded_coverages:
        filters["graph_expanded_coverages"] = expanded_coverages
    if expanded_question_categories:
        filters["graph_expanded_question_categories"] = expanded_question_categories

    if query_embedding:
        candidates = _vector_search(
            db, query_embedding, industry, jurisdiction_matches, TOP_K_CANDIDATES,
            entity_type=entity_type, public_entity_type=public_entity_type,
            department=department,
        )
    else:
        # Fallback: tag-based retrieval without vector search
        candidates = _tag_based_search(
            db, industry, jurisdiction_matches, TOP_K_CANDIDATES,
            entity_type=entity_type, public_entity_type=public_entity_type,
            department=department,
        )

    # Score and rerank
    scored = _rerank(
        candidates, industry, state, jurisdiction_matches,
        entity_type=entity_type, public_entity_type=public_entity_type,
        department=department,
        expanded_risk_themes=expanded_risk_themes,
        expanded_coverages=expanded_coverages,
    )

    # Select top results
    selected = scored[:TOP_K_SELECTED]

    # Store retrieval run (include graph expansion in filters_json for debug)
    if graph_result.get("expanded_themes"):
        filters["graph_expansion"] = {
            "seed_count": graph_result["seed_count"],
            "expansion_hops": graph_result["expansion_hops"],
            "expanded_themes": [
                {"name": t["name"], "node_type": t["node_type"], "weight": t["weight"]}
                for t in graph_result["expanded_themes"][:10]
            ],
        }

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
                      current_mod: float | None, raw_query: str | None,
                      entity_type: str | None = None,
                      public_entity_type: str | None = None,
                      department: str | None = None) -> str:
    if entity_type == "public_entity":
        parts = [f"municipal government public entity insurance"]
        if public_entity_type:
            parts.append(public_entity_type.replace("_", " "))
        if department:
            parts.append(f"{department.replace('_', ' ')} department")
        parts.append(f"in {state}")
    else:
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
                   jurisdictions: list[str], limit: int,
                   entity_type: str | None = None,
                   public_entity_type: str | None = None,
                   department: str | None = None) -> list[dict]:
    """Run vector similarity search with metadata filters."""
    # Use raw SQL for pgvector cosine distance
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Pre-filter: only consider chunks tagged with the requested industry
    # or with a matching jurisdiction. Vector similarity alone is not enough
    # to ensure topical relevance for insurance content.
    # Build entity-type filter clause for public entity queries
    entity_filter = ""
    params = {
        "query_embedding": embedding_str,
        "status": SourceStatus.READY,
        "min_authority": MIN_AUTHORITY_THRESHOLD,
        "min_freshness": MIN_FRESHNESS_THRESHOLD,
        "industry": industry,
        "jurisdictions": jurisdictions,
        "limit": limit,
    }

    if entity_type == "public_entity":
        # For public entities, prioritize chunks tagged as public_entity or with matching subtype/dept
        entity_clauses = [
            "EXISTS (SELECT 1 FROM chunk_tags ct WHERE ct.chunk_id = sc.id AND ct.tag_type = 'entity_type' AND ct.tag_value = 'public_entity')",
            "EXISTS (SELECT 1 FROM chunk_tags ct WHERE ct.chunk_id = sc.id AND ct.tag_type = 'jurisdiction' AND ct.tag_value = ANY(:jurisdictions))",
        ]
        if public_entity_type:
            entity_clauses.append(
                "EXISTS (SELECT 1 FROM chunk_tags ct WHERE ct.chunk_id = sc.id AND ct.tag_type = 'public_entity_type' AND ct.tag_value = :public_entity_type)"
            )
            params["public_entity_type"] = public_entity_type
        if department:
            entity_clauses.append(
                "EXISTS (SELECT 1 FROM chunk_tags ct WHERE ct.chunk_id = sc.id AND ct.tag_type = 'department' AND ct.tag_value = :department)"
            )
            params["department"] = department
        entity_filter = "AND (" + " OR ".join(entity_clauses) + ")"
    else:
        entity_filter = """AND (
            EXISTS (
              SELECT 1 FROM chunk_tags ct
              WHERE ct.chunk_id = sc.id AND ct.tag_type = 'industry' AND ct.tag_value = :industry
            )
            OR EXISTS (
              SELECT 1 FROM chunk_tags ct
              WHERE ct.chunk_id = sc.id AND ct.tag_type = 'jurisdiction' AND ct.tag_value = ANY(:jurisdictions)
            )
          )"""

    sql = text(f"""
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
          {entity_filter}
        ORDER BY ce.embedding <=> :query_embedding::vector
        LIMIT :limit
    """)

    results = db.execute(sql, params).fetchall()

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
                      limit: int,
                      entity_type: str | None = None,
                      public_entity_type: str | None = None,
                      department: str | None = None) -> list[dict]:
    """Fallback retrieval using tag matching when embeddings unavailable.

    Filters to chunks that have an industry or jurisdiction tag matching the query.
    For public entity queries, also matches entity_type, public_entity_type, and department tags.
    """
    from sqlalchemy import or_

    # Build subqueries for matching tags
    filter_subqueries = []

    if entity_type == "public_entity":
        # Match chunks tagged as public_entity
        entity_chunk_ids = (
            db.query(ChunkTag.chunk_id)
            .filter(ChunkTag.tag_type == "entity_type", ChunkTag.tag_value == "public_entity")
            .subquery()
        )
        filter_subqueries.append(SourceChunk.id.in_(entity_chunk_ids))

        if public_entity_type:
            pet_chunk_ids = (
                db.query(ChunkTag.chunk_id)
                .filter(ChunkTag.tag_type == "public_entity_type", ChunkTag.tag_value == public_entity_type)
                .subquery()
            )
            filter_subqueries.append(SourceChunk.id.in_(pet_chunk_ids))

        if department:
            dept_chunk_ids = (
                db.query(ChunkTag.chunk_id)
                .filter(ChunkTag.tag_type == "department", ChunkTag.tag_value == department)
                .subquery()
            )
            filter_subqueries.append(SourceChunk.id.in_(dept_chunk_ids))
    else:
        # Standard private-business matching: industry tag
        industry_chunk_ids = (
            db.query(ChunkTag.chunk_id)
            .filter(ChunkTag.tag_type == "industry", ChunkTag.tag_value == industry)
            .subquery()
        )
        filter_subqueries.append(SourceChunk.id.in_(industry_chunk_ids))

    # Always include jurisdiction matching
    jurisdiction_chunk_ids = (
        db.query(ChunkTag.chunk_id)
        .filter(ChunkTag.tag_type == "jurisdiction", ChunkTag.tag_value.in_(jurisdictions))
        .subquery()
    )
    filter_subqueries.append(SourceChunk.id.in_(jurisdiction_chunk_ids))

    # Get chunks that match any of the filter subqueries
    chunks = (
        db.query(SourceChunk)
        .join(Source, Source.id == SourceChunk.source_id)
        .filter(Source.status == SourceStatus.READY)
        .filter(Source.authority_score >= MIN_AUTHORITY_THRESHOLD)
        .filter(or_(*filter_subqueries))
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
            jurisdictions: list[str],
            entity_type: str | None = None,
            public_entity_type: str | None = None,
            department: str | None = None,
            expanded_risk_themes: list[str] | None = None,
            expanded_coverages: list[str] | None = None) -> list[dict]:
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

        if entity_type == "public_entity":
            # Public entity scoring: boost entity_type and department matches
            if ("entity_type", "public_entity") in tags:
                tag_overlap += 0.4
            if public_entity_type and ("public_entity_type", public_entity_type) in tags:
                tag_overlap += 0.3
            if department and ("department", department) in tags:
                tag_overlap += 0.2
        else:
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

        # Graph expansion bonus: boost chunks that match graph-expanded themes/coverages
        graph_bonus = 0.0
        if expanded_risk_themes:
            matched_expanded = [t for t in tags if t[0] == "risk_theme" and t[1] in expanded_risk_themes]
            if matched_expanded:
                graph_bonus += min(len(matched_expanded) * 0.08, 0.15)
        if expanded_coverages:
            matched_cov = [t for t in tags if t[0] == "coverage" and t[1] in expanded_coverages]
            if matched_cov:
                graph_bonus += min(len(matched_cov) * 0.06, 0.10)
        tag_overlap += graph_bonus

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
