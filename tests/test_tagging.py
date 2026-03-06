"""Tests for tag extraction sanity."""

from unittest.mock import MagicMock
from app.services.tagging import (
    INDUSTRY_KEYWORDS, COVERAGE_KEYWORDS, RISK_THEME_KEYWORDS,
    tag_source, tag_chunk,
)
from app.models.models import Source, SourceChunk


def _mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


def test_industry_keywords_populated():
    assert len(INDUSTRY_KEYWORDS) == 10
    assert "roofing" in INDUSTRY_KEYWORDS
    assert "trucking" in INDUSTRY_KEYWORDS


def test_coverage_keywords_populated():
    assert len(COVERAGE_KEYWORDS) == 10
    assert "workers_comp" in COVERAGE_KEYWORDS
    assert "commercial_auto" in COVERAGE_KEYWORDS


def test_tag_source_finds_roofing():
    db = _mock_db()
    source = MagicMock(spec=Source)
    source.id = "test-id"
    source.raw_text = "This article discusses roofing contractor safety and roofer fall protection."
    source.title = "Roofing Safety Guide"

    tags = tag_source(db, source)
    tag_values = [t.tag_value for t in tags]
    assert "roofing" in tag_values


def test_tag_source_finds_coverage():
    db = _mock_db()
    source = MagicMock(spec=Source)
    source.id = "test-id"
    source.raw_text = "Workers comp claims for workplace injury and OSHA violations."
    source.title = "Workers Comp Report"

    tags = tag_source(db, source)
    tag_values = [t.tag_value for t in tags]
    assert "workers_comp" in tag_values


def test_tag_source_finds_jurisdiction():
    db = _mock_db()
    source = MagicMock(spec=Source)
    source.id = "test-id"
    source.raw_text = "North Carolina requires workers comp for employers with 3 or more employees."
    source.title = "NC Insurance Guide"

    tags = tag_source(db, source)
    tag_values = [t.tag_value for t in tags]
    assert "nc" in tag_values


def test_tag_source_conservative():
    """Tags should not appear for unrelated content."""
    db = _mock_db()
    source = MagicMock(spec=Source)
    source.id = "test-id"
    source.raw_text = "The weather today is sunny with a high of 75 degrees."
    source.title = "Weather Report"

    tags = tag_source(db, source)
    # Should find very few or no tags
    assert len(tags) < 3


def test_tag_chunk_finds_risk_theme():
    db = _mock_db()
    chunk = MagicMock(spec=SourceChunk)
    chunk.id = "chunk-id"
    chunk.text_content = "Falls from height are the leading cause of death for roofers. Fall protection is critical."
    chunk.heading = "Fall Risk"

    tags = tag_chunk(db, chunk)
    tag_values = [t.tag_value for t in tags]
    assert "falls_from_height" in tag_values
