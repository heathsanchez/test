"""Bounded physical-law calibration, not a rerun of the native Nyx code."""

import math
import unittest
from unittest.mock import patch

import frame_commutation
from frame_commutation import simulate, kepler_truth, norm_difference


class FutureFrameCommutationTests(unittest.TestCase):
    def test_independent_kepler_reference_is_hand_pinned(self):
        pos, vel = kepler_truth(600.0)
        for actual, expected in zip(pos, (5584.4279451594075, 4192.052304588444)):
            self.assertAlmostEqual(actual, expected, places=7)
        for actual, expected in zip(vel, (-4.558029676982553, 5.9795741866751895)):
            self.assertAlmostEqual(actual, expected, places=8)

    def test_static_coordinate_conversion_at_event_epoch_is_not_enough(self):
        inertial = simulate('inertial', duration=0.0)
        rotating = simulate('naive_rotating', duration=0.0)
        self.assertLess(norm_difference(inertial[0], rotating[0]), 1e-12)
        self.assertLess(norm_difference(inertial[1], rotating[1]), 1e-12)

    def test_naive_rotating_kepler_ode_breaks_future_equivalence(self):
        inertial = simulate('inertial', duration=600.0)
        naive = simulate('naive_rotating', duration=600.0)
        self.assertGreater(norm_difference(inertial[0], naive[0]), 100.0)
        self.assertGreater(norm_difference(inertial[1], naive[1]), 0.1)

    def test_rotating_inertial_force_terms_restore_future_equivalence(self):
        inertial = simulate('inertial', duration=600.0)
        corrected = simulate('correct_rotating', duration=600.0)
        exact = kepler_truth(600.0)
        self.assertLess(norm_difference(inertial[0], exact[0]), 1e-5)
        self.assertLess(norm_difference(inertial[1], exact[1]), 1e-7)
        self.assertLess(norm_difference(inertial[0], corrected[0]), 1e-5)
        self.assertLess(norm_difference(inertial[1], corrected[1]), 1e-7)

    def test_earth_spin_ablation_eliminates_naive_discrepancy(self):
        """The discrepancy is caused by the changing frame, not gravity."""
        with patch.object(frame_commutation, 'SPIN', 0.0):
            for duration in (60.0, 600.0, 1200.0):
                inertial = simulate('inertial', duration=duration)
                naive = simulate('naive_rotating', duration=duration)
                self.assertLess(norm_difference(inertial[0], naive[0]), 1e-9)
                self.assertLess(norm_difference(inertial[1], naive[1]), 1e-11)

    def test_independent_model_reproduces_native_nyx_magnitude_without_nyx_runtime(self):
        """Approximate constant-spin model vs previously reported native values."""
        inertial = simulate('inertial', duration=600.0)
        naive = simulate('naive_rotating', duration=600.0)
        self.assertAlmostEqual(norm_difference(inertial[0], naive[0]),
                               201.19015652244954, delta=0.001)
        self.assertAlmostEqual(norm_difference(inertial[1], naive[1]),
                               0.713117640, delta=1e-5)


if __name__ == '__main__':
    unittest.main()
