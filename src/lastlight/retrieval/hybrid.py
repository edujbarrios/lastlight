"""Offline reciprocal-rank fusion without cross-backend score arithmetic."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import replace
import re
from typing import Iterable

from ..domain import KnowledgeDocument, SearchQuery, SearchResult
from ..interfaces import RetrievalStrategy
from .strategies import BM25RetrievalStrategy, LexicalRetrievalStrategy
from .sections import SectionConfig
from .tokenizer import tokenize


def _passage_support(result: SearchResult, query: str) -> int:
    """Select the more answer-bearing passage from duplicate backend hits."""
    terms = set(tokenize(query))
    passage = set(tokenize(result.passage))
    overlap = len(terms & passage)
    if re.search(r"\b(how many|how much|how long|cuanto|cuantos)\b", query.casefold()):
        overlap += 2 if re.search(r"\b\d+(?:[.,]\d+)?\b", result.passage) else 0
    return overlap


def reciprocal_rank_fusion(
    rankings: Iterable[list[SearchResult]],
    *,
    rank_constant: int = 60,
    limit: int = 3,
    query_text: str = "",
) -> list[SearchResult]:
    """Fuse ordered lists by source identity, not by incompatible raw scores.

    RRF(d) = sum(1 / (rank_constant + position)) across backends.
    The selected evidence passage is taken from the strongest rank contributor,
    with its original backend score preserved in backend_scores.
    """
    if rank_constant < 1 or limit < 1:
        raise ValueError("rank_constant and limit must be positive")
    votes: dict[tuple[str, str, str], float] = {}
    representative: dict[tuple[str, str, str], tuple[int, int, SearchResult]] = {}
    components: dict[tuple[str, str, str], list[tuple[str, float]]] = {}
    for index, results in enumerate(rankings):
        name = ("lexical", "bm25")[index] if index < 2 else f"backend_{index}"
        seen: set[tuple[str, str, str]] = set()
        for rank, result in enumerate(results, start=1):
            key = (result.document.pack_path, result.document.path, result.document.source_sha256)
            if key in seen:
                continue
            seen.add(key)
            votes[key] = votes.get(key, 0.0) + 1.0 / (rank_constant + rank)
            components.setdefault(key, []).append((name, result.score))
            old = representative.get(key)
            support = _passage_support(result, query_text)
            if old is None or (support, -rank) > (old[0], -old[1]):
                representative[key] = (support, rank, result)
    ordered = sorted(votes, key=lambda key: (-votes[key], key))
    output: list[SearchResult] = []
    for key in ordered[:limit]:
        original = representative[key][2]
        corroborated = len(components[key]) >= 2
        output.append(replace(
            original,
            score=votes[key],
            confidence="HIGH" if corroborated else "MEDIUM",
            backend_scores=tuple(components[key]),
        ))
    return output


class HybridRetrievalStrategy(RetrievalStrategy):
    """Two offline candidate searches + deterministic reciprocal-rank fusion."""

    def __init__(
        self, rank_constant: int = 60, candidate_factor: int = 3,
        section_config: SectionConfig | None = None,
    ) -> None:
        if rank_constant < 1 or candidate_factor < 1:
            raise ValueError("fusion parameters must be positive")
        self.rank_constant = rank_constant
        self.candidate_factor = candidate_factor
        self.lexical = LexicalRetrievalStrategy(section_config=section_config)
        self.bm25 = BM25RetrievalStrategy(section_config=section_config)
        self._last: ContextVar[dict[str, object] | None] = ContextVar(
            "lastlight_hybrid_decision", default=None
        )

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        size = min(len(documents), max(query.top_k, self.candidate_factor * query.top_k))
        effective = SearchQuery(query.text, max(size, 1))
        lexical = self.lexical.search(effective, documents)
        bm25 = self.bm25.search(effective, documents)
        results = reciprocal_rank_fusion(
            [lexical, bm25], rank_constant=self.rank_constant,
            limit=max(query.top_k, 1), query_text=query.text
        )
        self._last.set({
            "strategy": "hybrid", "mode": "fixed",
            "effective_top_k": max(query.top_k, 1),
            "verification_backend": "lexical+bm25",
            "verification_agreement": (
                lexical[0].document.path == bm25[0].document.path
                if lexical and bm25 else None
            ),
            "reason": "rank fusion; no raw-score mixing",
        })
        return results

    def decision_metadata(self) -> dict[str, object] | None:
        return self._last.get()
