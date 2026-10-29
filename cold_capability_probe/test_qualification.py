"""Full archived original-verifier replay, never a prospective G2/G3 trial."""
from pathlib import Path
import tempfile
import unittest

from cold_capability_probe import qualification


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class NativeArchivalQualificationTests(unittest.TestCase):
    def test_original_verifier_and_fresh_archived_world_recomputation(self):
        with tempfile.TemporaryDirectory(prefix="cap-replay-") as scratch:
            report = qualification.run(ROOT, Path(scratch))
        self.assertEqual(report["archived_native_rescore"], {
            "total": 27, "train": 17, "future": 10,
            "train_pass": 5, "train_fail": 12, "future_pass": 10,
        })
        self.assertEqual(report["recomputed_candidate_evaluations"], {
            "retain_both": 1, "ablate_E_grouping": 3,
            "ablate_F_filter": 3, "ablate_both": 9, "strong_stateless": 1,
        })
        self.assertEqual(report["recomputed_future_successful_arms"], 5)
        self.assertEqual(report["comparative_economics"], "TIE_STRONG_STATELESS")
        self.assertEqual(report["replay_boundary"], "ARCHIVED_SOURCE_OBSERVATION_NOT_NEW_NATIVE_TASK")


if __name__ == "__main__":
    unittest.main()
