import copy
import unittest

from open_development.release_v3 import _check_external
from open_development.residual import ResidualEnvelope


class ReleaseV3ExternalTests(unittest.TestCase):
    def external(self):
        source, role, child = "1" * 64, "2" * 64, "3" * 64
        fingerprint = "4" * 64
        residual = ResidualEnvelope(
            residual_class="GLOBAL_ROLE_REQUALIFICATION_REQUIRED",
            diagnosis="capability_failure",
            verifier_certified_witness={"source_active": True},
            closure_id="5" * 64,
            budget_id="6" * 64,
            necessary_constraint={
                "must_depend_on": source,
                "must_preserve_source_fingerprint": fingerprint,
                "must_reverify_power0_square_on_all_reals": True,
                "new_scope": "external-minif2f-global-quadratic-v1",
            },
            version_space_id="7" * 64,
            evidence_strength="exact-replay-certified",
            domain_payload={"external_repository": "google-deepmind/miniF2F"},
            source=source,
            source_fingerprint=fingerprint,
            constraint={
                "must_depend_on": source,
                "must_preserve_source_fingerprint": fingerprint,
                "must_reverify_power0_square_on_all_reals": True,
                "new_scope": "external-minif2f-global-quadratic-v1",
            },
        ).to_mapping()
        return {
            "outcome": "VERIFIED_EXTERNALLY_SELECTED_EXAPTATION",
            "freeze_commit": "a" * 40,
            "selection_nonce": "42",
            "source_external_bytes_seen_at_freeze": False,
            "source_freeze_digest": "8" * 64,
            "source_state_id": "9" * 64,
            "external_repository": "google-deepmind/miniF2F",
            "external_commit": "f0a20e14c1eeccd859d51bb4c2b3ee487889c303",
            "external_test_path": "MiniF2F/Test.lean",
            "external_test_blob_sha1": "7d3a756cb3da856fc26096c8da440f086653cfc1",
            "external_test_sha256": "a" * 64,
            "candidate_count": 2,
            "candidate_pool_digest": "b" * 64,
            "B_index": 0,
            "heldout_index": 1,
            "classification": {"reuse": False, "exaptation": True, "expansion": False},
            "K_A": source,
            "K_A_fingerprint": fingerprint,
            "K_B": role,
            "K_B_dependency": source,
            "K_C": child,
            "K_C_dependency": role,
            "cold": "unknown",
            "typed_residual": residual,
            "B_acquisition_budget": 2,
            "warm": "verified",
            "restart": True,
            "heldout_acquisition_budget": 0,
            "heldout_verdict": "verified",
            "heldout_execution_trace": [child, role, source],
            "B": {"name": "external_B", "statement_sha256": "c" * 64,
                  "global_certificate_sha256": "d" * 64, "polynomial": {"2": "1"}},
            "heldout": {"name": "external_H", "statement_sha256": "e" * 64,
                        "global_certificate_sha256": "f" * 64, "polynomial": {"2": "1", "0": "1"}},
            "behavioral_identity": {
                "same_behavioral_class_on_B_and_heldout": True,
                "not_available_to_developer": True,
                "source_distinct_implementation_hash": "0" * 64,
            },
            "controls": {
                "same_size_sham_K_B": "refuted",
                "wrong_direction_adapter": "refuted",
                "missing_K_A_executable_identity": "unknown",
                "unrelated_removal": "verified",
                "ancestor_revocation_heldout": "unknown",
                "raw_history_reconstruction_same_B_budget": "unknown",
                "matched_fixed_policy": {"B_acquisition_budget": 2, "verdict": "unknown"},
                "restored_source_same_identity": True,
                "restored_development": "verified",
                "restored_heldout": "verified",
                "history_preserved": True,
                "revoked_lineage_contains": [source, role, child],
            },
        }

    def test_external_authority_accepts_complete_evidence(self):
        _check_external(self.external(), source_commit="a" * 40, external_run_id=42)

    def test_external_authority_rejects_rehashed_bad_control(self):
        evidence = self.external()
        evidence["controls"]["same_size_sham_K_B"] = "verified"
        with self.assertRaisesRegex(ValueError, "opposing controls"):
            _check_external(evidence, source_commit="a" * 40, external_run_id=42)

    def test_external_authority_rejects_wrong_run_identity(self):
        with self.assertRaisesRegex(ValueError, "selection nonce"):
            _check_external(self.external(), source_commit="a" * 40, external_run_id=43)

    def test_external_authority_rejects_direct_reuse_relabel(self):
        evidence = copy.deepcopy(self.external())
        evidence["classification"] = {"reuse": True, "exaptation": False, "expansion": False}
        with self.assertRaisesRegex(ValueError, "classification"):
            _check_external(evidence, source_commit="a" * 40, external_run_id=42)


if __name__ == "__main__":
    unittest.main()
