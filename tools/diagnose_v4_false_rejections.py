"""Separate deterministic audit of Top-1-supported but refused queries.

Runs outside the external benchmark's timed measurement. Results are for
diagnosis, never benchmark-specific threshold fitting.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lastlight import LastLight
from lastlight_bench.schema import load_cases

FIELDS = (
    "strategy", "profile", "reason", "refusal_code", "explanation",
    "score", "runner_up_score", "score_margin", "score_ratio",
    "query_coverage", "weighted_query_coverage", "passage_coverage",
    "discriminative_matches", "relevance_strength", "calibrated_score",
    "verification_agreement", "evidence_sufficient", "section",
)
RETRIEVAL = (
    "strategy", "requested_strategy", "mode", "risk", "decision_profile",
    "effective_top_k", "verification_backend", "verification_agreement",
    "verification_candidates",
)


def inspect(corpus: Path, labels: Path, strategy: str, mode: str) -> dict[str, Any]:
    engine = LastLight(corpus, strategy=strategy, mode=mode)
    totals = {"answerable": 0, "top1_correct": 0, "false_rejections": 0}
    rows: list[dict[str, Any]] = []
    for case in load_cases(labels):
        if not case.answerable:
            continue
        totals["answerable"] += 1
        result = engine.query(case.query, top_k=3)
        if (not result.sources or
                result.sources[0].path.replace("\\", "/") != case.expected_path):
            continue
        totals["top1_correct"] += 1
        if result.accepted:
            continue
        totals["false_rejections"] += 1
        rows.append({
            "id": case.id, "language": case.language,
            "difficulty": case.difficulty,
            "category": case.category, "tags": list(case.tags),
            "refusal_reason": result.refusal_reason,
            "decision": {
                field: getattr(result.decision, field, None) for field in FIELDS
            },
            "retrieval": {
                field: getattr(result.retrieval, field, None) for field in RETRIEVAL
            },
            "sources": [{
                "path": source.path, "section": getattr(source, "section", None),
                "score": source.score,
                "backend_scores": list(getattr(source, "backend_scores", ())),
            } for source in result.sources],
        })
    return {
        "configuration": {"strategy": strategy, "mode": mode},
        "counts": totals,
        "false_rejections": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Top-1 false refusals")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--strategy", choices=("lexical", "bm25", "hybrid", "adaptive"),
                        required=True)
    parser.add_argument("--mode", choices=("survival", "balanced", "accuracy"),
                        default="balanced")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = inspect(args.corpus, args.cases, args.strategy, args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
