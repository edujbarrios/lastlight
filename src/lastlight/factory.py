"""Application factory."""

from __future__ import annotations

from pathlib import Path

from .app import LastLightApp
from .repository import MarkdownKnowledgeRepository
from .retrieval import (
    BM25RetrievalStrategy,
    CBackedLexicalRetrievalStrategy,
    LexicalRetrievalStrategy,
)


class ApplicationFactory:
    @staticmethod
    def create(
        knowledge_dir: Path | str | None = None,
        strategy: str = "lexical",
        language: str | None = None,
    ) -> LastLightApp:
        repository = MarkdownKnowledgeRepository(knowledge_dir)
        if strategy == "bm25":
            retrieval = BM25RetrievalStrategy()
        elif strategy == "c-lexical":
            retrieval = CBackedLexicalRetrievalStrategy()
        else:
            retrieval = LexicalRetrievalStrategy()
        return LastLightApp(repository=repository, retrieval=retrieval, language=language)
