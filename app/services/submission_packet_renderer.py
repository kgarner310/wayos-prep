"""Submission Packet Renderer — plain text and markdown output."""

from __future__ import annotations


def render_plain_text(title: str, sections: list[dict], workspace: dict) -> str:
    """Render a submission packet as copyable plain text."""
    lines = []
    lines.append(title.upper())
    lines.append("=" * len(title))
    lines.append("")

    for section in sections:
        lines.append(section["title"].upper())
        lines.append("-" * len(section["title"]))
        if section.get("body"):
            lines.append(section["body"])
        for item in section.get("items", []):
            lines.append(f"  - {item}")
        lines.append("")

    return "\n".join(lines)


def render_markdown(title: str, sections: list[dict], workspace: dict) -> str:
    """Render a submission packet as markdown."""
    lines = []
    lines.append(f"# {title}")
    lines.append("")

    for section in sections:
        lines.append(f"## {section['title']}")
        lines.append("")
        if section.get("body"):
            lines.append(section["body"])
            lines.append("")
        for item in section.get("items", []):
            lines.append(f"- {item}")
        if section.get("items"):
            lines.append("")

    return "\n".join(lines)
