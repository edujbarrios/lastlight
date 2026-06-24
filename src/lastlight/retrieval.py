"""Retrieval strategies."""

from __future__ import annotations

from .c_core import OptionalCCore
from .domain import KnowledgeDocument, SearchQuery, SearchResult
from .interfaces import RetrievalStrategy
from .chunking import chunk_text
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
    chunks = chunk_text(body, max_chars=max_chars)
    if not chunks:
        return body[:max_chars].strip()

    query_tokens = set(expand_query_tokens(tokenize(query_text)))
    best = max(
        chunks,
        key=lambda chunk: len(query_tokens.intersection(tokenize(chunk))),
    )
    return best


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
