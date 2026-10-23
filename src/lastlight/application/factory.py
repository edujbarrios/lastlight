"""Application factory."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .adaptive import AdaptiveRetrievalConfig, AdaptiveRetrievalStrategy
from .app import LastLightApp
from .knowledge_sources import build_knowledge_repository
from .retrieval import BM25RetrievalStrategy, LexicalRetrievalStrategy
from ..retrieval.hybrid import HybridRetrievalStrategy
from ..retrieval.sections import SectionConfig
from ..safety.calibration_v3 import CalibrationConfig


class ApplicationFactory:
    @staticmethod
    def create(
        knowledge_dir: Path | str | Sequence[Path | str] | None = None,
        strategy: str = "lexical",
        language: str | None = None,
        mode: str = "balanced",
        energy_budget_mwh: float | None = None,
        memory_budget_mb: int | None = None,
        decision_profile: str = "balanced",
        calibration: CalibrationConfig | None = None,
        sections: SectionConfig | None = None,
    ) -> LastLightApp:
        repository = build_knowledge_repository(knowledge_dir)
        if strategy == "bm25":
            retrieval = BM25RetrievalStrategy(section_config=sections)
        elif strategy == "hybrid":
            retrieval = HybridRetrievalStrategy(section_config=sections)
        elif strategy == "adaptive":
            retrieval = AdaptiveRetrievalStrategy(
                AdaptiveRetrievalConfig(
                    mode=mode,
                    energy_budget_mwh=energy_budget_mwh,
                    memory_budget_mb=memory_budget_mb,
                )
            )
        else:
            retrieval = LexicalRetrievalStrategy(section_config=sections)
        return LastLightApp(
            repository=repository, retrieval=retrieval, language=language,
            decision_profile=decision_profile, calibration=calibration,
        )
