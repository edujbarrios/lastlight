from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.c_core import OptionalCCore
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import CBackedLexicalRetrievalStrategy


class CCoreTests(unittest.TestCase):
    def test_python_fallback_counts_matches(self) -> None:
        core = OptionalCCore()

        count = core.count_matches(["water", "battery"], ["clean", "water"])

        self.assertEqual(count, 1)

    def test_c_backed_strategy_falls_back_to_python(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Water Purification",
                path="knowledge/water/purification.md",
                body="Boil water before drinking.",
                tags=("water", "purification"),
                priority="high",
            )
        ]

        results = CBackedLexicalRetrievalStrategy().search(
            SearchQuery("purify water", 1), docs
        )

        self.assertEqual(results[0].document.title, "Water Purification")


if __name__ == "__main__":
    unittest.main()

