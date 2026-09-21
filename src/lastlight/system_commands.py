"""System-level command objects for core provenance checks."""

from __future__ import annotations

import json

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
