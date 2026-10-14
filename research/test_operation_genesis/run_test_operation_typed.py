#!/usr/bin/env python3
"""Typed original-Go test operation witness from generic AST selection.

Never invents an assertion or edits third-party implementation. The same
source-derived test selector is used for each repository. This classifier
separates test assertions, selected-test panics, missing test operations,
setup/compile errors, and timeouts. No authority to merge or deploy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import time

def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def rev(path):
    r=subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],
        text=True,capture_output=True,check=True,timeout=10)
    return r.stdout.strip()

def failure_type(test, events, rc):
    """Classify only an observed failing selected test, never a generic bad exit."""
    seq=[e for e in events if e.get("Test")==test and
        e.get("Action") in ("run","pass","fail","skip")]
    actions=[e["Action"] for e in seq]
    if rc is None:
        return "TIMEOUT_UNKNOWN"
    if "run" not in actions:
        return "TEST_NOT_EXECUTED_UNKNOWN"
    if rc==0 or "fail" not in actions:
        return "NOT_FAILED"
    captured=[str(e.get("Output","")) for e in events if e.get("Action")=="output"]
    whole="".join(captured)
    # A selected Go test that produces a native panic is evidence of an
    # executed program failure, not necessarily a test assertion.
    panic=bool(re.search(r"(?m)^\s*panic:\s+",whole)) and
        bool(re.search(r"\b"+re.escape(test)+r"\b",whole))
    if panic:
        return "NATIVE_PANIC_IN_SELECTED_TEST"
    # t.Error{f}, Fatal{f} and their nested subtests emit source locations.
    # Only attach output to this exact selected test or its named subtests.
    selected_outputs=[
        str(e.get("Output","")) for e in events
        if e.get("Action")=="output" and
        (e.get("Test")==test or str(e.get("Test","")).startswith(test+"/"))
    ]
    if any(re.search(r"\.go:\d+:",x) for x in selected_outputs):
        return "NATIVE_TEST_ASSERTION"
    return "UNKNOWN_UNCLASSIFIED_TEST_FAILURE"

def native_test(package, names, cwd):
    names=sorted(set(names))
    pattern="^("+"|".join(re.escape(n) for n in names)+")$"
    cmd=["go","test","-json","-count=1","-timeout=5m","-run",pattern,package]
    t0=time.perf_counter()
    try:
        proc=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,check=False,timeout=360)
    except subprocess.TimeoutExpired:
        return {"status":"TIMEOUT_UNKNOWN","exit":None,"selected":{n:[] for n in names},
                "failure_kinds":{n:"TIMEOUT_UNKNOWN" for n in names},
                "elapsed_s":round(time.perf_counter()-t0,3)}
    events=[]
    for line in proc.stdout.splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:continue
    selected={}
    for name in names:
        selected[name]=[e["Action"] for e in events
            if e.get("Test")==name and e.get("Action") in ("run","pass","fail","skip")]
    kinds={name:failure_type(name,events,proc.returncode) for name in names}
    failures={n for n,a in selected.items() if "run" in a and "fail" in a}
    # Do not put arbitrary full upstream logs into the public report. Keep
    # small bounded source-native context with no installation credentials.
    interesting=[
        str(e.get("Output","")).strip() for e in events if e.get("Action")=="output" and
        (re.search(r"panic:|\.go:\d+:|want:|got:|have:|mismatch",str(e.get("Output","")),re.I))]
    return {
        "status":"COMPLETE" if all("run" in a for a in selected.values())
            else "TEST_NOT_EXECUTED_UNKNOWN",
        "exit":proc.returncode,
        "selected":selected,
        "failure_kinds":kinds,
        "failure_excerpt":interesting[:18],
        "elapsed_s":round(time.perf_counter()-t0,3),
        "native_stdout_sha256":hashlib.sha256(proc.stdout.encode()).hexdigest(),
        "invocation":cmd,
        "stderr_tail":proc.stderr[-600:],
        "go_event_count":len(events),
        "observed_failing_tests":sorted(failures)
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=pathlib.Path,required=True)
    p.add_argument("--base",type=pathlib.Path,required=True)
    p.add_argument("--head",type=pathlib.Path,required=True)
    p.add_argument("--pristine",type=pathlib.Path)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--ablate",action="store_true")
    p.add_argument("--withdraw",action="store_true")
    a=p.parse_args()
    m=json.loads(a.manifest.read_text())
    require(m.get("schema")=="metalogic.original-go-source-test-operation-extraction.v1",
            "SOURCE_SELECTOR_MANIFEST_SCHEMA_WRONG")
    require(rev(a.base)==m["base_sha"] and rev(a.head)==m["head_sha"],
            "EXACT_ORIGINAL_SOURCE_SHA_MISMATCH")
    require(m.get("source_test_patch_only") is True and
        m.get("selector_implementation_authorship")=="HUMAN_WRITTEN_GENERIC_GO_AST",
        "AUTHOR_TEST_ONLY_PATCH_UNVERIFIED")
    selected=m.get("selected",[])
    require(selected and all(x.get("package") and x.get("function") for x in selected),
        "TEST_OPERATION_UNAVAILABLE")
    grouped={}
    for x in selected:
        grouped.setdefault(x["package"],[]).append(x["function"])
    records,ablation={},{}
    if a.ablate:
        require(a.pristine is not None and rev(a.pristine)==m["base_sha"],
            "UNTOUCHED_CAUSAL_BASE_MISSING")
        status=subprocess.run(["git","-C",str(a.pristine),"status","--porcelain"],
            text=True,capture_output=True,check=True)
        require(not status.stdout.strip(),"PRISTINE_SOURCE_WAS_MODIFIED")
        for pkg,names in sorted(grouped.items()):
            observed=native_test(pkg,names,a.pristine)
            ablation[pkg]=observed
            require(observed["status"]=="TEST_NOT_EXECUTED_UNKNOWN" and
                observed["exit"]==0 and
                all(not x for x in observed["selected"].values()),
                "ABLATION_DID_NOT_REMOVE_NATIVE_TEST")
        verdict="UNKNOWN_REQUIRED_TEST_OPERATION_REMOVED"
    elif a.withdraw:
        verdict="STALE_EVIDENCE_WITHDRAWN"
    else:
        for pkg,names in sorted(grouped.items()):
            records[pkg]={"base":native_test(pkg,names,a.base),
                          "head":native_test(pkg,names,a.head)}
        def qualifies(pkg, rec):
            base,head=rec["base"],rec["head"]
            native_kinds={"NATIVE_TEST_ASSERTION","NATIVE_PANIC_IN_SELECTED_TEST"}
            return (base["status"]=="COMPLETE" and head["status"]=="COMPLETE" and
                base["exit"]!=0 and head["exit"]==0 and
                all(base["failure_kinds"].get(n) in native_kinds for n in grouped[pkg]) and
                all("run" in head["selected"][n] and
                    "pass" in head["selected"][n] and
                    "fail" not in head["selected"][n] for n in grouped[pkg]))
        if all(qualifies(pkg,rec) for pkg,rec in records.items()):
            verdict="WARRANTED_BOUNDED_UPSTREAM_AUTHORED_NATIVE_FAILURE_TO_SUCCESS"
        elif any(rec["base"]["status"]!="COMPLETE" or rec["head"]["status"]!="COMPLETE"
                 for rec in records.values()):
            verdict="UNKNOWN_NATIVE_SETUP_OR_TEST_NOT_EXECUTED"
        else:
            verdict="NO_QUALIFIED_NATIVE_FAILURE_TO_SUCCESS"
    report={
        "schema":"metalogic.source-derived-go-native-typed-failure.v1",
        "repository":m["repo"],"original_base_sha":m["base_sha"],
        "original_contributor_head_sha":m["head_sha"],
        "selected_original_author_tests":selected,
        "result":verdict,"native":records,"physical_test_absence":ablation,
        "selection_algorithm":"IDENTICAL_PREQUALIFIED_GO_AST_TEST_DIFF",
        "failure_normalizer":"HUMAN_WRITTEN_GENERIC_TYPED_GO_TEST_EVENTS",
        "test_assertions_invented":"NO_ORIGINAL_CONTRIBUTOR_SUPPLIED",
        "action_authorization":"NONE",
        "fully_informed_baseline":{
            "same_original_author_tests_available":"YES",
            "can_run_same_native_before_after_tests":"YES",
            "measured_reviewer_time_or_cost_advantage":"NOT_MEASURED",
            "autonomous_method_invention":"NOT_ESTABLISHED"},
        "nonclaims":["Native panic is bounded observed process failure, not a correctness theorem",
            "Tests and code fixes belong to original upstream contributors",
            "No independent source-to-user-intent derivation or L7 algorithmic self-rewrite"]
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("GO_TYPED_SOURCE_GENESIS "+json.dumps({
        "repo":m["repo"],"result":verdict,
        "selected":[x["function"] for x in selected],
        "base_kinds":{p:r["base"]["failure_kinds"] for p,r in records.items()},
        "head_statuses":{p:r["head"]["selected"] for p,r in records.items()},
        "L7":"UNKNOWN","baseline_win":"NOT_PROVEN"},ensure_ascii=False))
    if a.ablate:
        require(verdict=="UNKNOWN_REQUIRED_TEST_OPERATION_REMOVED","FAIL_ABLATION")
    elif a.withdraw:
        require(verdict=="STALE_EVIDENCE_WITHDRAWN","FAIL_WITHDRAWAL")
    else:
        require(verdict=="WARRANTED_BOUNDED_UPSTREAM_AUTHORED_NATIVE_FAILURE_TO_SUCCESS",
                "CAUSAL_NATIVE_EVIDENCE_NOT_QUALIFIED")
if __name__=="__main__":
    main()
