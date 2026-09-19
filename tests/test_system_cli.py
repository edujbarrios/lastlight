from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight import cli


class SystemCliTests(unittest.TestCase):
    def test_benchmark_routes_without_creating_query_app(self) -> None:
        with patch.object(cli.DeviceBenchmarkCommand, "execute", return_value=0) as execute:
            with patch.object(cli.ApplicationFactory, "create") as create:
                with redirect_stdout(io.StringIO()):
                    exit_code = cli.main(
                        [
                            "--benchmark",
                            "--benchmark-max-cases",
                            "12",
                            "--benchmark-energy-source",
                            "estimate",
                            "--benchmark-watts",
                            "5",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        execute.assert_called_once_with()
        create.assert_not_called()

    def test_verify_provenance_routes_without_creating_query_app(self) -> None:
        with patch.object(cli.VerifyProvenanceCommand, "execute", return_value=0) as execute:
            with patch.object(cli.ApplicationFactory, "create") as create:
                with redirect_stdout(io.StringIO()):
                    exit_code = cli.main(
                        [
                            "--verify-provenance",
                            "--provenance-json",
                            "--stale-after-days",
                            "180",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        execute.assert_called_once_with()
        create.assert_not_called()

    def test_rejects_zero_benchmark_cases(self) -> None:
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                cli.main(["--benchmark", "--benchmark-max-cases", "0"])

    def test_rejects_zero_stale_threshold(self) -> None:
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                cli.main(["--verify-provenance", "--stale-after-days", "0"])


if __name__ == "__main__":
    unittest.main()
