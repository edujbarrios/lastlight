from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.safety import LOW_CONFIDENCE_RESPONSE, safe_answer


class SafetyTests(unittest.TestCase):
    def test_refuses_low_confidence(self) -> None:
        doc = KnowledgeDocument(title="Doc", path="doc.md", body="Body")
        answer = safe_answer([
            SearchResult(document=doc, score=0.1, confidence="LOW", passage="Body")
        ])

        self.assertIn(LOW_CONFIDENCE_RESPONSE, answer)

    def test_includes_source_for_accepted_answer(self) -> None:
        doc = KnowledgeDocument(
            title="Water",
            path="knowledge/water/purification.md",
            body="Boil water.",
            tags=("water",),
            language="en",
        )
        answer = safe_answer([
            SearchResult(document=doc, score=2.0, confidence="HIGH", passage="Boil water.")
        ])

        self.assertIn("Source: knowledge/water/purification.md", answer)
        self.assertIn("[HIGH CONFIDENCE]", answer)


if __name__ == "__main__":
    unittest.main()

