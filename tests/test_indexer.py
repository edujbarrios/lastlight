from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.indexer import build_index, write_index
from lastlight.repository import MarkdownKnowledgeRepository


class IndexerTests(unittest.TestCase):
    def test_builds_auditable_json_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text(
                "---\ntitle: Water Test\ntags:\n  - water\n---\n\nBoil water.",
                encoding="utf-8",
            )
            index = build_index(MarkdownKnowledgeRepository(root))

        self.assertEqual(index["index_version"], 1)
        self.assertEqual(index["document_count"], 1)
        document = index["documents"][0]  # type: ignore[index]
        self.assertEqual(document["title"], "Water Test")
        self.assertIn("water", document["terms"])
        self.assertEqual(
            document["source_sha256"],
            hashlib.sha256(
                b"---\ntitle: Water Test\ntags:\n  - water\n---\n\nBoil water."
            ).hexdigest(),
        )

    def test_index_includes_pack_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lastlight-pack.json").write_text(
                '{"name":"Core Pack","version":"1.0","languages":["en"]}',
                encoding="utf-8",
            )
            (root / "water.md").write_text(
                "---\ntitle: Water\nlanguage: en\n---\n\nBoil water.",
                encoding="utf-8",
            )

            index = build_index(MarkdownKnowledgeRepository(root))

        self.assertEqual(index["pack"]["name"], "Core Pack")
        self.assertEqual(index["pack"]["version"], "1.0")
        self.assertEqual(index["pack"]["languages"], ["en"])
        self.assertEqual(index["document_count"], 1)

    def test_writes_index_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            root.mkdir()
            (root / "doc.md").write_text("Battery saving.", encoding="utf-8")
            output = Path(tmp) / "index.json"

            write_index(MarkdownKnowledgeRepository(root), output)
            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(data["document_count"], 1)
        self.assertEqual(data["documents"][0]["title"], "Doc")


if __name__ == "__main__":
    unittest.main()
