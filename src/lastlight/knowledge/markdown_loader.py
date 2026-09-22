"""Markdown document loading."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .domain import KnowledgeDocument
from .metadata import split_front_matter
from .util import normalize_relative_path, project_root


def load_markdown_document(path: Path, root: Path | None = None) -> KnowledgeDocument:
    root = root or project_root()
    text = path.read_text(encoding="utf-8")
    label = normalize_relative_path(path, root)
    return load_markdown_text(text, label)


def load_markdown_text(text: str, path_label: str) -> KnowledgeDocument:
    metadata, body = split_front_matter(text)
    source_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()

    title = str(metadata.get("title") or infer_title(Path(path_label), body))
    language = str(metadata.get("language") or "unknown")
    priority = str(metadata.get("priority") or "normal")
    tags = metadata.get("tags") or ()
    if isinstance(tags, str):
        tag_values = (tags,)
    elif isinstance(tags, list):
        tag_values = tuple(str(tag) for tag in tags)
    else:
        tag_values = ()

    return KnowledgeDocument(
        title=title,
        path=path_label,
        body=body,
        source_sha256=source_sha256,
        language=language,
        tags=tag_values,
        priority=priority,
        metadata=metadata,
    )


def infer_title(path: Path, body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem.replace("_", " ").replace("-", " ").title()
