import copy
import unittest

from open_development.release import (
    build_release,
    build_release_v2,
    validate_release_v2,
)
from open_development.residual import ResidualEnvelope


class ReleaseV2Tests(unittest.TestCase):
    def core(self):
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
        return build_release(
            repository="heathsanchez/test", source_commit="a" * 40, run_id=321,
            finite={"first": "verified", "second": "verified", "ablated": "unknown"},
            proof={"cold": ["unknown", "unknown"], "warm": ["verified", "verified"],
                   "restart": True, "exact_ablation": "unknown"},
            growth={"cold_O2": "unknown", "O1": "verified", "O2": "verified",
                    "cold_O3": "unknown", "O3_acquired": "verified",
                    "unlisted_O4_zero_acquisition_budget": "verified",
                    "second_restart": True, "third_restart": True,
                    "removal_ablation": "unknown"},
            native=native, reference=reference)

    def causal(self):
        return {
            "claim": "retained procedure body is a causal execution dependency",
            "verifier": "proof-composition-v1", "restart": True,
            "warm": "verified", "acquisition_budget": 0,
            "execution_trace": ["2" * 64, "1" * 64],
            "sham_body": "unknown", "missing_body": "unknown",
            "unrelated_removal": "verified", "restored_body": "verified",
            "exact_revocation": "unknown", "history_preserved": True,
            "limits": [],
        }

    def exaptation(self):
        source, role, child = "1" * 64, "2" * 64, "3" * 64
        residual = ResidualEnvelope(
            residual_class="ROLE_REQUALIFICATION_REQUIRED",
            diagnosis="capability_failure",
            verifier_certified_witness={"checked": True},
            closure_id="4" * 64, budget_id="5" * 64,
            necessary_constraint={"role": "factor-pair"},
            version_space_id="6" * 64,
            evidence_strength="replay-certified",
            domain_payload={"class": "ROLE_REQUALIFICATION_REQUIRED"},
            source=source, source_fingerprint="7" * 64,
            constraint={"role": "factor-pair"},
        ).to_mapping()
        return {
            "outcome": "VERIFIED_EXAPTATION_STRICT",
            "parent_checkpoint": "b" * 40,
            "workload_sha256": "8" * 64,
            "workload_was_frozen_in_parent_commit": True,
            "workload_contains_no_encoded_answer": True,
            "classification": {"reuse": False, "exaptation": True, "expansion": False},
            "A": {"K_A": source, "frozen_fingerprint": "7" * 64,
                  "frozen_digest": "9" * 64, "original_scope": "proof-composition",
                  "original_contract": {}, "original_verifier": "proof-composition-v1"},
            "B": {"cold": "unknown", "typed_residual": residual,
                  "B_acquisition_budget": 2, "warm": "verified",
                  "K_B": role, "K_B_dependency": source,
                  "K_C": child, "K_C_dependency": role},
            "heldout": {"acquisition_budget": 0, "verdict": "verified",
                        "execution_trace": [child, role, source]},
            "behavioral_identity": {"source_distinct_implementation": "direct-vieta-factor-program",
                                    "source_hash": "a" * 64,
                                    "same_behavioral_class": True,
                                    "protected_observations": [],
                                    "not_available_to_developer": True},
            "controls": {"same_size_sham_K_B": "refuted",
                         "same_size_serialized_bytes": 123,
                         "wrong_direction_adapter": "refuted",
                         "missing_K_A_executable_body": "unknown",
                         "unrelated_removal": "verified",
                         "raw_history_reconstruction_same_B_budget": "unknown",
                         "fixed_policy_matched_B_budget": {"B_acquisition_budget": 2,
                                                           "verdict": "unknown"},
                         "restored_lineage": "verified"},
            "revocation": {"removed": [source, role, child],
                           "history_preserved": True,
                           "restored_same_K_A_identity": True,
                           "recovery_metric_delta": {}},
            "developmental_cost": {"C_construction": 2, "C_verification": 5,
                                   "C_activation": 2, "C_execution": 23,
                                   "C_memory": 2, "C_recovery": 3,
                                   "C_total": 37, "wall_clock_excluded": True},
            "limits": [],
        }

    def semantics(self):
        return {"result": "TYPED_PROGRAM_SEMANTICS_LEAN_PASS",
                "axioms_pass_count": 11,
                "allowed_axioms": ["Classical.choice", "Quot.sound", "propext"],
                "lean_version": "Lean (version 4.34.0-rc2)",
                "mathlib_commit": "c" * 40,
                "source_hashes_sha256": "d" * 64}

    def evidence(self):
        return build_release_v2(
            repository="heathsanchez/test", source_commit="a" * 40,
            run_id=999, core_run_id=321,
            core_release=self.core(), causal=self.causal(),
            exaptation=self.exaptation(), semantics=self.semantics())

    def test_v2_round_trip(self):
        validate_release_v2(self.evidence())

    def test_v2_tampering_is_rejected(self):
        evidence = copy.deepcopy(self.evidence())
        evidence["components"]["strict_exaptation"]["classification"]["reuse"] = True
        with self.assertRaisesRegex(ValueError, "stale"):
            validate_release_v2(evidence)

    def test_v2_rehashed_false_exaptation_is_rejected(self):
        exaptation = self.exaptation()
        exaptation["controls"]["same_size_sham_K_B"] = "verified"
        with self.assertRaisesRegex(ValueError, "opposing controls"):
            build_release_v2(repository="heathsanchez/test", source_commit="a" * 40,
                             run_id=999, core_run_id=321, core_release=self.core(),
                             causal=self.causal(), exaptation=exaptation,
                             semantics=self.semantics())

    def test_v2_rejects_core_from_different_commit(self):
        with self.assertRaisesRegex(ValueError, "source commit"):
            build_release_v2(repository="heathsanchez/test", source_commit="e" * 40,
                             run_id=999, core_run_id=321, core_release=self.core(),
                             causal=self.causal(), exaptation=self.exaptation(),
                             semantics=self.semantics())


if __name__ == "__main__":
    unittest.main()
