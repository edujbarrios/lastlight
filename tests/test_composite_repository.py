from __future__ import annotations

import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.composite_repository import CompositeKnowledgeRepository
from lastlight.repository import MarkdownKnowledgeRepository


class CompositeKnowledgeRepositoryTests(unittest.TestCase):
    def _pack(self, root: Path, name: str, body: str) -> MarkdownKnowledgeRepository:
        root.mkdir()
        (root / "lastlight-pack.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "version": "1.0.0",
                    "languages": ["en"],
                    "license": "CC-BY-4.0",
                    "source": f"https://example.org/{name}",
                }
            ),
            encoding="utf-8",
        )
        en = root / "en"
        en.mkdir()
        (en / "guide.md").write_text(
            "---\ntitle: Guide\nlanguage: en\ntags:\n  - guide\n---\n" + body,
            encoding="utf-8",
        )
        return MarkdownKnowledgeRepository(root)

    def test_combines_documents_and_preserves_pack_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            water = self._pack(base / "water", "water-pack", "Purify water.")
            first_aid = self._pack(base / "first-aid", "first-aid-pack", "Stop bleeding.")
            repository = CompositeKnowledgeRepository([water, first_aid])

            documents = repository.list_documents()

        self.assertEqual(len(documents), 2)
        self.assertEqual({doc.pack_name for doc in documents}, {"water-pack", "first-aid-pack"})
        self.assertEqual({doc.pack_version for doc in documents}, {"1.0.0"})
        self.assertEqual(repository.pack_count, 2)

    def test_reuses_composed_documents_while_child_snapshots_are_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            water = self._pack(base / "water", "water-pack", "Purify water.")
            first_aid = self._pack(base / "first-aid", "first-aid-pack", "Stop bleeding.")
            repository = CompositeKnowledgeRepository([water, first_aid])

            with patch(
                "lastlight.knowledge.composite_repository.replace",
                wraps=dataclasses.replace,
            ) as replace_document:
                first = repository.list_documents()
                second = repository.list_documents()

            self.assertEqual(replace_document.call_count, 2)
            self.assertEqual(first, second)
            self.assertIsNot(first, second)
            self.assertIs(first[0], second[0])

    def test_rebuilds_composed_documents_when_child_snapshot_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            water_root = base / "water"
            water = self._pack(water_root, "water-pack", "Purify water.")
            first_aid = self._pack(base / "first-aid", "first-aid-pack", "Stop bleeding.")
            repository = CompositeKnowledgeRepository([water, first_aid])

            first = repository.list_documents()
            (water_root / "en" / "guide.md").write_text(
                "---\ntitle: Guide\nlanguage: en\ntags:\n  - guide\n---\n"
                "Purify and safely store emergency water.",
                encoding="utf-8",
            )
            second = repository.list_documents()

            self.assertIsNot(first[0], second[0])
            water_documents = [doc for doc in second if doc.pack_name == "water-pack"]
            self.assertIn("safely store emergency water", water_documents[0].body)

    def test_describe_packs_keeps_each_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            one = self._pack(base / "one", "one-pack", "One")
            two = self._pack(base / "two", "two-pack", "Two")
            repository = CompositeKnowledgeRepository((one, two))

            packs = repository.describe_packs()

        self.assertEqual([pack.name for pack in packs], ["one-pack", "two-pack"])

    def test_requires_at_least_one_repository(self) -> None:
        with self.assertRaises(ValueError):
            CompositeKnowledgeRepository([])


if __name__ == "__main__":
    unittest.main()
