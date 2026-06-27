"""Evaluation framework for deterministic retrieval."""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from statistics import mean

from .app import LastLightApp
from .domain import EvaluationCase, SearchResult
from .util import project_root

DEFAULT_EVAL_OUTPUT = project_root() / "eval" / "results.json"
DEFAULT_EVAL_TOP_K = 3


def load_evaluation_cases(path: Path | None = None) -> list[EvaluationCase]:
    path = path or project_root() / "data" / "eval.jsonl"
    cases: list[EvaluationCase] = []
    if not path.exists():
        return cases
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(
            EvaluationCase(
                query=raw["query"],
                expected_tag=raw["expected_tag"],
                difficulty=raw.get("difficulty", "standard"),
                expected_language=raw.get("expected_language"),
            )
        )
    return cases


def build_evaluation_report(
    app: LastLightApp,
    cases: list[EvaluationCase] | None = None,
    top_k: int = DEFAULT_EVAL_TOP_K,
) -> dict[str, object]:
    cases = cases if cases is not None else load_evaluation_cases()
    confidence_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    case_results: list[dict[str, object]] = []
    top_1_correct = 0
    top_k_correct = 0
    reciprocal_ranks: list[float] = []
    elapsed_samples_ms: list[float] = []
    by_tag: dict[str, dict[str, object]] = {}
    by_difficulty: dict[str, dict[str, object]] = {}
    by_language: dict[str, dict[str, object]] = {}

    for case in cases:
        start = time.perf_counter()
        results = app.search(case.query, top_k=top_k)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        elapsed_samples_ms.append(elapsed_ms)
        rank = _expected_rank(results, case)
        top_1_match = rank == 1
        top_k_match = rank is not None
        reciprocal_rank = 1.0 / rank if rank is not None else 0.0
        reciprocal_ranks.append(reciprocal_rank)
        if top_1_match:
            top_1_correct += 1
        if top_k_match:
            top_k_correct += 1

        _record_bucket(by_tag, case.expected_tag, top_1_match, top_k_match, reciprocal_rank)
        _record_bucket(
            by_difficulty, case.difficulty, top_1_match, top_k_match, reciprocal_rank
        )
        _record_bucket(
            by_language,
            case.expected_language or "unspecified",
            top_1_match,
            top_k_match,
            reciprocal_rank,
        )

        if not results:
            confidence_counts["NONE"] += 1
            language_counts["NONE"] += 1
            case_results.append(
                {
                    "query": case.query,
                    "expected_tag": case.expected_tag,
                    "expected_language": case.expected_language,
                    "difficulty": case.difficulty,
                    "top_1_correct": False,
                    "top_k_correct": False,
                    "rank": None,
                    "reciprocal_rank": 0.0,
                    "confidence": "NONE",
                    "elapsed_ms": elapsed_ms,
                    "result": None,
                    "results": [],
                }
            )
            continue
        top = results[0]
        confidence_counts[top.confidence] += 1
        language_counts[top.document.language] += 1
        case_results.append(
            {
                "query": case.query,
                "expected_tag": case.expected_tag,
                "expected_language": case.expected_language,
                "difficulty": case.difficulty,
                "top_1_correct": top_1_match,
                "top_k_correct": top_k_match,
                "rank": rank,
                "reciprocal_rank": reciprocal_rank,
                "confidence": top.confidence,
                "elapsed_ms": elapsed_ms,
                "result": {
                    "title": top.document.title,
                    "path": top.document.path,
                    "language": top.document.language,
                    "tags": list(top.document.tags),
                    "score": top.score,
                    "matched_terms": list(top.matched_terms),
                    "passage": top.passage,
                },
                "results": [_serialize_result(result) for result in results],
            }
        )

    total = len(cases)
    top_1_accuracy = top_1_correct / total if total else 0.0
    top_k_accuracy = top_k_correct / total if total else 0.0
    mean_reciprocal_rank = mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    return {
        "benchmark": {
            "top_k": top_k,
            "case_source": "data/eval.jsonl",
            "notes": (
                "Deterministic retrieval benchmark over local Markdown knowledge. "
                "A case is correct when any retrieved document contains the expected tag."
            ),
        },
        "total_cases": total,
        "correct": top_1_correct,
        "top_1_correct": top_1_correct,
        "top_k_correct": top_k_correct,
        "top_1_accuracy": top_1_accuracy,
        "top_k_accuracy": top_k_accuracy,
        "mean_reciprocal_rank": mean_reciprocal_rank,
        "latency_ms": _latency_summary(elapsed_samples_ms),
        "confidence": {
            label: confidence_counts.get(label, 0)
            for label in ("HIGH", "MEDIUM", "LOW", "NONE")
        },
        "top_result_languages": dict(sorted(language_counts.items())),
        "by_expected_tag": _finalize_buckets(by_tag),
        "by_difficulty": _finalize_buckets(by_difficulty),
        "by_expected_language": _finalize_buckets(by_language),
        "cases": case_results,
    }


def format_evaluation_report(report: dict[str, object]) -> str:
    confidence = report["confidence"]
    cases = report["cases"]
    failures: list[str] = []
    for case in cases:
        if case["top_1_correct"]:
            continue
        result = case["result"]
        if result is None:
            failures.append(f"- {case['query']!r}: no result")
        else:
            failures.append(
                f"- {case['query']!r}: expected tag {case['expected_tag']!r}, "
                f"got {result['path']}"
            )

    lines = [
        "LastLight evaluation",
        f"Total cases: {report['total_cases']}",
        f"Top-1 accuracy: {report['top_1_accuracy']:.2%}",
        f"Top-{report['benchmark']['top_k']} accuracy: {report['top_k_accuracy']:.2%}",
        f"MRR: {report['mean_reciprocal_rank']:.3f}",
        f"Mean search latency: {report['latency_ms']['mean']:.3f} ms",
        "Confidence statistics:",
    ]
    for label in ("HIGH", "MEDIUM", "LOW", "NONE"):
        lines.append(f"- {label}: {confidence.get(label, 0)}")
    lines.append("Failed cases:")
    lines.extend(failures if failures else ["- none"])
    return "\n".join(lines)


def run_evaluation(app: LastLightApp, cases: list[EvaluationCase] | None = None) -> str:
    return format_evaluation_report(build_evaluation_report(app, cases))


def write_evaluation_report(
    report: dict[str, object], output_path: Path | str = DEFAULT_EVAL_OUTPUT
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def _expected_rank(results: list[SearchResult], case: EvaluationCase) -> int | None:
    for index, result in enumerate(results, start=1):
        if case.expected_tag not in result.document.tags:
            continue
        if (
            case.expected_language is not None
            and result.document.language != case.expected_language
        ):
            continue
        return index
    return None


def _serialize_result(result: SearchResult) -> dict[str, object]:
    return {
        "title": result.document.title,
        "path": result.document.path,
        "language": result.document.language,
        "tags": list(result.document.tags),
        "score": result.score,
        "confidence": result.confidence,
        "matched_terms": list(result.matched_terms),
        "passage": result.passage,
    }


def _record_bucket(
    buckets: dict[str, dict[str, object]],
    key: str,
    top_1_match: bool,
    top_k_match: bool,
    reciprocal_rank: float,
) -> None:
    bucket = buckets.setdefault(
        key,
        {
            "total": 0,
            "top_1_correct": 0,
            "top_k_correct": 0,
            "reciprocal_rank_sum": 0.0,
        },
    )
    bucket["total"] = int(bucket["total"]) + 1
    bucket["top_1_correct"] = int(bucket["top_1_correct"]) + int(top_1_match)
    bucket["top_k_correct"] = int(bucket["top_k_correct"]) + int(top_k_match)
    bucket["reciprocal_rank_sum"] = float(bucket["reciprocal_rank_sum"]) + reciprocal_rank


def _finalize_buckets(
    buckets: dict[str, dict[str, object]]
) -> dict[str, dict[str, object]]:
    finalized: dict[str, dict[str, object]] = {}
    for key, bucket in sorted(buckets.items()):
        total = int(bucket["total"])
        top_1_correct = int(bucket["top_1_correct"])
        top_k_correct = int(bucket["top_k_correct"])
        reciprocal_rank_sum = float(bucket["reciprocal_rank_sum"])
        finalized[key] = {
            "total": total,
            "top_1_correct": top_1_correct,
            "top_k_correct": top_k_correct,
            "top_1_accuracy": top_1_correct / total if total else 0.0,
            "top_k_accuracy": top_k_correct / total if total else 0.0,
            "mean_reciprocal_rank": reciprocal_rank_sum / total if total else 0.0,
        }
    return finalized


def _latency_summary(samples_ms: list[float]) -> dict[str, float]:
    if not samples_ms:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
    ordered = sorted(samples_ms)
    p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    return {
        "mean": mean(samples_ms),
        "min": min(samples_ms),
        "max": max(samples_ms),
        "p95": ordered[p95_index],
    }
