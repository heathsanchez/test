import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
import trusted_native_receipt as admission


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class NativeEvidenceBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        def git(*argv):
            proc = subprocess.run(["git", *argv], cwd=self.repo,
                                  text=True, capture_output=True, check=False)
            if proc.returncode:
                raise AssertionError(proc.stderr)
            return proc.stdout.strip()
        self.git = git
        git("init", "-q")
        git("config", "user.email", "lab@example.invalid")
        git("config", "user.name", "Bounded Research")
        (self.repo / "sample.go").write_text("package p\n")
        git("add", ".")
        git("commit", "-qm", "base")
        self.base = git("rev-parse", "HEAD")
        code = "package p\nfunc NewInvariant() bool { return false }\n"
        (self.repo / "sample.go").write_text(code)
        git("add", ".")
        git("commit", "-qm", "head")
        self.head = git("rev-parse", "HEAD")
        self.pr = {"repo": "https://github.com/example/demo",
                   "nwo": "example/demo", "pr_number": 7}
        self.evidence = self.root / "trusted"
        self.evidence.mkdir()
        self.native = {
            "source_head": self.head,
            "original_sha256": digest(code.encode()),
            "test_sha256": "c" * 64,
            "golden_reference_used": False,
            "final_source_restored": True,
            "fixture_removed": True,
            "arm": [
                {"name": "original", "actual": "FAIL", "expected": "FAIL", "exit": 1},
                {"name": "candidate_patch", "actual": "PASS", "expected": "PASS", "exit": 0},
                {"name": "removed_patch", "actual": "FAIL", "expected": "FAIL", "exit": 1},
            ],
        }
        (self.evidence / "receipt.json").write_text(json.dumps(self.native))
        logs = {}
        for label in ("original", "candidate_patch", "removed_patch"):
            tag = "PASS" if label == "candidate_patch" else "FAIL"
            content = "=== RUN   TestMGCheckInvariant\n--- " + tag + ": TestMGCheckInvariant (0.00s)\n"
            (self.evidence / (label + ".log")).write_text(content)
            logs[label] = digest(content.encode())
        self.manifest = {
            "schema": "mgcheck-trusted-native-witness-v1",
            "subject": {"repo": "example/demo", "pr_number": 7,
                        "base": self.base, "head": self.head},
            "finding": {"file": "sample.go", "line": 2, "message": "Source-native invariant fails."},
            "evidence": {
                "original_source_sha256": digest(code.encode()),
                "native_receipt_sha256": digest((self.evidence / "receipt.json").read_bytes()),
                "native_test_sha256": "c" * 64,
                "native_test_name": "TestMGCheckInvariant",
                "log_sha256": logs,
            },
        }
        self.seal()

    def seal(self):
        self.b = json.dumps(self.manifest, sort_keys=True).encode()
        (self.evidence / "manifest.json").write_bytes(self.b)
        self.manifest_digest = digest(self.b)

    def changed_lines(self, repo, base, head, file):
        return {2}

    def evaluate(self, pr=None, anchor=None):
        return admission.admit(self.repo, pr or self.pr, self.base, self.head,
                               ["sample.go"], self.changed_lines, self.evidence,
                               self.manifest_digest if anchor is None else anchor)

    def test_exact_subject_and_real_logs_admitted(self):
        findings, state = self.evaluate()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["start_line"], 2)
        self.assertEqual(state["status"], "WARRANTED_BOUNDED_SUBJECT_BOUND_NATIVE_WITNESS")

    def test_modified_manifest_denied(self):
        self.manifest["finding"]["message"] = "forged"
        self.seal()
        self.assertEqual(self.evaluate(anchor="0" * 64)[0], [])

    def test_wrong_subject_and_wrong_source_denied(self):
        findings, state = self.evaluate({"nwo": "other/repo", "pr_number": 7})
        self.assertEqual(findings, [])
        self.assertEqual(state["status"], "UNKNOWN_OTHER_SOURCE_SUBJECT")
        (self.repo / "sample.go").write_text("package p\nfunc NewInvariant() bool { return true }\n")
        self.assertEqual(self.evaluate()[1]["status"], "UNKNOWN_SOURCE_BYTES_CHANGED")

    def test_native_logs_and_outcome_forgery_denied(self):
        (self.evidence / "original.log").write_text("=== RUN   TestMGCheckInvariant\nPASS\n")
        self.assertEqual(self.evaluate()[1]["status"], "UNKNOWN_NATIVE_LOG_DIGEST")
        (self.evidence / "original.log").write_text(
            "=== RUN   TestMGCheckInvariant\n--- FAIL: TestMGCheckInvariant (0.00s)\n")
        self.native["arm"][0]["actual"] = "PASS"
        (self.evidence / "receipt.json").write_text(json.dumps(self.native))
        self.manifest["evidence"]["native_receipt_sha256"] = digest(
            (self.evidence / "receipt.json").read_bytes())
        self.seal()
        self.assertEqual(self.evaluate()[1]["status"], "UNKNOWN_NATIVE_OUTCOME_CONFLICT")

    def test_missing_anchor_denied(self):
        findings, state = admission.admit(self.repo, self.pr, self.base, self.head,
                                           ["sample.go"], self.changed_lines,
                                           self.evidence, "")
        self.assertEqual(findings, [])
        self.assertEqual(state["status"], "UNKNOWN_MISSING_HOST_TRUST_ANCHOR")


if __name__ == "__main__":
    unittest.main()
