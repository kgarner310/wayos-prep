"""Tests for the parser service."""

from app.services.parser import clean_text, extract_headings


def test_clean_text_removes_nav():
    text = "Skip to main content\nActual article text here\nCopyright 2025 Company"
    cleaned = clean_text(text)
    assert "Skip to main content" not in cleaned
    assert "Actual article text" in cleaned


def test_clean_text_normalizes_whitespace():
    text = "Line 1\n\n\n\n\n\nLine 2\n\n\n\n\nLine 3"
    cleaned = clean_text(text)
    assert "\n\n\n\n" not in cleaned
    assert "Line 1" in cleaned
    assert "Line 2" in cleaned


def test_clean_text_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_clean_text_preserves_content():
    text = "Workers compensation claims for roofing\n\n- Falls from height\n- Equipment injury"
    cleaned = clean_text(text)
    assert "Workers compensation" in cleaned
    assert "Falls from height" in cleaned


def test_extract_headings():
    text = "# Main Title\n\nSome content\n\n## Sub Heading\n\nMore content"
    headings = extract_headings(text)
    assert len(headings) >= 2
    assert headings[0]["text"] == "Main Title"


def test_extract_caps_headings():
    text = "IMPORTANT NOTICE\n\nThis is important content."
    headings = extract_headings(text)
    assert len(headings) >= 1
