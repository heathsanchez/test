"""Independent guard tests for the budget-only full-source experiment."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("budget4x_runner", ROOT / "runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Budget4xRunnerTests(unittest.TestCase):
    def test_terminal_codes_cannot_promote_unknown(self):
        self.assertEqual(runner.classify_exit(0), "ACCEPT")
        self.assertEqual(runner.classify_exit(1), "REJECT")
        self.assertEqual(runner.classify_exit(2), "UNKNOWN")
        self.assertEqual(runner.classify_exit(124), "TIMEOUT")
        self.assertEqual(runner.classify_exit(-9), "ERROR")

    def test_known_200_verdicts_preserved_while_unknown_may_improve(self):
        rows = [
            {"case": "good/unchanged", "expected": 0, "rc": 0},
            {"case": "bad/forged", "expected": 1, "rc": 1},
            {"case": "good/old-unknown", "expected": 0, "rc": 0},
        ]
        self.assertTrue(runner.protected_nonregression(rows, {"good/old-unknown"}, 3))
        rows[2]["rc"] = 2
        self.assertTrue(runner.protected_nonregression(rows, {"good/old-unknown"}, 3))
        rows[1]["rc"] = 0
        self.assertFalse(runner.protected_nonregression(rows, {"good/old-unknown"}, 3))
        rows[1]["rc"] = 2
        self.assertFalse(runner.protected_nonregression(rows, {"good/old-unknown"}, 3))
        rows[1]["rc"] = 1
        rows[0]["rc"] = 2
        self.assertFalse(runner.protected_nonregression(rows, {"good/old-unknown"}, 3))

    def test_frontier_extracts_exact_source_prefix(self):
        records = [
            {"in": 1, "str": {"pre": 0, "str": "Foo"}},
            {"in": 2, "str": {"pre": 1, "str": "Bar"}},
            {"thm": {"name": 2, "type": 12, "value": 42}},
            {"in": 3, "str": {"pre": 0, "str": "Other"}},
        ]
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            source = folder / "source.ndjson"
            source.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in records))
            info = runner.extract_frontier(source, folder / "frontier.ndjson", "Foo.Bar")
            self.assertEqual(info["record"], 3)
            self.assertEqual(info["tag"], "thm")
            self.assertTrue(info["retained"])
            self.assertTrue((folder / "frontier.ndjson.zst").is_file())

    def test_frontier_cap_and_unknown_name_fail_closed(self):
        records = [
            {"in": 1, "str": {"pre": 0, "str": "Foo"}},
            {"thm": {"name": 1}},
        ]
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            source = folder / "source.ndjson"
            source.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in records))
            dest = folder / "frontier.ndjson"
            info = runner.extract_frontier(source, dest, "Foo", max_prefix_bytes=5)
            self.assertEqual(info["record"], 2)
            self.assertFalse(info["retained"])
            self.assertFalse(dest.exists())
            self.assertFalse((folder / "frontier.ndjson.zst").exists())
            self.assertIsNone(runner.extract_frontier(source, dest, "NotPresent"))


if __name__ == "__main__":
    unittest.main()
