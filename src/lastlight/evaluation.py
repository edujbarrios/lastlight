"""Evaluation framework for deterministic retrieval."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .app import LastLightApp
from .domain import EvaluationCase
from .util import project_root

DEFAULT_EVAL_OUTPUT = project_root() / "eval" / "results.json"


def load_evaluation_cases(path: Path | None = None) -> list[EvaluationCase]:
    path = path or project_root() / "data" / "eval.jsonl"
    cases: list[EvaluationCase] = []
    if not path.exists():
        return cases
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(EvaluationCase(query=raw["query"], expected_tag=raw["expected_tag"]))
    return cases


def build_evaluation_report(
    app: LastLightApp, cases: list[EvaluationCase] | None = None
) -> dict[str, object]:
    cases = cases if cases is not None else load_evaluation_cases()
    confidence_counts: Counter[str] = Counter()
    case_results: list[dict[str, object]] = []
    correct = 0

    for case in cases:
        results = app.search(case.query, top_k=1)
        if not results:
            confidence_counts["NONE"] += 1
            case_results.append(
                {
                    "query": case.query,
                    "expected_tag": case.expected_tag,
                    "correct": False,
                    "confidence": "NONE",
                    "result": None,
                }
            )
            continue
        top = results[0]
        confidence_counts[top.confidence] += 1
        is_correct = case.expected_tag in top.document.tags
        if is_correct:
            correct += 1
        case_results.append(
            {
                "query": case.query,
                "expected_tag": case.expected_tag,
                "correct": is_correct,
                "confidence": top.confidence,
                "result": {
                    "title": top.document.title,
                    "path": top.document.path,
                    "language": top.document.language,
                    "tags": list(top.document.tags),
                    "score": top.score,
                    "matched_terms": list(top.matched_terms),
                    "passage": top.passage,
                },
            }
        )

    total = len(cases)
    accuracy = correct / total if total else 0.0
    return {
        "total_cases": total,
        "correct": correct,
        "top_1_accuracy": accuracy,
        "confidence": {
            label: confidence_counts.get(label, 0)
            for label in ("HIGH", "MEDIUM", "LOW", "NONE")
        },
        "cases": case_results,
    }


def format_evaluation_report(report: dict[str, object]) -> str:
    confidence = report["confidence"]
    cases = report["cases"]
    failures: list[str] = []
    for case in cases:
        if case["correct"]:
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
