"""Fail-closed count and verdict controls for a real external test suite."""
import unittest
from research.g1_false_green_v1.runner import classify


class RecognizedSuiteGateTests(unittest.TestCase):
    def test_zero_recognized_cannot_be_green(self):
        self.assertEqual(classify(exit_code=0, recognized=0, failed=0),
                         "UNKNOWN_ZERO_RECOGNIZED_TESTS")

    def test_green_nonempty_suite_is_admitted(self):
        self.assertEqual(classify(exit_code=0, recognized=12, failed=0),
                         "PASS_BOUNDED")

    def test_nonzero_exit_is_rejected(self):
        self.assertEqual(classify(exit_code=1, recognized=12, failed=1),
                         "REJECTED")

    def test_reported_failure_rejects_even_with_exit_zero(self):
        self.assertEqual(classify(exit_code=0, recognized=12, failed=1),
                         "REJECTED")


if __name__ == "__main__":
    unittest.main()
