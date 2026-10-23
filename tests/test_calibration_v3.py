"""Development-only invented examples; independent of external benchmark labels."""

from __future__ import annotations

import unittest
from dataclasses import replace, asdict

import helpers  # noqa: F401
from lastlight import CalibrationConfig, StrategyCalibration, SectionConfig, LastLight
from lastlight.domain import KnowledgeDocument, SearchQuery, SearchResult
from lastlight.retrieval.hybrid import HybridRetrievalStrategy, reciprocal_rank_fusion
from lastlight.retrieval.sections import retrieval_units
from lastlight.safety.calibration_v3 import evaluate_calibrated_decision


DOCS = [
    KnowledgeDocument("Quartz batteries", "quartz.md",
                      "Quartz batteries must be stored below 12 volts. Never expose them to steam.",
                      tags=("quartz",)),
    KnowledgeDocument("Copper antennas", "copper.md",
                      "A copper antenna must be raised before transmission.", tags=("antenna",)),
    KnowledgeDocument("Quartz housing", "housing.md",
                      "The quartz housing is installed in a dry cabinet.", tags=("quartz",)),
]


def answer(query: str, passage: str, score: float = 8.0, *,
           confidence: str = "HIGH", path: str = "quartz.md"):
    source = next((d for d in DOCS if d.path == path), DOCS[0])
    return evaluate_calibrated_decision(
        query, [SearchResult(source, score, confidence, passage,
                             matched_terms=("quartz", "batteries", "store"))],
        strategy="bm25", corpus=DOCS,
    )


class CalibrationV3Tests(unittest.TestCase):
    def test_explict_quantity_with_unit(self):
        decision = answer("How many volts for quartz batteries?",
                          "Quartz batteries must be stored below 12 volts.")
        self.assertTrue(decision.accepted, (decision.reason, decision.calibrated_score))
        self.assertGreaterEqual(decision.calibrated_score, 0)
        self.assertLessEqual(decision.calibrated_score, 1)

    def test_negative_request_requires_prohibition(self):
        decision = answer("Can quartz batteries be stored without steam?",
                          "Quartz batteries have a protective housing.")
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.refusal_code, "MISSING_REQUESTED_FACT")

    def test_live_and_secret_intents_refuse(self):
        for query, code in (
            ("What quartz batteries are in stock today?", "DYNAMIC_INFORMATION_REQUIRED"),
            ("Give me the quartz API key.", "PRIVATE_OR_CREDENTIAL_DATA"),
        ):
            with self.subTest(query=query):
                decision = answer(query, "Quartz batteries are stored below 12 volts.")
                self.assertFalse(decision.accepted)
                self.assertEqual(decision.refusal_code, code)

    def test_unknown_question_refuses(self):
        decision = evaluate_calibrated_decision("unrelated asteroids", [],
                                               strategy="bm25", corpus=DOCS)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.refusal_code, "OUT_OF_DOMAIN")

    def test_synthetic_cross_language_request(self):
        decision = answer("Cuantos voltios de baterias quartz?",
                          "Las baterias quartz funcionan a 12 voltios.")
        self.assertIn(decision.refusal_code, (None, "INSUFFICIENT_EVIDENCE"))
        self.assertIn(decision.confidence, (None, "HIGH", "MEDIUM"))

    def test_threshold_monotonicity_on_fixed_candidates(self):
        query = "How many volts for quartz batteries?"
        passage = "Quartz batteries must be stored below 12 volts."
        candidate = SearchResult(DOCS[0], 8.0, "HIGH", passage,
                                 ("quartz", "batteries", "volts"))
        outputs = []
        for minimum in (.0, .3, .5, .7, .9, 1.0):
            config = CalibrationConfig(bm25=replace(CalibrationConfig().bm25,
                                                     min_decision_score=minimum))
            decision = evaluate_calibrated_decision(query, [candidate],
                                                    strategy="bm25", config=config,
                                                    corpus=DOCS)
            outputs.append(int(decision.accepted))
        self.assertEqual(outputs, sorted(outputs, reverse=True))

    def test_incompatible_or_invalid_calibration_is_rejected(self):
        with self.assertRaises(ValueError):
            StrategyCalibration(-0.2, .3, .4, .5)
        with self.assertRaises(ValueError):
            CalibrationConfig(weight_strength=0.3)

    def test_invented_near_duplicate_documents_do_not_multiply(self):
        first = SearchResult(DOCS[0], 8, "HIGH", DOCS[0].body, ("quartz",))
        other = SearchResult(DOCS[2], 7, "HIGH", DOCS[2].body, ("quartz",))
        fused = reciprocal_rank_fusion([[first, other], [other, first]], limit=3)
        self.assertEqual({r.document.path for r in fused}, {"quartz.md", "housing.md"})
        self.assertEqual(len(fused), 2)
        self.assertTrue(all(len(r.backend_scores) == 2 for r in fused))

    def test_hybrid_search_reports_components(self):
        results = HybridRetrievalStrategy().search(
            SearchQuery("quartz batteries stored", top_k=2), DOCS
        )
        self.assertEqual(results[0].document.path, "quartz.md")
        self.assertTrue(results[0].backend_scores)
        self.assertEqual(len(set((r.document.path for r in results))), len(results))

    def test_all_sections_preserve_immutable_source(self):
        long_body = ("# Quartz\n\n" + "A sentence about quartz batteries. " * 20 +
                     "\n\n## Cold storage\n\n" + "Store quartz batteries dry. " * 30)
        source = KnowledgeDocument("Quartz operations", "invented/quartz.md", long_body)
        config = SectionConfig(min_chars=100, max_chars=260, overlap_chars=40)
        chunks = retrieval_units([source], config)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(unit.source is source for unit in chunks))
        self.assertTrue(all(len(unit.passage_body) <= config.max_chars for unit in chunks))
        self.assertTrue(any("Cold storage" in unit.heading_path for unit in chunks))

    def test_short_document_stays_single_unit(self):
        chunks = retrieval_units(DOCS)
        self.assertEqual(len(chunks), len(DOCS))

    def test_public_optional_fields_serialize(self):
        from lastlight.types import SourceResult, SourceDocument
        doc = SourceDocument("Quartz", "a", "Quartz evidence", "p", "1",
                             "local", "/", "en", ("quartz",))
        src = SourceResult(doc, 1.0, "MEDIUM", "Quartz evidence",
                           section="Quartz > Storage", backend_scores=(("bm25", 4.0),))
        obj = asdict(src)
        self.assertEqual(obj["section"], "Quartz > Storage")
        self.assertEqual(obj["backend_scores"][0][0], "bm25")

    def test_public_engine_hybrid_and_config(self):
        from pathlib import Path
        pack = Path(__file__).resolve().parents[1] / "examplepack" / "lastlight-example-en.zip"
        engine = LastLight(pack, strategy="hybrid", calibration=CalibrationConfig())
        result = engine.query("How long will refrigerated food stay cold during an outage?")
        self.assertEqual(result.retrieval.strategy, "hybrid")
        self.assertTrue(result.sources)
        self.assertIsNotNone(result.decision.calibrated_score)
        self.assertIsInstance(result.decision.explanation, str)


if __name__ == "__main__":
    unittest.main()
