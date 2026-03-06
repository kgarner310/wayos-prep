"""Parser/cleaner for raw source text."""

import re
import logging

logger = logging.getLogger(__name__)


def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text = raw_text

    # Remove common nav/footer patterns
    nav_patterns = [
        r'(?i)skip to (main )?content',
        r'(?i)cookie (policy|consent|notice).*?\n',
        r'(?i)subscribe to our newsletter.*?\n',
        r'(?i)follow us on.*?\n',
        r'(?i)share this (article|post|page).*?\n',
        r'(?i)related (articles|posts|stories).*?\n',
        r'(?i)copyright \d{4}.*?\n',
        r'(?i)all rights reserved.*?\n',
        r'(?i)privacy policy.*?\n',
        r'(?i)terms (of (use|service)|and conditions).*?\n',
    ]
    for pattern in nav_patterns:
        text = re.sub(pattern, '\n', text)

    # Normalize whitespace
    text = re.sub(r'\t', ' ', text)
    text = re.sub(r' {3,}', '  ', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Remove zero-width chars
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)

    # Strip leading/trailing whitespace per line while preserving structure
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)

    # Collapse runs of blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_headings(text: str) -> list[dict]:
    """Extract heading-like lines from text."""
    headings = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Markdown headings
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            headings.append({"line": i, "level": level, "text": stripped.lstrip('#').strip()})
        # ALL CAPS short lines (likely headings)
        elif stripped.isupper() and 3 < len(stripped) < 80:
            headings.append({"line": i, "level": 2, "text": stripped})

    return headings
