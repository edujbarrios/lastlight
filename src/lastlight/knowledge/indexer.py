"""Offline index builder for audit and future retrieval experiments."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .interfaces import KnowledgeRepository
from .tokenizer import tokenize

INDEX_VERSION = 1


def _valid_index_shape(index: object) -> bool:
    """An invalid audit snapshot must never silently verify as complete."""
    if not isinstance(index, dict):
        return False
    version = index.get("index_version")
    documents = index.get("documents")
    count = index.get("document_count")
    if type(version) is not int or version != INDEX_VERSION:
        return False
    if not isinstance(documents, list) or type(count) is not int or count != len(documents):
        return False
    paths: set[str] = set()
    for item in documents:
        if not isinstance(item, dict):
            return False
        path = item.get("path")
        digest = item.get("source_sha256")
        if (
            not isinstance(path, str)
            or not path.strip()
            or path in paths
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None
        ):
            return False
        paths.add(path)
    return True



def verify_index(
    repository: KnowledgeRepository, index_path: Path | str
) -> dict[str, object]:
    """Compare current knowledge sources with a previously generated audit index."""
    path = Path(index_path)
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"ok": False, "error": str(error), "missing": [], "modified": [], "unexpected": []}

    if not _valid_index_shape(stored):
        return {
            "ok": False,
            "error": "unsupported or malformed index",
            "missing": [],
            "modified": [],
            "unexpected": [],
        }

    expected = {item["path"]: item["source_sha256"] for item in stored["documents"]}
    current = {
        document.path: document.source_sha256
        for document in repository.list_documents()
    }
    missing = sorted(set(expected) - set(current))
    unexpected = sorted(set(current) - set(expected))
    modified = sorted(
        item for item in set(expected) & set(current) if expected[item] != current[item]
    )
    return {
        "ok": not (missing or modified or unexpected),
        "missing": missing,
        "modified": modified,
        "unexpected": unexpected,
    }


def build_index(repository: KnowledgeRepository) -> dict[str, object]:
    documents = repository.list_documents()
    entries: list[dict[str, object]] = []
    corpus_terms: Counter[str] = Counter()

    for document in documents:
        tokens = tokenize(f"{document.title} {' '.join(document.tags)} {document.body}")
        term_counts = Counter(tokens)
        corpus_terms.update(term_counts)
        entries.append(
            {
                "path": document.path,
                "title": document.title,
                "language": document.language,
                "tags": list(document.tags),
                "priority": document.priority,
                "source_sha256": document.source_sha256,
                "token_count": len(tokens),
                "terms": dict(sorted(term_counts.items())),
            }
        )

    index: dict[str, object] = {
        "index_version": INDEX_VERSION,
        "document_count": len(documents),
        "term_count": len(corpus_terms),
        "documents": entries,
    }
    describe_pack = getattr(repository, "describe_pack", None)
    if callable(describe_pack):
        pack = describe_pack()
        index["pack"] = {
            "name": pack.name,
            "version": pack.version,
            "languages": list(pack.languages),
            "description": pack.description,
            "license": pack.license,
            "source": pack.source,
            "path": pack.path,
        }
    return index


def write_index(repository: KnowledgeRepository, output_path: Path | str) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    index = build_index(repository)
    output.write_text(
        json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output
