#!/usr/bin/env python3
"""Posthoc exposed AnyIO: native tests of nine precommitted source-selected edits.

All 9 exact whole-module SHA256 candidates were frozen before any native outcome.
Only original source-pinned V104 constructors and typed V6 author-test authority.
No editing upstream, source-specific repair, prospective G2 or future access.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile
from research.unified_consequence_runtime.qualify_recursive_frontier import original_candidates
from research.unified_consequence_runtime import qualify_source_bound_g2_v9 as original
from research.unified_consequence_runtime import g2_original_v104_training_native_v1 as admission

ROOT=Path(__file__).resolve().parents[2]
U=ROOT/"research/unified_consequence_runtime"
P=U/"G2_ANYIO_PRECAP_NATIVE_POSTHOC_V2_PROTOCOL.json"
FROZEN="877289b56a200b05e0c1c7915ac59a6fdef5a44b"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(repo,*parts,raw=False):
    value=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*parts],timeout=60)
    return value if raw else value.decode().strip()
def authority():
    live=P.read_bytes(); pinned=git(ROOT,"show",FROZEN+":"+str(P.relative_to(ROOT)),raw=True)
    if live!=pinned:raise ValueError("POSTHOC_PRE_NATIVE_PROTOCOL_MUTATED")
    p=json.loads(pinned)
    if len(p["shortlist"])!=9 or p["G2"]!="UNKNOWN":
        raise ValueError("WRONG_FROZEN_CANDIDATE_HORIZON")
    return p
def load_pre_cap(path,p):
    raw=Path(path).read_bytes()
    if sha(raw)!=p["source_only_artifact_sha256"]:
        raise ValueError("SOURCE_ONLY_ORIGINAL_ARTIFACT_DIGEST_CHANGED")
    with zipfile.ZipFile(path) as zip:
        if zip.testzip() is not None:raise ValueError("SOURCE_ONLY_ARTIFACT_CRC")
        result=json.loads(zip.read("evidence/udm-g2-precap-v1/diagnostic/RESULT.json"))
    if result["G2"]!="UNKNOWN" or result["heldout_future"]!="SEALED_UNOPENED":
        raise ValueError("SOURCE_ONLY_POSTHOC_AUTHORITY_CHANGED")
    if len(result["new_pre_cap_top"])!=3 or len(result["new_production_operations"])!=3:
        raise ValueError("SOURCE_ONLY_FUNCTION_SELECTION_CHANGED")
    return result

def emit(repo,triskelion,p,precap):
    raw=git(repo,"show",p["source"].split("@")[-1]+":"+p["production_path"],raw=True)
    if sha(raw)!=p["original_production_sha256"]:
        raise ValueError("ORIGINAL_SOURCE_BLOB_DIGEST_CHANGED")
    source=raw.decode("utf-8")
    tree=ast.parse(source,filename=p["production_path"])
    fns={f.name:f for f in tree.body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef))}
    names=[v["name"] for v in precap["new_pre_cap_top"]]
    assert names==[x["function"] for x in precap["new_production_operations"]]
    byname={}
    for j,name in enumerate(names):
        function=fns[name]
        one=ast.unparse(ast.Module(body=[copy.deepcopy(function)],type_ignores=[]))
        proposals=original_candidates(triskelion,one,cap=16)
        assert len(proposals)==precap["new_production_operations"][j]["original_emitted"]
        variants=[]
        for idx,(selector,builder,newtext) in enumerate(proposals[:3]):
            selected=ast.parse(newtext)
            assert len(selected.body)==1 and selected.body[0].name==name
            changed=copy.deepcopy(tree)
            target=[i for i,node in enumerate(changed.body)
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name]
            assert len(target)==1
            changed.body[target[0]]=selected.body[0]
            for k,(a,b) in enumerate(zip(ast.dump(tree,include_attributes=False).splitlines(),
                                        ast.dump(changed,include_attributes=False).splitlines())):
                pass  # Full untouched-module invariance below, not line-by-line source formatting.
            assert all(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
                       for i,(a,b) in enumerate(zip(tree.body,changed.body)) if i!=target[0])
            rendered=ast.unparse(ast.fix_missing_locations(changed))
            assert ast.dump(ast.parse(rendered),include_attributes=False)==ast.dump(changed,include_attributes=False)
            expect=precap["new_production_operations"][j]["first_four"][idx]
            if [list(selector),list(builder)]!=[expect["selector"],expect["builder"]]:
                raise ValueError("FROZEN_V104_GENERATOR_PROGRAM_CHANGED")
            if sha(rendered.encode())!=expect["whole_program_sha256"]:
                raise ValueError("FROZEN_PRECAP_EMITTED_SOURCE_CHANGED")
            variants.append((rendered,selector,builder))
        byname[name]=variants
    output=[]
    for wave in range(3):
        for name in names:
            content,sel,builder=byname[name][wave]
            output.append({"index":len(output),"function":name,"program":content,
                            "source_sha256":sha(content.encode()),"selector":list(sel),
                            "builder":list(builder)})
    for frozen,row in zip(p["shortlist"],output):
        if (frozen["index"],frozen["function_name"],frozen["whole_program_sha256"]) != (
                row["index"],row["function"],row["source_sha256"]):
            raise ValueError("NATIVE_CANDIDATE_DIFFERENT_FROM_ORIGINAL_PRECOMMITTED_SHA")
    return output

def run(repo,v104,source_only,output):
    result={"schema":"UDM_ANYIO_EXPOSED_PRECAP_POSTHOC_NATIVE_V2",
            "status":"UNKNOWN_NOT_EXECUTED","G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "G5":"UNKNOWN","G6":"UNKNOWN","heldout":"UNOPENED",
            "coding_agent":"NOT_RUN","ledger_comparator":"NOT_RUN",
            "native_calls_charged":0,"candidates":[],"training_only":True}
    t0=time.monotonic()
    output.mkdir(parents=True,exist_ok=False)
    try:
        p=authority();ref=load_pre_cap(source_only,p)
        base=p["source"].split("@")[-1]
        if git(repo,"rev-parse","HEAD")!=base or git(repo,"status","--porcelain"):
            raise ValueError("WRONG_OR_DIRTY_ORIGINAL_BASE")
        if git(v104,"rev-parse","HEAD")!=p["original_v104_pin"].split("@")[-1]:
            raise ValueError("WRONG_PINNED_V104_SOURCE")
        pool=json.loads((U/"G2_SOURCE_DISTINCT_POOL_V1.json").read_text())
        assert pool["case_pool"][0]["base"]==base
        task=pool["case_pool"][0]
        authors=admission.prepare_author(repo,task)
        author=authors[0]
        source_task={"author_tests":[v["path"] for v in task["head_author_tests"]],
                     "production":[v["path"] for v in task["production"]]}
        catalog=emit(repo,v104,p,ref)
        (output/"LOCKED_PRE_NATIVE_SCHEDULE.json").write_text(json.dumps([
            {k:v for k,v in c.items() if k!="program"} for c in catalog],indent=2)+"\n")
        (output/"SCIENCE_PROTOCOL_SHA256.json").write_text(json.dumps({
            "sha256":sha(P.read_bytes()),"source_only":p["source_only_artifact_sha256"],
            "native_trials_initially_zero":True,"heldout":"UNOPENED","G2":"UNKNOWN"},indent=2)+"\n")
        timeout=p["candidate_native_timeout_seconds"]
        baseline=original._observation(repo,base,author,{"replacements":[]},
              output/"baseline",source_task,timeout)
        result["native_calls_charged"]+=baseline["native_calls"]
        result["baseline"]={k:v for k,v in baseline.items() if k not in ("native_first","native_second")}
        if baseline["status"]!=original.BAD:
            result["status"]="UNKNOWN_NATIVE_BASELINE_NOT_AUTHENTIC"
            return result
        result["status"]="ORIGINAL_PROTECTED_FAIL_REPLAYED"
        for row in catalog:
            if result["native_calls_charged"]+2>p["maximum_native_calls_including_baseline"]:
                result["status"]="UNKNOWN_NATIVE_BUDGET"
                break
            if time.monotonic()-t0>p["wall_budget_seconds"]:
                result["status"]="UNKNOWN_WALL_BUDGET"
                break
            out=output/("candidate-"+str(row["index"]).zfill(2))
            r=original._observation(repo,base,author,{"replacements":[{
                "path":p["production_path"],"original_sha256":p["original_production_sha256"],
                "replacement":row["program"]}]},out,source_task,timeout)
            result["native_calls_charged"]+=r["native_calls"]
            evidence={k:v for k,v in r.items() if k not in ("native_first","native_second")}
            record={"index":row["index"],"function":row["function"],
                    "candidate_sha256":row["source_sha256"],"status":r["status"],
                    "native_calls_charged":r["native_calls"],
                    "evidence":evidence}
            result["candidates"].append(record)
            (output/"PROGRESS.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
            print("TRIAL",row["index"],row["function"],r["status"],"native_charged",result["native_calls_charged"],flush=True)
        if len(result["candidates"])!=9:
            return result
        counts={}
        for row in result["candidates"]:
            counts[row["status"]]=counts.get(row["status"],0)+1
        result["outcome_counts"]=counts
        result["status"]=("WARRANTED_BOUNDED_EXPOSED_POSTHOC_NATIVE_CANDIDATE" if (
            "VERIFIED_REPEATED_PASS_SCOPED_NATIVE" in counts) else
            "REJECTED_BOUNDED_EXPOSED_PRECAP_NATIVE_NINE_NO_PASS"
            if all(r["status"]=="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED" for r in result["candidates"])
            else "UNKNOWN_EXPOSED_PRECAP_NATIVE_MIXED_NEGATIVE")
        return result
    except BaseException as error:
        result["status"]="UNKNOWN_NATIVE_APPARATUS"
        result["reason"]=type(error).__name__+": "+str(error)
        result["traceback"]=traceback.format_exc(limit=7)[-2600:]
        return result
    finally:
        result["elapsed_seconds"]=time.monotonic()-t0
        (output/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")

if __name__=="__main__":
    if len(sys.argv)!=5:raise SystemExit("usage: SOURCE_BASE V104_SOURCE ORIGINAL_PRECAP_ZIP FRESH_OUTPUT")
    r=run(*(Path(x).resolve() for x in sys.argv[1:]))
    print(json.dumps({k:r.get(k) for k in ("status","native_calls_charged","outcome_counts","reason","G2")},sort_keys=True))
    raise SystemExit(0 if r["status"] in (
        "WARRANTED_BOUNDED_EXPOSED_POSTHOC_NATIVE_CANDIDATE",
        "REJECTED_BOUNDED_EXPOSED_PRECAP_NATIVE_NINE_NO_PASS",
        "UNKNOWN_EXPOSED_PRECAP_NATIVE_MIXED_NEGATIVE") else 2)
