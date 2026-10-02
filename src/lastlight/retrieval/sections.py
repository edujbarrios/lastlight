"""Markdown-aware retrieval units for long guidance documents."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from ..domain import KnowledgeDocument
from .chunking import overlapping_chunks

ATX_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
SECTION_AWARE_MIN_CHARS = 4_000
RETRIEVAL_UNIT_MAX_CHARS = 1_800
RETRIEVAL_UNIT_OVERLAP_CHARS = 250


@dataclass(frozen=True)
class MarkdownSection:
    """One structurally meaningful Markdown section."""

    heading_path: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class RetrievalUnit:
    """Internal scoring unit that still points back to its source document."""

    source_index: int
    source: KnowledgeDocument
    ranking_document: KnowledgeDocument
    passage_body: str
    heading_path: tuple[str, ...] = ()


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


def retrieval_units(documents: list[KnowledgeDocument]) -> list[RetrievalUnit]:
    """Create bounded scoring units for sufficiently large documents.

    Small documents keep the exact legacy scoring representation. Long documents
    are split first by Markdown structure and then, when needed, into bounded
    overlapping chunks. This also improves large unstructured documents and
    guides that contain one oversized section.
    """

    units: list[RetrievalUnit] = []
    for source_index, document in enumerate(documents):
        units.extend(document_retrieval_units(document, source_index=source_index))
    return units


def document_retrieval_units(
    document: KnowledgeDocument,
    *,
    source_index: int = 0,
) -> list[RetrievalUnit]:
    if len(document.body) < SECTION_AWARE_MIN_CHARS:
        return [_legacy_unit(document, source_index)]

    sections = markdown_sections(document.body)
    if not sections:
        return [_legacy_unit(document, source_index)]

    units: list[RetrievalUnit] = []
    for section in sections:
        title = _section_ranking_title(document.title, section.heading_path)
        for chunk in overlapping_chunks(
            section.body,
            max_chars=RETRIEVAL_UNIT_MAX_CHARS,
            overlap_chars=RETRIEVAL_UNIT_OVERLAP_CHARS,
        ):
            units.append(
                RetrievalUnit(
                    source_index=source_index,
                    source=document,
                    ranking_document=replace(document, title=title, body=chunk),
                    passage_body=chunk,
                    heading_path=section.heading_path,
                )
            )

    return units or [_legacy_unit(document, source_index)]


def _legacy_unit(document: KnowledgeDocument, source_index: int) -> RetrievalUnit:
    return RetrievalUnit(
        source_index=source_index,
        source=document,
        ranking_document=document,
        passage_body=document.body,
    )


def _section_ranking_title(document_title: str, heading_path: tuple[str, ...]) -> str:
    if not heading_path:
        return document_title

    components = heading_path
    if heading_path[0].strip().casefold() == document_title.strip().casefold():
        components = heading_path[1:]
    if not components:
        return document_title
    return f"{document_title} > {' > '.join(components)}"
