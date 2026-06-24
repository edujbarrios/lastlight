from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import helpers  # noqa: F401
from lastlight.repository import MarkdownKnowledgeRepository


class RepositoryTests(unittest.TestCase):
    def test_discovers_markdown_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "water"
            nested.mkdir()
            (nested / "a.md").write_text("Alpha", encoding="utf-8")
            (root / "b.txt").write_text("Ignored", encoding="utf-8")

            docs = MarkdownKnowledgeRepository(root).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "A")

    def test_loads_markdown_from_zip_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack.zip"
            with ZipFile(pack, "w") as archive:
                archive.writestr(
                    "water/purification.md",
                    "---\ntitle: Packed Water\ntags:\n  - water\n---\n\nBoil water.",
                )
                archive.writestr("notes.txt", "ignored")

            docs = MarkdownKnowledgeRepository(pack).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "Packed Water")
        self.assertEqual(docs[0].path, "pack.zip:water/purification.md")


if __name__ == "__main__":
    unittest.main()
