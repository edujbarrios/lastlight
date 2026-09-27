from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import helpers  # noqa: F401
from lastlight.compat import format_self_check, is_low_resource_target, run_self_check
from lastlight.domain import KnowledgeDocument
from lastlight.interfaces import KnowledgeRepository


class FakeRepository(KnowledgeRepository):
    def list_documents(self) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                title="Doc",
                path="knowledge/doc.md",
                body="Body",
            )
        ]


class CompatTests(unittest.TestCase):
    def test_self_check_reports_knowledge_and_dependencies(self) -> None:
        results = run_self_check(FakeRepository())
        names = {result.name for result in results}

        self.assertIn("knowledge", names)
        self.assertIn("dependencies", names)
        self.assertTrue(all(result.ok for result in results))

    def test_formats_self_check(self) -> None:
        output = format_self_check(run_self_check(FakeRepository()))

        self.assertIn("LastLight self-check", output)
        self.assertIn("[OK] knowledge", output)

    def test_arm64_is_not_assumed_to_be_low_resource(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            for machine in ("arm64", "aarch64"):
                with self.subTest(machine=machine):
                    with patch(
                        "lastlight.shared.compat.platform.machine",
                        return_value=machine,
                    ):
                        self.assertFalse(is_low_resource_target())

    def test_32_bit_arm_remains_a_low_resource_signal(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            for machine in ("armv7l", "armv8l", "armhf"):
                with self.subTest(machine=machine):
                    with patch(
                        "lastlight.shared.compat.platform.machine",
                        return_value=machine,
                    ):
                        self.assertTrue(is_low_resource_target())

    def test_termux_remains_low_resource_on_arm64(self) -> None:
        with patch.dict(os.environ, {"TERMUX_VERSION": "0.120"}, clear=True):
            with patch(
                "lastlight.shared.compat.platform.machine",
                return_value="aarch64",
            ):
                self.assertTrue(is_low_resource_target())


if __name__ == "__main__":
    unittest.main()

