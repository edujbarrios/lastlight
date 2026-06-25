"""Retrieval strategies."""

from __future__ import annotations

from .c_core import OptionalCCore
from .domain import KnowledgeDocument, SearchQuery, SearchResult
from .interfaces import RetrievalStrategy
from .chunking import sentence_windows
from .ranking import (
    bm25_scores,
    confidence_for_bm25_score,
    confidence_for_score,
    lexical_score,
)
from .tokenizer import expand_query_tokens, tokenize


class LexicalRetrievalStrategy(RetrievalStrategy):
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for document in documents:
            score, matched_terms = lexical_score(query.text, document, len(documents))
            if score <= 0:
                continue
            results.append(
                SearchResult(
                    document=document,
                    score=score,
                    confidence=confidence_for_score(score),
                    passage=select_passage(document.body, query.text),
                    matched_terms=matched_terms,
                )
            )
        results.sort(key=lambda result: (-result.score, result.document.path))
        return results[: max(query.top_k, 1)]


def select_passage(body: str, query_text: str, max_chars: int = 700) -> str:
    chunks = sentence_windows(body, max_chars=max_chars)
    if not chunks:
        return body[:max_chars].strip()

    query_tokens = tuple(expand_query_tokens(tokenize(query_text)))
    if not query_tokens:
        return chunks[0]

    best = max(chunks, key=lambda chunk: _passage_score(chunk, query_text, query_tokens))
    return best


def _passage_score(
    chunk: str, query_text: str, query_tokens: tuple[str, ...]
) -> tuple[float, int]:
    chunk_tokens = tokenize(chunk)
    if not chunk_tokens:
        return (0.0, 0)

    chunk_token_set = set(chunk_tokens)
    query_token_set = set(query_tokens)
    unique_matches = len(query_token_set.intersection(chunk_token_set))
    repeated_matches = sum(1 for token in chunk_tokens if token in query_token_set)
    density = unique_matches / max(len(chunk_token_set), 1)
    phrase_bonus = 1.0 if query_text.casefold() in chunk.casefold() else 0.0
    score = unique_matches * 4.0 + repeated_matches + density + phrase_bonus
    return (score, -len(chunk))


class BM25RetrievalStrategy(RetrievalStrategy):
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for document, (score, matched_terms) in zip(
            documents, bm25_scores(query.text, documents)
        ):
            if score <= 0:
                continue
            results.append(
                SearchResult(
                    document=document,
                    score=score,
                    confidence=confidence_for_bm25_score(score),
                    passage=select_passage(document.body, query.text),
                    matched_terms=matched_terms,
                )
            )
        results.sort(key=lambda result: (-result.score, result.document.path))
        return results[: max(query.top_k, 1)]


class CBackedLexicalRetrievalStrategy(RetrievalStrategy):
    def __init__(self, c_core: OptionalCCore | None = None) -> None:
        self.c_core = c_core or OptionalCCore()

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        query_tokens = expand_query_tokens(tokenize(query.text))
        if not query_tokens:
            return []

        results: list[SearchResult] = []
        for document in documents:
            document_tokens = tokenize(
                f"{document.title} {' '.join(document.tags)} {document.body}"
            )
            matched_count = self.c_core.count_matches(query_tokens, document_tokens)
            if matched_count <= 0:
                continue
            score, python_matched_terms = lexical_score(query.text, document, len(documents))
            if score <= 0:
                continue
            matched_terms = tuple(
                sorted(set(python_matched_terms).union(set(query_tokens).intersection(set(document_tokens))))
            )
            results.append(
                SearchResult(
                    document=document,
                    score=score,
                    confidence=confidence_for_score(score),
                    passage=select_passage(document.body, query.text),
                    matched_terms=matched_terms,
                )
            )
        results.sort(key=lambda result: (-result.score, result.document.path))
        return results[: max(query.top_k, 1)]
