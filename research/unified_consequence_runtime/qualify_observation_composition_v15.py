"""V15 source-exposed consequence-selection trial over supplied AST composition.

No hardcoded original source path, line, attribute, winning expression or
upstream repaired production. All source authority comes from V13/V9. A positive
result is scoped original source causal evidence, NOT prospective G2, autonomous
meta-grammar genesis, G3 or superiority to a fully informed agent.
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
from . import observation_composition_v15 as compose

HERE=Path(__file__).resolve().parent
PROTOCOL=HERE/"archaeology/typed-v104-v15/FROZEN_COMPOSITION_PROTOCOL.json"
V13=HERE/"V13_EXPOSED_BRANCH_OBSERVATION_RESULT.json"
V14=HERE/"V14_EXPOSED_SOURCE_SLOT_RESULT.json"
SCHEMA="UDM_V15_EXPOSED_NATIVE_COMPOSITIONAL_METHOD_ACQUISITION"
G2=G3=G4=G5=G6="UNKNOWN"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen():
    p=json.loads(PROTOCOL.read_text())
    if p["schema"]!="UDM_V15_EXPOSED_OBSERVATION_CONDITIONED_COMPOSITION_PROTOCOL":
        raise ValueError("wrong immutable experimental protocol")
    if p["generation"]["candidate_limit"]!=24 or (
            p["generation"]["per_candidate_native_replays"]!=2 or
            p["generation"]["native_timeout_seconds"]!=14 or
            p["generation"]["maximum_native_calls"]!=54):
        raise ValueError("native cost and search freeze changed")
    if p["task_scope"]!="PREVIOUSLY_EXPOSED_TENACITY_PR741_ONLY":
        raise ValueError("source authority changed")
    if p["source_history"]["v13_github_blob"]!=subprocess.check_output(
            ["git","hash-object",str(V13)],text=True).strip():
        raise ValueError("qualified V13 source observation receipt changed")
    old=json.loads(V13.read_text())
    if old["qualified_run_id"]!=39014314120 or old["observed_branch"]["independent_tracer_replays"]!=2:
        raise ValueError("source/branch observation was not independently qualified")
    if p["source_history"]["v14_no_verified_repair"]!=8 or not p["source_history"]["v14_mixed_negative_unknown"]:
        raise ValueError("original V14 evidence is not the declared negative residual")
    v14=json.loads(V14.read_text())
    if (v14["actions_run"]!=39017793736 or v14["actual"]["outcomes"]["verified_pass"]!=0
            or v14["actual"]["outcomes"]["unknown"]!=4
            or v14["zip_sha256"]!=p["source_history"]["v14_native_artifact_sha256"]):
        raise ValueError("prior original grammar control is not byte-bound")
    return p,old,v14


def measured(repo,base,author,candidate,out,task,timeout):
    out=Path(out).absolute()
    if out.exists():
        raise ValueError("native comparison output already exists")
    out.mkdir(parents=True)
    context=bridge.construct_candidate(repo,base,[author],candidate,out/"worktree")
    stage=native.stage(repo,context["candidate_commit"],out/"stage")
    actual=[]
    for _ in range(2):
        actual.append(native.run_protected(
            repo,context["candidate_commit"],out/"stage",
            required=tuple(context["required"]),
            paths=tuple(task["author_tests"]),
            interpreter=sys.executable,timeout=timeout))
    checked=native.verify_stage(repo,context["candidate_commit"],out/"stage")
    return {
      "candidate_commit":context["candidate_commit"],
      "candidate_sha256":context["candidate_sha256"],
      "original":context["source_base"],
      "typed_manifest_sha256":stage["typed_manifest_sha256"],
      "native_calls":sum(x.get("native_calls",0) for x in actual),
      "status":v9.replayed(*actual),
      "receipt_status":[x["status"] for x in actual],
      "junit":[x.get("junit") for x in actual],
      "executed_identical":actual[0].get("executed")==actual[1].get("executed"),
      "import_identity_identical":actual[0].get("imported_project_files")==actual[1].get("imported_project_files"),
      "post_stage_status":checked["status"],
      "first_exit":actual[0].get("native_exit"),
      "second_exit":actual[1].get("native_exit"),
      "times":[x.get("native_seconds") for x in actual]
    }


def run(out):
    if os.environ.get("UDM_V15_EXPOSED")!="EXPOSED_COMPOSITION_NOT_G2":
        raise ValueError("V15 cannot be executed as a prospective G2 trial")
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        raise ValueError("original tests must receive no GitHub credentials")
    protocol,v13,v14=frozen()
    task_record=v9.frozen()
    task=task_record["task_roles"][0]
    author=task_record["frozen_author_test_git_blob_refs"][0]
    if task["repository"]!="jd/tenacity" or author["repository"]!="jd/tenacity":
        raise ValueError("independent frozen exposed source task identity differs")
    native.verified_v6_source()
    root=Path(out).absolute()
    if root.exists() or root.resolve()!=root:
        raise ValueError("new isolated native result directory required")
    root.mkdir(parents=True)
    tic=time.monotonic()
    result={
      "schema":SCHEMA,"status":"UNKNOWN_NOT_EXECUTED",
      "source_exposed":True,"packaging_source_opened":False,
      "original_repaired_head_fetched":False,
      "composer":"SUPPLIED_GENERIC_AST_COMPOSITION_NOT_LEARNED_META_GRAMMAR",
      "future_discoverability":"NOT_EXECUTED",
      "full_informed_ledger":"NOT_RUN",
      "coding_agent":"NOT_RUN",
      "original_grammar":v14["status"],
      "original_v14_run":v14["actions_run"],
      "native_calls":0,"budget":protocol["generation"]["maximum_native_calls"],
      "candidate_results":[],"G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
      "G5":"UNKNOWN","G6":"UNKNOWN"}
    try:
        prepared=v7.prepare_task(task,author,root/"source")
        repo=Path(prepared["repo"])
        snap,regular=bridge._blobs(repo,task["base"])
        observation=v13["observed_branch"]
        event={
            "path":observation["target_source"],
            "line":observation["original_line"],
            "then_line":observation["then_line"],
            "attribute":observation["original_attribute"],
            "branch":"THEN","callable":observation["attribute_callable"],
            "kind":"IF_NOT_SELF_ATTRIBUTE"}
        if event["path"] not in task["production"] or not observation["then_branch_taken"]:
            raise ValueError("original native observed slot no longer source-bound")
        row=regular[event["path"]]
        source=bridge.typed._git(repo,"cat-file","blob",row["oid"])
        if digest(source)!=row["sha256"]:
            raise ValueError("original source bytes differ from exact original blob")
        proposals=compose.emit(source.decode("utf-8"),event["path"],event,
                               cap=protocol["generation"]["candidate_limit"])
        result["catalog"]={
          "source_manifest_sha256":snap["manifest_sha256"],
          "observed_event":event,
          "source_original_sha256":row["sha256"],
          "count":len(proposals),
          "all_modified_same_observed_slot":all(
            x["path"]==event["path"] and x["source_line"]==event["line"] for x in proposals),
          "first_candidate_sha256":proposals[0]["sha256"],
          "plan_sha256":digest(json.dumps([
                 [x["signature"],x["sha256"]] for x in proposals],sort_keys=True).encode()),
          "grammar":"SUPPLIED_AST_ATOM_AND_PAIR_COMPOSITION",
          "no_supplied_winning_method":True}
        (root/"CANDIDATES_BEFORE_NATIVE.json").write_text(
           json.dumps([{"signature":x["signature"],"sha256":x["sha256"],
                        "predicate_nodes":x["predicate_nodes"]} for x in proposals],
                      indent=2,sort_keys=True)+"\n")
        budget=protocol["generation"]["native_timeout_seconds"]
        base=measured(repo,task["base"],prepared["test"],
                      {"replacements":[]},root/"baseline",task,budget)
        result["native_calls"]+=base["native_calls"]
        result["baseline"]=base
        if base["status"]!=v9.BAD:
            result["status"]="UNKNOWN_NO_VERIFIED_PROTECTED_ORIGINAL_FAILURE"
            return result

        winner=None
        for i,variant in enumerate(proposals):
            if result["native_calls"]+2+4>result["budget"]:
                result["status"]="UNKNOWN_BUDGET_NO_FULL_RESTORE"
                return result
            candidate={"replacements":[{
               "path":event["path"],"original_sha256":row["sha256"],
               "replacement":variant["source"]}]}
            attempt={"i":i,"signature":variant["signature"],"sha256":variant["sha256"],
                     "status":"UNKNOWN","native_calls":0}
            try:
                evidence=measured(repo,task["base"],prepared["test"],
                                  candidate,root/("proposal-"+str(i).zfill(2)),
                                  task,budget)
                result["native_calls"]+=evidence["native_calls"]
                attempt.update({key:evidence[key] for key in (
                    "status","native_calls","receipt_status","junit","first_exit",
                    "second_exit","executed_identical","import_identity_identical",
                    "candidate_sha256","candidate_commit")})
            except Exception as error:
                attempt["reason"]=type(error).__name__+": "+str(error)
                result["native_calls"]+=2  # conservative charged reservation, no result promotion
            result["candidate_results"].append(attempt)
            if attempt["status"]==v9.GOOD:
                winner=(variant,candidate,attempt)
                break
        if winner is None:
            result["status"]="UNKNOWN_NO_VERIFIED_COMPOSITE_CONSTRUCTOR_REPAIR"
            return result
        result["selected"]={k:winner[2][k] for k in (
            "i","signature","sha256","candidate_sha256","candidate_commit")}
        # Physical withdrawal: no retained program code in replacement source.
        removal=measured(repo,task["base"],prepared["test"],
                         {"replacements":[]},root/"physical-withdrawal",task,budget)
        result["native_calls"]+=removal["native_calls"]
        result["removal"]=removal
        if removal["status"]!=v9.BAD:
            result["status"]="UNKNOWN_REMOVAL_DID_NOT_RESTORE_ORIGINAL_FAIL"
            return result
        # Fresh independently generated worktree and two native runs.
        restoration=measured(repo,task["base"],prepared["test"],
                             winner[1],root/"fresh-restoration",task,budget)
        result["native_calls"]+=restoration["native_calls"]
        result["restoration"]=restoration
        if restoration["status"]!=v9.GOOD:
            result["status"]="UNKNOWN_RESTORATION_NOT_VERIFIED"
            return result
        if (not result["selected"] or result["native_calls"]>result["budget"]
                or restoration["candidate_sha256"]!=winner[2]["candidate_sha256"]):
            result["status"]="UNKNOWN_CAUSAL_IDENTITY_OR_COST"
            return result
        result["status"]="WARRANTED_BOUNDED_EXPOSED_NATIVE_COMPOSITE_ACQUISITION_AND_SOURCE_ABLATION"
        return result
    except Exception as error:
        result["status"]="UNKNOWN_V15_EXECUTION_APPARATUS"
        result["error"]=type(error).__name__+": "+str(error)
        result["traceback_tail"]=traceback.format_exc(limit=8)[-2400:]
        return result
    finally:
        result["elapsed_seconds"]=time.monotonic()-tic
        (root/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    report=run(Path(os.environ["UDM_V15_OUT"]))
    print(json.dumps({
      "status":report["status"],"native_calls":report["native_calls"],
      "tested":len(report["candidate_results"]),
      "winner":report.get("selected"),
      "G2":"UNKNOWN","packaging_opened":False},sort_keys=True))
    raise SystemExit(0 if report["status"]==
      "WARRANTED_BOUNDED_EXPOSED_NATIVE_COMPOSITE_ACQUISITION_AND_SOURCE_ABLATION"
      else 2)
