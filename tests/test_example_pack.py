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
    / "lastlight-example-es.zip"
)


class ExamplePackIntegrationTests(unittest.TestCase):
    def test_committed_example_pack_is_valid(self) -> None:
        report = validate_pack(MarkdownKnowledgeRepository(EXAMPLE_PACK))

        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.errors, ())

    def test_water_query_retrieves_spanish_water_guidance(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)

        results = app.search("agua clara hervor 1 minuto")

        self.assertTrue(results)
        self.assertEqual(results[0].document.title, "Agua segura durante una emergencia")
        self.assertEqual(results[0].document.language, "es")
        self.assertEqual(results[0].confidence, "HIGH")
        self.assertIn("1 minuto", results[0].passage)

    def test_bleeding_query_retrieves_direct_pressure_guidance(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)

        results = app.search("sangrado grave presión directa herida")

        self.assertTrue(results)
        self.assertEqual(results[0].document.title, "Sangrado externo grave")
        self.assertEqual(results[0].confidence, "HIGH")
        self.assertIn("presión directa", results[0].passage)

    def test_out_of_domain_query_has_no_retrieval_result(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)

        results = app.search("¿cómo reparo un motor diésel?")

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
