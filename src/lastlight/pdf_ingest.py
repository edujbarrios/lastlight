"""Optional PDF ingestion helpers for building Markdown knowledge packs."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

ACTION_RE = re.compile(
    r"\b("
    r"avoid|call|check|cover|discard|do not|drink|evacuate|keep|mark|move|"
    r"never|rinse|seek|separate|should|stop|store|use|wash|warning"
    r")\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^([A-Z][A-Za-z0-9 ,:/()'-]{3,80})$")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
WHITESPACE_RE = re.compile(r"[ \t]+")


@dataclass(frozen=True)
class PdfPage:
    number: int
    text: str


@dataclass(frozen=True)
class PdfDocument:
    path: Path
    pages: tuple[PdfPage, ...]
    source_sha256: str

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text).strip()


def load_pdf(path: Path | str) -> PdfDocument:
    pdf_path = Path(path)
    data = pdf_path.read_bytes()
    source_sha256 = hashlib.sha256(data).hexdigest()
    pages = tuple(_extract_pages_with_pypdf(pdf_path) or _extract_pages_with_fitz(pdf_path))
    if not pages:
        raise RuntimeError(
            "No text could be extracted. The PDF may be scanned or image-only."
        )
    return PdfDocument(path=pdf_path, pages=pages, source_sha256=source_sha256)


def _extract_pages_with_pypdf(path: Path) -> list[PdfPage]:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore[import-not-found]
        except Exception:
            return []

    pages: list[PdfPage] = []
    reader = PdfReader(str(path))
    for index, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if text:
            pages.append(PdfPage(index, text))
    return pages


def _extract_pages_with_fitz(path: Path) -> list[PdfPage]:
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception:
        return []

    pages: list[PdfPage] = []
    with fitz.open(str(path)) as document:
        for index, page in enumerate(document, start=1):
            text = _clean_text(page.get_text("text") or "")
            if text:
                pages.append(PdfPage(index, text))
    return pages


def document_to_markdown(
    document: PdfDocument,
    title: str | None = None,
    language: str = "unknown",
    tags: tuple[str, ...] = (),
    priority: str = "normal",
    max_summary_items: int = 8,
) -> str:
    resolved_title = title or infer_title(document)
    summary_items = extract_important_points(document.text, limit=max_summary_items)
    body = text_to_markdown(document.pages)
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    if not tag_lines:
        tag_lines = "  - imported"

    summary = "\n".join(f"- {item}" for item in summary_items)
    if not summary:
        summary = "- No high-signal summary points were detected."

    return (
        "---\n"
        f"title: {resolved_title}\n"
        f"language: {language}\n"
        "tags:\n"
        f"{tag_lines}\n"
        f"priority: {priority}\n"
        "source_type: pdf\n"
        f"source_file: {document.path.name}\n"
        f"source_sha256: {document.source_sha256}\n"
        f"pages: {len(document.pages)}\n"
        "---\n\n"
        "## Important Points\n\n"
        f"{summary}\n\n"
        "## Extracted Text\n\n"
        f"{body}\n"
    )


def infer_title(document: PdfDocument) -> str:
    for line in document.text.splitlines():
        stripped = line.strip()
        if 4 <= len(stripped) <= 100:
            return stripped
    return document.path.stem.replace("_", " ").replace("-", " ").title()


def extract_important_points(text: str, limit: int = 8) -> list[str]:
    candidates = _candidate_sentences(text)
    scored = sorted(
        ((score_sentence(sentence), index, sentence) for index, sentence in enumerate(candidates)),
        key=lambda item: (-item[0], item[1]),
    )
    selected: list[str] = []
    seen: set[str] = set()
    for score, _, sentence in scored:
        if score <= 0:
            continue
        key = sentence.casefold()
        if key in seen:
            continue
        selected.append(sentence)
        seen.add(key)
        if len(selected) >= limit:
            break
    return selected


def score_sentence(sentence: str) -> int:
    score = 0
    if ACTION_RE.search(sentence):
        score += 3
    if any(marker in sentence.casefold() for marker in ("warning", "danger", "urgent")):
        score += 2
    if any(marker in sentence.casefold() for marker in ("do not", "never", "avoid")):
        score += 2
    if 40 <= len(sentence) <= 240:
        score += 1
    return score


def text_to_markdown(pages: tuple[PdfPage, ...]) -> str:
    sections: list[str] = []
    for page in pages:
        lines = [_markdown_line(line) for line in page.text.splitlines()]
        content = "\n".join(line for line in lines if line).strip()
        if content:
            sections.append(f"### Page {page.number}\n\n{content}")
    return "\n\n".join(sections).strip()


def _markdown_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if HEADING_RE.match(stripped) and not stripped.endswith("."):
        return f"### {stripped}"
    return stripped


def _candidate_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for sentence in SENTENCE_RE.split(paragraph):
            cleaned = sentence.strip()
            if len(cleaned) >= 25:
                sentences.append(cleaned)
    return sentences


def _clean_text(text: str) -> str:
    lines = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = WHITESPACE_RE.sub(" ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)
