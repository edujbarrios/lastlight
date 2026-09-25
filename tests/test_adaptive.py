from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.adaptive import (
    AdaptiveRetrievalConfig,
    AdaptiveRetrievalStrategy,
    ResourceProfile,
    classify_query_risk,
)
from lastlight.domain import SearchQuery


def profile(
    *,
    low_resource: bool = False,
    battery: float | None = 80.0,
) -> ResourceProfile:
    return ResourceProfile(
        low_resource_target=low_resource,
        memory_mb=4096,
        battery_percent=battery,
    )


class AdaptiveRetrievalTests(unittest.TestCase):
    def test_survival_mode_prefers_core_lexical_and_caps_top_k(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="survival"),
            profile(),
        )

        decision = strategy.plan(SearchQuery("find shelter", top_k=8))

        self.assertEqual(decision.strategy, "lexical")
        self.assertEqual(decision.effective_top_k, 2)
        self.assertIn("survival", decision.reason)

    def test_low_battery_forces_low_cost_lexical_path(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="balanced"),
            profile(battery=12.0),
        )

        decision = strategy.plan(SearchQuery("find shelter", top_k=5))

        self.assertEqual(decision.strategy, "lexical")
        self.assertEqual(decision.effective_top_k, 2)
        self.assertIn("battery", decision.reason)

    def test_critical_query_stays_on_safety_first_lexical_path(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"),
            profile(),
        )

        decision = strategy.plan(SearchQuery("person is not breathing", top_k=5))

        self.assertEqual(decision.risk, "critical")
        self.assertEqual(decision.strategy, "lexical")
        self.assertEqual(decision.effective_top_k, 3)

    def test_accuracy_mode_uses_bm25_for_normal_query(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"),
            profile(),
        )

        decision = strategy.plan(SearchQuery("organize a field kit", top_k=4))

        self.assertEqual(decision.risk, "normal")
        self.assertEqual(decision.strategy, "bm25")
        self.assertEqual(decision.effective_top_k, 4)

    def test_tight_energy_budget_overrides_balanced_mode(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="balanced", energy_budget_mwh=0.4),
            profile(),
        )

        decision = strategy.plan(SearchQuery("organize a field kit", top_k=4))

        self.assertEqual(decision.strategy, "lexical")
        self.assertIn("energy budget", decision.reason)

    def test_spanish_hemorrhage_is_classified_as_critical(self) -> None:
        self.assertEqual(classify_query_risk("tiene una hemorragia"), "critical")

    def test_heatstroke_is_not_misclassified_by_embedded_stroke(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"),
            profile(),
        )

        decision = strategy.plan(SearchQuery("person may have heatstroke", top_k=5))

        self.assertEqual(decision.risk, "high")
        self.assertEqual(decision.strategy, "bm25")

    def test_risk_terms_do_not_match_inside_unrelated_words(self) -> None:
        self.assertEqual(classify_query_risk("navigation near Las Vegas"), "normal")


if __name__ == "__main__":
    unittest.main()
