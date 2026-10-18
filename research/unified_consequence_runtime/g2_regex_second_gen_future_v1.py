#!/usr/bin/env python3
"""Source-distinct first-eligible native future test of unchanged regex operation.

The future cohort/order and acquired method are hash-frozen before any future
checkout. This driver never reads contributor-fixed production code.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import subprocess,sys,time,traceback
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_regex_language_boundary_v1 as acquired
from research.unified_consequence_runtime import g2_regex_equal_info_baseline_v1 as equalinfo
from research.unified_consequence_runtime import g2_context_fallback_operator_v1 as prior_context
from research.unified_consequence_runtime import g2_packaging_future_v1 as native_oracle
from research.unified_consequence_runtime import g2_werkzeug_train_v1 as guard

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
LOCK_COMMIT="7d9a8264173d0608e269e38a1ea68eaf79084de2"
METHOD_COMMIT="c1c07b60c2bc89e2f476bf9330856c3167fd2029"
EQUAL_INFO_COMMIT="4877c9e8c83b935317a891343ae9e603411ee90d"
POOL_COMMIT="d5327f0e72750a85f1a7a9cb0de6e82f608f572d"

def sha(b):return hashlib.sha256(b).hexdigest()
def show(c,p):return subprocess.check_output(["git","-C",str(ROOT),"show",c+":"+p],timeout=40)

def preflight():
    frozen=(ROOT/U/"G2_REGEX_BOUNDARY_SECOND_GEN_FUTURE_LOCK_V1.json").read_bytes()
    if frozen!=show(LOCK_COMMIT,U+"G2_REGEX_BOUNDARY_SECOND_GEN_FUTURE_LOCK_V1.json"):raise RuntimeError("LOCK_CHANGED")
    lock=json.loads(frozen)
    if (ROOT/U/"G2_GENESIS_V2_PACKAGING_TRAIN_FUTURE_POOL_PREQUERY.md").read_bytes()!=show(
        POOL_COMMIT,U+"G2_GENESIS_V2_PACKAGING_TRAIN_FUTURE_POOL_PREQUERY.md"):
        raise RuntimeError("POOL_PREQUERY_CHANGED")
    method=(ROOT/U/"g2_regex_language_boundary_v1.py").read_bytes()
    base=(ROOT/U/"g2_regex_equal_info_baseline_v1.py").read_bytes()
    if method!=show(METHOD_COMMIT,U+"g2_regex_language_boundary_v1.py"):raise RuntimeError("ACQUIRED_METHOD_CHANGED")
    if base!=show(EQUAL_INFO_COMMIT,U+"g2_regex_equal_info_baseline_v1.py"):raise RuntimeError("EQUAL_INFO_BASELINE_CHANGED")
    if sha(method)!=lock["frozen_method"]["sha256"]:raise RuntimeError("METHOD_SHA_MISMATCH")
    manifest,_=guard.manifest()
    rows=manifest["training_candidates"][1:]
    assert [(x["repo"]+"#"+str(x["pr"])) for x in rows]==lock["future"]["roles"]
    assert lock["future"]["unopened"] and lock["future"]["no_outcome_reselection"]
    acquired.self_test()
    equalinfo.self_test()
    return lock,rows

def protected_nodes_executed(row,dest):
    cases=list(ET.parse(dest/"native.xml").getroot().iter("testcase"))
    names=[t.attrib.get("name","").split("[",1)[0] for t in cases]
    nodes=row["protected_nodes"]
    return (bool(nodes) and len(cases)==row["native"]["counts"]["tests"]
            and all(x.rsplit("::",1)[-1] in names for x in nodes)
            and row["native"]["counts"]["skipped"]==0)

def prior_inventory(task,source,world):
    from research.unified_consequence_runtime import g2_anyio_mutable_closure_equivalence_fix_v2 as mutable
    from research.unified_consequence_runtime import attrs_residual_observation_genesis_v1 as projection
    a=mutable.scan_patterns(task["production"],source)
    ctx=prior_context.generate(source)
    result={"closure_patterns":len(a),"context_fallback_candidates":len(ctx),
            "attrs_projection":"UNKNOWN"}
    try:
        projection.derive_classifier_and_cases(world/task["author_test"])
        result["attrs_projection"]="APPLICABLE_BUT_NOT_NATIVE_VALIDATED"
    except Exception as ex:
        result["attrs_projection"]="NO_APPLICABLE_PATTERN"
        result["attrs_reason"]=type(ex).__name__+": "+str(ex)[:180]
    result["complete_no_candidates"]=(not a and not ctx and result["attrs_projection"]=="NO_APPLICABLE_PATTERN")
    return result,ctx

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    rep={"schema":"G2_REGEX_BOUNDARY_SOURCE_DISTINCT_FUTURE_V1",
         "G2":"UNKNOWN","status":"UNKNOWN_APPARATUS",
         "selected_future":"NONE","comparator":"NOT_EXECUTED",
         "Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
         "MathGraph":"EVIDENCE_PENDING"}
    start=time.monotonic()
    try:
        lock,pool=preflight()
        rep["frozen_method_sha256"]=lock["frozen_method"]["sha256"]
        rep["lock_commit"]=LOCK_COMMIT
        rep["selection_rule"]="FIRST_QUALIFIED_ORIGINAL_NATIVE_FAIL_IN_FROZEN_ORDER"
        rep["admissions"]=[]
        selected=None
        for i,task in enumerate(pool,start=1):
            row=native.one(task,i,out/("admission-"+str(i)))
            rep["admissions"].append({"repo":task["repo"],"pr":task["pr"],
                "status":row["status"],"source_sha256":row.get("source_sha256"),
                "native_counts":row.get("native",{}).get("counts"),
                "protected_nodes":row.get("protected_nodes"),
                "native_elapsed_seconds":row.get("native",{}).get("elapsed_seconds"),
                "provisioning":row.get("test_supplement")})
            if row["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
                continue
            if not protected_nodes_executed(row,out/("admission-"+str(i))):
                rep["admissions"][-1]["status"]="UNKNOWN_PARAMETRIC_PROTECTED_INTEGRITY"
                continue
            selected=(task,row)
            break
        if not selected:
            rep["status"]="UNKNOWN_NO_ADMISSIBLE_NEW_FUTURE"
            return rep
        task,row=selected
        rep["selected_future"]=task["repo"]+"#"+str(task["pr"])
        rep["selected_original_source_sha256"]=row["source_sha256"]
        rep["selected_original_native_counts"]=row["native"]["counts"]
        world=Path(row["work_dir"])
        py=Path(row["interpreter"])
        original=(world/task["production"]).read_bytes()
        if sha(original)!=row["source_sha256"]:
            raise RuntimeError("ORIGINAL_SOURCE_BYTES_CHANGED")
        if not guard.working_diff(world,task["production"],task["author_test"]):
            raise RuntimeError("SELECTED_WORKTREE_NOT_SOURCE_CLEAN")
        before, oldcontext=prior_inventory(task,original,world)
        rep["pre_acquisition"]=before
        # Old source-neutral context method has its own native arm when applicable.
        if oldcontext:
            rep["previous_context_native"]=native_oracle.test_one_arm(
                py,world,original,task,row["protected_nodes"],oldcontext,
                out,"old-context",row["native"]["counts"])
        begin=time.monotonic()
        baseline=equalinfo.generate(original)
        rep["equalinfo_generation_seconds"]=round(time.monotonic()-begin,5)
        begin=time.monotonic()
        generated=acquired.generate(original)
        rep["acquired_generation_seconds"]=round(time.monotonic()-begin,5)
        rep["equalinfo"]=native_oracle.test_one_arm(
            py,world,original,task,row["protected_nodes"],baseline,
            out,"equal-info-regex",row["native"]["counts"])
        rep["acquired"]=native_oracle.test_one_arm(
            py,world,original,task,row["protected_nodes"],generated,
            out,"acquired-regex",row["native"]["counts"])
        gain=rep["acquired"]["status"]=="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
        tie=rep["equalinfo"]["status"]=="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
        oldgain=rep.get("previous_context_native",{}).get("status")=="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
        rep["comparator"]="EQUAL_INFO_TIE" if tie and gain else "NO_NATIVE_BASELINE_GAIN" if gain and not tie else "NO_ACQUIRED_GAIN"
        rep["transfer_gain"]=gain
        rep["pre_acquisition_gain"]=oldgain
        if not generated:
            rep["status"]="REJECTED_NO_TRANSFER_CANDIDATE_ON_FIRST_FUTURE"
        elif not gain:
            rep["status"]="REJECTED_NO_NATIVE_TRANSFER_REPAIR"
        elif oldgain or not before["complete_no_candidates"]:
            rep["status"]="UNKNOWN_NO_CAUSAL_METHOD_DIFFERENCE"
        else:
            rep["status"]="CANDIDATE_BOUNDED_TRANSFER_PENDING_INDEPENDENT_CERTIFICATION"
        # The methods were written by the research harness, not autonomously learned.
        rep["autonomous_method_genesis"]="NOT_DEMONSTRATED"
        rep["G2"]="UNKNOWN"
        return rep
    except Exception as ex:
        rep["status"]="UNKNOWN_FUTURE_APPARATUS"
        rep["error"]=type(ex).__name__+": "+str(ex)[:800]
        rep["traceback"]=traceback.format_exc(limit=6)[-2100:]
        return rep
    finally:
        rep["wall_seconds"]=round(time.monotonic()-start,3)
        (out/"RESULT.json").write_text(json.dumps(rep,indent=2,sort_keys=True,default=str)+"\n")
        print("NEW_FUTURE_RESULT",json.dumps({k:rep.get(k) for k in
            ("status","G2","selected_future","comparator","transfer_gain","error")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: new_future_v1.py FRESH_OUT")
    main(Path(sys.argv[1]).resolve())
