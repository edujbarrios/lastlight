"""Retrieval strategies."""

from __future__ import annotations

from .domain import KnowledgeDocument, SearchQuery, SearchResult
from .interfaces import RetrievalStrategy
from .ranking import confidence_for_score, lexical_score
from .tokenizer import tokenize


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
    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    if not paragraphs:
        return body[:max_chars].strip()

    query_tokens = set(tokenize(query_text))
    best = max(
        paragraphs,
        key=lambda paragraph: len(query_tokens.intersection(tokenize(paragraph))),
    )
    if len(best) <= max_chars:
        return best
    return best[: max_chars - 3].rstrip() + "..."


class BM25RetrievalStrategy:
    """Future strategy placeholder."""

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        raise NotImplementedError("BM25 is planned for LastLight v0.2.")

