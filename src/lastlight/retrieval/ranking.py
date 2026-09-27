"""Lexical ranking helpers."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from ..domain import KnowledgeDocument
from .tokenizer import expand_query_tokens, normalize_text, tokenize

PRIORITY_BOOSTS = {"critical": 1.3, "high": 1.2, "normal": 1.0, "low": 0.9}


@dataclass(frozen=True)
class BM25Corpus:
    """Query-independent BM25 statistics for one ordered document corpus."""

    token_counts: tuple[Counter[str], ...]
    lengths: tuple[int, ...]
    average_length: float
    document_frequency: Counter[str]
    searchable_text: tuple[str, ...]


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


def document_tokens(document: KnowledgeDocument) -> list[str]:
    title_tokens = tokenize(document.title)
    tag_tokens = tokenize(" ".join(document.tags))
    body_tokens = tokenize(document.body)
    return title_tokens * 3 + tag_tokens * 2 + body_tokens


def prepare_bm25_corpus(documents: list[KnowledgeDocument]) -> BM25Corpus:
    """Build the query-independent token statistics used by BM25 scoring."""

    tokenized_documents = [document_tokens(document) for document in documents]
    lengths = tuple(len(tokens) for tokens in tokenized_documents)
    average_length = sum(lengths) / len(lengths) if lengths else 1.0
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized_documents:
        document_frequency.update(set(tokens))
    token_counts = tuple(Counter(tokens) for tokens in tokenized_documents)
    searchable_text = tuple(
        normalize_text(f"{document.title} {' '.join(document.tags)} {document.body}")
        for document in documents
    )
    return BM25Corpus(
        token_counts=token_counts,
        lengths=lengths,
        average_length=average_length,
        document_frequency=document_frequency,
        searchable_text=searchable_text,
    )


def bm25_scores(
    query_text: str,
    documents: list[KnowledgeDocument],
    k1: float = 1.2,
    b: float = 0.75,
    *,
    corpus: BM25Corpus | None = None,
) -> list[tuple[float, tuple[str, ...]]]:
    query_tokens = expand_query_tokens(tokenize(query_text))
    if not query_tokens or not documents:
        return [(0.0, ()) for _ in documents]

    prepared = corpus
    if prepared is None or len(prepared.lengths) != len(documents):
        prepared = prepare_bm25_corpus(documents)

    normalized_query = normalize_text(query_text)
    scores: list[tuple[float, tuple[str, ...]]] = []
    total_documents = len(documents)
    for counts, length, searchable, document in zip(
        prepared.token_counts,
        prepared.lengths,
        prepared.searchable_text,
        documents,
    ):
        matched: set[str] = set()
        score = 0.0
        for token in query_tokens:
            frequency = counts.get(token, 0)
            if frequency == 0:
                continue
            matched.add(token)
            df = prepared.document_frequency[token]
            idf = math.log(1.0 + (total_documents - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (
                1.0 - b + b * length / max(prepared.average_length, 1.0)
            )
            score += idf * (frequency * (k1 + 1.0)) / denominator

        if matched:
            if normalized_query and normalized_query in searchable:
                score += 1.0
            score *= PRIORITY_BOOSTS.get(document.priority.casefold(), 1.0)
        scores.append((score, tuple(sorted(matched))))
    return scores


def confidence_for_bm25_score(score: float) -> str:
    if score >= 3.0:
        return "HIGH"
    if score >= 1.0:
        return "MEDIUM"
    return "LOW"
