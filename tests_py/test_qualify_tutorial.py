import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.qualify_tutorial import (
    CaseResult,
    TutorialCase,
    build_summary,
    load_declared_suite,
)


CANDIDATE = "a" * 40
ARENA = "b" * 40


class TutorialInputTests(unittest.TestCase):
    def test_declared_suite_rejects_filename_drift_even_when_number_and_bytes_match(self):
        payload = b'{"kind":"test"}\n'
        manifest = (
            TutorialCase(
                number="001",
                relative_path=Path("good/001_basicDef.ndjson"),
                expected_exit_code=0,
                sha256=hashlib.sha256(payload).hexdigest(),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "good").mkdir()
            (root / "good/001_renamed.ndjson").write_bytes(payload)

            with self.assertRaisesRegex(ValueError, "expected good/001_basicDef.ndjson"):
                load_declared_suite(root, manifest=manifest)

    def test_declared_suite_rejects_hash_drift(self):
        manifest = (
            TutorialCase(
                number="001",
                relative_path=Path("good/001_basicDef.ndjson"),
                expected_exit_code=0,
                sha256=hashlib.sha256(b"expected").hexdigest(),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "good").mkdir()
            (root / "good/001_basicDef.ndjson").write_bytes(b"changed")

            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                load_declared_suite(root, manifest=manifest)


class TutorialSummaryTests(unittest.TestCase):
    def test_summary_preserves_manifest_order_and_exact_exit_contract(self):
        manifest = (
            TutorialCase("001", Path("good/001_basicDef.ndjson"), 0, "1" * 64),
            TutorialCase("002", Path("bad/002_badDef.ndjson"), 1, "2" * 64),
        )
        summary = build_summary(
            candidate_sha=CANDIDATE,
            arena_sha=ARENA,
            manifest=manifest,
            results=(
                CaseResult("002", 1),
                CaseResult("001", 0),
            ),
        )

        self.assertEqual([case["number"] for case in summary["cases"]], ["001", "002"])
        self.assertEqual(summary["expected_exit_codes"], [0, 1])
        self.assertEqual(summary["counts"], {"incorrect": 0, "matched": 2})
        self.assertTrue(summary["qualified"])
        self.assertEqual(summary["cases"][0]["input_sha256"], "1" * 64)

    def test_summary_fails_qualification_on_exit_mismatch(self):
        manifest = (
            TutorialCase("009", Path("bad/009_forallSortBad.ndjson"), 1, "9" * 64),
        )
        summary = build_summary(
            candidate_sha=CANDIDATE,
            arena_sha=ARENA,
            manifest=manifest,
            results=(CaseResult("009", 2),),
        )

        self.assertEqual(summary["counts"], {"incorrect": 1, "matched": 0})
        self.assertEqual(summary["cases"][0]["status"], "incorrect")
        self.assertFalse(summary["qualified"])


if __name__ == "__main__":
    unittest.main()
