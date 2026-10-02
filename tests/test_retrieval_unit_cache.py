from __future__ import annotations

import unittest
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import BM25RetrievalStrategy, LexicalRetrievalStrategy
from lastlight.retrieval.sections import retrieval_units as build_retrieval_units


def _large_document(body_suffix: str = "") -> KnowledgeDocument:
    body = (
        "# Operations Manual\n\n"
        + "\n\n".join(
            f"Routine procedure {index}. " + "General equipment guidance. " * 12
            for index in range(20)
        )
        + body_suffix
    )
    return KnowledgeDocument(
        title="Operations Manual",
        path="knowledge/operations.md",
        body=body,
        tags=("operations",),
    )


class RetrievalUnitCacheTests(unittest.TestCase):
    def test_strategies_reuse_units_for_equivalent_corpus(self) -> None:
        document = _large_document()
        equivalent = KnowledgeDocument(
            title=document.title,
            path=document.path,
            body=document.body,
            source_sha256=document.source_sha256,
            language=document.language,
            tags=document.tags,
            priority=document.priority,
        )

        for strategy_type in (LexicalRetrievalStrategy, BM25RetrievalStrategy):
            with self.subTest(strategy=strategy_type.__name__):
                strategy = strategy_type()
                with patch(
                    "lastlight.retrieval.strategies.retrieval_units",
                    wraps=build_retrieval_units,
                ) as prepare:
                    strategy.search(SearchQuery("routine equipment", 1), [document])
                    strategy.search(SearchQuery("general guidance", 1), [equivalent])

                self.assertEqual(prepare.call_count, 1)

    def test_strategies_rebuild_units_when_content_changes(self) -> None:
        document = _large_document()
        changed = _large_document(
            "\n\nEmergency beacon deployment requires a fully extended antenna."
        )

        for strategy_type in (LexicalRetrievalStrategy, BM25RetrievalStrategy):
            with self.subTest(strategy=strategy_type.__name__):
                strategy = strategy_type()
                with patch(
                    "lastlight.retrieval.strategies.retrieval_units",
                    wraps=build_retrieval_units,
                ) as prepare:
                    strategy.search(SearchQuery("routine equipment", 1), [document])
                    strategy.search(SearchQuery("emergency beacon antenna", 1), [changed])

                self.assertEqual(prepare.call_count, 2)


if __name__ == "__main__":
    unittest.main()
