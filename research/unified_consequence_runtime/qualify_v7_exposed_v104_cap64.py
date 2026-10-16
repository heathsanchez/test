"""Exposed-source complete 64-emitted-candidate V104 diagnostic, NEVER G2.

The source and original V104/author-test carrier are already exposed. Exactly
the first 64 candidates emitted by the unchanged original V104 generator are
fixed in order BEFORE any new native candidate outcome. Two independently
checked complete author-file native test executions each. No future source
release, economic advantage, novel operator or unrestricted grammar claim.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time

from . import qualify_typed_v104_prospective_v7 as old
from . import typed_v104_msi_bridge_v7 as bridge
from . import qualify_v7_exposed_protected_scope as diagnosis
from .developmental_choice import profile_binding, choose_verified_profiles

SCHEMA="UDM_V7_EXPOSED_V104_EMITTED_CAP64_CENSUS"
TOTAL_NATIVE_BUDGET=130
HORIZON=64


def status(row):
    if row.get("native_calls")!=2:
        return "UNKNOWN"
    one=row["first"];two=row["second"]
    if (one["native_calls"]!=two["native_calls"] or
            one.get("executed")!=two.get("executed") or
            one.get("imported_project_files")!=two.get("imported_project_files")
            or one.get("required")!=two.get("required")
            or one.get("deselected") or two.get("deselected")):
        return "UNKNOWN"
    if one["status"]==two["status"]=="FAIL_NATIVE_PROTECTED":
        return "VERIFIED_SCOPED_FAIL"
    if one["status"]==two["status"]=="PASS_SCOPED_NATIVE":
        return "VERIFIED_SCOPED_PASS"
    return "UNKNOWN"


def profile(order,events):
    if len(order)<HORIZON or any(x not in events for x in order[:HORIZON]):
        return None
    for pos,ident in enumerate(order[:HORIZON]):
        observed=events[ident]
        if observed=="VERIFIED_SCOPED_PASS":
            if all(events[x]=="VERIFIED_SCOPED_FAIL" for x in order[:pos]):
                return [0,2*(pos+1)]
            return None
        if observed!="VERIFIED_SCOPED_FAIL":
            return None
    return [1,2*HORIZON]


def run(out):
    root=Path(out).absolute()
    if root.exists():raise ValueError("new owned scope-limited output required")
    root.mkdir(parents=True)
    report={"schema":SCHEMA,"state":"EXPOSED_DIAGNOSTIC_ONLY",
            "status":"UNKNOWN","G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "source":"pallets/click PR3884, original baseline + head tests only",
            "full_suite_red_run":38977284706,
            "first_scoped_native_run":38977751776,
            "futures_unopened":["jd/tenacity","pypa/packaging"],
            "no_prospective_claim":True,"native_calls":0,"policy_count":0,
            "native_evaluations":[]}
    started=time.monotonic()
    try:
        protocol,refs=old.sealed_metadata()
        task,ref=protocol["candidates"][0],refs["refs"][0]
        prepared=old.prepare_task(task,ref,root/"input")
        repo=prepared["repo"]
        catalog=bridge.catalog_v104_typed(
             repo,task["base"],task["production"],
             Path(os.environ["UDM_V7_TRISKELION"]),
             Path(os.environ["UDM_V7_MSI"]),cap=64)
        orders=catalog["orders"]
        rows={r["id"]:r for r in catalog["rows"]}
        # Bound the candidate candidate universe BEFORE looking at outcomes.
        plans={name:order[:HORIZON] for name,order in sorted(orders.items())}
        universe=sorted({ident for seq in plans.values() for ident in seq})
        report.update(policy_count=len(plans),row_count=len(rows),
                      eligible_original_operations=len(universe),
                      frozen_plans_sha256=bridge.digest(bridge.canonical(plans).encode()),
                      original_policy_source=catalog["source"],
                      total_native_call_ceiling=TOTAL_NATIVE_BUDGET)
        (root/"POLICY_FRONTIER_BEFORE_NATIVE.json").write_text(json.dumps({
           "schema":"UDM_V7_EXPOSED_MSI_SOURCE_FROZEN_POLICY_FRONTIER",
           "original_manifest_sha256":catalog["original_typed_source_sha256"],
           "original_policy_source":catalog["source"],
           "prefix_horizon":HORIZON,
           "plans":plans,"universe":universe},sort_keys=True,indent=2)+"\n")
        base=bridge.construct_candidate(repo,task["base"],[prepared["test"]],
                      {"replacements":[]},root/"baseline-worktree")
        baseline=diagnosis.measured(repo,base["candidate_commit"],tuple(base["required"]),
                                     root/"baseline-native",tuple(task["author_tests"]))
        report["baseline"]={"first":baseline["first"]["status"],
                             "second":baseline["second"]["status"],
                             "junit":baseline["first"]["junit"],
                             "native_calls":baseline["native_calls"]}
        report["native_calls"]+=baseline["native_calls"]
        if (baseline["first"]["status"]!="FAIL_NATIVE_PROTECTED" or
                baseline["second"]["status"]!="FAIL_NATIVE_PROTECTED"):
            report["status"]="UNKNOWN_NO_AUTHENTIC_PROTECTED_RESIDUAL"
            return report
        observed={}
        for i,ident in enumerate(universe):
            if report["native_calls"]+2>TOTAL_NATIVE_BUDGET:
                observed[ident]="UNKNOWN_BUDGET"
                break
            item=rows[ident]
            try:
                candidate=bridge.construct_candidate(repo,task["base"],[prepared["test"]],
                                item["candidate"],root/("candidate-worktree-"+str(i).zfill(3)))
                result=diagnosis.measured(repo,candidate["candidate_commit"],
                                tuple(candidate["required"]),root/("native-"+str(i).zfill(3)),
                                tuple(task["author_tests"]))
                outcome=status(result)
                record={"id":ident,"selector":item["selector"],"builder":item["builder"],
                        "status":outcome,"first":result["first"]["status"],
                        "second":result["second"]["status"],
                        "source_commit":candidate["candidate_commit"],
                        "elapsed_seconds":result["elapsed_seconds"],
                        "native_calls":result["native_calls"]}
            except (RuntimeError,ValueError,OSError) as error:
                outcome="UNKNOWN_CANDIDATE"
                record={"id":ident,"status":outcome,
                        "reason":type(error).__name__+": "+str(error),"native_calls":0}
            observed[ident]=outcome
            report["native_calls"]+=record["native_calls"]
            report["native_evaluations"].append(record)
        profiles={name:profile(sequence,observed) for name,sequence in plans.items()}
        report["profiles"]=profiles
        missing=[name for name,vector in profiles.items() if vector is None]
        report["complete_policy_count"]=len(profiles)-len(missing)
        report["incomplete_policy_count"]=len(missing)
        report["scope_native_status_counts"]={
            k:list(observed.values()).count(k) for k in sorted(set(observed.values()))}
        if missing:
            report["status"]="UNKNOWN_INCOMPLETE_SOURCE_BOUND_MSI_NATIVE_PROFILE_CENSUS"
            return report
        candidates=tuple(sorted(plans))
        futures=("EXPOSED_CLICK",)
        vectors={c:{"EXPOSED_CLICK":profiles[c]} for c in candidates}
        bound=profile_binding(candidates,futures,vectors,scope={
            "protocol_binding":bridge.digest(old.PROTOCOL.read_bytes()),
            "candidate_catalog_sha256":bridge.digest(bridge.canonical(
               list(rows)).encode()),
            "source_binding":catalog["original_typed_source_sha256"],
            "budget":HORIZON,
            "real_native_evidence_sha256":bridge.digest(bridge.canonical(observed).encode())})
        chooser=choose_verified_profiles(Path(__file__).resolve().parents[2],
                       candidates,futures,vectors,evidence_binding=bound)
        report["original_pareto"]=chooser
        successes=[(name,profiles[name]) for name in profiles if profiles[name][0]==0]
        report["successful_policies"]=successes
        cold=profiles["COLD_V104_ORDER"]
        if cold[0]==1 and not successes:
            report["status"]="EXPOSED_COMPLETE_V104_EMITTED_CAP64_NO_PROTECTED_NATIVE_REPAIR"
        elif successes:
            report["status"]="EXPOSED_V104_EMITTED_CAP64_CONTAINS_SCOPED_NATIVE_REPAIR"
        else:
            report["status"]="UNKNOWN_CAP64_OUTCOME"
        return report
    except Exception as error:
        report.update(status="UNKNOWN_MSI_EXPOSED_DIAGNOSTIC_INTERFACE",
                      reason=type(error).__name__+": "+str(error))
        return report
    finally:
        report["wall_seconds"]=time.monotonic()-started
        (root/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    result=run(Path(os.environ["UDM_V7_MSI_CENSUS_OUT"]))
    print(json.dumps({"state":result["state"],"status":result["status"],
          "G2":result["G2"],"candidate_count":len(result["native_evaluations"]),
          "policies":result["policy_count"],"native_calls":result["native_calls"],
          "successes":result.get("scope_native_status_counts",{}).get("VERIFIED_SCOPED_PASS",0)},
          sort_keys=True))
    raise SystemExit(0 if result["status"] in (
        "EXPOSED_COMPLETE_V104_EMITTED_CAP64_NO_PROTECTED_NATIVE_REPAIR",
        "EXPOSED_V104_EMITTED_CAP64_CONTAINS_SCOPED_NATIVE_REPAIR") else 2)
