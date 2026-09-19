"""System-level command objects for provenance and device benchmarking."""

from __future__ import annotations

import json
from pathlib import Path

from .device_benchmark import build_device_benchmark, format_device_benchmark
from .interfaces import KnowledgeRepository
from .provenance import format_provenance_report, verify_pack_provenance


class VerifyProvenanceCommand:
    def __init__(
        self,
        repository: KnowledgeRepository,
        *,
        stale_after_days: int = 365,
        as_json: bool = False,
    ) -> None:
        self.repository = repository
        self.stale_after_days = stale_after_days
        self.as_json = as_json

    def execute(self) -> int:
        report = verify_pack_provenance(
            self.repository,
            stale_after_days=self.stale_after_days,
        )
        if self.as_json:
            print(json.dumps(report.to_dict(), ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(format_provenance_report(report))
        return 0 if report.ok else 1


class DeviceBenchmarkCommand:
    def __init__(
        self,
        knowledge_dir: Path | str | None = None,
        *,
        energy_source: str = "auto",
        energy_counter: Path | str | None = None,
        energy_unit: str = "mwh",
        watts: float = 15.0,
        max_cases: int | None = None,
        as_json: bool = False,
    ) -> None:
        self.knowledge_dir = knowledge_dir
        self.energy_source = energy_source
        self.energy_counter = energy_counter
        self.energy_unit = energy_unit
        self.watts = watts
        self.max_cases = max_cases
        self.as_json = as_json

    def execute(self) -> int:
        try:
            report = build_device_benchmark(
                self.knowledge_dir,
                energy_source=self.energy_source,
                energy_counter=self.energy_counter,
                energy_unit=self.energy_unit,
                watts=self.watts,
                max_cases=self.max_cases,
            )
        except (RuntimeError, ValueError) as error:
            print(f"Benchmark failed: {error}")
            return 1

        if self.as_json:
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(format_device_benchmark(report))
        return 0
