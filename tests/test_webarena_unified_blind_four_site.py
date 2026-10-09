"""Pure-boundary regression suite for four-site blind extension."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_unified_blind_four_site import (
    site_from_start, actual_start, classify_readonly_intent,
)


class FourSiteBlindTests(unittest.TestCase):
    def test_site_routing(self):
        cases={
            "__REDDIT__":"reddit",
            "__GITLAB__":"gitlab",
            "__SHOPPING__":"shopping",
            "__SHOPPING__/example.html":"shopping",
            "__SHOPPING_ADMIN__":"shopping_admin",
            "http://localhost:7770/p.html":"shopping",
            "http://localhost:7780/admin":"shopping_admin",
            "http://localhost:9999/f/books":"reddit",
            "http://localhost:8023/project":"gitlab",
        }
        for start,expected in cases.items():
            self.assertEqual(site_from_start(start),expected)
        with self.assertRaises(ValueError):
            site_from_start("https://external.invalid/")

    def test_shopping_review_intent(self):
        query="Get all review titles with 2 stars or below for the product on the current page."
        self.assertEqual(classify_readonly_intent("shopping",query),"shopping_low_reviews")
        self.assertEqual(actual_start("__SHOPPING__/product.html"),
                         "http://localhost:7770/product.html")

    def test_admin_month_range_from_instruction(self):
        for period in (
            "from January 2023 through May 2023",
            "from Jan 2022 through Nov 2022",
            "from Feb 2022 through Nov 2022",
        ):
            query=("Get the monthly count of completed orders "+period+
                   ', inclusive. Return a list of objects with keys "month" and "count" only.')
            self.assertEqual(
                classify_readonly_intent("shopping_admin",query),
                "admin_monthly_complete_orders"
            )
        self.assertEqual(actual_start("__SHOPPING_ADMIN__"),
                         "http://localhost:7780/admin")

    def test_admin_report_navigation_intents(self):
        cases=(
            "Show the sales order report for for last year (today is March 15, 2023).",
            "Show the orders report from May 1, 2021 to March 31, 2022.",
        )
        for intent in cases:
            self.assertEqual(
                classify_readonly_intent("shopping_admin",intent),
                "admin_orders_report_navigation",
            )

    def test_unwarranted_scope_fails_closed(self):
        with self.assertRaises(ValueError):
            classify_readonly_intent("shopping","Submit a purchase")
        with self.assertRaises(ValueError):
            classify_readonly_intent("shopping_admin","Delete every order")
        with self.assertRaises(ValueError):
            classify_readonly_intent(
                "shopping_admin",
                "Get the monthly count of completed orders during forever"
            )

    def test_no_evaluator_lookup_in_agent(self):
        src=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_unified_blind_four_site.py").read_text()
        for marker in ("task_id","intent_template_id","instantiation_dict","evaluate_task","expected_answer"):
            self.assertNotIn(marker,src)


if __name__=="__main__":
    unittest.main()
