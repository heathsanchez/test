"""Native integration tests: genuine Go construction and a rejected zero config."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
PLANNER = HERE / "constructor_planner.go"
BRIDGE = HERE / "native_constructor_bridge.py"
SYNTHETIC_SHA = "1" * 40


class ConstructorNativeTests(unittest.TestCase):
    def run_case(self, fixture: str, module: str):
        with tempfile.TemporaryDirectory(prefix="g3-native-") as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(HERE / "testdata" / fixture, root)
            manifest_path = Path(tmp) / "manifest.json"
            plan = subprocess.run(
                ["go", "run", str(PLANNER), "--source", str(root), "--out", str(manifest_path)],
                text=True, capture_output=True, check=True,
            )
            self.assertEqual(plan.returncode, 0)
            proposal = json.loads(manifest_path.read_text())
            self.assertEqual(proposal["status"], "CANDIDATE_CONSTRUCTOR")
            subprocess.run(
                [sys.executable, str(BRIDGE), "--manifest", str(manifest_path),
                 "--source-dir", str(root), "--module", module, "--sha", SYNTHETIC_SHA],
                text=True, capture_output=True, check=True,
            )
            execution = subprocess.run(["go", "run", "./cmd/mgconstructor"],
                                       cwd=root, text=True, capture_output=True)
            return proposal, execution

    def test_duration_constructor_compiles_and_returns_non_nil(self):
        _, result = self.run_case("duration", "example.com/mg-duration-fixture")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "CONSTRUCTED_NONNIL")
        self.assertEqual(report["constructed_type"], "*duration.Cache")
        self.assertEqual(report["source_sha"], SYNTHETIC_SHA)

    def test_context_helper_constructor_compiles_and_checks_error(self):
        _, result = self.run_case("context_config", "example.com/mg-context-config-fixture")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["constructed_type"], "*client.Client")
        self.assertIn("pkg.Defaults", report["call"])

    def test_generic_zero_configuration_fails_at_native_runtime(self):
        p, result = self.run_case("generic_invalid", "example.com/mg-generic-invalid-fixture")
        self.assertTrue(p["speculative_generic"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("UNKNOWN_NATIVE_CONSTRUCTOR_ERROR", result.stderr)


if __name__ == "__main__":
    unittest.main()
