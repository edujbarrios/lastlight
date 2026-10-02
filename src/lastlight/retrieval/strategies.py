"""Retrieval strategies."""

from __future__ import annotations

from ..domain import KnowledgeDocument, SearchQuery, SearchResult
from ..interfaces import RetrievalStrategy
from .chunking import sentence_windows
from .ranking import (
    BM25Corpus,
    bm25_scores,
    confidence_for_bm25_score,
    confidence_for_score,
    lexical_score,
    prepare_bm25_corpus,
)
from .sections import RetrievalUnit, retrieval_units
from .tokenizer import expand_query_tokens, tokenize

# Generic glue words that should never be the only evidence for a LOW result.
# Keeping this filter at the result boundary preserves established score scales
# for meaningful matches while removing obvious out-of-domain noise.
WEAK_LOW_CONFIDENCE_TERMS = frozenset(
    {"about", "does", "had", "has", "have", "that", "will"}
)

CorpusSignature = tuple[
    tuple[str, str, str, tuple[str, ...], str, str],
    ...,
]


class _UnitCachingRetrievalStrategy(RetrievalStrategy):
    def __init__(self) -> None:
        self._unit_cache: tuple[CorpusSignature, tuple[RetrievalUnit, ...]] | None = None

    def _prepared_units(self, documents: list[KnowledgeDocument]) -> tuple[RetrievalUnit, ...]:
        signature = _corpus_signature(documents)
        cached = self._unit_cache
        if cached is not None and cached[0] == signature:
            return cached[1]

        units = tuple(retrieval_units(documents))
        # Store signature and units together so concurrent readers never observe
        # units built for a different corpus. Concurrent misses may duplicate the
        # deterministic preparation work but cannot mix corpus state.
        self._unit_cache = (signature, units)
        return units


class LexicalRetrievalStrategy(_UnitCachingRetrievalStrategy):
    def __init__(self) -> None:
        super().__init__()

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        units = self._prepared_units(documents)
        best_by_source: dict[int, SearchResult] = {}
        for unit in units:
            score, matched_terms = lexical_score(
                query.text,
                unit.ranking_document,
                len(units),
            )
            if score <= 0:
                continue
            confidence = confidence_for_score(score)
            if _weak_low_confidence_match(confidence, matched_terms):
                continue
            result = SearchResult(
                document=unit.source,
                score=score,
                confidence=confidence,
                passage=select_passage(unit.passage_body, query.text),
                matched_terms=matched_terms,
            )
            _keep_best_result(best_by_source, unit.source_index, result)

        results = list(best_by_source.values())
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


class BM25RetrievalStrategy(_UnitCachingRetrievalStrategy):
    def __init__(self) -> None:
        super().__init__()
        self._corpus_cache: tuple[CorpusSignature, BM25Corpus] | None = None

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        units = self._prepared_units(documents)
        ranking_documents = [unit.ranking_document for unit in units]
        corpus = self._prepared_corpus(ranking_documents)
        best_by_source: dict[int, SearchResult] = {}

        for unit, (score, matched_terms) in zip(
            units,
            bm25_scores(query.text, ranking_documents, corpus=corpus),
        ):
            if score <= 0:
                continue
            confidence = confidence_for_bm25_score(score)
            if _weak_low_confidence_match(confidence, matched_terms):
                continue
            result = SearchResult(
                document=unit.source,
                score=score,
                confidence=confidence,
                passage=select_passage(unit.passage_body, query.text),
                matched_terms=matched_terms,
            )
            _keep_best_result(best_by_source, unit.source_index, result)

        results = list(best_by_source.values())
        results.sort(key=lambda result: (-result.score, result.document.path))
        return results[: max(query.top_k, 1)]

    def _prepared_corpus(self, documents: list[KnowledgeDocument]) -> BM25Corpus:
        signature = _corpus_signature(documents)
        cached = self._corpus_cache
        if cached is not None and cached[0] == signature:
            return cached[1]

        corpus = prepare_bm25_corpus(documents)
        # Store signature and prepared corpus in one immutable tuple so concurrent
        # readers can only observe a matching pair. Concurrent cache misses may
        # duplicate preparation, but cannot mix statistics from different corpora.
        self._corpus_cache = (signature, corpus)
        return corpus


def _corpus_signature(documents: list[KnowledgeDocument]) -> CorpusSignature:
    return tuple(
        (
            document.path,
            document.source_sha256,
            document.title,
            document.tags,
            document.priority,
            document.body,
        )
        for document in documents
    )


def _keep_best_result(
    best_by_source: dict[int, SearchResult],
    source_index: int,
    result: SearchResult,
) -> None:
    current = best_by_source.get(source_index)
    if current is None or result.score > current.score:
        best_by_source[source_index] = result


def _weak_low_confidence_match(confidence: str, matched_terms: tuple[str, ...]) -> bool:
    if confidence != "LOW" or not matched_terms:
        return False
    return set(matched_terms).issubset(WEAK_LOW_CONFIDENCE_TERMS)
