"""CLI construction adapter backed by the public Python API."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..api import LastLight


class ApplicationFactory:
    """Backward-compatible CLI factory that now constructs ``LastLight``."""

    @staticmethod
    def create(
        knowledge_dir: Path | str | Sequence[Path | str] | None = None,
        strategy: str = "lexical",
        language: str | None = None,
        mode: str = "balanced",
        energy_budget_mwh: float | None = None,
        memory_budget_mb: int | None = None,
    ) -> LastLight:
        return LastLight(
            knowledge=knowledge_dir,
            strategy=strategy,
            language=language,
            mode=mode,
            energy_budget_mwh=energy_budget_mwh,
            memory_budget_mb=memory_budget_mb,
        )
