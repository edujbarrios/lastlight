from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.compat import format_self_check, run_self_check
from lastlight.domain import KnowledgeDocument
from lastlight.interfaces import KnowledgeRepository


class FakeRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Doc",
                path="knowledge/doc.md",
                body="Body",
            )
        ]


class CompatTests(unittest.TestCase):
    def test_self_check_reports_knowledge_and_dependencies(self) -> None:
        results = run_self_check(FakeRepository())
        names = {result.name for result in results}

        self.assertIn("knowledge", names)
        self.assertIn("dependencies", names)
        self.assertTrue(all(result.ok for result in results))

    def test_formats_self_check(self) -> None:
        output = format_self_check(run_self_check(FakeRepository()))

        self.assertIn("LastLight self-check", output)
        self.assertIn("[OK] knowledge", output)


if __name__ == "__main__":
    unittest.main()

