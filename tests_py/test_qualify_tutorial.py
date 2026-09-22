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

    def test_production_manifest_pins_nat_as_case_044(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 44)
        case = TUTORIAL_MANIFEST[43]
        self.assertEqual(case.number, "044")
        self.assertEqual(case.relative_path, Path("good/044_natDef.ndjson"))
        self.assertEqual(case.expected_exit_code, 0)
        self.assertEqual(
            case.sha256,
            "95d33f871f126e234740e05d9291a1cedcc6a2d01522aedc3122b25aab17ab95",
        )

    def test_production_manifest_pins_eq_as_case_043(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 43)
        case = TUTORIAL_MANIFEST[42]
        self.assertEqual(case.number, "043")
        self.assertEqual(case.relative_path, Path("good/043_eqType.ndjson"))
        self.assertEqual(case.expected_exit_code, 0)
        self.assertEqual(
            case.sha256,
            "d45ed54cc74be3d7d92aae6bacc040420ba33f23fa034b4497edb389e089afdc",
        )

    def test_production_manifest_pins_rbtree_as_case_045(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 45)
        case = TUTORIAL_MANIFEST[44]
        self.assertEqual(case.number, "045")
        self.assertEqual(case.relative_path, Path("good/045_rbTreeDef.ndjson"))
        self.assertEqual(case.expected_exit_code, 0)
        self.assertEqual(
            case.sha256,
            "d9781f44fcb7e46ff06da1c8a273a4fec4ae989e4114d6668720bd5b87c20b79",
        )

    def test_production_manifest_pins_g20_malformed_corridor(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 49)
        expected = (
            ("046", Path("bad/046_inductBadNonSort.ndjson"), "372f6a167433b45749fa38f14ad3a2e8ca4e0dae8762812c0b9f288e9f68499f"),
            ("047", Path("bad/047_inductBadNonSort2.ndjson"), "95836e7bee5fbd00d1d16d88cea2defa8dfb2387fc0e400d200b59715716a0d9"),
            ("048", Path("bad/048_inductLevelParam.ndjson"), "732e2fc946ab308a819366bc5395865a69235098e1a401ec1a059d05d89ef06e"),
            ("049", Path("bad/049_inductTooFewParams.ndjson"), "5d54c2cc017f35b26744f8b5ca4438bdddd8f254f3023948a542b70e5da72827"),
        )
        for offset, (number, relative_path, sha256) in enumerate(expected, start=45):
            case = TUTORIAL_MANIFEST[offset]
            self.assertEqual(case.number, number)
            self.assertEqual(case.relative_path, relative_path)
            self.assertEqual(case.expected_exit_code, 1)
            self.assertEqual(case.sha256, sha256)

    def test_production_manifest_pins_g21_constructor_corridor(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 53)
        expected = (
            ("050", Path("bad/050_inductWrongCtorParams.ndjson"), "20214ec1a31221884548d3e91b689b9569fd7588af2fb0e219754b683041ac10"),
            ("051", Path("bad/051_inductWrongCtorResParams.ndjson"), "5506566449cc2f3c83f417007bf15a7a0101c458c450d77a23cfd4c2423910c4"),
            ("052", Path("bad/052_inductWrongCtorResLevel.ndjson"), "3f29bd3a753caa056cc45c20cd8aeb734bc44cfc6b3828a6c6ec855737f596f3"),
            ("053", Path("bad/053_inductInIndex.ndjson"), "8dc9a9997862a5f25b76520f5d69a146664ad9f0364dd350732a7f76e4190763"),
        )
        for offset, (number, relative_path, sha256) in enumerate(expected, start=49):
            case = TUTORIAL_MANIFEST[offset]
            self.assertEqual(case.number, number)
            self.assertEqual(case.relative_path, relative_path)
            self.assertEqual(case.expected_exit_code, 1)
            self.assertEqual(case.sha256, sha256)

    def test_production_manifest_pins_indneg_as_case_054(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 54)
        case = TUTORIAL_MANIFEST[53]
        self.assertEqual(case.number, "054")
        self.assertEqual(case.relative_path, Path("bad/054_indNeg.ndjson"))
        self.assertEqual(case.expected_exit_code, 1)
        self.assertEqual(
            case.sha256,
            "89592d2e05e7ea518cf550eb18b99d1172b63b96b90abf1454b7102300eda843",
        )

    def test_production_manifest_pins_reduce_ctor_param_as_case_055(self):
        self.assertGreaterEqual(len(TUTORIAL_MANIFEST), 55)
        case = TUTORIAL_MANIFEST[54]
        self.assertEqual(case.number, "055")
        self.assertEqual(case.relative_path, Path("good/055_reduceCtorParam.mk.ndjson"))
        self.assertEqual(case.expected_exit_code, 0)
        self.assertEqual(
            case.sha256,
            "16d146c5ef39743b6a95f21043a43b890e22d72792fd9436e37396765124a7a2",
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

    def test_multiple_declared_earned_cases_may_differ(self):
        manifest = (
            TutorialCase("046", Path("bad/046.ndjson"), 1, "6" * 64),
            TutorialCase("047", Path("bad/047.ndjson"), 1, "7" * 64),
            TutorialCase("048", Path("bad/048.ndjson"), 1, "8" * 64),
            TutorialCase("049", Path("bad/049.ndjson"), 1, "9" * 64),
        )
        summary = build_differential_summary(
            oracle_sha="b" * 40,
            candidate_sha="c" * 40,
            manifest=manifest,
            oracle_results=(
                CaseResult("046", 2),
                CaseResult("047", 2),
                CaseResult("048", 1),
                CaseResult("049", 2),
            ),
            candidate_results=(
                CaseResult("046", 1),
                CaseResult("047", 1),
                CaseResult("048", 1),
                CaseResult("049", 1),
            ),
            earned_case=("046", "047", "049"),
            earned_oracle_exit=2,
            earned_candidate_exit=1,
        )

        self.assertTrue(summary["qualified"])
        self.assertEqual(summary["counts"], {"equal": 1, "earned_delta": 3, "mismatch": 0})
        self.assertEqual(summary["mode"], "earned_deltas")
        self.assertEqual(summary["earned_cases"], ["046", "047", "049"])

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
