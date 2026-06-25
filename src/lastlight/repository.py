"""Repository implementation for Markdown knowledge."""

from __future__ import annotations

import json
from zipfile import ZipFile
from pathlib import Path

from .domain import KnowledgeDocument, KnowledgePack
from .interfaces import KnowledgeRepository
from .markdown_loader import load_markdown_document, load_markdown_text
from .util import project_root

PACK_MANIFEST = "lastlight-pack.json"


class MarkdownKnowledgeRepository(KnowledgeRepository):
    def __init__(self, knowledge_dir: Path | str | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else project_root() / "knowledge"

    def describe_pack(self) -> KnowledgePack:
        if self.knowledge_dir.is_file() and self.knowledge_dir.suffix == ".zip":
            return self._describe_zip_pack(self.knowledge_dir)

        manifest_path = self.knowledge_dir / PACK_MANIFEST
        if manifest_path.exists():
            metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
            return self._pack_from_metadata(metadata, str(self.knowledge_dir))

        return self._inferred_pack()

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

    def _describe_zip_pack(self, pack_path: Path) -> KnowledgePack:
        if not pack_path.exists():
            return self._inferred_pack()

        with ZipFile(pack_path) as archive:
            names = set(archive.namelist())
            if PACK_MANIFEST in names:
                metadata = json.loads(archive.read(PACK_MANIFEST).decode("utf-8"))
                return self._pack_from_metadata(metadata, str(pack_path))

        return self._inferred_pack()

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

    def _pack_from_metadata(self, metadata: dict[str, object], path: str) -> KnowledgePack:
        languages = metadata.get("languages") or ()
        if isinstance(languages, str):
            language_values = (languages,)
        elif isinstance(languages, list):
            language_values = tuple(str(language) for language in languages)
        else:
            language_values = ()

        return KnowledgePack(
            name=str(metadata.get("name") or self.knowledge_dir.stem or "knowledge"),
            version=str(metadata.get("version") or "unknown"),
            languages=language_values,
            description=str(metadata.get("description") or ""),
            license=str(metadata.get("license") or "unknown"),
            source=str(metadata.get("source") or "local"),
            path=path,
            metadata=metadata,
        )

    def _inferred_pack(self) -> KnowledgePack:
        documents = self.list_documents()
        languages = tuple(sorted({doc.language for doc in documents if doc.language != "unknown"}))
        return KnowledgePack(
            name=self.knowledge_dir.stem or "knowledge",
            languages=languages,
            path=str(self.knowledge_dir),
        )
