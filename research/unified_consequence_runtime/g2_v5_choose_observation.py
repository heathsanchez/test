#!/usr/bin/env python3
"""V5 fixed-method applicability and original-native causal test on admitted TRAINING.

This engine is engineer-supplied routing over two previously qualified method
languages; it is NOT invention of a new method language and NEVER opens future.
Run from the selected original native venv, without checkout credentials.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from . import g2_v5_native_admission as admission
from . import g2_pool_apply_fixed_methods_v1 as old_controls

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
METHOD_PINS=(
 ("mutable","094e2ddc3ba601a00eaf368151172a361e5542da",
  U+"g2_anyio_mutable_closure_equivalence_fix_v2.py"),
 ("projection","d83de24d3b5bb4352cd6991a85a0fbc1e72f6deb",
  U+"residual_projection_method_v1.py"),
 ("projection_support","b9d175d0b129c843bc5885aec77082f07f2b0601",
  U+"attrs_residual_observation_genesis_v1.py"),
)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def pinned_method_bytes():
    o={}
    for label,commit,path in METHOD_PINS:
        raw=(ROOT/path).read_bytes()
        if raw!=admission.gitshow(commit,path):
            raise ValueError("UNKNOWN_METHOD_SOURCE_DRIFT:"+label)
        o[label]=sha(raw)
    return o

def check_source(row,role):
    if row["repo"]!=role["repo"] or row["pr"]!=role["number"] or row["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
        raise ValueError("UNKNOWN_WRONG_PROSPECTIVE_TRAINING_ROLE")
    source=Path(row["work_dir"])
    if (source/role["production"]).is_symlink() or (source/role["author_test"]).is_symlink():
        raise ValueError("UNKNOWN_SOURCE_SYMLINK")
    original=(source/role["production"]).read_bytes()
    head=(source/role["author_test"]).read_bytes()
    if sha(original)!=row["source_sha256"] or sha(head)!=row["head_test_sha256"]:
        raise ValueError("UNKNOWN_SOURCE_OR_TEST_MUTATED")
    if subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()!=role["base"]:
        raise ValueError("UNKNOWN_WRONG_NATIVE_BASE")
    if not row["protected_nodes"] or not all(x.startswith(role["author_test"]+"::") for x in row["protected_nodes"]):
        raise ValueError("UNKNOWN_PROTECTED_TEST_SCOPE")
    return source,original,head

def choose_family(mutable_qualified: bool, projection_qualified: bool):
    if mutable_qualified and projection_qualified:
        return "UNKNOWN_CHOICE_TWO_APPLICABLE_METHODS"
    if mutable_qualified:
        return "APPLICABLE_MUTABLE_METHOD"
    if projection_qualified:
        return "APPLICABLE_PROJECTION_METHOD"
    return "UNKNOWN_NO_APPLICABLE_FROZEN_METHOD"

def prepare_choice(world,original,head,role,nodes,out):
    from . import g2_anyio_mutable_closure_equivalence_fix_v2 as mutable
    from . import residual_projection_method_v1 as projection
    from . import attrs_residual_observation_genesis_v1 as projected_engine
    try:
        closure=mutable.scan_patterns(role["production"],original)
    except Exception as exc:
        raise ValueError("UNKNOWN_CLOSURE_GRAMMAR_APPARATUS:"+type(exc).__name__) from exc
    observations={"mutable":{"source_patterns":len(closure),"qualified_patterns":0},
                  "projection":{"eligible_test_nodes":0,"observation_classes":0}}
    qualifying=[]
    if closure:
        trace=mutable.run_pytest(world,nodes,out/"mutable-observation",
              patterns=closure,timeout=120)
        if sha((world/role["production"]).read_bytes())!=sha(original):
            raise ValueError("UNKNOWN_MUTABLE_OBSERVER_CHANGED_SOURCE")
        observations["mutable"]["native_trace"]={
            "exit":trace.get("returncode"),"counts":trace.get("counts"),
            "events":len(trace.get("trace_events",[]))}
        for p in closure:
            witness=mutable.trace_has_stale_capture(p,trace.get("trace_events",[]))
            if witness.get("pass") is True:qualifying.append(p)
    observations["mutable"]["qualified_patterns"]=len(qualifying)
    try:
        base_test=subprocess.check_output(["git","-C",str(world),"show",
                                           role["base"]+":"+role["author_test"]],timeout=40)
    except subprocess.CalledProcessError:
        base_test=b""
    try:
        changed=projection.changed_nodes(base_test,head)
        p=projection.propose(world/role["author_test"],changed,
                             world/role["production"])
        observations["projection"]["eligible_test_nodes"]=len(changed)
        observations["projection"]["observation_classes"]=sum(len(x["classes"]) for x in p)
        observations["projection"]["negative_reason"]="NONE" if p else "NO_DIRECT_PARAMETRIZED_BOOLEAN_RESIDUAL"
    except Exception as exc:
        p=[]
        observations["projection"]["negative_reason"]=type(exc).__name__+":"+str(exc)[:240]
    if sha((world/role["production"]).read_bytes())!=sha(original):
        raise ValueError("UNKNOWN_PROJECTION_OBSERVER_CHANGED_SOURCE")
    decision=choose_family(bool(qualifying),bool(p))
    if not decision.startswith("APPLICABLE_"):
        return decision,observations,[],None
    candidates=[]
    if decision=="APPLICABLE_MUTABLE_METHOD":
        for item in sorted(qualifying,key=lambda x:x["pattern_id"])[:8]:
            repaired=mutable.repair_source(original,item)
            candidates.append({"method":"mutable","source":repaired,
             "identity":item["pattern_id"],"source_sha256":sha(repaired)})
        return "APPLICABLE_MUTABLE_METHOD",observations,candidates,mutable.run_pytest
    for row in sorted(p,key=lambda x:x["node"]):
        for cls in sorted(row["classes"],key=lambda x:x["class_id"]):
            rep=cls["representative"]
            repair=projected_engine.generate_repair(original,
                    row["residual"]["classifier_name"],
                    row["residual"]["argument_name"],rep)
            candidates.append({"method":"projection","source":repair,
               "identity":row["node"]+"|"+cls["class_id"],"source_sha256":sha(repair)})
            if len(candidates)>=8:break
        if len(candidates)>=8:break
    return "APPLICABLE_PROJECTION_METHOD",observations,candidates,projected_engine.run_pytest

def main(admission_file,out):
    out=Path(out).absolute();out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    result={"schema":"UDM_G2_V5_OBSERVATION_CHOICE_TRAINING_ONLY",
            "status":"UNKNOWN_NO_EARNED_NATIVE_TRAINING","G2":"UNKNOWN",
            "G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
            "future":"SEALED_UNOPENED","agent_comparator":"NOT_EXECUTED",
            "ledger_comparator":"NOT_EXECUTED","candidate_results":[]}
    try:
        roles=admission.frozen_roles()
        result["method_sha256"]=pinned_method_bytes()
        record=json.loads(Path(admission_file).read_text())
        if record.get("status")!="ADMITTED_FIRST_NEW_PROTECTED_FAILURE_FUTURE_SEALED" or not record.get("selected"):
            result["status"]="UNKNOWN_NO_EARNED_NATIVE_TRAINING"
            return result
        row=record["selected"]
        position=next((i for i,r in enumerate(roles["roles"][:3])
                      if r["repo"]==row["repo"] and r["number"]==row["pr"]),None)
        if position is None:raise ValueError("UNKNOWN_TRAINING_ROLE_NOT_FROZEN")
        role=roles["roles"][position]
        world,original,head=check_source(row,role)
        result["training"]={"repo":role["repo"],"pr":role["number"],
           "source_sha256":sha(original),"test_sha256":sha(head),
           "protected_nodes":row["protected_nodes"]}
        decision,observations,choices,run=prepare_choice(
            world,original,head,role,row["protected_nodes"],out)
        result["applicability"]=observations
        result["decision"]=decision
        if not choices or run is None:
            result["status"]=decision
            return result
        # Commit entire generated source schedule to evidence BEFORE any proposed
        # native repair is executed. No outcome-dependent rewrite of the schedule.
        public=[{k:v for k,v in x.items() if k!="source"} for x in choices]
        (out/"CANDIDATES_BEFORE_NATIVE.json").write_text(
            json.dumps(public,indent=2,sort_keys=True)+"\n")
        result["candidate_schedule_sha256"]=sha(
            json.dumps(public,sort_keys=True).encode())
        if len({x["source_sha256"] for x in choices})!=len(choices):
            result["status"]="UNKNOWN_DUPLICATE_SOURCE_CANDIDATES"
            return result
        for i,choice in enumerate(choices):
            if time.monotonic()-started>850:
                result["status"]="UNKNOWN_SEARCH_TIME_BUDGET"
                return result
            outcome=old_controls.controls(run,world,role["production"],original,
                       choice["source"],row["protected_nodes"],out/("candidate-"+str(i)))
            strict=outcome.get("status")=="WARRANTED_BOUNDED_TRAINING_REPAIR_ONLY"
            if strict:
                runs=[x for _,x in outcome.get("attempts",[])]
                runs+=[outcome.get("full_author_file",{}),
                       outcome.get("withdrawn",{}),outcome.get("restored",{})]
                strict=all(z.get("counts",{}).get("skipped")==0 for z in runs)
            result["candidate_results"].append({
                "identity":choice["identity"],"method":choice["method"],
                "source_sha256":choice["source_sha256"],
                "native_status":outcome.get("status"),
                "causal_scope_pass":strict,
                "native":outcome
            })
            if sha((world/role["production"]).read_bytes())!=sha(original):
                raise ValueError("UNKNOWN_REPAIR_WORKTREE_NOT_RESTORED")
            if strict:
                result["status"]="WARRANTED_BOUNDED_NEW_TRAINING_REPAIR_FUTURE_SEALED"
                result["winning_candidate_id"]=choice["identity"]
                return result
        result["status"]="UNKNOWN_NO_VERIFIED_FROZEN_METHOD_REPAIR"
        return result
    except Exception as exc:
        result["status"]="UNKNOWN_OBSERVATION_CHOICE_APPARATUS"
        result["reason"]=type(exc).__name__+":"+str(exc)[:550]
        return result
    finally:
        result["elapsed_seconds"]=round(time.monotonic()-started,4)
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True,default=repr)+"\n")

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: g2_v5_choose_observation.py ADMISSION_RESULT FRESH_OUTPUT")
    result=main(sys.argv[1],sys.argv[2])
    print("V5_OBSERVATION_CHOICE",result["status"],"FUTURE",result["future"],"G2",result["G2"],flush=True)
    if result["status"]=="UNKNOWN_OBSERVATION_CHOICE_APPARATUS":
        raise SystemExit(2)
