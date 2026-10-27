"""CPU-only LM-head pair contract, with no RunPod dependency."""
import ast
from pathlib import Path
import unittest

from gpu_megakernel_gate import FIELDS, evaluate_summary

HERE = Path(__file__).parent


class LMHeadPairContract(unittest.TestCase):
    def test_registered_pairs_and_reference_gate(self):
        gate = (HERE / "gpu_megakernel_gate.py").read_text()
        bridge = (HERE / "runpod_flash_h100_bridge.py").read_text()
        ast.parse(gate)
        ast.parse(bridge)
        self.assertIn('((2, 1), (3, 2), (2, 2), (16, 16))', gate)
        self.assertIn('("partial_2of3", 3, 2), ("full_2of2", 2, 2)', bridge)
        self.assertIn("if case == \"partial_2of3\" and not", bridge)
        self.assertIn("UNKNOWN_PARTIAL_CONTROL_FAILED", bridge)
        self.assertIn("LMHEAD_NATIVE_TIMEOUT", bridge)
        self.assertIn('"shared_weight_equivalence"', bridge)
        self.assertIn('"shared_fixture_weights_checked"] = True', bridge)
        self.assertIn('verify_paired_fixture_weights', gate)
        self.assertIn('torch.equal(partial.get_tensor(name), full.get_tensor(name))', gate)
        self.assertIn('run_async_differential(gate.read_text(), out, probe_kind=probe_kind)', bridge)
        self.assertIn('"pyvm_completed_calls": pyvm_completed[0]', gate)

    def test_vacuous_partial_logits_not_authorized(self):
        metrics = {
            field: {"elements": 8, "nonfinite": 0, "violations": 0, "max_abs_diff": 0.0}
            for field in FIELDS if field != "logits"
        }
        self.assertTrue(evaluate_summary(metrics, required_fields=FIELDS[:-1])["passed"])
        self.assertFalse(evaluate_summary(metrics, required_fields=FIELDS)["passed"])

    def test_full_logits_must_not_be_all_zero(self):
        source = (HERE / "gpu_megakernel_gate.py").read_text()
        self.assertIn('torch.count_nonzero(ref_logits).item() == 0', source)
        self.assertIn('torch.count_nonzero(gpu_logits).item() == 0', source)
        self.assertIn('lm_head_output_unobserved', source)

    def test_lmhead_timeout_not_equivalence_pass(self):
        source = (HERE / "runpod_flash_h100_bridge.py").read_text()
        self.assertIn('"status": "UNKNOWN_NATIVE_TIMEOUT", "passed": False', source)
        self.assertNotIn('"status": "PASS", "passed": False', source)


if __name__ == "__main__":
    unittest.main()
