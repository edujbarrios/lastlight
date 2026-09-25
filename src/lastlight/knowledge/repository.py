"""Repository implementation for Markdown knowledge."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo

from ..errors import PackError
from .domain import KnowledgeDocument, KnowledgePack
from .interfaces import KnowledgeRepository
from .markdown_loader import load_markdown_document, load_markdown_text
from .util import project_root

PACK_MANIFEST = "lastlight-pack.json"
PACK_README = "README.md"
MAX_ZIP_DOCUMENTS = 10_000
MAX_ZIP_ENTRY_BYTES = 2 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 256 * 1024


class MarkdownKnowledgeRepository(KnowledgeRepository):
    def __init__(self, knowledge_dir: Path | str | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else project_root() / "knowledge"

    def describe_pack(self) -> KnowledgePack:
        if _is_zip_pack(self.knowledge_dir):
            return self._describe_zip_pack(self.knowledge_dir)

        manifest_path = self.knowledge_dir / PACK_MANIFEST
        if manifest_path.exists():
            try:
                pack_root = self.knowledge_dir.resolve()
                resolved_manifest = manifest_path.resolve()
                if not resolved_manifest.is_relative_to(pack_root):
                    raise PackError(f"pack manifest escapes pack root: {manifest_path}")
                if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
                    raise PackError("pack manifest exceeds maximum allowed size")
                metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
            except PackError:
                raise
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise PackError(f"cannot read pack manifest: {error}") from error
            if not isinstance(metadata, dict):
                raise PackError("pack manifest must contain a JSON object")
            return self._pack_from_metadata(metadata, str(self.knowledge_dir))

        return self._inferred_pack()

    def list_documents(self) -> list[KnowledgeDocument]:
        if not self.knowledge_dir.exists():
            return []
        if _is_zip_pack(self.knowledge_dir):
            return self._list_zip_documents(self.knowledge_dir)

        pack_root = self.knowledge_dir.resolve()
        documents: list[KnowledgeDocument] = []
        for path in sorted(self.knowledge_dir.rglob("*")):
            if not path.is_file() or not _is_directory_markdown_document(path, self.knowledge_dir):
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(pack_root):
                raise PackError(f"knowledge document escapes pack root: {path}")
            try:
                documents.append(load_markdown_document(path, self.knowledge_dir))
            except (OSError, UnicodeDecodeError) as error:
                raise PackError(f"cannot read knowledge document {path}: {error}") from error
        return documents

    def _describe_zip_pack(self, pack_path: Path) -> KnowledgePack:
        if not pack_path.exists():
            return self._inferred_pack()
        try:
            with ZipFile(pack_path) as archive:
                infos = _validated_zip_infos(archive)
                manifest = next((info for info in infos if _canonical_zip_name(info.filename) == PACK_MANIFEST), None)
                if manifest is None:
                    return self._inferred_pack()
                if manifest.file_size > MAX_MANIFEST_BYTES:
                    raise PackError("pack manifest exceeds maximum allowed size")
                metadata = json.loads(archive.read(manifest).decode("utf-8"))
                if not isinstance(metadata, dict):
                    raise PackError("pack manifest must contain a JSON object")
                return self._pack_from_metadata(metadata, str(pack_path))
        except PackError:
            raise
        except (BadZipFile, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PackError(f"cannot read ZIP pack {pack_path}: {error}") from error

    def _list_zip_documents(self, pack_path: Path) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        try:
            with ZipFile(pack_path) as archive:
                infos = _validated_zip_infos(archive)
                markdown_infos = [info for info in infos if _is_zip_markdown_document(info.filename)]
                if len(markdown_infos) > MAX_ZIP_DOCUMENTS:
                    raise PackError(f"ZIP pack contains more than {MAX_ZIP_DOCUMENTS} Markdown documents")
                total_size = sum(info.file_size for info in markdown_infos)
                if total_size > MAX_ZIP_TOTAL_BYTES:
                    raise PackError("ZIP pack Markdown content exceeds maximum uncompressed size")
                for info in sorted(markdown_infos, key=lambda item: _canonical_zip_name(item.filename)):
                    if info.file_size > MAX_ZIP_ENTRY_BYTES:
                        raise PackError(f"ZIP entry exceeds maximum size: {info.filename}")
                    name = _canonical_zip_name(info.filename)
                    text = archive.read(info).decode("utf-8")
                    documents.append(load_markdown_text(text, name))
        except PackError:
            raise
        except (BadZipFile, OSError, UnicodeDecodeError) as error:
            raise PackError(f"cannot read ZIP pack {pack_path}: {error}") from error
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
        return KnowledgePack(name=self.knowledge_dir.stem or "knowledge", languages=languages, path=str(self.knowledge_dir))


def _is_zip_pack(path: Path) -> bool:
    return path.is_file() and path.suffix.casefold() == ".zip"


def _is_directory_markdown_document(path: Path, pack_root: Path) -> bool:
    try:
        relative = path.relative_to(pack_root)
    except ValueError:
        return False
    parts = relative.parts
    if any(part.startswith(".") or part == "__MACOSX" for part in parts):
        return False
    if len(parts) == 1 and relative.name.casefold() == PACK_README.casefold():
        return False
    return relative.suffix.casefold() == ".md"


def _canonical_zip_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PackError(f"unsafe ZIP member path: {name}")
    return path.as_posix()


def _validated_zip_infos(archive: ZipFile) -> tuple[ZipInfo, ...]:
    infos = tuple(archive.infolist())
    seen: set[str] = set()
    for info in infos:
        if info.is_dir():
            continue
        canonical = _canonical_zip_name(info.filename)
        folded = canonical.casefold()
        if folded in seen:
            raise PackError(f"duplicate ZIP member path after normalization: {canonical}")
        seen.add(folded)
    return infos


def _is_zip_markdown_document(name: str) -> bool:
    normalized = _canonical_zip_name(name)
    parts = PurePosixPath(normalized).parts
    if any(part.startswith(".") or part == "__MACOSX" for part in parts):
        return False
    if len(parts) == 1 and parts[0].casefold() == PACK_README.casefold():
        return False
    return parts[-1].casefold().endswith(".md")
