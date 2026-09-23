"""Stable public result contracts for library consumers."""

from __future__ import annotations

from dataclasses import dataclass, field


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
