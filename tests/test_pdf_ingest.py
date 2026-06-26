from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.pdf_ingest import (
    PdfDocument,
    PdfPage,
    document_to_markdown,
    extract_important_points,
    infer_title,
    text_to_markdown,
)


class PdfIngestTests(unittest.TestCase):
    def test_extracts_actionable_points(self) -> None:
        text = (
            "Background information only. "
            "Do not run a generator indoors because carbon monoxide can kill. "
            "Use clean water for wound care when possible."
        )

        points = extract_important_points(text, limit=2)

        self.assertIn(
            "Do not run a generator indoors because carbon monoxide can kill.",
            points,
        )
        self.assertIn("Use clean water for wound care when possible.", points)

    def test_converts_pages_to_markdown(self) -> None:
        pages = (
            PdfPage(1, "Emergency Water\nBoil water before drinking."),
            PdfPage(2, "Do not drink fuel-smelling water."),
        )

        markdown = text_to_markdown(pages)

        self.assertIn("### Page 1", markdown)
        self.assertIn("### Emergency Water", markdown)
        self.assertIn("### Page 2", markdown)

    def test_document_to_markdown_includes_summary_and_source_metadata(self) -> None:
        document = PdfDocument(
            path=Path("guide.pdf"),
            pages=(PdfPage(1, "Emergency Guide\nDo not run a generator indoors."),),
            source_sha256="abc123",
        )

        markdown = document_to_markdown(
            document,
            language="en",
            tags=("generator", "pdf"),
            priority="high",
        )

        self.assertIn("title: Emergency Guide", markdown)
        self.assertIn("language: en", markdown)
        self.assertIn("  - generator", markdown)
        self.assertIn("source_file: guide.pdf", markdown)
        self.assertIn("source_sha256: abc123", markdown)
        self.assertIn("## Important Points", markdown)
        self.assertIn("- Do not run a generator indoors.", markdown)

    def test_infers_title_from_first_text_line(self) -> None:
        document = PdfDocument(
            path=Path("fallback-name.pdf"),
            pages=(PdfPage(1, "My Field Guide\nBody."),),
            source_sha256="abc123",
        )

        self.assertEqual(infer_title(document), "My Field Guide")


if __name__ == "__main__":
    unittest.main()
