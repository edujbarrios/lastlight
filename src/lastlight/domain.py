"""Domain value objects for LastLight."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgePack:
    name: str
    version: str = "unknown"
    languages: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    license: str = "unknown"
    source: str = "local"
    path: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    path: str
    body: str
    source_sha256: str = ""
    language: str = "unknown"
    tags: tuple[str, ...] = field(default_factory=tuple)
    priority: str = "normal"
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchQuery:
    text: str
    top_k: int = 3


@dataclass(frozen=True)
class SearchResult:
    document: KnowledgeDocument
    score: float
    confidence: str
    passage: str
    matched_terms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvaluationCase:
    query: str
    expected_tag: str
