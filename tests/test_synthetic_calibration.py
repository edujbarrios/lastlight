"""Independent synthetic calibration cohort: no cases or fixtures from lastlight-bench.

These examples are invented and static. They test policy invariants and avoid
optimizing decision thresholds on the final evaluation corpus.
"""
from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.safety.decision import THRESHOLDS, evaluate_answer_decision


def item(text: str, *, path: str = "invented/cobalt.md",
         score: float = 7.0, confidence: str = "HIGH",
         matched: tuple[str, ...] = ("cobalt", "filter", "long")) -> SearchResult:
    document = KnowledgeDocument(
        title="Invented cobalt filter",
        path=path,
        body=text,
        tags=("cobalt", "filter"),
    )
    return SearchResult(document, score, confidence, text, matched)


DOCUMENTS = [
    KnowledgeDocument("Cobalt filter", "cobalt.md",
                      "The cobalt filter operates for 8 hours."),
    KnowledgeDocument("Copper pump", "copper.md",
                      "Copper water pumps are tested once a week."),
    KnowledgeDocument("Water drum", "water.md",
                      "Water storage needs a clean closed container."),
]


class SyntheticCalibrationTests(unittest.TestCase):
    def decision(self, query: str, results: list[SearchResult], *,
                 strategy: str = "bm25", profile: str = "balanced",
                 verification_agreement: bool | None = None):
        return evaluate_answer_decision(
            query, results, strategy=strategy, profile=profile,
            corpus=DOCUMENTS, verification_agreement=verification_agreement,
        )

    def test_explicit_quantity_and_time_support_accepts(self):
        result = self.decision(
            "How long cobalt filter",
            [item("The cobalt filter operates for 8 hours.")],
        )
        self.assertTrue(result.accepted, result.reason)
        self.assertTrue(result.evidence_sufficient)
        self.assertGreater(result.weighted_query_coverage, 0.5)
        self.assertEqual(result.strategy, "bm25")

    def test_high_confidence_and_large_margin_cannot_override_missing_quantity(self):
        decision = self.decision(
            "How many cobalt filters are stored",
            [item("The cobalt filters are stored in a cabinet.",
                  matched=("cobalt", "filter", "stored")),
             item("Water filters are stored elsewhere.", path="other.md",
                  score=0.1, matched=("filter",))],
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "missing_quantity_evidence")
        self.assertGreater(decision.score_ratio or 0, 10)

    def test_unrelated_number_does_not_answer_requested_quantity(self):
        decision = self.decision(
            "How many cobalt filters are stored",
            [item("The cobalt filters are stored in a cabinet. Revision 2023.",
                  matched=("cobalt", "filter", "stored"))],
        )
        self.assertFalse(decision.accepted)

    def test_live_stock_and_future_queries_refuse_despite_high_score(self):
        for query in (
            "How much cobalt stock remains right now?",
            "Are cobalt filters available today?",
            "Which filters will be in stock tomorrow?",
            "¿Cuánto queda actualmente del inventario de cobalto?",
        ):
            with self.subTest(query=query):
                decision = self.decision(query, [item(query, matched=("cobalt", "filter"))])
                self.assertFalse(decision.accepted)
                self.assertEqual(decision.reason, "requires_live_or_future_evidence")

    def test_private_credentials_authority_and_clinical_intents_refuse(self):
        for query in (
            "What is the cobalt password?",
            "¿Cuál es la contraseña privada?",
            "Who can certify cobalt safety?",
            "Can you prescribe a cobalt dose?",
        ):
            with self.subTest(query=query):
                result = self.decision(query, [item(query)])
                self.assertFalse(result.accepted)
                self.assertEqual(result.reason, "requires_authorized_or_private_evidence")

    def test_negative_request_requires_explicit_negative_condition(self):
        decision = self.decision(
            "Can cobalt filter run without ventilation?",
            [item("The cobalt filter operates with a ventilation fan.",
                  matched=("cobalt", "filter", "run", "ventilation"))],
        )
        self.assertFalse(decision.accepted)
        self.assertIn(decision.reason, {"missing_negative_evidence", "insufficient_query_coverage"})

    def test_lexical_can_be_more_permissive_than_bm25_without_score_mixing(self):
        data = [item("The cobalt filter operates for 8 hours.", score=1.8,
                     confidence="HIGH", matched=("cobalt", "filter", "long"))]
        lexical = self.decision("How long cobalt filter", data, strategy="lexical")
        bm25 = self.decision("How long cobalt filter", data, strategy="bm25")
        self.assertTrue(lexical.accepted)
        self.assertFalse(bm25.accepted)  # BM25-specific score strength

    def test_strict_profile_requires_stronger_evidence(self):
        for strategy in ("lexical", "bm25"):
            with self.subTest(strategy=strategy):
                balanced = THRESHOLDS[strategy]["balanced"]
                strict = THRESHOLDS[strategy]["conservative"]
                self.assertGreater(strict.min_strength, balanced.min_strength)
                self.assertGreater(strict.min_weighted_coverage, balanced.min_weighted_coverage)
                self.assertGreater(strict.min_passage_coverage, balanced.min_passage_coverage)

    def test_adaptive_secondary_disagreement_downgrades_or_refuses(self):
        supported = [item("The cobalt filter operates for 8 hours.")]
        agreed = self.decision("How long cobalt filter", supported,
                              verification_agreement=True)
        disagree = self.decision("How long cobalt filter", supported,
                                 verification_agreement=False)
        self.assertTrue(agreed.accepted)
        self.assertTrue(disagree.accepted)
        self.assertEqual(disagree.confidence, "MEDIUM")
        strict = self.decision("How long cobalt filter", supported,
                               profile="conservative", verification_agreement=False)
        self.assertFalse(strict.accepted)
        self.assertEqual(strict.reason, "retrieval_strategies_disagree")

    def test_idf_weights_rare_concepts_over_common_ones(self):
        common_only = self.decision(
            "water cobalt", [item("Water storage only.", matched=("water",),
                                   score=7)],
        )
        self.assertEqual(common_only.query_coverage, 0.5)
        self.assertLess(common_only.weighted_query_coverage, 0.5)

    def test_no_results_never_promote_to_an_answer(self):
        decision = self.decision("cobalt filter", [])
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.refusal_reason, "no_matching_knowledge")


if __name__ == "__main__":
    unittest.main()
