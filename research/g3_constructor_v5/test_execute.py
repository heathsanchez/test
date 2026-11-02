"""Native integration against self-contained source-pinned Go fixtures."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from execute import run_target


HERE = Path(__file__).resolve().parent


def git(*args: str, cwd: Path) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, check=True,
                       capture_output=True, text=True)
    return p.stdout.strip()


class SourceBoundNativeTest(unittest.TestCase):
    def test_legacy_moduleless_native_trace_and_operation_ablation(self):
        with tempfile.TemporaryDirectory() as t:
            repo, sha = self.make_repo(Path(t), "legacy")
            self.assertFalse((repo / "go.mod").exists())
            result = run_target(repo, sha, Path(t) / "logs", repo_name="fixture/legacy")
            self.assertEqual(result["status"], "WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY", result)
            self.assertEqual(result["environment"], "TEMPORARY_LEGACY_MODULE_OVERLAY")
            self.assertEqual(result["withdrawal"]["status"], "EXPECTED_MUTATOR_WITHDRAWAL")
            self.assertEqual(result["restoration"]["status"], "NATIVE_CACHE_TRACE_PASS")

    def test_generic_dual_result_add_native_trace(self):
        with tempfile.TemporaryDirectory() as t:
            repo, sha = self.make_repo(Path(t), "dual")
            result = run_target(repo, sha, Path(t) / "logs")
            self.assertEqual(result["status"], "WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY", result)
            self.assertTrue(result["plan"]["returns_error"])
            self.assertEqual(result["native"]["status"], "NATIVE_CACHE_TRACE_PASS")
            self.assertEqual(result["withdrawal"]["status"], "EXPECTED_TYPE_ABLATION_COMPILE_FAILURE")
            self.assertEqual(result["restoration"]["status"], "NATIVE_CACHE_TRACE_PASS")

    def make_repo(self, root: Path, name: str):
        repo = root / name
        shutil.copytree(HERE / "testdata" / name, repo)
        git("init", "--quiet", cwd=repo)
        git("add", ".", cwd=repo)
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "--quiet", "-m", "fixture", cwd=repo)
        return repo, git("rev-parse", "HEAD", cwd=repo)

    def test_wrong_source_digest_abstains_before_native(self):
        with tempfile.TemporaryDirectory() as t:
            repo, sha = self.make_repo(Path(t), "dual")
            with (repo / "cache.go").open("a") as f:
                f.write("\n// source mutation after freeze\n")
            result = run_target(repo, sha, Path(t) / "logs")
            self.assertEqual(result["status"], "UNKNOWN_DIRTY_SOURCE")
            self.assertNotIn("native", result)

    def test_broken_real_set_rejected_not_promoted(self):
        with tempfile.TemporaryDirectory() as t:
            repo, sha = self.make_repo(Path(t), "broken")
            result = run_target(repo, sha, Path(t) / "logs")
            self.assertEqual(result["status"], "UNKNOWN_NATIVE_SEMANTIC_TRACE")
            self.assertEqual(result["native"]["status"], "UNKNOWN_READBACK_MISMATCH")
            self.assertEqual(result["strict_g3"], "UNKNOWN")

    def test_sha_mismatch_fails_before_native_execution(self):
        with tempfile.TemporaryDirectory() as t:
            repo, _ = self.make_repo(Path(t), "builder")
            result = run_target(repo, "0" * 40, Path(t) / "logs")
            self.assertEqual(result["status"], "UNKNOWN_SOURCE_SHA_MISMATCH")
            self.assertNotIn("native", result)

    def test_builder_native_trace_withdrawal_restoration(self):
        with tempfile.TemporaryDirectory() as t:
            repo, sha = self.make_repo(Path(t), "builder")
            result = run_target(repo, sha, Path(t) / "logs")
            self.assertEqual(result["status"], "WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY")
            self.assertEqual(result["native"]["status"], "NATIVE_CACHE_TRACE_PASS")
            self.assertTrue(result["native"]["used_build"])
            self.assertEqual(result["withdrawal"]["status"], "UNKNOWN_NO_OPERATIONAL_REACHABILITY")
            self.assertEqual(result["restoration"]["status"], "NATIVE_CACHE_TRACE_PASS")
            self.assertEqual(result["strict_g3"], "UNKNOWN")
            self.assertEqual(result["fair_b1"], "NOT_TESTED")

    def test_generic_native_trace_type_ablation_restoration(self):
        with tempfile.TemporaryDirectory() as t:
            repo, sha = self.make_repo(Path(t), "generic")
            result = run_target(repo, sha, Path(t) / "logs")
            self.assertEqual(result["status"], "WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY")
            self.assertEqual(result["plan"]["call"], "pkg.New[string,string]()")
            self.assertEqual(result["native"]["status"], "NATIVE_CACHE_TRACE_PASS")
            self.assertFalse(result["native"]["used_build"])
            self.assertEqual(result["withdrawal"]["status"], "EXPECTED_TYPE_ABLATION_COMPILE_FAILURE")
            self.assertEqual(result["restoration"]["status"], "NATIVE_CACHE_TRACE_PASS")


if __name__ == "__main__":
    unittest.main()
