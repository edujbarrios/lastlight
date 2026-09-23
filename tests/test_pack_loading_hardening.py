from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import helpers  # noqa: F401
from lastlight.errors import PackError
from lastlight.knowledge.provenance import pack_fingerprint
from lastlight.repository import MarkdownKnowledgeRepository


MANIFEST = {
    "format_version": 1,
    "name": "Canonical test pack",
    "version": "1.0.0",
    "languages": ["en"],
    "license": "CC0-1.0",
    "source": "local:test",
    "publisher": "tests",
}
DOCUMENT = """---
title: Water
language: en
tags:
  - water
---

Boil water before drinking it.
"""


class PackLoadingHardeningTests(unittest.TestCase):
    def test_directory_and_zip_use_same_logical_document_path_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            (root / "en" / "water").mkdir(parents=True)
            (root / "lastlight-pack.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
            (root / "en" / "water" / "guide.md").write_text(DOCUMENT, encoding="utf-8")

            zip_path = Path(tmp) / "renamed-artifact.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr("lastlight-pack.json", json.dumps(MANIFEST))
                archive.writestr("en/water/guide.md", DOCUMENT)

            directory_repo = MarkdownKnowledgeRepository(root)
            zip_repo = MarkdownKnowledgeRepository(zip_path)
            directory_docs = directory_repo.list_documents()
            zip_docs = zip_repo.list_documents()

            self.assertEqual(directory_docs[0].path, "en/water/guide.md")
            self.assertEqual(zip_docs[0].path, "en/water/guide.md")
            self.assertEqual(
                pack_fingerprint(directory_docs, MANIFEST),
                pack_fingerprint(zip_docs, MANIFEST),
            )

    def test_rejects_zip_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "unsafe.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr("lastlight-pack.json", json.dumps(MANIFEST))
                archive.writestr("../escape.md", DOCUMENT)

            with self.assertRaises(PackError):
                MarkdownKnowledgeRepository(zip_path).list_documents()

    def test_rejects_duplicate_normalized_zip_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "duplicate.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
                archive.writestr("lastlight-pack.json", json.dumps(MANIFEST))
                archive.writestr("en/water/guide.md", DOCUMENT)
                archive.writestr("EN/WATER/GUIDE.MD", DOCUMENT)

            with self.assertRaises(PackError):
                MarkdownKnowledgeRepository(zip_path).list_documents()


if __name__ == "__main__":
    unittest.main()
