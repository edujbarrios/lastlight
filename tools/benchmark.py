"""Run small reproducible LastLight timing and energy estimates."""

from __future__ import annotations

import argparse
import platform
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    command: str
    median_ms: float
    min_ms: float
    max_ms: float
    estimated_mwh: float


CASES = (
    BenchmarkCase(
        "Lexical query",
        (sys.executable, "src/main.py", "how do I purify water"),
    ),
    BenchmarkCase(
        "BM25 query",
        (sys.executable, "src/main.py", "--strategy", "bm25", "how do I purify water"),
    ),
    BenchmarkCase(
        "Lexical evaluation",
        (sys.executable, "src/main.py", "--eval"),
    ),
    BenchmarkCase(
        "BM25 evaluation",
        (sys.executable, "src/main.py", "--strategy", "bm25", "--eval"),
    ),
    BenchmarkCase(
        "Unit tests",
        (sys.executable, "-m", "unittest", "discover", "-s", "tests"),
    ),
)


def run_case(case: BenchmarkCase, iterations: int, watts: float) -> BenchmarkResult:
    samples_ms: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(
            case.command,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        samples_ms.append((time.perf_counter() - start) * 1000.0)

    median_ms = statistics.median(samples_ms)
    return BenchmarkResult(
        name=case.name,
        command=" ".join(case.command),
        median_ms=median_ms,
        min_ms=min(samples_ms),
        max_ms=max(samples_ms),
        estimated_mwh=watts * (median_ms / 1000.0) / 3.6,
    )


def render_markdown(results: list[BenchmarkResult], iterations: int, watts: float) -> str:
    lines = [
        f"Benchmark iterations: {iterations}",
        f"Assumed active system power: {watts:.1f} W",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()}",
        "",
        "| Operation | Median time | Min | Max | Estimated energy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.name} | "
            f"{result.median_ms:.1f} ms | "
            f"{result.min_ms:.1f} ms | "
            f"{result.max_ms:.1f} ms | "
            f"{result.estimated_mwh:.4f} mWh |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark LastLight execution cost.")
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument(
        "--watts",
        type=float,
        default=15.0,
        help="assumed active system power draw used for mWh estimates",
    )
    args = parser.parse_args(argv)

    if args.iterations < 1:
        parser.error("--iterations must be at least 1")
    if args.watts <= 0:
        parser.error("--watts must be greater than 0")

    results = [run_case(case, args.iterations, args.watts) for case in CASES]
    print(render_markdown(results, args.iterations, args.watts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

