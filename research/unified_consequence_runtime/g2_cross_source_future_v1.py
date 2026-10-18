#!/usr/bin/env python3
"""Prospective sealed-future transfer of byte-identical Werkzeug-acquired operator.

Source/test of the sealed future are obtained ONLY after checking the committed
training receipt, immutable method bytes and original pre-source role freeze.
Does not train, tune or modify the learned grammar on the future.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,sys,traceback

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_cross_source_train_v1 as acquired

ROOT=pathlib.Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
RECEIPT=U+"G2_WERKZEUG_TRAINED_METHOD_V1_RECEIPT.json"
RECEIPT_COMMIT="0db4870126c610f2dd23591ba9968037ba52ce0a"
ROLE_PATH=U+"G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
ROLE_COMMIT="57c400ea49881e440f7895acaeebeee5854363e3"
METHOD_SHA="c94bf5750b09e1c00f8e1406309c01946f92b48b5e283fd0fc341a21916680dc"

def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],timeout=45,text=True).strip()
def fixed():
    rec=ROOT/RECEIPT
    assert rec.read_bytes()==subprocess.check_output(["git","-C",str(ROOT),"show",RECEIPT_COMMIT+":"+RECEIPT])
    receipt=json.loads(rec.read_text())
    assert receipt["status"]=="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY"
    assert receipt["future"]["role"]=="SEALED_UNOPENED"
    assert receipt["G2"]=="UNKNOWN"
    assert sha((ROOT/receipt["trained_method"]["path"]).read_bytes())==METHOD_SHA
    assert receipt["trained_method"]["file_sha256"]==METHOD_SHA
    assert (ROOT/ROLE_PATH).read_bytes()==subprocess.check_output(["git","-C",str(ROOT),"show",ROLE_COMMIT+":"+ROLE_PATH])
    roles=json.loads((ROOT/ROLE_PATH).read_text())
    assert receipt["future"]["repo"]==roles["sealed_futures"][0]["repo"]
    assert receipt["future"]["pr"]==roles["sealed_futures"][0]["pr"]
    assert receipt["training"]["repo"]!=receipt["future"]["repo"]
    assert acquired.control_grammar()==1
    return roles["sealed_futures"][0],receipt

def execute(out):
    out.mkdir(parents=True,exist_ok=False)
    result={"schema":"G2_CROSS_SOURCE_FROZEN_FUTURE_V1",
            "status":"UNKNOWN_FUTURE_APPARATUS",
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "training_repo":"pallets/werkzeug",
            "method_sha256":METHOD_SHA,
            "method_mutation_permitted":False,
            "equal_information_comparator":"NOT_RUN",
            "lean_clc_flash_certificate":"NOT_RUN"}
    try:
        task,receipt=fixed()
        result["future_repo"]=task["repo"]
        result["future_pr"]=task["pr"]
        result["training_artifact_sha256"]=receipt["archive_zip_sha256"]
        # First ever future source/native admission under this new, frozen method.
        admission=native.one(task,0,out/"future-admission")
        result["admission"]=admission
        if admission["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            result["status"]="UNKNOWN_FUTURE_NOT_NATIVE_ADMITTED"
            return
        if admission["native"]["counts"]["skipped"]!=0:
            result["status"]="UNKNOWN_FUTURE_PROTECTED_SKIPS"
            return
        world=pathlib.Path(admission["work_dir"])
        source=world/task["production"]
        orig=source.read_bytes()
        assert sha(orig)==admission["source_sha256"]
        nodes=admission["protected_nodes"]
        py=pathlib.Path(admission["interpreter"])
        assert git(world,"rev-parse","HEAD")==task["base"]
        assert sha((world/task["author_test"]).read_bytes())==admission["head_test_sha256"]
        assert git(world,"diff","--name-only").splitlines()==[task["author_test"]]
        # The EXACT acquired callable is invoked with no future-relative edit.
        options=acquired.enumerate_candidates(orig)
        result["observed_candidates"]=[{k:v for k,v in x.items() if k!="source"} for x in options]
        result["candidate_count"]=len(options)
        if not options:
            result["status"]="REJECTED_TRANSFER_INAPPLICABLE_ON_FUTURE"
            return
        baseline=acquired.run_test(py,world,nodes,out/"repeated-original")
        result["original_recheck"]=baseline
        if not acquired.original_fail(baseline,len(nodes)):
            result["status"]="UNKNOWN_FUTURE_ORIGINAL_NOT_REPRODUCED"
            return
        for i,option in enumerate(options):
            dest=out/("candidate-"+str(i).zfill(2))
            try:
                source.write_bytes(option["source"])
                assert sorted(git(world,"diff","--name-only").splitlines())==sorted(
                    [task["author_test"],task["production"]])
                a=acquired.run_test(py,world,nodes,dest/"protected-a")
                result.setdefault("attempts",[]).append({
                    "index":i,"source_sha256":option["source_sha256"],
                    "protected_a":a,"status":"REJECTED_PROTECTED"})
                attempt=result["attempts"][-1]
                if not acquired.native_pass(a,nodes):
                    continue
                full=acquired.run_test(py,world,[task["author_test"]],dest/"full-author",timeout=180)
                attempt["full_author"]=full
                if not acquired.native_pass(full):
                    attempt["status"]="REJECTED_REGRESSION"
                    continue
                b=acquired.run_test(py,world,nodes,dest/"protected-b")
                attempt["protected_b"]=b
                if not acquired.native_pass(b,nodes):
                    attempt["status"]="REJECTED_REPEAT"
                    continue
                source.write_bytes(orig)
                withdrawal=acquired.run_test(py,world,nodes,dest/"withdrawal")
                attempt["withdrawal"]=withdrawal
                if not acquired.original_fail(withdrawal,len(nodes)):
                    attempt["status"]="UNKNOWN_NO_CAUSAL_WITHDRAWAL"
                    continue
                source.write_bytes(option["source"])
                restoration=acquired.run_test(py,world,nodes,dest/"restoration")
                attempt["restoration"]=restoration
                if not acquired.native_pass(restoration,nodes) or sha(source.read_bytes())!=option["source_sha256"]:
                    attempt["status"]="UNKNOWN_NO_CAUSAL_RESTORATION"
                    continue
                attempt["status"]="CANDIDATE_SOURCE_DISTINCT_NATIVE_TRANSFER_NEEDS_COMPARATORS"
                result["status"]=attempt["status"]
                result["admitted_candidate"]={k:v for k,v in option.items() if k!="source"}
                (dest/"candidate_source.py").write_bytes(option["source"])
                return
            finally:
                source.write_bytes(orig)
                assert sha(source.read_bytes())==admission["source_sha256"]
                assert git(world,"diff","--name-only").splitlines()==[task["author_test"]]
        result["status"]="REJECTED_TRANSFER_NO_NATIVE_REPAIR"
    except Exception as exc:
        result["status"]="UNKNOWN_FUTURE_APPARATUS"
        result["error"]=type(exc).__name__+": "+str(exc)[:850]
        result["traceback_tail"]=traceback.format_exc(limit=8)[-1600:]
    finally:
        result["G2"]="UNKNOWN"
        result["lean_clc_flash_certificate"]="NOT_RUN"
        result["equal_information_comparator"]="NOT_RUN"
        (out/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2,default=str)+"\n")
        print("FUTURE_RESULT",result["status"],"G2",result["G2"],flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: g2_cross_source_future_v1.py FRESH_OUTPUT")
    execute(pathlib.Path(sys.argv[1]).resolve())
