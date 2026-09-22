"""Run the same offline software-health checks used by CI.

This script intentionally uses only the Python standard library so it can be run on
constrained or freshly cloned environments without installing tooling first.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
PACK = ROOT / "examplepack" / "lastlight-example-en.zip"
PACK_SOURCE = ROOT / "examplepack" / "source"
MAIN = ROOT / "src" / "main.py"

WATER_QUERY = (
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)
REFUSAL_QUERY = "How do I repair a diesel engine that will not start?"


def run_check(
    name: str,
    args: list[str],
    *,
    expected_code: int = 0,
    contains: tuple[str, ...] = (),
) -> str:
    print(f"[check] {name}", flush=True)
    completed = subprocess.run(
        [PYTHON, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout
    if completed.returncode != expected_code:
        raise SystemExit(
            f"{name} failed: expected exit {expected_code}, got {completed.returncode}\n{output}"
        )
    for expected in contains:
        if expected not in output:
            raise SystemExit(f"{name} missing expected output {expected!r}\n{output}")
    print(f"[pass]  {name}")
    return output


def main() -> int:
    run_check(
        "compile source and tests",
        ["-m", "compileall", "-q", "src", "tests", "tools"],
    )
    run_check(
        "unit and integration suite",
        ["-m", "unittest", "discover", "-s", "tests"],
    )
    run_check(
        "CLI entrypoint",
        [str(MAIN), "--help"],
        contains=("Offline intelligence under extreme constraints.",),
    )
    run_check(
        "validate example ZIP",
        [str(MAIN), "--knowledge", str(PACK), "--validate-pack"],
        contains=("Pack validation: PASS",),
    )
    run_check(
        "validate example directory",
        [str(MAIN), "--knowledge", str(PACK_SOURCE), "--validate-pack"],
        contains=("Pack validation: PASS",),
    )
    run_check(
        "lexical retrieval",
        [
            str(MAIN),
            "--knowledge",
            str(PACK),
            "--strategy",
            "lexical",
            "--format",
            "sources",
            WATER_QUERY,
        ],
        contains=("[HIGH] Safe water during an emergency",),
    )
    run_check(
        "BM25 retrieval",
        [
            str(MAIN),
            "--knowledge",
            str(PACK),
            "--strategy",
            "bm25",
            "--format",
            "sources",
            WATER_QUERY,
        ],
        contains=("[HIGH] Safe water during an emergency",),
    )

    plan_output = run_check(
        "adaptive survival plan",
        [
            str(MAIN),
            "--knowledge",
            str(PACK),
            "--strategy",
            "adaptive",
            "--mode",
            "survival",
            "--plan",
            WATER_QUERY,
        ],
    )
    plan = json.loads(plan_output)
    if plan.get("strategy") != "lexical" or plan.get("effective_top_k") != 2:
        raise SystemExit(f"unexpected adaptive survival plan: {plan}")

    constrained_output = run_check(
        "adaptive explicit low-memory policy",
        [
            str(MAIN),
            "--knowledge",
            str(PACK),
            "--strategy",
            "adaptive",
            "--mode",
            "balanced",
            "--memory-budget-mb",
            "64",
            "--plan",
            WATER_QUERY,
        ],
    )
    constrained = json.loads(constrained_output)
    if constrained.get("strategy") != "lexical":
        raise SystemExit(f"unexpected constrained adaptive plan: {constrained}")

    run_check(
        "multi-pack composition",
        [
            str(MAIN),
            "--knowledge",
            str(PACK),
            "--knowledge",
            str(PACK_SOURCE),
            "--format",
            "sources",
            WATER_QUERY,
        ],
        contains=("Safe water during an emergency",),
    )
    run_check(
        "confidence refusal exit contract",
        [
            str(MAIN),
            "--knowledge",
            str(PACK),
            "--fail-on-refusal",
            REFUSAL_QUERY,
        ],
        expected_code=2,
        contains=(
            "I do not have enough confidence to answer this question from the current knowledge base.",
        ),
    )

    print("\nAll LastLight software health checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
