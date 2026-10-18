#!/usr/bin/env python3
"""Frozen V2 compositional closure on *exposed training only*, not prospective G2.

All candidate primitives are from original V1 source-neutral regex generator.
An operator is accepted only after real source-native observed new consequences.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import difflib

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool
from research.unified_consequence_runtime import g2_regex_terminal_genesis_v1 as primitive
from research.unified_consequence_runtime import g2_werkzeug_guard_genesis_v1 as native

ROOT = Path(__file__).resolve().parents[2]
U = "research/unified_consequence_runtime/"
PROTOCOL_COMMIT = "90e4b817282f0d6a4c28f989d018b421aca66b68"
PRIMITIVE_COMMIT = "d45288833a13b1ddf6afde01c0b89a84bfc7ce32"
BASE = "737215ece92b530204c8ccd68b63c60943ce5a79"
HEAD = "3c4a07922fa3bd2f5fbcff8d73ddf7a0190c7b98"
SHA = "547eab1366fad5b7a452d957f3921b7fa1db14ef691a8d4a5760b269502fc63f"
MAX_NATIVE_CANDIDATE_TRIALS = 32
MAX_CONSTITUENTS = 4
TIME_BUDGET = 1250

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def freeze():
    proto=U+"G2_FINITE_REGEX_COMPOSITION_V2_FROZEN_PROTOCOL.md"
    p=subprocess.check_output(["git","-C",str(ROOT),"show",PROTOCOL_COMMIT+":"+proto],timeout=40)
    assert (ROOT/proto).read_bytes()==p, "PROTOCOL_CHANGED_AFTER_FREEZE"
    path=U+"g2_regex_terminal_genesis_v1.py"
    old=subprocess.check_output(["git","-C",str(ROOT),"show",PRIMITIVE_COMMIT+":"+path],timeout=40)
    assert old==(ROOT/path).read_bytes(), "PREVIOUSLY_ACQUIRED_PRIMITIVE_CHANGED"
    return {"repo":"mistralai/mistral-common","pr":380,"base":BASE,"head":HEAD,
            "production":"src/mistral_common/protocol/instruct/validator.py",
            "author_test":"tests/validation/test_validation.py"}

def prepare_candidates(source):
    """Guard against silent source-wide or duplicate-text replacements."""
    lines=source.splitlines(keepends=True)
    all_items=primitive.enumerate_candidates(source)
    items=[x for x in all_items if x["kind"]=="strict_terminal_anchor"]
    patches=[]
    for i,x in enumerate(items):
        pos=x["line"]-1
        assert 0<=pos<len(lines)
        old,new=x["old_expr"],x["new_expr"]
        assert old!=new and lines[pos].count(old)==1,"AMBIGUOUS_OR_MULTILINE_LITERAL"
        assert new.count(r"\Z") == old.count(r"\Z")+1
        assert old.endswith("$\"") or old.endswith("$'"),"NOT_TERMINAL_DOLLAR"
        changed=lines.copy()
        changed[pos]=changed[pos].replace(old,new,1)
        assert "".join(changed)==x["_edited"],"PRIMITIVE_NO_LONGER_EQUIVALENT"
        patches.append({"idx":i,"line":x["line"],"old":old,"new":new,
                        "candidate_sha256":x["candidate_sha256"],
                        "bytes_added":x["bytes_added"]})
    assert len(patches)<=16
    assert len({p["line"] for p in patches})==len(patches),"OVERLAPPING_LINES"
    return patches

def compose(source,items,subset):
    lines=source.splitlines(keepends=True)
    for index in sorted(subset):
        c=items[index];pos=c["line"]-1
        assert lines[pos].count(c["old"])==1
        lines[pos]=lines[pos].replace(c["old"],c["new"],1)
    s="".join(lines)
    compile(s,"<frozen-composed-source>","exec")
    return s.encode()

def verdicts(path):
    cases=list(ET.parse(path).getroot().iter("testcase"))
    statuses={}
    for node in cases:
        name=node.attrib.get("name")
        assert name and name not in statuses,"DUPLICATE_TEST_NAME"
        states={el.tag for el in node}
        statuses[name]=("ERROR" if "error" in states else
                        "FAIL" if "failure" in states else
                        "SKIP" if "skipped" in states else "PASS")
    return statuses

def test_one(py,work,protected,out,label):
    receipt=native.native(py,work,protected,label,out,140)
    names=verdicts(out/(label+".xml"))
    expected={p.split("::")[-1] for p in protected}
    assert set(names)==expected and len(names)==len(protected),"PROTECTED_SET_CHANGED"
    assert all(v in ("PASS","FAIL") for v in names.values()),"INCONCLUSIVE_NATIVE_TEST"
    counts=receipt["counts"]
    assert counts["tests"]==len(protected) and counts["errors"]==counts["skipped"]==0
    assert counts["failures"]==sum(v=="FAIL" for v in names.values())
    return receipt,names

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    r={"schema":"G2_COMPOSITION_MISTRAL_TRAIN_V2",
       "status":"UNKNOWN_APPARATUS","G2":"UNKNOWN",
       "future":"DEER_FLOW_SOURCE_SEALED_UNOPENED",
       "Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
       "training":{"repo":"mistralai/mistral-common","pr":380},
       "candidate_trials":[],"selected":[],"subsets":{}}
    start=time.monotonic()
    original=None;prod=None
    try:
        task=freeze()
        rec=pool.one(task,0,out/"original-admission")
        r["original_admission"]={k:v for k,v in rec.items() if k!="provisioning"}
        if rec["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            r["status"]="UNKNOWN_NATIVE_TRAINING_ADMISSION"
            return
        assert rec["source_sha256"]==SHA and rec["native"]["counts"]=={
            "tests":4,"failures":4,"errors":0,"skipped":0}
        work,py=Path(rec["work_dir"]),Path(rec["interpreter"])
        prod=work/task["production"]
        original=prod.read_bytes()
        assert digest(original)==SHA,"SOURCE_IDENTITY_CHANGED"
        source=original.decode()
        all_eligible=prepare_candidates(source)
        r["candidate_count"]=len(all_eligible)
        r["candidate_catalog"]=[{k:v for k,v in x.items() if k not in ("old","new")}
                                for x in all_eligible]
        if not all_eligible:
            r["status"]="REJECTED_PRIMITIVE_INAPPLICABLE"
            return
        failures=set(p.split("::")[-1] for p in rec["protected_nodes"])
        seen=set()
        selected=[]
        attempts=0
        for step in range(min(MAX_CONSTITUENTS,len(all_eligible))):
            if not failures:break
            proposals=[]
            for index,c in enumerate(all_eligible):
                if index in selected:continue
                if attempts>=MAX_NATIVE_CANDIDATE_TRIALS or time.monotonic()-start>TIME_BUDGET:
                    r["status"]="UNKNOWN_TRAINING_BUDGET"
                    return
                newset=selected+[index]
                candidate=compose(source,all_eligible,newset)
                prod.write_bytes(candidate)
                assert pool.git(work,"diff","--name-only").splitlines()==sorted(
                    [task["author_test"],task["production"]]),"UNAUTHORIZED_DIFF"
                prefix="search-step%02d-candidate%02d"%(step,index)
                receipt,verdict=test_one(py,work,rec["protected_nodes"],out,prefix)
                attempts+=1
                next_fail={key for key,v in verdict.items() if v=="FAIL"}
                trial={"step":step,"index":index,"trial_sha256":digest(candidate),
                       "counts":receipt["counts"],"receipt":receipt,
                       "remaining_failures":sorted(next_fail),
                       "native_vector":verdict,
                       "gain":len(failures-next_fail),
                       "regressions":sorted(next_fail-failures)}
                r["candidate_trials"].append(trial)
                if not next_fail-failures and len(next_fail)<len(failures):
                    proposals.append((trial["gain"],abs(len(candidate)-len(original)),index,next_fail))
                prod.write_bytes(original)
            if not proposals:
                r["status"]="REJECTED_NO_MONOTONE_GAINING_CONSTITUENT"
                return
            proposals.sort(key=lambda x:(-x[0],x[1],x[2]))
            best=proposals[0]
            selected.append(best[2])
            failures=best[3]
            r["selected"].append({"step":step,"index":best[2],
                                  "failures_remaining":sorted(failures),
                                  "composed_source_sha256":digest(compose(source,all_eligible,selected))})
        r["trial_count"]=attempts
        if failures:
            r["status"]="REJECTED_CLOSURE_INCOMPLETE"
            return
        k=len(selected)
        if k>4:
            r["status"]="UNKNOWN_SUBSET_BUDGET"
            return
        full=compose(source,all_eligible,selected)
        prod.write_bytes(full)
        r["full_source_sha256"]=digest(full)
        suite=native.native(py,work,[task["author_test"]],"full-author-suite",out,240)
        r["full_author_suite"]=suite
        sc=suite["counts"]
        if suite["exit"]!=0 or sc["tests"]<=len(rec["protected_nodes"]) or any(sc[key] for key in ("failures","errors","skipped")):
            r["status"]="REJECTED_FULL_AUTHOR_SUITE"
            return
        # Exact independent powerset replay. This is actual native evidence, not a simulated quotient.
        base_vector=None
        max_mask=(1<<k)-1
        for mask in range(1<<k):
            applied=[selected[j] for j in range(k) if mask&(1<<j)]
            raw=compose(source,all_eligible,applied)
            prod.write_bytes(raw)
            label="subset-%02d"%mask
            receipt,v=test_one(py,work,rec["protected_nodes"],out,label)
            r["subsets"][str(mask)]={
                "mask":mask,"applied_original_candidate_indices":applied,
                "source_sha256":digest(raw),"receipt":receipt,
                "verdicts":v,"passing":sorted(key for key,value in v.items() if value=="PASS")}
            if mask==0:base_vector=v
        assert base_vector and all(value=="FAIL" for value in base_vector.values())
        assert all(v=="PASS" for v in r["subsets"][str(max_mask)]["verdicts"].values())
        for left in range(1<<k):
            passed=set(r["subsets"][str(left)]["passing"])
            for right in range(1<<k):
                if left & right != left:continue
                assert passed.issubset(r["subsets"][str(right)]["passing"]), (
                    "MONOTONE_PASS_SET_FALSE",left,right)
        for j in range(k):
            withdrawn=max_mask^(1<<j)
            assert len(r["subsets"][str(withdrawn)]["passing"])<len(rec["protected_nodes"]),(
                "NON_CAUSAL_CONSTITUENT",j)
        # Full native reinstatement after removal; independent actual source hash assertion.
        prod.write_bytes(original)
        w,wd=test_one(py,work,rec["protected_nodes"],out,"physical-all-withdrawal")
        assert all(v=="FAIL" for v in wd.values())
        prod.write_bytes(full)
        p,pd=test_one(py,work,rec["protected_nodes"],out,"physical-all-restoration")
        assert all(v=="PASS" for v in pd.values())
        r["withdrawal"]=w;r["restoration"]=p
        r["total_native_executions"]=len(r["candidate_trials"])+(1<<k)+3
        patch="".join(difflib.unified_diff(source.splitlines(keepends=True),full.decode().splitlines(keepends=True),
                         fromfile="original/"+task["production"],tofile="generated/"+task["production"]))
        (out/"COMPOSED_GENERATED_PATCH.diff").write_text(patch)
        r["composed_patch_sha256"]=digest(patch.encode())
        r["status"]="CANDIDATE_FINITE_MONOTONE_COMPOSITION_AWAITING_INDEPENDENT_AUDIT"
    except Exception as exc:
        r["status"]="UNKNOWN_TRAINING_APPARATUS"
        r["error"]=type(exc).__name__+": "+str(exc)
    finally:
        if prod is not None and original is not None:
            prod.write_bytes(original)
        r["wall_seconds"]=round(time.monotonic()-start,3)
        r["G2"]="UNKNOWN"
        (out/"RESULT.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
        print(json.dumps({q:r.get(q) for q in ("status","candidate_count","trial_count",
              "total_native_executions","full_source_sha256","G2","Lean","CLC","FLASH")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_finite_composition_mistral_v2.py FRESH_OUTPUT")
    main(Path(sys.argv[1]).resolve())
