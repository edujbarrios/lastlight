from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.app import LastLightApp
from lastlight.domain import KnowledgeDocument, SearchQuery, SearchResult


class Repository:
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Generator Safety",
                path="knowledge/en/energy/generators.md",
                body="Never run a generator indoors.",
                tags=("generator", "carbon-monoxide"),
            )
        ]


class Retrieval:
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        return [
            SearchResult(
                document=documents[0],
                score=2.0,
                confidence="HIGH",
                passage="Never run a generator indoors.",
                matched_terms=("generator",),
            )
        ]


class AppTests(unittest.TestCase):
    def test_answer_adds_triage_checks_to_single_query(self) -> None:
        answer = LastLightApp(Repository(), Retrieval()).answer("generator safety")

        self.assertIn("Never run a generator indoors.", answer)
        self.assertIn("Follow-up checks:", answer)
        self.assertIn("fresh air", answer)


if __name__ == "__main__":
    unittest.main()
