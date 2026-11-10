"""The historical MGSO candidate cannot authorize a synthetic stronger claim."""

import unittest

from assess_mgso_claim import require_observation, require_stale_inspection


INSPECTION = (
    "NUCLEUS_MGSO_INSPECT:status=candidate-match;authority=none;"
    "fresh-check=false;declarations=1"
)


class TestMGSOClaimBoundary(unittest.TestCase):
    def test_exact_candidate_is_evidence_without_accept_authority(self):
        self.assertEqual(require_observation(2, INSPECTION), "candidate-match")

    def test_forged_authority_is_not_promoted(self):
        forged = INSPECTION.replace("authority=none", "authority=ACCEPT")
        with self.assertRaises(AssertionError):
            require_observation(2, forged)

    def test_inspector_returning_accept_fails_closed(self):
        with self.assertRaises(AssertionError):
            require_observation(0, INSPECTION)

    def test_duplicate_conflicting_receipts_fail_closed(self):
        with self.assertRaises(AssertionError):
            require_observation(2, INSPECTION + "\n" + INSPECTION)

    def test_unknown_historical_candidate_does_not_pass(self):
        unknown = INSPECTION.replace("status=candidate-match", "status=unknown")
        with self.assertRaises(AssertionError):
            require_observation(2, unknown)

    def test_source_mutation_stales_historical_candidate(self):
        self.assertEqual(
            require_stale_inspection(
                2, "NUCLEUS_MGSO_INSPECT:status=stale;authority=none;"
                "fresh-check=false;reason=source-sha256-mismatch"
            ),
            "stale",
        )

    def test_source_drift_cannot_be_reported_as_candidate(self):
        with self.assertRaises(AssertionError):
            require_stale_inspection(2, INSPECTION)


if __name__ == "__main__":
    unittest.main()
