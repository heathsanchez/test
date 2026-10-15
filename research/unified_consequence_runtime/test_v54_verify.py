"""Independent V54 authority checks, including native causal negative controls."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ADAPTER = Path(__file__).with_name("v54_verify.py")
SOURCE = Path(os.environ.get("V54_SOURCE", "/workspace/repos/triskelion"))
WORLDS = Path(os.environ.get("V54_WORLDS", "/workspace/v54-worlds"))
PYTHON = Path(os.environ.get("V54_PYTHON", "/workspace/v54-venv/bin/python"))
O1 = {"kind": "TOKEN_REWRITE", "src": "<", "dst": "<="}
O2 = {"kind": "TOKEN_REWRITE", "src": "and", "dst": "or"}


def adapter():
    spec = importlib.util.spec_from_file_location("v54_verify_test_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V54InputBindingTests(unittest.TestCase):
    def setUp(self):
        self.module = adapter()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def verify(self, stage, program):
        return self.module.verify(stage, program, SOURCE, WORLDS, self.root / "receipt.json", python_path=PYTHON)

    def test_wrong_scope_is_rejected_without_evaluating_native_tests(self):
        receipt = self.verify("o1", {"operators": [O1], "scope_word": "while"})
        self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(receipt["reason"], "scope_out_of_scope")
        self.assertFalse(receipt["evaluated"])

    def test_missing_code_cannot_be_replaced_by_forged_success_evidence(self):
        receipt = self.verify("final", {"operators": [], "scope_word": "if", "evidence": {"status": "accepted", "native_score": 1.0}})
        self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(receipt["reason"], "missing_or_extra_operator")
        self.assertFalse(receipt["evaluated"])

    def test_altered_executable_kind_is_rejected(self):
        receipt = self.verify("o1", {"operators": [dict(O1, kind="REPORT_SUCCESS")], "scope_word": "if"})
        self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(receipt["reason"], "operator_code_missing_or_altered")

    def test_embedded_code_is_rejected(self):
        receipt = self.verify("o1", {"operators": [dict(O1, dst="<=\nimport forged")], "scope_word": "if"})
        self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(receipt["reason"], "operator_code_missing_or_altered")

    def test_wrong_task_stage_is_rejected(self):
        receipt = self.verify("webarena:62", {"operators": [O1, O2], "scope_word": "if"})
        self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(receipt["reason"], "task_out_of_scope")
        self.assertFalse(receipt["evaluated"])

    def test_wrong_task_wrapper_is_rejected(self):
        receipt = self.verify("o1", {"operators": [O1], "scope_word": "if", "task": "other"})
        self.assertEqual(receipt["status"], "rejected")
        self.assertEqual(receipt["reason"], "task_out_of_scope")

    def test_original_source_bytes_are_pinned(self):
        with patch.object(self.module, "_git", return_value=b"print('forged authority')\n"):
            with self.assertRaisesRegex(self.module.V54VerificationError, "original_source_pin_mismatch"):
                self.module.source_bytes(SOURCE)

    def test_receipt_is_created_once_and_read_only(self):
        receipt = self.verify("other", [O1])
        path = self.root / "receipt.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o444)
        self.assertEqual(json.loads(path.read_text()), receipt)
        with self.assertRaises(FileExistsError):
            self.verify("other", [O1])

    def test_executed_program_is_a_frozen_copy_of_caller_input(self):
        program = {"operators": [dict(O1)], "scope_word": "if"}
        original_hash = self.module._sha(self.module._json_bytes(program))
        original_validation = self.module._program
        def validate_then_mutate(frozen, stage):
            operators = original_validation(frozen, stage)
            program["operators"][0]["dst"] = "=="
            self.assertEqual(operators[0]["dst"], "<=")
            raise self.module.V54VerificationError("test_stops_before_native_execution")
        with patch.object(self.module, "_program", side_effect=validate_then_mutate):
            receipt = self.verify("o1", program)
        self.assertEqual(receipt["program_sha256"], original_hash)

    def test_timeout_without_verified_native_imports_is_never_a_negative_witness(self):
        snapshots, files = {}, {}
        for world in self.module.WORLD_PINS:
            root = self.root / world
            root.mkdir()
            (root / "placeholder.py").write_text("pass\n")
            snapshots[world], files[world] = root, ["placeholder.py"]
        env = self.module._original_environment(self.module.source_bytes(SOURCE))
        authority = self.module._NativeAuthority(env, snapshots, files, self.root, PYTHON)
        command = self.module.TESTS["requests_iter_slices"][2]
        with patch.object(self.module.subprocess, "run", side_effect=subprocess.TimeoutExpired(command, 7)):
            with self.assertRaisesRegex(self.module.V54VerificationError, "native_source_or_import_integrity_failure"):
                authority.sh(command, snapshots["requests"])


@unittest.skipUnless(PYTHON.is_file() and all((WORLDS / name / ".git").exists() for name in ("django", "requests", "rich")), "Pinned V54 native worlds and dependencies are required")
class V54NativeVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = adapter()
        cls.directory = tempfile.TemporaryDirectory(prefix="test-v54-native-")
        cls.root = Path(cls.directory.name)
        cls.program = {"operators": [O1, O2], "scope_word": "if"}
        cls.receipt = cls.module.verify("final", cls.program, SOURCE, WORLDS, cls.root / "final.json", python_path=PYTHON)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_actual_native_program_passes_all_causal_gates(self):
        self.assertEqual(self.receipt["status"], "accepted", self.receipt)
        self.assertTrue(all(self.receipt["gates"].values()))
        self.assertTrue(self.receipt["source_unchanged"])
        self.assertEqual(self.receipt["source_commit"], self.module.SOURCE_COMMIT)
        self.assertEqual(self.receipt["source_sha256"], self.module.SOURCE_SHA256)
        self.assertEqual(self.receipt["program_sha256"], hashlib.sha256(self.module._json_bytes(self.program)).hexdigest())
        self.assertEqual({name: value["commit"] for name, value in self.receipt["native_pins"].items()}, self.module.WORLD_PINS)

    def test_native_negative_controls_are_real_failed_test_processes(self):
        by_label = {entry["label"]: entry for entry in self.receipt["native_receipts"]}
        for label in ("rich:deliberately_global_O1", "requests:double_broken", "requests:O1_only", "requests:O1_ablated"):
            with self.subTest(label=label):
                entry = by_label[label]
                self.assertFalse(entry["passed"])
                self.assertTrue(entry["timed_out"] or entry["exit_code"] != 0)
        self.assertTrue(by_label["rich:scoped_O1"]["passed"])
        self.assertTrue(by_label["requests:O1_then_O2"]["passed"])
        for entry in by_label.values():
            self.assertTrue(entry["source_unchanged"])
            self.assertTrue(entry["imports_verified"], entry)

    def test_changed_receipt_or_scope_or_code_cannot_replay_exact_binding(self):
        self.assertTrue(self.module.receipt_binding_valid(self.receipt, "final", self.program))
        changed = copy.deepcopy(self.receipt)
        changed["native_receipts"][-1]["passed"] = True
        self.assertFalse(self.module.receipt_binding_valid(changed, "final", self.program))
        self.assertFalse(self.module.receipt_binding_valid(self.receipt, "o1", self.program))
        self.assertFalse(self.module.receipt_binding_valid(self.receipt, "final", dict(self.program, scope_word="while")))
        self.assertFalse(self.module.receipt_binding_valid(self.receipt, "final", {"operators": [O1], "scope_word": "if"}))

    def test_dirty_producer_tree_and_untracked_bytecode_are_ignored(self):
        repo = self.root / "spoofed-rich"
        subprocess.run(["git", "clone", "--shared", "--no-checkout", str(WORLDS / "rich"), str(repo)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        (repo / "rich").mkdir()
        (repo / "rich/highlighter.py").write_text("raise AssertionError('producer spoof')\n")
        (repo / "rich/forged.pyc").write_bytes(b"forged bytecode")
        target = self.root / "clean-rich"
        pin, files = self.module._snapshot(repo, self.module.WORLD_PINS["rich"], target)
        self.assertNotIn("rich/forged.pyc", files)
        self.assertNotIn("producer spoof", (target / "rich/highlighter.py").read_text())
        self.assertEqual(pin["source_sha256"], self.receipt["native_pins"]["rich"]["source_sha256"])

    def test_producer_local_archive_attributes_cannot_change_pinned_tree(self):
        repo = self.root / "attribute-spoofed-rich"
        subprocess.run(["git", "clone", "--shared", "--no-checkout", str(WORLDS / "rich"), str(repo)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        (repo / ".git/info/attributes").write_text("rich/highlighter.py export-ignore\n")
        with self.assertRaisesRegex(self.module.V54VerificationError, "native_archive_tree_mismatch"):
            self.module._snapshot(repo, self.module.WORLD_PINS["rich"], self.root / "attribute-snapshot")

    def test_forged_producer_success_does_not_rescue_altered_operator(self):
        program = {"operators": [dict(O1, dst="=="), O2], "scope_word": "if", "evidence": self.receipt}
        result = self.module.verify("final", program, SOURCE, WORLDS, self.root / "altered.json", python_path=PYTHON)
        self.assertEqual(result["status"], "rejected", result)
        self.assertTrue(result["evaluated"])
        self.assertEqual(result["reason"], "native_failure")
        self.assertTrue(any(not entry["passed"] for entry in result["native_receipts"]))

    def test_isolated_cli_rejects_wrong_scope_and_binds_program(self):
        program = self.root / "operators.json"
        program.write_text(json.dumps(self.program))
        output = self.root / "wrong-scope-cli.json"
        process = subprocess.run([str(PYTHON), "-I", str(ADAPTER), "--source", str(SOURCE), "--worlds", str(WORLDS), "--operators", str(program), "--scope", "while", "--stage", "final", "--out", str(output)], capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(output.read_text())["reason"], "scope_out_of_scope")


if __name__ == "__main__":
    unittest.main()
