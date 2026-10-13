#!/usr/bin/env python3
"""Source-bound FLASH transport for external CSLib native semantic certificates.

The transported object is an exact pair of verified proof products, NOT an
unbounded programmable proof generator or an autonomous scientific result.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def fail(code):
    raise ValueError(code)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cslib", type=Path, required=True)
    p.add_argument("--proofs", type=Path, required=True)
    p.add_argument("--native-run", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()

    policy = json.loads(a.policy.read_bytes())
    protocol_bytes = a.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    report_bytes = (a.proofs / "report.json").read_bytes()
    report = json.loads(report_bytes)
    run = json.loads(a.native_run.read_bytes())
    if (run.get("id") != policy["run_id"] or
        run.get("head_sha") != policy["head_sha"] or
        run.get("repository", {}).get("full_name") != "heathsanchez/test" or
        run.get("status") != "completed" or run.get("conclusion") != "success" or
        not str(run.get("path","")).endswith(policy["workflow"])):
        fail("WRONG_NATIVE_QUALIFICATION")
    if sha(protocol_bytes) != policy["protocol_sha256"]:
        fail("PROTOCOL_AUTHORITY_CHANGED")
    if report.get("exact_protocol_sha256") != policy["protocol_sha256"]:
        fail("QUALIFICATION_PROTOCOL_MISMATCH")
    if report.get("native_verdict") != policy["native_verdict"]:
        fail("NO_NATIVE_SOURCE_METHOD_QUALIFICATION")
    if (report.get("scientific_L7") != "UNKNOWN" or
        report.get("generalized_self_improvement") != "UNKNOWN" or
        report.get("negative_infinite_support") != "UNKNOWN_INFINITE_SUPPORT"):
        fail("UNWARRANTED_METHOD_CLAIM")
    if report["source_commit"] != policy["upstream_commit"]:
        fail("ORIGINAL_SOURCE_COMMIT_MISMATCH")
    upstream = subprocess.check_output(["git","-C",str(a.cslib),"rev-parse","HEAD"],text=True).strip()
    if upstream != policy["upstream_commit"]:
        fail("SOURCE_CHECKOUT_MISMATCH")

    rows = report.get("sources", [])
    frozen = protocol["sources"]
    if len(rows) != len(frozen) or len(rows) != 2:
        fail("MISSING_QUALIFIED_NATIVE_SOURCE")
    indexed = {row["label"]: row for row in rows}
    sem = []
    certificates = []
    for source in frozen:
        label = source["label"]
        row = indexed.get(label)
        if row is None or row["source"] != source["file"] or row["source_blob_sha"] != source["blob_sha"]:
            fail("SOURCE_PROOF_CORRESPONDENCE_MISMATCH")
        original_blob = subprocess.check_output(
            ["git","-C",str(a.cslib),"hash-object",source["file"]],text=True).strip()
        if original_blob != source["blob_sha"]:
            fail("UNPINNED_SOURCE_BLOB")
        if row["reference"] != "INDEPENDENT_FIXED_POINT_AND_PARTITION_AGREE":
            fail("INDEPENDENT_ORACLE_NOT_QUALIFIED")
        native = row["native_proof"]
        if native["native_lean"] != "PASS" or native["relation_pairs"] < 4:
            fail("NATIVE_PROOF_INCOMPLETE")
        proof = (a.proofs / row["native_file"]).read_bytes()
        if sha(proof) != row["native_sha256"]:
            fail("NATIVE_PROOF_BYTES_DONT_MATCH")
        # Trust the exact independently run source+workflow proof check only.
        for bad in (b"sorry", b"admit", b"axiom"):
            if bad in proof:
                fail("GENERATED_UNCHECKED_PROOF")
        for required in ("theorem DerivedBisim_", "theorem DerivedRefutation_"):
            if required.encode() not in proof:
                fail("GENERATED_NATIVE_THEOREM_MISSING")
        input_key = source["file"] + "@" + source["blob_sha"]
        sem.append([input_key, "lean-proof:" + row["native_sha256"]])
        certificates.append({"source":source["file"],"blob":source["blob_sha"],
                             "native_proof_sha256":row["native_sha256"],
                             "relation_pairs":native["relation_pairs"],
                             "source_readout_count":native["input_constructor_count"]})
    if len(set(item[0] for item in sem)) != 2:
        fail("SOURCE_IDENTITY_NOT_DISTINCT")

    from realitygraph.flash import ExternalEventEnvelope
    source_id = "cslib:two-original-inductives:native-source-derived-bisimulation:v1"
    context = "source-bound-cslib:" + policy["upstream_commit"]
    checker = "Lean4.35-CSLib.Native.IsBisimulation"
    evidence = {
        "schema":"metalogic.cslib-original-source-method-evidence.v1",
        "qualified_native_run":policy["run_id"],
        "qualified_commit":policy["head_sha"],
        "artifact_id":policy["artifact_id"],
        "artifact_sha256":policy["artifact_sha256"],
        "source_commit":policy["upstream_commit"],
        "report_sha256":sha(report_bytes),
        "protocol_sha256":sha(protocol_bytes),
        "proof_products":certificates,
        "source_grammars":2,
        "generative_method_human_coded":True,
        "generalized_self_improvement":"UNKNOWN",
        "native_new_open_theorem":"UNKNOWN",
        "action_authorization":"NONE",
        "scientific_L7":"UNKNOWN",
    }
    evidence_bytes = canonical(evidence).encode()
    combined_cert = sha(canonical(certificates).encode())
    cap = {
        "capability_id":source_id,
        "input_type":"CSLib.OriginalInductiveLTS.Source",
        "output_type":"Lean.InductiveBisimulationCertificate",
        "semantics":sem,
        "guard_inputs":[item[0] for item in sem],
        "certificate_id":"lean-source-proof-products:" + combined_cert,
        "dependencies":[],
        "authority_snapshot":context,
        "verifier_id":checker,
        "provenance_ids":[
            "native-source-run:" + str(policy["run_id"]),
            "original-cslib:" + policy["upstream_commit"],
            "method-acquisition:" + policy["head_sha"]],
        "cost":1
    }
    envelope = ExternalEventEnvelope.capability(
        event_id=source_id, repository="heathsanchez/test",
        commit=policy["head_sha"], authority_snapshot=context,
        verifier_id=checker, source_evidence=evidence_bytes,
        capability=cap, oracle=sem, support_ids=[],
        origin="external-upstream-native-verified-human-built-generic-method")
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"evidence.json").write_bytes(evidence_bytes)
    (a.out/"event.json").write_text(envelope.to_text())
    envelope.verify_source_bytes((a.out/"evidence.json").read_bytes())
    restored = envelope.to_runtime_event()
    if restored.capability.certificate_id != cap["certificate_id"]:
        raise AssertionError("NATIVE_CERTIFICATE_IDENTITY_CHANGED")
    print("PASS_SOURCE_EXACT_NATIVE_PROOF_EVENT")
    print("GENERAL_METHOD_GENESIS=UNKNOWN")


if __name__ == "__main__":
    main()
