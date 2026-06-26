from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli


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
        app.answer.assert_called_once_with("hello")

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
        app.answer.assert_called_once_with("hola")

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


if __name__ == "__main__":
    unittest.main()
