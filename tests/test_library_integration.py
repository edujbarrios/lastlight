from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import LastLight, QueryResult


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PACK = ROOT / "examplepack" / "lastlight-example-en.zip"
EXAMPLE_SOURCE = ROOT / "examplepack" / "source"

WATER_QUERY = (
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)
REFUSAL_QUERY = "How do I repair a diesel engine that will not start?"


class LibraryIntegrationTests(unittest.TestCase):
    def test_external_consumer_can_query_zip_pack(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        result = engine.query(WATER_QUERY)

        self.assertIsInstance(result, QueryResult)
        self.assertTrue(result.accepted)
        self.assertEqual(result.confidence, "HIGH")
        self.assertIn("rolling boil for 1 minute", result.passage or "")
        self.assertEqual(result.sources[0].title, "Safe water during an emergency")

    def test_external_consumer_gets_structured_refusal(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        result = engine.query(REFUSAL_QUERY)

        self.assertFalse(result.accepted)
        self.assertIsNone(result.passage)

    def test_external_consumer_can_mount_multiple_packs(self) -> None:
        engine = LastLight.from_packs([EXAMPLE_PACK, EXAMPLE_SOURCE])
        result = engine.query(
            "The power has been out for several hours. "
            "How long will food stay safe in my refrigerator if I keep the door closed?"
        )

        self.assertTrue(result.sources)
        self.assertEqual(result.sources[0].title, "Food safety during a power outage")

    def test_external_consumer_can_inspect_adaptive_plan(self) -> None:
        engine = LastLight(EXAMPLE_PACK, strategy="adaptive", mode="survival")
        plan = engine.plan(WATER_QUERY)

        self.assertEqual(plan.strategy, "lexical")
        self.assertEqual(plan.mode, "survival")
        self.assertEqual(plan.effective_top_k, 2)


if __name__ == "__main__":
    unittest.main()
