"""Stable library-facing facade for the LastLight runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .application.factory import ApplicationFactory
from .shared.domain import SearchResult

KnowledgeSource = Path | str
KnowledgeSources = KnowledgeSource | Sequence[KnowledgeSource] | None


class LastLight:
    """Small public facade over the offline LastLight application runtime.

    Ecosystem clients should prefer this facade instead of importing internal
    factories or package-specific implementation modules.
    """

    def __init__(
        self,
        knowledge: KnowledgeSources = None,
        *,
        strategy: str = "lexical",
        language: str | None = None,
        mode: str = "balanced",
        energy_budget_mwh: float | None = None,
        memory_budget_mb: int | None = None,
    ) -> None:
        self.strategy = strategy
        self.mode = mode
        self._app = ApplicationFactory.create(
            knowledge_dir=knowledge,
            strategy=strategy,
            language=language,
            mode=mode,
            energy_budget_mwh=energy_budget_mwh,
            memory_budget_mb=memory_budget_mb,
        )

    @classmethod
    def from_packs(
        cls,
        packs: Sequence[KnowledgeSource],
        **kwargs: object,
    ) -> "LastLight":
        """Create an engine from one or more local directory/ZIP packs."""

        return cls(knowledge=packs, **kwargs)

    def search(self, text: str, *, top_k: int = 3) -> list[SearchResult]:
        """Return ranked retrieval results."""

        return self._app.search(text, top_k=top_k)

    def answer(self, text: str, *, top_k: int = 3) -> str:
        """Return the existing human-readable, safety-aware answer."""

        return self._app.answer(text, top_k=top_k)

    def plan(self, text: str, *, top_k: int = 3) -> dict[str, object]:
        """Run retrieval and expose the selected retrieval-policy metadata."""

        self._app.search(text, top_k=top_k)
        return self._app.retrieval_metadata() or {
            "strategy": self.strategy,
            "mode": "fixed",
            "effective_top_k": top_k,
        }
