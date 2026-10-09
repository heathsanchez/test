"""Pure-date and prohibited-input controls for blind report navigation."""
import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_shopping_admin_blind_report import parse_report_range


class ReportIntentTests(unittest.TestCase):
    def test_relative_year_is_grounded_in_given_date(self):
        self.assertEqual(
            parse_report_range("Show the sales order report for for last year (today is March 15, 2023)."),
            (date(2022,1,1),date(2022,12,31)),
        )

    def test_absolute_range(self):
        self.assertEqual(
            parse_report_range("Show the orders report from May 1, 2021 to March 31, 2022."),
            (date(2021,5,1),date(2022,3,31)),
        )

    def test_reject_unbounded_or_reversed_time(self):
        for query in (
            "Show the orders report someday.",
            "Show the orders report from May 1, 2023 to March 31, 2022.",
            "Show the orders report from yesterday.",
        ):
            with self.assertRaises(ValueError):
                parse_report_range(query)

    def test_no_benchmark_metadata_in_source(self):
        source=(Path(__file__).resolve().parents[1]/"scripts"/"webarena_shopping_admin_blind_report.py").read_text()
        for marker in ("task_id","intent_template_id","instantiation_dict","expected_answer","NetworkEventEvaluator"):
            self.assertNotIn(marker,source)


if __name__=="__main__":
    unittest.main()
