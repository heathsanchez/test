"""Independent elementary checks of a finite Markov counterexample."""

from math import sqrt
import unittest

from doob_counterexample import matvec, witness


class DoobTwoStateTests(unittest.TestCase):
    def setUp(self):
        self.w = witness()

    def near_zero(self, xs):
        for x in xs:
            self.assertAlmostEqual(x, 0.0, places=12)

    def test_baseline_is_genuine_markov_generator(self):
        q = self.w["q"]
        self.near_zero(matvec(q, [1, 1]))
        self.assertEqual([q[0][1], q[1][0]], [1, 1])

    def test_positive_killed_eigenpair_is_valid(self):
        self.assertGreater(min(self.w["h"]), 0)
        self.assertAlmostEqual(self.w["lambda"], (3 - sqrt(5)) / 2)
        self.near_zero(self.w["eigen_residual"])

    def test_bare_transform_is_not_probability_preserving(self):
        rows = self.w["bare_mass_derivative"]
        self.assertLess(rows[0], -0.3)
        self.assertGreater(rows[1], 0.6)
        self.assertNotAlmostEqual(rows[0], 0.0, places=12)

    def test_corrected_conditioned_transform_is_conservative(self):
        self.near_zero(self.w["conditioned_mass_derivative"])
        self.assertGreater(self.w["conditioned"][0][1], 0)
        self.assertGreater(self.w["conditioned"][1][0], 0)

    def test_pointwise_generator_positivity_axiom_conflicts_with_baseline_recovery(self):
        # A stated E1 requires T_h(L)f >= 0 whenever f >= 0, while E2
        # requires T_1(L)=L. For f=(1,0), Qf=(-1,+1) contradicts E1.
        self.assertEqual(self.w["E1_baseline_positive_f_qf"], [-1.0, 1.0])

    def test_baseline_p_times_h_not_stationary_for_conditioned_process(self):
        proposed = self.w["claimed_p_times_h"]
        actual = self.w["actual_conditioned_stationary"]
        self.assertGreater(abs(proposed[0] - actual[0]), 0.10)
        self.assertAlmostEqual(sum(proposed), 1)
        self.assertAlmostEqual(sum(actual), 1)
        self.assertAlmostEqual(actual[0], self.w["left_times_right_stationary"][0])
        self.assertAlmostEqual(actual[1], self.w["left_times_right_stationary"][1])


if __name__ == "__main__":
    unittest.main()
