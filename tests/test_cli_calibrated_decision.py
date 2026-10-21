"""CLI output modes must agree with the calibrated answer-decision boundary."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli
from lastlight.domain import KnowledgeDocument, SearchResult


def _ambiguous_results() -> list[SearchResult]:
    doc = KnowledgeDocument(
        title="Water storage", path="water.md",
        body="Sourced water storage guidance.", tags=("water",)
    )
    other = KnowledgeDocument(
        title="Supply storage", path="other.md",
        body="Sourced storage guidance.", tags=("storage",)
    )
    return [
        SearchResult(doc, 1.10, "MEDIUM", doc.body, matched_terms=("water",)),
        SearchResult(other, 1.00, "MEDIUM", other.body, matched_terms=("storage",)),
    ]


QUERY = "water treatment storage emergency supply"


class CalibratedCliDecisionTests(unittest.TestCase):
    def test_json_refuses_ambiguous_medium_confidence(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as factory:
            factory.return_value.search.return_value = _ambiguous_results()
            output = io.StringIO()
            with redirect_stdout(output):
                code = cli.main(["--format", "json", "--fail-on-refusal", QUERY])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(payload["accepted"])
        self.assertIn("not have enough confidence", payload["answer"])
        self.assertNotIn("Sourced water storage guidance.", payload["answer"])

    def test_sources_exit_code_respects_calibrated_refusal(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as factory:
            factory.return_value.search.return_value = _ambiguous_results()
            with redirect_stdout(io.StringIO()):
                code = cli.main(["--format", "sources", "--fail-on-refusal", QUERY])
        self.assertEqual(code, 2)

    def test_batch_refuses_same_ambiguous_query(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "queries.txt"
            source.write_text(QUERY + "\n", encoding="utf-8")
            with patch.object(cli.ApplicationFactory, "create") as factory:
                factory.return_value.search.return_value = _ambiguous_results()
                output = io.StringIO()
                with redirect_stdout(output):
                    code = cli.main(["--query-file", str(source)])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue().strip())
        self.assertFalse(payload["accepted"])
        self.assertIn("not have enough confidence", payload["answer"])

    def test_field_guide_refuses_same_ambiguous_query(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "queries.txt"
            guide = Path(folder) / "guide.md"
            source.write_text(QUERY + "\n", encoding="utf-8")
            with patch.object(cli.ApplicationFactory, "create") as factory:
                factory.return_value.search.return_value = _ambiguous_results()
                with redirect_stdout(io.StringIO()):
                    code = cli.main(["--query-file", str(source), "--field-guide", str(guide)])
            content = guide.read_text(encoding="utf-8")
        self.assertEqual(code, 2)
        self.assertIn("not have enough confidence", content)
        self.assertNotIn("Sourced water storage guidance.", content)


if __name__ == "__main__":
    unittest.main()
