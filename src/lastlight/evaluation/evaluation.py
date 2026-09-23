"""Evaluation framework for deterministic core regression checks."""

from __future__ import annotations

import json
import time
from collections import Counter
from importlib.resources import files
from pathlib import Path
from statistics import mean

from .app import LastLightApp
from .domain import EvaluationCase, SearchResult

DEFAULT_EVAL_RESOURCE = "data/eval_core.jsonl"
DEFAULT_EVAL_OUTPUT = Path.cwd() / "eval" / "core-results.json"
DEFAULT_EVAL_TOP_K = 3
EVAL_THRESHOLDS = {
    "top_1_accuracy": 0.75,
    "answer_precision": 0.95,
    "refusal_recall": 1.0,
    "answerable_recall": 0.75,
}


def load_evaluation_cases(path: Path | None = None) -> list[EvaluationCase]:
    if path is None:
        text = files("lastlight.evaluation").joinpath(DEFAULT_EVAL_RESOURCE).read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    cases: list[EvaluationCase] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(EvaluationCase(
            query=raw["query"],
            expected_tag=raw.get("expected_tag"),
            difficulty=raw.get("difficulty", "standard"),
            expected_language=raw.get("expected_language"),
            expected_tags=tuple(raw.get("expected_tags", ())),
            category=raw.get("category", "baseline"),
            should_refuse=bool(raw.get("should_refuse", False)),
        ))
    if not cases:
        raise ValueError("core evaluation suite contains zero cases")
    return cases


def build_evaluation_report(app: LastLightApp, cases: list[EvaluationCase] | None = None, top_k: int = DEFAULT_EVAL_TOP_K) -> dict[str, object]:
    cases = cases if cases is not None else load_evaluation_cases()
    if not cases:
        raise ValueError("evaluation requires at least one case")
    confidence_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    case_results: list[dict[str, object]] = []
    top_1_correct = top_k_correct = 0
    reciprocal_ranks: list[float] = []
    elapsed_samples_ms: list[float] = []
    by_tag: dict[str, dict[str, object]] = {}
    by_difficulty: dict[str, dict[str, object]] = {}
    by_language: dict[str, dict[str, object]] = {}
    by_category: dict[str, dict[str, object]] = {}
    true_accept = false_accept = true_refusal = false_refusal = 0

    for case in cases:
        start = time.perf_counter()
        results = app.search(case.query, top_k=top_k)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        elapsed_samples_ms.append(elapsed_ms)
        accepted_results = [r for r in results if r.confidence in {"HIGH", "MEDIUM"}]
        accepted = bool(accepted_results)
        if case.should_refuse:
            true_refusal += int(not accepted); false_accept += int(accepted)
        else:
            true_accept += int(accepted); false_refusal += int(not accepted)
        rank = _expected_rank(accepted_results, case)
        matched_tags = _matched_tags(accepted_results, case)
        top_1_match = (not case.should_refuse and rank == 1) or (case.should_refuse and not accepted)
        top_k_match = (not case.should_refuse and set(case.target_tags) <= matched_tags) or (case.should_refuse and not accepted)
        reciprocal_rank = 1.0 / rank if rank is not None else 0.0
        reciprocal_ranks.append(reciprocal_rank)
        top_1_correct += int(top_1_match); top_k_correct += int(top_k_match)
        for tag in case.target_tags or ("expected-refusal",):
            _record_bucket(by_tag, tag, top_1_match, top_k_match, reciprocal_rank)
        _record_bucket(by_difficulty, case.difficulty, top_1_match, top_k_match, reciprocal_rank)
        _record_bucket(by_category, case.category, top_1_match, top_k_match, reciprocal_rank)
        _record_bucket(by_language, case.expected_language or "unspecified", top_1_match, top_k_match, reciprocal_rank)
        top = results[0] if results else None
        confidence_counts[top.confidence if top else "NONE"] += 1
        language_counts[top.document.language if top else "NONE"] += 1
        case_results.append({
            "query": case.query, "expected_tag": case.expected_tag,
            "expected_tags": list(case.target_tags), "category": case.category,
            "should_refuse": case.should_refuse, "accepted": accepted,
            "expected_language": case.expected_language, "difficulty": case.difficulty,
            "top_1_correct": top_1_match, "top_k_correct": top_k_match,
            "rank": rank, "reciprocal_rank": reciprocal_rank,
            "confidence": top.confidence if top else "NONE", "elapsed_ms": elapsed_ms,
            "result": _serialize_result(top) if top else None,
            "results": [_serialize_result(r) for r in results],
        })

    total = len(cases)
    decision = _decision_metrics(true_accept, false_accept, true_refusal, false_refusal)
    report: dict[str, object] = {
        "benchmark": {"top_k": top_k, "case_source": "packaged:lastlight.evaluation/data/eval_core.jsonl",
                      "notes": "Small deterministic core regression suite; stress/hardware benchmarks belong in lastlight-bench."},
        "total_cases": total, "correct": top_1_correct,
        "top_1_correct": top_1_correct, "top_k_correct": top_k_correct,
        "top_1_accuracy": top_1_correct / total, "top_k_accuracy": top_k_correct / total,
        "mean_reciprocal_rank": mean(reciprocal_ranks),
        "latency_ms": _latency_summary(elapsed_samples_ms),
        "confidence": {label: confidence_counts.get(label, 0) for label in ("HIGH", "MEDIUM", "LOW", "NONE")},
        "top_result_languages": dict(sorted(language_counts.items())),
        "by_expected_tag": _finalize_buckets(by_tag), "by_difficulty": _finalize_buckets(by_difficulty),
        "by_category": _finalize_buckets(by_category), "by_expected_language": _finalize_buckets(by_language),
        "decision_metrics": decision, "cases": case_results,
    }
    passed, failures = evaluation_gate(report)
    report["gate"] = {"passed": passed, "failures": list(failures), "thresholds": dict(EVAL_THRESHOLDS)}
    return report


def evaluation_gate(report: dict[str, object]) -> tuple[bool, tuple[str, ...]]:
    failures: list[str] = []
    total = int(report.get("total_cases", 0))
    if total <= 0:
        failures.append("evaluation suite contains zero cases")
        return False, tuple(failures)
    decision = report["decision_metrics"]
    checks = {
        "top_1_accuracy": float(report["top_1_accuracy"]),
        "answer_precision": float(decision["answer_precision"]),
        "refusal_recall": float(decision["refusal_recall"]),
        "answerable_recall": float(decision["answerable_recall"]),
    }
    for name, value in checks.items():
        minimum = EVAL_THRESHOLDS[name]
        if value < minimum:
            failures.append(f"{name}={value:.3f} below required {minimum:.3f}")
    return not failures, tuple(failures)


def format_evaluation_report(report: dict[str, object]) -> str:
    confidence = report["confidence"]; decision = report["decision_metrics"]; gate = report.get("gate", {})
    lines = ["LastLight core evaluation", f"Total cases: {report['total_cases']}",
             f"Top-1 accuracy: {report['top_1_accuracy']:.2%}",
             f"Top-{report['benchmark']['top_k']} accuracy: {report['top_k_accuracy']:.2%}",
             f"MRR: {report['mean_reciprocal_rank']:.3f}",
             f"Mean search latency: {report['latency_ms']['mean']:.3f} ms",
             f"Answer precision: {decision['answer_precision']:.2%}",
             f"Refusal recall: {decision['refusal_recall']:.2%}",
             f"Answerable recall: {decision['answerable_recall']:.2%}",
             f"Regression gate: {'PASS' if gate.get('passed') else 'FAIL'}", "Confidence statistics:"]
    lines.extend(f"- {label}: {confidence.get(label, 0)}" for label in ("HIGH", "MEDIUM", "LOW", "NONE"))
    for failure in gate.get("failures", []): lines.append(f"- GATE: {failure}")
    return "\n".join(lines)


def run_evaluation(app: LastLightApp, cases: list[EvaluationCase] | None = None) -> str:
    return format_evaluation_report(build_evaluation_report(app, cases))


def write_evaluation_report(report: dict[str, object], output_path: Path | str = DEFAULT_EVAL_OUTPUT) -> Path:
    output = Path(output_path); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _expected_rank(results: list[SearchResult], case: EvaluationCase) -> int | None:
    for index, result in enumerate(results, start=1):
        if set(case.target_tags).intersection(result.document.tags) and (case.expected_language is None or result.document.language == case.expected_language): return index
    return None


def _matched_tags(results: list[SearchResult], case: EvaluationCase) -> set[str]:
    matched: set[str] = set()
    for result in results:
        if case.expected_language is None or result.document.language == case.expected_language:
            matched.update(set(case.target_tags).intersection(result.document.tags))
    return matched


def _decision_metrics(true_accept: int, false_accept: int, true_refusal: int, false_refusal: int) -> dict[str, int | float]:
    answer_total = true_accept + false_accept; refusal_total = true_refusal + false_accept
    return {"true_accept": true_accept, "false_accept": false_accept, "true_refusal": true_refusal, "false_refusal": false_refusal,
            "answer_precision": true_accept / answer_total if answer_total else 0.0,
            "refusal_recall": true_refusal / refusal_total if refusal_total else 0.0,
            "answerable_recall": true_accept / (true_accept + false_refusal) if true_accept + false_refusal else 0.0}


def _serialize_result(result: SearchResult) -> dict[str, object]:
    return {"title": result.document.title, "path": result.document.path, "language": result.document.language,
            "tags": list(result.document.tags), "score": result.score, "confidence": result.confidence,
            "matched_terms": list(result.matched_terms), "passage": result.passage}


def _record_bucket(buckets: dict[str, dict[str, object]], key: str, top_1_match: bool, top_k_match: bool, reciprocal_rank: float) -> None:
    bucket = buckets.setdefault(key, {"total": 0, "top_1_correct": 0, "top_k_correct": 0, "reciprocal_rank_sum": 0.0})
    bucket["total"] = int(bucket["total"]) + 1; bucket["top_1_correct"] = int(bucket["top_1_correct"]) + int(top_1_match)
    bucket["top_k_correct"] = int(bucket["top_k_correct"]) + int(top_k_match); bucket["reciprocal_rank_sum"] = float(bucket["reciprocal_rank_sum"]) + reciprocal_rank


def _finalize_buckets(buckets: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    finalized = {}
    for key, bucket in sorted(buckets.items()):
        total = int(bucket["total"]); t1 = int(bucket["top_1_correct"]); tk = int(bucket["top_k_correct"]); rr = float(bucket["reciprocal_rank_sum"])
        finalized[key] = {"total": total, "top_1_correct": t1, "top_k_correct": tk, "top_1_accuracy": t1 / total, "top_k_accuracy": tk / total, "mean_reciprocal_rank": rr / total}
    return finalized


def _latency_summary(samples_ms: list[float]) -> dict[str, float]:
    ordered = sorted(samples_ms); p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    return {"mean": mean(samples_ms), "min": min(samples_ms), "max": max(samples_ms), "p95": ordered[p95_index]}
