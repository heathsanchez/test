"""Independent finite witnesses for the Complete-O discovery harness."""
import os
from fractions import Fraction
import subprocess
import sys
import unittest

import collatz_coupled_dag_v1 as dag
import collatz_source_refinement_bridge as bridge


class BellmanAuditTests(unittest.TestCase):
    def test_infeasible_reverse_state_has_no_score(self):
        # No power of 2 times a multiple of 3 can equal 1 modulo 3.
        self.assertIsNone(dag.phi(1, 0))

    def test_infeasible_tail_does_not_allocate_a_giant_integer(self):
        # R_2(R_2(1))=1 has score (4,7).  An infeasible alternative
        # must not turn a sentinel cost into a 1,000,000,000-bit integer.
        source = """
import resource
resource.setrlimit(resource.RLIMIT_AS, (64*1024*1024, 64*1024*1024))
from collatz_coupled_dag_v1 import phi, Score
assert phi(2, 1) == Score(4, 7)
"""
        result = subprocess.run(
            [sys.executable, "-c", source],
            cwd=os.path.dirname(__file__), capture_output=True, text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_three_has_a_non_minus_one_rigid_transition(self):
        # 3 -> 5 -> 8 -> 4.  At depths 2 and 3 the source is optimal.
        self.assertEqual(dag.forward_cylinder(2, 3), (2, 8))
        self.assertEqual(dag.forward_cylinder(3, 3), (2, 4))
        self.assertEqual(dag.phi(2, 8), dag.Score(2, 5))
        self.assertEqual(dag.phi(2, 4), dag.Score(3, 5))
        self.assertEqual(dag.classify(2, 3)[0], "RIGID")
        self.assertEqual(dag.classify(3, 3)[0], "RIGID")
        self.assertNotEqual(4 % 3, 2)

    def test_bellman_matches_independent_fraction_replay(self):
        # Enumerate all complete words with sum <= the feasible source
        # length. Replay their intermediate values, without Bellman or
        # terminal-congruence shortcuts. A better score cannot lie above
        # this sum bound.
        def words(count, budget, prefix=()):
            if count == 0:
                yield prefix
            else:
                for a in range(1, budget-count+2):
                    yield from words(count-1, budget-a, prefix+(a,))

        for k in range(1, 9):
            for b in range(1, 2**k, 2):
                c, endpoint = dag.forward_cylinder(k, b)
                candidates = []
                for word in words(c, k):
                    value = Fraction(endpoint)
                    for a in word:
                        value = (2**a*value-1)/3
                        if value.denominator != 1 or value <= 0:
                            break
                    else:
                        total = sum(word)
                        cocycle = 2**total*endpoint-3**c*int(value)
                        candidates.append((total, -cocycle))
                self.assertTrue(candidates, (k, b))
                self.assertEqual(dag.phi(c, endpoint % 3**c).key(),
                                 min(candidates), (k, b))

    def test_fixed_integer_countdown_uses_refinement_parameter(self):
        def valuation2(value):
            return (value & -value).bit_length()-1

        for m in range(2, 41):
            n = 2**m-1
            actual_endpoint = n
            for k in range(1, m+1):
                actual_endpoint = dag.T(actual_endpoint)
                b = 2**k-1
                q = (n-b)//2**k
                self.assertEqual(actual_endpoint, 3**k*(q+1)-1)
                self.assertEqual(valuation2(actual_endpoint+1), m-k)
                if k < m:
                    self.assertEqual(q % 2, 1)
                    qp = (q-1)//2
                    kp, bp, cp, dp = bridge.child_formula(k, b, 1)
                    self.assertEqual(n, 2**kp*qp+bp)
                    self.assertEqual(dag.T(actual_endpoint), 3**cp*qp+dp)
                    self.assertEqual(valuation2(qp+1), valuation2(q+1)-1)
                else:
                    self.assertEqual(q, 0)
                    self.assertEqual(actual_endpoint % 2, 0)

    def test_even_exit_from_all_odd_family_can_still_be_rigid(self):
        # An odd-run countdown is not itself a certificate of lower merge.
        for k in range(1, 9):
            b = 2**k-1
            self.assertEqual(dag.forward_cylinder(k+1, b),
                             (k, (3**k-1)//2))
            self.assertEqual(dag.phi(k, (3**k-1)//2),
                             dag.Score(k+1, 3**k-2**k))
            self.assertEqual(dag.classify(k+1, b)[0], "RIGID")


if __name__ == "__main__":
    unittest.main()
