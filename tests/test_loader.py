from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.markdown_loader import load_markdown_document


class LoaderTests(unittest.TestCase):
    def test_loads_front_matter_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(
                "---\n"
                "title: Test Doc\n"
                "language: en\n"
                "tags:\n"
                "  - water\n"
                "  - test\n"
                "priority: high\n"
                "---\n\n"
                "Useful body.",
                encoding="utf-8",
            )

            doc = load_markdown_document(path, Path(tmp))

        self.assertEqual(doc.title, "Test Doc")
        self.assertEqual(doc.language, "en")
        self.assertEqual(doc.tags, ("water", "test"))
        self.assertEqual(doc.priority, "high")
        self.assertEqual(doc.body, "Useful body.")
        self.assertEqual(
            doc.source_sha256,
            hashlib.sha256(
                (
                    "---\n"
                    "title: Test Doc\n"
                    "language: en\n"
                    "tags:\n"
                    "  - water\n"
                    "  - test\n"
                    "priority: high\n"
                    "---\n\n"
                    "Useful body."
                ).encode("utf-8")
            ).hexdigest(),
        )

    def test_missing_metadata_is_graceful(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain_file.md"
            path.write_text("# Plain Title\n\nBody.", encoding="utf-8")
            doc = load_markdown_document(path, Path(tmp))

        self.assertEqual(doc.title, "Plain Title")
        self.assertEqual(doc.language, "unknown")
        self.assertEqual(doc.tags, ())


if __name__ == "__main__":
    unittest.main()
