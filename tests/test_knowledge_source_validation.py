from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import LastLight, PackError


class KnowledgeSourceValidationTests(unittest.TestCase):
    def test_missing_explicit_source_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing-pack.zip"

            with self.assertRaisesRegex(PackError, "knowledge source does not exist"):
                LastLight(missing)

    def test_empty_explicit_source_is_rejected(self) -> None:
        with self.assertRaisesRegex(PackError, "knowledge source path cannot be empty"):
            LastLight("")

    def test_existing_non_pack_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "notes.txt"
            source.write_text("not a knowledge pack", encoding="utf-8")

            with self.assertRaisesRegex(PackError, "must be a directory or .zip pack"):
                LastLight(source)


if __name__ == "__main__":
    unittest.main()
