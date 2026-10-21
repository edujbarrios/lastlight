"""Reject incomplete or contradictory audit indexes instead of silently verifying."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.indexer import verify_index
from lastlight.repository import MarkdownKnowledgeRepository


class AuditIndexValidationTests(unittest.TestCase):
    def test_incomplete_records_are_rejected(self) -> None:
        bad_indexes = [
            {"index_version": 1, "document_count": 1, "documents": [{}]},
            {"index_version": 1, "document_count": 0, "documents": [{"path": "a.md"}]},
            {"index_version": 1, "document_count": 2, "documents": []},
            {"index_version": True, "document_count": 0, "documents": []},
            {"index_version": 1, "document_count": True, "documents": []},
            {"index_version": 1, "documents": []},
            {"index_version": 1, "document_count": 1, "documents": [
                {"path": "doc.md", "source_sha256": "no-hash"}
            ]},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "index.json"
            repository = MarkdownKnowledgeRepository(root)
            for malformed in bad_indexes:
                with self.subTest(index=malformed):
                    path.write_text(json.dumps(malformed), encoding="utf-8")
                    report = verify_index(repository, path)
                    self.assertFalse(report["ok"])
                    self.assertEqual(report["error"], "unsupported or malformed index")

    def test_duplicate_index_paths_cannot_be_hidden_by_dict_overwrite(self) -> None:
        digest = "0" * 64
        duplicate = {
            "index_version": 1,
            "document_count": 2,
            "documents": [
                {"path": "same.md", "source_sha256": digest},
                {"path": "same.md", "source_sha256": digest},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "index.json"
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            report = verify_index(MarkdownKnowledgeRepository(root), path)
            self.assertFalse(report["ok"])
            self.assertEqual(report["error"], "unsupported or malformed index")


if __name__ == "__main__":
    unittest.main()
