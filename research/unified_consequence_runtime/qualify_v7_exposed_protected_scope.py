"""V7.1 exposure-qualified scoped author-test diagnostic; NEVER prospective G2.

Uses the already exposed click PR3884 from frozen V7 protocol. Runs the
original, unmodified native V6 worker on the *entire original author changed
test module*, rather than silently waiving unrelated upstream-suite skip/xfail.
All original tracked bytes and protected node identities remain authenticated.

The original full-suite V7 RED is preserved; this is a scope-distinct claim.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from . import qualify_typed_v104_prospective_v7 as protocol
from . import typed_v104_msi_bridge_v7 as bridge
from . import typed_native_authority_v6 as native


def measured(repo,commit,required,dest,paths):
    started=time.monotonic()
    stage=native.stage(repo,commit,dest)
    one=native.run_protected(repo,commit,dest,required=required,
                              interpreter=sys.executable,paths=paths,timeout=90)
    two=native.run_protected(repo,commit,dest,required=required,
                              interpreter=sys.executable,paths=paths,timeout=90)
    native.verify_stage(repo,commit,dest)
    return {"first":one,"second":two,"stage":stage,"elapsed_seconds":time.monotonic()-started,
            "native_calls":one.get("native_calls",0)+two.get("native_calls",0),
            "status":"WARRANTED_SCOPED_FAIL" if
                one.get("status")==two.get("status")=="FAIL_NATIVE_PROTECTED" and
                one.get("executed")==two.get("executed") and
                one.get("imported_project_files")==two.get("imported_project_files")
                else "UNKNOWN_SCOPED_NATIVE_AUTHORITY",
            "protected_repeated":one.get("required")==two.get("required")==list(required),
            "G2":"UNKNOWN"}


def run(out):
    frozen,refs=protocol.sealed_metadata()
    task=frozen["candidates"][0]
    ref=refs["refs"][0]
    if task["repository"]!="pallets/click" or task["pr"]!=3884:
        raise ValueError("only previous exposed Click diagnostic is authorized")
    root=Path(out).absolute()
    if root.exists():raise ValueError("new diagnostic evidence root required")
    root.mkdir(parents=True)
    result={"schema":"UDM_V7_EXPOSED_PROTECTED_TEST_SCOPE_DIAGNOSTIC",
            "status":"UNKNOWN",
            "role":"EXPOSED_DIAGNOSTIC_ONLY",
            "prior_scientific_red_run":38977284706,
            "prior_full_suite_result":"UNKNOWN_SKIPPED",
            "same_previous_source":True,
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "original_full_suite_claim":"NOT_WARRANTED",
            "untouched_futures":["jd/tenacity","pypa/packaging"],
            "sources_modified":"NO_EXTERNAL_SOURCE_MUTATION"}
    start=time.monotonic()
    try:
        task_out=protocol.prepare_task(task,ref,root/"source")
        repo=task_out["repo"]
        baseline=bridge.construct_candidate(
             repo,task["base"],[task_out["test"]],
             {"replacements":[]},root/"baseline-worktree")
        scope=tuple(task["author_tests"])
        first=measured(repo,baseline["candidate_commit"],tuple(task_out["protected"]),
                       root/"native-baseline",scope)
        result.update(baseline=first,
             protected=task_out["protected"],
             source_manifest_sha256=baseline["typed_manifest_sha256"])
        if first["status"]!="WARRANTED_SCOPED_FAIL":
            result["status"]="UNKNOWN_EXPOSED_SCOPED_TRAINING_RESIDUAL"
            return result
        result["status"]="WARRANTED_SCOPED_NATIVE_FAILURE_EXPOSED_DIAGNOSTIC"
        catalog=bridge.catalog_v104_typed(
            repo,task["base"],task["production"],
            Path(os.environ["UDM_V7_TRISKELION"]),
            Path(os.environ["UDM_V7_MSI"]),cap=64)
        result["catalog_rows"]=len(catalog["rows"])
        result["original_msi_policies"]=len(catalog["orders"])
        order=catalog["orders"]["COLD_V104_ORDER"][:8]
        index={x["id"]:x for x in catalog["rows"]}
        results=[];count=2
        for ident in order:
            row=index[ident]
            try:
                c=bridge.construct_candidate(repo,task["base"],[task_out["test"]],
                                             row["candidate"],
                                             root/("candidate-worktree-"+str(len(results))))
                observed=measured(repo,c["candidate_commit"],tuple(c["required"]),
                                  root/("native-candidate-"+str(len(results))),scope)
                measured_row={"id":ident,"status":observed["status"],
                              "observed_status":observed["first"]["status"],
                              "repeat_status":observed["second"]["status"],
                              "native_calls":observed["native_calls"],
                              "elapsed_seconds":observed["elapsed_seconds"],
                              "source_commit":c["candidate_commit"]}
            except Exception as e:
                measured_row={"id":ident,"status":"UNKNOWN_CANDIDATE_DIAGNOSTIC",
                              "reason":type(e).__name__+": "+str(e),
                              "native_calls":0}
            results.append(measured_row)
            count+=measured_row.get("native_calls",0)
        result["cold_prefix"]=results
        result["native_calls"]=count
        result["status"]="EXPOSED_NATIVE_FAILURE_AND_EIGHT_COLD_V104_CANDIDATES_OBSERVED"
        return result
    except Exception as e:
        result.update(status="UNKNOWN_EXPOSED_SOURCE_OR_NATIVE_INTERFACE",
                      reason=type(e).__name__+": "+str(e))
        return result
    finally:
        result["wall_seconds"]=time.monotonic()-start
        (root/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    r=run(Path(os.environ["UDM_V7_EXPOSED_OUT"]))
    print(json.dumps({"status":r["status"],"G2":r["G2"],
         "native_calls":r.get("native_calls",r.get("baseline",{}).get("native_calls",0)),
         "baseline_first":r.get("baseline",{}).get("first",{}).get("status"),
         "baseline_second":r.get("baseline",{}).get("second",{}).get("status"),
         "eight_cold_count":len(r.get("cold_prefix",[]))},sort_keys=True))
    # Engineering diagnostic green if protected author module reveals a real
    # bounded FAIL and the eight source-defined original proposals ran.
    raise SystemExit(0 if r["status"]==
         "EXPOSED_NATIVE_FAILURE_AND_EIGHT_COLD_V104_CANDIDATES_OBSERVED" else 2)
