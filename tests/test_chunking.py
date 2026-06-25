from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.chunking import chunk_text, sentence_windows


class ChunkingTests(unittest.TestCase):
    def test_keeps_short_paragraphs_as_chunks(self) -> None:
        chunks = chunk_text("First paragraph.\n\nSecond paragraph.", max_chars=80)

        self.assertEqual(chunks, ["First paragraph.", "Second paragraph."])

    def test_splits_long_text_without_exceeding_limit(self) -> None:
        text = "One sentence is useful. " * 20
        chunks = chunk_text(text, max_chars=90)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 90 for chunk in chunks))

    def test_sentence_windows_include_neighboring_context(self) -> None:
        text = "First step. Important middle instruction. Final warning."

        windows = sentence_windows(text, max_chars=80)

        self.assertIn(
            "First step. Important middle instruction. Final warning.",
            windows,
        )

    def test_sentence_windows_respect_limit(self) -> None:
        text = "Alpha beta gamma. " * 20

        windows = sentence_windows(text, max_chars=60)

        self.assertTrue(all(len(window) <= 60 for window in windows))


if __name__ == "__main__":
    unittest.main()
