"""Offline index builder for audit and future retrieval experiments."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .interfaces import KnowledgeRepository
from .tokenizer import tokenize

INDEX_VERSION = 1


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
                "token_count": len(tokens),
                "terms": dict(sorted(term_counts.items())),
            }
        )

    return {
        "index_version": INDEX_VERSION,
        "document_count": len(documents),
        "term_count": len(corpus_terms),
        "documents": entries,
    }


def write_index(repository: KnowledgeRepository, output_path: Path | str) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    index = build_index(repository)
    output.write_text(
        json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output

