from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.synthesis import SYNTHESIS_WARNING, synthesize_answer


class SynthesisTests(unittest.TestCase):
    def test_synthesis_includes_citation_and_passage(self) -> None:
        doc = KnowledgeDocument(
            title="Water Purification",
            path="knowledge/water/purification.md",
            body="Boil water before drinking.",
            tags=("water",),
            language="en",
        )
        result = SearchResult(
            document=doc,
            score=2.0,
            confidence="HIGH",
            passage="Boil water before drinking.",
        )

        answer = synthesize_answer("boil water", [result])

        self.assertIn(SYNTHESIS_WARNING, answer)
        self.assertIn("Source: knowledge/water/purification.md", answer)
        self.assertIn("Retrieved passage:\nBoil water before drinking.", answer)


if __name__ == "__main__":
    unittest.main()

