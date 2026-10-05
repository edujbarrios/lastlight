from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import (
    ConfigurationError,
    DecisionMetadata,
    LastLight,
    QueryExplanation,
    QueryResult,
    RetrievalMetadata,
    SourceDocument,
    SourceResult,
)


EXAMPLE_PACK = (
    Path(__file__).resolve().parents[1]
    / "examplepack"
    / "lastlight-example-en.zip"
)


class PublicApiTests(unittest.TestCase):
    def test_package_root_exposes_public_search_results(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        results = engine.search(
            "Someone has a deep cut and is bleeding heavily. "
            "What should I do while waiting for emergency services?"
        )

        self.assertTrue(results)
        self.assertIsInstance(results[0], SourceResult)
        self.assertIsInstance(results[0].document, SourceDocument)
        self.assertEqual(results[0].title, "Severe external bleeding")
        self.assertEqual(results[0].document.title, results[0].title)

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
        self.assertIsInstance(result.decision, DecisionMetadata)
        assert result.decision is not None
        self.assertTrue(result.decision.accepted)
        self.assertGreater(result.decision.score or 0.0, 0.0)
        self.assertGreater(result.decision.query_coverage, 0.0)
        self.assertTrue(result.decision.matched_terms)

    def test_explain_returns_auditable_decision_trace(self) -> None:
        engine = LastLight(EXAMPLE_PACK, strategy="bm25")
        explanation = engine.explain(
            "How long will food stay cold during a power outage?"
        )

        self.assertIsInstance(explanation, QueryExplanation)
        self.assertTrue(explanation.decision.accepted)
        self.assertIn(explanation.decision.confidence, {"HIGH", "MEDIUM"})
        self.assertEqual(
            explanation.sources[0].title,
            "Food safety during a power outage",
        )
        self.assertGreater(explanation.decision.query_coverage, 0.0)
        self.assertGreater(explanation.decision.score or 0.0, 0.0)

    def test_query_represents_refusal_without_parsing_cli_text(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        result = engine.query("How do I repair a diesel engine that will not start?")

        self.assertFalse(result.accepted)
        self.assertIsNone(result.confidence)
        self.assertIsNone(result.passage)
        self.assertIsNotNone(result.decision)
        assert result.decision is not None
        self.assertEqual(result.decision.reason, "no_matching_knowledge")
        self.assertEqual(result.refusal_reason, "no_matching_knowledge")

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

    def test_invalid_top_k_is_rejected_at_the_public_boundary(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        query = "How can I make collected water safer to drink?"

        with self.assertRaisesRegex(ConfigurationError, "top_k"):
            engine.search(query, top_k=0)
        with self.assertRaisesRegex(ConfigurationError, "top_k"):
            engine.query(query, top_k=-1)
        with self.assertRaisesRegex(ConfigurationError, "top_k"):
            engine.explain(query, top_k=0)
        with self.assertRaisesRegex(ConfigurationError, "top_k"):
            engine.answer(query, top_k=True)
        with self.assertRaisesRegex(ConfigurationError, "top_k"):
            engine.plan(query, top_k=1.5)  # type: ignore[arg-type]

    def test_invalid_energy_budget_is_rejected_at_the_public_boundary(self) -> None:
        invalid_values = (0, -1, float("nan"), float("inf"), True, "0.4")

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ConfigurationError, "energy_budget_mwh"):
                    LastLight(
                        EXAMPLE_PACK,
                        strategy="lexical",
                        energy_budget_mwh=value,  # type: ignore[arg-type]
                    )

    def test_invalid_memory_budget_is_rejected_at_the_public_boundary(self) -> None:
        invalid_values = (0, -1, 1.5, True, "64")

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ConfigurationError, "memory_budget_mb"):
                    LastLight(
                        EXAMPLE_PACK,
                        strategy="bm25",
                        memory_budget_mb=value,  # type: ignore[arg-type]
                    )

    def test_valid_resource_budgets_are_preserved_in_adaptive_metadata(self) -> None:
        engine = LastLight(
            EXAMPLE_PACK,
            strategy="adaptive",
            energy_budget_mwh=1,
            memory_budget_mb=128,
        )

        plan = engine.plan("organize a field kit")

        self.assertEqual(plan.energy_budget_mwh, 1.0)
        self.assertEqual(plan.memory_budget_mb, 128)

    def test_unknown_strategy_is_rejected_instead_of_falling_back(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "unsupported retrieval strategy"):
            LastLight(EXAMPLE_PACK, strategy="bm225")

    def test_unknown_adaptive_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "unsupported adaptive mode"):
            LastLight(EXAMPLE_PACK, strategy="adaptive", mode="turbo")


if __name__ == "__main__":
    unittest.main()
