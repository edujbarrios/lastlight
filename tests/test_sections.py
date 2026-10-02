from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.retrieval.sections import MarkdownSection, markdown_sections


class MarkdownSectionTests(unittest.TestCase):
    def test_preserves_heading_hierarchy(self) -> None:
        sections = markdown_sections(
            "# Field Guide\n\nIntro text.\n\n"
            "## Bleeding\n\nGeneral bleeding guidance.\n\n"
            "### Tourniquet use\n\nUse only for severe bleeding.\n\n"
            "## Burns\n\nCool the burn."
        )

        self.assertEqual(
            sections,
            [
                MarkdownSection(("Field Guide",), "Intro text."),
                MarkdownSection(("Field Guide", "Bleeding"), "General bleeding guidance."),
                MarkdownSection(
                    ("Field Guide", "Bleeding", "Tourniquet use"),
                    "Use only for severe bleeding.",
                ),
                MarkdownSection(("Field Guide", "Burns"), "Cool the burn."),
            ],
        )

    def test_retains_preamble_before_first_heading(self) -> None:
        sections = markdown_sections("Important preface.\n\n# Guide\n\nGuidance.")

        self.assertEqual(sections[0], MarkdownSection((), "Important preface."))
        self.assertEqual(sections[1], MarkdownSection(("Guide",), "Guidance."))

    def test_ignores_heading_like_lines_inside_code_fences(self) -> None:
        sections = markdown_sections(
            "# Guide\n\nBefore.\n\n"
            "```markdown\n## Not a real section\nexample\n```\n\n"
            "## Real section\n\nAfter."
        )

        self.assertEqual(len(sections), 2)
        self.assertIn("## Not a real section", sections[0].body)
        self.assertEqual(sections[1].heading_path, ("Guide", "Real section"))

    def test_omits_empty_parent_sections(self) -> None:
        sections = markdown_sections("# Guide\n## Topic\n### Detail\nUseful text.")

        self.assertEqual(
            sections,
            [MarkdownSection(("Guide", "Topic", "Detail"), "Useful text.")],
        )


if __name__ == "__main__":
    unittest.main()
