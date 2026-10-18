#!/usr/bin/env python3
"""V5 first-authentic-failure admission on frozen source-hidden metadata roles.

Reuses the exact independently qualified V2 native preparation/test runner.
No source/test/PR patch inspection outside frozen TRAINING_0..2. The fourth
SEALED_FUTURE is metadata-only and cannot be opened from this module.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from . import g2_pool_first_native_failure_v1 as native

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
ROLE=U+"G2_OBSERVATION_CHOICE_V5_ROLE_FREEZE.json"
ROLE_COMMIT="d96833fa8a41b4e5b67d5a9498ee1b1607c476e2"
PINNED_NATIVE="a701e7693609eef3c96cc5cdb24ac737cf590d4b"
NATIVE_FILE=U+"g2_pool_first_native_failure_v1.py"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def gitshow(revision,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",revision+":"+path],timeout=50)

def frozen_roles():
    raw=(ROOT/ROLE).read_bytes()
    if raw!=gitshow(ROLE_COMMIT,ROLE):
        raise ValueError("UNKNOWN_V5_ROLE_FREEZE_CHANGED")
    if (ROOT/NATIVE_FILE).read_bytes()!=gitshow(PINNED_NATIVE,NATIVE_FILE):
        raise ValueError("UNKNOWN_PREQUALIFIED_NATIVE_ENGINE_CHANGED")
    meta=json.loads(raw)
    if (meta["schema"]!="UDM_G2_V5_METADATA_ROLE_FREEZE_SOURCE_UNOPENED"
            or meta["state"]!="FROZEN_BEFORE_ANY_TARGET_SOURCE_OR_NATIVE_EXECUTION"
            or len(meta["roles"])!=4):
        raise ValueError("UNKNOWN_V5_ROLE_SCOPE")
    roles=meta["roles"]
    if [r["role"] for r in roles] != ["TRAINING_0","TRAINING_1","TRAINING_2","SEALED_FUTURE"]:
        raise ValueError("UNKNOWN_V5_ROLE_ORDER")
    if len({r["repo"].lower() for r in roles})!=4:
        raise ValueError("UNKNOWN_V5_SOURCE_DISTINCT")
    if any(r.get("source_body")!="UNOPENED" or r.get("native_status")!="NOT_EXECUTED" for r in roles):
        raise ValueError("UNKNOWN_V5_PREMATURE_SOURCE_EXPOSURE")
    if meta.get("G2")!="UNKNOWN":
        raise ValueError("UNKNOWN_FALSE_PROSPECTIVE_PROMOTION")
    return meta

def clean_selected(row):
    if row.get("status")!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
        return False,"NOT_NATIVE_PROTECTED_FAIL"
    evidence=row.get("native") or {}
    c=evidence.get("counts") or {}
    if not (evidence.get("returncode")==1 and c.get("tests",0)>0
            and c.get("failures",0)>0 and c.get("errors")==0
            and c.get("skipped")==0):
        return False,"NO_COMPLETE_UNSKIPPED_PROTECTED_FAILURE"
    source=Path(row["work_dir"])/row["production"]
    test=Path(row["work_dir"])/row["author_test"]
    if sha(source.read_bytes())!=row["source_sha256"] or sha(test.read_bytes())!=row["head_test_sha256"]:
        return False,"SOURCE_OR_AUTHOR_TEST_IDENTITY_MUTATED"
    if not row.get("protected_nodes"):
        return False,"ZERO_PROTECTED_NODES"
    return True,"AUTHENTIC_PROTECTED_FAIL"

def execute(output):
    output=Path(output).absolute()
    output.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    result={"schema":"UDM_G2_V5_FIRST_NATIVE_FAILURE","status":"UNKNOWN_NO_ADMITTED_TRAINING_FAILURE",
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
            "future":"SEALED_UNOPENED","method_acquisition":"NOT_YET_EXECUTED",
            "source_exposure":"TRAINING_ONLY","admissions":[],"selected":None}
    try:
        roles=frozen_roles()
        result["role_freeze_commit"]=ROLE_COMMIT
        result["role_metadata_sha256"]=roles["metadata_sha256"]
        for i,role in enumerate(roles["roles"][:3]):
            if time.monotonic()-start>1400:
                result["admissions"].append({"index":i,"repo":role["repo"],
                                             "status":"UNKNOWN_TOTAL_BUDGET_EXHAUSTED"})
                break
            task={"repo":role["repo"],"pr":role["number"],"base":role["base"],
                  "head":role["author_head"],"author_test":role["author_test"],
                  "production":role["production"]}
            row=native.one(task,i,output/("admission-"+str(i)))
            # The original qualified V2 primitive records the native result
            # without repeating its immutable task paths. Rebind only the
            # *already frozen* source/test paths before V5 strict validation.
            row["production"]=task["production"]
            row["author_test"]=task["author_test"]
            ok,why=clean_selected(row) if row.get("status")=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE" else (False,row["status"])
            row["v5_boundary"]=why
            if row.get("status")=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE" and not ok:
                row["status"]="UNKNOWN_STRICT_V5_NATIVE_BOUNDARY"
            result["admissions"].append(row)
            (output/"PROGRESS.json").write_text(json.dumps({
                "admissions":result["admissions"],"future":"SEALED_UNOPENED",
                "G2":"UNKNOWN"},sort_keys=True,indent=2))
            print("V5_TRAINING_ADMISSION",i,role["repo"],row["status"],flush=True)
            if ok:
                result["selected"]=row
                result["status"]="ADMITTED_FIRST_NEW_PROTECTED_FAILURE_FUTURE_SEALED"
                result["method_acquisition"]="READY_FOR_BYTE_PINNED_V5_CHOICE"
                break
    except Exception as exc:
        result["status"]="UNKNOWN_V5_NATIVE_APPARATUS"
        result["reason"]=type(exc).__name__+":"+str(exc)[:550]
    finally:
        result["total_wall_seconds"]=round(time.monotonic()-start,4)
        (output/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    return result

if __name__=="__main__":
    r=execute(sys.argv[1])
    print("V5_BOUNDARY",r["status"],"FUTURE",r["future"],"G2",r["G2"],flush=True)
    if r["status"]=="UNKNOWN_V5_NATIVE_APPARATUS":
        raise SystemExit(2)
