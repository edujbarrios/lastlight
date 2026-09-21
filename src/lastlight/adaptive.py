"""Resource-adaptive retrieval planning."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .compat import is_low_resource_target
from .domain import KnowledgeDocument, SearchQuery, SearchResult
from .interfaces import RetrievalStrategy
from .retrieval import BM25RetrievalStrategy, LexicalRetrievalStrategy
from .tokenizer import tokenize

CRITICAL_RISK_TERMS = frozenset(
    {
        "bleeding",
        "hemorrhage",
        "unconscious",
        "not breathing",
        "chest pain",
        "poison",
        "overdose",
        "seizure",
        "stroke",
        "hemorragia",
        "inconsciente",
        "no respira",
        "dolor pecho",
        "veneno",
        "sobredosis",
        "convulsion",
        "ictus",
    }
)

HIGH_RISK_TERMS = frozenset(
    {
        "water",
        "purify",
        "contaminated",
        "fire",
        "smoke",
        "gas",
        "generator",
        "hypothermia",
        "heatstroke",
        "agua",
        "purificar",
        "contaminada",
        "fuego",
        "humo",
        "gas",
        "generador",
        "hipotermia",
        "golpe calor",
    }
)


@dataclass(frozen=True)
class ResourceProfile:
    low_resource_target: bool
    memory_mb: int | None
    battery_percent: float | None

    @classmethod
    def detect(cls) -> "ResourceProfile":
        return cls(
            low_resource_target=is_low_resource_target(),
            memory_mb=_physical_memory_mb(),
            battery_percent=_battery_percent(),
        )


@dataclass(frozen=True)
class AdaptiveRetrievalConfig:
    mode: str = "balanced"
    energy_budget_mwh: float | None = None
    memory_budget_mb: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"survival", "balanced", "accuracy"}:
            raise ValueError(f"unsupported adaptive mode: {self.mode}")
        if self.energy_budget_mwh is not None and self.energy_budget_mwh <= 0:
            raise ValueError("energy_budget_mwh must be greater than 0")
        if self.memory_budget_mb is not None and self.memory_budget_mb <= 0:
            raise ValueError("memory_budget_mb must be greater than 0")


@dataclass(frozen=True)
class RetrievalDecision:
    strategy: str
    mode: str
    risk: str
    effective_top_k: int
    reason: str
    low_resource_target: bool
    memory_mb: int | None
    battery_percent: float | None
    energy_budget_mwh: float | None
    memory_budget_mb: int | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class AdaptiveRetrievalStrategy(RetrievalStrategy):
    """Select a core retrieval strategy from query risk and constraints."""

    def __init__(
        self,
        config: AdaptiveRetrievalConfig | None = None,
        profile: ResourceProfile | None = None,
    ) -> None:
        self.config = config or AdaptiveRetrievalConfig()
        self.profile = profile or ResourceProfile.detect()
        self.lexical = LexicalRetrievalStrategy()
        self.bm25 = BM25RetrievalStrategy()
        self.last_decision: RetrievalDecision | None = None

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        decision = self.plan(query)
        self.last_decision = decision
        effective_query = SearchQuery(query.text, decision.effective_top_k)
        strategy = {
            "lexical": self.lexical,
            "bm25": self.bm25,
        }[decision.strategy]
        return strategy.search(effective_query, documents)

    def plan(self, query: SearchQuery) -> RetrievalDecision:
        risk = classify_query_risk(query.text)
        constrained, constraint_reason = self._constraint_reason()

        if constrained:
            return self._decision(
                "lexical",
                risk,
                min(max(query.top_k, 1), 2),
                constraint_reason,
            )

        if risk == "critical":
            return self._decision(
                "lexical",
                risk,
                min(max(query.top_k, 1), 3),
                "critical-risk query: prefer the safer lexical refusal profile",
            )

        if risk == "high" and self.config.mode != "accuracy":
            return self._decision(
                "lexical",
                risk,
                min(max(query.top_k, 1), 3),
                "high-risk query in a safety-first mode",
            )

        if self.config.mode == "accuracy":
            return self._decision(
                "bm25",
                risk,
                max(query.top_k, 1),
                "accuracy mode with no active resource constraint",
            )

        return self._decision(
            "bm25",
            risk,
            max(query.top_k, 1),
            "balanced mode with sufficient detected resources",
        )

    def decision_metadata(self) -> dict[str, object] | None:
        return self.last_decision.to_dict() if self.last_decision else None

    def _constraint_reason(self) -> tuple[bool, str]:
        if self.config.mode == "survival":
            return True, "survival mode caps retrieval cost"
        if self.config.energy_budget_mwh is not None and self.config.energy_budget_mwh <= 0.5:
            return True, "energy budget is at or below 0.5 mWh/query"
        if self.config.memory_budget_mb is not None and self.config.memory_budget_mb <= 64:
            return True, "memory budget is at or below 64 MB"
        if self.profile.battery_percent is not None and self.profile.battery_percent <= 20:
            return True, "detected battery is at or below 20%"
        if self.profile.low_resource_target:
            return True, "ARM/Termux low-resource target detected"
        return False, ""

    def _decision(
        self,
        strategy: str,
        risk: str,
        effective_top_k: int,
        reason: str,
    ) -> RetrievalDecision:
        return RetrievalDecision(
            strategy=strategy,
            mode=self.config.mode,
            risk=risk,
            effective_top_k=effective_top_k,
            reason=reason,
            low_resource_target=self.profile.low_resource_target,
            memory_mb=self.profile.memory_mb,
            battery_percent=self.profile.battery_percent,
            energy_budget_mwh=self.config.energy_budget_mwh,
            memory_budget_mb=self.config.memory_budget_mb,
        )


def classify_query_risk(text: str) -> str:
    normalized = " ".join(tokenize(text, keep_stopwords=True))
    if any(term in normalized for term in CRITICAL_RISK_TERMS):
        return "critical"
    if any(term in normalized for term in HIGH_RISK_TERMS):
        return "high"
    return "normal"


def _physical_memory_mb() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(page_size, int) or not isinstance(pages, int):
        return None
    return max(int(page_size * pages / (1024 * 1024)), 1)


def _battery_percent() -> float | None:
    root = Path("/sys/class/power_supply")
    if not root.exists():
        return None
    capacities: list[float] = []
    for supply in sorted(root.iterdir()):
        try:
            supply_type = (supply / "type").read_text(encoding="utf-8").strip().casefold()
            if supply_type != "battery":
                continue
            value = float((supply / "capacity").read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            continue
        capacities.append(value)
    if not capacities:
        return None
    return sum(capacities) / len(capacities)
