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
            (root / "lastlight-pack.json").write_text("{}", encoding="utf-8")
            (root / "b.txt").write_text("Ignored", encoding="utf-8")

            docs = MarkdownKnowledgeRepository(root).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "A")

    def test_directory_markdown_extension_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide.MD").write_text("Uppercase extension", encoding="utf-8")

            docs = MarkdownKnowledgeRepository(root).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].path, "guide.MD")

    def test_directory_ignores_hidden_metadata_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".hidden").mkdir()
            (root / "__MACOSX").mkdir()
            (root / ".hidden" / "notes.md").write_text("hidden", encoding="utf-8")
            (root / "__MACOSX" / "water.md").write_text("metadata", encoding="utf-8")
            (root / "water.md").write_text("Boil water.", encoding="utf-8")

            docs = MarkdownKnowledgeRepository(root).list_documents()

        self.assertEqual([doc.path for doc in docs], ["water.md"])

    def test_ignores_root_readme_in_directory_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Pack documentation", encoding="utf-8")
            nested = root / "es"
            nested.mkdir()
            (nested / "agua.md").write_text(
                "---\nlanguage: es\n---\n\nAgua segura.", encoding="utf-8"
            )

            docs = MarkdownKnowledgeRepository(root).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "Agua")

    def test_readme_only_directory_has_no_searchable_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Pack format specification", encoding="utf-8")

            docs = MarkdownKnowledgeRepository(root).list_documents()

        self.assertEqual(docs, [])

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
        self.assertEqual(docs[0].path, "water/purification.md")

    def test_ignores_root_readme_in_zip_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack.zip"
            with ZipFile(pack, "w") as archive:
                archive.writestr("README.md", "Pack documentation")
                archive.writestr("es/agua.md", "---\nlanguage: es\n---\n\nAgua segura.")

            docs = MarkdownKnowledgeRepository(pack).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].path, "es/agua.md")

    def test_loads_zip_pack_with_uppercase_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack.ZIP"
            with ZipFile(pack, "w") as archive:
                archive.writestr("water.md", "Boil water.")

            docs = MarkdownKnowledgeRepository(pack).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].path, "water.md")

    def test_ignores_zip_metadata_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack.zip"
            with ZipFile(pack, "w") as archive:
                archive.writestr("__MACOSX/water.md", "metadata")
                archive.writestr(".hidden/notes.md", "hidden")
                archive.writestr("water.md", "Boil water.")

            docs = MarkdownKnowledgeRepository(pack).list_documents()

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].path, "water.md")

    def test_reads_directory_pack_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lastlight-pack.json").write_text(
                "{\n"
                '  "name": "Field Water Pack",\n'
                '  "version": "1.0.0",\n'
                '  "languages": ["en", "es"],\n'
                '  "license": "CC-BY-4.0",\n'
                '  "source": "community"\n'
                "}\n",
                encoding="utf-8",
            )

            pack = MarkdownKnowledgeRepository(root).describe_pack()

        self.assertEqual(pack.name, "Field Water Pack")
        self.assertEqual(pack.version, "1.0.0")
        self.assertEqual(pack.languages, ("en", "es"))
        self.assertEqual(pack.license, "CC-BY-4.0")
        self.assertEqual(pack.source, "community")

    def test_reads_zip_pack_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack_path = Path(tmp) / "spanish.zip"
            with ZipFile(pack_path, "w") as archive:
                archive.writestr(
                    "lastlight-pack.json",
                    '{"name":"Spanish Basics","languages":["es"],"version":"0.1"}',
                )
                archive.writestr("communications/spanish.md", "Hola")

            pack = MarkdownKnowledgeRepository(pack_path).describe_pack()

        self.assertEqual(pack.name, "Spanish Basics")
        self.assertEqual(pack.languages, ("es",))
        self.assertEqual(pack.version, "0.1")

    def test_infers_pack_languages_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text(
                "---\nlanguage: en\n---\n\nAlpha",
                encoding="utf-8",
            )
            (root / "b.md").write_text(
                "---\nlanguage: es\n---\n\nBravo",
                encoding="utf-8",
            )

            pack = MarkdownKnowledgeRepository(root).describe_pack()

        self.assertEqual(pack.languages, ("en", "es"))


if __name__ == "__main__":
    unittest.main()
