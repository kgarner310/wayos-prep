"""Tests for the chunking service."""

from app.services.chunker import chunk_text, estimate_tokens


def test_estimate_tokens():
    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("a" * 400) == 100  # ~4 chars per token


def test_chunk_empty_text():
    assert chunk_text("") == []
    assert chunk_text("   ") == []
    assert chunk_text(None) == []


def test_chunk_short_text():
    text = "This is a short paragraph about roofing safety.\n\nFalls are the #1 risk."
    chunks = chunk_text(text)
    assert len(chunks) >= 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["text_content"]
    assert chunks[0]["token_count"] > 0
    assert chunks[0]["char_count"] > 0
    assert chunks[0]["chunk_hash"]


def test_chunk_with_headings():
    text = """# Section One

This is content under section one. It discusses important topics about insurance.

# Section Two

This is content under section two. It covers different aspects of risk management.

# Section Three

This is the third section with more detail about coverage options.
"""
    chunks = chunk_text(text)
    assert len(chunks) >= 2
    # Check that headings are captured
    headings = [c["heading"] for c in chunks if c.get("heading")]
    assert len(headings) > 0


def test_chunk_large_text():
    # Create text that exceeds max token target
    paragraphs = []
    for i in range(20):
        paragraphs.append(f"Paragraph {i}: " + "This is a detailed paragraph about commercial insurance risk factors. " * 10)
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text)
    assert len(chunks) > 1
    # Check sequential indexing
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i


def test_chunk_preserves_metadata():
    text = "This is a test chunk about workers compensation in North Carolina."
    chunks = chunk_text(text, source_jurisdiction_state="nc",
                        authority_score=8.0, freshness_score=7.5)
    assert len(chunks) == 1
    assert chunks[0]["jurisdiction_state"] == "nc"
    assert chunks[0]["authority_score"] == 8.0
    assert chunks[0]["freshness_score"] == 7.5


def test_chunk_all_caps_heading():
    text = """IMPORTANT SAFETY NOTICE

All workers must wear fall protection when working above 6 feet.

EQUIPMENT REQUIREMENTS

Hard hats, safety glasses, and steel-toed boots are required on all job sites.
"""
    chunks = chunk_text(text)
    headings = [c["heading"] for c in chunks if c.get("heading")]
    assert any("SAFETY" in h or "EQUIPMENT" in h for h in headings)
