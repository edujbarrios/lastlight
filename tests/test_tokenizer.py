from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.tokenizer import expand_query_tokens, normalize_text, tokenize


class TokenizerTests(unittest.TestCase):
    def test_normalizes_unicode_and_case(self) -> None:
        self.assertEqual(normalize_text("Purificación"), "purificacion")

    def test_removes_english_and_spanish_stopwords(self) -> None:
        tokens = tokenize("How do I purify water para la familia")
        self.assertEqual(tokens, ["purify", "water", "familia"])

    def test_expands_common_emergency_aliases(self) -> None:
        tokens = expand_query_tokens(tokenize("bateria telefono"))
        self.assertIn("battery", tokens)
        self.assertIn("phone", tokens)


if __name__ == "__main__":
    unittest.main()
