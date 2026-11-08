"""C38: require evidence for checked, non-proof-erasing application congruence."""

import unittest

from probe_c38_typed_congruence import parse_congruence


class C38TypedCongruenceTest(unittest.TestCase):
    def test_all_checked_data_arguments_can_establish_congruence(self):
        e = parse_congruence(
            "NUCLEUS_C38_TYPED_SPINE:head=NameId(65):spine=4:"
            "depth=7:proof_erasures=false:result=proven"
        )
        self.assertEqual(e["head"], 65)
        self.assertEqual(e["spine"], 4)
        self.assertFalse(e["proof_erasures"])

    def test_requires_a_checked_source_result(self):
        for line in (
            "NUCLEUS_C38_TYPED_SPINE:head=NameId(65):spine=4:"
            "depth=7:proof_erasures=false:result=guessed",
            "NUCLEUS_C38_TYPED_SPINE:head=NameId(65):spine=0:"
            "depth=7:proof_erasures=false:result=proven",
            "NUCLEUS_C38_TYPED_SPINE:head=NameId(65):spine=4:"
            "depth=7:proof_erasures=false",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_congruence(line)

    def test_ignores_other_diagnostics(self):
        self.assertIsNone(parse_congruence("NUCLEUS_C37_ROOT_REASON:..."))


if __name__ == "__main__":
    unittest.main()
