"""Real native evaluator checks for the frozen developmental task scope."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ADAPTER = Path(__file__).with_name("developmental_verify.py")
PYTHON = Path(sys.executable)
EVALUATOR = Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified'))
ARCHIVE = Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))
COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"


class NativeVerifierTests(unittest.TestCase):
    def adapter(self):
        self.assertTrue(ADAPTER.is_file(), "Native verifier adapter has not been implemented")
        spec = importlib.util.spec_from_file_location("developmental_verify", ADAPTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def verify(self, response, task_id, config=None):
        return self.adapter().verify(
            response,
            task_id,
            config or ARCHIVE / "config.json",
            evaluator_path=EVALUATOR,
        )

    def test_archived_native_responses_pass_and_bind_exact_bytes(self):
        for family, task_id in (("e", 62), ("e", 64), ("e", 65), ("d", 168), ("d", 169), ("d", 172)):
            with self.subTest(task_id=task_id):
                response = ARCHIVE / family / str(task_id) / "agent_response.json"
                verdict = self.verify(response, task_id)
                self.assertEqual(verdict["status"], "accepted", verdict)
                self.assertEqual(verdict["score"], 1.0)
                self.assertEqual(verdict["native_status"], "success")
                self.assertEqual(verdict["task_id"], task_id)
                self.assertEqual(verdict["intent_template_id"], 276 if family == "e" else 289)
                self.assertEqual(verdict["response_sha256"], hashlib.sha256(response.read_bytes()).hexdigest())
                self.assertEqual(verdict["verifier_source_commit"], COMMIT)
                self.assertEqual(verdict["scope"], "frozen_original_tasks")
                self.assertGreaterEqual(verdict["elapsed_seconds"], 0)
                self.assertNotIn("expected", json.dumps(verdict))

    def test_wrong_not_found_is_rejected_by_native_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "agent_response.json"
            response.write_text(json.dumps({"task_type": "RETRIEVE", "status": "NOT_FOUND_ERROR", "retrieved_data": None, "error_details": None}))
            for task_id in (62, 63, 64, 65, 169, 172):
                with self.subTest(task_id=task_id):
                    verdict = self.verify(response, task_id)
                    self.assertEqual(verdict["status"], "rejected", verdict)
                    self.assertTrue(verdict["evaluated"])
                    self.assertEqual(verdict["native_status"], "failure")
                    self.assertEqual(verdict["native_score"], 0.0)
                    self.assertEqual(verdict["score"], 0.0)

    def test_out_of_scope_task_is_rejected_without_evaluation(self):
        verdict = self.verify(ARCHIVE / "e/62/agent_response.json", 61)
        self.assertEqual(verdict["status"], "rejected")
        self.assertEqual(verdict["reason"], "task_out_of_scope")
        self.assertFalse(verdict["evaluated"])
        self.assertEqual(verdict["score"], 0.0)

    def test_changed_template_cannot_override_frozen_dataset(self):
        self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            data_path = Path(directory) / "dataset.json"
            dataset = json.loads((EVALUATOR / "assets/dataset/webarena-verified.json").read_text())
            next(task for task in dataset if task["task_id"] == 62)["intent_template_id"] = 277
            data_path.write_text(json.dumps(dataset))
            config = json.loads((ARCHIVE / "config.json").read_text())
            config["test_data_file"] = str(data_path)
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps(config))
            verdict = self.verify(ARCHIVE / "e/62/agent_response.json", 62, config_path)
            self.assertEqual(verdict["status"], "rejected", verdict)
            self.assertEqual(verdict["reason"], "dataset_pin_mismatch")
            self.assertFalse(verdict["evaluated"])

    def test_source_change_is_rejected_before_oracle_import(self):
        adapter = self.adapter()
        import webarena_verified
        package = Path(webarena_verified.__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "webarena_verified"
            shutil.copytree(package, copy, ignore=shutil.ignore_patterns("__pycache__"))
            source = copy / "api/internal/evaluator.py"
            source.write_bytes(source.read_bytes() + b"\n# tampered native source\n")
            with self.assertRaisesRegex(adapter.VerifierPinError, "installed_package_pin_mismatch"):
                adapter.verify_package_pin(copy, EVALUATOR)

    def test_untracked_oracle_code_is_rejected(self):
        adapter = self.adapter()
        import webarena_verified
        package = Path(webarena_verified.__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "webarena_verified"
            shutil.copytree(package, copy, ignore=shutil.ignore_patterns("__pycache__"))
            (copy / "new_oracle.py").write_text("score = 1\n")
            with self.assertRaisesRegex(adapter.VerifierPinError, "installed_package_pin_mismatch"):
                adapter.verify_package_pin(copy, EVALUATOR)

    def test_byte_changes_change_artifact_binding_without_changing_native_result(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            value = json.loads((ARCHIVE / "e/62/agent_response.json").read_text())
            first.write_text(json.dumps(value))
            second.write_text(json.dumps(value, indent=2) + "\n")
            v1, v2 = self.verify(first, 62), self.verify(second, 62)
            self.assertEqual(v1["status"], "accepted")
            self.assertEqual(v2["status"], "accepted")
            self.assertNotEqual(v1["response_sha256"], v2["response_sha256"])

    def test_independent_isolated_cli_writes_native_failure_verdict(self):
        self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "agent_response.json"
            response.write_text('{"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":null,"error_details":null}')
            output = Path(directory) / "verdict.json"
            process = subprocess.run(
                [str(PYTHON), "-I", str(ADAPTER), "--response", str(response), "--task-id", "62", "--config", str(ARCHIVE / "config.json"), "--evaluator", str(EVALUATOR), "--out", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            verdict = json.loads(output.read_text())
            self.assertEqual(verdict["status"], "rejected")
            self.assertEqual(verdict["score"], 0.0)
            self.assertEqual(verdict["native_status"], "failure")
            self.assertEqual(verdict["response_sha256"], hashlib.sha256(response.read_bytes()).hexdigest())

    def test_independent_isolated_cli_accepts_original_and_rejects_cross_task_replay(self):
        self.adapter()
        response = ARCHIVE / "d/169/agent_response.json"
        with tempfile.TemporaryDirectory() as directory:
            for task_id, status, score in ((169, "accepted", 1.0), (172, "rejected", 0.0)):
                with self.subTest(task_id=task_id):
                    output = Path(directory) / f"verdict-{task_id}.json"
                    process = subprocess.run(
                        [str(PYTHON), "-I", str(ADAPTER), "--response", str(response), "--task-id", str(task_id), "--config", str(ARCHIVE / "config.json"), "--evaluator", str(EVALUATOR), "--out", str(output)],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(process.returncode, 0, process.stderr)
                    verdict = json.loads(output.read_text())
                    self.assertEqual(verdict["status"], status, verdict)
                    self.assertEqual(verdict["score"], score)
                    self.assertEqual(verdict["native_score"], score)
                    self.assertEqual(verdict["task_id"], task_id)
                    self.assertEqual(verdict["intent_template_id"], 289)
                    self.assertEqual(verdict["verifier_source_commit"], COMMIT)
                    self.assertEqual(verdict["response_sha256"], hashlib.sha256(response.read_bytes()).hexdigest())

    def test_native_imports_compile_pinned_source_instead_of_cached_bytecode(self):
        self.verify(ARCHIVE / "e/62/agent_response.json", 62)
        import sys
        import webarena_verified
        package = Path(webarena_verified.__file__).resolve().parent
        native_modules = [module for name, module in sys.modules.items() if name == "webarena_verified" or name.startswith("webarena_verified.")]
        self.assertTrue(native_modules)
        for module in native_modules:
            with self.subTest(module=module.__name__):
                source = Path(module.__file__)
                self.assertTrue(source.is_relative_to(package))
                self.assertEqual(
                    getattr(module.__loader__, "verified_source_sha256", None),
                    hashlib.sha256(source.read_bytes()).hexdigest(),
                    "Native module was not compiled by the pinned source loader",
                )

    def test_missing_response_is_an_error_and_never_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            verdict = self.verify(Path(directory) / "missing.json", 62)
            self.assertEqual(verdict["status"], "error")
            self.assertFalse(verdict["evaluated"])
            self.assertEqual(verdict["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
