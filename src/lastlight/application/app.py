"""Application service layer."""

from __future__ import annotations

from .domain import SearchQuery, SearchResult
from .interfaces import KnowledgeRepository, RetrievalStrategy
from .language import resolve_retrieval_language
from .safety import safe_answer_for_result
from .triage import append_follow_up_questions
from ..safety.calibration import AnswerDecision
from ..safety.calibration_v3 import CalibrationConfig, evaluate_calibrated_decision


class LastLightApp:
    def __init__(
        self,
        repository: KnowledgeRepository,
        retrieval: RetrievalStrategy,
        language: str | None = None,
        decision_profile: str = "balanced",
        calibration: CalibrationConfig | None = None,
    ) -> None:
        self.repository = repository
        self.retrieval = retrieval
        self.language = language.casefold() if language else None
        self.decision_profile = decision_profile
        self.calibration = calibration or CalibrationConfig()

    def search(self, text: str, top_k: int = 3) -> list[SearchResult]:
        documents = self.repository.list_documents()
        effective_language = resolve_retrieval_language(
            text,
            documents,
            explicit_language=self.language,
        )
        if effective_language:
            documents = [
                document
                for document in documents
                if document.language.casefold() == effective_language
            ]
        return self.retrieval.search(SearchQuery(text=text, top_k=top_k), documents)

    def decide(self, text: str, results: list[SearchResult]) -> AnswerDecision:
        metadata = self.retrieval_metadata() or {}
        selected = str(metadata.get("strategy") or (
            "bm25" if type(self.retrieval).__name__ == "BM25RetrievalStrategy"
            else "hybrid" if type(self.retrieval).__name__ == "HybridRetrievalStrategy"
            else "lexical"
        ))
        return evaluate_calibrated_decision(
            text, results, strategy=selected, profile=self.decision_profile,
            corpus=self.repository.list_documents(), config=self.calibration,
            verification_agreement=(metadata.get("verification_agreement")
                                    if isinstance(metadata.get("verification_agreement"), bool)
                                    else None),
        )

    def answer(self, text: str, top_k: int = 3) -> str:
        results = self.search(text, top_k=top_k)
        decision = self.decide(text, results)
        return append_follow_up_questions(
            safe_answer_for_result(decision.result, confidence=decision.confidence),
            decision.result,
        )

    def retrieval_metadata(self) -> dict[str, object] | None:
        getter = getattr(self.retrieval, "decision_metadata", None)
        if not callable(getter):
            return None
        metadata = getter()
        return metadata if isinstance(metadata, dict) else None
