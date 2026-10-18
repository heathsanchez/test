#!/usr/bin/env python3
"""Prospective source-distinct V2 finite composition test; never change learned grammar.

The method is imported verbatim from the independently qualified Mistral
training version. The only target-specific inputs are PRECOMMITTED source IDs.
This script must be Git-frozen before it is allowed to fetch the future.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as admission
from research.unified_consequence_runtime import g2_finite_composition_mistral_v2 as learned
from research.unified_consequence_runtime import g2_regex_terminal_genesis_v1 as primitive
from research.unified_consequence_runtime import g2_werkzeug_guard_genesis_v1 as native

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
FREEZE_PATH=U+"G2_FINITE_COMPOSITION_FUTURE_FREEZE_V1.json"
MAX_TRIALS=32
MAX_PARTS=4
WALL_LIMIT=1300

def checksum(raw):
    return hashlib.sha256(raw).hexdigest()

def original_at(commit,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",commit+":"+path],timeout=65)

def preflight(freeze_commit):
    raw=(ROOT/FREEZE_PATH).read_bytes()
    assert raw==original_at(freeze_commit,FREEZE_PATH),"FUTURE_ROLE_OR_METHOD_FREEZE_MUTATED"
    frozen=json.loads(raw)
    assert frozen["status"]=="SEALED_BEFORE_ANY_FUTURE_SOURCE_OR_TEST_ACCESS"
    for x in frozen["locked_files"]:
        assert (ROOT/x["path"]).read_bytes()==original_at(x["commit"],x["path"]),("METHOD_BYTES_CHANGED",x["path"])
    assert frozen["training"]["independent_audit_run"]==39162426039
    assert frozen["G2"]=="UNKNOWN"
    f=frozen["future"]
    assert f["repo"]=="bytedance/deer-flow" and f["pr"]==5960
    assert f["source_opened_at_freeze"] is False and f["author_test_opened_at_freeze"] is False
    return frozen

def case_vector(work,rec):
    path=Path(rec["work_dir"])/"__not_a_file__"
    del path
    actual=Path(rec["junit_path"]) if "junit_path" in rec else None
    if actual is None:
        return None
    return learned.verdicts(actual)

def native_trial(py,work,protected,out,label):
    r,v=learned.test_one(py,work,protected,out,label)
    return r,v

def single_primitive_control(source,candidates,work,py,task,protected,original_vector,out):
    # The historical learned grammar BEFORE finite composition: one source edit.
    # This is an unchanged method, not a strong fully-informed coding agent.
    prod=work/task["production"]
    original=prod.read_bytes()
    attempts=[]
    winner=None
    for index,c in enumerate(candidates[:MAX_TRIALS]):
        changed=learned.compose(source,candidates,[index])
        prod.write_bytes(changed)
        try:
            r,v=native_trial(py,work,protected,out,"single-%02d"%index)
            row={"candidate_index":index,"source_sha256":checksum(changed),
                 "native":r,"verdicts":v}
            attempts.append(row)
            if all(x=="PASS" for x in v.values()):
                suite=native.native(py,work,[task["author_test"]],
                                    "single-%02d-full"%index,out,240)
                row["full_author"]=suite
                cts=suite["counts"]
                if suite["exit"]==0 and cts["tests"]>len(v) and not any(cts[k] for k in ("failures","errors","skipped")):
                    winner=index
                    break
        finally:
            prod.write_bytes(original)
    return {"status":"NATIVE_PASS" if winner is not None else "NO_NATIVE_SINGLE_OPERATOR_REPAIR",
            "candidate_count":len(candidates),"attempted":len(attempts),
            "winner":winner,"trials":attempts,"matched_original_obligation":sorted(original_vector)}

def frozen_fullmatch_control_candidates(source):
    """Pre-existing V1 .match→.fullmatch grammar with identical composition budget.

    The alternate operation is declared before future exposure, not a
    method adapted after inspecting a protected result.
    """
    lines=source.splitlines(keepends=True)
    out=[]
    for v in primitive.enumerate_candidates(source):
        if v["kind"]!="whole_input_match":
            continue
        pos=v["line"]-1
        if not 0<=pos<len(lines) or lines[pos].count(v["old_expr"])!=1:
            continue
        replacement=lines.copy()
        replacement[pos]=replacement[pos].replace(v["old_expr"],v["new_expr"],1)
        if "".join(replacement)!=v["_edited"]:
            continue
        out.append({"idx":len(out),"line":v["line"],"old":v["old_expr"],
                    "new":v["new_expr"],"candidate_sha256":v["candidate_sha256"],
                    "bytes_added":v["bytes_added"]})
        if len(out)>=16:
            break
    return out

def finite_compose(source,candidates,work,py,task,protected,old_vector,out):
    # Byte-identical Mistral V2 prepare_candidates/compose/test_one functions:
    # strict improvement, no regression, finite ranked search and ≤4 parts.
    prod=work/task["production"]
    original=prod.read_bytes()
    selected=[]
    remaining={k for k,v in old_vector.items() if v=="FAIL"}
    initial_pass={k for k,v in old_vector.items() if v=="PASS"}
    trials=[]
    elapsed_start=time.monotonic()
    status="REJECTED_COMPOSITION_NO_MONOTONE_IMPROVEMENT"
    for step in range(min(MAX_PARTS,len(candidates))):
        if not remaining:
            break
        proposals=[]
        for index in range(len(candidates)):
            if index in selected:
                continue
            if len(trials)>=MAX_TRIALS or time.monotonic()-elapsed_start>WALL_LIMIT:
                return {"status":"UNKNOWN_NATIVE_BUDGET","trials":trials,"selected":selected}
            joined=selected+[index]
            edited=learned.compose(source,candidates,joined)
            prod.write_bytes(edited)
            try:
                r,v=native_trial(py,work,protected,out,"compound-%02d-candidate-%02d"%(step,index))
                new_fail={k for k,w in v.items() if w=="FAIL"}
                trial={"step":step,"index":index,"native":r,"verdicts":v,
                       "source_sha256":checksum(edited),"new_failures":sorted(new_fail)}
                trials.append(trial)
                if not (new_fail-remaining) and len(new_fail)<len(remaining) and initial_pass.issubset(
                        {k for k,w in v.items() if w=="PASS"}):
                    proposals.append((len(remaining-new_fail),abs(len(edited)-len(original)),index,new_fail))
            finally:
                prod.write_bytes(original)
        if not proposals:
            return {"status":status,"trials":trials,"selected":selected}
        proposals.sort(key=lambda v:(-v[0],v[1],v[2]))
        choice=proposals[0]
        selected.append(choice[2])
        remaining=choice[3]
        status="REJECTED_COMPOSITION_INCOMPLETE"
    if remaining or not selected:
        return {"status":status,"trials":trials,"selected":selected}
    k=len(selected)
    assert k<=4
    full=learned.compose(source,candidates,selected)
    prod.write_bytes(full)
    try:
        repeat1,rv1=native_trial(py,work,protected,out,"compound-complete-repeat-a")
        repeat2,rv2=native_trial(py,work,protected,out,"compound-complete-repeat-b")
        if not all(x=="PASS" for x in rv1.values()) or rv1!=rv2:
            return {"status":"REJECTED_COMPOSITION_REPEATED_PROTECTED","trials":trials,"selected":selected}
        suite=native.native(py,work,[task["author_test"]],"compound-full-author",out,240)
        sc=suite["counts"]
        if suite["exit"]!=0 or sc["tests"]<=len(rv1) or any(sc[q] for q in ("failures","errors","skipped")):
            return {"status":"REJECTED_COMPOSITION_FULL_AUTHOR","trials":trials,"selected":selected,"full_author":suite}
        subsets={}
        for mask in range(1<<k):
            subset=[selected[i] for i in range(k) if mask&(1<<i)]
            prod.write_bytes(learned.compose(source,candidates,subset))
            r,v=native_trial(py,work,protected,out,"compound-subset-%02d"%mask)
            subsets[str(mask)]={"mask":mask,"original_indices":subset,
                                "source_sha256":checksum(prod.read_bytes()),"native":r,"verdicts":v}
        assert subsets["0"]["verdicts"]==old_vector,"BASELINE_NOT_RESTORED"
        assert all(q=="PASS" for q in subsets[str((1<<k)-1)]["verdicts"].values())
        for x in range(1<<k):
            passed={n for n,w in subsets[str(x)]["verdicts"].items() if w=="PASS"}
            for y in range(1<<k):
                if x & y == x:
                    assert passed.issubset({n for n,w in subsets[str(y)]["verdicts"].items() if w=="PASS"}),"NONMONOTONE"
        for i in range(k):
            ablate=((1<<k)-1)^(1<<i)
            assert any(q=="FAIL" for q in subsets[str(ablate)]["verdicts"].values()),"PART_NOT_CAUSALLY_NECESSARY"
        prod.write_bytes(original)
        withdrawal,withdrawn=native_trial(py,work,protected,out,"compound-physical-withdrawal")
        assert withdrawn==old_vector,"WITHDRAWAL_DID_NOT_RESTORE_EXACT_FAILURE"
        prod.write_bytes(full)
        restore,restored=native_trial(py,work,protected,out,"compound-physical-restoration")
        assert all(q=="PASS" for q in restored.values()),"RESTORATION_FAILED"
        return {"status":"CANDIDATE_CAUSAL_CROSS_SOURCE_FINITE_COMPOSITION",
                "selected":selected,"candidate_count":len(candidates),
                "trials":trials,"full_source_sha256":checksum(full),
                "protected_passed_twice":[repeat1,repeat2],"full_author":suite,
                "subsets":subsets,"withdrawal":withdrawal,"restoration":restore}
    finally:
        prod.write_bytes(original)

def main(out,freeze_commit):
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"G2_FINITE_COMPOSITION_SOURCE_DISTINCT_FUTURE_V1",
            "status":"UNKNOWN_PROSPECTIVE_APPARATUS","G2":"UNKNOWN",
            "future_opened":False,"future_causal_gain_verified":False,
            "Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
            "strong_coding_agent":"NOT_EXECUTED","fully_informed_ledger":"NOT_EXECUTED"}
    prod=None
    original=None
    st=time.monotonic()
    try:
        freeze=preflight(freeze_commit)
        report["freeze_commit"]=freeze_commit
        report["training_audit_run"]=freeze["training"]["independent_audit_run"]
        future=freeze["future"]
        task={k:future[k] for k in ("repo","pr","base","head","production","author_test")}
        report["future_opened"]=True
        original_rec=admission.one(task,0,out/"original-author-admission")
        report["original_native_admission"]={k:v for k,v in original_rec.items() if k not in ("provisioning",)}
        if original_rec["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"]="UNKNOWN_FUTURE_NOT_ADMITTED_"+original_rec["status"]
            return
        counts=original_rec["native"]["counts"]
        if (counts["errors"] or counts["skipped"] or counts["tests"]==0
              or counts["failures"]==0 or counts["tests"]!=len(original_rec["protected_nodes"])):
            report["status"]="UNKNOWN_FUTURE_PROTECTED_CASE_MAPPING"
            return
        work=Path(original_rec["work_dir"])
        py=Path(original_rec["interpreter"])
        prod=work/task["production"]
        original=prod.read_bytes()
        assert checksum(original)==original_rec["source_sha256"]
        assert admission.git(work,"diff","--name-only").splitlines()==[task["author_test"]]
        source=original.decode("utf-8")
        baseline_xml=out/"original-author-admission/native.xml"
        original_vector=learned.verdicts(baseline_xml)
        expected={q.split("::")[-1] for q in original_rec["protected_nodes"]}
        if set(original_vector)!=expected or not all(q in ("FAIL","PASS") for q in original_vector.values()):
            report["status"]="UNKNOWN_FUTURE_ORIGINAL_PROTECTED_MAPPING"
            return
        report["protected_case_vector_before"]=original_vector
        catalog=learned.prepare_candidates(source)
        report["qualified_finite_grammar_candidate_count"]=len(catalog)
        report["candidate_catalog"]=[{k:v for k,v in x.items() if k not in ("old","new")} for x in catalog]
        if not catalog:
            report["status"]="REJECTED_UNCHANGED_COMPOSITION_INAPPLICABLE"
            report["unchanged_single_primitive"]="NOT_EXECUTED_NO_OPERATOR"
            report["matched_fullmatch_composition"]="NOT_EXECUTED_ACQUIRED_METHOD_INAPPLICABLE"
            return
        comparator=frozen_fullmatch_control_candidates(source)
        report["matched_fullmatch_candidate_count"]=len(comparator)
        report["matched_fullmatch_composition"]=(finite_compose(
            source,comparator,work,py,task,original_rec["protected_nodes"],original_vector,out)
            if comparator else {"status":"NO_FROZEN_FULLMATCH_CANDIDATES"})
        report["unchanged_single_primitive"]=single_primitive_control(
            source,catalog,work,py,task,original_rec["protected_nodes"],original_vector,out)
        report["new_composition"]=finite_compose(
            source,catalog,work,py,task,original_rec["protected_nodes"],original_vector,out)
        result=report["new_composition"]
        if result["status"]=="CANDIDATE_CAUSAL_CROSS_SOURCE_FINITE_COMPOSITION":
            matched=report["matched_fullmatch_composition"].get("status")
            report["status"]=("CANDIDATE_TRANSFER_TIES_PRIOR_GRAMMAR" if
                    report["unchanged_single_primitive"]["winner"] is not None
                    or matched=="CANDIDATE_CAUSAL_CROSS_SOURCE_FINITE_COMPOSITION"
                    else "CANDIDATE_SOURCE_DISTINCT_CAUSAL_GAIN_AWAITING_INDEPENDENT_AUDIT")
            report["future_causal_gain_verified"]=False
        else:
            report["status"]=result["status"]
        assert prod.read_bytes()==original
        assert admission.git(work,"diff","--name-only").splitlines()==[task["author_test"]]
    except Exception as err:
        report["status"]="UNKNOWN_FUTURE_APPARATUS"
        report["error"]=type(err).__name__+": "+str(err)[:950]
    finally:
        if prod is not None and original is not None:
            prod.write_bytes(original)
        report["G2"]="UNKNOWN"
        report["wall_seconds"]=round(time.monotonic()-st,3)
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print(json.dumps({k:report.get(k) for k in
              ("status","G2","future_opened","qualified_finite_grammar_candidate_count","Lean","CLC","FLASH")},sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: g2_finite_composition_future_v1.py FRESH_OUTPUT FREEZE_COMMIT")
    main(Path(sys.argv[1]).resolve(),sys.argv[2])
