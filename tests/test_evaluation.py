from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.app import LastLightApp
from lastlight.domain import EvaluationCase, KnowledgeDocument, SearchQuery, SearchResult
from lastlight.evaluation import run_evaluation
from lastlight.interfaces import KnowledgeRepository, RetrievalStrategy


class FakeRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Bleeding",
                path="knowledge/medical/bleeding.md",
                body="Apply pressure to severe bleeding.",
                tags=("bleeding",),
            )
        ]


class FakeRetrieval(RetrievalStrategy):
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        return [
            SearchResult(
                document=documents[0],
                score=2.0,
                confidence="HIGH",
                passage=documents[0].body,
            )
        ]


class EvaluationTests(unittest.TestCase):
    def test_reports_accuracy_and_confidence(self) -> None:
        app = LastLightApp(FakeRepository(), FakeRetrieval())
        output = run_evaluation(app, [EvaluationCase("stop bleeding", "bleeding")])

        self.assertIn("Total cases: 1", output)
        self.assertIn("Top-1 accuracy: 100.00%", output)
        self.assertIn("- HIGH: 1", output)


if __name__ == "__main__":
    unittest.main()

