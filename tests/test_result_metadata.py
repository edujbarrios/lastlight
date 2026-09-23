from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import LastLight


EXAMPLE_PACK = (
    Path(__file__).resolve().parents[1]
    / "examplepack"
    / "lastlight-example-en.zip"
)


class ResultMetadataTests(unittest.TestCase):
    def test_out_of_domain_refusal_has_no_match_reason(self) -> None:
        result = LastLight(EXAMPLE_PACK).query(
            "How do I repair a diesel engine that will not start?"
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.sources, ())
        self.assertEqual(result.refusal_reason, "no_matching_knowledge")

    def test_empty_retrieval_has_machine_readable_reason(self) -> None:
        result = LastLight(EXAMPLE_PACK).query("the and or")
        self.assertFalse(result.accepted)
        self.assertEqual(result.sources, ())
        self.assertEqual(result.refusal_reason, "no_matching_knowledge")

    def test_accepted_query_has_no_refusal_reason(self) -> None:
        result = LastLight(EXAMPLE_PACK).query(
            "Someone is bleeding heavily from a deep cut. What should I do?"
        )
        self.assertTrue(result.accepted)
        self.assertIsNone(result.refusal_reason)

    def test_adaptive_plan_exposes_active_resource_budget(self) -> None:
        plan = LastLight(
            EXAMPLE_PACK,
            strategy="adaptive",
            mode="balanced",
            energy_budget_mwh=0.4,
            memory_budget_mb=128,
        ).plan(
            "The power has been out for several hours. How long will food stay safe?"
        )
        self.assertEqual(plan.strategy, "lexical")
        self.assertEqual(plan.energy_budget_mwh, 0.4)
        self.assertEqual(plan.memory_budget_mb, 128)
        self.assertIsNotNone(plan.low_resource_target)
        self.assertIsNotNone(plan.memory_mb)


if __name__ == "__main__":
    unittest.main()
