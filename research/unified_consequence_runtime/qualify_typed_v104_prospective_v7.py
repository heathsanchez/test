"""Frozen new-source experiment: V6 typed native -> original V104/MSI choice.

No source task is touched before GitHub commits this exact source, the fixed
protocol, author-test blob OIDs and all packages/budgets. The task base is
fetched alone; only exact independently authored HEAD test blobs are fetched,
never repaired HEAD production. All original frozen failures remain immutable.

G2 only if original MSI independently selects a UNIQUE native-qualified
training policy whose held-out future succeeds where the complete COLD prefix
failed under the same eight-candidate horizon. UNKNOWN preserves authority.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import urllib.request

from . import typed_v104_msi_bridge_v7 as bridge
from . import typed_source_inventory_v5 as typed

HERE=Path(__file__).resolve().parent
RECORDS=HERE/"archaeology/typed-v104-v7"
PROTOCOL=RECORDS/"PROTOCOL.json"
TEST_REFS=RECORDS/"FROZEN_AUTHOR_TEST_REFS.json"
SCHEMA="UDM_V7_PROSPECTIVE_TYPED_G2_EXECUTION"
FIXED_NATIVE_PYTEST="8.3.5"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)


def sealed_metadata():
    protocol=json.loads(PROTOCOL.read_text())
    refs=json.loads(TEST_REFS.read_text())
    assert protocol["schema"]=="UDM_TYPED_V104_G2_PROSPECTIVE_FREEZE_V7"
    assert refs["schema"]=="UDM_V7_FIXED_AUTHOR_TEST_BLOB_POINTERS"
    assert len(protocol["candidates"])==len(refs["refs"])==3
    assert [x["role"] for x in protocol["candidates"]]==["TRAINING","FUTURE_A","FUTURE_B"]
    for t,r in zip(protocol["candidates"],refs["refs"]):
        assert t["repository"]==r["repository"] and t["head"]==r["head_commit"]
        assert t["author_tests"]==[r["path"]]
    assert protocol["budgets"]["candidate_evaluations_per_method_per_task"]==8
    return protocol,refs


def _command(cmd,*,cwd=None,timeout=100):
    start=time.monotonic()
    p=subprocess.run(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    return {"exit":p.returncode,"seconds":time.monotonic()-start,
            "stdout_sha256":sha(p.stdout),"stderr_sha256":sha(p.stderr),
            "stderr_tail":p.stderr.decode(errors="replace")[-750:]}


def _git(root,*args):
    p=subprocess.run(["git","-C",str(root),*args],stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,timeout=40)
    if p.returncode:
        raise ValueError("frozen task source Git operation failed: "+" ".join(args[:2])+
                         "; "+p.stderr.decode(errors="replace")[-300:])
    return p.stdout.decode().strip()


def receive(repo_slug,ref):
    request=urllib.request.Request(
        "https://api.github.com/repos/"+repo_slug+"/git/blobs/"+ref["git_oid"],
        headers={"Accept":"application/vnd.github+json",
                 "User-Agent":"udm-v7-prospective-frozen-author-tests",
                 **({"Authorization":"Bearer "+os.environ["GH_TOKEN"]}
                    if os.environ.get("GH_TOKEN") else {})})
    started=time.monotonic()
    with urllib.request.urlopen(request,timeout=35) as resp:
        doc=json.load(resp)
    if doc.get("sha")!=ref["git_oid"] or doc.get("encoding")!="base64":
        raise ValueError("GitHub authenticated HEAD test blob mismatch")
    raw=base64.b64decode(doc["content"],validate=False)
    if bridge._git_blob_oid(raw)!=ref["git_oid"]:
        raise ValueError("transported author-test byte body has wrong Git OID")
    return {"path":ref["path"],"git_oid":ref["git_oid"],"sha256":sha(raw),
            "bytes":raw.hex()}, time.monotonic()-started


def prepare_task(task,ref,out):
    out=Path(out).absolute()
    if out.exists():raise ValueError("new fixed task source output required")
    out.mkdir(parents=True)
    repo=out/"source"
    repo.mkdir()
    transfer=[]
    def launch(*args):
        entry=_command(["git","-C",str(repo),*args],timeout=100)
        transfer.append({"command":[*args[:2]],**entry})
        if entry["exit"]:raise ValueError("original base source fetch/checkout refused")
    launch("init","-q")
    launch("fetch","--no-tags","--depth=1",
           "https://github.com/"+task["repository"]+".git",task["base"])
    launch("checkout","--detach","-q","FETCH_HEAD")
    if _git(repo,"rev-parse","HEAD")!=task["base"]:
        raise ValueError("fetched project source differs from precommitted base SHA")
    head=subprocess.run(["git","-C",str(repo),"cat-file","-e",
                         task["head"]+"^{commit}"],capture_output=True)
    if head.returncode==0:
        raise ValueError("repaired HEAD commit wrongly fetched into frozen learner")
    base_snapshot=typed.snapshot(repo,task["base"])
    source_test,download_seconds=receive(task["repository"],ref)
    protected=bridge.changed_author_assertions(repo,task["base"],[source_test])
    return {"repo":str(repo),"source_binding":base_snapshot["manifest_sha256"],
            "test":source_test,"protected":protected,
            "source_receipt":{"repository":task["repository"],"base":task["base"],
                              "head_test_oid":source_test["git_oid"],
                              "head_production_fetched":False,"source":base_snapshot["counts"],
                              "transfer":transfer,"test_transport_seconds":download_seconds}}


def evaluate(repo,base,author,candidate,out):
    started=time.monotonic()
    root=Path(out).absolute()
    root.mkdir(parents=True,exist_ok=False)
    committed=bridge.construct_candidate(repo,base,[author],candidate,root/"candidate-worktree")
    attempt=bridge.native_profile(repo,committed,root/"native",
                                  interpreter=sys.executable,timeout=90)
    return {"status":attempt["status"],"candidate_sha256":attempt["candidate_sha256"],
            "source_commit":attempt["source_commit"],
            "measurements":attempt.get("measurements"),
            "native_evidence_sha256":attempt["native_evidence_sha256"],
            "native_calls":attempt["native_calls"],
            "native_seconds":attempt["cost_seconds"],
            "elapsed_seconds":time.monotonic()-started,
            "protected":committed["required"],"evidence":attempt}


def _profile_for_order(order,actual,horizon):
    prefix=order[:horizon]
    if len(prefix)!=horizon or any(candidate not in actual for candidate in prefix):
        return None
    for position,ident in enumerate(prefix):
        row=actual[ident]
        if row["status"]=="VERIFIED_REPEATED_PASS_SCOPED_NATIVE":
            return [0,2*(position+1)]
        if row["status"]!="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED":
            return None
    return [1,2*horizon]


def _select_original(rows,actual,budget,task_repo):
    from .developmental_choice import profile_binding, choose_verified_profiles
    names=tuple(rows["orders"])
    futures=("TRAINING",)
    carrier={}
    for policy in names:
        metric=_profile_for_order(rows["orders"][policy],actual,budget)
        if metric is None:
            return {"status":"UNKNOWN_INCOMPLETE_VERIFIED_POLICY_PROFILES",
                    "completed_policies":len(carrier),"required_policies":len(names),
                    "native_calls":sum(x["native_calls"] for x in actual.values()),
                    "MDA":"NOT_RUN"}
        carrier[policy]={"TRAINING":metric}
    source_scope={"protocol_binding":sha(PROTOCOL.read_bytes()),
                  "candidate_catalog_sha256":sha(canonical(
                      [r["id"] for r in rows["rows"]]).encode()),
                  "source_binding":rows["original_typed_source_sha256"],
                  "budget":budget,
                  "native_evidence_sha256":sha(canonical({
                       k:v["native_evidence_sha256"] for k,v in actual.items()}).encode())}
    root=Path(__file__).resolve().parents[2]
    binding=profile_binding(names,futures,carrier,scope=source_scope)
    choice=choose_verified_profiles(root,names,futures,carrier,evidence_binding=binding)
    return {"status":choice["status"],"choice":choice,
            "scope":source_scope,"profiles":carrier,
            "candidates":list(names),
            "G2":"UNKNOWN","MDA":"NOT_RUN_WITHOUT_PROSPECTIVE_CAUSAL_TEST"}


def _budget_time(start,limit):
    return time.monotonic()-start < limit


def test_first_training(task,ref,out,protocol):
    started=time.monotonic()
    report={"role":task["role"],"repository":task["repository"],
            "base":task["base"],"status":"UNKNOWN","source_opened":False,
            "native_calls":0,"candidate_count":0,"candidate_evaluations":[],
            "future_source_opened":False}
    try:
        prepared=prepare_task(task,ref,out/"task")
        report.update(source_opened=True,
                      source_identity=prepared["source_binding"],
                      protected=prepared["protected"],
                      source_receipt=prepared["source_receipt"])
        base=task["base"];repo=prepared["repo"];author=prepared["test"]
        baseline=evaluate(repo,base,author,{"replacements":[]},out/"baseline")
        report["baseline"]=baseline
        report["native_calls"]+=baseline["native_calls"]
        if baseline["status"]!="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED":
            report["status"]="UNKNOWN_NO_QUALIFIED_NATIVE_TRAINING_RESIDUAL"
            return report
        catalog=bridge.catalog_v104_typed(repo,base,task["production"],
                        Path(os.environ["UDM_V7_TRISKELION"]),
                        Path(os.environ["UDM_V7_MSI"]),cap=64,
                        observation={})
        report["catalog"]={"row_count":len(catalog["rows"]),
                           "policy_count":len(catalog["orders"]),
                           "sha256":sha(canonical(catalog).encode()),
                           "source":catalog["source"],
                           "original_typed_source_sha256":catalog["original_typed_source_sha256"]}
        index={row["id"]:row for row in catalog["rows"]}
        seen={};max_native=protocol["budgets"]["total_per_task_native_calls"]
        horizon=protocol["budgets"]["candidate_evaluations_per_method_per_task"]
        # Fair, fixed round-robin across original policy prefixes. Every
        # candidate measured at most once and its cost is shared, never free.
        name_order=list(catalog["orders"])
        sorted_names=[name_order[0],*sorted(name_order[1:])]
        scheduled=[]
        for pos in range(horizon):
            for name in sorted_names:
                order=catalog["orders"][name]
                if len(order)>pos and order[pos] not in scheduled:
                    scheduled.append(order[pos])
        for ident in scheduled:
            if report["native_calls"]+2>max_native or not _budget_time(
                    started,protocol["budgets"]["total_experiment_wall_seconds"]):
                break
            row=index[ident]
            try:
                event=evaluate(repo,base,author,row["candidate"],
                           out/"training-evaluations"/("candidate-"+str(len(seen)).zfill(3)))
            except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
                event={"status":"UNKNOWN_CANDIDATE_PROVISION","reason":str(error),
                       "native_calls":0,"candidate_sha256":ident}
            report["native_calls"]+=event.get("native_calls",0)
            seen[ident]=event
            report["candidate_evaluations"].append({
               "id":ident,"selector":row["selector"],"builder":row["builder"],
               "status":event["status"],"native_calls":event.get("native_calls",0),
               "source_commit":event.get("source_commit"),
               "native_evidence_sha256":event.get("native_evidence_sha256"),
               "elapsed_seconds":event.get("elapsed_seconds")})
        report["candidate_count"]=len(seen)
        choice=_select_original(catalog,seen,horizon,repo)
        report["choice"]=choice
        report["status"]="TRAINING_NATIVE_SOURCE_EVALUATED_"+choice["status"]
        report["original_orders"]=catalog["orders"]
        report["candidate_catalog"]=[{"id":r["id"],"candidate":r["candidate"]}
                                    for r in catalog["rows"]]
        return report
    except Exception as error:
        report.update(status="UNKNOWN_TRAINING_SETUP_OR_AUTHORITY",
                      obstruction=type(error).__name__+": "+str(error),
                      traceback=traceback.format_exc()[-3500:])
        return report
    finally:
        report["wall_seconds"]=time.monotonic()-started


def run(out):
    start=time.monotonic()
    protocol,refs=sealed_metadata()
    if os.environ.get("UDM_V7_ALLOW_PROSPECTIVE")!="YES_EXACT_FROZEN_SOURCE":
        raise ValueError("prospective source access requires explicit bound CI launch")
    if not Path(out).is_absolute() or Path(out).exists():
        raise ValueError("new absolute bounded evidence directory required")
    dest=Path(out);dest.mkdir(parents=True)
    result={"schema":SCHEMA,"status":"UNKNOWN",
            "protocol_sha256":sha(PROTOCOL.read_bytes()),
            "frozen_test_refs_sha256":sha(TEST_REFS.read_bytes()),
            "source_commit":os.environ.get("GITHUB_SHA"),
            "tasks":[], "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
            "G5":"UNKNOWN","G6":"UNKNOWN",
            "informed_ledger":"NOT_RUN_BEFORE_NATIVE_G2_ADMISSION",
            "coding_agent":"NOT_RUN_NO_AUTHENTIC_TOOL_USING_MODEL_ACCESS",
            "unopened_futures":["jd/tenacity","pypa/packaging"],
            "no_outcome_based_reselection":True,
            "no_head_production_input":True}
    try:
        training=test_first_training(protocol["candidates"][0],refs["refs"][0],
                                     dest/"training",protocol)
        result["tasks"].append(training)
        if (training.get("status","").startswith("TRAINING_NATIVE_SOURCE_EVALUATED_")
                and training["choice"]["status"]=="AUTHORIZED_REPAIR"
                and training["choice"]["choice"]["selected"]!="COLD_V104_ORDER"
                and training["choice"]["profiles"]["COLD_V104_ORDER"]["TRAINING"][0]==1):
            # Selected only from training evidence. Future A remains unopened
            # until this line. Future B is reserved for independent G3.
            sel=training["choice"]["choice"]["selected"]
            result["training_selected_policy"]=sel
            result["status"]="CANDIDATE_TRAINING_POLICY_FOR_FUTURE"
            result["next_source_release"]="FUTURE_A_EXPLICIT_G2_ELIGIBLE"
            # Actual future test is deliberately implemented in this same
            # precommitted source below, never selected by seeing its result.
            future=trial_future(protocol["candidates"][1],refs["refs"][1],
                                 dest/"future-a",protocol,sel)
            result["tasks"].append(future)
            result["unopened_futures"]=["pypa/packaging"]
            if future.get("status")=="QUALIFIED_UNIQUE_G2_PROSPECTIVE_CAUSAL_EFFECT":
                result["G2"]="WARRANTED_BOUNDED"
                result["status"]="WARRANTED_BOUNDED_G2_UNDER_FROZEN_NATIVE_HORIZON"
            else:result["status"]="UNKNOWN_PROSPECTIVE_CAUSAL_SELECTION"
        else:
            result["status"]="UNKNOWN_NO_UNIQUE_NATIVE_TRAINING_POLICY_OR_COLD_CAUSAL_RESIDUAL"
        return result
    finally:
        result["wall_seconds"]=time.monotonic()-start
        (dest/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")


def trial_future(task,ref,out,protocol,selected):
    start=time.monotonic()
    record={"role":"FUTURE_A","repository":task["repository"],"source_opened":False,
            "status":"UNKNOWN","native_calls":0,
            "selected_without_future_observations":selected}
    try:
        prepared=prepare_task(task,ref,out/"source")
        record.update(source_opened=True,protected=prepared["protected"],
                      source_receipt=prepared["source_receipt"])
        repo,base,author=prepared["repo"],task["base"],prepared["test"]
        original_baseline=evaluate(repo,base,author,{"replacements":[]},out/"baseline")
        record["baseline"]=original_baseline
        record["native_calls"]+=original_baseline["native_calls"]
        if original_baseline["status"]!="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED":
            record["status"]="UNKNOWN_NO_PROTECTED_FUTURE_NATIVE_RESIDUAL"
            return record
        catalog=bridge.catalog_v104_typed(repo,base,task["production"],
                            Path(os.environ["UDM_V7_TRISKELION"]),
                            Path(os.environ["UDM_V7_MSI"]),cap=64)
        index={r["id"]:r for r in catalog["rows"]}
        if selected not in catalog["orders"]:
            record["status"]="UNKNOWN_SELECTED_POLICY_NOT_APPLICABLE_TO_FUTURE"
            return record
        horizon=protocol["budgets"]["candidate_evaluations_per_method_per_task"]
        result={}
        for group in ("COLD_V104_ORDER",selected):
            attempts=[];within=[]
            for num,ident in enumerate(catalog["orders"][group][:horizon]):
                if ident not in result:
                    if record["native_calls"]+2>protocol["budgets"]["total_per_task_native_calls"]:
                        break
                    row=index[ident]
                    candidate=evaluate(repo,base,author,row["candidate"],
                                       out/("attempt-"+str(len(result)).zfill(3)))
                    result[ident]=candidate
                    record["native_calls"]+=candidate["native_calls"]
                attempts.append({"id":ident,"status":result[ident]["status"]})
            record[group]={"attempts":attempts,
                           "complete":len(attempts)==horizon,
                           "profile":_profile_for_order(catalog["orders"][group],result,horizon)}
        cold=record["COLD_V104_ORDER"];warm=record[selected]
        if (cold["complete"] and warm["complete"] and cold["profile"] is not None
                and warm["profile"] is not None and cold["profile"][0]==1
                and warm["profile"][0]==0):
            record["status"]="QUALIFIED_UNIQUE_G2_PROSPECTIVE_CAUSAL_EFFECT"
            record["causal_scope"]="selected source-bound original policy vs cold same native budget, G3/G4 not established"
        else:
            record["status"]="UNKNOWN_NO_CAUSAL_FUTURE_ADVANTAGE"
        return record
    except Exception as error:
        record.update(status="UNKNOWN_FUTURE_SETUP_OR_SOURCE_AUTHORITY",
                      obstruction=type(error).__name__+": "+str(error),
                      traceback=traceback.format_exc()[-3500:])
        return record
    finally:
        record["wall_seconds"]=time.monotonic()-start


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    result=run(Path(args.out))
    print(json.dumps({"schema":SCHEMA,"status":result["status"],
                      "G2":result["G2"],
                      "training_status":result["tasks"][0].get("status") if result["tasks"] else "NOT_RUN",
                      "native_calls":sum(t.get("native_calls",0) for t in result["tasks"]),
                      "unopened_futures":result["unopened_futures"]},sort_keys=True))
    # This workflow's scientific status is RED/UNKNOWN unless prospective G2
    # succeeded. A zero-native admission refusal must not appear green.
    raise SystemExit(0 if result["G2"]=="WARRANTED_BOUNDED" else 2)


if __name__=="__main__":
    main()
