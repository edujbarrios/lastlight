from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.adaptive import AdaptiveRetrievalStrategy as LegacyAdaptive
from lastlight.app import LastLightApp as LegacyApp
from lastlight.composite_repository import CompositeKnowledgeRepository as LegacyComposite
from lastlight.factory import ApplicationFactory as LegacyFactory
from lastlight.repository import MarkdownKnowledgeRepository as LegacyRepository
from lastlight.retrieval import LexicalRetrievalStrategy as LegacyLexical
from lastlight.application.app import LastLightApp
from lastlight.application.factory import ApplicationFactory
from lastlight.cli import build_parser, main
from lastlight.knowledge.composite_repository import CompositeKnowledgeRepository
from lastlight.knowledge.repository import MarkdownKnowledgeRepository
from lastlight.retrieval.adaptive import AdaptiveRetrievalStrategy
from lastlight.retrieval.strategies import LexicalRetrievalStrategy
from lastlight.retrieval.tokenizer import tokenize
from lastlight.safety import safe_answer
from lastlight.shared.domain import SearchQuery


class PackageLayoutTests(unittest.TestCase):
    def test_retrieval_package_is_primary_implementation(self) -> None:
        self.assertIs(LegacyAdaptive, AdaptiveRetrievalStrategy)
        self.assertIs(LegacyLexical, LexicalRetrievalStrategy)
        self.assertEqual(tokenize("Safe drinking water"), ["safe", "drinking", "water"])

    def test_knowledge_package_is_primary_implementation(self) -> None:
        self.assertIs(LegacyComposite, CompositeKnowledgeRepository)
        self.assertIs(LegacyRepository, MarkdownKnowledgeRepository)

    def test_application_package_preserves_public_imports(self) -> None:
        self.assertIs(LegacyApp, LastLightApp)
        self.assertIs(LegacyFactory, ApplicationFactory)
        self.assertTrue(callable(main))
        self.assertEqual(build_parser().prog, "lastlight")
        self.assertTrue(callable(safe_answer))
        self.assertEqual(SearchQuery("water").text, "water")


if __name__ == "__main__":
    unittest.main()
