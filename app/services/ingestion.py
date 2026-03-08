"""Source ingestion service."""

import hashlib
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.models import Source
from app.core.enums import SourceStatus
from app.services.scoring import compute_authority_score, compute_freshness_score
from app.services.url_guard import validate_external_url

logger = logging.getLogger(__name__)


def ingest_raw_text(
    db: Session,
    title: str,
    raw_text: str,
    source_type: str = "article",
    authority_level: str = "trade",
    jurisdiction_state: str | None = None,
    published_at: datetime | None = None,
    publisher: str | None = None,
    author: str | None = None,
) -> Source:
    doc_hash = hashlib.sha256(raw_text.encode()).hexdigest()

    source = Source(
        source_type=source_type,
        title=title,
        raw_text=raw_text,
        document_hash=doc_hash,
        authority_level=authority_level,
        authority_score=compute_authority_score(authority_level),
        freshness_score=compute_freshness_score(published_at),
        jurisdiction_state=jurisdiction_state,
        published_at=published_at,
        publisher=publisher,
        author=author,
        status=SourceStatus.NEW,
    )

    db.add(source)
    db.commit()
    db.refresh(source)
    logger.info(f"Ingested text source: {source.id} - {title}")
    return source


def ingest_url(
    db: Session,
    url: str,
    source_type: str = "article",
    authority_level: str = "trade",
    jurisdiction_state: str | None = None,
) -> Source:
    """Fetch URL, extract text, and create source."""
    validated_url = validate_external_url(url)
    try:
        resp = httpx.get(validated_url, timeout=10, follow_redirects=False, headers={
            "User-Agent": "WAYOS-PREP/1.0 (internal research tool)"
        })
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"Failed to fetch URL: {e}")

    html = resp.text
    soup = BeautifulSoup(html, "lxml")

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else url

    # Remove script/style/nav/footer elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Extract visible text
    raw_text = soup.get_text(separator="\n", strip=True)

    if not raw_text or len(raw_text) < 50:
        raise ValueError("Extracted text too short to be useful")

    doc_hash = hashlib.sha256(raw_text.encode()).hexdigest()

    source = Source(
        source_type=source_type,
        title=title,
        url=url,
        canonical_url=url,
        raw_text=raw_text,
        document_hash=doc_hash,
        authority_level=authority_level,
        authority_score=compute_authority_score(authority_level),
        freshness_score=compute_freshness_score(None),
        jurisdiction_state=jurisdiction_state,
        status=SourceStatus.NEW,
    )

    db.add(source)
    db.commit()
    db.refresh(source)
    logger.info(f"Ingested URL source: {source.id} - {title}")
    return source


def ingest_file(
    db: Session,
    filename: str,
    content: str,
    source_type: str = "article",
    authority_level: str = "trade",
    jurisdiction_state: str | None = None,
) -> Source:
    """Ingest a text file upload."""
    doc_hash = hashlib.sha256(content.encode()).hexdigest()

    source = Source(
        source_type=source_type,
        title=filename,
        raw_text=content,
        document_hash=doc_hash,
        authority_level=authority_level,
        authority_score=compute_authority_score(authority_level),
        freshness_score=compute_freshness_score(None),
        jurisdiction_state=jurisdiction_state,
        status=SourceStatus.NEW,
    )

    db.add(source)
    db.commit()
    db.refresh(source)
    logger.info(f"Ingested file source: {source.id} - {filename}")
    return source
