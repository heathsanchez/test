from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

from kernel import Kernel
from challenge_pack import (
    DEPTHS,
    PREFIX_PAIRS,
    EXTENDED_PAIRS,
    IDENTICAL_PAIR,
    INCOMPLETE,
    COMPLETE_FOR_INCOMPLETE,
    separator_sequence,
)

SCIENTIFIC_FREEZE_COMMIT = "69499cb0ad2e35ff1e4e69e00da946cc12bda7e0"

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    observed = {
        name: git_blob_sha(HERE / name)
        for name in freeze["scientific_core_paths"]
    }
    freeze_ok = observed == freeze["git_blob_sha"]

    kernel = Kernel()

    prefix_results = {}
    extended_results = {}
    bounded_prefix = {}
    bounded_extended = {}
    signatures_equal = {}

    for depth in DEPTHS:
        left, right = PREFIX_PAIRS[depth]
        ex_left, ex_right = EXTENDED_PAIRS[depth]

        prefix_results[str(depth)] = kernel.compare(left, right)
        extended_results[str(depth)] = kernel.compare(ex_left, ex_right)
        bounded_prefix[str(depth)] = kernel.bounded_compare(left, right, depth)
        bounded_extended[str(depth)] = kernel.bounded_compare(ex_left, ex_right, depth + 1)
        signatures_equal[str(depth)] = (
            kernel.observation_signature(left) == kernel.observation_signature(right)
        )

    identical_global = kernel.compare(*IDENTICAL_PAIR)
    identical_with_certificate = kernel.compare(
        *IDENTICAL_PAIR,
        global_completeness_certificate=True,
    )

    incomplete = kernel.compare(INCOMPLETE, COMPLETE_FOR_INCOMPLETE)
    no_verifier = kernel.compare(
        PREFIX_PAIRS[3][0],
        PREFIX_PAIRS[3][1],
        verification_enabled=False,
    )

    kernel_text = (HERE / "kernel.py").read_text().lower()
    forbidden = (
        "delayed",
        "separator_sequence",
        "all ones",
        "challenge depth",
        "prefix_pairs",
        "extended_pairs",
    )

    same_prefix_different_continuations = {}
    for depth in DEPTHS:
        left, right = PREFIX_PAIRS[depth]
        ex_left, ex_right = EXTENDED_PAIRS[depth]
        same_prefix_different_continuations[str(depth)] = {
            "same_prefix_signature": (
                kernel.observation_signature(left)
                == kernel.observation_signature(right)
            ),
            "equal_continuation_available": (
                kernel.compare(ex_left, ex_left).get("status")
                == "UNKNOWN_BEYOND_FINITE_HORIZON"
            ),
            "separating_continuation_available": (
                kernel.compare(ex_left, ex_right).get("status")
                == "VERIFIED_NOT_EQUIVALENT"
            ),
        }

    gates = {}
    gates["H1_frozen_scientific_core_byte_identical"] = freeze_ok

    gates["H2_every_challenge_prefix_table_is_complete"] = all(
        kernel.authority(left) is None and kernel.authority(right) is None
        for left, right in PREFIX_PAIRS.values()
    )

    gates["H3_pairs_are_observationally_identical_through_each_finite_depth"] = all(
        signatures_equal.values()
    )

    gates["H4_identical_finite_prefixes_remain_unknown_globally"] = all(
        prefix_results[str(depth)].get("status") == "UNKNOWN_BEYOND_FINITE_HORIZON"
        for depth in DEPTHS
    )

    gates["H5_one_more_authorized_layer_exposes_explicit_separator"] = all(
        extended_results[str(depth)].get("status") == "VERIFIED_NOT_EQUIVALENT"
        and tuple(extended_results[str(depth)].get("witness", [])) == separator_sequence(depth)
        and extended_results[str(depth)].get("witness_depth") == depth + 1
        for depth in DEPTHS
    )

    gates["H6_separator_produces_verified_nonequivalence"] = all(
        extended_results[str(depth)].get("status") == "VERIFIED_NOT_EQUIVALENT"
        for depth in DEPTHS
    )

    gates["H7_bounded_equivalence_through_observed_depth_is_positive"] = all(
        bounded_prefix[str(depth)].get("status") == "VERIFIED_BOUNDED_EQUIVALENCE"
        and bounded_prefix[str(depth)].get("bound") == depth
        for depth in DEPTHS
    )

    gates["H8_same_pair_fails_bounded_equivalence_at_next_depth"] = all(
        bounded_extended[str(depth)].get("status")
        == "VERIFIED_NOT_EQUIVALENT_WITHIN_BOUND"
        and bounded_extended[str(depth)].get("witness_depth") == depth + 1
        for depth in DEPTHS
    )

    gates["H9_underdetermination_construction_succeeds_at_every_tested_depth"] = all(
        signatures_equal[str(depth)]
        and prefix_results[str(depth)].get("status") == "UNKNOWN_BEYOND_FINITE_HORIZON"
        and extended_results[str(depth)].get("status") == "VERIFIED_NOT_EQUIVALENT"
        for depth in DEPTHS
    )

    gates["H10_genuinely_identical_finite_pair_still_global_unknown_without_certificate"] = (
        identical_global.get("status") == "UNKNOWN_BEYOND_FINITE_HORIZON"
    )

    gates["H11_explicit_completeness_or_finite_scope_can_close_the_claim"] = (
        identical_with_certificate.get("status")
        == "VERIFIED_EQUIVALENT_UNDER_EXTERNAL_COMPLETENESS_CERTIFICATE"
        and all(
            bounded_prefix[str(depth)].get("status") == "VERIFIED_BOUNDED_EQUIVALENCE"
            for depth in DEPTHS
        )
    )

    gates["H12_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
    )

    gates["H13_verifier_ablation_authorizes_no_claim"] = (
        no_verifier.get("status") == "UNKNOWN_NO_VERIFIER"
    )

    gates["H14_frozen_kernel_contains_no_hidden_delayed_pattern_or_challenge_depth"] = all(
        re.search(r"\b" + re.escape(token) + r"\b", kernel_text) is None
        for token in forbidden
    )

    gates["H15_same_finite_signature_admits_equal_and_future_separating_continuations"] = all(
        row["same_prefix_signature"]
        and row["equal_continuation_available"]
        and row["separating_continuation_available"]
        for row in same_prefix_different_continuations.values()
    )

    evidence = {
        "experiment": "finite_horizon_identifiability_v38",
        "scientific_freeze_commit": SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest": freeze,
        "observed_core_git_blob_sha": observed,
        "tested_depths": list(DEPTHS),
        "prefix_results": prefix_results,
        "extended_results": extended_results,
        "bounded_prefix": bounded_prefix,
        "bounded_extended": bounded_extended,
        "signatures_equal": signatures_equal,
        "same_prefix_different_continuations": same_prefix_different_continuations,
        "identical_global": identical_global,
        "identical_with_certificate": identical_with_certificate,
        "incomplete": incomplete,
        "no_verifier": no_verifier,
        "gates": gates,
    }
    evidence["full_pass"] = all(gates.values())
    evidence["verdict"] = (
        "VERIFIED_FINITE_HORIZON_UNDERDETERMINATION_AND_UNKNOWN_BOUNDARY"
        if evidence["full_pass"]
        else "FINITE_HORIZON_IDENTIFIABILITY_V38_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
