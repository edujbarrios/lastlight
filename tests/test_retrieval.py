from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import BM25RetrievalStrategy, LexicalRetrievalStrategy


class RetrievalTests(unittest.TestCase):
    def test_ranks_relevant_document_first(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Water Purification",
                path="knowledge/water/purification.md",
                body="Boil contaminated water at a rolling boil.",
                tags=("water", "purification"),
                priority="high",
            ),
            KnowledgeDocument(
                title="Compass",
                path="knowledge/navigation/compass.md",
                body="Keep compass away from metal.",
                tags=("navigation", "compass"),
            ),
        ]

        results = LexicalRetrievalStrategy().search(SearchQuery("purify water", 2), docs)

        self.assertEqual(results[0].document.title, "Water Purification")
        self.assertIn(results[0].confidence, {"HIGH", "MEDIUM"})

    def test_returns_empty_for_unmatched_query(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Compass",
                path="knowledge/navigation/compass.md",
                body="Keep compass away from metal.",
                tags=("navigation",),
            )
        ]

        results = LexicalRetrievalStrategy().search(SearchQuery("satellite firmware", 2), docs)

        self.assertEqual(results, [])

    def test_bm25_ranks_relevant_document_first(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Battery Saving",
                path="knowledge/energy/battery_saving.md",
                body="Reduce phone screen brightness and use low power mode.",
                tags=("battery", "phone"),
                priority="high",
            ),
            KnowledgeDocument(
                title="Burns",
                path="knowledge/medical/burns.md",
                body="Cool burns with clean water.",
                tags=("burns",),
            ),
        ]

        results = BM25RetrievalStrategy().search(SearchQuery("save phone battery", 2), docs)

        self.assertEqual(results[0].document.title, "Battery Saving")
        self.assertIn(results[0].confidence, {"HIGH", "MEDIUM"})


if __name__ == "__main__":
    unittest.main()
