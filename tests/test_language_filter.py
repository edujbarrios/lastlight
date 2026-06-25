from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.app import LastLightApp
from lastlight.domain import KnowledgeDocument, SearchQuery, SearchResult
from lastlight.interfaces import KnowledgeRepository, RetrievalStrategy


class TwoLanguageRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Water",
                path="knowledge/en/water.md",
                body="Boil water.",
                language="en",
                tags=("water",),
            ),
            KnowledgeDocument(
                title="Agua",
                path="knowledge/es/agua.md",
                body="Hervir agua.",
                language="es",
                tags=("agua",),
            ),
        ]


class CapturingRetrieval(RetrievalStrategy):
    def __init__(self) -> None:
        self.seen_documents: list[KnowledgeDocument] = []

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        self.seen_documents = documents
        return []


class LanguageFilterTests(unittest.TestCase):
    def test_filters_documents_by_language(self) -> None:
        retrieval = CapturingRetrieval()
        app = LastLightApp(TwoLanguageRepository(), retrieval, language="es")

        app.search("agua")

        self.assertEqual([doc.language for doc in retrieval.seen_documents], ["es"])
        self.assertEqual(retrieval.seen_documents[0].title, "Agua")

    def test_without_language_uses_all_documents(self) -> None:
        retrieval = CapturingRetrieval()
        app = LastLightApp(TwoLanguageRepository(), retrieval)

        app.search("water")

        self.assertEqual([doc.language for doc in retrieval.seen_documents], ["en", "es"])


if __name__ == "__main__":
    unittest.main()
