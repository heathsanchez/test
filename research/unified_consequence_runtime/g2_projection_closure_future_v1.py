#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib
from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL="research/unified_consequence_runtime/G2_PROJECTION_CLOSURE_FUTURE_V1_PROTOCOL.json"
PROTOCOL_COMMIT="c89461f13ee4f3aae270e904966c4514726e7442"
ROLE_PATH="research/unified_consequence_runtime/G2_PROSPECTIVE_PAIR_ROLE_MANIFEST_V2.json"
ROLE_COMMIT="a96afabe52abb60a899e17465a3c152fd2c7da92"
METHOD_PINS={
 "research/unified_consequence_runtime/attrs_residual_observation_genesis_v1.py":"27dbf45d6c3efc7596b6069c4e737c0a1339d014",
 "research/unified_consequence_runtime/residual_projection_method_v1.py":"c316946a467cb5361884cbbda56a3340abc558f5",
}

def git(repo,*args,raw=False):
    out=subprocess.check_output(["git","--no-replace-objects","-C",str(repo),*args])
    return out if raw else out.decode().strip()

def sha(b):return hashlib.sha256(b).hexdigest()

def bind(path,commit):
    live=(ROOT/path).read_bytes();old=git(ROOT,"show",commit+":"+path,raw=True)
    if live!=old:raise ValueError("FROZEN_FILE_CHANGED:"+path)
    return live

def main(world:Path,base_test:Path,head_test:Path,out:Path):
    p=json.loads(bind(PROTOCOL,PROTOCOL_COMMIT))
    roles=json.loads(bind(ROLE_PATH,ROLE_COMMIT))
    for path,commit in METHOD_PINS.items():bind(path,commit)
    from research.unified_consequence_runtime import residual_projection_method_v1 as method
    from research.unified_consequence_runtime.attrs_residual_observation_genesis_v1 import (
        generate_repair, run_pytest
    )
    role=next(x for x in roles["selected"] if x["role"]=="SEALED_FUTURE")
    if role["repository"]!="tox-dev/tox" or role["pr"]!=4168:raise ValueError("FUTURE_ROLE_CHANGED")
    world=world.resolve(strict=True);out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    if git(world,"rev-parse","HEAD")!=role["base"]:raise ValueError("FUTURE_BASE_CHANGED")
    prod=role["production"][0];test=role["author_tests"][0]
    original=git(world,"show",role["base"]+":"+prod,raw=True)
    if (world/prod).read_bytes()!=original:raise ValueError("FUTURE_PRODUCTION_MUTATED")
    head_raw=git(world,"show",role["head"]+":"+test,raw=True)
    if (world/test).read_bytes()!=head_raw or head_test.read_bytes()!=head_raw:
        raise ValueError("FUTURE_AUTHOR_TEST_OVERLAY_MISMATCH")
    base_raw=git(world,"show",role["base"]+":"+test,raw=True)
    if base_test.read_bytes()!=base_raw:raise ValueError("FUTURE_BASE_TEST_MISMATCH")
    changed=method.changed_nodes(base_raw,head_raw)
    result={
      "schema":"UDM_G2_PROJECTION_CLOSURE_FUTURE_V1_RESULT","status":"UNKNOWN",
      "future_repository":role["repository"],"future_pr":role["pr"],
      "future_base":role["base"],"future_head_test":role["head"],
      "production_path":prod,"author_test_path":test,
      "derived_changed_nodes":changed,
      "method_protocol":PROTOCOL_COMMIT,
      "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN"
    }
    (out/"DERIVED_CHANGED_NODES.json").write_text(json.dumps(changed,indent=2)+"\n")
    if not changed:
        result["status"]="UNKNOWN_NO_CHANGED_AUTHOR_TEST_NODE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    nodes=[str(world/test)+"::"+n for n in changed]
    baseline=run_pytest(world,nodes,out/"baseline",timeout=480)
    result["baseline"]=baseline
    if baseline["counts"]["tests"]<=0 or baseline["counts"]["errors"]!=0:
        result["status"]="UNKNOWN_FUTURE_APPARATUS"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    if baseline["counts"]["failures"]<=0:
        result["status"]="UNKNOWN_NO_AUTHENTIC_FUTURE_PROTECTED_FAILURE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    proposals=method.propose(world/test,changed,world/prod)
    result["proposal_count"]=len(proposals)
    result["proposals"]=[method.serializable(x) for x in proposals]
    if not proposals:
        result["status"]="REJECTED_PROSPECTIVE_FUTURE_METHOD_INAPPLICABLE"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    proposals.sort(key=lambda x:(x["node"],x["classes"][0]["representative"]))
    chosen=proposals[0];res=chosen["residual"];obs=chosen["classes"][0]
    attr=obs["representative"]
    repaired=generate_repair(original,res["classifier_name"],res["argument_name"],attr)
    result["selected"]={
      "node":chosen["node"],"classifier_name":res["classifier_name"],
      "attribute":attr,"observation_class":obs["class_id"],"source_sha256":sha(repaired)
    }
    (out/"GENERATED_REPAIR.py").write_bytes(repaired)
    (world/prod).write_bytes(repaired)
    a=run_pytest(world,nodes,out/"repair-a",timeout=480)
    b=run_pytest(world,nodes,out/"repair-b",timeout=480)
    full=run_pytest(world,[str(world/test)],out/"repair-full",timeout=720)
    result["repair_runs"]={"a":a,"b":b,"full":full}
    good=all(r["counts"]["failures"]==0 and r["counts"]["errors"]==0 and r["counts"]["tests"]>0 for r in (a,b,full))
    if not good:
        (world/prod).write_bytes(original)
        result["status"]="REJECTED_PROSPECTIVE_FUTURE_GENERATED_REPAIR"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    (world/prod).write_bytes(original)
    withdrawal=run_pytest(world,nodes,out/"withdrawal",timeout=480)
    result["withdrawal"]=withdrawal
    if withdrawal["counts"]["failures"]<=0 or withdrawal["counts"]["errors"]!=0:
        result["status"]="UNKNOWN_FUTURE_WITHDRAWAL"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    (world/prod).write_bytes(repaired)
    restoration=run_pytest(world,nodes,out/"restoration",timeout=480)
    result["restoration"]=restoration
    if restoration["counts"]["failures"] or restoration["counts"]["errors"]:
        result["status"]="UNKNOWN_FUTURE_RESTORATION"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");return result
    result["status"]="WARRANTED_BOUNDED_PROSPECTIVE_G2"
    result["G2"]="WARRANTED_BOUNDED_PROSPECTIVE_G2"
    result["causal_withdrawal"]=True;result["restoration"]=True
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=="__main__":
    if len(sys.argv)!=5:raise SystemExit("usage: g2_projection_closure_future_v1.py WORLD BASE_TEST HEAD_TEST OUT")
    r=main(*(Path(x).resolve() for x in sys.argv[1:]))
    print(json.dumps({
      "status":r.get("status"),"changed_nodes":r.get("derived_changed_nodes"),
      "baseline":r.get("baseline",{}).get("counts"),"proposal_count":r.get("proposal_count"),
      "selected":r.get("selected"),"G2":r.get("G2")
    },sort_keys=True))
    raise SystemExit(0 if r.get("status") in {
      "WARRANTED_BOUNDED_PROSPECTIVE_G2",
      "REJECTED_PROSPECTIVE_FUTURE_METHOD_INAPPLICABLE",
      "REJECTED_PROSPECTIVE_FUTURE_GENERATED_REPAIR",
      "UNKNOWN_NO_AUTHENTIC_FUTURE_PROTECTED_FAILURE"
    } else 2)
