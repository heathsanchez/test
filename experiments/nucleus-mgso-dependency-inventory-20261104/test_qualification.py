"""The Rust checker, not the semantic inventory, supplies every verdict."""

import os
from pathlib import Path
import tempfile
import unittest

from qualification import generate_cases, qualify


FIXTURES = Path(__file__).resolve().parents[2] / "metatron-kernel/tests/fixtures"


class QualificationTests(unittest.TestCase):
    def test_mutant_sources_are_deterministic_and_distinct(self):
        original = (FIXTURES / "good-theorem-use.ndjson").read_bytes()
        arms = dict(generate_cases(original))
        self.assertEqual(set(arms), {"original", "later_rename", "renumber_name_id",
                                     "earlier_binder_change", "first_theorem_to_axiom",
                                     "self_const_forgery", "global_quotient_forgery"})
        self.assertEqual(arms["original"], original)
        self.assertEqual(len(set(arms.values())), 7)
        self.assertEqual(original.split(b'{"in":4', 1)[0],
                         arms["later_rename"].split(b'{"in":4', 1)[0])

    def test_real_nucleus_produces_native_verdicts_and_rejects_global_forgery(self):
        binary = os.getenv("NUCLEUS_DEPENDENCY_BINARY")
        if not binary:
            self.skipTest("set NUCLEUS_DEPENDENCY_BINARY to freshly built independent Rust kernel")
        with tempfile.TemporaryDirectory(prefix="nucleus-dep-test-") as directory:
            report = qualify(Path(binary), FIXTURES / "good-theorem-use.ndjson",
                             Path(directory))
        self.assertEqual(report["type"], "nucleus.dependency-native-qualification.v1")
        self.assertEqual(report["authority"], "NONE")
        self.assertEqual(report["proof_skips"], 0)
        self.assertEqual(report["live_kernel_invocations"], 7)
        self.assertEqual({r["case"]: r["exit_code"] for r in report["arms"]}, {
            "original": 0,
            "later_rename": 0,
            "renumber_name_id": 0,
            "earlier_binder_change": 0,
            "first_theorem_to_axiom": 0,
            "self_const_forgery": 1,
            "global_quotient_forgery": 1,
        })
        self.assertEqual(report["historical_inspection"]["original"]["exit_code"], 2)
        self.assertIn("candidate-match", report["historical_inspection"]["original"]["stderr"])
        self.assertEqual(report["historical_inspection"]["later_rename"]["exit_code"], 2)
        self.assertIn("status=stale", report["historical_inspection"]["later_rename"]["stderr"])
        by_case = {r["case"]: r for r in report["arms"]}
        self.assertEqual(by_case["later_rename"]["candidate_reuse_count"], 1)
        self.assertEqual(by_case["renumber_name_id"]["candidate_reuse_count"], 2)
        self.assertEqual(by_case["earlier_binder_change"]["candidate_reuse_count"], 0)
        self.assertEqual(by_case["global_quotient_forgery"]["candidate_reuse_count"], 2)
        self.assertEqual(by_case["global_quotient_forgery"]["exit_code"], 1)
        self.assertEqual(by_case["self_const_forgery"]["inventory_status"], "UNKNOWN")
        self.assertTrue(all(r["proof_skips"] == 0 and r["source_verified_by"] == "Nucleus"
                            for r in report["arms"]))


if __name__ == "__main__":
    unittest.main()
