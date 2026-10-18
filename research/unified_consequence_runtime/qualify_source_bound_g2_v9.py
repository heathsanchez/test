"""V9 source-hidden prospective G2: original V104 policy -> MSI selection -> heldout.

This is a NEW preregistration after the Click V7/V8 diagnostic, with explicit
adaptivity disclosure. Inputs are only exact original base Git source and exact
head-authored test Git blobs. Previously reserved Tenacity becomes training;
previously reserved Packaging remains unopened unless training warrants its use.

The source language, MSI orders, Pareto chooser, typed native executor, MDA
research ledger, and underlying verifiers are unchanged. Unwarranted training,
incomplete profiles, partial test coverage or missing comparison retain UNKNOWN.
G3, G4, G5, G6 always remain UNKNOWN here.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from . import qualify_typed_v104_prospective_v7 as original
from . import typed_v104_msi_bridge_v7 as bridge
from . import typed_native_authority_v6 as native
from .developmental_choice import profile_binding, choose_verified_profiles

HERE=Path(__file__).resolve().parent
FREEZE=HERE/"archaeology/typed-v104-v9/FROZEN_PROTOCOL.json"
SCHEMA="UDM_V9_SOURCE_BOUND_G2_PROSPECTIVE_RUN"
PROTOCOL_SCHEMA="UDM_V9_SOURCE_BOUND_G2_PROSPECTIVE_FREEZE"
FROZEN_GIT_BLOB="0ee57b34091ab9abf4ffa9f7e5a8acf8aa1c457a"
V104_SOURCE="ORIGINAL_PINNED_V104"
MSI_SOURCE="ORIGINAL_PINNED_MSI_V10"
G3=G4=G5=G6="UNKNOWN"
COLD="COLD_V104_ORDER"
GOOD="VERIFIED_REPEATED_PASS_SCOPED_NATIVE"
BAD="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED"
UNVERIFIED="UNKNOWN_NATIVE_EVIDENCE"


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)


def sha(obj):
    raw=obj if isinstance(obj,bytes) else canonical(obj).encode()
    return hashlib.sha256(raw).hexdigest()


def frozen():
    if subprocess.check_output(["git","hash-object",str(FREEZE)],text=True).strip()!=FROZEN_GIT_BLOB:
        raise ValueError("frozen source-hidden experiment was altered")
    result=json.loads(FREEZE.read_text())
    if result.get("schema")!=PROTOCOL_SCHEMA or result.get("parent")!="e3ac262c379fc90687e25eba9ba4a2249db02f4c":
        raise ValueError("frozen V9 protocol identity mismatch")
    if ([x.get("role") for x in result.get("task_roles",[])]
            !=["TRAINING","HELDOUT_FUTURE"] or
            [x.get("repository") for x in result["task_roles"]]
            !=["jd/tenacity","pypa/packaging"]):
        raise ValueError("frozen source roles changed")
    if result["budget"]["search_horizon_per_policy"]!=8 or (
            result["method_pins"]["original_v104"]!="426c54f7c774560e0fabe7213c5ef333b1327c71" or
            result["method_pins"]["original_msi_v10"]!="56cfd7b523e3592cae4eafa5468f437ccb94dbe9"):
        raise ValueError("source-qualified V104/MSI grammar altered")
    # Read-only compatibility view used by frozen acceptance contracts.
    return dict(result,source_pins=result["method_pins"])


def schedule(orders,horizon):
    """Independent of prospective outcomes; one real native receipt per ID."""
    if not isinstance(orders,dict) or COLD not in orders or not isinstance(horizon,int) or horizon<1:
        raise ValueError("original policy orders absent")
    names=[COLD,*sorted(name for name in orders if name!=COLD)]
    rows=[];seen=set()
    for index in range(horizon):
        for name in names:
            candidates=orders[name]
            if len(candidates)<=index:
                continue
            key=candidates[index]
            if key not in seen:
                seen.add(key);rows.append(key)
    return rows


def replayed(a,b):
    """Only independently observed exact native replay can enter a policy vector."""
    if not all(isinstance(x,dict) and x.get("native_calls")==1
               and x.get("native_exit") is not None for x in (a,b)):
        return UNVERIFIED
    shared=("required","executed","deselected","imported_project_files",
            "typed_manifest_sha256")
    if any(a.get(k)!=b.get(k) for k in shared):
        return UNVERIFIED
    if a.get("deselected") or b.get("deselected") or not a.get("executed"):
        return UNVERIFIED
    for x in (a,b):
        if any(not any(y==req or y.startswith(req+"[") or y.startswith(req+"::")
                       for y in x["executed"])
               for req in x["required"]):
            return UNVERIFIED
    if a["status"]==b["status"]=="PASS_SCOPED_NATIVE" and a["native_exit"]==b["native_exit"]==0:
        return GOOD
    if a["status"]==b["status"]=="FAIL_NATIVE_PROTECTED" and a["native_exit"]==b["native_exit"]==1:
        return BAD
    return UNVERIFIED


def profile(order,events,horizon):
    if not isinstance(order,(list,tuple)) or len(order)<horizon:
        return None
    for i,key in enumerate(order[:horizon]):
        state=events.get(key)
        if state==GOOD:
            return [0,2*(i+1)]
        if state!=BAD:
            return None
    return [1,2*horizon]


def authorize_future(choice,cold):
    return (isinstance(choice,dict) and
            choice.get("status")=="AUTHORIZED_REPAIR" and
            isinstance(choice.get("selected"),str) and
            choice["selected"]!=cold)


def g2_verdict(record):
    """Verdict over *internally verified* event record, never an input authority."""
    if not isinstance(record,dict):return "UNKNOWN"
    cold=record.get("cold_profile")
    selected=record.get("selected_profile")
    if (cold!=[1,16] or not isinstance(selected,list)
            or len(selected)!=2 or selected[0]!=0 or selected[1] not in range(2,17,2)):
        return "UNKNOWN"
    if not all(record.get(k) is True for k in (
            "removal_replayed","restoration_replayed",
            "physical_program_removed","independent_future_native")):
        return "UNKNOWN"
    return "WARRANTED_BOUNDED_PROSPECTIVE_G2"


def _native(repo,base,author,candidate,out,task,timeout):
    """Same frozen old source/candidate plus native process twice.

    The runner's *entire fixed author test file* is executed; its actual
    collection, executed calls and imports are source-hashed. This is not a
    complete upstream test suite. Zero calls on setup refusal remain UNKNOWN.
    """
    started=time.monotonic()
    out=Path(out).absolute()
    if out.exists():raise ValueError("native evidence output must not preexist")
    out.mkdir(parents=True)
    context=bridge.construct_candidate(repo,base,[author],candidate,out/"worktree")
    staged=native.stage(repo,context["candidate_commit"],out/"stage")
    required=tuple(context["required"])
    paths=tuple(task["author_tests"])
    observed=[]
    for _ in range(2):
        observed.append(native.run_protected(repo,context["candidate_commit"],out/"stage",
                                             required=required,paths=paths,
                                             interpreter=sys.executable,timeout=timeout))
    post=native.verify_stage(repo,context["candidate_commit"],out/"stage")
    verdict=replayed(*observed)
    receipt={
        "schema":"UDM_V9_ACTUAL_SCOPED_NATIVE_DOUBLE_REPLAY",
        "status":verdict,
        "measured_statuses":[x["status"] for x in observed],
        "native_calls":sum(x.get("native_calls",0) for x in observed),
        "candidate_source_commit":context["candidate_commit"],
        "candidate_sha256":context["candidate_sha256"],
        "required":list(required),
        "paths":list(paths),
        "stage":post["status"],
        "source_manifest_sha256":staged["typed_manifest_sha256"],
        "executed":observed[0].get("executed",[]),
        "junit_first":observed[0].get("junit"),
        "junit_second":observed[1].get("junit"),
        "imported_project_first":observed[0].get("imported_project_files",[]),
        "imported_project_second":observed[1].get("imported_project_files",[]),
        "native_first":observed[0],
        "native_second":observed[1],
        "elapsed_seconds":time.monotonic()-started,
    }
    receipt["evidence_sha256"]=sha(receipt)
    return receipt


def _observation(repo,base,author,candidate,out,task,deadline_seconds):
    try:
        return _native(repo,base,author,candidate,out,task,deadline_seconds)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        # Conservative two-call budget charge: even partially failed launches
        # may have reached a native subprocess. No imaginary positive receipts.
        return {"status":UNVERIFIED,"native_calls":2,
                "reason":type(error).__name__+": "+str(error),"evidence_sha256":None,
                "elapsed_seconds":0,"conservative_budget_charge":True}


def _source_task(task,ref,out):
    # Reuse original audited V7 exact original base + head TEST blob transport.
    return original.prepare_task(task,ref,out)


def _original_catalog(repo,base,task):
    rows=bridge.catalog_v104_typed(repo,base,task["production"],
                    Path(os.environ["UDM_V7_TRISKELION"]),
                    Path(os.environ["UDM_V7_MSI"]),cap=64,observation={})
    if rows["source"]["v104_language"]!=V104_SOURCE or rows["source"]["msi_policy"]!=MSI_SOURCE:
        raise ValueError("original source method silently substituted")
    if len(rows["orders"])!=37 or COLD not in rows["orders"]:
        raise ValueError("incomplete original MSI policy language")
    return rows


def _select(rows,states,evidence,protocol_sha):
    names=tuple(rows["orders"])
    futures=("TRAINING",)
    carrier={}
    for name in names:
        metric=profile(rows["orders"][name],states,8)
        if metric is None:
            return {"status":"UNKNOWN_INCOMPLETE_POLICY_NATIVE_PROFILES",
                    "complete":len(carrier),"expected":len(names),"G2":"UNKNOWN"}
        carrier[name]={"TRAINING":metric}
    source_scope={"protocol_binding":protocol_sha,
                  "candidate_catalog_sha256":sha([r["id"] for r in rows["rows"]]),
                  "source_binding":rows["original_typed_source_sha256"],
                  "budget":8,"native_evidence_sha256":sha(evidence)}
    bound=profile_binding(names,futures,carrier,scope=source_scope)
    choice=choose_verified_profiles(Path(__file__).resolve().parents[2],
                                    names,futures,carrier,evidence_binding=bound)
    return {"status":choice["status"],"choice":choice,
            "profiles":carrier,"scope":source_scope,
            "G2":"UNKNOWN"}


def _prepare_frozen(role,p,root):
    task=p["task_roles"][role]
    ref=p["frozen_author_test_git_blob_refs"][role]
    if (ref["repository"]!=task["repository"]
            or ref["head_commit"]!=task["head"]
            or ref["path"] not in task["author_tests"]):
        raise ValueError("independent HEAD author-test blob pointer has been changed")
    return task,ref,_source_task(task,ref,root/"source")


def _execute_training(result,p,baseout):
    start=time.monotonic();training={"role":"TRAINING","status":"UNKNOWN",
                                      "candidate_evaluations":[],"native_calls":0}
    result["training"]=training
    task,ref,prepared=_prepare_frozen(0,p,baseout)
    training["source_opened"]=True
    training["source_receipt"]=prepared["source_receipt"]
    repo=prepared["repo"];author=prepared["test"];base=task["base"]
    baseline=_observation(repo,base,author,{"replacements":[]},baseout/"baseline",
                          task,p["budget"]["max_seconds_per_native_call"])
    training["baseline"]={k:v for k,v in baseline.items() if k not in ("native_first","native_second")}
    training["native_calls"]+=baseline["native_calls"]
    result["native_calls"]+=baseline["native_calls"]
    if baseline["status"]!=BAD:
        training["status"]="UNKNOWN_NO_AUTHENTIC_TRAINING_PROTECTED_FAILURE"
        return None
    cat=_original_catalog(repo,base,task)
    catalog_sha=sha(cat)
    plans={"schema":"UDM_V9_PRE_NATIVE_TRAINING_CATALOG",
           "method_source":cat["source"],"original_git_manifest":cat["original_typed_source_sha256"],
           "catalog_sha256":catalog_sha,"policy_orders":cat["orders"],
           "candidate_ids":[r["id"] for r in cat["rows"]],
           "candidate_count":len(cat["rows"]),"horizon":8}
    (baseout/"POLICIES_BEFORE_NATIVE.json").write_text(json.dumps(plans,sort_keys=True,indent=2)+"\n")
    training["catalog_sha256"]=catalog_sha;training["policy_count"]=len(cat["orders"])
    training["emitted_count"]=len(cat["rows"])
    index={r["id"]:r for r in cat["rows"]}
    schedule_order=schedule(cat["orders"],8)
    training["scheduled_candidates"]=len(schedule_order)
    states={};evidence={}
    maxcalls=p["budget"]["max_native_calls_training"]
    for key in schedule_order:
        if (training["native_calls"]+2>maxcalls
                or time.monotonic()-start>p["budget"]["training_wall_seconds"]):
            training["budget_exhausted"]=True
            break
        row=index[key]
        receipt=_observation(repo,base,author,row["candidate"],
                            baseout/"candidate-"+str(len(states)).zfill(3),
                            task,p["budget"]["max_seconds_per_native_call"])
        training["native_calls"]+=receipt["native_calls"]
        result["native_calls"]+=receipt["native_calls"]
        states[key]=receipt["status"]
        evidence[key]=receipt.get("evidence_sha256")
        training["candidate_evaluations"].append({
            "id":key,"status":receipt["status"],"native_calls":receipt["native_calls"],
            "builder":row["builder"],"selector":row["selector"],
            "elapsed_seconds":receipt.get("elapsed_seconds"),
            "evidence_sha256":receipt.get("evidence_sha256"),
            "reason":receipt.get("reason")})
    training["state_counts"]={k:list(states.values()).count(k) for k in sorted(set(states.values()))}
    choice=_select(cat,states,evidence,sha(FREEZE.read_bytes()))
    training["choice"]=choice
    training["status"]="TRAINING_"+choice["status"]
    if not authorize_future(choice.get("choice"),COLD):
        return None
    selected=choice["choice"]["selected"]
    if (choice["profiles"][COLD]["TRAINING"]!=[1,16] or
            choice["profiles"][selected]["TRAINING"][0]!=0):
        training["status"]="UNKNOWN_NO_TRAINING_CAUSAL_POLICY_WITNESS"
        return None
    training["status"]="TRAINING_UNIQUE_NONCOLD_ORIGINAL_MSI_POLICY"
    return selected


def _execute_future(result,p,out,selected):
    start=time.monotonic()
    future={"role":"HELDOUT_FUTURE","status":"UNKNOWN",
            "source_opened":False,"native_calls":0,"removal_replayed":False,
            "restoration_replayed":False,"physical_program_removed":False}
    result["future"]=future
    task,ref,prepared=_prepare_frozen(1,p,out)
    future["source_opened"]=True
    result["unopened_heldout"]=False
    future["source_receipt"]=prepared["source_receipt"]
    repo=prepared["repo"];base=task["base"];author=prepared["test"]
    baseline=_observation(repo,base,author,{"replacements":[]},out/"baseline",
                          task,p["budget"]["max_seconds_per_native_call"])
    future["native_calls"]+=baseline["native_calls"]
    result["native_calls"]+=baseline["native_calls"]
    future["baseline"]={k:v for k,v in baseline.items() if k not in ("native_first","native_second")}
    if baseline["status"]!=BAD:
        future["status"]="UNKNOWN_NO_AUTHENTIC_FUTURE_PROTECTED_FAILURE"
        return
    cat=_original_catalog(repo,base,task)
    if selected not in cat["orders"]:
        future["status"]="UNKNOWN_SELECTED_POLICY_NOT_APPLICABLE"
        return
    cold=cat["orders"][COLD][:8]
    warm=cat["orders"][selected][:8]
    if len(cold)!=8 or len(warm)!=8:
        future["status"]="UNKNOWN_INSUFFICIENT_SOURCE_METHODS"
        return
    union=[];seen=set()
    for key in cold+warm:
        if key not in seen:
            seen.add(key);union.append(key)
    frontier={"schema":"UDM_V9_PRE_NATIVE_HELDOUT_POLICY_COMMIT",
              "source_sha256":cat["original_typed_source_sha256"],
              "catalog_sha256":sha(cat),"selected_from_training":selected,
              "cold_order":cold,"warm_order":warm,
              "execution_order":union,
              "original_v104":V104_SOURCE,"original_msi":MSI_SOURCE}
    (out/"POLICIES_BEFORE_NATIVE.json").write_text(json.dumps(frontier,indent=2,sort_keys=True)+"\n")
    index={row["id"]:row for row in cat["rows"]}
    events={}
    for key in union:
        if (future["native_calls"]+2>p["budget"]["max_native_calls_heldout"]
                or time.monotonic()-start>p["budget"]["heldout_wall_seconds"]):
            future["status"]="UNKNOWN_FUTURE_NATIVE_BUDGET"
            return
        receipt=_observation(repo,base,author,index[key]["candidate"],
                            out/"candidate-"+str(len(events)).zfill(3),task,
                            p["budget"]["max_seconds_per_native_call"])
        events[key]=receipt["status"]
        future["native_calls"]+=receipt["native_calls"]
        result["native_calls"]+=receipt["native_calls"]
    cold_profile=profile(cold,events,8);warm_profile=profile(warm,events,8)
    future.update(cold_profile=cold_profile,selected_profile=warm_profile,
                  observations={k:events[k] for k in sorted(events)})
    if cold_profile!=[1,16] or not warm_profile or warm_profile[0]!=0:
        future["status"]="UNKNOWN_NO_PROTECTED_FUTURE_CAUSAL_ADVANTAGE"
        return
    # Physically withdraw the selected method from the finite executable
    # dispatch table, rerun cold from scratch in separate native processes.
    programs={selected:tuple(warm)}
    removed=programs.pop(selected)
    assert selected not in programs and removed==tuple(warm)
    future["physical_program_removed"]=True
    refreshed={}
    for key in cold:
        if future["native_calls"]+2>p["budget"]["max_native_calls_heldout"]:
            future["status"]="UNKNOWN_NO_BUDGET_FOR_PHYSICAL_ABLATION"
            return
        event=_observation(repo,base,author,index[key]["candidate"],
                           out/"removal-"+str(len(refreshed)).zfill(3),task,
                           p["budget"]["max_seconds_per_native_call"])
        refreshed[key]=event["status"];future["native_calls"]+=event["native_calls"]
        result["native_calls"]+=event["native_calls"]
    if profile(cold,refreshed,8)!=[1,16]:
        future["status"]="UNKNOWN_ABLATION_NONFAILURE"
        return
    future["removal_replayed"]=True
    # Restore exactly the source-pinned learned MSI policy executable, then
    # independently requalify its first native winner by two fresh subprocesses.
    rebuilt=_original_catalog(repo,base,task)
    if rebuilt["orders"][selected][:8]!=warm:
        future["status"]="UNKNOWN_RESTORED_POLICY_SOURCE_CHANGED"
        return
    programs[selected]=tuple(warm)
    winner=next((x for x in warm if events[x]==GOOD),None)
    if winner is None or future["native_calls"]+2>p["budget"]["max_native_calls_heldout"]:
        future["status"]="UNKNOWN_RESTORATION_BUDGET_OR_WITNESS"
        return
    restore_index={row["id"]:row for row in rebuilt["rows"]}
    again=_observation(repo,base,author,restore_index[winner]["candidate"],
                       out/"restored-verified",task,
                       p["budget"]["max_seconds_per_native_call"])
    future["native_calls"]+=again["native_calls"];result["native_calls"]+=again["native_calls"]
    if again["status"]!=GOOD:
        future["status"]="UNKNOWN_RESTORATION_NOT_REVERIFIED"
        return
    future["restoration_replayed"]=True
    future["independent_future_native"]=True
    future["status"]=g2_verdict(future)


def run(dest):
    if os.environ.get("UDM_V9_EXPLICIT_SOURCE_ACCESS")!="YES_AFTER_FROZEN_CI":
        raise ValueError("V9 source unsealing requires the frozen CI guard")
    p=frozen()
    root=Path(dest).absolute()
    if not root.is_absolute() or root.exists() or root.is_relative_to(HERE):
        raise ValueError("fresh external research output directory required")
    root.mkdir(parents=True)
    start=time.monotonic()
    report={"schema":SCHEMA,"status":"UNKNOWN","G2":"UNKNOWN",
            "G3":G3,"G4":G4,"G5":G5,"G6":G6,
            "protocol_sha256":sha(FREEZE.read_bytes()),
            "frozen_contract_git_blob":FROZEN_GIT_BLOB,
            "source_parent":p["parent"],"native_calls":0,
            "unopened_heldout":True,"training_verified_choice":False,
            "informed_executable_ledger":"NOT_RUN_NO_WARRANTED_FUTURE",
            "coding_agent":"NOT_RUN_NO_EXTERNAL_MODEL_CREDENTIALS",
            "task_role_change":"DISCLOSED_ADAPTIVE_AFTER_V7_CLICK_RED",
            "source_repair_heads_not_fetched":True}
    try:
        selected=_execute_training(report,p,root/"training")
        if selected is None:
            report["status"]="UNKNOWN_NO_UNIQUE_SOURCE_BOUND_TRAINING_POLICY"
            return report
        report["training_verified_choice"]=True
        report["trained_policy"]=selected
        # This is the ONLY point the HEAD-authored Packaging test body
        # becomes observable; no future source or repaired head production was
        # used for training method selection.
        _execute_future(report,p,root/"future",selected)
        report["G2"]=report["future"]["status"] if (
            report["future"]["status"]=="WARRANTED_BOUNDED_PROSPECTIVE_G2") else "UNKNOWN"
        report["status"]=(report["G2"] if report["G2"]!="UNKNOWN"
                          else "UNKNOWN_PROSPECTIVE_FUTURE_CAUSAL_TEST")
        return report
    except Exception as error:
        report.update(status="UNKNOWN_NATIVE_SCIENTIFIC_PROCEDURE",
                      obstruction=type(error).__name__+": "+str(error),
                      traceback=traceback.format_exc(limit=12)[-3000:])
        return report
    finally:
        report["wall_seconds"]=time.monotonic()-start
        (root/"RESULT.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    result=run(Path(os.environ["UDM_V9_RESULT_OUT"]))
    print(json.dumps({"schema":result["schema"],"status":result["status"],
                      "G2":result["G2"],"native_calls":result["native_calls"],
                      "unopened_heldout":result["unopened_heldout"]},sort_keys=True))
    raise SystemExit(0 if result["status"]=="WARRANTED_BOUNDED_PROSPECTIVE_G2" else 2)
