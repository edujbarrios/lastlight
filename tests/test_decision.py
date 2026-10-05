from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.safety.decision import evaluate_answer_decision


def _result(
    path: str,
    score: float,
    confidence: str,
    matched_terms: tuple[str, ...],
) -> SearchResult:
    document = KnowledgeDocument(
        title=path,
        path=path,
        body="Emergency guidance for water treatment and storage.",
        tags=("water",),
    )
    return SearchResult(
        document=document,
        score=score,
        confidence=confidence,
        passage=document.body,
        matched_terms=matched_terms,
    )


class AnswerDecisionTests(unittest.TestCase):
    def test_clear_high_confidence_winner_stays_high(self) -> None:
        decision = evaluate_answer_decision(
            "water treatment storage emergency supply",
            [
                _result("winner.md", 4.0, "HIGH", ("water", "storage")),
                _result("runner.md", 1.0, "MEDIUM", ("water",)),
            ],
        )

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.confidence, "HIGH")
        self.assertEqual(decision.reason, "strong_match_clear_margin")
        self.assertEqual(decision.score_margin, 3.0)
        self.assertEqual(decision.score_ratio, 4.0)

    def test_ambiguous_high_matches_are_downgraded(self) -> None:
        decision = evaluate_answer_decision(
            "water treatment storage emergency supply",
            [
                _result("winner.md", 4.0, "HIGH", ("water",)),
                _result("runner.md", 3.9, "HIGH", ("water",)),
            ],
        )

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.confidence, "MEDIUM")
        self.assertEqual(decision.reason, "ambiguous_high_confidence_matches")
        self.assertLess(decision.query_coverage, 0.5)

    def test_weak_ambiguous_medium_match_is_refused(self) -> None:
        decision = evaluate_answer_decision(
            "water treatment storage emergency supply",
            [
                _result("winner.md", 1.10, "MEDIUM", ("water",)),
                _result("runner.md", 1.00, "MEDIUM", ("storage",)),
            ],
        )

        self.assertFalse(decision.accepted)
        self.assertIsNone(decision.confidence)
        self.assertEqual(decision.refusal_reason, "insufficient_confidence")
        self.assertEqual(
            decision.reason,
            "weak_query_coverage_and_ambiguous_margin",
        )

    def test_empty_results_explain_no_matching_knowledge(self) -> None:
        decision = evaluate_answer_decision("repair diesel engine", [])

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "no_matching_knowledge")
        self.assertEqual(decision.refusal_reason, "no_matching_knowledge")
        self.assertIsNone(decision.score)


if __name__ == "__main__":
    unittest.main()
