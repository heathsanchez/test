"""CPU checks for fixed-tolerance, bounded full16 depth diagnostics."""
import ast
from pathlib import Path
import unittest

from gpu_megakernel_gate import ATOL, RTOL

ROOT = Path(__file__).parent


class DepthDiagnosticTests(unittest.TestCase):
    def test_registered_depth_sweep_and_dag_control(self):
        worker = (ROOT / "runpod_flash_h100_bridge.py").read_text()
        ast.parse(worker)
        self.assertIn('elif probe_kind == "depth_diagnostic":', worker)
        self.assertIn('("rr", x) for x in (1, 2, 4, 8, 12, 16)', worker)
        self.assertIn('[("dag", 16)]', worker)
        self.assertIn('report["status"] = "DIAGNOSTIC_RECORDED"', worker)
        self.assertIn('if outcome.get("passed") is not False:', worker)
        self.assertIn('if key not in report["checks"]:', worker)
        self.assertIn('if probe_kind in ("lmhead", "full16", "depth_diagnostic")', worker)

    def test_diagnostic_status_cannot_be_promoted_to_full_model_pass(self):
        worker = (ROOT / "runpod_flash_h100_bridge.py").read_text()
        self.assertIn('elif probe_kind == "depth_diagnostic":\n        allowed = ("DIAGNOSTIC_RECORDED",)', worker)
        self.assertIn('elif probe_kind == "full16":\n        allowed = ("PASS_FULL16",)', worker)
        self.assertNotIn('allowed = ("DIAGNOSTIC_RECORDED", "PASS_FULL16")', worker)

    def test_reference_thresholds_unchanged(self):
        self.assertEqual(ATOL, 0.05)
        self.assertEqual(RTOL, 0.10)
        gate = (ROOT / "gpu_megakernel_gate.py").read_text()
        self.assertIn('registered = {(2, 1), (3, 2), (2, 2)}', gate)
        self.assertIn('{(16, depth) for depth in (1, 2, 4, 8, 12, 16)}', gate)
        self.assertIn('choices=(1, 2, 4, 8, 12, 16)', gate)
        self.assertNotIn('choices=(1, 2, 16)', gate)
        self.assertIn('if pyvm_completed[0] < 1:', gate)


if __name__ == "__main__":
    unittest.main()
