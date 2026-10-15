"""Regression checks of evidence admission, not native V54 outcome evidence."""
import ast
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import tokenize
import unittest
from unittest.mock import patch
import json

import generate


class FormalEvidenceTests(unittest.TestCase):
    def test_enumeration_matches_pinned_original_loop(self):
        tree = ast.parse(generate.ORIGINAL.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "one_rewrite_discovery")
        source = "if left < 2 and right:\n    pass\n"
        destinations = ["<", "<=", "and", "or"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.py"
            observed = []

            def reset():
                path.write_text(source)

            def native():
                observed.append(generate.sha(path.read_bytes()))
                return False

            env = {"rq_path": path, "line_no": 1, "DESTS": destinations,
                   "make_double_broken": reset, "test_rq": native,
                   "tokenize": tokenize, "io": io}
            exec(compile(ast.Module(body=[function], type_ignores=[]), "pinned-v54", "exec"), env)
            self.assertEqual(env["one_rewrite_discovery"](), [])
            reconstructed = generate.enumerate_rewrites({"source_text": source, "line_no": 1}, destinations)
            self.assertEqual([item["source_sha256"] for item in reconstructed], observed)
            self.assertEqual([item["index"] for item in reconstructed], list(range(len(observed))))

    def test_timeout_and_missing_observation_are_distinct(self):
        self.assertEqual(generate.normalize_call({"id": 1, "status": "native_failure",
                                                 "passed": False, "returncode": 124}), "timedOut")
        self.assertEqual(generate.normalize_call({"id": 2, "status": "native_failure",
                                                 "passed": False, "returncode": 1}), "failed")
        for status in (None, "unknown", "error"):
            with self.assertRaises(ValueError):
                generate.normalize_call({"id": 3, "status": status, "passed": False})

    def test_producer_pass_flag_cannot_override_native_status(self):
        with self.assertRaises(ValueError):
            generate.normalize_call({"id": 4, "status": "native_failure", "passed": True, "returncode": 1})
        with self.assertRaises(ValueError):
            generate.normalize_call({"id": 5, "status": "pass", "passed": True, "returncode": 1})

    def test_malformed_input_invalidates_stale_checked_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native, out = root / "native", root / "formal"
            native.mkdir(); out.mkdir()
            for name in ("GeneratedV54.lean", "transition-table.json", "lean-verification.json"):
                (out / name).write_text("stale checked artifact")
            (native / "native-calls.jsonl").write_text("")
            (native / "snapshot.json").write_text("[]")
            (native / "source-provenance.json").write_text(json.dumps({
                "commit": generate.ORIGINAL_COMMIT, "sha256": generate.ORIGINAL_SHA256,
                "world_pins": {"requests": generate.REQUESTS_COMMIT},
                "relocated_paths": {"requests": "/fixture/requests"}}))
            argv = ["generate.py", "--native-calls", str(native / "native-calls.jsonl"),
                    "--broken", str(native / "snapshot.json"), "--warm", str(native / "snapshot.json"),
                    "--final", str(native / "snapshot.json"), "--output-dir", str(out)]
            with patch("sys.argv", argv), redirect_stdout(io.StringIO()):
                self.assertEqual(generate.main(), 1)
            self.assertEqual(json.loads((out / "evidence-manifest.json").read_text())["status"], "UNKNOWN")
            for name in ("GeneratedV54.lean", "transition-table.json", "lean-verification.json"):
                self.assertFalse((out / name).exists())


if __name__ == "__main__":
    unittest.main()
