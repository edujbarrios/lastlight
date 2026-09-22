from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.factory import ApplicationFactory
from lastlight.pack_validation import validate_pack
from lastlight.repository import MarkdownKnowledgeRepository


EXAMPLE_PACK = (
    Path(__file__).resolve().parents[1]
    / "examplepack"
    / "lastlight-example-en.zip"
)


class ExamplePackIntegrationTests(unittest.TestCase):
    def test_committed_example_pack_is_valid(self) -> None:
        report = validate_pack(MarkdownKnowledgeRepository(EXAMPLE_PACK))

        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.errors, ())

    def test_natural_language_water_query_retrieves_english_guidance(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)

        results = app.search(
            "The water supply is down and I have no bottled water. "
            "I found water that looks clear. What should I do before drinking it?"
        )

        self.assertTrue(results)
        self.assertEqual(results[0].document.title, "Safe water during an emergency")
        self.assertEqual(results[0].document.language, "en")
        self.assertEqual(results[0].confidence, "HIGH")
        self.assertAlmostEqual(results[0].score, 2.539, places=3)
        self.assertIn("rolling boil for 1 minute", results[0].passage)

    def test_natural_language_bleeding_query_retrieves_direct_pressure_guidance(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)

        results = app.search(
            "Someone has a deep wound and is bleeding heavily. What should I do while help is on the way?"
        )

        self.assertTrue(results)
        self.assertEqual(results[0].document.title, "Severe external bleeding")
        self.assertEqual(results[0].confidence, "HIGH")
        self.assertIn("Keep pressure on the wound", results[0].passage)

    def test_out_of_domain_query_has_no_acceptable_result(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)
        query = "How do I repair a diesel engine that will not start?"

        results = app.search(query)
        answer = app.answer(query)

        self.assertTrue(all(result.confidence == "LOW" for result in results))
        self.assertIn("I do not have enough confidence", answer)


if __name__ == "__main__":
    unittest.main()
