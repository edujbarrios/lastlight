"""Compare untouched corpus-v4 results with separately installed LastLight versions.

Uses lastlight_bench.runner.run_benchmark and write_json without altering the
benchmark's labels, corpus, or metric definitions. V3 is explicitly refused.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import venv
from typing import Any

from benchmark_v4_readiness import inspect_checkout

VERSIONS = ("0.2.2", "0.3.0")
MATRIX = (
    ("lexical", "balanced"),
    ("bm25", "balanced"),
    ("hybrid", "balanced"),
    ("adaptive", "survival"),
    ("adaptive", "balanced"),
    ("adaptive", "accuracy"),
)
RUNNER = """
import sys
from pathlib import Path
from lastlight_bench.runner import run_benchmark, write_json
corpus, cases, strategy, mode, output = sys.argv[1:]
write_json(run_benchmark(Path(corpus), Path(cases), strategy, mode, 3, 3),
           Path(output))
"""


def _run(arguments: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(arguments, check=True, cwd=cwd)


def _python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _install(version: str, root: Path, benchmark: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(root)
    python = _python(root)
    _run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
          f"lastlight=={version}"])
    # The external benchmark pins 0.2.2; do not let it change the installed version.
    _run([str(python), "-m", "pip", "install", "--no-deps",
          "--disable-pip-version-check", str(benchmark)])
    _run([str(python), "-c",
          "import importlib.metadata as m; "
          f"assert m.version('lastlight') == '{version}'; "
          "import lastlight_bench.runner"])
    return python


def _summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for version, strategy, mode in sorted({
        (run["version"], run["strategy"], run["mode"]) for run in runs
    }):
        selected = [
            run["summary"] for run in runs
            if (run["version"], run["strategy"], run["mode"])
            == (version, strategy, mode)
        ]
        metrics = {}
        for key in (
            "top1_accuracy", "mrr", "answer_precision", "answerable_recall",
            "refusal_recall", "false_accept_rate", "latency_ms_mean",
            "latency_ms_p50", "latency_ms_p95", "peak_memory_mib",
        ):
            values = [float(row[key]) for row in selected if key in row]
            if values:
                metrics[key] = {
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                }
        result[f"{version}/{strategy}/{mode}"] = metrics
    return result


def compare(
    benchmark: Path, output: Path, workspace: Path, *, repeats: int = 3,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    benchmark = benchmark.resolve()
    preflight = inspect_checkout(benchmark)
    if not preflight["ready"]:
        raise ValueError("Not the required corpus v4: " + "; ".join(preflight["errors"]))
    corpus = benchmark / Path(preflight["corpus_manifest"]).parent
    cases = benchmark / preflight["case_dataset"]
    workspace.mkdir(parents=True, exist_ok=True)
    envs = {
        version: _install(version, workspace / version, benchmark)
        for version in VERSIONS
    }
    runs: list[dict[str, Any]] = []
    for repeat in range(repeats):
        matrix = MATRIX if repeat % 2 == 0 else tuple(reversed(MATRIX))
        versions = VERSIONS if repeat % 2 == 0 else tuple(reversed(VERSIONS))
        for strategy, mode in matrix:
            for version in versions:
                if version == "0.2.2" and strategy == "hybrid":
                    continue
                filename = f"{version}-{strategy}-{mode}-{repeat + 1}.json"
                raw = output / "raw" / filename
                raw.parent.mkdir(parents=True, exist_ok=True)
                _run([
                    str(envs[version]), "-c", RUNNER, str(corpus), str(cases),
                    strategy, mode, str(raw),
                ], cwd=benchmark)
                report = json.loads(raw.read_text(encoding="utf-8"))
                runs.append({
                    "version": version, "strategy": strategy, "mode": mode,
                    "repeat": repeat + 1, "summary": report["summary"],
                })
                if repeat == 0:
                    audit = output / "audits" / filename
                    audit.parent.mkdir(parents=True, exist_ok=True)
                    _run([
                        str(envs[version]),
                        str(Path(__file__).with_name("diagnose_v4_false_rejections.py")),
                        "--corpus", str(corpus), "--cases", str(cases),
                        "--strategy", strategy, "--mode", mode,
                        "--output", str(audit),
                    ], cwd=benchmark)
    after = inspect_checkout(benchmark)
    for name in ("corpus_sha256", "case_dataset_sha256"):
        if after[name] != preflight[name]:
            raise RuntimeError(f"Benchmark source changed during comparison: {name}")
    report = {
        "identity": preflight,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
        },
        "runs": runs,
        "comparison": _summary(runs),
        "method": (
            "LastLight 0.2.2 and 0.3.0 installed in separate virtual environments; "
            "independent processes; identical unchanged corpus-v4 and labels; "
            "warmup=3; top_k=3; alternating order; repeats. Metric definitions "
            "and timed tracemalloc belong to the unmodified external benchmark."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare installed versions on corpus v4")
    parser.add_argument("--benchmark", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    report = compare(args.benchmark, args.output, args.workspace, repeats=args.repeats)
    print(json.dumps(report["comparison"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
