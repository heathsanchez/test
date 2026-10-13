#!/usr/bin/env python3
"""Admit a real pinned native Lean proof as a narrowly scoped FLASH capability.

Must be given a successful, independently fetched GitHub Actions run and its
reconciled artifact bytes. This does NOT turn a tested finite relation into a
general CSLib proof-discovery method, and never grants action authority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_native_receipt(original, artifact, run, expected):
    if run.get("id") != expected["run_id"]:
        raise ValueError("WRONG_QUALIFICATION_RUN")
    if run.get("head_sha") != expected["head_sha"]:
        raise ValueError("WRONG_QUALIFICATION_SOURCE")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("NO_NATIVE_QUALIFICATION")
    if run.get("repository", {}).get("full_name") != "heathsanchez/test":
        raise ValueError("WRONG_QUALIFICATION_REPOSITORY")
    if not str(run.get("path", "")).endswith(
        ".github/workflows/unified-cslib-native-continuation.yml"):
        raise ValueError("WRONG_NATIVE_QUALIFICATION_WORKFLOW")
    m = json.loads((artifact / "manifest.json").read_text())
    if m["schema"] != "metalogic.cslib-native-proof-closure.v1":
        raise ValueError("UNKNOWN_NATIVE_PROOF_PROFILE")
    if m.get("native_verdict") != "NATIVE_CSLIB_SOURCE_PINNED_PASS":
        raise ValueError("NATIVE_PROOF_NOT_CHECKED")
    if m.get("source_commit") != "4b88bcac4c0dec65b3f45b59e85f5397045efd8d":
        raise ValueError("CSLIB_SEMANTIC_SOURCE_MISMATCH")
    if m.get("toolchain") != "leanprover/lean4:v4.35.0-rc4":
        raise ValueError("CSLIB_LEAN_VERSION_MISMATCH")
    if m.get("scientific_method_genesis") != "UNKNOWN":
        raise ValueError("IMPROPER_GENERAL_GENESIS_CLAIM")
    base = Path(original)
    if m["original_case_sha256"] != sha((base / "frozen.json").read_bytes()):
        raise ValueError("FROZEN_CASE_CONTENT_MISMATCH")
    if m["original_generator_sha256"] != sha((base / "run.py").read_bytes()):
        raise ValueError("FROZEN_GENERATOR_CONTENT_MISMATCH")
    cases = m.get("cases")
    if len(cases) != 6 or len(set((x["split"], x["id"]) for x in cases)) != 6:
        raise ValueError("INCOMPLETE_NATIVE_CASE_QUALIFICATION")
    for c in cases:
        if c["native_lean"] != "PASS":
            raise ValueError("INCOMPLETE_NATIVE_PROOF")
        raw = (artifact / c["proof_filename"]).read_bytes()
        if sha(raw) != c["proof_sha256"]:
            raise ValueError("PROOF_BYTES_DONT_MATCH")
        if b"sorry" in raw or b"admit" in raw or b"axiom" in raw:
            raise ValueError("FORBIDDEN_UNTRUSTED_PROOF")
        if b"theorem certified :" not in raw:
            raise ValueError("SEMANTIC_THEOREM_NOT_PRESENT")
    # The original independent algorithm is a second, source-pinned comparator.
    source = runpy.run_path(str(base / "run.py"))
    frozen = source["F"]
    target = next(c for c in frozen["holdout"] if c["id"] == "cycle")
    relation, _ = source["synthesize"](target)
    if relation != source["independent"](target):
        raise ValueError("INDEPENDENT_ORACLE_DISAGREES")
    cycle = next(c for c in cases if c["id"] == "cycle" and c["split"] == "holdout")
    if not cycle["seed_proven"] or cycle["seed_refuted"]:
        raise ValueError("TARGET_STATUS_MISMATCH")
    if cycle["source_simulation_pairs"] != len(relation):
        raise ValueError("PROOF_AND_REFERENCE_MISMATCH")
    return m, cycle, target, relation


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--proofs", type=Path, required=True)
    ap.add_argument("--native-run", type=Path, required=True)
    ap.add_argument("--policy", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    policy = json.loads(a.policy.read_text())
    run = json.loads(a.native_run.read_text())
    manifest, cycle, case, relation = verify_native_receipt(
        a.original, a.proofs, run, policy)

    # Existing FLASH is the only writer of authoritative typed event envelopes.
    from realitygraph.flash import ExternalEventEnvelope
    input_type = "CSLib.LTS.cycle.pair@4b88bcac"
    output_type = "BoolRelationMembership"
    sem = [
        [str(x) + "," + str(y), "true" if (x, y) in relation else "false"]
        for x in range(case["n"]) for y in range(case["n"])
    ]
    certificate_id = "lean:" + cycle["proof_sha256"]
    snapshot = "cslib-finite-source:" + manifest["source_commit"]
    verifier = "lean-v4.35.0-rc4:CSLib-LTS.IsSimulation"
    identity = "cslib:cycle:native-source-checked-simulation:v1"
    evidence = {
        "schema": "metalogic.cslib-native-proof-evidence.v1",
        "native_run_id": policy["run_id"],
        "native_run_head": run["head_sha"],
        "artifact_id": policy["artifact_id"],
        "artifact_sha256": policy["artifact_sha256"],
        "source_commits": {
            "native_coordinator": run["head_sha"],
            "cslib": manifest["source_commit"]
        },
        "native_cases": 6,
        "target": "cycle",
        "proof_sha256": cycle["proof_sha256"],
        "original_case_sha256": manifest["original_case_sha256"],
        "original_generator_sha256": manifest["original_generator_sha256"],
        "independent_finite_reference": "PASS",
        "native_lean": "PASS",
        "old_target_status": "FAILED_NATIVE_CERTIFICATE",
        "scope": "finite source-local LTS relation in pinned CSLib",
        "scientific_method_genesis": "UNKNOWN",
        "action_authorization": "NONE",
        "sci_e2e_system": "UNKNOWN"
    }
    raw = canonical(evidence).encode()
    cap = {
        "capability_id": identity,
        "input_type": input_type,
        "output_type": output_type,
        "semantics": sem,
        "guard_inputs": [row[0] for row in sem],
        "certificate_id": certificate_id,
        "dependencies": [],
        "authority_snapshot": snapshot,
        "verifier_id": verifier,
        "provenance_ids": [
            "github-run:" + str(policy["run_id"]),
            "CSLib-commit:" + manifest["source_commit"],
            "original-v10-run:38237298379"
        ],
        "cost": 1
    }
    envelope = ExternalEventEnvelope.capability(
        event_id=identity,
        repository="heathsanchez/test",
        commit=run["head_sha"],
        authority_snapshot=snapshot,
        verifier_id=verifier,
        source_evidence=raw,
        capability=cap,
        oracle=sem,
        support_ids=[certificate_id, "github-run:" + str(policy["run_id"])],
        origin="native-checked-finite-source-certificate",
    )
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "event.json").write_text(envelope.to_text())
    (a.out / "evidence.json").write_bytes(raw)
    envelope.verify_source_bytes((a.out / "evidence.json").read_bytes())
    # Parsing the native FLASH event remains a separate typed admission check.
    item = envelope.to_runtime_event()
    if item.capability.certificate_id != certificate_id:
        raise AssertionError("native certificate identity changed")
    print("SOURCE_PINNED_NATIVE_FLASH_EVENT_PREPARED")
    print("SEMANTIC_SCOPE=FINITE_CSLIB_NOT_GENERAL_METHOD_GENESIS")


if __name__ == "__main__":
    main()
