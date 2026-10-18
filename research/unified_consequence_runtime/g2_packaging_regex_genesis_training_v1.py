#!/usr/bin/env python3
"""Train a generic regex end-boundary operation on exposed Packaging evidence.

This run never fetches the newly frozen Click/Requests/urllib3/Pydantic pool.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import subprocess,sys,time,traceback

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_packaging_future_v1 as previous
from research.unified_consequence_runtime import g2_regex_language_boundary_v1 as genesis
from research.unified_consequence_runtime import g2_werkzeug_train_v1 as controls

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
METHOD_COMMIT="c1c07b60c2bc89e2f476bf9330856c3167fd2029"
ROLES_COMMIT="d5327f0e72750a85f1a7a9cb0de6e82f608f572d"
EXPECTED_SOURCE_SHA="a10d2871bb4015855a6e894790949189afff40ae7364fe0210efa91e299fa32e"

def sha(b):return hashlib.sha256(b).hexdigest()
def git_show(commit,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",commit+":"+path],timeout=30)
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    r={"schema":"G2_PACKAGING_REGEX_GENESIS_TRAIN_V1","G2":"UNKNOWN",
       "new_future_pool":"SEALED_UNOPENED","status":"UNKNOWN_ENVIRONMENT"}
    begin=time.monotonic()
    try:
        if (ROOT/U/"G2_GENESIS_V2_PACKAGING_TRAIN_FUTURE_POOL_PREQUERY.md").read_bytes()!=git_show(
            ROLES_COMMIT,U+"G2_GENESIS_V2_PACKAGING_TRAIN_FUTURE_POOL_PREQUERY.md"):
            raise RuntimeError("FUTURE_POOL_PROTOCOL_CHANGED")
        methodbytes=(ROOT/U/"g2_regex_language_boundary_v1.py").read_bytes()
        if methodbytes!=git_show(METHOD_COMMIT,U+"g2_regex_language_boundary_v1.py"):
            raise RuntimeError("METHOD_CHANGED_AFTER_FREEZE")
        r["method_sha256"]=sha(methodbytes)
        genesis.self_test()
        manifest,_=controls.manifest()
        task=manifest["sealed_futures"][0]
        if task["repo"]!="pypa/packaging" or task["pr"]!=1446:
            raise RuntimeError("WRONG_EXPOSED_TRAINING_SOURCE")
        baseline=native.one(task,5,out/"native-original")
        r["native_original"]=baseline
        if baseline["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            r["status"]="UNKNOWN_NATIVE_TRAINING_NOT_ADMITTED"
            return r
        counts=baseline["native"]["counts"]
        nodes=baseline["protected_nodes"]
        if counts!={"tests":5,"failures":1,"errors":0,"skipped":0} or len(nodes)!=1:
            r["status"]="UNKNOWN_ORIGINAL_PARAMETRIC_BASELINE"
            return r
        world=Path(baseline["work_dir"])
        py=Path(baseline["interpreter"])
        source=(world/task["production"]).read_bytes()
        if sha(source)!=EXPECTED_SOURCE_SHA:
            raise RuntimeError("BASE_SOURCE_HASH_CHANGED")
        c=genesis.generate(source)
        r["candidate_count"]=len(c)
        r["candidate_catalogue"]=[{k:v for k,v in x.items() if k!="source"} for x in c]
        if not c:
            r["status"]="REJECTED_NO_REGEX_BOUNDARY_CANDIDATES"
            return r
        result=previous.test_one_arm(py,world,source,task,nodes,c,out,"regex-genesis-training",counts)
        r["generated_repair"]=result
        if result["status"]=="WARRANTED_BOUNDED_NATIVE_CANDIDATE":
            r["status"]="WARRANTED_BOUNDED_PACKAGING_TRAINING_REPAIR_FUTURE_SEALED"
        else:
            r["status"]="REJECTED_REGEX_BOUNDARY_TRAINING_NO_NATIVE_REPAIR"
        return r
    except Exception as ex:
        r["status"]="UNKNOWN_TRAINING_APPARATUS"
        r["error"]=type(ex).__name__+": "+str(ex)[:700]
        r["traceback"]=traceback.format_exc(limit=6)[-1500:]
        return r
    finally:
        r["wall_seconds"]=round(time.monotonic()-begin,4)
        (out/"RESULT.json").write_text(json.dumps(r,indent=2,sort_keys=True,default=str)+"\n")
        print("REGEX_TRAINING",json.dumps({k:r.get(k) for k in ("status","candidate_count","new_future_pool","G2","error")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: packaging_genesis_train.py OUT")
    main(Path(sys.argv[1]).resolve())
