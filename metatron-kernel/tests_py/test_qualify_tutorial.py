import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.qualify_tutorial import (
    CaseResult,
    TUTORIAL_MANIFEST,
    TutorialCase,
    build_differential_summary,
    build_summary,
    load_declared_suite,
)


CANDIDATE = "a" * 40
ARENA = "b" * 40


class TutorialInputTests(unittest.TestCase):
    def test_production_manifest_pins_punit_as_case_042(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 42)
        case = TUTORIAL_MANIFEST[41]
        self.assertEqual(case.number, "042")
        self.assertEqual(case.relative_path, Path("good/042_pUnitType.ndjson"))
        self.assertEqual(case.expected_exit_code, 0)
        self.assertEqual(
            case.sha256,
            "acc7a70c97888e02e2b92e583b370803db0bdac1ddc38f9ff036831459d3a891",
        )

    def test_production_manifest_pins_eq_as_case_043(self):
        self.assertEqual(len(TUTORIAL_MANIFEST), 43)
        case = TUTORIAL_MANIFEST[42]
        self.assertEqual(case.number, "043")
        self.assertEqual(case.relative_path, Path("good/043_eqType.ndjson"))
        self.assertEqual(case.expected_exit_code, 0)
        self.assertEqual(
            case.sha256,
            "d45ed54cc74be3d7d92aae6bacc040420ba33f23fa034b4497edb389e089afdc",
        )

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


class DifferentialSummaryTests(unittest.TestCase):
    def test_zero_authority_refactor_requires_exact_oracle_equivalence(self):
        manifest = (
            TutorialCase("039", Path("good/039_andType.ndjson"), 0, "3" * 64),
            TutorialCase("040", Path("good/040_prodType.ndjson"), 0, "4" * 64),
            TutorialCase("041", Path("good/041_pprodType.ndjson"), 0, "5" * 64),
        )
        try:
            summary = build_differential_summary(
                oracle_sha="b" * 40,
                candidate_sha="c" * 40,
                manifest=manifest,
                oracle_results=(
                    CaseResult("039", 0),
                    CaseResult("040", 0),
                    CaseResult("041", 0),
                ),
                candidate_results=(
                    CaseResult("039", 0),
                    CaseResult("040", 0),
                    CaseResult("041", 0),
                ),
                earned_case=None,
                earned_oracle_exit=2,
                earned_candidate_exit=0,
            )
        except ValueError as error:
            self.fail(f"zero-delta qualification is unsupported: {error}")

        self.assertTrue(summary["qualified"])
        self.assertEqual(summary["counts"], {"equal": 3, "earned_delta": 0, "mismatch": 0})
        self.assertEqual(summary["mode"], "exact_equivalence")

    def test_only_declared_earned_case_may_differ_from_sealed_oracle(self):
        manifest = (
            TutorialCase("039", Path("good/039_andType.ndjson"), 0, "3" * 64),
            TutorialCase("040", Path("good/040_prodType.ndjson"), 0, "4" * 64),
        )
        summary = build_differential_summary(
            oracle_sha="b" * 40,
            candidate_sha="c" * 40,
            manifest=manifest,
            oracle_results=(CaseResult("039", 0), CaseResult("040", 2)),
            candidate_results=(CaseResult("039", 0), CaseResult("040", 0)),
            earned_case="040",
            earned_oracle_exit=2,
            earned_candidate_exit=0,
        )

        self.assertTrue(summary["qualified"])
        self.assertEqual(summary["counts"], {"equal": 1, "earned_delta": 1, "mismatch": 0})

    def test_difference_outside_earned_case_fails(self):
        manifest = (
            TutorialCase("039", Path("good/039_andType.ndjson"), 0, "3" * 64),
            TutorialCase("040", Path("good/040_prodType.ndjson"), 0, "4" * 64),
        )
        summary = build_differential_summary(
            oracle_sha="b" * 40,
            candidate_sha="c" * 40,
            manifest=manifest,
            oracle_results=(CaseResult("039", 0), CaseResult("040", 2)),
            candidate_results=(CaseResult("039", 1), CaseResult("040", 0)),
            earned_case="040",
            earned_oracle_exit=2,
            earned_candidate_exit=0,
        )

        self.assertFalse(summary["qualified"])
        self.assertEqual(summary["counts"]["mismatch"], 1)


if __name__ == "__main__":
    unittest.main()
