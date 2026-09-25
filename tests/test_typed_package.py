from __future__ import annotations

import unittest
from importlib.resources import files
from typing import get_args

import helpers  # noqa: F401
from lastlight import AdaptiveMode, RefusalReason, RetrievalStrategyName, __version__


class TypedPackageTests(unittest.TestCase):
    def test_pep561_marker_is_packaged_with_lastlight(self) -> None:
        self.assertTrue(files("lastlight").joinpath("py.typed").is_file())

    def test_public_literal_contracts_are_exported(self) -> None:
        self.assertEqual(set(get_args(RetrievalStrategyName)), {"lexical", "bm25", "adaptive"})
        self.assertEqual(set(get_args(AdaptiveMode)), {"survival", "balanced", "accuracy"})
        self.assertEqual(
            set(get_args(RefusalReason)),
            {"no_matching_knowledge", "insufficient_confidence"},
        )

    def test_release_version_is_0_1_4(self) -> None:
        self.assertEqual(__version__, "0.1.4")


if __name__ == "__main__":
    unittest.main()
