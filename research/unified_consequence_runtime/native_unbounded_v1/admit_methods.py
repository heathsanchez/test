#!/usr/bin/env python3
"""Admit two distinct Lean-checked parametric Nat-LTS methods into real FLASH.

Only pinned checked product bytes are transported; no authority to mutate
source or decide arbitrary target applicability is conferred.  A backward
proof is not made logically dependent on a forward proof solely because the
search history tried forward first. Their causal lineage is tracked separately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stop(message):
    raise ValueError(message)


def commit(repo):
    return subprocess.check_output(
        ["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()


def blob(repo, path):
    return subprocess.check_output(
        ["git","-C",str(repo),"hash-object",path],text=True).strip()


def validate(paths, policy, native_run, protocol_bytes, report_raw):
    protocol = json.loads(protocol_bytes)
    report = json.loads(report_raw)
    r = native_run
    if (r.get("id") != policy["qualified_run_id"] or
        r.get("head_sha") != policy["qualified_head_sha"] or
        r.get("status") != "completed" or r.get("conclusion") != "success" or
        r.get("repository",{}).get("full_name") != "heathsanchez/test" or
        not str(r.get("path","")).endswith(policy["qualified_workflow"])):
        stop("UNQUALIFIED_OR_WRONG_NATIVE_RUN")
    if sha(protocol_bytes) != policy["original_protocol_sha256"]:
        stop("FROZEN_ORIGINAL_PROTOCOL_CHANGED")
    if report.get("source_protocol_sha256") != policy["original_protocol_sha256"]:
        stop("NATIVE_SOURCE_PROTOCOL_REPLAY_MISMATCH")
    if report.get("upstream_commit") != policy["original_source_commit"]:
        stop("UPSTREAM_NATIVE_SOURCE_MISMATCH")
    if report.get("method_sha256") != policy["original_universal_method_sha256"]:
        stop("UNIVERSAL_NATIVE_METHOD_CHANGED")
    if report.get("native_generic_induction") != "PASS":
        stop("PARAMETRIC_NAT_METHOD_NOT_LEAN_CHECKED")
    if report.get("negative_direction_check") != policy["negative_direction_check"]:
        stop("UNSOUND_ORIENTATION_NOT_REJECTED")
    if report.get("science_l7") != "UNKNOWN" or report.get("scientific_e2e_system") != "UNKNOWN":
        stop("SCIENTIFIC_AUTHORITY_INFLATED")
    if report.get("allowed_method_language_human_defined") is not True:
        stop("GENERATOR_AUTHORSHIP_NOT_ACKNOWLEDGED")
    if commit(paths.cslib) != policy["original_source_commit"]:
        stop("UNEXPECTED_CURRENT_CSLIB_SOURCE")
    cases = report.get("native_source_methods")
    if not isinstance(cases,list) or len(cases)!=3:
        stop("THREE_NATIVE_METHOD_PRODUCTS_REQUIRED")
    reference = {item["stage"]:item for item in protocol["source_sets"]}
    for idx, (actual, bound) in enumerate(zip(cases, policy["accepted"])):
        if (actual["stage"],actual["direction"],actual["system"],actual["native_proof_sha256"]) != (
            bound["stage"],bound["direction"],bound["system"],bound["proof_sha256"]):
            stop("NATIVE_METHOD_CASE_CORRESPONDENCE_MISMATCH")
        source=reference[actual["stage"]]
        if (actual["source_blob_sha"] != source["blob_sha"] or
            actual["file"] != source["file"] or
            actual["source_symbol"] != source["source_symbol"]):
            stop("SOURCE_SYSTEM_OR_GRAMMAR_MISMATCH")
        if blob(paths.cslib, source["file"]) != source["blob_sha"]:
            stop("ORIGINAL_CSLIB_NATIVE_BLOB_CHANGED")
        if actual.get("native_lean") != "PASS" or actual.get("delta") != 1:
            stop("SOURCE_NATIVE_METHOD_NOT_QUALIFIED")
        product=(paths.proofs/actual["native_proof_file"]).read_bytes()
        if sha(product) != actual["native_proof_sha256"]:
            stop("NATIVE_LEAN_PROOF_BYTES_CHANGED")
        if any(atom in product for atom in (b"sorry",b"admit",b"axiom")):
            stop("UNCHECKED_GENERATED_PROOF")
        if (b"theorem generated_unbounded" not in product or
            ("SourceInducedInfinite.forward" if actual["direction"]=="UP"
              else "SourceInducedInfinite.backward").encode() not in product):
            stop("GENERIC_THEOREM_NOT_USED_IN_NATIVE_PROOF")
    method=(paths.proofs/"source-method-compiled.lean").read_bytes()
    if sha(method)!=policy["original_universal_method_sha256"]:
        stop("COMPILED_UNBOUNDED_METHOD_BYTES_CHANGED")
    if [x["kind"] for x in report.get("old_method_residuals",[])] != [
       "UNKNOWN_PREVIOUS_FINITE_GRAMMAR"]*3:
        stop("FINITE_PREVIOUS_METHOD_UNSUPPORTED_NOT_ESTABLISHED")
    if [x["direction"] for x in cases]!=["UP","UP","DOWN"]:
        stop("METHOD_REFINEMENT_NOT_EARNED")
    hist=report.get("native_feedback_history",[])
    if len(hist)!=3 or sum(x["attempts"] for x in hist)+2 != report["total_native_calls"]:
        stop("NATIVE_SEARCH_COST_ACCOUNTING_INCONSISTENT")
    if not any(t["direction"]=="UP" and not t["accepted"]
               for t in hist[-1]["trials"]):
        stop("OLD_INDUCTION_DIRECTION_NOT_FALSIFIED")
    return protocol, report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cslib",type=Path,required=True)
    p.add_argument("--proofs",type=Path,required=True)
    p.add_argument("--native-run",type=Path,required=True)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    policy=json.loads(args.policy.read_bytes())
    run=json.loads(args.native_run.read_bytes())
    proto,report=validate(args,policy,run,args.protocol.read_bytes(),
                           (args.proofs/"report.json").read_bytes())
    from realitygraph.flash import ExternalEventEnvelope
    root=args.out
    for direction,label in [("UP","forward"),("DOWN","backward")]:
        selected=[x for x in report["native_source_methods"] if x["direction"]==direction]
        stages=[x["stage"] for x in selected]
        if stages!=(["ACQUIRE","HELDOUT"] if direction=="UP" else ["GENERATOR_REVISION"]):
            stop("GENESIS_STAGING_MISMATCH")
        identity=f"cslib:nat-infinite-trace:{label}-method:v1"
        evidence={
            "schema":"metalogic.native-parametric-method-event-evidence.v1",
            "run_id":policy["qualified_run_id"],
            "source_commit":policy["original_source_commit"],
            "producer_commit":policy["qualified_head_sha"],
            "artifact_id":policy["artifact_id"],
            "artifact_sha256":policy["artifact_zip_sha256"],
            "method_sha256":report["method_sha256"],
            "old_finite_method":"UNKNOWN_PREVIOUS_FINITE_GRAMMAR",
            "method_direction":direction,
            "qualified_products":[{
                "stage":x["stage"],"system":x["system"],
                "blob":x["source_blob_sha"],
                "proof_sha256":x["native_proof_sha256"],
                "source_symbol":x["source_symbol"]
            } for x in selected],
            "new_observation_or_extension":"source-feedback-selected parametric induction method within named meta-grammar",
            "native_trial_cost":report["total_native_calls"],
            "method_language_human_defined":True,
            "scientific_L7":"UNKNOWN","original_native_open_theorem":"NOT_CLAIMED",
            "applicability":"ONLY_THE_EXACT_SOURCE_SYSTEMS",
            "action_authorization":"NONE",
        }
        raw=canonical(evidence).encode()
        input_type="CSLib.LTS.Nat.ParametricSource@" + policy["original_source_commit"]
        semantics=[]
        for x in selected:
            key=x["system"]+"@"+x["source_blob_sha"]
            semantics.append([key,"LeanProof:"+x["native_proof_sha256"]])
        capability={
            "capability_id":identity,
            "input_type":input_type,
            "output_type":"Lean.Native.ParametricMTrProof",
            "semantics":semantics,
            "guard_inputs":[x[0] for x in semantics],
            "certificate_id":"LeanUniversalMethod:"+policy["original_universal_method_sha256"],
            "dependencies":[],
            "authority_snapshot":"cslib-unbounded-nat-method@"+policy["original_source_commit"],
            "verifier_id":"Lean4.35.0-rc4:CSLibNativeParametricInduction",
            "provenance_ids":[
                "native-run:"+str(policy["qualified_run_id"]),
                "method-compiler:"+policy["qualified_head_sha"],
                "native-source:"+policy["original_source_commit"],
                "method-direction:"+direction],
            "cost":len(selected)
        }
        e=ExternalEventEnvelope.capability(
            event_id=identity,repository="heathsanchez/test",
            commit=policy["qualified_head_sha"],
            authority_snapshot=capability["authority_snapshot"],
            verifier_id=capability["verifier_id"],
            source_evidence=raw,capability=capability,
            oracle=semantics,support_ids=[],
            origin="source-induced-method-within-human-typed-meta-substrate")
        directory=root/label
        directory.mkdir(parents=True,exist_ok=True)
        (directory/"evidence.json").write_bytes(raw)
        (directory/"event.json").write_text(e.to_text())
        e.verify_source_bytes((directory/"evidence.json").read_bytes())
        obj=e.to_runtime_event()
        if obj.capability.certificate_id!=capability["certificate_id"]:
            raise AssertionError("PROOF_METHOD_CERTIFICATE_CHANGED")
        print("NATIVE_PARAMETRIC_EVENT="+identity)
    print("SCIENTIFIC_GENERATOR_SELF_INVENTION=UNKNOWN")


if __name__=="__main__":
    main()
