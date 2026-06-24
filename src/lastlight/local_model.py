"""Auditable tiny local language model packs."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .interfaces import KnowledgeRepository
from .tokenizer import tokenize

MODEL_VERSION = 1
DEFAULT_ORDER = 2


def build_local_model(
    repository: KnowledgeRepository, order: int = DEFAULT_ORDER
) -> dict[str, object]:
    if order < 1:
        raise ValueError("order must be at least 1")

    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    token_count = 0
    documents = repository.list_documents()

    for document in documents:
        tokens = tokenize(f"{document.title} {' '.join(document.tags)} {document.body}")
        token_count += len(tokens)
        if len(tokens) <= order:
            continue
        for index in range(len(tokens) - order):
            prefix = " ".join(tokens[index : index + order])
            next_token = tokens[index + order]
            transitions[prefix][next_token] += 1

    serializable_transitions = {
        prefix: dict(sorted(counts.items())) for prefix, counts in sorted(transitions.items())
    }
    return {
        "model_version": MODEL_VERSION,
        "model_type": "word-ngram",
        "order": order,
        "document_count": len(documents),
        "token_count": token_count,
        "transition_count": len(serializable_transitions),
        "transitions": serializable_transitions,
    }


def write_local_model(
    repository: KnowledgeRepository, output_path: Path | str, order: int = DEFAULT_ORDER
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    model = build_local_model(repository, order=order)
    output.write_text(
        json.dumps(model, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def read_local_model(path: Path | str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_local_model(path: Path | str) -> str:
    model = read_local_model(path)
    lines = [
        "LastLight local model",
        f"Type: {model.get('model_type', 'unknown')}",
        f"Version: {model.get('model_version', 'unknown')}",
        f"Order: {model.get('order', 'unknown')}",
        f"Documents: {model.get('document_count', 'unknown')}",
        f"Tokens: {model.get('token_count', 'unknown')}",
        f"Transitions: {model.get('transition_count', 'unknown')}",
    ]
    return "\n".join(lines)

