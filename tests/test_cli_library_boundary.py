from __future__ import annotations

import unittest
from pathlib import Path

import helpers  # noqa: F401
from lastlight import LastLight
from lastlight.cli.factory import ApplicationFactory


EXAMPLE_PACK = (
    Path(__file__).resolve().parents[1]
    / "examplepack"
    / "lastlight-example-en.zip"
)


class CliLibraryBoundaryTests(unittest.TestCase):
    def test_cli_factory_constructs_public_lastlight_facade(self) -> None:
        app = ApplicationFactory.create(EXAMPLE_PACK)

        self.assertIsInstance(app, LastLight)
        result = app.query("How long will food stay cold during a power outage?")
        self.assertTrue(result.sources)


if __name__ == "__main__":
    unittest.main()
