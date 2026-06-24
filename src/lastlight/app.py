"""Application service layer."""

from __future__ import annotations

from .domain import SearchQuery, SearchResult
from .interfaces import KnowledgeRepository, RetrievalStrategy
from .safety import safe_answer


class LastLightApp:
    def __init__(self, repository: KnowledgeRepository, retrieval: RetrievalStrategy) -> None:
        self.repository = repository
        self.retrieval = retrieval

    def search(self, text: str, top_k: int = 3) -> list[SearchResult]:
        documents = self.repository.list_documents()
        return self.retrieval.search(SearchQuery(text=text, top_k=top_k), documents)

    def answer(self, text: str) -> str:
        return safe_answer(self.search(text, top_k=3))

