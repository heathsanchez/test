"""Regression for the C9 compounding direct-descent short-circuit."""

import unittest

import collatz_q0_coalescence_component_audit as base


class C9CompoundingShortCircuit(unittest.TestCase):
    def test_hard_source_closes_before_late_c9_hit(self):
        n=218263167
        y=n
        first=None
        at142=None
        for k in range(1,143):
            y=base.T(y)
            if first is None and y<n:
                first=(k,y)
            if k==142:
                at142=y
        self.assertEqual(first,(124,168546160))
        self.assertEqual(at142,468713)
        self.assertLess(first[1],n)
        # The later C9 residue hit is irrelevant after the direct descent.
        self.assertLess(124,142)


if __name__=="__main__":
    unittest.main()
