"""Fail-closed qualification manifests for the bounded developmental core.

v1 is retained for backward-compatible CI.  v2 composes the v1 core evidence
with executable causality, strict prospective exaptation, and the independent
Mathlib-backed proof-semantics authority into one release identity.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from .residual import ResidualEnvelope
from .runtime import digest

SCHEMA = "open-development-release/v1"
CLAIM = "bounded verifier-governed developmental machine"
SCHEMA_V2 = "open-development-release/v2"
CLAIM_V2 = "bounded verifier-governed developmental machine with causal retention and strict prospective exaptation"
LIMITATIONS = [
    "finite supplied constructor grammars",
    "exact rational polynomial proof domain",
    "reference-identity qualification uses a supplied allocation/identity/table/link substrate",
    "no unrestricted grammar invention or completeness claim",
    "generated proof certificates use the exact-rational checker; generic rules and qualified programs have separate Lean evidence",
]
LIMITATIONS_V2 = [
    *LIMITATIONS,
    "prospective exaptation workload is repository-frozen but internally authored, not independently administered",
    "strict exaptation Python interpreter is not Lean-verified",
    "protected behavioral equivalence is bounded to frozen observations",
    "zero acquisition budget is not zero execution cost",
    "does not decide metaphysical discovery versus creation",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_release(*, repository: str, source_commit: str, run_id: int,
                  finite: Mapping[str, Any], proof: Mapping[str, Any],
                  growth: Mapping[str, Any], native: Mapping[str, Any],
                  reference: Mapping[str, Any]) -> dict[str, Any]:
    """Build the backward-compatible v1 core release."""
    _require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
             "source commit must be a full lowercase Git SHA")
    _require(run_id > 0 and re.fullmatch(r"[^/]+/[^/]+", repository) is not None,
             "invalid GitHub run identity")
    _require(finite.get("first") == "verified" and finite.get("second") == "verified"
             and finite.get("ablated") == "unknown", "finite causal gate failed")
    _require(proof.get("cold") == ["unknown", "unknown"]
             and proof.get("warm") == ["verified", "verified"]
             and proof.get("restart") is True
             and proof.get("exact_ablation") == "unknown", "proof self-application gate failed")
    _require(growth.get("cold_O2") == "unknown" and growth.get("O1") == "verified"
             and growth.get("O2") == "verified"
             and growth.get("cold_O3") == "unknown"
             and growth.get("O3_acquired") == "verified"
             and growth.get("unlisted_O4_zero_acquisition_budget") == "verified"
             and growth.get("second_restart") is True
             and growth.get("third_restart") is True
             and growth.get("removal_ablation") == "unknown",
             "capability-growth causal gate failed")
    _require(native.get("cold") == "unknown" and native.get("old_ast_count") == 7882
             and native.get("old_max_direct_arity") == 5
             and native.get("deciding_arity") == 6
             and native.get("candidate_count") == 237
             and native.get("unique_survivors") == 1
             and native.get("source") == "verified" and native.get("transfer") == "verified"
             and native.get("dependent_acquisition") == "verified"
             and native.get("heldout_zero_budget") == "verified"
             and native.get("restart") is True and native.get("ablation") == "unknown",
             "native constructor integration gate failed")
    _require(reference.get("cold") == "unknown"
             and reference.get("candidate_count") == 12
             and reference.get("unique_survivors") == 1
             and reference.get("source") == "verified"
             and reference.get("transfer") == "verified"
             and reference.get("dependent_acquisition") == "verified"
             and reference.get("heldout_zero_budget") == "verified"
             and reference.get("graph_lineage") == ["scc", "condensation", "generations", "semiconnected"]
             and reference.get("lineage_acquisitions") == 4
             and reference.get("heldout_semiconnected_zero_budget") == "verified"
             and reference.get("first_restart") is True
             and reference.get("second_restart") is True
             and reference.get("no_memo_control") is False
             and reference.get("tag_key_control") is False
             and reference.get("postorder_control") is False
             and reference.get("ablation") == "unknown"
             and reference.get("lineage_ablation") == "unknown",
             "reference identity integration gate failed")
    body = {
        "schema": SCHEMA,
        "claim": CLAIM,
        "scope": "finite observational, exact-rational proof-program, native recursive-type, and reference-identity development",
        "source_commit": source_commit,
        "run_id": run_id,
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "controls": {
            "finite": dict(finite), "proof_procedure": dict(proof),
            "capability_growth": dict(growth),
            "native_constructor": dict(native),
            "reference_identity": dict(reference),
        },
        "formal_authorities": [
            "Lean 4.24.0 MSI/developmental bridge and finite realization",
            "Lean nested-fixpoint roundtrip and variable-arity realization",
            "Lean reference-identity graph observation and tree-language obstruction",
            "pinned Mathlib generic proof-program rules and concrete O2/O3 semantics",
        ],
        "limitations": LIMITATIONS,
    }
    return {**body, "evidence_digest": digest(body)}


def validate_release(manifest: Mapping[str, Any]) -> None:
    _require(manifest.get("schema") == SCHEMA and manifest.get("claim") == CLAIM,
             "unknown release claim or schema")
    supplied = manifest.get("evidence_digest")
    body = {key: value for key, value in manifest.items() if key != "evidence_digest"}
    _require(isinstance(supplied, str) and supplied == digest(body),
             "release evidence is missing, malformed, or stale")
    rebuilt = build_release(
        repository=manifest["run_url"].split("github.com/", 1)[1].split("/actions/", 1)[0],
        source_commit=manifest["source_commit"], run_id=manifest["run_id"],
        finite=manifest["controls"]["finite"],
        proof=manifest["controls"]["proof_procedure"],
        growth=manifest["controls"]["capability_growth"],
        native=manifest["controls"]["native_constructor"],
        reference=manifest["controls"]["reference_identity"])
    _require(rebuilt == dict(manifest), "release evidence does not match its declared run")


def _check_causal(causal: Mapping[str, Any]) -> None:
    _require(causal.get("claim") == "retained procedure body is a causal execution dependency",
             "causal executable claim mismatch")
    _require(causal.get("restart") is True and causal.get("warm") == "verified"
             and causal.get("acquisition_budget") == 0,
             "causal executable reuse gate failed")
    _require(causal.get("sham_body") == "unknown"
             and causal.get("missing_body") == "unknown"
             and causal.get("unrelated_removal") == "verified"
             and causal.get("restored_body") == "verified"
             and causal.get("exact_revocation") == "unknown"
             and causal.get("history_preserved") is True,
             "causal executable intervention controls failed")
    trace = causal.get("execution_trace")
    _require(isinstance(trace, list) and len(trace) >= 2 and len(set(trace)) == len(trace),
             "causal execution trace malformed")


def _check_exaptation(exaptation: Mapping[str, Any]) -> None:
    _require(exaptation.get("outcome") == "VERIFIED_EXAPTATION_STRICT",
             "strict exaptation outcome failed")
    _require(exaptation.get("workload_was_frozen_in_parent_commit") is True
             and exaptation.get("workload_contains_no_encoded_answer") is True,
             "strict exaptation workload freeze failed")
    _require(exaptation.get("classification") == {
        "reuse": False, "exaptation": True, "expansion": False},
        "strict exaptation classification failed")
    A = exaptation.get("A", {})
    B = exaptation.get("B", {})
    heldout = exaptation.get("heldout", {})
    behavioral = exaptation.get("behavioral_identity", {})
    controls = exaptation.get("controls", {})
    revocation = exaptation.get("revocation", {})
    cost = exaptation.get("developmental_cost", {})
    source, role, child = A.get("K_A"), B.get("K_B"), B.get("K_C")
    _require(all(isinstance(x, str) and len(x) == 64 for x in (source, role, child)),
             "strict exaptation lineage identities malformed")
    _require(B.get("cold") == "unknown" and B.get("warm") == "verified"
             and B.get("B_acquisition_budget") == 2,
             "strict exaptation B boundary failed")
    residual = ResidualEnvelope.from_mapping(B.get("typed_residual", {}))
    _require(residual.diagnosis == "capability_failure"
             and residual.residual_class == "ROLE_REQUALIFICATION_REQUIRED"
             and residual.evidence_strength == "replay-certified",
             "strict exaptation typed residual failed")
    _require(B.get("K_B_dependency") == source and B.get("K_C_dependency") == role,
             "strict exaptation dependency lineage failed")
    _require(heldout.get("acquisition_budget") == 0
             and heldout.get("verdict") == "verified"
             and heldout.get("execution_trace") == [child, role, source],
             "strict exaptation held-out execution failed")
    _require(behavioral.get("same_behavioral_class") is True
             and behavioral.get("not_available_to_developer") is True,
             "strict exaptation behavioral identity failed")
    _require(controls.get("same_size_sham_K_B") == "refuted"
             and controls.get("wrong_direction_adapter") == "refuted"
             and controls.get("missing_K_A_executable_body") == "unknown"
             and controls.get("unrelated_removal") == "verified"
             and controls.get("raw_history_reconstruction_same_B_budget") == "unknown"
             and controls.get("fixed_policy_matched_B_budget", {}).get("B_acquisition_budget") == 2
             and controls.get("fixed_policy_matched_B_budget", {}).get("verdict") == "unknown"
             and controls.get("restored_lineage") == "verified",
             "strict exaptation opposing controls failed")
    removed = set(revocation.get("removed", []))
    _require({source, role, child} <= removed and revocation.get("history_preserved") is True
             and revocation.get("restored_same_K_A_identity") is True,
             "strict exaptation revocation/restoration failed")
    parts = [cost.get(k) for k in (
        "C_construction", "C_verification", "C_activation",
        "C_execution", "C_memory", "C_recovery")]
    _require(all(isinstance(x, int) and x >= 0 for x in parts)
             and cost.get("C_total") == sum(parts)
             and cost.get("wall_clock_excluded") is True,
             "strict exaptation cost identity failed")


def _check_semantics(semantics: Mapping[str, Any]) -> None:
    _require(semantics.get("result") == "TYPED_PROGRAM_SEMANTICS_LEAN_PASS",
             "proof semantics authority failed")
    _require(semantics.get("axioms_pass_count") == 11,
             "proof semantics theorem count failed")
    _require(semantics.get("allowed_axioms") == ["Classical.choice", "Quot.sound", "propext"],
             "proof semantics allowed axioms changed")
    _require(isinstance(semantics.get("lean_version"), str) and semantics["lean_version"].startswith("Lean"),
             "proof semantics Lean version missing")
    _require(re.fullmatch(r"[0-9a-f]{40}", semantics.get("mathlib_commit", "")) is not None,
             "proof semantics Mathlib identity malformed")
    _require(isinstance(semantics.get("source_hashes_sha256"), str)
             and len(semantics["source_hashes_sha256"]) == 64,
             "proof semantics source hash identity malformed")


def build_release_v2(*, repository: str, source_commit: str, run_id: int,
                     core_release: Mapping[str, Any], causal: Mapping[str, Any],
                     exaptation: Mapping[str, Any], semantics: Mapping[str, Any],
                     core_run_id: int) -> dict[str, Any]:
    """Build the consolidated v2 authority from independently replayed components."""
    _require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
             "source commit must be a full lowercase Git SHA")
    _require(run_id > 0 and core_run_id > 0 and re.fullmatch(r"[^/]+/[^/]+", repository) is not None,
             "invalid GitHub release identity")
    validate_release(core_release)
    _require(core_release.get("source_commit") == source_commit,
             "v1 core evidence is not for the v2 source commit")
    _require(core_release.get("run_id") == core_run_id,
             "v1 core run identity mismatch")
    _check_causal(causal)
    _check_exaptation(exaptation)
    _check_semantics(semantics)
    body = {
        "schema": SCHEMA_V2,
        "claim": CLAIM_V2,
        "scope": "bounded core v1 plus executable causality, strict prospective role requalification, and pinned proof-program semantics",
        "source_commit": source_commit,
        "run_id": run_id,
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "core_run_id": core_run_id,
        "core_run_url": f"https://github.com/{repository}/actions/runs/{core_run_id}",
        "components": {
            "core_v1": dict(core_release),
            "causal_executable_reuse": dict(causal),
            "strict_exaptation": dict(exaptation),
            "proof_program_semantics": dict(semantics),
        },
        "component_digests": {
            "core_v1": digest(core_release),
            "causal_executable_reuse": digest(causal),
            "strict_exaptation": digest(exaptation),
            "proof_program_semantics": digest(semantics),
        },
        "formal_authorities": [
            "v1 bounded Open Development core release",
            "shared ResidualEnvelope/v1 contract",
            "exact-rational executable causal/exaptation replay",
            "pinned Mathlib proof-program semantics with allowed-axiom audit",
        ],
        "limitations": LIMITATIONS_V2,
    }
    return {**body, "evidence_digest": digest(body)}


def validate_release_v2(manifest: Mapping[str, Any]) -> None:
    _require(manifest.get("schema") == SCHEMA_V2 and manifest.get("claim") == CLAIM_V2,
             "unknown v2 release claim or schema")
    supplied = manifest.get("evidence_digest")
    body = {key: value for key, value in manifest.items() if key != "evidence_digest"}
    _require(isinstance(supplied, str) and supplied == digest(body),
             "v2 release evidence is missing, malformed, or stale")
    rebuilt = build_release_v2(
        repository=manifest["run_url"].split("github.com/", 1)[1].split("/actions/", 1)[0],
        source_commit=manifest["source_commit"], run_id=manifest["run_id"],
        core_run_id=manifest["core_run_id"],
        core_release=manifest["components"]["core_v1"],
        causal=manifest["components"]["causal_executable_reuse"],
        exaptation=manifest["components"]["strict_exaptation"],
        semantics=manifest["components"]["proof_program_semantics"])
    _require(rebuilt == dict(manifest), "v2 release evidence does not match its declared run")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--finite", type=Path)
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--growth", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--core-release", type=Path)
    parser.add_argument("--causal", type=Path)
    parser.add_argument("--exaptation", type=Path)
    parser.add_argument("--semantics", type=Path)
    parser.add_argument("--core-run-id", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text())
    if args.core_release is not None:
        _require(all(x is not None for x in (
            args.causal, args.exaptation, args.semantics, args.core_run_id)),
            "v2 release requires core-release, causal, exaptation, semantics, and core-run-id")
        manifest = build_release_v2(
            repository=args.repository, source_commit=args.source_commit,
            run_id=args.run_id, core_run_id=args.core_run_id,
            core_release=load(args.core_release), causal=load(args.causal),
            exaptation=load(args.exaptation), semantics=load(args.semantics))
        validate_release_v2(manifest)
        label = "RELEASE_V2_EVIDENCE_PASS"
    else:
        _require(all(x is not None for x in (
            args.finite, args.proof, args.growth, args.native, args.reference)),
            "v1 release requires finite, proof, growth, native, and reference inputs")
        manifest = build_release(
            repository=args.repository, source_commit=args.source_commit,
            run_id=args.run_id, finite=load(args.finite), proof=load(args.proof),
            growth=load(args.growth), native=load(args.native), reference=load(args.reference))
        validate_release(manifest)
        label = "RELEASE_EVIDENCE_PASS"
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(label, manifest["evidence_digest"])


if __name__ == "__main__":
    main()
