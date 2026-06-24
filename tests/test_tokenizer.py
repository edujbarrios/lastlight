from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.tokenizer import normalize_text, tokenize


class TokenizerTests(unittest.TestCase):
    def test_normalizes_unicode_and_case(self) -> None:
        self.assertEqual(normalize_text("Purificación"), "purificacion")

    def test_removes_english_and_spanish_stopwords(self) -> None:
        tokens = tokenize("How do I purify water para la familia")
        self.assertEqual(tokens, ["purify", "water", "familia"])


if __name__ == "__main__":
    unittest.main()

