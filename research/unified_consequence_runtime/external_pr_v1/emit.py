#!/usr/bin/env python3
"""Source-exact external PR behavior evidence for the original FLASH runtime.

The native tests, PR edits, and repairs all originate from external
contributors. This event represents precisely two historical red(base) /
green(head) observations plus a reusable *human-built* AST selection
method. It does not verify mathematical truth, authorize merge, or generate
a source-code fix.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def hashed(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def check(ok,reason):
    if not ok: raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    ap=argparse.ArgumentParser()
    for name in ("--policy","--evidence","--run","--out"):
        ap.add_argument(name,type=Path,required=True)
    a=ap.parse_args()
    p=read(a.policy)
    raw=a.evidence.read_bytes()
    r=json.loads(raw)
    run=read(a.run)
    check(p.get("schema")=="metalogic.external-pr-source-receipt-policy.v1","BAD_POLICY_SCHEMA")
    check(hashed(raw)==p["evidence_receipt_sha256"],"NATIVE_PR_RECEIPT_BYTES_DIFFER")
    check(r["protocol_sha256"]==p["protocol_sha256"],"EXTERNAL_PR_FROZEN_PROTOCOL_CHANGED")
    check(
        run.get("id")==p["producer_run"] and
        run.get("head_sha")==p["producer_head"] and
        run.get("repository",{}).get("full_name")==p["producer_repository"] and
        run.get("conclusion")=="success" and run.get("status")=="completed" and
        str(run.get("path","")).endswith(p["producer_workflow"]),
        "NATIVE_PR_VERIFIER_RUN_MISMATCH"
    )
    check(
        r["schema"]=="metalogic.real-external-pr-native-evidence.v1" and
        r["original_external_repo"]==p["external_source_repository"] and
        r["qualified_count"]==len(p["exact_cases"]) and
        r["advisory_conclusion"]=="NEUTRAL_REVIEW_EVIDENCE_ONLY" and
        r["action_authorization"]=="NONE" and r["code_repair_generated"]=="NO" and
        r["method_generator_software_authorship"]=="HUMAN_WRITTEN" and
        r["scientific_L7"]=="UNKNOWN",
        "PR_RECEIPT_SCOPE_OR_AUTHORITY_INFLATED"
    )
    evidence=[]
    semantic=[]
    for expected,actual in zip(p["exact_cases"],r["cases"]):
        check(actual["pr"]==expected["pr"],"EXTERNAL_PR_SEQUENCE_CHANGED")
        check(actual["base_sha"]==p["original_base"],"EXTERNAL_PR_BASE_CHANGED")
        check(actual["head_sha"]==expected["head"],"EXTERNAL_PR_HEAD_CHANGED")
        check(actual["result"]==p["verdict"],"NATIVE_PR_NOT_QUALIFIED")
        check(
            actual["source_behavioral_proof"]=="RED_BASE_GREEN_HEAD_NATIVE_TESTS" and
            actual["application_to_external_owner"]=="READ_ONLY_NOT_INSTALLED",
            "MISSING_NATIVE_PR_COUNTERFACTUAL_OR_INSTALLATION_LAUNDERED"
        )
        before=actual["before_source_with_head_tests"]
        after=actual["after_source_with_head_tests"]
        before_full=actual["old_full_suite_on_base"]
        head_full=actual["full_suite_on_head"]
        checks=actual["AST_derived_new_test_methods"]
        check(
            len(checks)==expected["discovered_tests"] and
            before["test_count"]==after["test_count"]==len(checks) and
            before["exit_code"]==1 and after["exit_code"]==0 and
            before_full["exit_code"]==head_full["exit_code"]==0 and
            before_full["test_count"]==expected["base_suite"] and
            head_full["test_count"]==expected["head_suite"],
            "NATIVE_PR_BEHAVIOR_CHANGED_OR_COUNTERFACTUAL_WEAK"
        )
        check(
            "AssertionError" in before["test_stdout_stderr_tail"] and
            "FAILED" in before["test_stdout_stderr_tail"] and
            "OK" in after["test_stdout_stderr_tail"] and
            "ModuleNotFoundError" not in before["test_stdout_stderr_tail"] and
            "ImportError" not in before["test_stdout_stderr_tail"],
            "EXTERNAL_PR_TEST_SETUP_FAILURE_NOT_BEHAVIORAL_REGRESSION"
        )
        id=f"{p['external_source_repository']}#{expected['pr']}@{expected['head']}"
        semantic.append([id,"NATIVE_RED_BASE_GREEN_HEAD_VERIFIED_SCOPED"])
        evidence.append({
            "pr":expected["pr"],
            "head":expected["head"],
            "base":p["original_base"],
            "discovered_tests":checks,
            "base_exit":before["exit_code"],
            "head_exit":after["exit_code"],
            "old_full_count":before_full["test_count"],
            "new_full_count":head_full["test_count"],
            "author_supplied_fix":True,
        })
    from realitygraph.flash import ExternalEventEnvelope
    ident="mathgraph-check:ieantn:two-real-pr-native-regressions:v1"
    snapshot="teorth-IEANTN-native-regressions@"+p["original_base"]
    verifier="Python3.12:IEANTN.stdlib-unittest-source-replay"
    source={
        "schema":"metalogic.external-pr-native-qualified-event.v1",
        "producer_native_verifier_run":p["producer_run"],
        "producer_commit":p["producer_head"],
        "zip_artifact_id":p["archive_id"],
        "zip_sha256":p["archive_zip_sha256"],
        "native_receipt_sha256":hashed(raw),
        "external_source_repository":p["external_source_repository"],
        "original_base_sha":p["original_base"],
        "observations":evidence,
        "method_generator_software_authorship":"HUMAN_WRITTEN",
        "external_pr_fixes_authored_by":"UPSTREAM_CONTRIBUTORS",
        "action_authorization":"NONE",
        "outside_owner_installed":"NO",
        "scientific_L7":"UNKNOWN",
    }
    source_bytes=canonical(source).encode()
    cap={
        "capability_id":ident,
        "input_type":"GitHub.PullRequest.ExactNativeRegressionScope",
        "output_type":"ReadOnly.NativeCounterfactualEvidence",
        "semantics":semantic,
        "guard_inputs":[x[0] for x in semantic],
        "certificate_id":"python-unittest-receipt:"+hashed(raw),
        "dependencies":[],
        "authority_snapshot":snapshot,
        "verifier_id":verifier,
        "provenance_ids":[
            "github-run:"+str(p["producer_run"]),
            "upstream-source:"+p["external_source_repository"],
            "external-pr:155","external-pr:158"],
        "cost":len(semantic),
    }
    envelope=ExternalEventEnvelope.capability(
        event_id=ident,
        repository=p["producer_repository"],
        commit=p["producer_head"],
        authority_snapshot=snapshot,
        verifier_id=verifier,
        source_evidence=source_bytes,
        capability=cap,
        oracle=semantic,
        support_ids=[],
        origin="outside-owner-native-pr-source-counterfactual-advisory"
    )
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"evidence.json").write_bytes(source_bytes)
    (a.out/"event.json").write_text(envelope.to_text())
    envelope.verify_source_bytes((a.out/"evidence.json").read_bytes())
    check(envelope.to_runtime_event().capability.certificate_id==cap["certificate_id"],
          "FLASH_PR_NATIVE_RECEIPT_CHANGED")
    print("QUALIFIED_TWO_EXTERNAL_ORIGINAL_PR_REGRESSIONS")
    print("NO_CODE_FIX_GENERATED")
    print("NO_GITHUB_APP_INSTALLATION")
    print("NO_GENERAL_L7_CLAIM")


if __name__=="__main__":
    main()
