"""Application service layer."""

from __future__ import annotations

from .domain import SearchQuery, SearchResult
from .interfaces import KnowledgeRepository, RetrievalStrategy
from .safety import safe_answer
from .synthesis import synthesize_answer
from .triage import append_follow_up_questions, first_acceptable_result


class LastLightApp:
    def __init__(
        self,
        repository: KnowledgeRepository,
        retrieval: RetrievalStrategy,
        language: str | None = None,
    ) -> None:
        self.repository = repository
        self.retrieval = retrieval
        self.language = language.casefold() if language else None

    def search(self, text: str, top_k: int = 3) -> list[SearchResult]:
        documents = self.repository.list_documents()
        if self.language:
            documents = [
                document
                for document in documents
                if document.language.casefold() == self.language
            ]
        return self.retrieval.search(SearchQuery(text=text, top_k=top_k), documents)

    def answer(self, text: str, top_k: int = 3) -> str:
        results = self.search(text, top_k=top_k)
        return append_follow_up_questions(
            safe_answer(results), first_acceptable_result(results)
        )

    def synthesize(self, text: str, top_k: int = 3) -> str:
        return synthesize_answer(text, self.search(text, top_k=top_k))
