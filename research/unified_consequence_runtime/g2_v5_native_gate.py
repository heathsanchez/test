#!/usr/bin/env python3
"""V5 original native first-failure admission, preserving sealed future.

This is a new cohort-specific ORCHESTRATOR of the existing V2 native
admission machinery, not a change to its method, grammar, or protected tests.
No candidate repairs or G2 claims are made by this script.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import sys
import time
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native

ROOT = pathlib.Path(__file__).resolve().parents[2]
U = "research/unified_consequence_runtime/"
LOCK = U + "G2_OBSERVATION_CHOICE_V5_ROLE_FREEZE.json"
LOCK_COMMIT = "d96833fa8a41b4e5b67d5a9498ee1b1607c476e2"
SPEC = U + "G2_OBSERVATION_CHOICE_V5_PREQUERY.json"
SPEC_COMMIT = "fc3177b20e7508d511c32a9ec6c76d711cc8389d"
TRAIN = ["TRAINING_0", "TRAINING_1", "TRAINING_2"]

def frozen(path, commit):
    current = (ROOT / path).read_bytes()
    original = subprocess.check_output(["git", "-C", str(ROOT), "show", commit + ":" + path])
    if current != original:
        raise ValueError("IMMUTABLE_FREEZE_CHANGED:" + path)
    return json.loads(original)

def main(out):
    out.mkdir(parents=True, exist_ok=False)
    role = frozen(LOCK, LOCK_COMMIT)
    spec = frozen(SPEC, SPEC_COMMIT)
    assert role["prequery_commit"] == SPEC_COMMIT
    assert len(role["roles"]) == 4
    assert [r["role"] for r in role["roles"]] == [*TRAIN, "SEALED_FUTURE"]
    assert [r["repo"] for r in role["roles"]] == [
        "pallets/flask", "Textualize/textual", "python-poetry/poetry-core",
        "marshmallow-code/marshmallow"]
    excluded = {r.lower() for r in spec["historical_exclusions"]}
    assert all(r["repo"].lower() not in excluded for r in role["roles"])
    report = {
        "schema":"UDM_G2_V5_FIRST_ORIGINAL_NATIVE_PROTECTED_FAILURE",
        "original_role_lock_sha256":hashlib.sha256((ROOT / LOCK).read_bytes()).hexdigest(),
        "prequery_commit": SPEC_COMMIT,
        "freeze_commit":LOCK_COMMIT,
        "status":"UNKNOWN_NO_ADMISSIBLE_TRAINING_FAILURE",
        "admissions":[], "selected":None, "future":"SEALED_UNOPENED",
        "future_native":"NOT_EXECUTED", "G2":"UNKNOWN", "G3":"UNKNOWN",
        "G4":"UNKNOWN", "G5":"UNKNOWN", "G6":"UNKNOWN",
    }
    start=time.monotonic()
    try:
        for i, task in enumerate(role["roles"][:3]):
            if time.monotonic()-start > 1250:
                report["status"]="UNKNOWN_TOTAL_ADMISSION_BUDGET"
                break
            t={"repo":task["repo"],"pr":task["number"],
               "base":task["base"],"head":task["author_head"],
               "author_test":task["author_test"],"production":task["production"]}
            row=native.one(t,i,out/("training-"+str(i)))
            c=row.get("native",{}).get("counts",{})
            # V5's stronger no-skipped-protected-assertion admission requirement
            if row["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
                if c.get("skipped",0) != 0:
                    row["status"]="UNKNOWN_PROTECTED_SKIPS_NOT_ELIGIBLE"
                    row.pop("work_dir",None);row.pop("interpreter",None)
                elif not row.get("protected_nodes") or c.get("tests",0)<1:
                    row["status"]="UNKNOWN_MISSING_PROTECTED_NODE_EXECUTION"
                    row.pop("work_dir",None);row.pop("interpreter",None)
            report["admissions"].append(row)
            (out/"PROGRESS.json").write_text(json.dumps({
                "admissions":report["admissions"],"future":"SEALED_UNOPENED",
                "G2":"UNKNOWN"},indent=2,sort_keys=True))
            print("V5_ADMISSION",i,t["repo"],row["status"],flush=True)
            if row["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
                report["selected"]=row
                report["status"]="WARRANTED_BOUNDED_FIRST_ORIGINAL_PROTECTED_NATIVE_FAIL"
                break
        report["elapsed_seconds"]=round(time.monotonic()-start,3)
    finally:
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print("V5_NATIVE_RESULT",report["status"],"FUTURE_SEALED",flush=True)
    return report

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: g2_v5_native_gate.py NEW_OUTPUT_DIR")
    main(pathlib.Path(sys.argv[1]).resolve())
