"""CLI resource budgets must reject NaN and infinity before policy selection."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli


class CliBudgetValidationTests(unittest.TestCase):
    def test_rejects_nonfinite_energy_budgets(self) -> None:
        for value in ("nan", "NaN", "inf", "-inf", "Infinity"):
            with self.subTest(value=value):
                with patch.object(cli.ApplicationFactory, "create") as factory:
                    with redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            cli.main([
                                "--strategy", "adaptive",
                                "--energy-budget-mwh", value,
                                "water",
                            ])
                self.assertEqual(error.exception.code, 2)
                factory.assert_not_called()

    def test_accepts_finite_positive_energy_budget(self) -> None:
        self.assertEqual(cli.positive_float("0.001"), 0.001)
        self.assertEqual(cli.positive_float("100"), 100.0)


if __name__ == "__main__":
    unittest.main()
