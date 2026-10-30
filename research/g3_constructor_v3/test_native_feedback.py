"""V3 native Go tests: exact hints work, opaque hints never silently pass."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
PLANNER = HERE.parents[0] / "g3_constructor_v2" / "constructor_planner.go"
BRIDGE = HERE / "native_feedback_bridge.py"
SYNTHETIC_SHA = "7" * 40


class FeedbackNativeTests(unittest.TestCase):
    def run_case(self, fixture):
        module = f"example.com/mg-feedback-{fixture}-fixture"
        with tempfile.TemporaryDirectory(prefix="g3-feedback-") as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(HERE / "testdata" / fixture, root)
            manifest_path = Path(tmp) / "manifest.json"
            subprocess.run(
                ["go", "run", str(PLANNER), "--source", str(root), "--out", str(manifest_path)],
                text=True, capture_output=True, check=True,
            )
            proposal = json.loads(manifest_path.read_text())
            self.assertEqual(proposal["status"], "CANDIDATE_CONSTRUCTOR")
            subprocess.run(
                [sys.executable, str(BRIDGE), "--manifest", str(manifest_path),
                 "--source-dir", str(root), "--module", module, "--sha", SYNTHETIC_SHA],
                text=True, capture_output=True, check=True,
            )
            execution = subprocess.run(
                ["go", "run", "./cmd/mgconstructor"], cwd=root,
                text=True, capture_output=True,
            )
            return proposal, execution

    def test_explicit_multi_field_hints_admit_valid_runtime_constructor(self):
        proposal, result = self.run_case("hinted")
        self.assertTrue(proposal["speculative_generic"])
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["status"], "CONSTRUCTED_NONNIL_WITH_HINT_REPAIRS")
        self.assertEqual(receipt["source_sha"], SYNTHETIC_SHA)
        self.assertEqual(
            [x["field"] for x in receipt["repairs"]],
            ["NumCounters", "NumCounters", "MaxCost", "BufferItems"],
        )
        self.assertEqual(receipt["attempts"], 5)

    def test_longest_field_name_wins_in_error_string(self):
        _, result = self.run_case("collision")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual([x["field"] for x in receipt["repairs"]], ["MaxCost"])

    def test_opaque_error_abstains_without_guessing(self):
        _, result = self.run_case("opaque")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("UNKNOWN_RUNTIME_HINT_UNMATCHED", result.stderr)


    def test_same_source_error_wording_ablation_is_causal(self):
        original_plan, original_result = self.run_case("hinted")
        masked_plan, masked_result = self.run_case("hinted", mask_errors=True)
        self.assertEqual(original_plan["call"], masked_plan["call"])
        self.assertEqual(original_result.returncode, 0, original_result.stderr)
        self.assertNotEqual(masked_result.returncode, 0)
        self.assertIn("UNKNOWN_RUNTIME_HINT_UNMATCHED", masked_result.stderr)


if __name__ == "__main__":
    unittest.main()
