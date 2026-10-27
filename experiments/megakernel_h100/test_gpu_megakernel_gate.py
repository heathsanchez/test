"""CPU-only contract tests for the pre-registered GPU result gate."""

import ast
from pathlib import Path
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

    def test_registered_lmhead_pair_scope(self):
        source = Path(__file__).with_name("gpu_megakernel_gate.py").read_text()
        self.assertIn("num_hidden_layers=num_layers, num_attention_heads=32", source)
        self.assertIn('((2, 1), (3, 2), (2, 2), (16, 16))', source)
        self.assertIn("lm_head_active = num_layers == layer_limit", source)
        self.assertIn('f"layer_limit={layer_limit}"', source)
        self.assertIn('"lm_head_exercised": lm_head_active', source)

    def test_partial_layer_gate_excludes_vacuous_logits(self):
        three = {k: v for k, v in self.good.items() if k != "logits"}
        self.assertTrue(evaluate_summary(three, required_fields=("hidden_states", "k_cache", "v_cache"))["passed"])
        self.assertFalse(evaluate_summary(three)["passed"])

    def test_full_head_missing_logits_rejected(self):
        bad = dict(self.good)
        del bad["logits"]
        self.assertFalse(evaluate_summary(bad, required_fields=("hidden_states", "k_cache", "v_cache", "logits"))["passed"])

    def test_unexecuted_reference_cannot_authorize(self):
        source = Path(__file__).with_name("gpu_megakernel_gate.py")
        code = source.read_text()
        self.assertNotIn('"skip_pyvm=false"', code)
        module = ast.parse(code)
        run_diff = next(n for n in module.body
                        if isinstance(n, ast.FunctionDef) and n.name == "run_diff")
        guarded = next(n for n in run_diff.body
                       if isinstance(n, ast.FunctionDef) and n.name == "gated_diff")
        isolated = ast.fix_missing_locations(ast.Module(body=[guarded], type_ignores=[]))
        scope = {"pyvm_completed": [0]}
        exec(compile(isolated, str(source), "exec"), scope)
        with self.assertRaisesRegex(AssertionError, "reference never completed"):
            scope["gated_diff"](None, None)

    def _full16_verdict(self, checks):
        # Extract the pure contract without importing RunPod or accessing GPUs.
        path = Path(__file__).with_name("runpod_flash_h100_bridge.py")
        module = ast.parse(path.read_text())
        fn = next(n for n in module.body
                  if isinstance(n, ast.FunctionDef) and n.name == "full16_verdict")
        isolated = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
        scope = {"SOURCE_PIN": "7309cec801537b61fea3b50d7dfe454a6cde578e"}
        exec(compile(isolated, str(path), "exec"), scope)
        return scope["full16_verdict"](checks)

    def _full16_receipt(self, sched, passed=True):
        return {
            "scheduler": sched,
            "source_commit": "7309cec801537b61fea3b50d7dfe454a6cde578e",
            "fixture_layers": 16, "executed_layers": 16,
            "lm_head_exercised": True, "pyvm_completed_calls": 1,
            "fields_compared": ["hidden_states", "k_cache", "v_cache", "logits"],
            "passed": passed,
            "fields": {f: {"elements": 1, "violations": 0, "nonfinite": 0}
                       for f in ("hidden_states", "k_cache", "v_cache", "logits")},
        }

    def test_full16_requires_both_schedulers(self):
        rr = self._full16_receipt("rr")
        self.assertEqual(self._full16_verdict({"rr": rr}), "UNKNOWN_FULL16_INCOMPLETE")

    def test_full16_both_valid_comparisons_pass(self):
        checks = {s: self._full16_receipt(s) for s in ("rr", "dag")}
        self.assertEqual(self._full16_verdict(checks), "PASS_FULL16")

    def test_full16_rr_rejection_not_promoted_by_dag_pass(self):
        checks = {s: self._full16_receipt(s) for s in ("rr", "dag")}
        checks["rr"]["passed"] = False
        checks["rr"]["fields"]["hidden_states"]["violations"] = 23
        self.assertEqual(self._full16_verdict(checks), "REJECTED_FULL16_DIFFERENTIAL")

    def test_full16_invalid_source_or_gpu_reference_receipt_unknown(self):
        checks = {s: self._full16_receipt(s) for s in ("rr", "dag")}
        checks["rr"]["source_commit"] = "0" * 40
        self.assertEqual(self._full16_verdict(checks), "UNKNOWN_FULL16_INVALID_RECEIPT")
        checks["rr"] = self._full16_receipt("rr")
        checks["dag"]["pyvm_completed_calls"] = 0
        self.assertEqual(self._full16_verdict(checks), "UNKNOWN_FULL16_INVALID_RECEIPT")

    def test_full16_false_positive_metric_rejected(self):
        checks = {s: self._full16_receipt(s) for s in ("rr", "dag")}
        checks["rr"]["fields"]["logits"]["violations"] = 9
        self.assertEqual(self._full16_verdict(checks), "UNKNOWN_FULL16_INVALID_RECEIPT")

    def test_full16_negative_receipt_does_not_skip_dag(self):
        src = Path(__file__).with_name("runpod_flash_h100_bridge.py").read_text()
        self.assertIn('except RuntimeError as exc:', src)
        self.assertIn('report["status"] = full16_verdict(report["checks"])', src)
        self.assertNotIn('if not report["checks"].get(sched, {}).get("passed"):', src)

    def test_mismatch_observations_bounded(self):
        src = Path(__file__).with_name("gpu_megakernel_gate.py").read_text()
        self.assertIn('name in ("hidden_states", "logits")', src)
        self.assertIn('k=min(int(violations), 8)', src)
        self.assertIn('"flat_index": int(i)', src)

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
