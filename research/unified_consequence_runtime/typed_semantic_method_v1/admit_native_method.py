#!/usr/bin/env python3
"""Admit genuine pinned CSLib method-generated Lean proof products into FLASH.

The granted scope is ONLY the three frozen actual theorem statements. These
typed events do not authorize arbitrary method execution or attest that the
human-authored meta-generator learned to rewrite its own implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fail(reason):
    raise ValueError(reason)


def git(repo,*args):
    return subprocess.check_output(
        ["git","-C",str(repo),*args],text=True).strip()


def checked_source(repo,protocol):
    if git(repo,"rev-parse","HEAD")!=protocol["upstream"]["commit"]:
        fail("CSLIB_ORIGINAL_SOURCE_COMMIT_CHANGED")
    for original in protocol["exact_source_modules"]:
        if git(repo,"hash-object",original["path"])!=original["git_blob"]:
            fail("CSLIB_ORIGINAL_SOURCE_BLOB_CHANGED")


def main():
    arg=argparse.ArgumentParser()
    for key in ("--cslib","--protocol","--policy","--proofs","--run","--out"):
        arg.add_argument(key,type=Path,required=True)
    a=arg.parse_args()

    policy=json.loads(a.policy.read_bytes())
    protocol_raw=a.protocol.read_bytes()
    protocol=json.loads(protocol_raw)
    report_raw=(a.proofs/"report.json").read_bytes()
    report=json.loads(report_raw)
    run=json.loads(a.run.read_bytes())

    if (
        run.get("id")!=policy["run_id"] or
        run.get("head_sha")!=policy["run_commit"] or
        run.get("repository",{}).get("full_name")!="heathsanchez/test" or
        run.get("status")!="completed" or run.get("conclusion")!="success" or
        not str(run.get("path","")).endswith(policy["qualified_workflow"])
    ):
        fail("SOURCE_METHOD_NATIVE_RUN_NOT_QUALIFIED")
    if digest(protocol_raw)!=policy["original_protocol_raw_sha256"]:
        fail("FROZEN_METHOD_PROTOCOL_CHANGED")
    if report.get("protocol_raw_sha256")!=policy["original_protocol_raw_sha256"]:
        fail("SOURCE_METHOD_PROOF_PROTOCOL_CHANGED")
    if report.get("exact_upstream_sha")!=policy["original_source_commit"]:
        fail("NATIVE_METHOD_UPSTREAM_SOURCE_CHANGED")
    if report.get("scientific_status")!="WARRANTED_BOUNDED_NATIVE_METHOD_GRAMMAR_EXTENSION":
        fail("NATIVE_METHOD_NOT_QUALIFIED")
    if report.get("native_call_count")!=policy["expected_native_calls"]:
        fail("SOURCE_METHOD_NATIVE_CALL_COUNT_CHANGED")
    if report.get("native_source_theorem_count")!=policy["expected_theorem_names_mined"]:
        fail("SOURCE_METHOD_SOURCE_CATALOGUE_CHANGED")
    if report.get("general_autonomous_L7")!="UNKNOWN":
        fail("NATIVE_METHOD_UNSUPPORTED_L7_CLAIM")
    if report.get("meta_generator_substrate_human_written") is not True:
        fail("METHOD_GENERATOR_AUTHORSHIP_CHANGED")
    if report.get("source_theorems_are_original_preexisting") is not True:
        fail("SOURCE_THEOREMS_ARE_NOT_PREEXISTING")
    checked_source(a.cslib,protocol)

    index=json.loads((a.proofs/"source-lemma-index.json").read_bytes())
    learned=json.loads((a.proofs/"retained-method-grammar.json").read_bytes())
    if learned.get("qualified_source_commit")!=policy["original_source_commit"]:
        fail("LEARNED_GRAMMAR_SOURCE_CHANGED")
    if learned.get("publisher_authority")!="NONE":
        fail("LEARNED_GRAMMAR_SELF_AUTHORIZATION")
    if len(report.get("native_goal_scoped_results",[]))!=len(policy["proof_products"]):
        fail("QUALIFIED_NATIVE_GOAL_COUNT_CHANGED")
    if len(policy["proof_products"])!=3:
        fail("EXPECTED_THREE_SOURCE_BOUND_GOALS")

    frozen_by_stage={g["stage"]:g for g in protocol["target_goals"]}
    native_results={g["stage"]:g for g in report["native_goal_scoped_results"]}
    memory=[]
    from realitygraph.flash import ExternalEventEnvelope

    a.out.mkdir(parents=True,exist_ok=True)
    events=[]
    for spec in policy["proof_products"]:
        stage=spec["stage"]
        goal=frozen_by_stage[stage]
        source=native_results[stage]
        if source["status"]!="PASS_SCOPED" or source["goal_id"]!=spec["goal_id"]:
            fail("SCOPED_METHOD_TARGET_NOT_QUALIFIED")
        if source["original_goal"]!=goal["statement"]:
            fail("NATIVE_PROOF_GOAL_NOT_ORIGINAL")
        if source["native_proof_sha256"]!=spec["sha256"] or source["native_proof_path"]!=spec["proof"]:
            fail("NATIVE_PROOF_IDENTITY_CHANGED")
        if source["new_method_primitives"]!=[spec["new_source_rule"]]:
            fail("QUALIFIED_NEW_METHOD_RULE_NOT_PRESENT")
        if source["previous_exact_program_reused"] is not False:
            fail("METHOD_GRAMMAR_EXTENSION_WAS_NOT_NECESSARY")
        if source["baseline_ties"]:
            fail("STRONG_NATIVE_BASELINE_ALREADY_PROVED_GOAL")
        if not all(not entry["candidate_passed_without"]
                   for entry in source["source_lemma_deletion_checks"]):
            fail("NEW_METHOD_RULE_NOT_CAUSALLY_NECESSARY")
        if source["source_lemma_deletion_checks"] != [{
            "lemma":spec["new_source_rule"],"candidate_passed_without":False}]:
            fail("SOURCE_THEOREM_DELETION_REPORT_CHANGED")
        original=index.get(spec["new_source_rule"])
        if original is None or original["source"] not in {
                v["path"] for v in protocol["exact_source_modules"]}:
            fail("SOURCE_RULE_NOT_DERIVED_FROM_FROZEN_LIBRARY")
        if original["name"]!=spec["new_source_rule"]:
            fail("SOURCE_LEMMA_NAME_CHANGED")
        if original["name"].split(".")[-1] not in (
            a.cslib/original["source"]).read_text(encoding="utf-8"):
            fail("SOURCE_THEOREM_NOT_PRESENT")
        memory.append(spec["new_source_rule"])
        if source["source_lemmas_retained"]!=memory:
            fail("SOURCE_METHOD_GENERATOR_GRAMMAR_REPLAY_CHANGED")

        path=a.proofs/spec["proof"]
        proof_bytes=path.read_bytes()
        if digest(proof_bytes)!=spec["sha256"]:
            fail("EXACT_NATIVE_PROOF_BYTES_CHANGED")
        required=("theorem exact_target\n    "+goal["statement"]+" := by").encode()
        if required not in proof_bytes:
            fail("GENERATED_THEOREM_SCOPE_CHANGED")
        if any(word in proof_bytes for word in (b"sorry",b"admit",b"axiom")):
            fail("GENERATED_THEOREM_HAS_UNTRUSTED_ESCAPE")
        if spec["new_source_rule"].encode() not in proof_bytes:
            fail("NEWLY_LEARNED_RULE_NOT_EXECUTED")
        key="cslib:transport-method:"+stage.lower()+":v1"
        evidence={
            "schema":"metalogic.native-typed-grammar-proof-evidence.v1",
            "native_run":policy["run_id"],
            "run_sha":policy["run_commit"],
            "artifact_id":policy["artifact_id"],
            "artifact_sha256":policy["artifact_zip_sha256"],
            "upstream_cslib_source_sha":policy["original_source_commit"],
            "source_module_pins":{v["path"]:v["git_blob"]
                                  for v in protocol["exact_source_modules"]},
            "protocol_sha256":policy["original_protocol_raw_sha256"],
            "stage":stage,
            "frozen_goal":spec["goal_id"],
            "frozen_goal_sha256":digest(goal["statement"].encode()),
            "native_proof_sha256":spec["sha256"],
            "learned_source_rule":spec["new_source_rule"],
            "retained_earlier_source_rules":memory[:-1],
            "source_lemma_deletion_ablation":"PASS_SCOPED_PROOF_PLAN",
            "native_method_candidate_count":report["native_call_count"],
            "meta_generator_human_authored":True,
            "action_authorization":"NONE",
            "scientific_open_theorem":"NOT_CLAIMED",
            "scientific_L7":"UNKNOWN"
        }
        evidence_bytes=canonical(evidence).encode()
        observable=spec["goal_id"]+"@"+digest(goal["statement"].encode())
        sem=[[observable,"LeanSourceProof:"+spec["sha256"]]]
        capability={
            "capability_id":key,
            "input_type":"CSLib.FrozenSourceGoal",
            "output_type":"Lean.Native.SourceComposedProof",
            "semantics":sem,
            "guard_inputs":[observable],
            "certificate_id":"LeanProof:"+spec["sha256"],
            "dependencies":[],
            "authority_snapshot":"CSLib.source-bound.typed-transport@"+policy["original_source_commit"],
            "verifier_id":"Lean4.35.0-rc4:CSLib.StructuralTransport",
            "provenance_ids":[
                "source-native-run:"+str(policy["run_id"]),
                "source-compiler:"+policy["run_commit"],
                "source-grammar-stage:"+stage,
                "source-rule:"+spec["new_source_rule"]
            ],
            "cost":1
        }
        e=ExternalEventEnvelope.capability(
            event_id=key,
            repository="heathsanchez/test",
            commit=policy["run_commit"],
            authority_snapshot=capability["authority_snapshot"],
            verifier_id=capability["verifier_id"],
            source_evidence=evidence_bytes,
            capability=capability,
            oracle=sem,
            support_ids=[],
            origin="source-mined-native-checked-scoped-method-proof")
        destination=a.out/stage.lower()
        destination.mkdir(parents=True,exist_ok=True)
        (destination/"event.json").write_text(e.to_text())
        (destination/"evidence.json").write_bytes(evidence_bytes)
        e.verify_source_bytes((destination/"evidence.json").read_bytes())
        if e.to_runtime_event().capability.certificate_id!=capability["certificate_id"]:
            raise AssertionError("FLASH_CHANGED_SOURCE_METHOD_CERTIFICATE")
        events.append(key)
    if learned["source_lemmas"]!=memory:
        fail("FINAL_GENERATIVE_LANGUAGE_NOT_RETAINED")
    print("NATIVE_SOURCE_DERIVED_TYPED_CAPABILITIES="+str(len(events)))
    print("NATIVE_METHOD_RULES="+canonical(memory))
    print("METHOD_SUBSTRATE_SELF_INVENTION=UNKNOWN")


if __name__=="__main__":
    main()
