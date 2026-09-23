"""Stable public result contracts for library consumers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceResult:
    title: str
    path: str
    pack_name: str
    pack_version: str
    language: str
    tags: tuple[str, ...]
    score: float
    confidence: str
    passage: str
    matched_terms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievalMetadata:
    strategy: str
    mode: str
    effective_top_k: int
    risk: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class QueryResult:
    query: str
    accepted: bool
    confidence: str | None
    passage: str | None
    sources: tuple[SourceResult, ...]
    retrieval: RetrievalMetadata
