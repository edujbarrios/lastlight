from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import helpers  # noqa: F401
from lastlight.repository import MarkdownKnowledgeRepository


class RepositoryPackCacheTests(unittest.TestCase):
    def test_reuses_directory_manifest_metadata_until_manifest_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "lastlight-pack.json"
            manifest.write_text(
                '{"name":"Field Pack","version":"1","languages":["en"]}',
                encoding="utf-8",
            )
            repository = MarkdownKnowledgeRepository(root)

            with patch(
                "lastlight.knowledge.repository.json.loads",
                wraps=json.loads,
            ) as loads:
                first = repository.describe_pack()
                second = repository.describe_pack()
                manifest.write_text(
                    '{"name":"Field Pack","version":"2.0","languages":["en"]}',
                    encoding="utf-8",
                )
                third = repository.describe_pack()

            self.assertEqual(loads.call_count, 2)
            self.assertIs(first, second)
            self.assertEqual(first.version, "1")
            self.assertEqual(third.version, "2.0")

    def test_reuses_zip_pack_metadata_until_archive_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack_path = Path(tmp) / "field.zip"
            with ZipFile(pack_path, "w") as archive:
                archive.writestr(
                    "lastlight-pack.json",
                    '{"name":"Field Pack","version":"1","languages":["en"]}',
                )
                archive.writestr("en/guide.md", "Guidance")
            repository = MarkdownKnowledgeRepository(pack_path)

            with patch.object(
                repository,
                "_describe_zip_pack",
                wraps=repository._describe_zip_pack,
            ) as describe:
                first = repository.describe_pack()
                second = repository.describe_pack()
                with ZipFile(pack_path, "w") as archive:
                    archive.writestr(
                        "lastlight-pack.json",
                        '{"name":"Field Pack","version":"2.0","languages":["en"]}',
                    )
                    archive.writestr("en/guide.md", "Updated guidance")
                third = repository.describe_pack()

            self.assertEqual(describe.call_count, 2)
            self.assertIs(first, second)
            self.assertEqual(first.version, "1")
            self.assertEqual(third.version, "2.0")


if __name__ == "__main__":
    unittest.main()
