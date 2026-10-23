"""Unseen invented validation fixtures, separate from calibration development tests.

Do not edit these tests in response to external benchmark results.
"""
from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.safety.calibration_v3 import evaluate_calibrated_decision
from lastlight.retrieval.hybrid import reciprocal_rank_fusion


DOCS = (
    KnowledgeDocument("Amber pipe", "amber.md",
                      "The amber pipe needs two steel clips before assembly."),
    KnowledgeDocument("Iris relay", "iris.md",
                      "Never activate an iris relay without the safety cover."),
    KnowledgeDocument("Slate gauge", "slate.md",
                      "The slate gauge records pressure once each hour."),
)


class IndependentValidationTests(unittest.TestCase):
    def test_evidence_confidence_contract_and_repeatability(self):
        source = SearchResult(DOCS[0], 8.0, "HIGH", DOCS[0].body,
                              matched_terms=("amber", "pipe", "clips"))
        a = evaluate_calibrated_decision("What does the amber pipe need?",
                                         [source], strategy="bm25", corpus=DOCS)
        b = evaluate_calibrated_decision("What does the amber pipe need?",
                                         [source], strategy="bm25", corpus=DOCS)
        self.assertEqual(a, b)
        self.assertIn(a.confidence, ("HIGH", "MEDIUM", None))
        self.assertTrue(0.0 <= (a.calibrated_score or 0.0) <= 1.0)

    def test_negative_question_rejects_positive_only_passage(self):
        candidate = SearchResult(DOCS[1], 8.0, "HIGH",
                                 "Activate an iris relay with the safety cover.",
                                 ("iris", "relay", "cover"))
        decision = evaluate_calibrated_decision(
            "Can an iris relay run without a safety cover?",
            [candidate], strategy="bm25", corpus=DOCS
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.refusal_code, "MISSING_REQUESTED_FACT")

    def test_rank_fusion_does_not_depend_on_raw_score_scale(self):
        def mk(doc, score):
            return SearchResult(doc, score, "HIGH", doc.body, ())
        lexical = [mk(DOCS[0], 1.2), mk(DOCS[1], .6)]
        bm25 = [mk(DOCS[1], 5.0), mk(DOCS[0], 3.0)]
        initial = reciprocal_rank_fusion([lexical, bm25], limit=3)
        scaled = reciprocal_rank_fusion(
            [[mk(DOCS[0], 120), mk(DOCS[1], 60)],
             [mk(DOCS[1], 50000), mk(DOCS[0], 30000)]], limit=3
        )
        self.assertEqual([x.document.path for x in initial],
                         [x.document.path for x in scaled])
        self.assertEqual([x.score for x in initial],
                         [x.score for x in scaled])


if __name__ == "__main__":
    unittest.main()
