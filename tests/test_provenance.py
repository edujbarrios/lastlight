from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import helpers  # noqa: F401
from lastlight.provenance import verify_pack_provenance
from lastlight.repository import MarkdownKnowledgeRepository


class PackProvenanceTests(unittest.TestCase):
    def _pack(self, root: Path, manifest: dict[str, object]) -> MarkdownKnowledgeRepository:
        (root / "lastlight-pack.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        knowledge = root / "en"
        knowledge.mkdir()
        (knowledge / "water.md").write_text(
            "---\ntitle: Water\nlanguage: en\ntags:\n  - water\n---\nBoil water.",
            encoding="utf-8",
        )
        return MarkdownKnowledgeRepository(root)

    def test_reports_publisher_age_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = self._pack(
                Path(tmp),
                {
                    "name": "field-guide",
                    "version": "1.2.0",
                    "languages": ["en"],
                    "license": "CC-BY-4.0",
                    "source": "https://example.org/guide",
                    "publisher": "Example Relief",
                    "published_at": "2026-09-01",
                    "expires_at": "2027-09-01",
                    "provenance": [{"source": "https://example.org/guide"}],
                },
            )
            report = verify_pack_provenance(
                repository, today=date(2026, 9, 19), stale_after_days=365
            )

        self.assertTrue(report.ok)
        self.assertEqual(report.publisher, "Example Relief")
        self.assertEqual(report.age_days, 18)
        self.assertEqual(len(report.fingerprint_sha256), 64)

    def test_expired_pack_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = self._pack(
                Path(tmp),
                {
                    "name": "old-pack",
                    "version": "1.0.0",
                    "languages": ["en"],
                    "license": "CC-BY-4.0",
                    "source": "local",
                    "publisher": "Example",
                    "published_at": "2024-01-01",
                    "expires_at": "2025-01-01",
                    "provenance": [{"source": "local"}],
                },
            )
            report = verify_pack_provenance(repository, today=date(2026, 9, 19))

        self.assertFalse(report.ok)
        self.assertTrue(report.expired)
        self.assertTrue(any("expired" in error for error in report.errors))

    def test_stale_pack_warns_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = self._pack(
                Path(tmp),
                {
                    "name": "old-pack",
                    "version": "1.0.0",
                    "languages": ["en"],
                    "license": "CC-BY-4.0",
                    "source": "local",
                    "publisher": "Example",
                    "published_at": "2024-01-01",
                    "provenance": [{"source": "local"}],
                },
            )
            report = verify_pack_provenance(
                repository, today=date(2026, 9, 19), stale_after_days=180
            )

        self.assertTrue(report.ok)
        self.assertTrue(any("freshness threshold" in warning for warning in report.warnings))

    def test_bad_declared_fingerprint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = self._pack(
                Path(tmp),
                {
                    "name": "tampered",
                    "version": "1.0.0",
                    "languages": ["en"],
                    "license": "CC-BY-4.0",
                    "source": "local",
                    "publisher": "Example",
                    "published_at": "2026-09-01",
                    "fingerprint_sha256": "0" * 64,
                },
            )
            report = verify_pack_provenance(repository, today=date(2026, 9, 19))

        self.assertFalse(report.ok)
        self.assertTrue(any("fingerprint" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()
