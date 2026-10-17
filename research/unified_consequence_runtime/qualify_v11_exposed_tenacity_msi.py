"""V11 retrospective/source-exposed original V104/MSI candidate census on Tenacity.

Uses exactly existing V9 training algorithm, but chooses V10's already
qualified class-method protected test boundary privately. This is a diagnostic
after source exposure; never a second prospective G2 trial. The original
Packaging heldout's source/test blob is not touched or fetched.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from types import FunctionType

from . import qualify_source_bound_g2_v9 as previous
from . import typed_native_authority_v10 as native
from . import typed_v104_msi_bridge_v7 as bridge

HERE=Path(__file__).resolve().parent
PROTOCOL=HERE/"archaeology/typed-v104-v11/FROZEN_DIAGNOSTIC.json"
FROZEN_GIT_BLOB="4cf29e6e9020c986a725401d5e9f34076aa6fab2"
SCHEMA="UDM_V11_EXPOSED_TENACITY_ORIGINAL_V104_MSI_RESULTS"


def original_training_with_v10():
    """Private function global namespace; no mutation of V9 or V6 source."""
    priv=dict(vars(previous), native=native)
    fn=FunctionType(previous._native.__code__,priv,"_native",
                    previous._native.__defaults__,previous._native.__closure__)
    fn.__kwdefaults__=previous._native.__kwdefaults__
    priv["_native"]=fn
    observe=FunctionType(previous._observation.__code__,priv,"_observation",
                         previous._observation.__defaults__,previous._observation.__closure__)
    observe.__kwdefaults__=previous._observation.__kwdefaults__
    priv["_observation"]=observe
    training=FunctionType(previous._execute_training.__code__,priv,"_execute_training",
                          previous._execute_training.__defaults__,
                          previous._execute_training.__closure__)
    training.__kwdefaults__=previous._execute_training.__kwdefaults__
    return training


def run(out):
    if os.environ.get("UDM_V11_EXPOSED_ONLY")!="ACK_EXPOSED_TENACITY_ONLY":
        raise ValueError("V11 diagnostic requires explicit exposed-source mode")
    git_blob=subprocess.check_output(["git","hash-object",str(PROTOCOL)],text=True).strip()
    if git_blob!=FROZEN_GIT_BLOB:
        raise ValueError("V11 exposed-diagnostic source freeze differs")
    p=json.loads(PROTOCOL.read_text())
    if p.get("schema")!="UDM_V11_EXPOSED_TENACITY_ORIGINAL_V104_MSI_DIAGNOSTIC":
        raise ValueError("wrong exposed diagnostic protocol")
    if p.get("v9_scientific_red_run")!=38985251065 or p.get("v10_source_native_qualified_run")!=38985872094:
        raise ValueError("original experimental lineage not preserved")
    if p["heldout_source_opened"] is not False:
        raise ValueError("unopened heldout original source must remain sealed")
    native.verified_v6_source()
    trial=Path(out).absolute()
    if not trial.is_absolute() or trial.exists():
        raise ValueError("new isolated evidence output required")
    trial.mkdir(parents=True)
    result={"schema":SCHEMA,"status":"UNKNOWN","G2":"UNKNOWN","G3":"UNKNOWN",
            "G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
            "state":"SOURCE_EXPOSED_DIAGNOSTIC_ONLY",
            "exposed_training":"jd/tenacity PR741",
            "heldout_source":"pypa/packaging PR1446",
            "packaging_source_opened":False,
            "prior_V9_RED":38985251065,
            "V10_class_authority_GREEN":38985872094,
            "native_calls":0,
            "original_protocol_git_blob":FROZEN_GIT_BLOB,
            "original_v104":"426c54f7c774560e0fabe7213c5ef333b1327c71",
            "original_msi":"56cfd7b523e3592cae4eafa5468f437ccb94dbe9"}
    started=time.monotonic()
    try:
        original=previous.frozen()
        holder={"native_calls":0}
        selected=original_training_with_v10()(holder,original,trial/"training")
        result["native_calls"]=holder["native_calls"]
        result["training"]=holder.get("training")
        if result["training"] is None:
            raise ValueError("no executed original training evidence")
        result["selected_candidate_policy"]=selected
        result["baseline_status"]=result["training"].get("baseline",{}).get("status")
        result["complete_policy_count"]=len([
           item for item in result["training"].get("choice",{}).get("profiles",{}).values()
           if item.get("TRAINING") is not None
        ])
        counts=result["training"].get("state_counts",{})
        result["source_native_candidate_classification"]=counts
        if result["baseline_status"]!=previous.BAD:
            result["status"]="UNKNOWN_NO_ORIGINAL_EXPOSED_PROTECTED_RESIDUAL"
        elif selected is not None:
            result["status"]="EXPOSED_TRAINING_UNIQUE_MSI_NONCOLD_POLICY_ONLY"
        elif (result["training"].get("choice",{}).get("status")==
              "UNKNOWN_INCOMPLETE_POLICY_NATIVE_PROFILES"):
            result["status"]="UNKNOWN_INCOMPLETE_ORIGINAL_SOURCE_NATIVE_MSI_PROFILES"
        else:
            result["status"]="EXPOSED_TENACITY_NO_UNIQUE_SOURCE_BOUND_MSI_POLICY"
        return result
    except Exception as error:
        result["status"]="UNKNOWN_EXPOSED_DIAGNOSTIC_APPARATUS"
        result["reason"]=type(error).__name__+": "+str(error)
        result["traceback"]=traceback.format_exc(limit=12)[-2400:]
        return result
    finally:
        result["wall_seconds"]=time.monotonic()-started
        (trial/"RESULT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    r=run(Path(os.environ["UDM_V11_OUT"]))
    print(json.dumps({"status":r["status"],"G2":r["G2"],
         "native_calls":r["native_calls"],"baseline":r.get("baseline_status"),
         "profiles":r.get("complete_policy_count"),"states":r.get("source_native_candidate_classification"),
         "packaging_opened":False},sort_keys=True))
    # Green for an executed negative/positive bounded diagnostic with complete
    # actual evidence; RED for unknown/incomplete. Never green as scientific G2.
    raise SystemExit(0 if r["status"] in (
        "EXPOSED_TENACITY_NO_UNIQUE_SOURCE_BOUND_MSI_POLICY",
        "EXPOSED_TRAINING_UNIQUE_MSI_NONCOLD_POLICY_ONLY") else 2)
