"""V13 source-exposed test of observation -> *unchanged* V104/MSI ranking.

Protected original tests, original source and original V9/V10/V12 verdicts are
unaltered. Candidate ranking gets only independently repeated source-derived
branch observations from this disclosed, exposed training source. A result is
NEVER prospective G2 or an independently constructed new repair.
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

from . import qualify_source_bound_g2_v9 as v9
from . import qualify_typed_v104_prospective_v7 as v7
from . import typed_v104_msi_bridge_v7 as bridge
from . import typed_native_authority_v10 as native
from . import observed_branch_v13 as observed

HERE=Path(__file__).resolve().parent
FROZEN=HERE/"archaeology/typed-v104-v13/FROZEN_BRANCH_PROTOCOL.json"
FROZEN_BLOB="5985d2a0a81e27bf8003a63985d09634bf4d26db"
SCHEMA="UDM_V13_EXPOSED_NATIVE_BRANCH_OBSERVATION_AND_MSI_ACTIVATION"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def run(dest):
    if os.environ.get("UDM_V13_EXPOSED")!="EXPOSED_OBSERVATION_ONLY":
        raise ValueError("V13 must remain original-source exposed diagnostic")
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        raise ValueError("no GitHub token may be injected into public source test")
    actual=subprocess.check_output(["git","hash-object",str(FROZEN)],text=True).strip()
    if actual!=FROZEN_BLOB:
        raise ValueError("V13 frozen source-observation protocol mutated")
    p=json.loads(FROZEN.read_text())
    if p["schema"]!="UDM_V13_EXPOSED_SOURCE_DERIVED_BRANCH_OBSERVATION" or p["verdicts"]["G2"]!="UNKNOWN":
        raise ValueError("source observation G2 authority changed")
    if (p["costs"]["protected_native_verifier_calls"]!=2 or
            p["costs"]["observer_native_calls"]!=2):
        raise ValueError("independent native observation budget modified")
    taskrecord=v9.frozen()
    task=taskrecord["task_roles"][0]
    ref=taskrecord["frozen_author_test_git_blob_refs"][0]
    if task["repository"]!="jd/tenacity" or ref["repository"]!="jd/tenacity":
        raise ValueError("original exposed source identity differs")
    native.verified_v6_source()
    root=Path(dest).absolute()
    if root.exists() or root.resolve()!=root:
        raise ValueError("new output root required")
    root.mkdir(parents=True)
    started=time.monotonic()
    result={
        "schema":SCHEMA,"status":"UNKNOWN_NO_NATIVE_OBSERVATION",
        "source_exposed":True,"source_role":"ORIGINAL_EXPOSED_TENACITY_ONLY",
        "packaging_source_opened":False,
        "original_repaired_head_fetched":False,
        "native_calls":0,
        "observation":None,"catalog":None,
        "original_V9_sci_RED":38985251065,
        "original_V11_sci_RED":38986306451,
        "original_V12_sci_RED":39013082924,
        "V12_human_successes":["NONE_OR_ZERO","CALLABILITY"],
        "no_new_operator_synthesis":True,
        "comparators":"NOT_RUN_NONPROSPECTIVE",
        "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN"
    }
    try:
        prepared=v7.prepare_task(task,ref,root/"source")
        repo=Path(prepared["repo"])
        context=bridge.construct_candidate(repo,task["base"],[prepared["test"]],
                                           {"replacements":[]},root/"baseline-commit")
        wanted=tuple(context["required"])
        if not wanted or not all(native.accepts_class_method(x) for x in wanted):
            raise ValueError("original source-bound protected test nodes not qualified")
        stage=native.stage(repo,context["candidate_commit"],root/"native-stage")
        results=[]
        for _ in range(2):
            entry=native.run_protected(repo,context["candidate_commit"],root/"native-stage",
                required=wanted,paths=tuple(task["author_tests"]),timeout=90,
                interpreter=sys.executable)
            results.append(entry)
            result["native_calls"]+=entry.get("native_calls",0)
        verified=v9.replayed(*results)
        result["baseline"]={
          "first":{k:results[0].get(k) for k in ("status","junit","native_exit","native_calls","executed","imported_project_files")},
          "second":{k:results[1].get(k) for k in ("status","junit","native_exit","native_calls","executed","imported_project_files")},
          "status":verified,
          "typed_manifest_sha256":stage["typed_manifest_sha256"]
        }
        if verified!=v9.BAD:
            result["status"]="UNKNOWN_NO_INDEPENDENT_PROTECTED_FAIL"
            return result
        traces=[]
        for index in range(2):
            trace=observed.run_observer(repo,context["candidate_commit"],root/"native-stage",
                       production_paths=tuple(task["production"]),
                       required=wanted,testpaths=tuple(task["author_tests"]),
                       interpreter=sys.executable,timeout=90)
            result["native_calls"]+=trace.get("native_calls",0)
            traces.append(trace)
        result["trace_replays"]=traces
        if (result["native_calls"]!=4 or
                any(x["status"]!="OBSERVED_PROTECTED_FAILURE_BRANCH_EDGE" for x in traces)):
            result["status"]="UNKNOWN_NO_REPEATED_SOURCE_DERIVED_BRANCH_WITNESS"
            return result
        if (traces[0]["events"]!=traces[1]["events"] or
                traces[0]["source_manifest_sha256"]!=traces[1]["source_manifest_sha256"]
                or traces[0]["source_original_guard_sha256"]!=traces[1]["source_original_guard_sha256"]):
            result["status"]="UNKNOWN_BRANCH_TRACE_REPLAY_MISMATCH"
            return result
        source=stage["typed_manifest_sha256"]
        if traces[0]["source_manifest_sha256"]!=source:
            result["status"]="UNKNOWN_SOURCE_BINDING"
            return result
        # Original AST slots and actual trace, never a target-specific line.
        evidence={}
        for x in traces[0]["events"]:
            evidence.setdefault(x["path"],set()).add(int(x["line"]))
        evidence={key:sorted(lines) for key,lines in sorted(evidence.items())}
        result["observation"]={
          "status":"WARRANTED_BOUNDED_EXECUTED_BRANCH_EDGE_NOT_UNIQUE_CAUSATION",
          "observed_path_lines":evidence,
          "events":traces[0]["events"],
          "native_trace_calls":2,
          "original_protected_verification_calls":2,
          "original_typed_manifest_sha256":source,
          "events_sha256":digest(observed._canonical(traces[0]["events"]).encode()),
          "no_hardcoded_guard_location":True,
          "source_observation_authority":observed.SOURCE_OBSERVATION_AUTHORITY
        }
        triskelion=Path(os.environ["UDM_V7_TRISKELION"])
        msi=Path(os.environ["UDM_V7_MSI"])
        cold=bridge.catalog_v104_typed(repo,task["base"],tuple(task["production"]),
                                      triskelion,msi,cap=64,observation={})
        informed=bridge.catalog_v104_typed(repo,task["base"],tuple(task["production"]),
                                          triskelion,msi,cap=64,observation=evidence)
        if (cold["source"]!=informed["source"] or
                cold["original_typed_source_sha256"]!=informed["original_typed_source_sha256"]
                or [x["id"] for x in cold["rows"]]!=[x["id"] for x in informed["rows"]]
                or len(cold["orders"])!=37 or len(informed["orders"])!=37):
            result["status"]="UNKNOWN_ORIGINAL_LANGUAGE_INTEGRITY"
            return result
        altered=[{"id":x["id"],"path":x["path"],"changed_lines":x["changed_lines"],
                  "old_K":y["features"]["K"],"new_K":x["features"]["K"]}
                 for y,x in zip(cold["rows"],informed["rows"])
                 if y["features"]["K"]!=x["features"]["K"]]
        order_changed=[key for key in cold["orders"]
                       if cold["orders"][key][:8]!=informed["orders"][key][:8]]
        original_reach=sum(any(int(lineno) in row["changed_lines"]
                   for path,values in evidence.items()
                   if path==row["path"] for lineno in values)
                   for row in informed["rows"])
        result["catalog"]={
          "source":"UNCHANGED_ORIGINAL_V104_AND_MSI",
          "cold_catalog_size":len(cold["rows"]),
          "observation_catalog_size":len(informed["rows"]),
          "original_msi_policy_count":len(cold["orders"]),
          "changed_K_count":len(altered),
          "changed_prefix_policy_count":len(order_changed),
          "example_affected_features":altered[:10],
          "observed_guard_reached_by_emitted_v104_candidate_count":original_reach,
          "old_default_K_universal":all(x["features"]["K"]==1000000 for x in cold["rows"]),
          "new_K_source_bound":bool(altered),
          "observation_only_no_new_candidates":True,
          "candidate_ids_unchanged":True
        }
        result["status"]=(
          "WARRANTED_BOUNDED_EXPOSED_BRANCH_OBSERVATION_IN_MSI"
          if altered else "UNKNOWN_OBSERVATION_NOT_ACTIVATED_IN_ORIGINAL_CATALOG")
        return result
    except Exception as error:
        result["status"]="UNKNOWN_EXPOSED_OBSERVER_APPARATUS"
        result["error"]=type(error).__name__+": "+str(error)
        result["traceback_tail"]=traceback.format_exc(limit=8)[-2500:]
        return result
    finally:
        result["elapsed_seconds"]=time.monotonic()-started
        (root/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    output=Path(os.environ["UDM_V13_OUT"])
    r=run(output)
    print(json.dumps({
       "status":r["status"],"native_calls":r["native_calls"],
       "observation":r.get("observation"),
       "catalog":r.get("catalog"),"packaging_source_opened":False,
       "G2":"UNKNOWN"
    },sort_keys=True))
    raise SystemExit(0 if r["status"]=="WARRANTED_BOUNDED_EXPOSED_BRANCH_OBSERVATION_IN_MSI" else 2)
