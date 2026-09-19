from __future__ import annotations

import unittest
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.device_benchmark import StrategyBenchmark, recommend_strategy


class DeviceBenchmarkTests(unittest.TestCase):
    def _result(
        self,
        strategy: str,
        precision: float,
        refusal: float,
        top_k: float = 0.8,
        energy: float = 1.0,
        p95: float = 10.0,
    ) -> StrategyBenchmark:
        return StrategyBenchmark(
            strategy=strategy,
            cases=10,
            top_1_accuracy=0.7,
            top_k_accuracy=top_k,
            mrr=0.75,
            answer_precision=precision,
            refusal_recall=refusal,
            answerable_recall=0.9,
            mean_latency_ms=5.0,
            p95_latency_ms=p95,
            python_peak_memory_mb=2.0,
            energy_per_query_mwh=energy,
            energy_kind="measured",
            elapsed_s=0.1,
        )

    def test_recommendation_prioritizes_safety(self) -> None:
        fast = self._result("fast", precision=0.80, refusal=0.40, energy=0.1)
        safe = self._result("safe", precision=0.95, refusal=0.80, energy=2.0)

        recommendation = recommend_strategy([fast, safe])

        self.assertEqual(recommendation["strategy"], "safe")

    def test_recommendation_uses_accuracy_as_tiebreaker(self) -> None:
        first = self._result("first", precision=0.90, refusal=0.70, top_k=0.75)
        second = self._result("second", precision=0.90, refusal=0.70, top_k=0.85)

        recommendation = recommend_strategy([first, second])

        self.assertEqual(recommendation["strategy"], "second")

    def test_recommendation_uses_energy_after_safety_and_accuracy(self) -> None:
        costly = self._result("costly", precision=0.90, refusal=0.70, energy=2.0)
        efficient = self._result("efficient", precision=0.90, refusal=0.70, energy=0.5)

        recommendation = recommend_strategy([costly, efficient])

        self.assertEqual(recommendation["strategy"], "efficient")

    def test_empty_results_have_no_recommendation(self) -> None:
        recommendation = recommend_strategy([])
        self.assertIsNone(recommendation["strategy"])


if __name__ == "__main__":
    unittest.main()
