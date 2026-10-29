"""Probe a generic cold callable export; not Metatron admission or native science."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ORIGINAL_SOURCE_SHA = "e4bf4175331252c2b2d2d192ca80999ee8ba377c9116349ebfbd3bd1de39849c"
ORIGINAL_DEP_SHA = "96e61d23420684ec77d93ed94a8a0e3ba319eac643175206e279daf8e3b5e5df"


class ColdSourceCallTests(unittest.TestCase):
    def manifest(self):
        return {
            "schema": "research.source-call.v0",
            "root": str(REPO),
            "module": "scripts/webarena_two_capability_composition_v1.py",
            "sha256": ORIGINAL_SOURCE_SHA,
            "dependencies": {
                "scripts/webarena_compounding_economics_v1.py": ORIGINAL_DEP_SHA,
            },
            "exports": ["select_winners"],
        }

    def invoke(self, manifest, payload):
        with tempfile.TemporaryDirectory(prefix="source-call-") as scratch:
            manifest_path = Path(scratch) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            return subprocess.run(
                [sys.executable, str(HERE / "cold_call.py"), str(manifest_path)],
                input=json.dumps(payload), text=True, capture_output=True,
                check=False, timeout=15,
            )

    def test_fresh_process_executes_source_function_on_archived_observation(self):
        # The original source-observed customer identity, not an answer from the loader.
        archive = REPO / "historical_composition"
        observation = json.loads((archive / "observation.json").read_text())
        evidence = json.loads((archive / "source_detail.json").read_text())
        payload = {
            "symbol": "select_winners",
            "args": [observation, "customer email", "cancelled"],
        }
        result = self.invoke(self.manifest(), payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["result"], [evidence["selected_customer"]])
        self.assertEqual(report["state"], "EXECUTED_UNTYPED_NOT_ADMITTED")

    def test_wrong_source_digest_denies_before_import(self):
        manifest = self.manifest()
        manifest["sha256"] = "0" * 64
        result = self.invoke(manifest, {"symbol": "select_winners", "args": []})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_DIGEST_MISMATCH", result.stderr)

    def test_wrong_dependency_digest_denies_before_import(self):
        manifest = self.manifest()
        manifest["dependencies"]["scripts/webarena_compounding_economics_v1.py"] = "0" * 64
        result = self.invoke(manifest, {"symbol": "select_winners", "args": []})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEPENDENCY_DIGEST_MISMATCH", result.stderr)

    def test_unexported_source_symbol_denied(self):
        result = self.invoke(self.manifest(), {"symbol": "read", "args": []})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SYMBOL_NOT_EXPORTED", result.stderr)


if __name__ == "__main__":
    unittest.main()
