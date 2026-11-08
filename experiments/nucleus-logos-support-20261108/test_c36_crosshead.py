"""Fail-closed tests for source-certified cross-head recursor diagnostics."""

import unittest

from probe_c36_crosshead import parse_record


class C36CrossHeadEvents(unittest.TestCase):
    def test_metered_source_replay_event(self):
        event = parse_record(
            "NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=0:side=right:head=NameId(147):"
            "grant=2048:spent=183:remaining=260571:outcome=unknown"
        )
        self.assertEqual(event["head"], 147)
        self.assertEqual(event["spent"], 183)
        self.assertEqual(event["outcome"], "unknown")

    def test_rejects_unpaid_work_and_malformed_claim(self):
        for event in (
            "NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=0:side=right:head=NameId(147):"
            "grant=512:spent=513:remaining=400:outcome=changed",
            "NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=0:side=right:head=NameId(147):"
            "grant=0:spent=0:remaining=400:outcome=changed",
            "NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=0:side=right:head=NameId(147):"
            "grant=512:spent=1:remaining=400:outcome=guessed",
            "NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=0:side=right:head=NameId(147):"
            "grant=512:spent=1:outcome=changed",
        ):
            with self.subTest(event=event), self.assertRaises(ValueError):
                parse_record(event)

    def test_irrelevant_events_ignored(self):
        self.assertIsNone(parse_record("NUCLEUS_C35_RECURSOR_CHARGE:..."))


if __name__ == "__main__":
    unittest.main()
