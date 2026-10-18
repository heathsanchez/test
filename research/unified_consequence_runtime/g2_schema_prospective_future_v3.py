#!/usr/bin/env python3
"""Second prospectively sealed native future: byte-identical Packaging-acquired
whole-string generator against schedule original. Never adapts to future outcomes.
"""
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys,traceback
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_cross_source_train_v1 as oracle
from research.unified_consequence_runtime import g2_whole_input_regex_syntax_v2 as acquired
from research.unified_consequence_runtime import g2_unittest_ast_admission_v3 as admission_v3
from research.unified_consequence_runtime import g2_packaging_boundary_genesis_v1 as original_inventory

ROOT=pathlib.Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
RECEIPT=U+"G2_SCHEDULE_V3_QUALIFIED_CROSS_SOURCE_TRAINING_RECEIPT.json"
RECEIPT_FREEZE="ba39e2948dc114f1ae8bcbd0619b1419c50af4ec"
ROLE_PRECOMMIT="0e6e8bc2ec313c38370710b82378f072f5891cbd"
METHOD_SHA="12353d3b30f33aa98a6edf5623e1d92ba442ca2f0750e7f3f48aae930ebbc788"


def sha(b):return hashlib.sha256(b).hexdigest()
def fixed():
    assert (ROOT/RECEIPT).read_bytes()==subprocess.check_output(
        ["git","-C",str(ROOT),"show",RECEIPT_FREEZE+":"+RECEIPT])
    r=json.loads((ROOT/RECEIPT).read_text())
    assert r["status"]=="WARRANTED_BOUNDED_MATCHED_SOURCE_DISTINCT_TRAINING_REUSE_ONLY"
    assert r["next_sealed_future"]["source_not_opened"] is True and r["G2"]=="UNKNOWN"
    assert r["experiment_protocol"]==ROLE_PRECOMMIT
    assert sha((ROOT/r["method_path"]).read_bytes())==r["method_sha256"]==METHOD_SHA
    assert sha((ROOT/r["admission_path"]).read_bytes())==r["admission_sha256"]
    future=dict(r["next_sealed_future"])
    assert future["repo"]=="keleshev/schema" and future["pr"]==356
    assert future["repo"] != r["observed_training_source"]
    assert acquired.controls()
    assert admission_v3.controls()
    admission_v3.install()
    return future,r

def same_case_ids(a,b):
    if a["counts"]["tests"]!=b["counts"]["tests"]:return False
    def names(x):return sorted((y["class"],y["name"]) for y in x.get("cases",[]))
    return len(names(a))>0 and names(a)==names(b)
def passes(r,original):
    c=r["counts"]
    return (r["returncode"]==0 and c["failures"]==c["errors"]==c["skipped"]==0
            and same_case_ids(r,original))
def failure(r):
    c=r["counts"]
    return r["returncode"]==1 and c["tests"]>0 and c["failures"]>=1 and c["errors"]==c["skipped"]==0

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"G2_PACKAGING_SCHEDULE_TO_SCHEMA_FUTURE_V3","status":"UNKNOWN_FUTURE_APPARATUS",
            "trained_method_sha256":METHOD_SHA,"G2":"UNKNOWN",
            "old_inventory_comparator":"V1_SAME_SOURCE_PATTERN_INVENTORY","strong_agent_comparator":"NOT_RUN",
            "lean_clc_flash":"NOT_RUN","no_method_rewriting":True, "future":"SCHEMA_OPENED_PROSPECTIVELY","science":"PROSPECTIVE_NATIVE_SOURCE_TRANSFER"}
    try:
        future,receipt=fixed()
        report.update(future_repo=future["repo"],future_pr=future["pr"],
                      training_artifact_sha256=receipt["artifact_sha256"])
        adm=native.one(future,0,out/"original-admission")
        report["admission"]=adm
        if adm["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"]="UNKNOWN_FUTURE_NATIVE_NOT_ADMITTED"
            return
        if adm["native"]["counts"]["skipped"] or adm["native"]["counts"]["errors"]:
            report["status"]="UNKNOWN_FUTURE_NATIVE_SKIPS_OR_ERRORS"
            return
        world=pathlib.Path(adm["work_dir"])
        path=world/future["production"]
        original=path.read_bytes()
        assert sha(original)==adm["source_sha256"]
        assert oracle.run_git(world,"rev-parse","HEAD")==future["base"]
        assert oracle.run_git(world,"diff","--name-only").splitlines()==[future["author_test"]]
        py=pathlib.Path(adm["interpreter"])
        protected=adm["protected_nodes"]
        # Check the exact emitted testcase identities independently.
        baseline=oracle.run_test(py,world,protected,out/"baseline-repeat",timeout=150)
        report["baseline"]=baseline
        if not failure(baseline):
            report["status"]="UNKNOWN_ORIGINAL_NATIVE_NONREPRODUCED"
            return
        report["prior_v1_candidate_count"]=len(original_inventory.enumerate_candidates(original))
        candidates=acquired.enumerate_candidates(original)
        report["candidate_count"]=len(candidates)
        report["enumeration"]=[{k:v for k,v in o.items() if k!="source"} for o in candidates]
        if not candidates:
            report["status"]="REJECTED_SCHEMA_FUTURE_METHOD_INAPPLICABLE"
            return
        for index,op in enumerate(candidates):
            dest=out/("candidate-"+str(index).zfill(2))
            try:
                path.write_bytes(op["source"])
                assert sorted(oracle.run_git(world,"diff","--name-only").splitlines())==sorted(
                    [future["author_test"],future["production"]])
                a=oracle.run_test(py,world,protected,dest/"protected-a",timeout=150)
                trial={"index":index,"family":op["family"],"source_sha256":op["source_sha256"],
                       "protected_a":a,"status":"REJECTED_PROTECTED"}
                report.setdefault("trials",[]).append(trial)
                if not passes(a,baseline):continue
                full=oracle.run_test(py,world,[future["author_test"]],dest/"full-author",timeout=200)
                trial["full_author"]=full
                if not oracle.native_pass(full):
                    trial["status"]="REJECTED_AUTHOR_REGRESSION"
                    continue
                b=oracle.run_test(py,world,protected,dest/"protected-b",timeout=150)
                trial["protected_b"]=b
                if not passes(b,baseline):
                    trial["status"]="REJECTED_REPEAT"
                    continue
                path.write_bytes(original)
                withdrawn=oracle.run_test(py,world,protected,dest/"withdrawal",timeout=150)
                trial["withdrawal"]=withdrawn
                if not failure(withdrawn) or not same_case_ids(withdrawn,baseline):
                    trial["status"]="UNKNOWN_WITHDRAWAL_NOT_REPRODUCED"
                    continue
                path.write_bytes(op["source"])
                restore=oracle.run_test(py,world,protected,dest/"restoration",timeout=150)
                trial["restoration"]=restore
                if not passes(restore,baseline) or sha(path.read_bytes())!=op["source_sha256"]:
                    trial["status"]="UNKNOWN_RESTORATION_NOT_REPRODUCED"
                    continue
                trial["status"]="CANDIDATE_SOURCE_DISTINCT_SCHEMA_TRANSFER_NEEDS_COMPARATOR_AND_FORMAL"
                report["status"]=trial["status"]
                report["acquired_operator"]={k:v for k,v in op.items() if k!="source"}
                (dest/"candidate_source.py").write_bytes(op["source"])
                break
            finally:
                path.write_bytes(original)
                assert sha(path.read_bytes())==adm["source_sha256"]
                assert oracle.run_git(world,"diff","--name-only").splitlines()==[future["author_test"]]
        else:
            report["status"]="REJECTED_SCHEMA_FUTURE_NATIVE_REPAIR"
    except Exception as e:
        report["status"]="UNKNOWN_FUTURE_APPARATUS"
        report["error"]=type(e).__name__+": "+str(e)[:850]
        report["traceback_tail"]=traceback.format_exc(limit=8)[-1800:]
    finally:
        report["G2"]="UNKNOWN"
        report["future"]="SCHEMA_OPENED_PROSPECTIVELY"
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print("SCHEMA_FUTURE_RESULT",report["status"],"G2",report["G2"],flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_schema_prospective_future_v3.py OUTPUT")
    main(pathlib.Path(sys.argv[1]).resolve())
