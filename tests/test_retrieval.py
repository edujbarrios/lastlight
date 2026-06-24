from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import LexicalRetrievalStrategy


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


if __name__ == "__main__":
    unittest.main()

