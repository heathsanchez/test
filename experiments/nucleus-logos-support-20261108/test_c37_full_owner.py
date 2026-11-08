"""Fail-closed tests for the full-remaining-owner recursor replay audit."""

import unittest

from probe_c37_full_owner import parse_reason_event


class C37FullOwnerTests(unittest.TestCase):
    def test_full_owner_budget_exhaustion(self):
        event = parse_reason_event(
            "NUCLEUS_C37_ROOT_REASON:depth=0:head=NameId(147):"
            "grant=260755:spent=260755:remaining=0:"
            "reason=nested-recursor-iota-budget"
        )
        self.assertEqual(event["head"], 147)
        self.assertTrue(event["exhausted"])

    def test_requires_metered_event_and_source_reason(self):
        for line in (
            "NUCLEUS_C37_ROOT_REASON:depth=0:head=NameId(147):"
            "grant=260755:spent=260756:remaining=0:reason=nested-recursor-iota-budget",
            "NUCLEUS_C37_ROOT_REASON:depth=0:head=NameId(147):"
            "grant=260755:spent=200:remaining=0:reason=source guessed",
            "NUCLEUS_C37_ROOT_REASON:depth=0:head=NameId(147):"
            "grant=0:spent=0:remaining=0:reason=nested-recursor-iota-budget",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_reason_event(line)

    def test_other_diagnostics_not_confused_with_c37(self):
        self.assertIsNone(parse_reason_event(
            "NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=0:side=right:"
            "head=NameId(147):grant=512:spent=512:remaining=100:outcome=unknown"
        ))


if __name__ == "__main__":
    unittest.main()
