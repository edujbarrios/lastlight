"""Helpers for constructing repositories from one or many knowledge sources."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .composite_repository import CompositeKnowledgeRepository
from .interfaces import KnowledgeRepository
from .repository import MarkdownKnowledgeRepository

KnowledgeSource = Path | str
KnowledgeSources = KnowledgeSource | Sequence[KnowledgeSource] | None


def normalize_knowledge_sources(sources: KnowledgeSources) -> tuple[KnowledgeSource, ...]:
    if sources is None:
        return ()
    if isinstance(sources, (str, Path)):
        return (sources,)
    return tuple(sources)


def build_knowledge_repository(sources: KnowledgeSources = None) -> KnowledgeRepository:
    normalized = normalize_knowledge_sources(sources)
    if not normalized:
        return MarkdownKnowledgeRepository()

    repositories = tuple(MarkdownKnowledgeRepository(source) for source in normalized)
    if len(repositories) == 1:
        return repositories[0]
    return CompositeKnowledgeRepository(repositories)
