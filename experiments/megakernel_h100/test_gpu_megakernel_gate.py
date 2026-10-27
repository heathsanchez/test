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
        self.assertIn("registered = {(2, 1), (3, 2), (2, 2)}", source)
        self.assertIn("(16, depth) for depth in (1, 2, 4, 8, 12, 16)", source)
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
