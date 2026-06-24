from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight.local_model import (
    build_local_model,
    summarize_local_model,
    write_local_model,
)
from lastlight.repository import MarkdownKnowledgeRepository


class LocalModelTests(unittest.TestCase):
    def test_builds_tiny_ngram_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text("Water purification means boil water.", encoding="utf-8")

            model = build_local_model(MarkdownKnowledgeRepository(root), order=2)

        self.assertEqual(model["model_type"], "word-ngram")
        self.assertEqual(model["order"], 2)
        self.assertGreater(model["transition_count"], 0)

    def test_writes_and_summarizes_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            root.mkdir()
            (root / "doc.md").write_text("Battery saving preserves power.", encoding="utf-8")
            output = Path(tmp) / "model.json"

            write_local_model(MarkdownKnowledgeRepository(root), output)
            data = json.loads(output.read_text(encoding="utf-8"))
            summary = summarize_local_model(output)

        self.assertEqual(data["document_count"], 1)
        self.assertIn("LastLight local model", summary)
        self.assertIn("Transitions:", summary)


if __name__ == "__main__":
    unittest.main()

