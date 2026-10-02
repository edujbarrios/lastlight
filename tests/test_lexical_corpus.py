from __future__ import annotations

import unittest
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import LexicalRetrievalStrategy
from lastlight.retrieval.ranking import (
    lexical_score,
    lexical_scores,
    prepare_lexical_corpus,
)


def _documents() -> list[KnowledgeDocument]:
    return [
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
            body="Cool burns with clean running water.",
            tags=("burns", "first-aid"),
        ),
    ]


class LexicalCorpusTests(unittest.TestCase):
    def test_prepared_batch_scoring_matches_single_document_scoring(self) -> None:
        documents = _documents()
        query = "save phone battery"
        corpus = prepare_lexical_corpus(documents)

        batch_scores = lexical_scores(query, documents, corpus=corpus)
        individual_scores = [
            lexical_score(query, document, corpus_size=len(documents))
            for document in documents
        ]

        self.assertEqual(batch_scores, individual_scores)

    def test_strategy_reuses_prepared_statistics_for_equivalent_corpus(self) -> None:
        documents = _documents()
        reloaded = [
            KnowledgeDocument(
                title=document.title,
                path=document.path,
                body=document.body,
                source_sha256=document.source_sha256,
                language=document.language,
                tags=document.tags,
                priority=document.priority,
            )
            for document in documents
        ]
        strategy = LexicalRetrievalStrategy()

        with patch(
            "lastlight.retrieval.strategies.prepare_lexical_corpus",
            wraps=prepare_lexical_corpus,
        ) as prepare:
            strategy.search(SearchQuery("save phone battery", 2), documents)
            strategy.search(SearchQuery("clean running water", 2), reloaded)

        self.assertEqual(prepare.call_count, 1)

    def test_strategy_rebuilds_statistics_when_content_changes(self) -> None:
        documents = _documents()
        changed = [
            KnowledgeDocument(
                title="Battery Saving",
                path="knowledge/energy/battery_saving.md",
                body="Disconnect the battery before electrical maintenance.",
                tags=("battery", "phone"),
                priority="high",
            ),
            documents[1],
        ]
        strategy = LexicalRetrievalStrategy()

        with patch(
            "lastlight.retrieval.strategies.prepare_lexical_corpus",
            wraps=prepare_lexical_corpus,
        ) as prepare:
            strategy.search(SearchQuery("save phone battery", 2), documents)
            strategy.search(SearchQuery("electrical maintenance", 2), changed)

        self.assertEqual(prepare.call_count, 2)


if __name__ == "__main__":
    unittest.main()
