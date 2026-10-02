from __future__ import annotations

import unittest
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import BM25RetrievalStrategy, LexicalRetrievalStrategy, select_passage


def _long_repetitive_guide() -> KnowledgeDocument:
    body = "\n\n".join(
        f"Preparedness section {index}. General preparedness supplies include water, radio, "
        "lighting, batteries, and routine equipment checks. " * 8
        for index in range(16)
    )
    return KnowledgeDocument(
        title="Preparedness Manual",
        path="knowledge/preparedness/manual.md",
        body=body,
        tags=("preparedness", "supplies"),
        priority="high",
    )


class PassageEfficiencyTests(unittest.TestCase):
    def test_passage_selection_runs_once_for_winning_source(self) -> None:
        guide = _long_repetitive_guide()
        query = SearchQuery("general preparedness water supplies", 1)

        for strategy in (LexicalRetrievalStrategy(), BM25RetrievalStrategy()):
            with self.subTest(strategy=type(strategy).__name__):
                with patch(
                    "lastlight.retrieval.strategies.select_passage",
                    wraps=select_passage,
                ) as choose_passage:
                    results = strategy.search(query, [guide])

                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].document, guide)
                self.assertEqual(choose_passage.call_count, 1)

    def test_passage_selection_only_runs_for_top_k_results(self) -> None:
        documents = [
            KnowledgeDocument(
                title="Emergency Water Storage",
                path="knowledge/water/storage.md",
                body="Store emergency water in clean sealed containers and inspect supplies regularly.",
                tags=("water", "storage", "emergency"),
                priority="high",
            ),
            KnowledgeDocument(
                title="Emergency Water Treatment",
                path="knowledge/water/treatment.md",
                body="Treat emergency water by following the purification guidance for the source.",
                tags=("water", "treatment", "emergency"),
            ),
            KnowledgeDocument(
                title="Emergency Water Transport",
                path="knowledge/water/transport.md",
                body="Carry emergency water in closed containers that can be moved safely.",
                tags=("water", "transport", "emergency"),
            ),
        ]
        query = SearchQuery("emergency water", 1)

        for strategy in (LexicalRetrievalStrategy(), BM25RetrievalStrategy()):
            with self.subTest(strategy=type(strategy).__name__):
                with patch(
                    "lastlight.retrieval.strategies.select_passage",
                    wraps=select_passage,
                ) as choose_passage:
                    results = strategy.search(query, documents)

                self.assertEqual(len(results), 1)
                self.assertEqual(choose_passage.call_count, 1)


if __name__ == "__main__":
    unittest.main()
