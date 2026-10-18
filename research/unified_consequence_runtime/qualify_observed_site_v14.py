"""V14 exposed-only: original V104 emission at a V13 source-observed AST slot.

No new constructor grammar, unknown task exposure, human selected winning edit,
or prospective G2. All protected native outcomes independently repeated by V10.
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
from . import observed_site_v14 as emitter

HERE=Path(__file__).resolve().parent
PROTOCOL=HERE/"archaeology/typed-v104-v14/FROZEN_PROTOCOL.json"
V13=HERE/"V13_EXPOSED_BRANCH_OBSERVATION_RESULT.json"
G2=G3=G4=G5=G6="UNKNOWN"
SCHEMA="UDM_V14_EXPOSED_ORIGINAL_V104_SLOT_NATIVE_DIAGNOSTIC"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def check_freeze():
    p=json.loads(PROTOCOL.read_text())
    if p["schema"]!="UDM_V14_SOURCE_CONDITIONED_ORIGINAL_V104_SLOT_PRECOMMIT":
        raise ValueError("new experimental scope differs")
    if p["budget"]!={"cap":8,"baseline_native_calls":2,"candidate_native_calls":16,
                     "total_native_calls":18,"max_seconds_per_call":90}:
        raise ValueError("candidate emission/native budget differs from frozen")
    if subprocess.check_output(["git","hash-object",str(V13)],text=True).strip()!=p["inherited_v13_machine_receipt_blob"]:
        raise ValueError("V13 original result not exactly authenticated")
    source=json.loads(V13.read_text())
    if (source["qualified_run_id"]!=39014314120
            or source["qualified_zip_sha256"]!=p["inherited_v13_artifact_sha256"]
            or source["observed_branch"]["independent_tracer_replays"]!=2):
        raise ValueError("V13 authentic original native observation absent")
    return p,source


def native_pair(repo,base,author,candidate,root,task):
    stage_root=root/"git-worktree"
    context=bridge.construct_candidate(repo,base,[author],candidate,stage_root)
    native_stage=native.stage(repo,context["candidate_commit"],root/"native-source")
    receipts=[]
    for _ in range(2):
        receipts.append(native.run_protected(
            repo,context["candidate_commit"],root/"native-source",
            required=tuple(context["required"]),paths=tuple(task["author_tests"]),
            interpreter=sys.executable,timeout=90))
    native.verify_stage(repo,context["candidate_commit"],root/"native-source")
    return context,receipts,v9.replayed(*receipts)


def run(out):
    if os.environ.get("UDM_V14_EXPOSED")!="SOURCE_EXPOSED_ORIGINAL_ONLY":
        raise ValueError("V14 requires explicit exposed-only native science ceiling")
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        raise ValueError("live source tests cannot inherit GitHub tokens")
    p,v13=check_freeze()
    v9p=v9.frozen()
    task=v9p["task_roles"][0]
    author=v9p["frozen_author_test_git_blob_refs"][0]
    if task["repository"]!="jd/tenacity":
        raise ValueError("original Tenacity source identity unavailable")
    event0=v13["observed_branch"]
    event={
        "path":event0["target_source"],
        "line":event0["original_line"],
        "then_line":event0["then_line"],
        "attribute":event0["original_attribute"],
        "kind":"IF_NOT_SELF_ATTRIBUTE",
        "branch":"THEN","callable":event0["attribute_callable"]
    }
    if (event["path"] not in task["production"]
            or not event0["then_branch_taken"]
            or not event["callable"]):
        raise ValueError("unqualified V13 trace event")
    native.verified_v6_source()
    root=Path(out).absolute()
    if root.exists() or root.resolve()!=root:
        raise ValueError("new V14 evidence directory required")
    root.mkdir(parents=True)
    started=time.monotonic()
    result={
        "schema":SCHEMA,"status":"UNKNOWN",
        "source_exposed":True,"source":"jd/tenacity PR741 prior exposed",
        "v13_source_run":v13["qualified_run_id"],"v13_observation":event,
        "packaging_source_opened":False,
        "original_repaired_HEAD_fetched":False,
        "candidate_language":"UNMODIFIED_ORIGINAL_PINNED_V104_AST_BUILDERS",
        "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
        "comparators":"NOT_RUN_EXPOSED_DIAGNOSTIC",
        "native_calls":0,"candidate_outcomes":[]
    }
    try:
        prepared=v7.prepare_task(task,author,root/"source")
        repo=Path(prepared["repo"])
        snap,regular=bridge._blobs(repo,task["base"])
        row=regular[event["path"]]
        original=bridge.typed._git(repo,"cat-file","blob",row["oid"])
        if digest(original)!=row["sha256"]:
            raise ValueError("observed original production blob changed")
        programs=emitter.targeted_original_candidates(
            original.decode("utf-8"),event["path"],event,
            Path(os.environ["UDM_V7_TRISKELION"]),cap=p["budget"]["cap"])
        if len(programs)!=p["budget"]["cap"]:
            result["status"]="UNKNOWN_INCOMPLETE_SOURCE_CONDITIONED_CATALOG"
            return result
        # Exactly original V104 cold/default policy, for counterfactual grammar:
        unobserved=bridge.catalog_v104_typed(
            repo,task["base"],tuple(task["production"]),
            Path(os.environ["UDM_V7_TRISKELION"]),
            Path(os.environ["UDM_V7_MSI"]),cap=64,observation={})
        old_guard_count=sum(
            event["path"]==c["path"] and event["line"] in c["changed_lines"]
            for c in unobserved["rows"])
        if old_guard_count!=0:
            result["status"]="UNKNOWN_ORIGINAL_EMISSION_COUNTERFACTUAL_CHANGED"
            return result
        # The fixed original-hash order is committed to disk BEFORE any native trial.
        plan={"schema":"UDM_V14_EXPOSED_BEFORE_NATIVE_FREEZE",
              "observed_source_manifest_sha256":snap["manifest_sha256"],
              "observation":event,
              "language":"ORIGINAL_SOURCE_PINNED_V104_ONLY",
              "original_v104_cold_candidates":len(unobserved["rows"]),
              "original_v104_cold_guard_edit_count":old_guard_count,
              "candidate_ids":[digest(x["source"].encode()) for x in programs],
              "candidate_builders":[x["builder"] for x in programs],
              "native_budget":p["budget"]}
        (root/"CANDIDATES_BEFORE_NATIVE.json").write_text(json.dumps(plan,sort_keys=True,indent=2)+"\n")
        result["catalog"]={
           "original_method_source":unobserved["source"],
           "original_candidate_count":len(unobserved["rows"]),
           "original_candidate_guard_edits":old_guard_count,
           "new_observation_conditional_candidates":len(programs),
           "all_candidate_source_slots_are_observed":all(
                  x["observed_line"]==event["line"] for x in programs),
           "source_generated_not_supplied_repair":True,
           "all_builders_original":True,
           "first_eight_ids_sha256":digest(json.dumps(plan["candidate_ids"]).encode())
        }
        baseline={ "replacements":[]}
        base_context,base_events,base_state=native_pair(
            repo,task["base"],prepared["test"],baseline,root/"baseline",task)
        result["native_calls"]+=2
        result["baseline"]={
          "status":base_state,
          "first":base_events[0]["status"],"second":base_events[1]["status"],
          "junit_first":base_events[0]["junit"],"junit_second":base_events[1]["junit"],
          "native_calls":2
        }
        if base_state!=v9.BAD:
            result["status"]="UNKNOWN_NO_PROTECTED_ORIGINAL_BASELINE_FAILURE"
            return result
        for i,item in enumerate(programs):
            candidate={"replacements":[{
                "path":event["path"],"original_sha256":row["sha256"],
                "replacement":item["source"]
            }]}
            record={"id":digest(item["source"].encode()),
                    "builder":item["builder"],
                    "selector":item["selector"],
                    "changed_lines":item["changed_lines"],
                    "candidate_source_sha256":item["source_sha256"],
                    "source_observed_site":event["line"],
                    "status":"UNKNOWN_NATIVE_EVIDENCE","native_calls":0}
            try:
                context,measure,state=native_pair(
                    repo,task["base"],prepared["test"],candidate,
                    root/("attempt-"+str(i).zfill(2)),task)
                result["native_calls"]+=2
                record.update(status=state,native_calls=2,
                  candidate_git_commit=context["candidate_commit"],
                  first={k:measure[0].get(k) for k in ("status","junit","native_exit","native_calls")},
                  second={k:measure[1].get(k) for k in ("status","junit","native_exit","native_calls")})
            except Exception as error:
                record["status"]="UNKNOWN_NATIVE_APPARATUS"
                record["reason"]=type(error).__name__+": "+str(error)
                # An early failure cannot support a FAIL or PASS; reserve the
                # two-call cap conservatively in accounting.
                record["reserved_max_calls"]=2
            result["candidate_outcomes"].append(record)
        states=[r["status"] for r in result["candidate_outcomes"]]
        result["measured"]={
            "verified_pass":states.count(v9.GOOD),
            "verified_fail":states.count(v9.BAD),
            "unknown":len(states)-states.count(v9.GOOD)-states.count(v9.BAD),
            "full_grammar_exhausted":False,
            "cap_eight_executed":len(states)==8,
            "source_observed_preactivation":True
        }
        result["status"]=(
            "EXPOSED_ORIGINAL_V104_AT_OBSERVED_SLOT_NATIVE_PASS"
            if result["measured"]["verified_pass"]>0
            else "EXPOSED_ORIGINAL_V104_SITE_EIGHT_NO_VERIFIED_REPAIR")
        return result
    except Exception as error:
        result["status"]="UNKNOWN_V14_NATIVE_APPARATUS"
        result["error"]=type(error).__name__+": "+str(error)
        result["traceback_tail"]=traceback.format_exc(limit=8)[-2400:]
        return result
    finally:
        result["elapsed_seconds"]=time.monotonic()-started
        (root/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    report=run(Path(os.environ["UDM_V14_OUT"]))
    print(json.dumps({"status":report["status"],"native_calls":report["native_calls"],
        "catalog":report.get("catalog"),"measured":report.get("measured"),
        "G2":"UNKNOWN","packaging_opened":False},sort_keys=True))
    raise SystemExit(0 if report["status"] in (
       "EXPOSED_ORIGINAL_V104_AT_OBSERVED_SLOT_NATIVE_PASS",
       "EXPOSED_ORIGINAL_V104_SITE_EIGHT_NO_VERIFIED_REPAIR") else 2)
