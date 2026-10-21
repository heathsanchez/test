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
import keyword

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

    def test_missing_cold_observation_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native, out = root / "native", root / "formal"
            native.mkdir()
            states = {"broken": "if x < 1 and y:\n    pass\n",
                      "warm": "if x <= 1 and y:\n    pass\n",
                      "final": "if x <= 1 or y:\n    pass\n"}
            for name, source in states.items():
                (native / f"{name}.json").write_text(json.dumps({
                    "source_text": source, "source_sha256": generate.sha(source.encode()),
                    "line_no": 1, "path": "/fixture/requests/" + generate.TARGET_FILE,
                    "scope": {"world": "requests", "relative_path": generate.TARGET_FILE,
                              "line_no": 1, "first_word": "if"}}))
            destinations = sorted(set([s for s in tokenize.EXACT_TOKEN_TYPES if 1 <= len(s) <= 2] + keyword.kwlist))
            candidates = generate.enumerate_rewrites({"source_text": states["broken"], "line_no": 1}, destinations)
            calls = [{"id": c["index"], "phase": "cold",
                      "candidate_source_sha256": {generate.TARGET_FILE: c["source_sha256"]}}
                     for c in candidates[:-1]]
            (native / "native-calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))
            (native / "source-provenance.json").write_text(json.dumps({
                "commit": generate.ORIGINAL_COMMIT, "sha256": generate.ORIGINAL_SHA256,
                "world_pins": {"requests": generate.REQUESTS_COMMIT},
                "relocated_paths": {"requests": "/fixture/requests"}}))
            argv = ["generate.py", "--native-calls", str(native / "native-calls.jsonl"),
                    "--broken", str(native / "broken.json"), "--warm", str(native / "warm.json"),
                    "--final", str(native / "final.json"), "--output-dir", str(out)]
            with patch("sys.argv", argv), redirect_stdout(io.StringIO()):
                self.assertEqual(generate.main(), 1)
            manifest = json.loads((out / "evidence-manifest.json").read_text())
            self.assertEqual(manifest["status"], "UNKNOWN")
            self.assertIn("Incomplete or reordered", manifest["reason"])
            self.assertFalse((out / "GeneratedV54.lean").exists())


if __name__ == "__main__":
    unittest.main()
