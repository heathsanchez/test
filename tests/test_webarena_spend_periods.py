"""The natural-language bridge consumes 'during'; native period parsing accepts both forms."""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from webarena_shopping_category_spend import parse_time

class SpendPeriodParsing(unittest.TestCase):
    def test_month_with_and_without_preposition(self):
        self.assertEqual(parse_time("Jan 2023"),parse_time("during Jan 2023"))
        self.assertEqual(parse_time("January 2023"),parse_time("during January 2023"))
        self.assertEqual(parse_time("Jan 2023")[1],datetime(2023,1,1))

    def test_day_with_and_without_preposition(self):
        self.assertEqual(parse_time("January 29, 2023"),parse_time("during January 29, 2023"))
        self.assertEqual(parse_time("January 29, 2023")[1],datetime(2023,1,29))

    def test_invalid_dates_fail_closed(self):
        for raw in ("someday","January 2023 and tomorrow","January 29 2023 extra"):
            with self.assertRaises(ValueError):parse_time(raw)

if __name__=="__main__":unittest.main()
