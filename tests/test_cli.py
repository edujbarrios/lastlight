from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli
from lastlight.domain import KnowledgeDocument, SearchResult


class CliTests(unittest.TestCase):
    def test_pack_info_does_not_create_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text("Body.", encoding="utf-8")

            with patch.object(cli.ApplicationFactory, "create") as create:
                with redirect_stdout(io.StringIO()):
                    exit_code = cli.main(["--knowledge", str(root), "--pack-info"])

        self.assertEqual(exit_code, 0)
        create.assert_not_called()

    def test_list_knowledge_does_not_create_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text("Body.", encoding="utf-8")

            with patch.object(cli.ApplicationFactory, "create") as create:
                with redirect_stdout(io.StringIO()):
                    exit_code = cli.main(
                        ["--knowledge", str(root), "--list-knowledge"]
                    )

        self.assertEqual(exit_code, 0)
        create.assert_not_called()

    def test_query_creates_application(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            app = create.return_value
            app.answer.return_value = "answer"

            with redirect_stdout(io.StringIO()):
                exit_code = cli.main(["hello"])

        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            knowledge_dir=None, strategy="lexical", language=None
        )
        app.answer.assert_called_once_with("hello", top_k=3)

    def test_query_passes_language_filter(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            app = create.return_value
            app.answer.return_value = "answer"

            with redirect_stdout(io.StringIO()):
                exit_code = cli.main(["--language", "es", "hola"])

        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            knowledge_dir=None, strategy="lexical", language="es"
        )
        app.answer.assert_called_once_with("hola", top_k=3)

    def test_query_passes_top_k(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            app = create.return_value
            app.answer.return_value = "answer"

            with redirect_stdout(io.StringIO()):
                exit_code = cli.main(["--top-k", "5", "hello"])

        self.assertEqual(exit_code, 0)
        app.answer.assert_called_once_with("hello", top_k=5)

    def test_rejects_non_positive_top_k(self) -> None:
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                with redirect_stderr(io.StringIO()):
                    cli.main(["--top-k", "0", "hello"])

    def test_query_json_output_is_machine_readable(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            app = create.return_value
            app.search.return_value = []
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = cli.main(["--format", "json", "unknown"])

        self.assertEqual(exit_code, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["query"], "unknown")
        self.assertFalse(data["accepted"])
        self.assertEqual(data["results"], [])

    def test_query_sources_output_lists_ranked_sources(self) -> None:
        document = KnowledgeDocument(
            title="Water",
            path="knowledge/en/water/purification.md",
            body="Boil water.",
            tags=("water",),
        )
        with patch.object(cli.ApplicationFactory, "create") as create:
            app = create.return_value
            app.search.return_value = [
                SearchResult(
                    document=document,
                    score=2.0,
                    confidence="HIGH",
                    passage="Boil water.",
                )
            ]
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = cli.main(["--format", "sources", "water"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Sources for: water", output.getvalue())
        self.assertIn("knowledge/en/water/purification.md", output.getvalue())

    def test_serve_creates_application_and_runs_server_command(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            with patch.object(cli.ServeCommand, "execute", return_value=0) as execute:
                exit_code = cli.main(["--serve", "--host", "127.0.0.1", "--port", "9999"])

        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            knowledge_dir=None, strategy="lexical", language=None
        )
        execute.assert_called_once_with()

    def test_import_pdf_does_not_create_application(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            with patch.object(cli.ImportPdfCommand, "execute", return_value=0) as execute:
                exit_code = cli.main(
                    [
                        "--import-pdf",
                        "guide.pdf",
                        "--import-output",
                        "knowledge/en/imported/guide.md",
                        "--language",
                        "en",
                        "--import-tags",
                        "imported,pdf,water",
                        "--import-priority",
                        "high",
                        "--import-summary-items",
                        "3",
                    ]
                )

        self.assertEqual(exit_code, 0)
        create.assert_not_called()
        execute.assert_called_once_with()

    def test_export_pack_passes_require_valid_flag(self) -> None:
        with patch.object(cli, "ExportPackCommand") as command_class:
            command_class.return_value.execute.return_value = 0
            with redirect_stdout(io.StringIO()):
                exit_code = cli.main([
                    "--export-pack",
                    "dist/pack.zip",
                    "--require-valid-pack",
                ])

        self.assertEqual(exit_code, 0)
        self.assertTrue(command_class.call_args.kwargs["require_valid"])


if __name__ == "__main__":
    unittest.main()
