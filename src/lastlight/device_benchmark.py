"""Integrated device benchmark for retrieval, safety, memory, and energy."""

from __future__ import annotations

import os
import platform
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

from .energy import EnergyMeter, discover_energy_meter, energy_delta_mwh
from .evaluation import build_evaluation_report, load_evaluation_cases
from .factory import ApplicationFactory
from .repository import MarkdownKnowledgeRepository

DEFAULT_STRATEGIES = ("lexical", "bm25", "c-lexical", "adaptive")


@dataclass(frozen=True)
class StrategyBenchmark:
    strategy: str
    cases: int
    top_1_accuracy: float
    top_k_accuracy: float
    mrr: float
    answer_precision: float
    refusal_recall: float
    answerable_recall: float
    mean_latency_ms: float
    p95_latency_ms: float
    python_peak_memory_mb: float
    energy_per_query_mwh: float | None
    energy_kind: str
    elapsed_s: float

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "cases": self.cases,
            "top_1_accuracy": self.top_1_accuracy,
            "top_k_accuracy": self.top_k_accuracy,
            "mrr": self.mrr,
            "answer_precision": self.answer_precision,
            "refusal_recall": self.refusal_recall,
            "answerable_recall": self.answerable_recall,
            "mean_latency_ms": self.mean_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "python_peak_memory_mb": self.python_peak_memory_mb,
            "energy_per_query_mwh": self.energy_per_query_mwh,
            "energy_kind": self.energy_kind,
            "elapsed_s": self.elapsed_s,
        }


def build_device_benchmark(
    knowledge_dir: Path | str | None = None,
    *,
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    energy_source: str = "auto",
    energy_counter: Path | str | None = None,
    energy_unit: str = "mwh",
    watts: float = 15.0,
    max_cases: int | None = None,
) -> dict[str, object]:
    if watts <= 0:
        raise ValueError("watts must be greater than 0")
    if max_cases is not None and max_cases < 1:
        raise ValueError("max_cases must be at least 1")

    repository = MarkdownKnowledgeRepository(knowledge_dir)
    documents = repository.list_documents()
    cases = load_evaluation_cases()
    if max_cases is not None:
        cases = cases[:max_cases]

    meter = discover_energy_meter(
        energy_source,
        counter_path=energy_counter,
        counter_unit=energy_unit,
    )
    results = [
        _benchmark_strategy(
            strategy,
            knowledge_dir,
            cases,
            meter=meter,
            watts=watts,
        )
        for strategy in strategies
    ]

    return {
        "device": _device_profile(),
        "corpus": {
            "documents": len(documents),
            "characters": sum(len(document.body) for document in documents),
            "languages": sorted(
                {document.language for document in documents if document.language != "unknown"}
            ),
        },
        "evaluation_cases": len(cases),
        "energy_source": meter.name if meter is not None else f"estimate-{watts:.1f}W",
        "strategies": [result.to_dict() for result in results],
        "recommendation": recommend_strategy(results),
    }


def _benchmark_strategy(
    strategy: str,
    knowledge_dir: Path | str | None,
    cases: list[object],
    *,
    meter: EnergyMeter | None,
    watts: float,
) -> StrategyBenchmark:
    factory_kwargs: dict[str, object] = {
        "knowledge_dir": knowledge_dir,
        "strategy": strategy,
    }
    if strategy == "adaptive":
        factory_kwargs["mode"] = "balanced"
    app = ApplicationFactory.create(**factory_kwargs)

    before_energy = meter.sample() if meter is not None else None
    tracemalloc.start()
    start = time.perf_counter()
    report = build_evaluation_report(app, cases=cases)
    elapsed_s = time.perf_counter() - start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    after_energy = meter.sample() if meter is not None else None

    total_cases = int(report["total_cases"])
    if meter is not None and before_energy is not None and after_energy is not None:
        total_energy_mwh = energy_delta_mwh(before_energy, after_energy)
        energy_kind = "measured"
    else:
        total_energy_mwh = watts * elapsed_s / 3.6
        energy_kind = "estimated"
    energy_per_query = total_energy_mwh / total_cases if total_cases else None

    latency = report["latency_ms"]
    decisions = report["decision_metrics"]
    return StrategyBenchmark(
        strategy=strategy,
        cases=total_cases,
        top_1_accuracy=float(report["top_1_accuracy"]),
        top_k_accuracy=float(report["top_k_accuracy"]),
        mrr=float(report["mean_reciprocal_rank"]),
        answer_precision=float(decisions["answer_precision"]),
        refusal_recall=float(decisions["refusal_recall"]),
        answerable_recall=float(decisions["answerable_recall"]),
        mean_latency_ms=float(latency["mean"]),
        p95_latency_ms=float(latency["p95"]),
        python_peak_memory_mb=peak_bytes / (1024 * 1024),
        energy_per_query_mwh=energy_per_query,
        energy_kind=energy_kind,
        elapsed_s=elapsed_s,
    )


def recommend_strategy(results: list[StrategyBenchmark]) -> dict[str, object]:
    if not results:
        return {"strategy": None, "reason": "no benchmark results"}

    def score(result: StrategyBenchmark) -> tuple[float, float, float, float]:
        safety = 0.6 * result.answer_precision + 0.4 * result.refusal_recall
        energy = result.energy_per_query_mwh
        efficiency = 1.0 / energy if energy is not None and energy > 0 else 0.0
        return (
            safety,
            result.top_k_accuracy,
            efficiency,
            -result.p95_latency_ms,
        )

    best = max(results, key=score)
    return {
        "strategy": best.strategy,
        "reason": (
            "highest safety-first score (60% answer precision, 40% refusal recall), "
            "then top-k accuracy, energy/query, and p95 latency"
        ),
        "answer_precision": best.answer_precision,
        "refusal_recall": best.refusal_recall,
        "energy_per_query_mwh": best.energy_per_query_mwh,
        "energy_kind": best.energy_kind,
    }


def format_device_benchmark(report: dict[str, object]) -> str:
    device = report["device"]
    corpus = report["corpus"]
    lines = [
        "LastLight Device Benchmark",
        "=" * 28,
        "",
        "Device",
        f"Platform: {device['platform']}",
        f"Machine: {device['machine']}",
        f"CPU cores: {device['cpu_count']}",
        f"Python: {device['python']}",
        f"Physical memory: {device['memory_mb'] if device['memory_mb'] is not None else 'unknown'} MB",
        "",
        "Corpus",
        f"Documents: {corpus['documents']}",
        f"Characters: {corpus['characters']}",
        f"Languages: {', '.join(corpus['languages']) or 'unknown'}",
        f"Evaluation cases: {report['evaluation_cases']}",
        f"Energy source: {report['energy_source']}",
        "",
        "| Strategy | Top-1 | Top-k | Precision | Refusal recall | p95 | Peak Python MB | Energy/query |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in report["strategies"]:
        energy = result["energy_per_query_mwh"]
        energy_text = (
            f"{energy:.4f} mWh ({result['energy_kind']})"
            if energy is not None
            else "n/a"
        )
        lines.append(
            f"| {result['strategy']} | {result['top_1_accuracy']:.2%} | "
            f"{result['top_k_accuracy']:.2%} | {result['answer_precision']:.2%} | "
            f"{result['refusal_recall']:.2%} | {result['p95_latency_ms']:.2f} ms | "
            f"{result['python_peak_memory_mb']:.2f} | {energy_text} |"
        )
    recommendation = report["recommendation"]
    lines.extend(
        [
            "",
            f"Recommendation: {recommendation['strategy']}",
            f"Reason: {recommendation['reason']}",
        ]
    )
    return "\n".join(lines)


def _device_profile() -> dict[str, object]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine() or "unknown",
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory_mb": _physical_memory_mb(),
    }


def _physical_memory_mb() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(page_size, int) or not isinstance(pages, int):
        return None
    return max(int(page_size * pages / (1024 * 1024)), 1)
