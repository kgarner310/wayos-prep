"""Text chunking service. Heading-aware with paragraph fallback."""

import hashlib
import logging
import re

logger = logging.getLogger(__name__)

TARGET_MIN_TOKENS = 300
TARGET_MAX_TOKENS = 800
OVERLAP_TOKENS = 50

# Rough token estimate: 1 token ~ 4 chars
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def chunk_text(text: str, source_jurisdiction: str | None = None,
               source_jurisdiction_state: str | None = None,
               authority_score: float = 5.0,
               freshness_score: float = 5.0) -> list[dict]:
    """Chunk text into pieces targeting 300-800 tokens.

    Returns list of dicts with keys:
        chunk_index, heading, text_content, token_count, char_count, chunk_hash,
        jurisdiction, jurisdiction_state, authority_score, freshness_score
    """
    if not text or not text.strip():
        return []

    sections = _split_by_headings(text)

    chunks = []
    chunk_index = 0

    for section in sections:
        heading = section.get("heading")
        content = section["content"]
        token_est = estimate_tokens(content)

        if token_est <= TARGET_MAX_TOKENS:
            if token_est >= 10:  # skip tiny fragments
                chunks.append(_make_chunk(
                    chunk_index, heading, content,
                    source_jurisdiction, source_jurisdiction_state,
                    authority_score, freshness_score
                ))
                chunk_index += 1
        else:
            # Split large sections by paragraphs
            sub_chunks = _split_by_paragraphs(content, heading)
            for sc in sub_chunks:
                chunks.append(_make_chunk(
                    chunk_index, sc.get("heading", heading), sc["content"],
                    source_jurisdiction, source_jurisdiction_state,
                    authority_score, freshness_score
                ))
                chunk_index += 1

    # Add overlap between adjacent chunks
    chunks = _add_overlap(chunks)

    return chunks


def _split_by_headings(text: str) -> list[dict]:
    """Split text into sections by headings."""
    lines = text.split('\n')
    sections = []
    current_heading = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        is_heading = False

        if stripped.startswith('#'):
            is_heading = True
            heading_text = stripped.lstrip('#').strip()
        elif stripped.isupper() and 3 < len(stripped) < 80 and not stripped.endswith('.'):
            is_heading = True
            heading_text = stripped

        if is_heading:
            if current_lines:
                content = '\n'.join(current_lines).strip()
                if content:
                    sections.append({"heading": current_heading, "content": content})
            current_heading = heading_text if is_heading else None
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        content = '\n'.join(current_lines).strip()
        if content:
            sections.append({"heading": current_heading, "content": content})

    if not sections and text.strip():
        sections = [{"heading": None, "content": text.strip()}]

    return sections


def _split_by_paragraphs(text: str, heading: str | None) -> list[dict]:
    """Split a large section into paragraph-based chunks."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_tokens = estimate_tokens(para)

        if current_tokens + para_tokens > TARGET_MAX_TOKENS and current_chunk:
            chunks.append({
                "heading": heading,
                "content": '\n\n'.join(current_chunk)
            })
            current_chunk = []
            current_tokens = 0

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunks.append({
            "heading": heading,
            "content": '\n\n'.join(current_chunk)
        })

    return chunks


def _add_overlap(chunks: list[dict]) -> list[dict]:
    """Add light overlap between adjacent chunks."""
    if len(chunks) <= 1:
        return chunks

    overlap_chars = OVERLAP_TOKENS * CHARS_PER_TOKEN

    for i in range(1, len(chunks)):
        prev_text = chunks[i - 1]["text_content"]
        if len(prev_text) > overlap_chars:
            overlap = prev_text[-overlap_chars:]
            # Find a sentence boundary in the overlap
            last_period = overlap.rfind('. ')
            if last_period > 0:
                overlap = overlap[last_period + 2:]
            chunks[i]["text_content"] = overlap + "\n\n" + chunks[i]["text_content"]
            chunks[i]["token_count"] = estimate_tokens(chunks[i]["text_content"])
            chunks[i]["char_count"] = len(chunks[i]["text_content"])
            chunks[i]["chunk_hash"] = hashlib.sha256(chunks[i]["text_content"].encode()).hexdigest()

    return chunks


def _make_chunk(index: int, heading: str | None, content: str,
                jurisdiction: str | None, jurisdiction_state: str | None,
                authority_score: float, freshness_score: float) -> dict:
    return {
        "chunk_index": index,
        "heading": heading,
        "text_content": content,
        "token_count": estimate_tokens(content),
        "char_count": len(content),
        "chunk_hash": hashlib.sha256(content.encode()).hexdigest(),
        "jurisdiction": jurisdiction,
        "jurisdiction_state": jurisdiction_state,
        "authority_score": authority_score,
        "freshness_score": freshness_score,
    }
