from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import helpers  # noqa: F401
from lastlight.pack_export import export_pack


class PackExportTests(unittest.TestCase):
    def test_exports_manifest_and_markdown_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            root.mkdir()
            (root / "lastlight-pack.json").write_text('{"name":"Core"}', encoding="utf-8")
            (root / "water.md").write_text("Water", encoding="utf-8")
            (root / "notes.txt").write_text("Ignored", encoding="utf-8")
            nested = root / "medical"
            nested.mkdir()
            (nested / "bleeding.md").write_text("Bleeding", encoding="utf-8")
            output = Path(tmp) / "pack.zip"

            export_pack(root, output)

            with ZipFile(output) as archive:
                names = archive.namelist()

        self.assertEqual(
            names,
            ["lastlight-pack.json", "medical/bleeding.md", "water.md"],
        )

    def test_export_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            root.mkdir()
            (root / "b.md").write_text("Bravo", encoding="utf-8")
            (root / "a.md").write_text("Alpha", encoding="utf-8")
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"

            export_pack(root, first)
            export_pack(root, second)

            first_bytes = first.read_bytes()
            second_bytes = second.read_bytes()

        self.assertEqual(first_bytes, second_bytes)

    def test_export_requires_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "pack.zip"
            source.write_text("not a directory", encoding="utf-8")

            with self.assertRaises(ValueError):
                export_pack(source, Path(tmp) / "output.zip")


if __name__ == "__main__":
    unittest.main()
