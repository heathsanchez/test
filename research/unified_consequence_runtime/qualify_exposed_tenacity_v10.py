"""Exposed Tenacity test-method authority diagnostic after V9 frozen RED.

Tenacity's changed original author assertion was not admitted by V9 because
V6 understood file::test_method but not file::TestClass::test_method.
This source has ALREADY been exposed. This procedure is NOT a prospective
G2 attempt. The Packaging future's source remains unopened.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from . import qualify_source_bound_g2_v9 as v9
from . import qualify_typed_v104_prospective_v7 as original
from . import typed_v104_msi_bridge_v7 as bridge
from . import typed_native_authority_v10 as v10


def run():
    t=time.monotonic()
    p=v9.frozen()
    task=p["task_roles"][0]
    ref=p["frozen_author_test_git_blob_refs"][0]
    with tempfile.TemporaryDirectory(prefix="udm-v10-exposed-tenacity-") as parent:
        root=Path(parent).resolve()
        prepared=original.prepare_task(task,ref,root/"training-input")
        original_context=bridge.construct_candidate(
            prepared["repo"],task["base"],[prepared["test"]],
            {"replacements":[]},root/"original-baseline-worktree")
        requires=tuple(original_context["required"])
        # Exact original method is an actual class member; no new node,
        # operator or hand-selected test method is permitted.
        witness="tests/test_tenacity.py::TestWaitConditions::test_wait_falsy_callable_is_called"
        if witness not in requires:
            raise ValueError("changed original protected class-method node absent")
        if not all(v10.accepts_class_method(x) for x in requires):
            raise ValueError("V10 class node grammar still misses original changed assertions")
        stage=v10.stage(prepared["repo"],original_context["candidate_commit"],
                       root/"typed-source-stage")
        observations=[]
        for index in range(2):
            event=v10.run_protected(
                prepared["repo"],original_context["candidate_commit"],
                root/"typed-source-stage",
                required=requires,paths=tuple(task["author_tests"]),
                interpreter=sys.executable,timeout=90)
            observations.append(event)
        identity=v10.verify_stage(
            prepared["repo"],original_context["candidate_commit"],
            root/"typed-source-stage")
        out={
            "schema":"UDM_V10_EXPOSED_ORIGINAL_TENACITY_CLASS_METHOD_DIAGNOSTIC",
            "source_role":"EXPOSED_TRAINING_DIAGNOSTIC_ONLY",
            "repository":task["repository"],"base_commit":task["base"],
            "original_head_test_git_oid":ref["git_oid"],
            "frozen_v9_science_run":38985251065,
            "frozen_v9_scientific_RED_preserved":True,
            "packaging_source_opened":False,
            "original_head_production_fetched":False,
            "required":list(requires),
            "protected_method":witness,
            "stage":identity["status"],
            "original_manifest_sha256":stage["typed_manifest_sha256"],
            "first":{"status":observations[0]["status"],
                     "junit":observations[0].get("junit"),
                     "executed":observations[0].get("executed"),
                     "native_exit":observations[0].get("native_exit"),
                     "native_calls":observations[0].get("native_calls")},
            "second":{"status":observations[1]["status"],
                      "junit":observations[1].get("junit"),
                      "executed":observations[1].get("executed"),
                      "native_exit":observations[1].get("native_exit"),
                      "native_calls":observations[1].get("native_calls")},
            "duration_seconds":time.monotonic()-t,
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G5":"UNKNOWN","G6":"UNKNOWN",
            "no_prospective_comparator":True}
        out["protected_method_observed"]=all(
            any(x==witness or x.startswith(witness+"[") for x in e.get("executed",[]))
            for e in observations)
        if not out["protected_method_observed"]:
            out["boundary"]="UNKNOWN_NATIVE_CLASS_METHOD_NOT_EXECUTED"
        elif all(x["status"]=="FAIL_NATIVE_PROTECTED" for x in observations):
            out["boundary"]="WARRANTED_BOUNDED_EXPOSED_PROTECTED_FAILURE_ONLY"
        else:
            out["boundary"]="UNKNOWN_NATIVE_PROTECTED_RESIDUAL_OR_OTHER_AUTHOR_SUITE_FAILURE"
        return out


if __name__=="__main__":
    report=run()
    # Public CI log is a small factual summary; do not expose source bodies.
    Path("qualification/v10/EXPOSED_TENACITY_RESULT.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"boundary":report["boundary"],
                      "two_native_calls":[report["first"]["native_calls"],
                                          report["second"]["native_calls"]],
                      "first":report["first"]["status"],
                      "second":report["second"]["status"],
                      "protected_method_observed":report["protected_method_observed"],
                      "G2":"UNKNOWN","packaging_source_opened":False},sort_keys=True))
    raise SystemExit(0 if report["protected_method_observed"]
                     and report["stage"]=="PASS_TYPED_STAGE_IDENTITY" else 2)
