from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import LastLight, QueryResult, RetrievalMetadata, SourceResult


EXAMPLE_PACK = (
    Path(__file__).resolve().parents[1]
    / "examplepack"
    / "lastlight-example-en.zip"
)


class PublicApiTests(unittest.TestCase):
    def test_package_root_exposes_lastlight_facade(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        results = engine.search(
            "The water supply is down and I have no bottled water. "
            "I found water that looks clear. What should I do before drinking it?"
        )

        self.assertTrue(results)
        self.assertEqual(results[0].document.title, "Safe water during an emergency")

    def test_query_returns_stable_public_contracts(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        result = engine.query(
            "The water supply is down and I have no bottled water. "
            "I found water that looks clear. What should I do before drinking it?"
        )

        self.assertIsInstance(result, QueryResult)
        self.assertTrue(result.accepted)
        self.assertEqual(result.confidence, "HIGH")
        self.assertIn("rolling boil for 1 minute", result.passage or "")
        self.assertIsInstance(result.sources[0], SourceResult)
        self.assertEqual(result.sources[0].title, "Safe water during an emergency")
        self.assertIsInstance(result.retrieval, RetrievalMetadata)
        self.assertEqual(result.retrieval.strategy, "lexical")

    def test_query_represents_refusal_without_parsing_cli_text(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        result = engine.query("How do I repair a diesel engine that will not start?")

        self.assertFalse(result.accepted)
        self.assertIsNone(result.confidence)
        self.assertIsNone(result.passage)

    def test_public_facade_exposes_adaptive_plan(self) -> None:
        engine = LastLight(EXAMPLE_PACK, strategy="adaptive", mode="survival")
        plan = engine.plan("How can I make collected water safer to drink?")

        self.assertEqual(plan.strategy, "lexical")
        self.assertEqual(plan.mode, "survival")
        self.assertEqual(plan.effective_top_k, 2)

    def test_from_packs_supports_multiple_sources(self) -> None:
        engine = LastLight.from_packs([EXAMPLE_PACK, EXAMPLE_PACK])
        result = engine.query("How long will food stay cold during a power outage?")

        self.assertTrue(result.sources)


if __name__ == "__main__":
    unittest.main()
