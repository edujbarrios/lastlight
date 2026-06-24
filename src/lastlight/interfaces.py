"""Small interfaces that keep the domain independent from storage and ranking."""

from __future__ import annotations

from typing import Protocol

from .domain import KnowledgeDocument, SearchQuery, SearchResult


class KnowledgeRepository(Protocol):
    def list_documents(self) -> list[KnowledgeDocument]:
        """Return every available knowledge document."""


class RetrievalStrategy(Protocol):
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        """Return ranked search results for a query."""

