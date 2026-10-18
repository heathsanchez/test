#!/usr/bin/env python3
"""Prospective, source-distinct future test of *unchanged* acquired operation.

The separate Packaging source may be opened ONLY because training qualification
and method/comparator freeze at commit 5446c27f predate this code/execution.
No method or selector adaptations may be made after seeing future source.
"""
from __future__ import annotations
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool
from research.unified_consequence_runtime import g2_werkzeug_guard_genesis_v1 as acquired
from research.unified_consequence_runtime import g2_cross_source_matched_baseline_v1 as comparison

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
FREEZE_COMMIT="5446c27f88d0cfd71beb6d30561668b752a710c5"
ROLE_COMMIT="57c400ea49881e440f7895acaeebeee5854363e3"
MAX_SEARCH_SECONDS_PER_ARM=690

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git_bytes(rev,rel):
    return subprocess.check_output(["git","-C",str(ROOT),"show",rev+":"+rel],timeout=40)

def ensure_prior_method_freeze():
    rel=U+"G2_WERKZEUG_ACQUIRED_OPERATOR_PRE_FUTURE_FREEZE_V1.json"
    b=(ROOT/rel).read_bytes()
    assert git_bytes(FREEZE_COMMIT,rel)==b,"FREEZE_MANIFEST_CHANGED"
    freeze=json.loads(b)
    assert freeze["state"]=="WARRANTED_BOUNDED_TRAINING_OPERATOR_FROZEN_BEFORE_FUTURE_SOURCE"
    assert freeze["G2"]=="UNKNOWN"
    operator=freeze["acquired_operator"]
    assert operator["callable"]=="enumerate_candidates"
    assert operator["frozen_git_commit"]=="216f960c18fd8a5d1e3f78a5c811333153802e0c"
    assert git_bytes(operator["frozen_git_commit"],operator["path"])==(ROOT/operator["path"]).read_bytes()
    baseline=freeze["comparators"][1]
    assert baseline["name"]=="drop_context_guard_v1"
    assert git_bytes(baseline["frozen_git_commit"],baseline["path"])==(ROOT/baseline["path"]).read_bytes()
    p=U+"G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
    manifest=json.loads(git_bytes(ROLE_COMMIT,p))
    assert (ROOT/p).read_bytes()==git_bytes(ROLE_COMMIT,p)
    assert len(manifest["sealed_futures"])==1
    task=manifest["sealed_futures"][0]
    assert task["repo"]==freeze["future"]["repo"] and task["pr"]==freeze["future"]["pr"]
    return task,freeze

def run_native(py,work,nodes,name,out,seconds=160):
    junit=out/(name+".xml")
    args=[str(py),"-m","pytest","-q","--junitxml="+str(junit),*nodes]
    st=time.monotonic()
    try:
        p=subprocess.run(args,cwd=work,capture_output=True,text=True,timeout=seconds,
                         env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        exitcode,stdout,stderr=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as e:
        exitcode,stdout,stderr=124,(e.stdout or b"").decode(errors="replace") if isinstance(e.stdout,bytes) else (e.stdout or ""),"TIMEOUT"
    log=out/(name+".log")
    log.write_text(json.dumps({"argv":args,"returncode":exitcode,"stdout":stdout,"stderr":stderr},indent=2)+"\n")
    c=pool.junit(junit)
    return {"returncode":exitcode,"counts":c,"elapsed_seconds":round(time.monotonic()-st,3),
            "junit_sha256":sha(junit.read_bytes()) if junit.exists() else None,
            "log_sha256":sha(log.read_bytes())}

def original_fails(native):
    c=native["counts"]
    return native["returncode"]==1 and c["tests"]>0 and c["failures"]>=1 and c["errors"]==c["skipped"]==0

def qualifies_protected(after,before):
    a,b=after["counts"],before["counts"]
    return after["returncode"]==0 and a["tests"]==b["tests"] and a["tests"]>0 and all(a[k]==0 for k in ("failures","errors","skipped"))

def status_allowed(work,task,with_patch):
    names=pool.git(work,"diff","--name-only").splitlines()
    expected=sorted([task["author_test"]]+([task["production"]] if with_patch else []))
    return names==expected

def trial_arm(label,items,source,original,work,py,task,protected,base,out):
    prod=work/task["production"]
    rows=[]
    started=time.monotonic()
    winner=None
    for i,v in enumerate(items):
        if time.monotonic()-started>MAX_SEARCH_SECONDS_PER_ARM:
            return {"status":"UNKNOWN_ARM_BUDGET","candidate_count":len(items),
                    "trials":rows,"wall_seconds":round(time.monotonic()-started,3)}
        patch=v["_edited"].encode("utf-8")
        assert prod.read_bytes()==original,"CANDIDATE_NOT_APPLIED_TO_ORIGINAL"
        prod.write_bytes(patch)
        assert status_allowed(work,task,True),"OUTSIDE_SINGLE_SOURCE_PATCH"
        row={"index":i,"predicate_line":v["if_line"],"candidate_sha256":sha(patch)}
        rows.append(row)
        ident="%s-%02d"%(label,i)
        row["native"]=run_native(py,work,protected,ident+"-protected",out,160)
        if not qualifies_protected(row["native"],base):
            prod.write_bytes(original)
            continue
        row["author_suite"]=run_native(py,work,[task["author_test"]],ident+"-author-suite",out,240)
        cs=row["author_suite"]["counts"]
        if (row["author_suite"]["returncode"]!=0 or cs["tests"]<=base["counts"]["tests"]
            or cs["failures"]!=0 or cs["errors"]!=0):
            prod.write_bytes(original)
            continue
        prod.write_bytes(original)
        row["withdrawal"]=run_native(py,work,protected,ident+"-withdrawal",out,160)
        if not (original_fails(row["withdrawal"])
                and row["withdrawal"]["counts"]==base["counts"]):
            return {"status":"UNKNOWN_CAUSAL_WITHDRAWAL_MISMATCH",
                    "candidate_count":len(items),"trials":rows}
        prod.write_bytes(patch)
        row["restoration"]=run_native(py,work,protected,ident+"-restoration",out,160)
        if not qualifies_protected(row["restoration"],base):
            return {"status":"UNKNOWN_CAUSAL_RESTORATION_MISMATCH",
                    "candidate_count":len(items),"trials":rows}
        diff="".join(difflib.unified_diff(
            source.splitlines(keepends=True),v["_edited"].splitlines(keepends=True),
            fromfile="original/"+task["production"],tofile="generated/"+task["production"]
        ))
        (out/(label+"-generated.patch")).write_text(diff)
        winner={"index":i,"source_sha256":sha(patch),
                "patch_sha256":sha(diff.encode()),"author_suite_passes":cs["tests"],
                "causal_withdrawal_restoration":True}
        prod.write_bytes(original)
        break
    assert prod.read_bytes()==original and status_allowed(work,task,False),"WORKTREE_NOT_RESTORED"
    return {"status":"CANDIDATE_NATIVE_REPAIR" if winner else "REJECTED_NO_QUALIFIED_CANDIDATE",
            "candidate_count":len(items),"trials":rows,"winner":winner,
            "wall_seconds":round(time.monotonic()-started,3)}

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    r={"schema":"G2_CROSS_SOURCE_FUTURE_UNCHANGED_OPERATOR_V1",
       "status":"UNKNOWN_ENVIRONMENT","future_opened":False,
       "method_changed_after_future":False,
       "G2":"UNKNOWN","G3":"UNKNOWN","Lean":"NOT_EXECUTED",
       "CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED","future_native_test_replayed":False}
    began=time.monotonic()
    try:
        task,freeze=ensure_prior_method_freeze()
        r.update({"future_repo":task["repo"],"future_pr":task["pr"],
                  "acquired_training_run":freeze["training"]["original_native_run"],
                  "method_freeze_commit":FREEZE_COMMIT,
                  "method_git_blob":freeze["acquired_operator"]["frozen_git_blob"],
                  "baseline_git_blob":freeze["comparators"][1]["frozen_git_blob"]})
        # Native admission reuses the exact precommitted, independent eligibility rule.
        r["future_opened"]=True
        admitted=pool.one(task,0,out/"original-admission")
        r["original_future"]={k:v for k,v in admitted.items() if k not in ("provisioning",)}
        if admitted["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            r["status"]="UNKNOWN_FUTURE_NOT_ADMITTED_"+admitted["status"]
            return
        n=admitted["native"]
        if not original_fails(n):
            r["status"]="UNKNOWN_FUTURE_NO_AUTHENTIC_PROTECTED_FAILURE"
            return
        work,py=Path(admitted["work_dir"]),Path(admitted["interpreter"])
        protected=admitted["protected_nodes"]
        if n["counts"]["tests"]<len(protected):
            r["status"]="UNKNOWN_INCOMPLETE_PROTECTED_ORIGINAL"
            return
        prod=work/task["production"]
        source_bytes=prod.read_bytes()
        assert sha(source_bytes)==admitted["source_sha256"],"FUTURE_SOURCE_HASH_CHANGED"
        source=source_bytes.decode("utf-8")
        assert status_allowed(work,task,False),"FUTURE_BASELINE_DIRTY"
        r["protected_nodes"]=protected
        r["original_source_sha256"]=sha(source_bytes)
        # All frozen arms see IDENTICAL source, tests, native obligations and time budget.
        old= comparison.enumerate_candidates(source)
        new= acquired.enumerate_candidates(source)
        r["baseline_candidate_count"]=len(old)
        r["acquired_candidate_count"]=len(new)
        r["baseline"]=trial_arm("matched-baseline",old,source,source_bytes,work,py,task,protected,n,out)
        if r["baseline"]["status"].startswith("UNKNOWN"):
            r["status"]="UNKNOWN_BASELINE_APPARATUS"
            return
        r["acquired"]=trial_arm("acquired-method",new,source,source_bytes,work,py,task,protected,n,out)
        if r["acquired"]["status"].startswith("UNKNOWN"):
            r["status"]="UNKNOWN_ACQUIRED_METHOD_APPARATUS"
            return
        r["future_native_test_replayed"]=True
        if r["acquired"]["winner"] is None:
            r["status"]=("REJECTED_PROSPECTIVE_METHOD_INAPPLICABLE"
                         if len(new)==0 else "REJECTED_PROSPECTIVE_METHOD_NATIVE")
        elif r["baseline"]["winner"] is not None:
            r["status"]="CANDIDATE_TRANSFER_TIED_INFORMED_BASELINE_NOT_ADVANTAGE"
        else:
            r["status"]="CANDIDATE_PROSPECTIVE_NATIVE_GAIN_AWAITING_INDEPENDENT_AUDIT"
        assert status_allowed(work,task,False) and prod.read_bytes()==source_bytes
    except Exception as e:
        r["status"]="UNKNOWN_FUTURE_APPARATUS"
        r["error"]=type(e).__name__+": "+str(e)
    finally:
        r["wall_seconds"]=round(time.monotonic()-began,3)
        (out/"RESULT.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:r.get(k) for k in ("status","G2","future_repo",
              "future_opened","acquired_candidate_count","baseline_candidate_count",
              "Lean","CLC","FLASH")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_cross_source_future_probe_v1.py FRESH_OUTPUT")
    main(Path(sys.argv[1]).resolve())
