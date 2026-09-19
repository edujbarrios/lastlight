"""Compose multiple knowledge repositories into one searchable corpus."""

from __future__ import annotations

from dataclasses import replace

from .domain import KnowledgeDocument, KnowledgePack
from .interfaces import KnowledgeRepository


class CompositeKnowledgeRepository(KnowledgeRepository):
    """Expose multiple packs through the existing KnowledgeRepository interface."""

    def __init__(self, repositories: list[KnowledgeRepository] | tuple[KnowledgeRepository, ...]) -> None:
        self.repositories = tuple(repositories)
        if not self.repositories:
            raise ValueError("at least one knowledge repository is required")

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
        documents: list[KnowledgeDocument] = []
        for repository, pack in zip(self.repositories, self.describe_packs()):
            for document in repository.list_documents():
                documents.append(
                    replace(
                        document,
                        pack_name=pack.name,
                        pack_version=pack.version,
                        pack_source=pack.source,
                        pack_path=pack.path,
                    )
                )
        return documents

    @property
    def pack_count(self) -> int:
        return len(self.repositories)
