"""Lexical ranking helpers."""

from __future__ import annotations

import math
from collections import Counter

from .domain import KnowledgeDocument
from .tokenizer import expand_query_tokens, normalize_text, tokenize

PRIORITY_BOOSTS = {"critical": 1.3, "high": 1.2, "normal": 1.0, "low": 0.9}


def lexical_score(query_text: str, document: KnowledgeDocument, corpus_size: int = 1) -> tuple[float, tuple[str, ...]]:
    query_tokens = expand_query_tokens(tokenize(query_text))
    if not query_tokens:
        return 0.0, ()

    body_tokens = tokenize(document.body)
    title_tokens = tokenize(document.title)
    tag_tokens = tokenize(" ".join(document.tags))
    body_counts = Counter(body_tokens)
    body_unique = set(body_tokens)
    matched = [token for token in query_tokens if token in body_unique or token in title_tokens or token in tag_tokens]
    if not matched:
        return 0.0, ()

    score = 0.0
    for token in query_tokens:
        body_hits = min(body_counts.get(token, 0), 4)
        title_hit = 1 if token in title_tokens else 0
        tag_hit = 1 if token in tag_tokens else 0
        rare_boost = 1.0 + min(len(token), 12) / 20.0
        score += (body_hits * 1.0 + title_hit * 3.0 + tag_hit * 2.5) * rare_boost

    normalized_query = normalize_text(query_text)
    searchable = normalize_text(f"{document.title} {' '.join(document.tags)} {document.body}")
    if normalized_query and normalized_query in searchable:
        score += 4.0

    if len(matched) >= 2:
        score += math.log2(len(set(matched)) + 1)

    score *= PRIORITY_BOOSTS.get(document.priority.casefold(), 1.0)
    score /= max(math.sqrt(len(body_tokens) + 20), 1.0)
    score *= 1.0 + min(corpus_size, 100) / 500.0
    return score, tuple(sorted(set(matched)))


def confidence_for_score(score: float) -> str:
    if score >= 1.45:
        return "HIGH"
    if score >= 0.55:
        return "MEDIUM"
    return "LOW"
