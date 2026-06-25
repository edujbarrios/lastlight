from __future__ import annotations

import unittest

import helpers  # noqa: F401
from lastlight.web import parse_query, parse_query_string, render_page


class WebTests(unittest.TestCase):
    def test_parse_query_trims_form_value(self) -> None:
        self.assertEqual(parse_query(b"q=%20water%20purification%20"), "water purification")

    def test_parse_query_string_trims_url_value(self) -> None:
        self.assertEqual(parse_query_string("/?q=%20find%20north%20"), "find north")

    def test_render_page_escapes_query_and_answer(self) -> None:
        html = render_page("<query>", "<answer>").decode("utf-8")

        self.assertIn("&lt;query&gt;", html)
        self.assertIn("&lt;answer&gt;", html)
        self.assertNotIn("<query>", html)
        self.assertNotIn("<answer>", html)


if __name__ == "__main__":
    unittest.main()
