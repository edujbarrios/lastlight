from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.adaptive import AdaptiveRetrievalStrategy as LegacyAdaptive
from lastlight.composite_repository import CompositeKnowledgeRepository as LegacyComposite
from lastlight.repository import MarkdownKnowledgeRepository as LegacyRepository
from lastlight.retrieval import LexicalRetrievalStrategy as LegacyLexical
from lastlight.knowledge.composite_repository import CompositeKnowledgeRepository
from lastlight.knowledge.repository import MarkdownKnowledgeRepository
from lastlight.retrieval.adaptive import AdaptiveRetrievalStrategy
from lastlight.retrieval.strategies import LexicalRetrievalStrategy
from lastlight.retrieval.tokenizer import tokenize


class PackageLayoutTests(unittest.TestCase):
    def test_retrieval_package_is_primary_implementation(self) -> None:
        self.assertIs(LegacyAdaptive, AdaptiveRetrievalStrategy)
        self.assertIs(LegacyLexical, LexicalRetrievalStrategy)
        self.assertEqual(tokenize("Safe drinking water"), ["safe", "drinking", "water"])

    def test_knowledge_package_is_primary_implementation(self) -> None:
        self.assertIs(LegacyComposite, CompositeKnowledgeRepository)
        self.assertIs(LegacyRepository, MarkdownKnowledgeRepository)


if __name__ == "__main__":
    unittest.main()
