import copy
import unittest

from open_development.release import build_release, validate_release


class ReleaseEvidenceTests(unittest.TestCase):
    native = {"cold": "unknown", "old_ast_count": 7882,
              "old_max_direct_arity": 5, "deciding_arity": 6,
              "candidate_count": 237, "unique_survivors": 1,
              "source": "verified", "transfer": "verified",
              "dependent_acquisition": "verified", "heldout_zero_budget": "verified",
              "restart": True, "ablation": "unknown"}

    def evidence(self):
        return build_release(
            repository="heathsanchez/test", source_commit="a" * 40, run_id=123,
            finite={"first": "verified", "second": "verified", "ablated": "unknown"},
            proof={"cold": ["unknown", "unknown"], "warm": ["verified", "verified"],
                   "restart": True, "exact_ablation": "unknown"},
            growth={"cold_O2": "unknown", "O1": "verified", "O2": "verified",
                    "cold_O3": "unknown", "O3_acquired": "verified",
                    "unlisted_O4_zero_acquisition_budget": "verified",
                    "second_restart": True, "third_restart": True,
                    "removal_ablation": "unknown"}, native=self.native)

    def test_round_trip(self):
        validate_release(self.evidence())

    def test_tampering_is_rejected(self):
        evidence = copy.deepcopy(self.evidence())
        evidence["controls"]["capability_growth"]["removal_ablation"] = "verified"
        with self.assertRaisesRegex(ValueError, "stale"):
            validate_release(evidence)

    def test_rehashed_false_claim_is_rejected(self):
        evidence = self.evidence()
        with self.assertRaisesRegex(ValueError, "capability-growth"):
            build_release(repository="heathsanchez/test", source_commit="a" * 40,
                          run_id=123, finite=evidence["controls"]["finite"],
                          proof=evidence["controls"]["proof_procedure"],
                          growth={**evidence["controls"]["capability_growth"],
                                  "removal_ablation": "verified"}, native=self.native)

    def test_rehashed_native_obstruction_claim_is_rejected(self):
        evidence = self.evidence()
        with self.assertRaisesRegex(ValueError, "native constructor"):
            build_release(repository="heathsanchez/test", source_commit="a" * 40,
                          run_id=123, finite=evidence["controls"]["finite"],
                          proof=evidence["controls"]["proof_procedure"],
                          growth=evidence["controls"]["capability_growth"],
                          native={**self.native, "old_ast_count": 7881})


if __name__ == "__main__":
    unittest.main()
