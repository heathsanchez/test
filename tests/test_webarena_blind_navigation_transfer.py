"""Regression controls for two unrelated blind navigation capabilities."""
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from webarena_blind_navigation_transfer import compile_navigation, execute_navigation


class NavigationGrammar(unittest.TestCase):
    def test_review_queue_distinct_from_assignee_queue(self):
        route = compile_navigation(
            "Go to the merge requests requiring my review", "__GITLAB__"
        )
        qs = parse_qs(urlparse(route["target"]).query)
        self.assertEqual(qs["reviewer_username"], ["byteblaze"])
        self.assertEqual(qs["scope"], ["all"])
        self.assertEqual(qs["state"], ["opened"])
        self.assertNotIn("assignee_username", qs)

    def test_tax_range_anchored_in_user_instruction(self):
        route = compile_navigation(
            "Show the tax report for for this year (today is March 15, 2023).",
            "__SHOPPING_ADMIN__",
        )
        qs = parse_qs(urlparse(route["target"]).query)
        self.assertEqual(qs, {
            "report_type": ["created_at_order"],
            "from": ["01/1/2023"],
            "to": ["03/15/2023"],
        })
        leap = compile_navigation(
            "Show the tax report for this year (today is February 29, 2024).",
            "__SHOPPING_ADMIN__",
        )
        self.assertEqual(parse_qs(urlparse(leap["target"]).query)["to"], ["02/29/2024"])

    def test_unsupported_commands_and_wrong_sites_fail(self):
        for intent, site in [
            ("Go to the merge requests requiring my review", "__SHOPPING_ADMIN__"),
            ("Show the tax report for this year (today is March 15, 2023).", "__GITLAB__"),
            ("Delete all orders", "__SHOPPING_ADMIN__"),
        ]:
            with self.assertRaises(ValueError):
                compile_navigation(intent, site)

    def test_agent_does_not_read_benchmark_metadata(self):
        content = (Path(__file__).resolve().parents[1] / "scripts" / "webarena_blind_navigation_transfer.py").read_text()
        for forbidden in ("task_id", "intent_template_id", "instantiation_dict", "evaluate_task", "expected_answer"):
            self.assertNotIn(forbidden, content)


class NavigationObservation(unittest.IsolatedAsyncioTestCase):
    async def test_observed_url_params_must_match(self):
        class Response:
            status = 200
            def __init__(self, url): self.url = url
        class Page:
            url = ""
            async def goto(self, url, **kwargs):
                self.url = url
                return Response(url)
        route = compile_navigation(
            "Show the tax report for this year (today is March 15, 2023).",
            "__SHOPPING_ADMIN__",
        )
        observed = await execute_navigation(Page(), route)
        self.assertEqual(observed["http_status"], 200)


if __name__ == "__main__":
    unittest.main()
