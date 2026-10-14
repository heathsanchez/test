#!/usr/bin/env python3
"""Consume a PREVIOUSLY qualified native artifact into a source-bound reviewer receipt.

No tests, models, or per-repo patch generation are rerun. This is a read-only
projection of a human-authored known-finding native verification, not an
independent evaluator of new review text or an automated PR merge decision.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

REQUIRED_LOGS = {
    "old_targeted_suite": "original_unit_suite.log",
    "original_native_observer": "original_review_witness.log",
    "candidate_native_observer_and_old_suite": "candidate_review_and_suite.log",
    "deliberately_wrong_candidate": "wrong_candidate_negative.log",
    "physical_patch_removal": "physically_restored_observer.log",
}
WARRANT = "WARRANTED_BOUNDED_KNOWN_REVIEW_FINDING_NATIVE_REMEDIATION"
INPUT_SCHEMA = "mathgraph-check.review-input.v1"


def digest(b):
    return hashlib.sha256(b).hexdigest()


def admit(doc, evidence, log_bytes):
    reasons=[]
    subject=doc.get("subject",{})
    original=doc.get("prior_native_run",{})
    if doc.get("schema")!=INPUT_SCHEMA:
        reasons.append("UNKNOWN_INPUT_SCHEMA")
    if subject.get("repo")!="allan-mobley-jr/gimmes" or subject.get("pr")!=468:
        reasons.append("UNKNOWN_SUBJECT")
    if subject.get("head")!=evidence.get("subject_head"):
        reasons.append("UNKNOWN_SOURCE_IDENTITY")
    if evidence.get("qualification")!=WARRANT or not evidence.get("native_execution_completed",False):
        reasons.append("UNKNOWN_VERIFICATION_BOUNDARY")
    if doc.get("expected_original_file_sha256")!=evidence.get("original_source_sha256"):
        reasons.append("UNKNOWN_ORIGINAL_FILE_IDENTITY")
    if original.get("run_id")!=38638946524 or original.get("artifact_id")!=11929207814:
        reasons.append("UNKNOWN_EVIDENCE_RUN")
    if original.get("sha256")!="0e567242796ff0a68fadb4ded8fe754b0721c450b221d5733b9edad1be793fbe":
        reasons.append("UNKNOWN_EVIDENCE_ARCHIVE_ID")
    if not evidence.get("final_exact_original_source_restored",False) or not evidence.get("temporary_test_removed",False):
        reasons.append("UNKNOWN_CAUSAL_RESTORATION")
    for name,path in REQUIRED_LOGS.items():
        step=evidence.get(name)
        if not isinstance(step,dict) or path not in log_bytes:
            reasons.append("UNKNOWN_MISSING_NATIVE_LOG:"+name)
            continue
        if step.get("log_sha256") != digest(log_bytes[path]):
            reasons.append("UNKNOWN_NATIVE_LOG_DIGEST:"+name)
            continue
        expected=0 if name in ("old_targeted_suite","candidate_native_observer_and_old_suite") else None
        if expected==0 and step.get("exit")!=0:
            reasons.append("UNKNOWN_REQUIRED_GREEN:"+name)
        if expected is None and step.get("exit")==0:
            reasons.append("UNKNOWN_REQUIRED_RED:"+name)
    if not isinstance(doc.get("findings"),list) or len(doc["findings"])!=3:
        reasons.append("UNKNOWN_REVIEW_INPUT_COUNT")
    else:
        keys=[f.get("key") for f in doc["findings"]]
        if len(set(keys))!=3 or keys.count("historical-volume-fallback")!=1:
            reasons.append("UNKNOWN_REVIEW_FINDING_ID")
        if any(f.get("producer")!="llm_review:claude-sonnet-4.6" for f in doc["findings"]):
            reasons.append("UNKNOWN_REVIEW_PRODUCER")
    return sorted(set(reasons))


def project(doc, evidence, log_bytes):
    reasons=admit(doc,evidence,log_bytes)
    admitted=not reasons
    records=[]
    for f in doc.get("findings",[]):
        is_native=(f.get("key")=="historical-volume-fallback"
                   and f.get("proof_role")=="native_separable")
        state=("WARRANTED_BOUNDED_NATIVE_WITNESS_AND_CANDIDATE_REPAIR"
               if admitted and is_native else
               "UNKNOWN_NORMATIVE_CONTRACT" if admitted else
               "UNKNOWN_SOURCE_OR_EVIDENCE")
        records.append({
            "key":f.get("key"),
            "location":{"file":f.get("file"),"start_line":f.get("start_line"),"end_line":f.get("end_line")},
            "producer":f.get("producer"),"original_review_message":f.get("review_message"),
            "status":state,
            "action":("Inspect the bounded candidate repair and tests; do not auto-merge"
                      if state.startswith("WARRANTED") else
                      "Require independent requirement/maintainer decision; do not auto-repair"),
            "evidence":(["native run 38638946524", "original RED; repair GREEN; wrong alternative RED; byte restore RED"]
                        if state.startswith("WARRANTED") else []),
        })
    return {
        "schema":"mathgraph-check.review-resolution-receipt.v1",
        "subject":doc.get("subject"),
        "original_review_proposals":len(records),
        "native_findings_promoted":sum(x["status"].startswith("WARRANTED") for x in records),
        "unknown_or_withheld":sum(not x["status"].startswith("WARRANTED") for x in records),
        "source_attestation": "WARRANTED_BOUNDED" if admitted else "UNKNOWN",
        "admission_errors":reasons,
        "reviewer_alone":"PUBLISHED_PRIOR_REVIEW_ONLY; NO_EXECUTION_RECEIPTS_ATTACHED",
        "mathgraph_path":"READ_ONLY_REPLAY_OF_PRIOR_NATIVE_EVIDENCE",
        "same_information_live_agent":"NOT_RUN",
        "novel_defect_discovery":"NOT_CLAIMED",
        "method_invention":"HUMAN_AUTHORED_INPUT_OBSERVER_REPAIR",
        "benchmark_score":"NOT_RUN",
        "merger_authority":"UNKNOWN",
        "artifact_ref":"https://github.com/heathsanchez/test/actions/runs/38638946524/artifacts/11929207814",
        "records":records,
    }


def render_markdown(result):
    lines=["# MathGraph Check — bounded review resolution preview",
           "",
           "Subject: "+str(result["subject"]),
           "",
           "Reviewer-only: "+str(result["original_review_proposals"])+
           " pre-existing source-anchored findings, no native receipts.",
           "Evidence consumer: "+str(result["native_findings_promoted"])+
           " bounded native findings admitted; "+str(result["unknown_or_withheld"])+
           " unresolved.",
           "Merge authority: UNKNOWN. Live coding-agent competitor NOT RUN.",
           ""]
    for r in result["records"]:
        lines+=["## "+r["key"],r["status"],r["action"],""]
    if result["admission_errors"]:
        lines+=["Revocation triggers: "+", ".join(result["admission_errors"])]
    lines+=["Source-scoped original native evidence: "+result["artifact_ref"]]
    return "\n".join(lines)+"\n"


def load(native_dir):
    doc=json.loads((Path(__file__).parent/"review_input.json").read_text())
    native=Path(native_dir)
    rec=json.loads((native/"receipt.json").read_text())
    logs={s:(native/s).read_bytes() for s in REQUIRED_LOGS.values()}
    return doc,rec,logs


def self_checks(doc,rec,logs):
    baseline=project(doc,rec,logs)
    if baseline["native_findings_promoted"]!=1 or baseline["unknown_or_withheld"]!=2:
        raise AssertionError("RECEIPT_BASELINE_INCOMPLETE:"+repr(baseline["admission_errors"]))
    changed=copy.deepcopy(doc);changed["subject"]["head"]="0"*40
    if project(changed,rec,logs)["native_findings_promoted"]!=0:
        raise AssertionError("STALE_SOURCE_EVIDENCE_PROMOTED")
    wrong=copy.deepcopy(rec);wrong["candidate_native_observer_and_old_suite"]["exit"]=1
    if project(doc,wrong,logs)["native_findings_promoted"]!=0:
        raise AssertionError("FAILED_PATCH_EVIDENCE_PROMOTED")
    dirty=dict(logs);bad=next(iter(dirty));dirty[bad]=dirty[bad]+b"\nALTERED\n"
    if project(doc,rec,dirty)["native_findings_promoted"]!=0:
        raise AssertionError("CORRUPT_LOG_PROMOTED")
    missing=dict(logs);del missing[bad]
    if project(doc,rec,missing)["native_findings_promoted"]!=0:
        raise AssertionError("MISSING_LOG_PROMOTED")
    withdrawn=copy.deepcopy(rec);withdrawn["final_exact_original_source_restored"]=False
    if project(doc,withdrawn,logs)["native_findings_promoted"]!=0:
        raise AssertionError("REVOKED_SOURCE_PROMOTED")
    return baseline


if __name__=="__main__":
    native_dir=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    doc,rec,logs=load(native_dir)
    result=self_checks(doc,rec,logs)
    raw=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    (out/"review_resolution.json").write_text(raw)
    (out/"review_resolution.md").write_text(render_markdown(result))
    print("REVIEW_RESOLUTION_RECEIPT_PASS; 1 bounded admitted, 2 unknown; 5/5 negative revocation controls")
    print("NO MODEL OR NATIVE TEST REEXECUTION")
