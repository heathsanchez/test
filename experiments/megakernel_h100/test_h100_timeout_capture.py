"""Exercise interrupted stage evidence capture without a GPU or RunPod credentials."""
import ast
import hashlib
from pathlib import Path
import subprocess
import time
import unittest
from unittest.mock import patch

BRIDGE = Path(__file__).with_name("runpod_flash_h100_bridge.py")


def load_stage(report):
    module = ast.parse(BRIDGE.read_text())
    worker = next(n for n in module.body if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == "run_h100_differential")
    stage = next(n for n in worker.body if isinstance(n, ast.FunctionDef) and n.name == "stage")
    wrapper = ast.fix_missing_locations(ast.Module(body=[stage], type_ignores=[]))
    scope = {"subprocess": subprocess, "hashlib": hashlib, "time": time, "report": report}
    exec(compile(wrapper, str(BRIDGE), "exec"), scope)
    return scope["stage"]


class TimeoutEvidenceTests(unittest.TestCase):
    def test_timeout_retains_partial_stdout_stderr(self):
        report = {"stages": []}
        stage = load_stage(report)
        fail = subprocess.TimeoutExpired(
            cmd=["python", "-u", "diff.py"], timeout=180,
            output=b"interpreting with pyvm...\\n",
            stderr=b"partial diagnostic\\n",
        )
        with patch.object(subprocess, "run", side_effect=fail):
            with self.assertRaises(subprocess.TimeoutExpired):
                stage("diff_rr", ["python", "-u", "diff.py"], 180)
        self.assertEqual(len(report["stages"]), 1)
        entry = report["stages"][0]
        self.assertEqual(entry["name"], "diff_rr")
        self.assertTrue(entry["timed_out"])
        self.assertEqual(entry["timeout_seconds"], 180)
        self.assertIn("interpreting with pyvm", entry["output_tail"])
        self.assertIn("partial diagnostic", entry["output_tail"])
        self.assertTrue(entry["output_sha256"])

    def test_diff_subprocess_uses_unbuffered_python(self):
        source = BRIDGE.read_text()
        self.assertIn('stage(f"diff_{sched}", [sys.executable, "-u", str(gate)', source)


if __name__ == "__main__":
    unittest.main()
