"""Small text chunking helpers for passage selection and retrieval."""

from __future__ import annotations

import re

SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+")


def chunk_text(text: str, max_chars: int = 700) -> list[str]:
    _require_positive_max_chars(max_chars)
    chunks: list[str] = []
    for paragraph in (part.strip() for part in text.split("\n\n")):
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue
        chunks.extend(_chunk_long_paragraph(paragraph, max_chars))
    return chunks or [text[:max_chars].strip()]


def overlapping_chunks(
    text: str,
    max_chars: int = 1_800,
    overlap_chars: int = 250,
) -> list[str]:
    """Return bounded chunks with paragraph-aware overlap between neighbors.

    The helper starts from ``chunk_text`` atoms, packs adjacent atoms up to
    ``max_chars``, and carries as much complete trailing context as fits within
    ``overlap_chars`` into the next chunk. This keeps ranking units bounded
    without producing one candidate per short paragraph.
    """

    _require_positive_max_chars(max_chars)
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be at least 0")
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be smaller than max_chars")

    atoms = chunk_text(text, max_chars=max_chars)
    if len(atoms) <= 1:
        return atoms

    chunks: list[str] = []
    start = 0
    while start < len(atoms):
        end = start
        selected: list[str] = []

        while end < len(atoms):
            candidate = "\n\n".join([*selected, atoms[end]])
            if selected and len(candidate) > max_chars:
                break
            selected.append(atoms[end])
            end += 1
            if len(candidate) >= max_chars:
                break

        chunk = "\n\n".join(selected).strip()
        if chunk and (not chunks or chunks[-1] != chunk):
            chunks.append(chunk)
        if end >= len(atoms):
            break

        overlap_start = end
        if overlap_chars:
            for candidate_start in range(end - 1, start - 1, -1):
                overlap = "\n\n".join(atoms[candidate_start:end])
                if len(overlap) > overlap_chars:
                    break
                overlap_start = candidate_start

        # Always consume at least one new atom. This matters when a short
        # completed window would otherwise fit entirely inside the overlap.
        start = max(overlap_start, start + 1) if overlap_start < end else end

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
    _require_positive_max_chars(max_chars)
    windows: list[str] = []
    for paragraph in (part.strip() for part in text.split("\n\n")):
        if not paragraph:
            continue
        sentences = _text_units(paragraph)
        if not sentences:
            continue
        for index in range(len(sentences)):
            window = _window_around_sentence(sentences, index, max_chars)
            if window and window not in windows:
                windows.append(window)
    return windows or chunk_text(text, max_chars=max_chars)


def _text_units(paragraph: str) -> list[str]:
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if len(lines) > 1 and any(BULLET_RE.match(line) for line in lines):
        return [BULLET_RE.sub("", line).strip() for line in lines if line.strip()]
    return [
        sentence.strip()
        for sentence in SENTENCE_BOUNDARY_RE.split(paragraph)
        if sentence.strip()
    ]


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


def _require_positive_max_chars(max_chars: int) -> None:
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")
