"""Stable library-facing facade for the LastLight runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .application.factory import ApplicationFactory
from .errors import ConfigurationError
from .safety.triage import first_acceptable_result
from .shared.domain import SearchResult
from .types import QueryResult, RetrievalMetadata, SourceDocument, SourceResult

KnowledgeSource = Path | str
KnowledgeSources = KnowledgeSource | Sequence[KnowledgeSource] | None

SUPPORTED_STRATEGIES = frozenset({"lexical", "bm25", "adaptive"})
SUPPORTED_MODES = frozenset({"survival", "balanced", "accuracy"})


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
        if strategy not in SUPPORTED_STRATEGIES:
            choices = ", ".join(sorted(SUPPORTED_STRATEGIES))
            raise ConfigurationError(
                f"unsupported retrieval strategy: {strategy!r}; choose one of: {choices}"
            )
        if mode not in SUPPORTED_MODES:
            choices = ", ".join(sorted(SUPPORTED_MODES))
            raise ConfigurationError(
                f"unsupported adaptive mode: {mode!r}; choose one of: {choices}"
            )

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

    def search(self, text: str, *, top_k: int = 3) -> list[SourceResult]:
        """Return ranked public source results without leaking internal domain types."""

        return [self._source_result(result) for result in self._search_internal(text, top_k=top_k)]

    def query(self, text: str, *, top_k: int = 3) -> QueryResult:
        """Return a stable, structured result suitable for UIs and integrations."""

        results = self._search_internal(text, top_k=top_k)
        accepted = first_acceptable_result(results)
        metadata = self._metadata(top_k)
        return QueryResult(
            query=text,
            accepted=accepted is not None,
            confidence=accepted.confidence if accepted else None,
            passage=accepted.passage if accepted else None,
            sources=tuple(self._source_result(result) for result in results),
            retrieval=metadata,
        )

    def answer(self, text: str, *, top_k: int = 3) -> str:
        """Return the existing human-readable, safety-aware answer."""

        return self._app.answer(text, top_k=top_k)

    def plan(self, text: str, *, top_k: int = 3) -> RetrievalMetadata:
        """Run retrieval and expose the selected retrieval-policy metadata."""

        self._search_internal(text, top_k=top_k)
        return self._metadata(top_k)

    def retrieval_metadata(self) -> dict[str, object] | None:
        """Compatibility hook for first-party adapters; prefer :meth:`plan`."""

        return self._app.retrieval_metadata()

    def _search_internal(self, text: str, *, top_k: int = 3) -> list[SearchResult]:
        """Internal bridge for first-party adapters that still need domain results."""

        return self._app.search(text, top_k=top_k)

    def _metadata(self, top_k: int) -> RetrievalMetadata:
        raw = self._app.retrieval_metadata() or {
            "strategy": self.strategy,
            "mode": "fixed",
            "effective_top_k": top_k,
        }
        return RetrievalMetadata(
            strategy=str(raw.get("strategy", self.strategy)),
            mode=str(raw.get("mode", "fixed")),
            effective_top_k=int(raw.get("effective_top_k", top_k)),
            risk=str(raw["risk"]) if raw.get("risk") is not None else None,
            reason=str(raw["reason"]) if raw.get("reason") is not None else None,
        )

    @staticmethod
    def _source_result(result: SearchResult) -> SourceResult:
        document = result.document
        public_document = SourceDocument(
            title=document.title,
            path=document.path,
            body=document.body,
            pack_name=document.pack_name,
            pack_version=document.pack_version,
            pack_source=document.pack_source,
            pack_path=document.pack_path,
            language=document.language,
            tags=document.tags,
            priority=document.priority,
        )
        return SourceResult(
            document=public_document,
            score=result.score,
            confidence=result.confidence,
            passage=result.passage,
            matched_terms=result.matched_terms,
        )
