"""Frozen V12 *exposed-source* six-arm causal guard intervention.

The source and independent author test are historical/exposed Tenacity PR741.
All candidate guards are HUMAN-supplied in the immutable V12 freeze; no
autonomous new operation, MSI optimization success, or prospective G2 can follow.
Original V6/V10 native worker, original V104/MSI policy source, V9/V11 evidence,
and separate Packaging heldout source are untouched.
"""
from __future__ import annotations

import ast
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

HERE=Path(__file__).resolve().parent
PROTOCOL=HERE/"archaeology/typed-v104-v12/FROZEN_GUARDS.json"
FROZEN_PROTOCOL_BLOB="4f9a9b7daef5e3799c6e79706f6665a24e763737"
ARMS=("BASE","NONE_ONLY","NONE_OR_ZERO","CALLABILITY","SHAM","REMOVAL")
ORIGINAL_GUARD="if not self.wait:"
SHAM_BEFORE="return tornado is not None"
SHAM_AFTER="return tornado is None"
PATH="tenacity/__init__.py"
SCHEMA="UDM_V12_EXPOSED_GUARD_NATIVE_INTERVENTION"
POSITIVE="VERIFIED_REPEATED_PASS_SCOPED_NATIVE"
NEGATIVE="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED"
UNKNOWN="UNKNOWN"


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def frozen():
    if subprocess.check_output(["git","hash-object",str(PROTOCOL)],text=True,timeout=15).strip()!=FROZEN_PROTOCOL_BLOB:
        raise ValueError("original pre-result V12 arm protocol changed")
    p=json.loads(PROTOCOL.read_text())
    if p.get("schema")!="UDM_V12_EXPOSED_TENACITY_CAUSAL_GUARD_INTERVENTION":
        raise ValueError("wrong frozen experiment")
    if tuple(x.get("id") for x in p.get("candidate_order",()))!=ARMS:
        raise ValueError("frozen six-arm ordering or alternatives altered")
    if p.get("original_head_test_blob")!="577720ec7cf0a48b9b2909e45ddde29235f460ac":
        raise ValueError("frozen original independently authored test differs")
    if p.get("prior_V11_red")!=38986306451 or p.get("budgets",{}).get("native_calls_ceiling")!=12:
        raise ValueError("frozen original V11 or cost authority changed")
    if p.get("claims",{}).get("G2")!="UNKNOWN" or p.get("original_repaired_HEAD_production")!="PROHIBITED":
        raise ValueError("frozen scientific claims changed")
    return p


def transform(arm, source):
    if arm not in ARMS or not isinstance(source,str):
        raise ValueError("unknown precommitted V12 source operation")
    if arm in ("BASE","REMOVAL"):
        return source
    if arm=="SHAM":
        if source.count(SHAM_BEFORE)!=1:
            raise ValueError("original sham location missing or ambiguous")
        result=source.replace(SHAM_BEFORE,SHAM_AFTER,1)
    else:
        if source.count(ORIGINAL_GUARD)!=1:
            raise ValueError("original guard location missing or ambiguous")
        value={
          "NONE_ONLY":"if self.wait is None:",
          "NONE_OR_ZERO":"if self.wait is None or self.wait == 0:",
          "CALLABILITY":"if not self.wait and not callable(self.wait):"
        }[arm]
        result=source.replace(ORIGINAL_GUARD,value,1)
    ast.parse(result,filename=PATH)
    return result


def native_status(first, second):
    # Existing V9's replay rule checks actual call counts, required/executed,
    # deselection, imported source hashes and matching original manifest.
    verdict=v9.replayed(first,second)
    return "UNKNOWN" if verdict==v9.UNVERIFIED else verdict


def _candidate(base, raw, arm):
    if arm in ("BASE","REMOVAL"):return {"replacements":[]}
    original=raw.decode("utf-8")
    changed=transform(arm,original)
    if changed==original:raise ValueError("precommitted alternative did not change source")
    return {"replacements":[{
        "path":PATH, "original_sha256":digest(raw),
        "replacement":changed
    }]}


def run(out):
    if os.environ.get("UDM_V12_EXPOSED")!="YES_DIAGNOSTIC_NOT_G2":
        raise ValueError("V12 cannot run without explicit exposed-only authority")
    p=frozen()
    v9p=v9.frozen()
    original=v9p["task_roles"][0]
    author=v9p["frozen_author_test_git_blob_refs"][0]
    if (original.get("repository")!="jd/tenacity"
            or original.get("base")!="4a74682e0186b5f2d25906aa190cd639c705a958"
            or author.get("git_oid")!=p["original_head_test_blob"]):
        raise ValueError("original source-identity authority differs")
    if original.get("author_tests")!=[p["protected_author_test_scope"]]:
        raise ValueError("test scope not source-pinned")
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        raise ValueError("upstream trusted Python may not receive a live GitHub token")
    native.verified_v6_source()

    dest=Path(out).absolute()
    if dest.exists() or dest.resolve()!=dest:raise ValueError("fresh canonical evidence output required")
    dest.mkdir(parents=True)
    started=time.monotonic()
    result={
        "schema":SCHEMA,"status":"UNKNOWN_NOT_RUN",
        "source_exposed":True,
        "source_repository":"jd/tenacity",
        "original_source_commit":original["base"],
        "original_head_test_oid":author["git_oid"],
        "original_repaired_head_fetched":False,
        "packaging_source_opened":False,
        "frozen_protocol_git_blob":FROZEN_PROTOCOL_BLOB,
        "frozen_budget":p["budgets"],
        "arm_order":list(ARMS),
        "candidate_outcomes":{},
        "native_calls":0,
        "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN",
        "G5":"UNKNOWN","G6":"UNKNOWN",
        "candidate_provenance":"HUMAN_SUPPLIED_EXPOSED_ONLY",
        "comparators":"NOT_RUN",
        "prior_V9_scientific_RED":38985251065,
        "prior_V10_green":38985872094,
        "prior_V11_scientific_RED":38986306451,
    }
    try:
        prepared=v7.prepare_task(original,author,dest/"source")
        repo=prepared["repo"]
        snap, files=bridge._blobs(repo,original["base"])
        if PATH not in files or files[PATH]["mode"] not in bridge.typed.REGULAR_MODES:
            raise ValueError("original production source not an independently regular tracked blob")
        raw=bridge.typed._git(repo,"cat-file","blob",files[PATH]["oid"])
        if digest(raw)!=files[PATH]["sha256"]:
            raise ValueError("original Tenacity source Git blob mismatch")
        if raw.decode("utf-8").count(ORIGINAL_GUARD)!=1 or raw.decode("utf-8").count(SHAM_BEFORE)!=1:
            raise ValueError("source-specific human precommit alternatives not matched")
        result["original_source_manifest_sha256"]=snap["manifest_sha256"]
        result["source_receipt"]=prepared["source_receipt"]
        result["protected_expected"]=[p["protected_method"]]
        result["native_arms"]=[]
        for arm in ARMS:
            if result["native_calls"]+2>p["budgets"]["native_calls_ceiling"]:
                result["status"]="UNKNOWN_BUDGET_EXHAUSTED"
                break
            step=dest/("arm-"+arm.lower())
            step.mkdir()
            entry={"arm":arm,"candidate_source":"HUMAN_PRECOMMITTED",
                   "status":"UNKNOWN_NATIVE_EVIDENCE","native_calls":0}
            result["candidate_outcomes"][arm]="UNKNOWN"
            try:
                candidate=_candidate(original["base"],raw,arm)
                context=bridge.construct_candidate(
                    repo,original["base"],[prepared["test"]],candidate,step/"candidate-worktree")
                required=tuple(context["required"])
                if p["protected_method"] not in required:
                    raise ValueError("independent protected original method absent")
                if (len(context["changed_paths"]) not in (1,2)
                        or (arm in ("BASE","REMOVAL") and PATH in context["changed_paths"])
                        or (arm in ("NONE_ONLY","NONE_OR_ZERO","CALLABILITY","SHAM")
                            and PATH not in context["changed_paths"])):
                    raise ValueError("candidate changed unqualified source")
                receipt_stage=native.stage(repo,context["candidate_commit"],step/"stage")
                measured=[]
                for index in range(2):
                    checked=native.run_protected(
                        repo,context["candidate_commit"],step/"stage",
                        required=required,
                        paths=tuple(original["author_tests"]),
                        interpreter=sys.executable,
                        timeout=p["budgets"]["per_call_seconds"])
                    measured.append(checked)
                    result["native_calls"]+=checked.get("native_calls",0)
                    entry["native_calls"]+=checked.get("native_calls",0)
                stage_post=native.verify_stage(repo,context["candidate_commit"],step/"stage")
                outcome=native_status(*measured)
                entry.update(status=outcome,source_commit=context["candidate_commit"],
                             candidate_sha256=context["candidate_sha256"],
                             authored_tests=context["author_test_blobs"],
                             original_source_manifest_sha256=context["protocol_source_manifest_sha256"],
                             stage_after=stage_post["status"],
                             required=list(required),
                             first={k:measured[0].get(k) for k in (
                                "status","junit","native_calls","native_exit",
                                "executed","deselected","imported_project_files",
                                "typed_manifest_sha256")},
                             second={k:measured[1].get(k) for k in (
                                "status","junit","native_calls","native_exit",
                                "executed","deselected","imported_project_files",
                                "typed_manifest_sha256")})
                result["candidate_outcomes"][arm]=outcome
            except Exception as err:
                entry["error"]=type(err).__name__+": "+str(err)
                # Unknown cannot be silently turned into a native negative or success.
                result["candidate_outcomes"][arm]="UNKNOWN_NATIVE_APPARATUS"
            entry["wall_seconds"]=time.monotonic()-started
            result["native_arms"].append(entry)
            (step/"RESULT.json").write_text(json.dumps(entry,indent=2,sort_keys=True)+"\n")
            if entry.get("error"):
                result["status"]="UNKNOWN_ARM_APPARATUS"
                break

        outcomes=result["candidate_outcomes"]
        if len(outcomes)!=len(ARMS):
            result["status"]="UNKNOWN_INCOMPLETE_FROZEN_ARM_CENSUS"
        elif result["native_calls"]>12:
            result["status"]="UNKNOWN_NATIVE_BUDGET"
        elif all(outcomes.get(a)==NEGATIVE for a in ("BASE","SHAM","REMOVAL")) and (
                outcomes.get("NONE_OR_ZERO")==POSITIVE):
            result["status"]="WARRANTED_BOUNDED_EXPOSED_HUMAN_GUARD_INTERVENTION_ONLY"
            result["positive_alternatives"]=[a for a in ("NONE_ONLY","NONE_OR_ZERO","CALLABILITY")
                                              if outcomes.get(a)==POSITIVE]
            result["causal_counterfactuals"]={
              "base_failed":True,"human_source_change_passed":True,
              "unrelated_sham_failed":True,"original_source_restored_failed":True,
              "autonomous_selection":False
            }
        elif any(x in ("UNKNOWN","UNKNOWN_NATIVE_APPARATUS","UNKNOWN_NATIVE_EVIDENCE") for x in outcomes.values()):
            result["status"]="UNKNOWN_INCOMPLETE_NATIVE_ARM_EVIDENCE"
        else:
            result["status"]="EXPOSED_GUARD_HYPOTHESIS_REJECTED_BY_NATIVE_CONTROLS"
        return result
    except Exception as err:
        result["status"]="UNKNOWN_EXPOSED_NATIVE_APPARATUS"
        result["error"]=type(err).__name__+": "+str(err)
        result["traceback_tail"]=traceback.format_exc(limit=8)[-2100:]
        return result
    finally:
        result["wall_seconds"]=time.monotonic()-started
        (dest/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    report=run(Path(os.environ["UDM_V12_OUT"]))
    print(json.dumps({
      "status":report["status"],"candidate_outcomes":report.get("candidate_outcomes"),
      "native_calls":report["native_calls"],"G2":"UNKNOWN",
      "packaging_source_opened":False,"autonomous_policy_acquired":False
    },sort_keys=True))
    # CI GREEN means an actual bounded human-defined causal diagnostic, never G2.
    raise SystemExit(0 if report["status"] in (
      "WARRANTED_BOUNDED_EXPOSED_HUMAN_GUARD_INTERVENTION_ONLY",
      "EXPOSED_GUARD_HYPOTHESIS_REJECTED_BY_NATIVE_CONTROLS") else 2)
