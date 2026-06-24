"""Evaluation framework for deterministic retrieval."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .app import LastLightApp
from .domain import EvaluationCase
from .util import project_root


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


def run_evaluation(app: LastLightApp, cases: list[EvaluationCase] | None = None) -> str:
    cases = cases if cases is not None else load_evaluation_cases()
    failures: list[str] = []
    confidence_counts: Counter[str] = Counter()
    correct = 0

    for case in cases:
        results = app.search(case.query, top_k=1)
        if not results:
            failures.append(f"- {case.query!r}: no result")
            confidence_counts["NONE"] += 1
            continue
        top = results[0]
        confidence_counts[top.confidence] += 1
        if case.expected_tag in top.document.tags:
            correct += 1
        else:
            failures.append(
                f"- {case.query!r}: expected tag {case.expected_tag!r}, got {top.document.path}"
            )

    total = len(cases)
    accuracy = correct / total if total else 0.0
    lines = [
        "LastLight evaluation",
        f"Total cases: {total}",
        f"Top-1 accuracy: {accuracy:.2%}",
        "Confidence statistics:",
    ]
    for label in ("HIGH", "MEDIUM", "LOW", "NONE"):
        lines.append(f"- {label}: {confidence_counts.get(label, 0)}")
    lines.append("Failed cases:")
    lines.extend(failures if failures else ["- none"])
    return "\n".join(lines)

