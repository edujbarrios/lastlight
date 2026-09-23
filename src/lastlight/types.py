"""Stable public result contracts for library consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RetrievalStrategyName = Literal["lexical", "bm25", "adaptive"]
AdaptiveMode = Literal["survival", "balanced", "accuracy"]
RefusalReason = Literal["no_matching_knowledge", "insufficient_confidence"]


@dataclass(frozen=True)
class SourceDocument:
    """Public, immutable view of a retrieved knowledge document."""

    title: str
    path: str
    body: str
    pack_name: str
    pack_version: str
    pack_source: str
    pack_path: str
    language: str
    tags: tuple[str, ...]
    priority: str = "normal"


@dataclass(frozen=True)
class SourceResult:
    """Ranked source result exposed by the public Python API."""

    document: SourceDocument
    score: float
    confidence: str
    passage: str
    matched_terms: tuple[str, ...] = field(default_factory=tuple)

    @property
    def title(self) -> str:
        return self.document.title

    @property
    def path(self) -> str:
        return self.document.path

    @property
    def pack_name(self) -> str:
        return self.document.pack_name

    @property
    def pack_version(self) -> str:
        return self.document.pack_version

    @property
    def pack_source(self) -> str:
        return self.document.pack_source

    @property
    def pack_path(self) -> str:
        return self.document.pack_path

    @property
    def language(self) -> str:
        return self.document.language

    @property
    def tags(self) -> tuple[str, ...]:
        return self.document.tags

    @property
    def priority(self) -> str:
        return self.document.priority


@dataclass(frozen=True)
class PackInfo:
    """Public metadata for one mounted knowledge pack."""

    name: str
    version: str
    languages: tuple[str, ...]
    description: str
    license: str
    source: str
    path: str
    document_count: int


@dataclass(frozen=True)
class PackValidation:
    """Validation result for one mounted knowledge pack."""

    pack: PackInfo
    ok: bool
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PackProvenance:
    """Provenance and freshness result for one mounted knowledge pack."""

    pack: PackInfo
    ok: bool
    fingerprint_sha256: str
    publisher: str
    published_at: str | None = None
    expires_at: str | None = None
    age_days: int | None = None
    expired: bool = False
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievalMetadata:
    """Structured explanation of the retrieval strategy selected for a query."""

    strategy: str
    mode: str
    effective_top_k: int
    risk: str | None = None
    reason: str | None = None
    low_resource_target: bool | None = None
    memory_mb: int | None = None
    battery_percent: float | None = None
    energy_budget_mwh: float | None = None
    memory_budget_mb: int | None = None


@dataclass(frozen=True)
class QueryResult:
    """Stable result returned by :meth:`LastLight.query`."""

    query: str
    accepted: bool
    confidence: str | None
    passage: str | None
    sources: tuple[SourceResult, ...]
    retrieval: RetrievalMetadata
    refusal_reason: RefusalReason | None = None
