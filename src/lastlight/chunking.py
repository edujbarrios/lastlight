"""Small text chunking helpers for passage selection."""

from __future__ import annotations

import re

SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_chars: int = 700) -> list[str]:
    chunks: list[str] = []
    for paragraph in (part.strip() for part in text.split("\n\n")):
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue
        chunks.extend(_chunk_long_paragraph(paragraph, max_chars))
    return chunks or [text[:max_chars].strip()]


def _chunk_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for sentence in SENTENCE_BOUNDARY_RE.split(paragraph):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_wrap(sentence, max_chars))
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def _hard_wrap(text: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while len(remaining) > max_chars:
        split_at = remaining.rfind(" ", 0, max_chars)
        if split_at <= 0:
            split_at = max_chars
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks

