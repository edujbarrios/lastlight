from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchResult
from lastlight.triage import append_follow_up_questions, suggest_follow_up_questions


def result(
    body: str = "Boil water when it may be unsafe.",
    confidence: str = "HIGH",
    tags: tuple[str, ...] = ("water", "purification"),
    language: str = "en",
) -> SearchResult:
    return SearchResult(
        document=KnowledgeDocument(
            title="Water Purification",
            path=f"knowledge/{language}/water.md",
            body=body,
            tags=tags,
            language=language,
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

    def test_localizes_follow_up_checks_for_spanish_results(self) -> None:
        spanish = result(
            body="Hierve el agua antes de beberla.",
            tags=("agua", "purification"),
            language="es",
        )

        questions = suggest_follow_up_questions(spanish)
        answer = append_follow_up_questions("Hierve el agua.", spanish)

        self.assertIn(
            "¿El agua huele a combustible, productos químicos, aguas residuales o disolventes?",
            questions,
        )
        self.assertIn("Comprobaciones de seguimiento:", answer)
        self.assertNotIn("Follow-up checks:", answer)


if __name__ == "__main__":
    unittest.main()
