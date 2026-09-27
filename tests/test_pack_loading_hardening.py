from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

import helpers  # noqa: F401
import lastlight.knowledge.repository as repository_module
from lastlight.errors import PackError
from lastlight.knowledge.provenance import pack_fingerprint
from lastlight.knowledge.repository import MAX_DOCUMENT_BYTES, MAX_MANIFEST_BYTES
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

    def test_rejects_directory_manifest_symlink_outside_pack_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            outside_manifest = Path(tmp) / "outside.json"
            outside_manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")
            manifest = root / "lastlight-pack.json"
            try:
                manifest.symlink_to(outside_manifest)
            except OSError as error:
                self.skipTest(f"symlinks are unavailable: {error}")

            with self.assertRaisesRegex(PackError, "manifest escapes pack root"):
                MarkdownKnowledgeRepository(root).describe_pack()

    def test_rejects_oversized_directory_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            (root / "lastlight-pack.json").write_text(
                " " * (MAX_MANIFEST_BYTES + 1),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PackError, "manifest exceeds maximum allowed size"):
                MarkdownKnowledgeRepository(root).describe_pack()

    def test_rejects_oversized_directory_document_before_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            (root / "oversized.md").write_text(
                "x" * (MAX_DOCUMENT_BYTES + 1),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(PackError, "document exceeds maximum size"):
                MarkdownKnowledgeRepository(root).list_documents()

    def test_rejects_directory_document_count_over_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            (root / "one.md").write_text(DOCUMENT, encoding="utf-8")
            (root / "two.md").write_text(DOCUMENT, encoding="utf-8")

            with patch.object(repository_module, "MAX_PACK_DOCUMENTS", 1):
                with self.assertRaisesRegex(PackError, "more than 1 Markdown documents"):
                    MarkdownKnowledgeRepository(root).list_documents()

    def test_rejects_directory_total_markdown_size_over_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pack"
            root.mkdir()
            (root / "one.md").write_text(DOCUMENT, encoding="utf-8")
            (root / "two.md").write_text(DOCUMENT, encoding="utf-8")
            one_size = (root / "one.md").stat().st_size

            with patch.object(repository_module, "MAX_TOTAL_DOCUMENT_BYTES", one_size + 1):
                with self.assertRaisesRegex(PackError, "maximum total size"):
                    MarkdownKnowledgeRepository(root).list_documents()

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
