"""C33 native parser contract for source-only pre-iota congruence trials."""

import unittest

from probe_c33_source_congruence import parse_record


class C33SourceCongruenceTests(unittest.TestCase):
    def test_checked_equality_and_charge_are_distinct(self):
        event = parse_record(
            "NUCLEUS_C28_SOURCE_CONGRUENCE:head=NameId(147):depth=7:"
            "grant=4096:spent=1200:remaining=100:proved=true:first_failed=None"
        )
        self.assertEqual(event["head"], 147)
        self.assertEqual(event["grant"], 4096)
        self.assertEqual(event["spent"], 1200)
        self.assertTrue(event["proved"])

    def test_overdraw_or_bad_proof_claim_rejected(self):
        self.assertRaises(ValueError, parse_record,
                          "NUCLEUS_C28_SOURCE_CONGRUENCE:head=NameId(66):depth=2:"
                          "grant=512:spent=513:remaining=0:proved=false:first_failed=Some(0)")
        self.assertRaises(ValueError, parse_record,
                          "NUCLEUS_C28_SOURCE_CONGRUENCE:head=NameId(66):depth=2:"
                          "grant=512:spent=300:remaining=1:proved=true:first_failed=Some(0)")

    def test_other_log_is_not_observation(self):
        self.assertIsNone(parse_record("NUCLEUS_C31_PROJECTION:seq=5"))


if __name__ == "__main__":
    unittest.main()
