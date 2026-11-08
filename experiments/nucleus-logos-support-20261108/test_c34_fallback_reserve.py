"""Isolated parser/red-gate checks for source-owned C34 scheduling trial."""

import unittest

from c34_probe import MARKER, parse_reserve


class C34SourceOwnedReservation(unittest.TestCase):
    def event(self, *, grant=249, spent=183, remaining=317, reserve=250):
        return (f"{MARKER}head=NameId(66):depth=5:divisor=2:"
                f"reserve={reserve}:cap=2048:grant={grant}:spent={spent}:"
                f"remaining={remaining}:proved=true")

    def test_registered_event_parses_with_reserved_work_intact(self):
        event = parse_reserve(self.event())
        self.assertEqual(event["reserve"], 250)
        self.assertEqual(event["remaining"], 317)
        self.assertTrue(event["proved"])

    def test_unpaid_work_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_reserve(self.event(grant=249, spent=250))

    def test_borrowing_from_fallback_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_reserve(self.event(reserve=250, remaining=249))

    def test_truncated_event_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_reserve(f"{MARKER}head=NameId(66)")

    def test_unrelated_lines_are_ignored(self):
        self.assertIsNone(parse_reserve("normal verifier log"))


if __name__ == "__main__":
    unittest.main()
