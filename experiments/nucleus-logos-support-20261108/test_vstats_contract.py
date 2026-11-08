"""Protect native reference diagnostics from ambiguous text-grep matches."""

import unittest

from vstats_contract import parse_vstats, require_counter


class ValueStatsContract(unittest.TestCase):
    def test_exact_counter_does_not_match_suffix_of_another_counter(self):
        records = parse_vstats([
            "vstats chain12_datF Stats { mk_pi_closed_hit: 71, closed_hit: 0, "
            "inst_hit: 12, inst_miss: 3 } arena 55\n",
        ])
        self.assertEqual(records["chain12_datF"]["closed_hit"], 0)
        require_counter(records, "closed_hit", "zero", "chain12_datF")
        require_counter(records, "inst_hit", "positive", "chain12_datF")

    def test_all_zero_checks_every_declaration(self):
        records = parse_vstats([
            "vstats a Stats { closed_hit: 0, mk_pi_closed_hit: 20 } arena 1\n",
            "vstats b Stats { closed_hit: 0, mk_pi_closed_hit: 21 } arena 2\n",
        ])
        require_counter(records, "closed_hit", "zero")
        with self.assertRaises(ValueError):
            require_counter(records, "mk_pi_closed_hit", "zero")

    def test_missing_declaration_or_counter_fails_closed(self):
        records = parse_vstats(["vstats a Stats { closed_hit: 0 } arena 1\n"])
        with self.assertRaises(ValueError):
            require_counter(records, "closed_hit", "positive", "a")
        with self.assertRaises(ValueError):
            require_counter(records, "closed_hit", "zero", "missing")
        with self.assertRaises(ValueError):
            require_counter(records, "inst_hit", "zero", "a")

    def test_duplicates_and_bad_stats_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_vstats(["vstats a Stats { closed_hit: 0, closed_hit: 2 } arena 1\n"])
        with self.assertRaises(ValueError):
            parse_vstats(["vstats a Stats { closed_hit: nope } arena 1\n"])
        with self.assertRaises(ValueError):
            parse_vstats(["unrelated line\n"])


if __name__ == "__main__":
    unittest.main()
