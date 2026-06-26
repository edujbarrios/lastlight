from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.session import LastLightSession


class RecordingApp:
    def __init__(
        self,
        title: str = "Generator Safety",
        tags: tuple[str, ...] = ("generator", "carbon-monoxide"),
        matched_terms: tuple[str, ...] = ("generator",),
    ) -> None:
        self.queries: list[str] = []
        self.document = KnowledgeDocument(
            title=title,
            path="knowledge/en/doc.md",
            body="Never run a generator indoors.",
            language="en",
            tags=tags,
        )
        self.matched_terms = matched_terms

    def search(self, text: str, top_k: int = 3) -> list[SearchResult]:
        self.queries.append(text)
        return [
            SearchResult(
                document=self.document,
                score=2.0,
                confidence="HIGH",
                passage="Never run a generator indoors.",
                matched_terms=self.matched_terms,
            )
        ]


class SessionTests(unittest.TestCase):
    def test_follow_up_query_uses_previous_context(self) -> None:
        app = RecordingApp()
        session = LastLightSession(app)

        session.answer("generator safety")
        session.answer("indoors?")

        self.assertEqual(app.queries[0], "generator safety")
        self.assertIn("generator safety", app.queries[1])
        self.assertIn("Generator Safety", app.queries[1])
        self.assertIn("indoors?", app.queries[1])

    def test_natural_follow_up_query_uses_previous_context(self) -> None:
        app = RecordingApp(
            title="Water Purification",
            tags=("water", "purification", "boiling"),
            matched_terms=("water",),
        )
        session = LastLightSession(app)

        session.answer("I have dirty water after a blackout. How do I make it safer to drink?")
        session.answer("What should I do if boiling is not possible?")

        self.assertIn("Water Purification", app.queries[1])
        self.assertIn("What should I do if boiling is not possible?", app.queries[1])

    def test_clear_removes_context(self) -> None:
        app = RecordingApp()
        session = LastLightSession(app)

        session.answer("generator safety")
        session.clear()
        session.answer("indoors?")

        self.assertEqual(app.queries[-1], "indoors?")

    def test_non_follow_up_query_does_not_use_context(self) -> None:
        app = RecordingApp()
        session = LastLightSession(app)

        session.answer("generator safety")
        session.answer("water purification emergency")

        self.assertEqual(app.queries[-1], "water purification emergency")


if __name__ == "__main__":
    unittest.main()
