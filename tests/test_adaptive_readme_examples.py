from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.adaptive import AdaptiveRetrievalConfig, AdaptiveRetrievalStrategy, ResourceProfile
from lastlight.domain import SearchQuery


def stable_profile() -> ResourceProfile:
    return ResourceProfile(
        low_resource_target=False,
        memory_mb=4096,
        battery_percent=80.0,
    )


WATER_QUERY = (
    "The water supply is down and I have no bottled water. "
    "I found water that looks clear. What should I do before drinking it?"
)

FOOD_QUERY = (
    "The power has been out for several hours. "
    "How long will food stay safe in my refrigerator if I keep the door closed?"
)


class AdaptiveReadmeExampleTests(unittest.TestCase):
    def test_balanced_keeps_high_risk_water_on_lexical(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="balanced"), stable_profile()
        )

        decision = strategy.plan(SearchQuery(WATER_QUERY, top_k=3))

        self.assertEqual(decision.risk, "high")
        self.assertEqual(decision.strategy, "lexical")
        self.assertEqual(decision.effective_top_k, 3)
        self.assertEqual(decision.reason, "high-risk query in a safety-first mode")

    def test_balanced_uses_bm25_for_normal_food_query(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="balanced"), stable_profile()
        )

        decision = strategy.plan(SearchQuery(FOOD_QUERY, top_k=3))

        self.assertEqual(decision.risk, "normal")
        self.assertEqual(decision.strategy, "bm25")
        self.assertEqual(decision.effective_top_k, 3)
        self.assertEqual(
            decision.reason, "balanced mode with sufficient detected resources"
        )

    def test_accuracy_uses_bm25_for_high_risk_water_when_unconstrained(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"), stable_profile()
        )

        decision = strategy.plan(SearchQuery(WATER_QUERY, top_k=3))

        self.assertEqual(decision.risk, "high")
        self.assertEqual(decision.strategy, "bm25")
        self.assertEqual(decision.reason, "accuracy mode with no active resource constraint")

    def test_survival_caps_water_query_to_two_lexical_results(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="survival"), stable_profile()
        )

        decision = strategy.plan(SearchQuery(WATER_QUERY, top_k=3))

        self.assertEqual(decision.strategy, "lexical")
        self.assertEqual(decision.effective_top_k, 2)
        self.assertEqual(decision.reason, "survival mode caps retrieval cost")


if __name__ == "__main__":
    unittest.main()
