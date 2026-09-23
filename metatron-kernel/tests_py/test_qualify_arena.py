import unittest

from scripts.qualify_arena import CaseResult, build_summary, classify_exit


CANDIDATE = "a" * 40
ARENA = "b" * 40


class QualificationSummaryTests(unittest.TestCase):
    def test_exit_codes_have_exact_verdict_names(self):
        self.assertEqual(classify_exit(0), "accept")
        self.assertEqual(classify_exit(1), "reject")
        self.assertEqual(classify_exit(2), "unknown")
        self.assertEqual(classify_exit(3), "error")
        self.assertEqual(classify_exit(70), "error")

    def test_unknown_required_good_case_is_incomplete_not_incorrect(self):
        summary = build_summary(
            candidate_sha=CANDIDATE,
            arena_sha=ARENA,
            expected_cases={"good": "accept"},
            results=[CaseResult("good", "accept", "unknown", 2)],
        )
        self.assertEqual(summary["counts"]["incomplete"], 1)
        self.assertEqual(summary["counts"]["incorrect"], 0)
        self.assertEqual(summary["cases"][0]["status"], "incomplete")

    def test_wrong_decision_is_incorrect_and_output_is_ordered(self):
        summary = build_summary(
            candidate_sha=CANDIDATE,
            arena_sha=ARENA,
            expected_cases={"zeta": "accept", "alpha": "reject"},
            results=[
                CaseResult("zeta", "accept", "reject", 1),
                CaseResult("alpha", "reject", "reject", 1),
            ],
        )
        self.assertEqual([case["name"] for case in summary["cases"]], ["alpha", "zeta"])
        self.assertEqual(summary["counts"]["matched"], 1)
        self.assertEqual(summary["counts"]["incorrect"], 1)

    def test_missing_declared_case_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing case"):
            build_summary(
                candidate_sha=CANDIDATE,
                arena_sha=ARENA,
                expected_cases={"good": "accept", "bad": "reject"},
                results=[CaseResult("good", "accept", "accept", 0)],
            )

    def test_error_is_distinct_from_incorrect(self):
        summary = build_summary(
            candidate_sha=CANDIDATE,
            arena_sha=ARENA,
            expected_cases={"good": "accept"},
            results=[CaseResult("good", "accept", "error", 3)],
        )
        self.assertEqual(summary["counts"]["error"], 1)
        self.assertEqual(summary["counts"]["incorrect"], 0)


if __name__ == "__main__":
    unittest.main()
