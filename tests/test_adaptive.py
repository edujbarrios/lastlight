from __future__ import annotations

import threading
import unittest

import helpers  # noqa: F401
from lastlight.adaptive import (
    AdaptiveRetrievalConfig,
    AdaptiveRetrievalStrategy,
    ResourceProfile,
    classify_query_risk,
)
from lastlight.domain import KnowledgeDocument, SearchQuery


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

    def test_bm25_adaptive_verification_records_separate_backend(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"), profile()
        )
        documents = [
            KnowledgeDocument(
                title="Cobalt valve", path="invented/cobalt.md",
                body="Disconnect the cobalt valve before maintenance.",
            ),
            KnowledgeDocument(
                title="Quartz cell", path="invented/quartz.md",
                body="Store a quartz cell in dry conditions.",
            ),
        ]
        results = strategy.search(SearchQuery("cobalt valve maintenance"), documents)
        metadata = strategy.decision_metadata() or {}
        self.assertEqual(results[0].document.path, "invented/cobalt.md")
        self.assertEqual(metadata["strategy"], "bm25")
        self.assertEqual(metadata["verification_backend"], "lexical")
        self.assertIs(metadata["verification_agreement"], True)

    def test_accuracy_uses_lexical_candidate_for_stronger_passage(self) -> None:
        from lastlight.domain import SearchResult
        from lastlight.retrieval.sections import SectionConfig
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"),
            profile(),
            section_config=SectionConfig(min_chars=100, max_chars=200, overlap_chars=20),
        )
        self.assertEqual(strategy.bm25.section_config.min_chars, 100)
        self.assertEqual(strategy.lexical.section_config.min_chars, 100)
        document = KnowledgeDocument("Amber cells", "amber.md",
            "Amber cells operate for 7 hours. Amber cells must stay dry.")
        other = KnowledgeDocument("Quartz cells", "quartz.md",
            "Quartz cells operate for 3 hours.")
        def mocked_bm25(query, docs):
            return [
                SearchResult(document, 8.0, "HIGH", "Amber cells must stay dry.",
                             ("amber", "cells")),
                SearchResult(other, 2.0, "MEDIUM", other.body, ("cells",)),
            ]
        def mocked_lexical(query, docs):
            return [SearchResult(document, 3.0, "HIGH",
                                 "Amber cells operate for 7 hours.",
                                 ("amber", "cells", "hours"))]
        strategy.bm25.search = mocked_bm25  # type: ignore[method-assign]
        strategy.lexical.search = mocked_lexical  # type: ignore[method-assign]
        output = strategy.search(SearchQuery("How long amber cells operate?"), [document, other])
        self.assertEqual(output[0].score, 8.0)
        self.assertIn("7 hours", output[0].passage)
        self.assertEqual(strategy.decision_metadata()["verification_candidates"], 3)

    def test_decision_metadata_is_isolated_per_thread(self) -> None:
        strategy = AdaptiveRetrievalStrategy(
            AdaptiveRetrievalConfig(mode="accuracy"),
            profile(),
        )
        document = KnowledgeDocument(
            title="Mixed guide",
            path="knowledge/en/mixed.md",
            body="Person not breathing. Organize a field kit.",
            language="en",
        )
        barrier = threading.Barrier(2)
        observed: dict[str, tuple[object, object]] = {}

        def run(name: str, text: str) -> None:
            strategy.search(SearchQuery(text, top_k=4), [document])
            barrier.wait(timeout=5)
            metadata = strategy.decision_metadata() or {}
            observed[name] = (metadata.get("risk"), metadata.get("strategy"))

        critical = threading.Thread(
            target=run,
            args=("critical", "person is not breathing"),
        )
        normal = threading.Thread(
            target=run,
            args=("normal", "organize a field kit"),
        )
        critical.start()
        normal.start()
        critical.join(timeout=5)
        normal.join(timeout=5)

        self.assertFalse(critical.is_alive())
        self.assertFalse(normal.is_alive())
        self.assertEqual(observed["critical"], ("critical", "lexical"))
        self.assertEqual(observed["normal"], ("normal", "bm25"))


if __name__ == "__main__":
    unittest.main()
