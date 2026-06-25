from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

import helpers  # noqa: F401
from lastlight.commands import ListKnowledgeCommand
from lastlight.domain import KnowledgeDocument
from lastlight.interfaces import KnowledgeRepository


class MixedRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Agua",
                path="knowledge/es/water.md",
                body="Hervir agua.",
                language="es",
                tags=("agua",),
                priority="high",
            ),
            KnowledgeDocument(
                title="Battery",
                path="knowledge/en/battery.md",
                body="Save battery.",
                language="en",
                tags=("energy",),
                priority="normal",
            ),
        ]


class EmptyRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return []


class ListKnowledgeTests(unittest.TestCase):
    def test_lists_documents(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = ListKnowledgeCommand(MixedRepository()).execute()

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("en | normal | Battery | energy | knowledge/en/battery.md", text)
        self.assertIn("es | high | Agua | agua | knowledge/es/water.md", text)

    def test_filters_by_language(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            ListKnowledgeCommand(MixedRepository(), language="es").execute()

        text = output.getvalue()
        self.assertIn("Agua", text)
        self.assertNotIn("Battery", text)

    def test_empty_repository_is_clear(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            ListKnowledgeCommand(EmptyRepository()).execute()

        self.assertEqual(output.getvalue().strip(), "No knowledge documents found.")


if __name__ == "__main__":
    unittest.main()
