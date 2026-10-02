from __future__ import annotations

import unittest
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.domain import KnowledgeDocument, SearchQuery
from lastlight.retrieval import BM25RetrievalStrategy, LexicalRetrievalStrategy, select_passage
from lastlight.retrieval.ranking import prepare_bm25_corpus


def _long_first_aid_guide() -> KnowledgeDocument:
    filler = "General preparedness information and routine supplies. " * 120
    body = (
        "# First Aid Field Guide\n\n"
        f"{filler}\n\n"
        "## Burns\n\nCool a minor burn with clean running water.\n\n"
        "## Severe bleeding\n\n"
        "### Tourniquet use\n\n"
        "For life-threatening limb bleeding that cannot be controlled with direct pressure, "
        "apply a tourniquet according to the guide and seek emergency help.\n\n"
        "## Fractures\n\nImmobilize the injured area and avoid unnecessary movement."
    )
    return KnowledgeDocument(
        title="First Aid Field Guide",
        path="knowledge/medical/first-aid.md",
        body=body,
        tags=("first-aid", "medical"),
        priority="high",
    )


class RetrievalTests(unittest.TestCase):
    def test_ranks_relevant_document_first(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Water Purification",
                path="knowledge/water/purification.md",
                body="Boil contaminated water at a rolling boil.",
                tags=("water", "purification"),
                priority="high",
            ),
            KnowledgeDocument(
                title="Compass",
                path="knowledge/navigation/compass.md",
                body="Keep compass away from metal.",
                tags=("navigation", "compass"),
            ),
        ]

        results = LexicalRetrievalStrategy().search(SearchQuery("purify water", 2), docs)

        self.assertEqual(results[0].document.title, "Water Purification")
        self.assertIn(results[0].confidence, {"HIGH", "MEDIUM"})

    def test_returns_empty_for_unmatched_query(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Compass",
                path="knowledge/navigation/compass.md",
                body="Keep compass away from metal.",
                tags=("navigation",),
            )
        ]

        results = LexicalRetrievalStrategy().search(SearchQuery("satellite firmware", 2), docs)

        self.assertEqual(results, [])

    def test_bm25_ranks_relevant_document_first(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Battery Saving",
                path="knowledge/energy/battery_saving.md",
                body="Reduce phone screen brightness and use low power mode.",
                tags=("battery", "phone"),
                priority="high",
            ),
            KnowledgeDocument(
                title="Burns",
                path="knowledge/medical/burns.md",
                body="Cool burns with clean water.",
                tags=("burns",),
            ),
        ]

        results = BM25RetrievalStrategy().search(SearchQuery("save phone battery", 2), docs)

        self.assertEqual(results[0].document.title, "Battery Saving")
        self.assertIn(results[0].confidence, {"HIGH", "MEDIUM"})

    def test_bm25_reuses_prepared_statistics_for_equivalent_corpus(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Battery Saving",
                path="knowledge/energy/battery_saving.md",
                body="Reduce phone screen brightness and use low power mode.",
                tags=("battery", "phone"),
                priority="high",
            ),
            KnowledgeDocument(
                title="Burns",
                path="knowledge/medical/burns.md",
                body="Cool burns with clean water.",
                tags=("burns",),
            ),
        ]
        reloaded_docs = [
            KnowledgeDocument(
                title=document.title,
                path=document.path,
                body=document.body,
                source_sha256=document.source_sha256,
                language=document.language,
                tags=document.tags,
                priority=document.priority,
            )
            for document in docs
        ]
        strategy = BM25RetrievalStrategy()

        with patch(
            "lastlight.retrieval.strategies.prepare_bm25_corpus",
            wraps=prepare_bm25_corpus,
        ) as prepare:
            strategy.search(SearchQuery("save phone battery", 2), docs)
            strategy.search(SearchQuery("clean water", 2), reloaded_docs)

        self.assertEqual(prepare.call_count, 1)

    def test_bm25_rebuilds_prepared_statistics_when_content_changes(self) -> None:
        docs = [
            KnowledgeDocument(
                title="Battery Saving",
                path="knowledge/energy/battery_saving.md",
                body="Reduce phone screen brightness and use low power mode.",
                tags=("battery", "phone"),
            )
        ]
        changed_docs = [
            KnowledgeDocument(
                title="Battery Saving",
                path="knowledge/energy/battery_saving.md",
                body="Disconnect the battery before electrical maintenance.",
                tags=("battery", "phone"),
            )
        ]
        strategy = BM25RetrievalStrategy()

        with patch(
            "lastlight.retrieval.strategies.prepare_bm25_corpus",
            wraps=prepare_bm25_corpus,
        ) as prepare:
            strategy.search(SearchQuery("save phone battery", 1), docs)
            strategy.search(SearchQuery("electrical maintenance", 1), changed_docs)

        self.assertEqual(prepare.call_count, 2)

    def test_lexical_ranks_long_markdown_guide_by_relevant_section(self) -> None:
        guide = _long_first_aid_guide()

        results = LexicalRetrievalStrategy().search(
            SearchQuery("tourniquet severe bleeding", 1),
            [guide],
        )

        self.assertEqual(results[0].document, guide)
        self.assertIn("life-threatening limb bleeding", results[0].passage)
        self.assertNotIn("General preparedness information", results[0].passage)

    def test_bm25_builds_statistics_over_sections_for_long_markdown_guide(self) -> None:
        guide = _long_first_aid_guide()
        strategy = BM25RetrievalStrategy()

        with patch(
            "lastlight.retrieval.strategies.prepare_bm25_corpus",
            wraps=prepare_bm25_corpus,
        ) as prepare:
            results = strategy.search(SearchQuery("tourniquet severe bleeding", 1), [guide])

        ranked_documents = prepare.call_args.args[0]
        self.assertGreater(len(ranked_documents), 1)
        self.assertTrue(any("Tourniquet use" in doc.title for doc in ranked_documents))
        self.assertEqual(results[0].document, guide)
        self.assertIn("apply a tourniquet", results[0].passage)

    def test_select_passage_prefers_best_sentence_window(self) -> None:
        body = (
            "General preparation matters. Keep supplies organized.\n\n"
            "If you need direction, use the shadow stick method. "
            "Mark the first shadow tip, wait, then mark the second tip. "
            "The line gives an approximate west to east direction.\n\n"
            "Unrelated radio instructions follow."
        )

        passage = select_passage(body, "shadow stick direction", max_chars=170)

        self.assertIn("shadow stick method", passage)
        self.assertIn("west to east direction", passage)
        self.assertLessEqual(len(passage), 170)


if __name__ == "__main__":
    unittest.main()
