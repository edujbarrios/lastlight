"""Repository implementation for Markdown knowledge."""

from __future__ import annotations

from pathlib import Path

from .domain import KnowledgeDocument
from .interfaces import KnowledgeRepository
from .markdown_loader import load_markdown_document
from .util import project_root


class MarkdownKnowledgeRepository(KnowledgeRepository):
    def __init__(self, knowledge_dir: Path | str | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else project_root() / "knowledge"

    def list_documents(self) -> list[KnowledgeDocument]:
        if not self.knowledge_dir.exists():
            return []

        root = project_root()
        documents = [
            load_markdown_document(path, root)
            for path in sorted(self.knowledge_dir.rglob("*.md"))
            if path.is_file()
        ]
        return documents

