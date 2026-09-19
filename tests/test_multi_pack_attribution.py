from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.safety import format_result, result_to_dict


class MultiPackAttributionTests(unittest.TestCase):
    def _result(self) -> SearchResult:
        document = KnowledgeDocument(
            title="Water Purification",
            path="water.md",
            body="Boil water.",
            language="en",
            pack_name="water-pack",
            pack_version="1.2.0",
            pack_source="https://example.org/water",
            pack_path="water-pack.zip",
        )
        return SearchResult(document, 2.0, "HIGH", "Boil water.")

    def test_text_answer_identifies_source_pack(self) -> None:
        rendered = format_result(self._result())
        self.assertIn("Pack: water-pack 1.2.0", rendered)
        self.assertIn("Source: water.md", rendered)

    def test_json_result_includes_pack_metadata(self) -> None:
        payload = result_to_dict(self._result())
        self.assertEqual(payload["pack"]["name"], "water-pack")
        self.assertEqual(payload["pack"]["version"], "1.2.0")
        self.assertEqual(payload["pack"]["path"], "water-pack.zip")


if __name__ == "__main__":
    unittest.main()
