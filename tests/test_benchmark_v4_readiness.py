"""Offline, independent checks for the read-only v4 identity gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "benchmark_v4_readiness.py"
SPEC = importlib.util.spec_from_file_location("benchmark_v4_readiness", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def _make(root: Path, *, docs: int = 44, cases: int = 240) -> None:
    corpus = root / "corpus" / "synthetic"
    corpus.mkdir(parents=True)
    (corpus / "lastlight-pack.json").write_text('{"name":"fixture"}', encoding="utf-8")
    for number in range(docs):
        language = "en" if number < 28 else "es"
        folder = corpus / language / "notes"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{number}.md").write_text("# Synthetic evidence", encoding="utf-8")
    dataset = root / "datasets"
    dataset.mkdir()
    (dataset / "eval.jsonl").write_text("\n".join(
        json.dumps({"id": str(number), "answerable": number < 168,
                    "language": "es" if number % 2 else "en"})
        for number in range(cases)
    ), encoding="utf-8")


def test_v4_shape_passes_and_fingerprints_are_stable(tmp_path: Path) -> None:
    _make(tmp_path)
    first = GATE.inspect_checkout(tmp_path)
    second = GATE.inspect_checkout(tmp_path)
    assert first["ready"]
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["case_dataset_sha256"] == second["case_dataset_sha256"]


def test_v3_shape_fails_without_using_labels_for_tuning(tmp_path: Path) -> None:
    _make(tmp_path, docs=32, cases=160)
    report = GATE.inspect_checkout(tmp_path)
    assert not report["ready"]
    assert "documents: expected 44, observed 32" in report["errors"]
    assert "cases: expected 240, observed 160" in report["errors"]


def test_label_change_is_detected(tmp_path: Path) -> None:
    _make(tmp_path)
    before = GATE.inspect_checkout(tmp_path)
    labels = tmp_path / "datasets" / "eval.jsonl"
    lines = labels.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[0])
    row["answerable"] = False
    lines[0] = json.dumps(row)
    labels.write_text("\n".join(lines), encoding="utf-8")
    after = GATE.inspect_checkout(tmp_path)
    assert not after["ready"]
    assert after["actual"]["answerable"] == 167
    assert before["case_dataset_sha256"] != after["case_dataset_sha256"]


def test_nonboolean_answerable_is_invalid(tmp_path: Path) -> None:
    _make(tmp_path)
    labels = tmp_path / "datasets" / "eval.jsonl"
    labels.write_text('{"answerable":"yes"}\n', encoding="utf-8")
    try:
        GATE.inspect_checkout(tmp_path)
    except ValueError as error:
        assert "boolean answerable" in str(error)
    else:
        raise AssertionError("Malformed labels should be refused")
