"""Fail-closed external-validity release authority.

v3 composes the same-commit Open Development v2 release with the independently
maintained MiniF2F post-freeze qualification.  It does not broaden the theorem
family or turn UNKNOWN into impossibility; it only binds the already-run
external-selection experiment into one replayable release identity.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from .release import validate_release_v2
from .residual import ResidualEnvelope
from .runtime import digest

SCHEMA_V3 = "open-development-release/v3"
CLAIM_V3 = (
    "bounded verifier-governed developmental machine with causal retention "
    "and externally selected prospective exaptation"
)
CORPUS_REPOSITORY = "google-deepmind/miniF2F"
CORPUS_COMMIT = "f0a20e14c1eeccd859d51bb4c2b3ee487889c303"
TEST_PATH = "MiniF2F/Test.lean"
TEST_BLOB_SHA1 = "7d3a756cb3da856fc26096c8da440f086653cfc1"

LIMITATIONS_V3 = [
    "external tasks are selected from a predeclared one-variable global-quadratic family, not arbitrary MiniF2F",
    "adapter, parser, exact-rational verifier, and requalification operation are supplied before external selection",
    "the independently maintained test split is pinned, but the protocol does not prove that no human had ever seen it",
    "selection uses a post-freeze platform run identity and can select a different pair on a rerun",
    "the external exact-rational interpreter is Python, not Lean-verified",
    "proof-program and constructor substrates elsewhere in the release remain finite and supplied",
    "zero acquisition budget is not zero execution cost",
    "UNKNOWN is never promoted to impossibility",
    "no unrestricted grammar invention, universal theorem proving, or metaphysical discovery/creation claim",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _hex(value: Any, n: int) -> bool:
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{n}}}", value) is not None


def _check_external(external: Mapping[str, Any], *, source_commit: str, external_run_id: int) -> None:
    _require(external.get("outcome") == "VERIFIED_EXTERNALLY_SELECTED_EXAPTATION",
             "external exaptation outcome failed")
    _require(external.get("freeze_commit") == source_commit,
             "external freeze/source commit mismatch")
    _require(external.get("selection_nonce") == str(external_run_id),
             "external selection nonce/run identity mismatch")
    _require(external.get("source_external_bytes_seen_at_freeze") is False,
             "external bytes were present at source freeze")
    _require(external.get("external_repository") == CORPUS_REPOSITORY
             and external.get("external_commit") == CORPUS_COMMIT
             and external.get("external_test_path") == TEST_PATH
             and external.get("external_test_blob_sha1") == TEST_BLOB_SHA1,
             "external corpus identity mismatch")
    _require(_hex(external.get("external_test_sha256"), 64)
             and _hex(external.get("source_freeze_digest"), 64)
             and _hex(external.get("source_state_id"), 64)
             and _hex(external.get("candidate_pool_digest"), 64),
             "external provenance digest malformed")
    _require(isinstance(external.get("candidate_count"), int) and external["candidate_count"] >= 2
             and external.get("B_index") != external.get("heldout_index"),
             "external post-freeze selection boundary failed")
    _require(external.get("classification") == {
        "reuse": False, "exaptation": True, "expansion": False},
        "external developmental classification failed")

    source, role, child = external.get("K_A"), external.get("K_B"), external.get("K_C")
    _require(all(_hex(x, 64) for x in (source, role, child)),
             "external lineage identities malformed")
    _require(_hex(external.get("K_A_fingerprint"), 64)
             and external.get("K_B_dependency") == source
             and external.get("K_C_dependency") == role,
             "external lineage dependency failed")

    _require(external.get("cold") == "unknown"
             and external.get("warm") == "verified"
             and external.get("B_acquisition_budget") == 2,
             "external B development boundary failed")
    residual = ResidualEnvelope.from_mapping(external.get("typed_residual", {}))
    _require(residual.residual_class == "GLOBAL_ROLE_REQUALIFICATION_REQUIRED"
             and residual.diagnosis == "capability_failure"
             and residual.evidence_strength == "exact-replay-certified"
             and residual.source == source
             and residual.source_fingerprint == external.get("K_A_fingerprint")
             and residual.necessary_constraint == residual.constraint,
             "external typed residual failed")
    _require(residual.constraint.get("must_depend_on") == source
             and residual.constraint.get("must_preserve_source_fingerprint") == external.get("K_A_fingerprint")
             and residual.constraint.get("must_reverify_power0_square_on_all_reals") is True,
             "external residual constraint failed")

    _require(external.get("restart") is True
             and external.get("heldout_acquisition_budget") == 0
             and external.get("heldout_verdict") == "verified"
             and external.get("heldout_execution_trace") == [child, role, source],
             "external held-out causal execution failed")
    for key in ("B", "heldout"):
        task = external.get(key, {})
        _require(isinstance(task.get("name"), str) and task.get("name")
                 and _hex(task.get("statement_sha256"), 64)
                 and _hex(task.get("global_certificate_sha256"), 64)
                 and isinstance(task.get("polynomial"), Mapping),
                 f"external {key} identity malformed")
    _require(external["B"]["statement_sha256"] != external["heldout"]["statement_sha256"],
             "external B and held-out are identical")

    behavioral = external.get("behavioral_identity", {})
    _require(behavioral.get("same_behavioral_class_on_B_and_heldout") is True
             and behavioral.get("not_available_to_developer") is True
             and _hex(behavioral.get("source_distinct_implementation_hash"), 64),
             "external source-distinct behavioral check failed")

    controls = external.get("controls", {})
    _require(controls.get("same_size_sham_K_B") == "refuted"
             and controls.get("wrong_direction_adapter") == "refuted"
             and controls.get("missing_K_A_executable_identity") == "unknown"
             and controls.get("unrelated_removal") == "verified"
             and controls.get("ancestor_revocation_heldout") == "unknown"
             and controls.get("raw_history_reconstruction_same_B_budget") == "unknown"
             and controls.get("matched_fixed_policy", {}).get("B_acquisition_budget") == 2
             and controls.get("matched_fixed_policy", {}).get("verdict") == "unknown"
             and controls.get("restored_source_same_identity") is True
             and controls.get("restored_development") == "verified"
             and controls.get("restored_heldout") == "verified"
             and controls.get("history_preserved") is True,
             "external opposing controls failed")
    _require({source, role, child} <= set(controls.get("revoked_lineage_contains", [])),
             "external revocation lineage incomplete")


def build_release_v3(*, repository: str, source_commit: str, run_id: int,
                     v2_run_id: int, external_run_id: int,
                     v2_release: Mapping[str, Any], external: Mapping[str, Any]) -> dict[str, Any]:
    _require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
             "source commit must be a full lowercase Git SHA")
    _require(all(isinstance(x, int) and x > 0 for x in (run_id, v2_run_id, external_run_id))
             and re.fullmatch(r"[^/]+/[^/]+", repository) is not None,
             "invalid GitHub release identity")
    validate_release_v2(v2_release)
    _require(v2_release.get("source_commit") == source_commit,
             "v2 authority is not for the v3 source commit")
    _require(v2_release.get("run_id") == v2_run_id,
             "v2 authority run identity mismatch")
    _check_external(external, source_commit=source_commit, external_run_id=external_run_id)

    body = {
        "schema": SCHEMA_V3,
        "claim": CLAIM_V3,
        "scope": (
            "Open Development v2 plus a post-freeze, independently maintained MiniF2F "
            "external-selection qualification within the precommitted global-quadratic family"
        ),
        "source_commit": source_commit,
        "run_id": run_id,
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "v2_run_id": v2_run_id,
        "v2_run_url": f"https://github.com/{repository}/actions/runs/{v2_run_id}",
        "external_run_id": external_run_id,
        "external_run_url": f"https://github.com/{repository}/actions/runs/{external_run_id}",
        "components": {
            "release_v2": dict(v2_release),
            "external_minif2f_post_freeze": dict(external),
        },
        "component_digests": {
            "release_v2": digest(v2_release),
            "external_minif2f_post_freeze": digest(external),
        },
        "formal_authorities": [
            "same-commit Open Development release/v2 authority",
            "shared ResidualEnvelope/v1 fail-closed contract",
            "post-freeze pinned google-deepmind/miniF2F Test.lean corpus identity",
            "exact-rational external role/program replay with causal ablation and source-distinct behavioral control",
        ],
        "limitations": LIMITATIONS_V3,
    }
    return {**body, "evidence_digest": digest(body)}


def validate_release_v3(manifest: Mapping[str, Any]) -> None:
    _require(manifest.get("schema") == SCHEMA_V3 and manifest.get("claim") == CLAIM_V3,
             "unknown v3 release claim or schema")
    supplied = manifest.get("evidence_digest")
    body = {key: value for key, value in manifest.items() if key != "evidence_digest"}
    _require(isinstance(supplied, str) and supplied == digest(body),
             "v3 release evidence is missing, malformed, or stale")
    rebuilt = build_release_v3(
        repository=manifest["run_url"].split("github.com/", 1)[1].split("/actions/", 1)[0],
        source_commit=manifest["source_commit"], run_id=manifest["run_id"],
        v2_run_id=manifest["v2_run_id"], external_run_id=manifest["external_run_id"],
        v2_release=manifest["components"]["release_v2"],
        external=manifest["components"]["external_minif2f_post_freeze"])
    _require(rebuilt == dict(manifest), "v3 release evidence does not match its declared runs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--v2-run-id", required=True, type=int)
    parser.add_argument("--external-run-id", required=True, type=int)
    parser.add_argument("--v2-release", type=Path, required=True)
    parser.add_argument("--external", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text())
    manifest = build_release_v3(
        repository=args.repository, source_commit=args.source_commit, run_id=args.run_id,
        v2_run_id=args.v2_run_id, external_run_id=args.external_run_id,
        v2_release=load(args.v2_release), external=load(args.external))
    validate_release_v3(manifest)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("RELEASE_V3_EXTERNAL_VALIDITY_PASS", manifest["evidence_digest"])


if __name__ == "__main__":
    main()
