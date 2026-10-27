"""CPU-only contract tests for the pre-registered GPU result gate."""

import unittest

from gpu_megakernel_gate import evaluate_summary, validate_manifest


class GateTests(unittest.TestCase):
    def setUp(self):
        self.good = {
            "hidden_states": {"elements": 2048, "nonfinite": 0, "violations": 0, "max_abs_diff": 0.01},
            "k_cache": {"elements": 1024, "nonfinite": 0, "violations": 0, "max_abs_diff": 0.0},
            "v_cache": {"elements": 1024, "nonfinite": 0, "violations": 0, "max_abs_diff": 0.0},
            "logits": {"elements": 128256, "nonfinite": 0, "violations": 0, "max_abs_diff": 0.01},
        }

    def test_positive(self):
        self.assertTrue(evaluate_summary(self.good)["passed"])

    def test_mismatch_is_failing_not_just_printed(self):
        self.good["hidden_states"]["violations"] = 1
        self.assertFalse(evaluate_summary(self.good)["passed"])

    def test_nonfinite_is_failing(self):
        self.good["v_cache"]["nonfinite"] = 1
        self.assertFalse(evaluate_summary(self.good)["passed"])

    def test_missing_comparison_is_failing(self):
        del self.good["logits"]
        self.assertFalse(evaluate_summary(self.good)["passed"])

    def test_source_manifest_mismatch_is_failing(self):
        self.assertTrue(validate_manifest("7309cec801537b61fea3b50d7dfe454a6cde578e") )
        self.assertFalse(validate_manifest("0" * 40))


if __name__ == "__main__":
    unittest.main()
