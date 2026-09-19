from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli


class AdaptiveCliTests(unittest.TestCase):
    def test_adaptive_cli_passes_resource_policy_to_factory(self) -> None:
        with patch.object(cli.ApplicationFactory, "create") as create:
            app = create.return_value
            app.search.return_value = []
            app.retrieval_metadata.return_value = {
                "strategy": "lexical",
                "mode": "survival",
                "risk": "high",
                "effective_top_k": 2,
                "reason": "survival mode caps retrieval cost",
            }
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = cli.main(
                    [
                        "--strategy",
                        "adaptive",
                        "--mode",
                        "survival",
                        "--energy-budget-mwh",
                        "0.4",
                        "--memory-budget-mb",
                        "64",
                        "--plan",
                        "water",
                    ]
                )

        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            knowledge_dir=None,
            strategy="adaptive",
            language=None,
            mode="survival",
            energy_budget_mwh=0.4,
            memory_budget_mb=64,
        )
        app.search.assert_called_once_with("water", top_k=3)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["strategy"], "lexical")
        self.assertEqual(payload["risk"], "high")

    def test_plan_requires_query(self) -> None:
        with patch.object(cli.ApplicationFactory, "create"):
            with self.assertRaises(SystemExit):
                with redirect_stdout(io.StringIO()):
                    with redirect_stderr(io.StringIO()):
                        cli.main(["--strategy", "adaptive", "--plan"])

    def test_rejects_non_positive_energy_budget(self) -> None:
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                with redirect_stderr(io.StringIO()):
                    cli.main(
                        [
                            "--strategy",
                            "adaptive",
                            "--energy-budget-mwh",
                            "0",
                            "water",
                        ]
                    )


if __name__ == "__main__":
    unittest.main()
