"""Compose multiple knowledge repositories into one searchable corpus."""

from __future__ import annotations

from dataclasses import replace

from .domain import KnowledgeDocument, KnowledgePack
from .interfaces import KnowledgeRepository

CompositeCacheKey = tuple[
    tuple[str, str, str, str, tuple[int, ...]],
    ...,
]


class CompositeKnowledgeRepository(KnowledgeRepository):
    """Expose multiple packs through the existing KnowledgeRepository interface."""

    def __init__(self, repositories: list[KnowledgeRepository] | tuple[KnowledgeRepository, ...]) -> None:
        self.repositories = tuple(repositories)
        if not self.repositories:
            raise ValueError("at least one knowledge repository is required")
        self._document_cache: tuple[CompositeCacheKey, tuple[KnowledgeDocument, ...]] | None = None

    def describe_packs(self) -> tuple[KnowledgePack, ...]:
        packs: list[KnowledgePack] = []
        for index, repository in enumerate(self.repositories, start=1):
            describe_pack = getattr(repository, "describe_pack", None)
            if callable(describe_pack):
                packs.append(describe_pack())
                continue
            packs.append(KnowledgePack(name=f"knowledge-{index}"))
        return tuple(packs)

    def list_documents(self) -> list[KnowledgeDocument]:
        packs = self.describe_packs()
        snapshots: list[tuple[KnowledgeDocument, ...]] = []
        key_parts: list[tuple[str, str, str, str, tuple[int, ...]]] = []

        for repository, pack in zip(self.repositories, packs):
            source_documents = tuple(repository.list_documents())
            snapshots.append(source_documents)
            key_parts.append(
                (
                    pack.name,
                    pack.version,
                    pack.source,
                    pack.path,
                    tuple(id(document) for document in source_documents),
                )
            )

        key: CompositeCacheKey = tuple(key_parts)
        cached = self._document_cache
        if cached is not None and cached[0] == key:
            return list(cached[1])

        documents: list[KnowledgeDocument] = []
        for source_documents, pack in zip(snapshots, packs):
            for document in source_documents:
                documents.append(
                    replace(
                        document,
                        pack_name=pack.name,
                        pack_version=pack.version,
                        pack_source=pack.source,
                        pack_path=pack.path,
                    )
                )

        prepared = tuple(documents)
        self._document_cache = (key, prepared)
        return list(prepared)

    @property
    def pack_count(self) -> int:
        return len(self.repositories)
