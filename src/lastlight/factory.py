"""Application factory."""

from __future__ import annotations

from pathlib import Path

from .adaptive import AdaptiveRetrievalConfig, AdaptiveRetrievalStrategy
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
        mode: str = "balanced",
        energy_budget_mwh: float | None = None,
        memory_budget_mb: int | None = None,
    ) -> LastLightApp:
        repository = MarkdownKnowledgeRepository(knowledge_dir)
        if strategy == "bm25":
            retrieval = BM25RetrievalStrategy()
        elif strategy == "c-lexical":
            retrieval = CBackedLexicalRetrievalStrategy()
        elif strategy == "adaptive":
            retrieval = AdaptiveRetrievalStrategy(
                AdaptiveRetrievalConfig(
                    mode=mode,
                    energy_budget_mwh=energy_budget_mwh,
                    memory_budget_mb=memory_budget_mb,
                )
            )
        else:
            retrieval = LexicalRetrievalStrategy()
        return LastLightApp(repository=repository, retrieval=retrieval, language=language)
