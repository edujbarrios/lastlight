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
                body="Hierve el agua antes de beberla.",
                language="es",
                tags=("agua",),
            ),
        ]


class SpanishOnlyRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Agua segura",
                path="pack-es/agua.md",
                body="Hierve el agua antes de beberla.",
                language="es",
                tags=("agua",),
            )
        ]


class CapturingRetrieval(RetrievalStrategy):
    def __init__(self) -> None:
        self.seen_documents: list[KnowledgeDocument] = []

    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        self.seen_documents = documents
        return []


class FirstDocumentRetrieval(RetrievalStrategy):
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        if not documents:
            return []
        document = documents[0]
        return [
            SearchResult(
                document=document,
                score=2.0,
                confidence="HIGH",
                passage=document.body,
            )
        ]


class LanguageFilterTests(unittest.TestCase):
    def test_explicit_language_filter_still_wins(self) -> None:
        retrieval = CapturingRetrieval()
        app = LastLightApp(TwoLanguageRepository(), retrieval, language="es")

        app.search("water")

        self.assertEqual([doc.language for doc in retrieval.seen_documents], ["es"])

    def test_spanish_query_routes_multilingual_corpus_to_spanish(self) -> None:
        retrieval = CapturingRetrieval()
        app = LastLightApp(TwoLanguageRepository(), retrieval)

        app.search("cómo puedo conseguir agua segura")

        self.assertEqual([doc.language for doc in retrieval.seen_documents], ["es"])
        self.assertEqual(retrieval.seen_documents[0].title, "Agua")

    def test_english_query_routes_multilingual_corpus_to_english(self) -> None:
        retrieval = CapturingRetrieval()
        app = LastLightApp(TwoLanguageRepository(), retrieval)

        app.search("how can I get safe water")

        self.assertEqual([doc.language for doc in retrieval.seen_documents], ["en"])
        self.assertEqual(retrieval.seen_documents[0].title, "Water")

    def test_ambiguous_query_keeps_multilingual_fallback(self) -> None:
        retrieval = CapturingRetrieval()
        app = LastLightApp(TwoLanguageRepository(), retrieval)

        app.search("radio")

        self.assertEqual([doc.language for doc in retrieval.seen_documents], ["en", "es"])

    def test_monolingual_spanish_pack_answers_from_spanish_documents_automatically(self) -> None:
        app = LastLightApp(SpanishOnlyRepository(), FirstDocumentRetrieval())

        answer = app.answer("water safety")

        self.assertIn("Hierve el agua antes de beberla.", answer)
        self.assertNotIn("Boil water", answer)


if __name__ == "__main__":
    unittest.main()
