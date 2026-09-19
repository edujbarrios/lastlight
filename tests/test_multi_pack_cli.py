from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli
from lastlight.composite_repository import CompositeKnowledgeRepository
from lastlight.factory import ApplicationFactory


class MultiPackCliTests(unittest.TestCase):
    def test_query_forwards_multiple_knowledge_sources(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            create.return_value.answer.return_value = "answer"
            with redirect_stdout(io.StringIO()):
                exit_code = cli.main(
                    [
                        "--knowledge",
                        "water.zip",
                        "--knowledge",
                        "first-aid.zip",
                        "purify water",
                    ]
                )

        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            knowledge_dir=["water.zip", "first-aid.zip"],
            strategy="lexical",
            language=None,
        )

    def test_single_knowledge_source_keeps_backwards_compatible_factory_value(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            create.return_value.answer.return_value = "answer"
            with redirect_stdout(io.StringIO()):
                exit_code = cli.main(["--knowledge", "water.zip", "water"])

        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            knowledge_dir="water.zip", strategy="lexical", language=None
        )

    def test_pack_specific_operation_rejects_multiple_sources(self) -> None:
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                cli.main(
                    [
                        "--knowledge",
                        "one.zip",
                        "--knowledge",
                        "two.zip",
                        "--verify-provenance",
                    ]
                )

    def test_factory_builds_composite_repository_for_multiple_sources(self) -> None:
        app = ApplicationFactory.create(["one.zip", "two.zip"])
        self.assertIsInstance(app.repository, CompositeKnowledgeRepository)
        self.assertEqual(app.repository.pack_count, 2)


if __name__ == "__main__":
    unittest.main()
