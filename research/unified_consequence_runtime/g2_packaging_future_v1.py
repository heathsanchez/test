#!/usr/bin/env python3
"""First real source-distinct future test of the frozen acquired operator.

The method, role choice and comparator are verified against pre-future Git
commits before any future fetch/checkout/test. All native claims are bounded.
"""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
import subprocess,sys,time,traceback

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_context_fallback_operator_v1 as acquired
from research.unified_consequence_runtime import g2_equal_info_guard_ablation_v1 as equal_info
from research.unified_consequence_runtime import g2_werkzeug_train_v1 as controls

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
LOCK="G2_ACQUIRED_OPERATION_V1_PRE_FUTURE_LOCK.json"
LOCK_COMMIT="e967f86c8f486a6b55b9d7d20c8ace11619008e4"
METHOD_COMMIT="6fbfa0a633439f0eb5c8e9c55726f2b053e1bdd1"
BASELINE_COMMIT="0a67b3bee47b8fdaa420aed9b370e5ddb2f82780"

def sha(b):return hashlib.sha256(b).hexdigest()

def git_show(commit,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",commit+":"+path],timeout=40)

def preflight():
    lockbytes=(ROOT/U/LOCK).read_bytes()
    if lockbytes!=git_show(LOCK_COMMIT,U+LOCK):raise RuntimeError("POST_FREEZE_LOCK_CHANGED")
    lock=json.loads(lockbytes)
    methodbytes=(ROOT/U+"g2_context_fallback_operator_v1.py").read_bytes()
    baselinebytes=(ROOT/U+"g2_equal_info_guard_ablation_v1.py").read_bytes()
    if methodbytes!=git_show(METHOD_COMMIT,U+"g2_context_fallback_operator_v1.py"):raise RuntimeError("ACQUIRED_METHOD_CHANGED")
    if baselinebytes!=git_show(BASELINE_COMMIT,U+"g2_equal_info_guard_ablation_v1.py"):raise RuntimeError("COMPARATOR_CHANGED")
    if sha(methodbytes)!=lock["acquired_method"]["sha256"]:raise RuntimeError("ACQUIRED_SHA_MISMATCH")
    roles, _ = controls.manifest()  # checks role, generic method, frozen experiment protocol
    fut=roles["sealed_futures"][0]
    for fld in ("repo","pr","base","head","production","author_test"):
        if fut[fld]!=lock["future"][fld]:raise RuntimeError("FUTURE_ROLE_CHANGED:"+fld)
    assert lock["training_evidence"]["artifact_zip_sha256"]=="83d9a4a427476af203d8466728368d9ad65fd11c6c0247b44483ca9f6c1b66e6"
    assert lock["training"]["production_generated_sha256"]=="535c5292e2c9a147c29ac0109540bf2c5e9a017fd2dc5e57a997241ade8cd1e7"
    assert lock["future"]["source_unopened_at_lock"] is True
    assert lock["no_future_reselection"] is True
    equal_info.self_test()
    acquired.self_test()
    return fut,lock

def test_one_arm(py,world,original,task,nodes,candidates,out,label,original_counts):
    report={"name":label,"candidate_count":len(candidates),"candidate_cap":12,"status":"NO_CANDIDATE",
            "native_invocations":0,"candidate_outcomes":[],"generation_only":False}
    production=task["production"]
    if not candidates:
        return report
    for i,c in enumerate(candidates[:12]):
        item={"candidate_index":i,"candidate_sha256":sha(c["source"]),"status":"REJECTED_NATIVE"}
        item["candidate_rule"]={k:v for k,v in c.items() if k!="source"}
        try:
            (world/production).write_bytes(c["source"])
            if not controls.working_diff(world,production,task["author_test"],patched=True):
                raise RuntimeError("UNAUTHORIZED_SOURCE_EDIT")
            first=controls.run(py,world,nodes,out/f"{label}-{i:02d}"/"protected")
            report["native_invocations"]+=1
            item["protected"]=first
            if not controls.exactly(first,len(nodes),0):
                report["candidate_outcomes"].append(item)
                continue
            again=controls.run(py,world,nodes,out/f"{label}-{i:02d}"/"protected-repeat")
            report["native_invocations"]+=1
            item["protected_repeat"]=again
            if not controls.exactly(again,len(nodes),0):
                report["candidate_outcomes"].append(item)
                continue
            full=controls.run(py,world,[task["author_test"]],out/f"{label}-{i:02d}"/"full-author-file")
            report["native_invocations"]+=1
            item["full_author_file"]=full
            if full["returncode"]!=0 or full["counts"]["errors"] or full["counts"]["failures"] or full["counts"]["tests"]<len(nodes):
                report["candidate_outcomes"].append(item)
                continue
            (world/production).write_bytes(original)
            withdrawn=controls.run(py,world,nodes,out/f"{label}-{i:02d}"/"withdrawal")
            report["native_invocations"]+=1
            item["withdrawal"]=withdrawn
            if not controls.exactly(withdrawn,
                                    original_counts["tests"]-original_counts["failures"],
                                    original_counts["failures"]):
                item["status"]="UNKNOWN_WITHDRAWAL"
                report["candidate_outcomes"].append(item)
                continue
            (world/production).write_bytes(c["source"])
            restored=controls.run(py,world,nodes,out/f"{label}-{i:02d}"/"restoration")
            report["native_invocations"]+=1
            item["restoration"]=restored
            if not controls.exactly(restored,len(nodes),0) or sha((world/production).read_bytes())!=item["candidate_sha256"]:
                item["status"]="UNKNOWN_RESTORATION"
                report["candidate_outcomes"].append(item)
                continue
            item["status"]="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
            report["candidate_outcomes"].append(item)
            report["status"]="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
            report["success_sha256"]=item["candidate_sha256"]
            break
        finally:
            (world/production).write_bytes(original)
            if sha((world/production).read_bytes()) != sha(original):
                raise RuntimeError("PHYSICAL_RESTORE_FAILED")
            if not controls.working_diff(world,production,task["author_test"]):
                raise RuntimeError("RESTORE_DIRTY_TRACKED_TREE")
    if report["status"]=="NO_CANDIDATE" and report["candidate_outcomes"]:
        report["status"]="REJECTED_NO_NATIVE_PASS"
    report["total_native_seconds"]=round(sum(
        sum(c[k]["seconds"] for k in ("protected","protected_repeat","full_author_file","withdrawal","restoration") if k in c)
        for c in report["candidate_outcomes"]),4)
    return report

def original_inventory(task,original,world,lock):
    from research.unified_consequence_runtime import g2_anyio_mutable_closure_equivalence_fix_v2 as mutable
    from research.unified_consequence_runtime import attrs_residual_observation_genesis_v1 as projection
    code=task["production"]
    old=mutable.scan_patterns(code,original)
    result={"mutable_patterns":len(old),"mutable":"NO_APPLICABLE_PATTERN" if not old else "APPLICABLE_UNEXECUTED",
            "primitive_projection":"NOT_APPLICABLE","source":"FROZEN_PRE_ACQUISITION_INVENTORY"}
    try:
        projection.derive_classifier_and_cases(world/task["author_test"])
        result["primitive_projection"]="APPLICABLE_UNEXECUTED"
    except Exception as e:
        result["primitive_projection"]="NO_APPLICABLE_PATTERN"
        result["projection_reason"]=type(e).__name__+": "+str(e)[:200]
    result["complete"] = not old and result["primitive_projection"]=="NO_APPLICABLE_PATTERN"
    return result

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"G2_PROSPECTIVE_PACKAGING_FUTURE_V1",
            "status":"UNKNOWN_PRE_FUTURE","G2":"UNKNOWN",
            "claim":"NO_CROSS_SOURCE_WARRANT_FROM_UNVERIFIED_REPORTED_FLAGS",
            "heldout":"SEALED_UNTIL_PREFLIGHT","lean":"NOT_EXECUTED",
            "CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
            "MathGraph":"EVIDENCE_CANDIDATE","strong_agent":"NOT_RUN"}
    start=time.monotonic()
    try:
        task,lock=preflight()
        report["pre_future_lock_sha256"]=sha((ROOT/U/LOCK).read_bytes())
        report["method_sha256"]=lock["acquired_method"]["sha256"]
        report["training_artifact_sha256"]=lock["training_evidence"]["artifact_zip_sha256"]
        report["heldout"]="UNSEALED_AFTER_VERIFIED_PRE_FUTURE_LOCK"
        report["future_identifiers"]={k:task[k] for k in ("repo","pr","base","head","production","author_test")}
        # Exactly one preselected future; no alternatives if it is ineligible.
        original_test=native.one(task,5,out/"future-native-admission")
        report["future_native"]=original_test
        if original_test["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"]="UNKNOWN_FUTURE_NOT_ADMITTED"
            return report
        nodes=original_test["protected_nodes"]
        counts=original_test["native"]["counts"]
        if counts["tests"]!=len(nodes) or counts["skipped"] or counts["failures"]<1 or counts["errors"]:
            report["status"]="UNKNOWN_PROTECTED_FUTURE_INTEGRITY"
            return report
        world=Path(original_test["work_dir"])
        py=Path(original_test["interpreter"])
        original=(world/task["production"]).read_bytes()
        if sha(original)!=original_test["source_sha256"]:
            raise RuntimeError("ORIGINAL_FUTURE_SOURCE_IDENTITY")
        if not controls.working_diff(world,task["production"],task["author_test"]):
            raise RuntimeError("ORIGINAL_FUTURE_DIRTY_SOURCE")
        report["protected_count"]=len(nodes)
        report["future_original_source_sha256"]=sha(original)
        report["pre_acquisition"]=original_inventory(task,original,world,lock)
        gen_started=time.monotonic()
        learned=acquired.generate(original)  # unchanged acquired method
        report["acquired_generation_seconds"]=round(time.monotonic()-gen_started,6)
        gen_started=time.monotonic()
        base=equal_info.generate(original)
        report["equal_info_generation_seconds"]=round(time.monotonic()-gen_started,6)
        # Each arm sees identical original source and author-derived protected tests.
        report["equal_info_baseline"]=test_one_arm(py,world,original,task,nodes,base,out,"baseline",counts)
        report["acquired_operator"]=test_one_arm(py,world,original,task,nodes,learned,out,"acquired",counts)
        gained=report["acquired_operator"]["status"]=="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
        baselined=report["equal_info_baseline"]["status"]=="WARRANTED_BOUNDED_NATIVE_CANDIDATE"
        report["baseline_native_gain"]=baselined
        report["acquired_native_gain"]=gained
        report["source_distinct"]=task["repo"] != lock["training"]["repo"]
        if not learned:
            report["status"]="REJECTED_PROSPECTIVE_TRANSFER_INAPPLICABLE"
        elif not gained:
            report["status"]="REJECTED_NO_NATIVE_FUTURE_REPAIR"
        elif baselined or not report["pre_acquisition"]["complete"]:
            report["status"]="UNKNOWN_NO_VERIFIED_COMPARATIVE_ADVANTAGE"
        else:
            report["status"]="CANDIDATE_BOUNDED_CROSS_SOURCE_GAIN_PENDING_CERTIFICATION"
        # Never self-promote before independent auditor/Lean/CLC/FLASH.
        report["G2"]="UNKNOWN"
        return report
    except Exception as ex:
        report["status"]="UNKNOWN_FUTURE_APPARATUS"
        report["error"]=type(ex).__name__+": "+str(ex)[:950]
        report["traceback"]=traceback.format_exc(limit=8)[-2100:]
        return report
    finally:
        report["wall_seconds"]=round(time.monotonic()-start,4)
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print("FUTURE_RESULT",json.dumps({k:report.get(k) for k in
             ("status","heldout","G2","protected_count","acquired_native_gain","baseline_native_gain","error")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_packaging_future_v1.py FRESH_OUT")
    main(Path(sys.argv[1]).resolve())
