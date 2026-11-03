"""Coverage and honesty against all source-native repository fixtures."""

import os
from pathlib import Path
import unittest

from corpus_inventory import survey


FIXTURES = Path(__file__).resolve().parents[2] / "metatron-kernel/tests/fixtures"


class CorpusInventoryTests(unittest.TestCase):
    def test_55_real_fixtures_include_bounded_refusals(self):
        report = survey(FIXTURES)
        self.assertEqual(report["fixture_count"], 55)
        self.assertEqual(report["candidate_count"], 52)
        self.assertEqual(report["refused_count"], 3)
        self.assertEqual(report["complete_kernel_dependency_closure"], "UNKNOWN")
        self.assertEqual(report["verification_reuse_authority"], "NONE")
        self.assertEqual(report["proof_skips"], 0)

    def test_native_corpus_checks_every_case_even_if_inventory_is_candidate(self):
        binary = os.getenv("NUCLEUS_DEPENDENCY_BINARY")
        if not binary:
            self.skipTest("real native Nucleus binary required")
        report = survey(FIXTURES, Path(binary))
        self.assertEqual(report["native_invocations"], 55)
        self.assertEqual(report["fixture_count"], 55)
        self.assertEqual(report["proof_skips"], 0)
        self.assertTrue(all(row["native_exit_code"] in (0, 1, 2, 3)
                            for row in report["rows"]))
        self.assertTrue(any(row["inventory_status"] == "CANDIDATE_ONLY"
                            and row["native_exit_code"] != 0 for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
