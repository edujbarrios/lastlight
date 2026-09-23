from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import LastLight, PackInfo, PackProvenance, PackValidation


EXAMPLE_PACK = (
    Path(__file__).resolve().parents[1]
    / "examplepack"
    / "lastlight-example-en.zip"
)


class PackPublicApiTests(unittest.TestCase):
    def test_packs_exposes_metadata_without_internal_repository_types(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        packs = engine.packs()

        self.assertEqual(len(packs), 1)
        self.assertIsInstance(packs[0], PackInfo)
        self.assertEqual(packs[0].name, "LastLight Example Pack EN")
        self.assertEqual(packs[0].version, "1.1.0")
        self.assertEqual(packs[0].document_count, 3)
        self.assertIn("en", packs[0].languages)

    def test_validate_packs_returns_structured_reports(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        reports = engine.validate_packs()

        self.assertEqual(len(reports), 1)
        self.assertIsInstance(reports[0], PackValidation)
        self.assertTrue(reports[0].ok)
        self.assertEqual(reports[0].errors, ())

    def test_verify_provenance_returns_structured_report(self) -> None:
        engine = LastLight(EXAMPLE_PACK)
        reports = engine.verify_provenance()

        self.assertEqual(len(reports), 1)
        self.assertIsInstance(reports[0], PackProvenance)
        self.assertEqual(reports[0].pack.name, "LastLight Example Pack EN")
        self.assertEqual(len(reports[0].fingerprint_sha256), 64)

    def test_multi_pack_metadata_is_returned_per_mount(self) -> None:
        engine = LastLight.from_packs([EXAMPLE_PACK, EXAMPLE_PACK])
        self.assertEqual(len(engine.packs()), 2)
        self.assertEqual(len(engine.validate_packs()), 2)
        self.assertEqual(len(engine.verify_provenance()), 2)


if __name__ == "__main__":
    unittest.main()
