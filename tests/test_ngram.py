from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.ngram import NGramLanguageModel


class NGramTests(unittest.TestCase):
    def test_generates_only_trained_tokens(self) -> None:
        model = NGramLanguageModel(order=2)
        model.train("boil water before drinking water")

        generated = model.generate("boil water", max_tokens=5).split()

        self.assertTrue(generated)
        self.assertTrue(set(generated).issubset({"boil", "water", "before", "drinking"}))

    def test_rejects_invalid_order(self) -> None:
        with self.assertRaises(ValueError):
            NGramLanguageModel(order=0)


if __name__ == "__main__":
    unittest.main()

