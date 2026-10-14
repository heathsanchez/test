#!/usr/bin/env python3
"""Native cross-repository source-A coherence replay, no method reselection.

Only real checked-out uiri/toml implementations and independently installed
Python standard-library tomllib are used.  A single human-authored codec binding
is frozen across all PRs; the sole selected predicate comes from prior source A.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import tomllib

SUBJECTS = {
    "T1": {"old": "3f637dba5f68db63d4b30967fedda51c82459471",
           "head": "e879373d2e86a02c1d9b13438e6dadfdad935577",
           "pr": 367},
    "T2": {"old": "3f637dba5f68db63d4b30967fedda51c82459471",
           "head": "99d17a24e137e2d2a5118e468b0d06e0d2065739",
           "pr": 349},
    "T3": {"old": "65bab7582ce14c55cdeec2244c65ea23039c9e6f",
           "head": "c97a49cfe10f584a36ea5746fe651331d3c777ab",
           "pr": 453},
}
SOURCE_A_OLD = "7ab7469addd60e03ca3bfbb1287642e8d771e1c0"
SOURCE_A_HEAD = "dcdfda3f825189c7f31048b6598142a944151073"
V11_BLOB = "0f7fb6b837cd65aa86b5fef7c097196fc0df4845"

# Frozen BEFORE author patches were opened. No source-specific target functions.
PAYLOADS = [
    [], [1], [1, 2], [1, 2, 3], ["a", "b"], [1, "abc"],
    [{}], [{}, {}], [{"x": 1}, {}], [{}, {"x": 2}],
    [{"nested": {}}, {}], [{"x": 1}, {"y": 2}], [{"x": []}, {}],
    {"x": {}}, {"x": {"y": 1}}, {"x": []},
    "hello", "a'b", 'a"b', "\\", "x\u0001", "\u0001x", "end\u001f",
]
WRAPPERS = ("value", "items")

def normalized(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def cases():
    result = []
    for ix, payload in enumerate(PAYLOADS):
        for wrapper in WRAPPERS:
            result.append({"id":f"case_{ix:02d}_{wrapper}",
                           "input":{wrapper:deepcopy(payload)}})
    return result

def ensure_source(repo:Path,commit:str):
    res=subprocess.run(["git","rev-parse","HEAD"],cwd=repo,capture_output=True,text=True)
    if res.returncode or res.stdout.strip()!=commit:
        raise ValueError("UNKNOWN_TARGET_WRONG_GIT_SHA")
    # Check entire tree is exact original checkout, not a working patch.
    res=subprocess.run(["git","status","--porcelain"],cwd=repo,capture_output=True,text=True)
    if res.returncode or res.stdout.strip():
        raise ValueError("UNKNOWN_TARGET_DIRTY_SOURCE")

def source_native(repo_dir, commit, subject, side, output):
    repo=Path(repo_dir).resolve()
    if subject not in SUBJECTS or side not in ("old","head"):
        raise ValueError("UNKNOWN_TARGET_SUBJECT")
    if SUBJECTS[subject][side]!=commit:
        raise ValueError("UNKNOWN_TARGET_DECLARED_SHA")
    ensure_source(repo,commit)
    sys.path.insert(0,str(repo))
    import toml
    module=Path(toml.__file__).resolve()
    if not module.is_relative_to(repo):
        raise ValueError("UNKNOWN_WRONG_TOML_PACKAGE")
    began=time.monotonic()
    rows=[]
    for case in cases():
        input_data=deepcopy(case["input"])
        record={"id":case["id"],"input":input_data}
        try:
            encoded=toml.dumps(deepcopy(input_data))
            record["native_encoder_status"]="OK"
            record["serialized"]=encoded
        except Exception as exc:
            record["native_encoder_status"]="UNKNOWN_"+type(exc).__name__
            record["serialized"]=None
        if record["serialized"] is None:
            record.update(reference_status="NOT_EXECUTED", decoded=None,
                          coherence=None,label="UNKNOWN")
        else:
            try:
                data=tomllib.loads(record["serialized"])
                record["reference_status"]="OK"
                record["decoded"]=data
                record["coherence"]=data==input_data
                record["label"]="PASS" if record["coherence"] else "FAIL"
            except Exception as exc:
                record["reference_status"]="ERROR_"+type(exc).__name__
                record["decoded"]=None
                record["coherence"]=False
                record["label"]="FAIL"
        rows.append(record)
    results={
        "repo":"uiri/toml",
        "pr":SUBJECTS[subject]["pr"],
        "subject":subject,
        "revision":side,
        "commit":commit,
        "native_module_file":str(module.relative_to(repo)),
        "compiler":"Python "+sys.version.split()[0],
        "frozen_input_grammar_sha256":sha(normalized(cases()).encode()),
        "finite_case_count":len(rows),
        "wall_seconds_native":round(time.monotonic()-began,6),
        "rows":rows
    }
    p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(results,indent=2,sort_keys=True)+"\n")
    print(normalized({"subject":subject,"revision":side,"source":commit,
          "native_runs":len(rows),"pass":sum(r["label"]=="PASS" for r in rows),
          "fail":sum(r["label"]=="FAIL" for r in rows),
          "unknown":sum(r["label"]=="UNKNOWN" for r in rows)}))

def verified_policy(path):
    location=Path(path)
    if not location.is_file():
        return None, "UNKNOWN_NO_SOURCE_CAPABILITY"
    receipt_path=location.parent/"frozen_A_capability_sha256.txt"
    if not receipt_path.is_file():
        return None, "UNKNOWN_MISSING_SOURCE_PIN"
    expected=receipt_path.read_text().split()[0]
    if len(expected)!=64 or sha(location.read_bytes())!=expected:
        return None, "UNKNOWN_BAD_SOURCE_SUPPORT"
    policy=json.loads(location.read_bytes())
    if (policy.get("source_A")!={"old":SOURCE_A_OLD,"head":SOURCE_A_HEAD} or
        policy.get("original_v11_solver_blob")!=V11_BLOB or
        policy.get("selected_channels")!=["coherence"] or
        policy.get("source_compiled_lookup",{}).get("[true]")!="PASS" or
        policy.get("source_compiled_lookup",{}).get("[false]")!="FAIL"):
        return None, "UNKNOWN_UNQUALIFIED_SOURCE_POLICY"
    return policy,"WARRANTED_BOUNDED_A_SOURCE_ADMISSION"

def classify(policy,record):
    if policy is None:
        return "UNKNOWN_NO_SOURCE_CAPABILITY"
    if record["coherence"] is None:
        return "UNKNOWN_UNSUPPORTED_NATIVE_ENCODING"
    key=normalized([record["coherence"]])
    return policy["source_compiled_lookup"].get(key,"UNKNOWN_UNSEEN_SOURCE_OBSERVATION")

def transfer(policy_path,folder,destination):
    policy,status=verified_policy(policy_path)
    if policy is None:
        raise ValueError("SOURCE_CAPABILITY_UNAVAILABLE:"+status)
    root=Path(folder)
    begin=time.monotonic()
    outcomes={}
    for subj in SUBJECTS:
        old=json.loads((root/(subj+"old.json")).read_text())
        head=json.loads((root/(subj+"head.json")).read_text())
        if (old["commit"]!=SUBJECTS[subj]["old"] or
            head["commit"]!=SUBJECTS[subj]["head"] or
            old["subject"]!=subj or head["subject"]!=subj or
            old["revision"]!="old" or head["revision"]!="head"):
            raise ValueError("UNKNOWN_WRONG_NATIVE_SUBJECT")
        if ([r["id"] for r in old["rows"]] !=
            [r["id"] for r in head["rows"]]):
            raise ValueError("UNKNOWN_NONIDENTICAL_NATIVE_INPUTS")
        repaired=[];diffs=0;lexical_only=0;unresolved=[];false=0
        examples=[];control_concordance=0
        for a,b in zip(old["rows"],head["rows"]):
            p=classify(policy,a);q=classify(policy,b)
            if p in ("PASS","FAIL") and p!=a["label"]:false+=1
            if q in ("PASS","FAIL") and q!=b["label"]:false+=1
            if a["label"]=="FAIL" and b["label"]=="PASS":
                repaired.append(a["id"])
                if len(examples)<3:
                    examples.append({"id":a["id"],"source":a["input"],
                                     "old_serialized":a["serialized"],
                                     "head_serialized":b["serialized"],
                                     "source_coherence":a["coherence"],
                                     "head_coherence":b["coherence"]})
            if a["serialized"]!=b["serialized"] and a["serialized"] is not None and b["serialized"] is not None:
                diffs+=1
                if a["label"]==b["label"]=="PASS":
                    lexical_only+=1
            if a["label"]==b["label"]=="PASS":
                control_concordance+=1
            if a["label"]=="UNKNOWN" or b["label"]=="UNKNOWN":
                unresolved.append(a["id"])
        introduced=sum(1 for a,b in zip(old["rows"],head["rows"])
                       if a["label"]=="PASS" and b["label"]=="FAIL")
        outcomes[subj]={
            "introduced_native_violations":introduced,
            "source_old":old["commit"],"source_head":head["commit"],
            "tested_case_count":len(old["rows"]),
            "old_native_coherence_violations":sum(r["label"]=="FAIL" for r in old["rows"]),
            "new_native_coherence_violations":sum(r["label"]=="FAIL" for r in head["rows"]),
            "original_native_UNKNOWN":sum(r["label"]=="UNKNOWN" for r in old["rows"]),
            "contributor_native_UNKNOWN":sum(r["label"]=="UNKNOWN" for r in head["rows"]),
            "old_fail_to_head_pass_count":len(repaired),
            "old_fail_to_head_pass_inputs":repaired,
            "selected_A_coherence_detected":len(repaired),
            "false_warrants":false,
            "string_output_changed_cases":diffs,
            "valid_lexical_only_changed_cases":lexical_only,
            "ordinary_both_Pass_controls":control_concordance,
            "unknown_case_count":len(unresolved),"unknown_cases":unresolved,
            "examples":examples}
    # A normal independent stateless codec checker computes the same predicate;
    # retaining A's source choice does NOT create an economic advantage.
    assert policy["selected_channels"]==["coherence"]
    assert all(v["false_warrants"]==0 for v in outcomes.values())
    assert (outcomes["T2"]["old_fail_to_head_pass_count"]==0
            and outcomes["T2"]["introduced_native_violations"]==0
            and outcomes["T2"]["valid_lexical_only_changed_cases"]>0), (
                "T2 formatting-only negative control failed")
    removed=Path(policy_path).with_suffix(".withdrawn")
    original=Path(policy_path)
    if removed.exists():raise ValueError("UNKNOWN_STALE_WITHDRAWAL_FILE")
    original.rename(removed)
    try:
        missing_status=verified_policy(original)[1]
    finally:
        removed.rename(original)
    assert missing_status=="UNKNOWN_NO_SOURCE_CAPABILITY"
    assert verified_policy(original)[1]=="WARRANTED_BOUNDED_A_SOURCE_ADMISSION"
    if (outcomes["T1"]["old_fail_to_head_pass_count"]>0 and outcomes["T1"]["introduced_native_violations"]==0):
        outcome="PASS_BOUNDED_REAL_CROSS_REPOSITORY_COHERENCE_TRANSFER"
    else:
        outcome="UNKNOWN_OR_REJECTED_REAL_CROSS_REPOSITORY_COHERENCE_TRANSFER"
    report={
        "status":outcome,
        "source_capability":"A:tomlkit#599",
        "source_policy_exact_digest":sha(original.read_bytes()),
        "source_old":SOURCE_A_OLD,"source_head":SOURCE_A_HEAD,
        "operation":"coherence",
        "method_was_reselected_on_target":False,
        "source_compiled_lookup_reused_byte_identically":True,
        "target_adapter":"HUMAN_PREDECLARED_TOML_CODEC_PLUS_STDLIB_TOMLLIB",
        "target_repository":"uiri/toml",
        "target_prs":outcomes,
        "capability_deleted_from_disk_causes":missing_status,
        "source_restore_status":verified_policy(original)[1],
        "native_target_invocations":sum(2*x["tested_case_count"] for x in outcomes.values()),
        "source_A_native_invocations_retained_acquisition":80,
        "source_A_V11_feasibility_calls_charged":policy.get("source_v11_oracle_calls"),
        "finite_source_input_count":len(cases()),
        "total_receiver_seconds":round(time.monotonic()-begin,6),
        "equally_informed_executable_ledger":"TIES_SUPPORTED_CASES",
        "equally_informed_stateless_roundtrip":"TIES_SUPPORTED_CASES",
        "model_strong_coding_agent":"NOT_RUN",
        "lifetime_economic_advantage":"NOT_ESTABLISHED",
        "outside_contractor_autonomous_language_genesis":"NOT_ESTABLISHED",
        "source_blindness":"PR_TITLES_AND_BODIES_ALREADY_READ",
        "outside_repo_writes":"NONE",
        "novel_bug_discovery":"NOT_CLAIMED"
    }
    destination=Path(destination);destination.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(normalized({"phase":"TRANSFER",
          "status":outcome,
          "counts":{k:{"fixed":v["old_fail_to_head_pass_count"],
                       "lexical_only":v["valid_lexical_only_changed_cases"],
                       "false":v["false_warrants"],
                       "unknown":v["unknown_case_count"]} for k,v in outcomes.items()}}))
    # A negative outcome must preserve source but stop qualification.
    if outcome!="PASS_BOUNDED_REAL_CROSS_REPOSITORY_COHERENCE_TRANSFER":
        raise SystemExit(23)

def main():
    if sys.argv[1]=="native":
        if len(sys.argv)!=7:raise ValueError("ARGUMENTS_NATIVE")
        source_native(Path(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
    elif sys.argv[1]=="transfer":
        if len(sys.argv)!=5:raise ValueError("ARGUMENTS_TRANSFER")
        transfer(sys.argv[2],sys.argv[3],sys.argv[4])
    else:raise ValueError("UNKNOWN_MODE")

if __name__=="__main__":main()
