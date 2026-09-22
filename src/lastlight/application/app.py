"""Application service layer."""

from __future__ import annotations

from .domain import SearchQuery, SearchResult
from .interfaces import KnowledgeRepository, RetrievalStrategy
from .language import resolve_retrieval_language
from .safety import safe_answer
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
        effective_language = resolve_retrieval_language(
            text,
            documents,
            explicit_language=self.language,
        )
        if effective_language:
            documents = [
                document
                for document in documents
                if document.language.casefold() == effective_language
            ]
        return self.retrieval.search(SearchQuery(text=text, top_k=top_k), documents)

    def answer(self, text: str, top_k: int = 3) -> str:
        results = self.search(text, top_k=top_k)
        return append_follow_up_questions(
            safe_answer(results), first_acceptable_result(results)
        )

    def retrieval_metadata(self) -> dict[str, object] | None:
        getter = getattr(self.retrieval, "decision_metadata", None)
        if not callable(getter):
            return None
        metadata = getter()
        return metadata if isinstance(metadata, dict) else None
