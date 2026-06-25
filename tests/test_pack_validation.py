from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.pack_validation import format_validation_report, validate_pack
from lastlight.repository import MarkdownKnowledgeRepository


class PackValidationTests(unittest.TestCase):
    def test_valid_pack_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lastlight-pack.json").write_text(
                '{"name":"Core","version":"1.0","languages":["en"],'
                '"license":"MPL-2.0","source":"local"}',
                encoding="utf-8",
            )
            (root / "water.md").write_text(
                "---\ntitle: Water\nlanguage: en\ntags:\n  - water\n---\n\nBoil.",
                encoding="utf-8",
            )

            report = validate_pack(MarkdownKnowledgeRepository(root))

        self.assertTrue(report.ok)
        self.assertEqual(report.errors, ())

    def test_missing_manifest_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "water.md").write_text(
                "---\ntitle: Water\nlanguage: en\n---\n\nBoil.",
                encoding="utf-8",
            )

            report = validate_pack(MarkdownKnowledgeRepository(root))

        self.assertFalse(report.ok)
        self.assertIn("missing lastlight-pack.json manifest", report.errors)

    def test_language_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lastlight-pack.json").write_text(
                '{"name":"Core","version":"1.0","languages":["es"],'
                '"license":"MPL-2.0","source":"local"}',
                encoding="utf-8",
            )
            (root / "water.md").write_text(
                "---\ntitle: Water\nlanguage: en\n---\n\nBoil.",
                encoding="utf-8",
            )

            report = validate_pack(MarkdownKnowledgeRepository(root))

        self.assertFalse(report.ok)
        self.assertIn("manifest languages missing document language: en", report.errors)

    def test_warns_when_document_is_outside_language_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lastlight-pack.json").write_text(
                '{"name":"Core","version":"1.0","languages":["en"],'
                '"license":"MPL-2.0","source":"local"}',
                encoding="utf-8",
            )
            (root / "water.md").write_text(
                "---\ntitle: Water\nlanguage: en\ntags:\n  - water\n---\n\nBoil.",
                encoding="utf-8",
            )

            report = validate_pack(MarkdownKnowledgeRepository(root))

        self.assertTrue(report.ok)
        self.assertIn(
            "1 document(s) are outside their language section",
            report.warnings,
        )

    def test_accepts_document_inside_language_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            en = root / "en"
            en.mkdir()
            (root / "lastlight-pack.json").write_text(
                '{"name":"Core","version":"1.0","languages":["en"],'
                '"license":"MPL-2.0","source":"local"}',
                encoding="utf-8",
            )
            (en / "water.md").write_text(
                "---\ntitle: Water\nlanguage: en\ntags:\n  - water\n---\n\nBoil.",
                encoding="utf-8",
            )

            report = validate_pack(MarkdownKnowledgeRepository(root))

        self.assertNotIn(
            "1 document(s) are outside their language section",
            report.warnings,
        )

    def test_format_validation_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = validate_pack(MarkdownKnowledgeRepository(root))

        output = format_validation_report(report)

        self.assertIn("Pack validation: FAIL", output)
        self.assertIn("ERROR: pack contains no Markdown documents", output)


if __name__ == "__main__":
    unittest.main()
