"""Run reproducible LastLight timing and energy benchmarks."""

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
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lastlight.energy import (  # noqa: E402
    EnergyMeter,
    discover_energy_meter,
    energy_delta_mwh,
)


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
    energy_mwh: float
    energy_kind: str
    energy_source: str


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
        "C lexical query",
        (
            sys.executable,
            "src/main.py",
            "--strategy",
            "c-lexical",
            "how do I purify water",
        ),
    ),
    BenchmarkCase(
        "Adaptive query",
        (
            sys.executable,
            "src/main.py",
            "--strategy",
            "adaptive",
            "how do I purify water",
        ),
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


def run_case(
    case: BenchmarkCase,
    iterations: int,
    watts: float,
    meter: EnergyMeter | None = None,
) -> BenchmarkResult:
    samples_ms: list[float] = []
    samples_mwh: list[float] = []

    for _ in range(iterations):
        before_energy = meter.sample() if meter is not None else None
        start = time.perf_counter()
        subprocess.run(
            case.command,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        duration_ms = (time.perf_counter() - start) * 1000.0
        after_energy = meter.sample() if meter is not None else None

        samples_ms.append(duration_ms)
        if before_energy is not None and after_energy is not None:
            samples_mwh.append(energy_delta_mwh(before_energy, after_energy))
        else:
            samples_mwh.append(watts * (duration_ms / 1000.0) / 3.6)

    measured = meter is not None
    return BenchmarkResult(
        name=case.name,
        command=" ".join(case.command),
        median_ms=statistics.median(samples_ms),
        min_ms=min(samples_ms),
        max_ms=max(samples_ms),
        energy_mwh=statistics.median(samples_mwh),
        energy_kind="measured" if measured else "estimated",
        energy_source=meter.name if meter is not None else f"{watts:.1f} W assumption",
    )


def render_markdown(
    results: list[BenchmarkResult],
    iterations: int,
    watts: float,
    meter: EnergyMeter | None,
) -> str:
    if meter is None:
        energy_summary = (
            f"Energy source: estimated from an assumed {watts:.1f} W active system draw"
        )
    else:
        energy_summary = f"Energy source: measured with {meter.name}"

    lines = [
        f"Benchmark iterations: {iterations}",
        energy_summary,
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()}",
        "",
        "| Operation | Median time | Min | Max | Energy | Energy source |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.name} | "
            f"{result.median_ms:.1f} ms | "
            f"{result.min_ms:.1f} ms | "
            f"{result.max_ms:.1f} ms | "
            f"{result.energy_mwh:.4f} mWh | "
            f"{result.energy_kind}: {result.energy_source} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark LastLight execution cost.")
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument(
        "--watts",
        type=float,
        default=15.0,
        help="fallback active system power draw used only for energy estimates",
    )
    parser.add_argument(
        "--energy-source",
        choices=("auto", "rapl", "counter", "estimate"),
        default="auto",
        help="use a real hardware counter when available, otherwise estimate",
    )
    parser.add_argument(
        "--energy-counter",
        metavar="PATH",
        help="cumulative hardware energy counter text file for auto/counter mode",
    )
    parser.add_argument(
        "--energy-unit",
        choices=("uj", "mj", "j", "uwh", "mwh", "wh"),
        default="mwh",
        help="unit emitted by --energy-counter",
    )
    args = parser.parse_args(argv)

    if args.iterations < 1:
        parser.error("--iterations must be at least 1")
    if args.watts <= 0:
        parser.error("--watts must be greater than 0")
    if args.energy_source == "counter" and not args.energy_counter:
        parser.error("--energy-source counter requires --energy-counter")

    try:
        meter = discover_energy_meter(
            args.energy_source,
            counter_path=args.energy_counter,
            counter_unit=args.energy_unit,
        )
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))

    results = [run_case(case, args.iterations, args.watts, meter) for case in CASES]
    print(render_markdown(results, args.iterations, args.watts, meter))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
