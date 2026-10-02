"""Markdown-aware retrieval sections for long guidance documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

ATX_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass(frozen=True)
class MarkdownSection:
    """One structurally meaningful Markdown section.

    ``heading_path`` preserves the heading hierarchy that leads to the section.
    ``body`` contains only the content owned by that heading, without content
    from later sibling/child sections.
    """

    heading_path: tuple[str, ...]
    body: str


def markdown_sections(text: str) -> list[MarkdownSection]:
    """Split Markdown on ATX headings while respecting fenced code blocks.

    Text before the first heading is retained as an unheaded section. Empty
    heading sections are omitted, so a hierarchy-only parent does not become a
    retrieval candidate unless it has its own prose.
    """

    sections: list[MarkdownSection] = []
    heading_stack: list[tuple[int, str]] = []
    current_path: tuple[str, ...] = ()
    current_lines: list[str] = []
    active_fence: tuple[str, int] | None = None

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(MarkdownSection(current_path, body))
        current_lines.clear()

    for line in text.splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            marker_key = (marker[0], len(marker))
            if active_fence is None:
                active_fence = marker_key
            elif marker_key[0] == active_fence[0] and marker_key[1] >= active_fence[1]:
                active_fence = None
            current_lines.append(line)
            continue

        if active_fence is None:
            heading = ATX_HEADING_RE.match(line)
            if heading:
                flush()
                level = len(heading.group(1))
                title = heading.group(2).strip()
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, title))
                current_path = tuple(item[1] for item in heading_stack)
                continue

        current_lines.append(line)

    flush()
    return sections
