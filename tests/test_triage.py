from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.triage import append_follow_up_questions, suggest_follow_up_questions


def result(
    body: str = "Boil water when it may be unsafe.",
    confidence: str = "HIGH",
    tags: tuple[str, ...] = ("water", "purification"),
) -> SearchResult:
    return SearchResult(
        document=KnowledgeDocument(
            title="Water Purification",
            path="knowledge/en/water.md",
            body=body,
            tags=tags,
        ),
        score=2.0,
        confidence=confidence,
        passage="Boil water before drinking.",
        matched_terms=("water",),
    )


class TriageTests(unittest.TestCase):
    def test_suggests_domain_specific_questions(self) -> None:
        questions = suggest_follow_up_questions(result())

        self.assertIn("Does the water smell like fuel, chemicals, sewage, or solvents?", questions)
        self.assertEqual(len(questions), 2)

    def test_skips_low_confidence_results(self) -> None:
        self.assertEqual(suggest_follow_up_questions(result(confidence="LOW")), ())

    def test_appends_checks_to_accepted_answer(self) -> None:
        answer = append_follow_up_questions("Boil water before drinking.", result())

        self.assertIn("Boil water before drinking.", answer)
        self.assertIn("Follow-up checks:", answer)


if __name__ == "__main__":
    unittest.main()
