"""Application factory."""

from __future__ import annotations

from pathlib import Path

from .app import LastLightApp
from .repository import MarkdownKnowledgeRepository
from .retrieval import LexicalRetrievalStrategy


class ApplicationFactory:
    @staticmethod
    def create(knowledge_dir: Path | str | None = None) -> LastLightApp:
        repository = MarkdownKnowledgeRepository(knowledge_dir)
        retrieval = LexicalRetrievalStrategy()
        return LastLightApp(repository=repository, retrieval=retrieval)

