from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.app import LastLightApp
from lastlight.domain import EvaluationCase, KnowledgeDocument, SearchQuery, SearchResult
from lastlight.evaluation import build_evaluation_report, run_evaluation, write_evaluation_report
from lastlight.interfaces import KnowledgeRepository, RetrievalStrategy


class FakeRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Bleeding",
                path="knowledge/medical/bleeding.md",
                body="Apply pressure to severe bleeding.",
                tags=("bleeding",),
            )
        ]


class FakeRetrieval(RetrievalStrategy):
    def search(
        self, query: SearchQuery, documents: list[KnowledgeDocument]
    ) -> list[SearchResult]:
        return [
            SearchResult(
                document=documents[0],
                score=2.0,
                confidence="HIGH",
                passage=documents[0].body,
            )
        ]


class EvaluationTests(unittest.TestCase):
    def test_reports_accuracy_and_confidence(self) -> None:
        app = LastLightApp(FakeRepository(), FakeRetrieval())
        output = run_evaluation(app, [EvaluationCase("stop bleeding", "bleeding")])

        self.assertIn("Total cases: 1", output)
        self.assertIn("Top-1 accuracy: 100.00%", output)
        self.assertIn("Top-3 accuracy: 100.00%", output)
        self.assertIn("MRR: 1.000", output)
        self.assertIn("- HIGH: 1", output)

    def test_builds_structured_report(self) -> None:
        app = LastLightApp(FakeRepository(), FakeRetrieval())
        report = build_evaluation_report(
            app, [EvaluationCase("stop bleeding", "bleeding")]
        )

        self.assertEqual(report["total_cases"], 1)
        self.assertEqual(report["correct"], 1)
        self.assertEqual(report["top_1_correct"], 1)
        self.assertEqual(report["top_k_correct"], 1)
        self.assertEqual(report["top_1_accuracy"], 1.0)
        self.assertEqual(report["top_k_accuracy"], 1.0)
        self.assertEqual(report["mean_reciprocal_rank"], 1.0)
        self.assertIn("latency_ms", report)
        self.assertIn("by_expected_tag", report)
        case = report["cases"][0]  # type: ignore[index]
        self.assertTrue(case["top_1_correct"])
        self.assertTrue(case["top_k_correct"])
        self.assertEqual(case["rank"], 1)
        self.assertEqual(case["result"]["path"], "knowledge/medical/bleeding.md")

    def test_writes_structured_report(self) -> None:
        report = {"total_cases": 0, "correct": 0, "top_1_accuracy": 0.0, "cases": []}
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "eval" / "results.json"

            write_evaluation_report(report, output)
            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(data["total_cases"], 0)


if __name__ == "__main__":
    unittest.main()
