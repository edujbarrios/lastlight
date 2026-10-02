from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.chunking import chunk_text, overlapping_chunks, sentence_windows


class ChunkingTests(unittest.TestCase):
    def test_keeps_short_paragraphs_as_chunks(self) -> None:
        chunks = chunk_text("First paragraph.\n\nSecond paragraph.", max_chars=80)

        self.assertEqual(chunks, ["First paragraph.", "Second paragraph."])

    def test_splits_long_text_without_exceeding_limit(self) -> None:
        text = "One sentence is useful. " * 20
        chunks = chunk_text(text, max_chars=90)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 90 for chunk in chunks))

    def test_overlapping_chunks_pack_short_paragraphs(self) -> None:
        text = "Alpha guidance.\n\nBeta guidance.\n\nGamma guidance.\n\nDelta guidance."

        chunks = overlapping_chunks(text, max_chars=45, overlap_chars=18)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 45 for chunk in chunks))
        self.assertTrue(any("Alpha guidance." in chunk and "Beta guidance." in chunk for chunk in chunks))

    def test_overlapping_chunks_carry_complete_trailing_context(self) -> None:
        text = (
            "First context.\n\n"
            "Shared context.\n\n"
            "Third instruction.\n\n"
            "Fourth instruction."
        )

        chunks = overlapping_chunks(text, max_chars=34, overlap_chars=18)

        containing_shared = [chunk for chunk in chunks if "Shared context." in chunk]
        self.assertGreaterEqual(len(containing_shared), 2)
        self.assertTrue(all(len(chunk) <= 34 for chunk in chunks))

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

    def test_sentence_windows_handle_bulleted_steps(self) -> None:
        text = "- Check breathing\n- Apply pressure\n- Call for help"

        windows = sentence_windows(text, max_chars=80)

        self.assertIn("Check breathing Apply pressure Call for help", windows)

    def test_rejects_non_positive_limits(self) -> None:
        for max_chars in (0, -1):
            with self.subTest(max_chars=max_chars):
                with self.assertRaisesRegex(ValueError, "max_chars"):
                    chunk_text("Safety guidance.", max_chars=max_chars)
                with self.assertRaisesRegex(ValueError, "max_chars"):
                    sentence_windows("Safety guidance.", max_chars=max_chars)
                with self.assertRaisesRegex(ValueError, "max_chars"):
                    overlapping_chunks("Safety guidance.", max_chars=max_chars)

    def test_overlapping_chunks_validate_overlap(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlap_chars"):
            overlapping_chunks("Safety guidance.", max_chars=100, overlap_chars=-1)
        with self.assertRaisesRegex(ValueError, "overlap_chars"):
            overlapping_chunks("Safety guidance.", max_chars=100, overlap_chars=100)


if __name__ == "__main__":
    unittest.main()
