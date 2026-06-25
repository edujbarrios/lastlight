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


def sentence_windows(text: str, max_chars: int = 700) -> list[str]:
    """Return sentence-aware windows with useful local context."""
    windows: list[str] = []
    for paragraph in (part.strip() for part in text.split("\n\n")):
        if not paragraph:
            continue
        sentences = [
            sentence.strip()
            for sentence in SENTENCE_BOUNDARY_RE.split(paragraph)
            if sentence.strip()
        ]
        if not sentences:
            continue
        for index in range(len(sentences)):
            window = _window_around_sentence(sentences, index, max_chars)
            if window and window not in windows:
                windows.append(window)
    return windows or chunk_text(text, max_chars=max_chars)


def _window_around_sentence(
    sentences: list[str], center_index: int, max_chars: int
) -> str:
    selected = [sentences[center_index]]
    left = center_index - 1
    right = center_index + 1

    while True:
        changed = False
        if right < len(sentences):
            candidate = " ".join([*selected, sentences[right]])
            if len(candidate) <= max_chars:
                selected.append(sentences[right])
                right += 1
                changed = True
        if left >= 0:
            candidate = " ".join([sentences[left], *selected])
            if len(candidate) <= max_chars:
                selected.insert(0, sentences[left])
                left -= 1
                changed = True
        if not changed:
            break

    window = " ".join(selected).strip()
    if len(window) > max_chars:
        return _hard_wrap(window, max_chars)[0]
    return window
