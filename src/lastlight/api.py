"""Stable library-facing facade for the LastLight runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .application.factory import ApplicationFactory
from .errors import ConfigurationError, PackValidationError
from .knowledge.pack_validation import validate_pack
from .knowledge.provenance import verify_pack_provenance
from .safety.triage import first_acceptable_result
from .shared.domain import SearchResult
from .types import (
    PackInfo,
    PackProvenance,
    PackValidation,
    QueryResult,
    RetrievalMetadata,
    SourceDocument,
    SourceResult,
)

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

    def packs(self) -> tuple[PackInfo, ...]:
        """Return stable metadata for every mounted knowledge pack."""

        return tuple(self._pack_info(repository) for repository in self._repositories())

    def validate_packs(self, *, raise_on_error: bool = False) -> tuple[PackValidation, ...]:
        """Validate all mounted packs without requiring CLI parsing.

        Set ``raise_on_error=True`` when an integration should fail fast instead
        of inspecting the returned validation reports.
        """

        reports: list[PackValidation] = []
        for repository in self._repositories():
            report = validate_pack(repository)
            reports.append(
                PackValidation(
                    pack=self._pack_info(repository),
                    ok=report.ok,
                    errors=report.errors,
                    warnings=report.warnings,
                )
            )
        result = tuple(reports)
        if raise_on_error:
            failures = [report for report in result if not report.ok]
            if failures:
                summary = "; ".join(
                    f"{report.pack.name}: {', '.join(report.errors)}" for report in failures
                )
                raise PackValidationError(summary)
        return result

    def verify_provenance(self, *, stale_after_days: int = 365) -> tuple[PackProvenance, ...]:
        """Verify fingerprints, freshness and provenance for every mounted pack."""

        reports: list[PackProvenance] = []
        for repository in self._repositories():
            report = verify_pack_provenance(
                repository,
                stale_after_days=stale_after_days,
            )
            reports.append(
                PackProvenance(
                    pack=self._pack_info(repository),
                    ok=report.ok,
                    fingerprint_sha256=report.fingerprint_sha256,
                    publisher=report.publisher,
                    published_at=report.published_at,
                    expires_at=report.expires_at,
                    age_days=report.age_days,
                    expired=report.expired,
                    errors=report.errors,
                    warnings=report.warnings,
                )
            )
        return tuple(reports)

    def search(self, text: str, *, top_k: int = 3) -> list[SourceResult]:
        """Return ranked public source results without leaking internal domain types."""

        return [self._source_result(result) for result in self._search_internal(text, top_k=top_k)]

    def query(self, text: str, *, top_k: int = 3) -> QueryResult:
        """Return a stable, structured result suitable for UIs and integrations."""

        results = self._search_internal(text, top_k=top_k)
        accepted = first_acceptable_result(results)
        metadata = self._metadata(top_k)
        refusal_reason = None
        if accepted is None:
            refusal_reason = "no_matching_knowledge" if not results else "insufficient_confidence"
        return QueryResult(
            query=text,
            accepted=accepted is not None,
            confidence=accepted.confidence if accepted else None,
            passage=accepted.passage if accepted else None,
            sources=tuple(self._source_result(result) for result in results),
            retrieval=metadata,
            refusal_reason=refusal_reason,
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

    def _repositories(self) -> tuple[object, ...]:
        repository = self._app.repository
        repositories = getattr(repository, "repositories", None)
        if isinstance(repositories, tuple):
            return repositories
        if isinstance(repositories, list):
            return tuple(repositories)
        return (repository,)

    @staticmethod
    def _pack_info(repository: object) -> PackInfo:
        describe_pack = getattr(repository, "describe_pack", None)
        list_documents = getattr(repository, "list_documents", None)
        if not callable(list_documents):
            raise TypeError("knowledge repository does not expose list_documents()")
        documents = list_documents()
        pack = describe_pack() if callable(describe_pack) else None
        return PackInfo(
            name=str(getattr(pack, "name", "knowledge")),
            version=str(getattr(pack, "version", "unknown")),
            languages=tuple(getattr(pack, "languages", ()) or ()),
            description=str(getattr(pack, "description", "")),
            license=str(getattr(pack, "license", "unknown")),
            source=str(getattr(pack, "source", "local")),
            path=str(getattr(pack, "path", "")),
            document_count=len(documents),
        )

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
            low_resource_target=(
                bool(raw["low_resource_target"])
                if raw.get("low_resource_target") is not None
                else None
            ),
            memory_mb=int(raw["memory_mb"]) if raw.get("memory_mb") is not None else None,
            battery_percent=(
                float(raw["battery_percent"])
                if raw.get("battery_percent") is not None
                else None
            ),
            energy_budget_mwh=(
                float(raw["energy_budget_mwh"])
                if raw.get("energy_budget_mwh") is not None
                else None
            ),
            memory_budget_mb=(
                int(raw["memory_budget_mb"])
                if raw.get("memory_budget_mb") is not None
                else None
            ),
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
