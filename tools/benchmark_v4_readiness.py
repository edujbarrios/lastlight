"""Read-only identity gate for the external LastLight corpus-v4 holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

EXPECTED = {
    "documents": 44,
    "english_documents": 28,
    "spanish_documents": 16,
    "cases": 240,
    "answerable": 168,
    "refusals": 72,
}


def _digest(paths: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _git_sha(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _pick(paths: list[Path], *, count: int, manifest: bool) -> Path:
    if len(paths) == 1:
        return paths[0]
    sizes = {
        path: (sum(1 for _ in path.parent.rglob("*.md")) if manifest
               else sum(bool(line.strip()) for line in path.read_text(
                   encoding="utf-8").splitlines()))
        for path in paths
    }
    matching = [path for path, size in sizes.items() if size == count]
    if len(matching) == 1:
        return matching[0]
    raise ValueError("Cannot uniquely select external benchmark source: "
                     + ", ".join(str(path) for path in paths))


def inspect_checkout(
    checkout: Path, *, corpus: Path | None = None, cases: Path | None = None,
) -> dict[str, Any]:
    """Inspect external sources; never modify benchmark documents or labels."""
    checkout = checkout.resolve()
    if not checkout.is_dir():
        raise ValueError(f"Benchmark checkout is absent: {checkout}")
    manifest = (
        checkout / corpus / "lastlight-pack.json" if corpus is not None
        else _pick(list((checkout / "corpus").rglob("lastlight-pack.json")),
                   count=EXPECTED["documents"], manifest=True)
    )
    labels = (
        checkout / cases if cases is not None
        else _pick(list((checkout / "datasets").rglob("*.jsonl")),
                   count=EXPECTED["cases"], manifest=False)
    )
    if not manifest.is_file() or not labels.is_file():
        raise ValueError("The corpus manifest and JSONL labels must both exist")
    if not manifest.resolve().is_relative_to(checkout):
        raise ValueError("Corpus manifest is outside the external checkout")
    if not labels.resolve().is_relative_to(checkout):
        raise ValueError("Dataset is outside the external checkout")
    documents = sorted(manifest.parent.rglob("*.md"))
    rows = [json.loads(line) for line in labels.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    if any(type(row.get("answerable")) is not bool for row in rows):
        raise ValueError("Each case must supply a boolean answerable label")
    language = {"en": 0, "es": 0}
    for doc in documents:
        parts = doc.relative_to(manifest.parent).parts
        if parts and parts[0] in language:
            language[parts[0]] += 1
    actual = {
        "documents": len(documents),
        "english_documents": language["en"],
        "spanish_documents": language["es"],
        "cases": len(rows),
        "answerable": sum(row["answerable"] for row in rows),
        "refusals": sum(not row["answerable"] for row in rows),
    }
    errors = [
        f"{key}: expected {expected}, observed {actual[key]}"
        for key, expected in EXPECTED.items() if actual[key] != expected
    ]
    return {
        "ready": not errors,
        "expected": EXPECTED,
        "actual": actual,
        "errors": errors,
        "benchmark_sha": _git_sha(checkout),
        "corpus_manifest": str(manifest.relative_to(checkout)),
        "case_dataset": str(labels.relative_to(checkout)),
        "corpus_sha256": _digest([manifest, *documents], checkout),
        "case_dataset_sha256": hashlib.sha256(labels.read_bytes()).hexdigest(),
        "words_whitespace": sum(len(doc.read_text(encoding="utf-8").split())
                                for doc in documents),
        "query_languages": {
            name: sum(row.get("language") == name for row in rows)
            for name in ("en", "es")
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the external v4 holdout identity")
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = inspect_checkout(args.checkout, corpus=args.corpus, cases=args.cases)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        report = {"ready": False, "expected": EXPECTED, "errors": [str(exc)]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
