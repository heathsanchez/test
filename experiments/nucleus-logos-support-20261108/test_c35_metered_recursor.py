"""C35 fuel-accounting trace must be source-owned and fail closed."""

import unittest

from c35_probe import MARKER, parse_record


class C35MeteredRecursor(unittest.TestCase):
    def example(self, *, grant=512, spent=48, remaining=1024):
        return (f"{MARKER}depth=3:left=false:grant={grant}:spent={spent}:"
                f"remaining={remaining}:changed=false")

    def test_actual_work_and_unused_allowance_distinct(self):
        event = parse_record(self.example())
        self.assertEqual(event["grant"], 512)
        self.assertEqual(event["spent"], 48)
        self.assertFalse(event["changed"])

    def test_unpaid_or_zero_budget_denied(self):
        for text in (self.example(grant=48, spent=49), self.example(grant=0, spent=0)):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_record(text)

    def test_malformed_event_rejected(self):
        with self.assertRaises(ValueError):
            parse_record(f"{MARKER}depth=2:left=no")

    def test_irrelevant_line_ignored(self):
        self.assertIsNone(parse_record("ordinary verifier stderr"))


if __name__ == "__main__":
    unittest.main()
