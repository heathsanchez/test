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
    reference = {"cold": "unknown", "candidate_count": 12, "unique_survivors": 1,
                 "source": "verified", "transfer": "verified",
                 "dependent_acquisition": "verified", "heldout_zero_budget": "verified",
                 "graph_lineage": ["scc", "condensation", "generations", "semiconnected"],
                 "lineage_acquisitions": 4,
                 "heldout_semiconnected_zero_budget": "verified",
                 "first_restart": True, "second_restart": True,
                 "no_memo_control": False, "tag_key_control": False,
                 "postorder_control": False, "ablation": "unknown",
                 "lineage_ablation": "unknown"}

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
                    "removal_ablation": "unknown"}, native=self.native,
            reference=self.reference)

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
                          "removal_ablation": "verified"}, native=self.native,
                          reference=self.reference)

    def test_rehashed_native_obstruction_claim_is_rejected(self):
        evidence = self.evidence()
        with self.assertRaisesRegex(ValueError, "native constructor"):
            build_release(repository="heathsanchez/test", source_commit="a" * 40,
                          run_id=123, finite=evidence["controls"]["finite"],
                          proof=evidence["controls"]["proof_procedure"],
                          growth=evidence["controls"]["capability_growth"],
                          native={**self.native, "old_ast_count": 7881},
                          reference=self.reference)

    def test_rehashed_reference_causal_claim_is_rejected(self):
        evidence = self.evidence()
        with self.assertRaisesRegex(ValueError, "reference identity"):
            build_release(repository="heathsanchez/test", source_commit="a" * 40,
                          run_id=123, finite=evidence["controls"]["finite"],
                          proof=evidence["controls"]["proof_procedure"],
                          growth=evidence["controls"]["capability_growth"],
                          native=self.native,
                          reference={**self.reference, "tag_key_control": True})


if __name__ == "__main__":
    unittest.main()
