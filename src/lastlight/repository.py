"""Repository implementation for Markdown knowledge."""

from __future__ import annotations

from zipfile import ZipFile
from pathlib import Path

from .domain import KnowledgeDocument
from .interfaces import KnowledgeRepository
from .markdown_loader import load_markdown_document, load_markdown_text
from .util import project_root


class MarkdownKnowledgeRepository(KnowledgeRepository):
    def __init__(self, knowledge_dir: Path | str | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else project_root() / "knowledge"

    def list_documents(self) -> list[KnowledgeDocument]:
        if not self.knowledge_dir.exists():
            return []

        if self.knowledge_dir.is_file() and self.knowledge_dir.suffix == ".zip":
            return self._list_zip_documents(self.knowledge_dir)

        root = project_root()
        documents = [
            load_markdown_document(path, root)
            for path in sorted(self.knowledge_dir.rglob("*.md"))
            if path.is_file()
        ]
        return documents

    def _list_zip_documents(self, pack_path: Path) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        with ZipFile(pack_path) as archive:
            for name in sorted(archive.namelist()):
                if name.endswith("/") or not name.casefold().endswith(".md"):
                    continue
                data = archive.read(name)
                text = data.decode("utf-8")
                documents.append(load_markdown_text(text, f"{pack_path.name}:{name}"))
        return documents
