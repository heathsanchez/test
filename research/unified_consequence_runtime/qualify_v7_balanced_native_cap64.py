"""Exposed Click balanced original V104 family scheduling: actual native control.

All 64 candidates are source-derived using the ORIGINAL authenticated V104
'allowed' grammar and are frozen before ANY new native candidate result.
Compared with the separately frozen original order under the same 130-call
ceiling. This is a previously exposed diagnostic and may NEVER promote G2.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time

from . import qualify_typed_v104_prospective_v7 as frozen
from . import qualify_v7_exposed_protected_scope as scoped
from . import typed_v104_msi_bridge_v7 as bridge
from . import typed_source_inventory_v5 as typed
from . import v104_family_balance_v7 as balanced

SCHEMA="UDM_V7_EXPOSED_V104_FAMILY_BALANCED_NATIVE_COMPARISON"
CAP=64
MAX_NATIVE=130


def run(out):
    destination=Path(out).absolute()
    if destination.exists():raise ValueError("new immutable diagnostic output required")
    destination.mkdir(parents=True)
    started=time.monotonic()
    result={"schema":SCHEMA,"scope":"EXPOSED_SOURCE_DIAGNOSTIC_ONLY",
            "prior_cold_first8":38977751776,
            "prior_msi_all37":38978292314,
            "prior_full64":38978813909,
            "source_only_balanced":38979430841,
            "status":"UNKNOWN","G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "source":"pallets/click PR3884, already exposed",
            "futures_unopened":["jd/tenacity","pypa/packaging"],
            "native_calls":0,"candidate_evaluations":[]}
    try:
        protocol,refs=frozen.sealed_metadata()
        task,ref=protocol["candidates"][0],refs["refs"][0]
        prepared=frozen.prepare_task(task,ref,destination/"source")
        repo=Path(prepared["repo"])
        base=task["base"]
        production=task["production"]
        if len(production)!=1:
            raise ValueError("frozen exposed balancing requires exactly one original production file")
        path=production[0]
        snapshot=typed.snapshot(repo,base)
        desc=next((x for x in snapshot["manifest"] if x["path"]==path and x["mode"] in typed.REGULAR_MODES),None)
        if desc is None:
            raise ValueError("original production AST missing from immutable typed Git tree")
        raw=typed._git(repo,"cat-file","blob",desc["oid"])
        source=raw.decode("utf-8")
        original=bridge.catalog_v104_typed(repo,base,production,
                    Path(os.environ["UDM_V7_TRISKELION"]),
                    Path(os.environ["UDM_V7_MSI"]),cap=CAP)
        plan=balanced.emit(Path(os.environ["UDM_V7_TRISKELION"]),source,cap=CAP)
        if len(original["rows"])!=CAP or len(plan["rows"])!=CAP:
            raise ValueError("equal fixed 64-emission candidate counts not established")
        original_family={(tuple(x["selector"]),tuple(x["builder"])) for x in original["rows"]}
        balanced_family={(tuple(x["selector"]),tuple(x["builder"])) for x in plan["rows"]}
        if len(balanced_family)<=len(original_family):
            raise ValueError("balanced original V104 grammar did not change method-family coverage")
        plan_id=hashlib.sha256(json.dumps(
               [{"selector":row["selector"],"builder":row["builder"],
                 "slot_rank":row["slot_rank"],"id":row["id"]}
                 for row in plan["rows"]],sort_keys=True).encode()).hexdigest()
        result.update(original_cap64_family_count=len(original_family),
                      balanced_cap64_family_count=len(balanced_family),
                      fixed_balanced_frontier_sha256=plan_id,
                      original_source_sha256=hashlib.sha256(raw).hexdigest(),
                      original_typed_source_manifest_sha256=snapshot["manifest_sha256"],
                      balanced_original_program_calls=plan["program_generator_calls"],
                      balanced_source_only_wall_seconds=time.monotonic()-started)
        frontier={"schema":"UDM_EXPOSED_BALANCED_PRENATIVE_FRONTIER",
                  "original_source_sha256":result["original_source_sha256"],
                  "balanced_source_pin":plan["source_pin"],
                  "cap":CAP,
                  "balanced_families":len(balanced_family),
                  "original_families":len(original_family),
                  "candidate_ids":[row["id"] for row in plan["rows"]],
                  "candidate_sha256":plan_id,
                  "native_calls_so_far":0,
                  "scientific_G2":"UNKNOWN"}
        (destination/"FROZEN_BALANCED_CANDIDATES_BEFORE_NATIVE.json").write_text(
                    json.dumps(frontier,sort_keys=True,indent=2)+"\n")
        original_cold=bridge.construct_candidate(repo,base,[prepared["test"]],
                    {"replacements":[]},destination/"baseline-worktree")
        baseline=scoped.measured(repo,original_cold["candidate_commit"],
                     tuple(original_cold["required"]),destination/"baseline-native",
                     tuple(task["author_tests"]))
        result["baseline"]={"first":baseline["first"]["status"],
                            "second":baseline["second"]["status"],
                            "junit":baseline["first"]["junit"],
                            "native_calls":baseline["native_calls"]}
        result["native_calls"]+=baseline["native_calls"]
        if not (baseline["first"]["status"]==
                baseline["second"]["status"]=="FAIL_NATIVE_PROTECTED"):
            result["status"]="UNKNOWN_NO_REPEATED_PROTECTED_BASELINE_FAILURE"
            return result
        for idx,row in enumerate(plan["rows"]):
            if result["native_calls"]+2>MAX_NATIVE:
                result["status"]="UNKNOWN_NATIVE_BUDGET_EXHAUSTED"
                return result
            candidate={"replacements":[{"path":path,
                          "original_sha256":desc["sha256"],
                          "replacement":row["replacement"]}]}
            try:
                artifact=bridge.construct_candidate(repo,base,[prepared["test"]],candidate,
                         destination/("candidate-source-"+str(idx).zfill(3)))
                measured=scoped.measured(repo,artifact["candidate_commit"],
                         tuple(artifact["required"]),
                         destination/("native-"+str(idx).zfill(3)),
                         tuple(task["author_tests"]))
                repeat_ok=(measured["first"]["status"]==measured["second"]["status"] and
                    measured["first"]["executed"]==measured["second"]["executed"] and
                    measured["first"]["imported_project_files"]==
                    measured["second"]["imported_project_files"])
                measured_status=("VERIFIED_SCOPED_PASS" if repeat_ok and
                    measured["first"]["status"]=="PASS_SCOPED_NATIVE" else
                    "VERIFIED_SCOPED_FAIL" if repeat_ok and
                    measured["first"]["status"]=="FAIL_NATIVE_PROTECTED" else "UNKNOWN_NATIVE")
                event={"candidate_id":row["id"],"index":idx,
                       "selector":row["selector"],"builder":row["builder"],
                       "status":measured_status,
                       "first":measured["first"]["status"],
                       "second":measured["second"]["status"],
                       "source_commit":artifact["candidate_commit"],
                       "native_calls":measured["native_calls"],
                       "seconds":measured["elapsed_seconds"]}
            except (ValueError, RuntimeError,OSError) as error:
                event={"candidate_id":row["id"],"index":idx,
                       "selector":row["selector"],"builder":row["builder"],
                       "status":"UNKNOWN_CANDIDATE",
                       "reason":type(error).__name__+": "+str(error),
                       "native_calls":0}
            result["candidate_evaluations"].append(event)
            result["native_calls"]+=event["native_calls"]
        states=[row["status"] for row in result["candidate_evaluations"]]
        result["state_counts"]={name:states.count(name) for name in sorted(set(states))}
        result["completed_candidates"]=len(result["candidate_evaluations"])
        result["successful_candidates"]=[x["candidate_id"] for x in result["candidate_evaluations"]
                                          if x["status"]=="VERIFIED_SCOPED_PASS"]
        if any(name.startswith("UNKNOWN") for name in states):
            result["status"]="UNKNOWN_INCOMPLETE_BALANCED_ORIGINAL_NATIVE_CENSUS"
        elif result["successful_candidates"]:
            result["status"]="EXPOSED_BALANCED_ORIGINAL_V104_NATIVE_REPAIRS_EXIST"
        else:
            result["status"]="EXPOSED_BALANCED_ORIGINAL_V104_ALL64_NATIVE_FAILURE"
        return result
    except Exception as error:
        result.update(status="UNKNOWN_EXPOSED_BALANCE_INTERFACE",
                      reason=type(error).__name__+": "+str(error))
        return result
    finally:
        result["wall_seconds"]=time.monotonic()-started
        (destination/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    r=run(Path(os.environ["UDM_V7_BALANCED_NATIVE_OUT"]))
    print(json.dumps({"status":r["status"],"G2":r["G2"],
       "candidate_count":len(r["candidate_evaluations"]),
       "native_calls":r["native_calls"],
       "balanced_families":r.get("balanced_cap64_family_count"),
       "success_count":len(r.get("successful_candidates",[]))},sort_keys=True))
    raise SystemExit(0 if r["status"] in (
        "EXPOSED_BALANCED_ORIGINAL_V104_NATIVE_REPAIRS_EXIST",
        "EXPOSED_BALANCED_ORIGINAL_V104_ALL64_NATIVE_FAILURE") else 2)
