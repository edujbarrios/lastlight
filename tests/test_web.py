from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, KnowledgePack, SearchResult
from lastlight.session import LastLightSession
from lastlight.web import (
    WebPack,
    WebTurn,
    mounted_packs,
    parse_clear,
    parse_query,
    parse_query_string,
    render_history,
    render_page,
    solution_answer,
    solution_turn,
)


class FakeRepository:
    def describe_packs(self) -> tuple[KnowledgePack, ...]:
        return (
            KnowledgePack(name="water-es", version="1.2.0", path="water-es.zip"),
            KnowledgePack(name="first-aid-es", version="2.0.0", path="first-aid-es.zip"),
        )


class FakeApp:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.repository = FakeRepository()

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        return self.results


class WebTests(unittest.TestCase):
    def test_parse_query_trims_form_value(self) -> None:
        self.assertEqual(parse_query(b"q=%20water%20purification%20"), "water purification")

    def test_parse_query_string_trims_url_value(self) -> None:
        self.assertEqual(parse_query_string("/?q=%20find%20north%20"), "find north")

    def test_parse_clear_detects_clear_request(self) -> None:
        self.assertTrue(parse_clear("/?clear=1"))
        self.assertFalse(parse_clear("/?q=water"))

    def test_render_page_escapes_query_and_answer(self) -> None:
        html = render_page("<query>", "<answer>").decode("utf-8")

        self.assertIn("&lt;query&gt;", html)
        self.assertIn("&lt;answer&gt;", html)
        self.assertNotIn("<query>", html)
        self.assertNotIn("<answer>", html)
        self.assertIn('placeholder="Ask across the mounted knowledge packs..."', html)
        self.assertIn('href="/?clear=1"', html)
        self.assertIn("Keep calm.", html)
        self.assertIn("The situation may be unstable", html)
        self.assertIn("Breathe slowly for 30 seconds.", html)
        self.assertIn("Built-in knowledge", html)

    def test_render_page_lists_multiple_mounted_packs(self) -> None:
        html = render_page(
            packs=(
                WebPack("water-es", "1.2.0"),
                WebPack("first-aid-es", "2.0.0"),
            )
        ).decode("utf-8")

        self.assertIn("2 packs mounted", html)
        self.assertIn("water-es", html)
        self.assertIn("1.2.0", html)
        self.assertIn("first-aid-es", html)
        self.assertIn("offline", html)

    def test_render_history_shows_multiple_turns(self) -> None:
        html = render_history(
            [
                ("generator safety", "Keep it outside."),
                ("indoors?", "Do not run it indoors."),
            ]
        )

        self.assertIn("You: generator safety", html)
        self.assertIn("Keep it outside.", html)
        self.assertIn("You: indoors?", html)
        self.assertIn("LastLight answer", html)
        self.assertIn("Do not run it indoors.", html)

    def test_render_history_shows_pack_provenance(self) -> None:
        html = render_history(
            [
                WebTurn(
                    query="safe water",
                    answer="Boil water.",
                    pack_name="water-es",
                    pack_version="1.2.0",
                    source_path="es/water.md",
                    confidence="HIGH",
                )
            ]
        )

        self.assertIn("water-es 1.2.0", html)
        self.assertIn("es/water.md", html)
        self.assertIn("HIGH", html)

    def test_mounted_packs_reads_composite_repository_metadata(self) -> None:
        packs = mounted_packs(FakeApp([]))

        self.assertEqual([pack.name for pack in packs], ["water-es", "first-aid-es"])
        self.assertEqual([pack.version for pack in packs], ["1.2.0", "2.0.0"])

    def test_solution_answer_returns_only_passage(self) -> None:
        document = KnowledgeDocument(
            title="Water",
            path="knowledge/en/water.md",
            body="Boil water.",
            language="en",
            tags=("water",),
        )
        result = SearchResult(
            document=document,
            score=2.0,
            confidence="HIGH",
            passage="Boil water before drinking.",
        )

        answer = solution_answer(LastLightSession(FakeApp([result])), "water")

        self.assertEqual(answer, "Boil water before drinking.")
        self.assertNotIn("Source:", answer)
        self.assertNotIn("HIGH", answer)

    def test_solution_turn_keeps_source_pack_metadata(self) -> None:
        document = KnowledgeDocument(
            title="Water",
            path="es/water.md",
            body="Boil water.",
            pack_name="water-es",
            pack_version="1.2.0",
            pack_path="water-es.zip",
        )
        result = SearchResult(document, 2.0, "HIGH", "Boil water before drinking.")

        turn = solution_turn(LastLightSession(FakeApp([result])), "water")

        self.assertEqual(turn.pack_name, "water-es")
        self.assertEqual(turn.pack_version, "1.2.0")
        self.assertEqual(turn.source_path, "es/water.md")
        self.assertEqual(turn.confidence, "HIGH")

    def test_solution_answer_refuses_when_confidence_is_low(self) -> None:
        document = KnowledgeDocument(title="Low", path="low.md", body="Low.")
        result = SearchResult(
            document=document,
            score=0.1,
            confidence="LOW",
            passage="Low confidence passage.",
        )

        answer = solution_answer(LastLightSession(FakeApp([result])), "unknown")

        self.assertIn("not have enough confidence", answer)


if __name__ == "__main__":
    unittest.main()
