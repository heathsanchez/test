#!/usr/bin/env python3
"""Preregistered routing across TWO previously qualified source-native Go observers.

No new source/semantic observer is implemented here. This code selects, runs,
and logs already-qualified read-only native verifiers at exact PR source pins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/mgcheck_activation_20261015"))
from run_selector import prepare_source, evaluate, build_native_binary, load, put, run, candidate_plan

SEL_BLOB = "4409ae416d2b4aeb35a2fb8555a0cb7def60833d"
EXE_BLOB = "e2b21d3949bfdb9056ef369f4b044d592f9e6747"


def verifier_digest_check():
    for filename, expected in (("selector.go", SEL_BLOB),
                               ("run_test_operation.py", EXE_BLOB)):
        actual = run(["git", "hash-object", HERE / filename]).stdout.strip()
        if actual != expected:
            raise AssertionError("QUALIFIED_OBSERVER_BYTES_CHANGED " + filename +
                                 " expected " + expected + " got " + actual)


def build_selection_tool(out):
    run(["go", "build", "-o", out, HERE / "selector.go"], timeout=180)


def execute_logged(cmd, folder, label, *, timeout=360):
    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    t = time.monotonic()
    p = run(cmd, check=False, timeout=timeout)
    elapsed = int(1000 * (time.monotonic()-t))
    (folder / (label + ".log")).write_text(p.stdout, encoding="utf-8")
    return {"exit": p.returncode, "wall_ms": elapsed,
            "log_tail": p.stdout[-2000:], "command": [str(x) for x in cmd]}


def source_test_observer(binary, src, folder):
    """QUALIFIED Go AST Test selector and QUALIFIED original-native executor."""
    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    expected = {
        "schema": "metalogic.original-go-source-test-operation-extraction.v1",
        "old_original": src["old_sha"], "head_original": src["head_sha"],
    }
    selector_out = folder / "selected-original-tests.json"
    cmd = [
        binary, "-base", src["old"], "-head", src["head"], "-out", selector_out,
        "-source-repo", src["repo"], "-base-sha", src["old_sha"],
        "-head-sha", src["head_sha"],
    ]
    selection = execute_logged(cmd, folder, "select", timeout=90)
    if selection["exit"] != 0 or not selector_out.exists():
        return {
            "status": "UNKNOWN_NO_ELIGIBLE_ORIGINAL_GO_TEST_OPERATION",
            "qualified": False, "selected_test_functions": [],
            "selector": selection, "native": None, "ablation": None,
            "withdrawal": None, "source": expected,
            "all_process_ms": selection["wall_ms"],
        }
    manifest = load(selector_out)
    if manifest["schema"] != expected["schema"] or manifest["repo"] != src["repo"]:
        raise AssertionError("UNTRUSTED_SOURCE_TEST_MANIFEST")
    if manifest["base_sha"] != src["old_sha"] or manifest["head_sha"] != src["head_sha"]:
        raise AssertionError("SELECTED_AUTHOR_TEST_SOURCE_IDENTITY_CHANGED")
    if manifest.get("source_test_patch_only") is not True:
        raise AssertionError("SELECTOR_MODIFIED_ORIGINAL_IMPLEMENTATION")
    selected = manifest.get("selected", [])
    if not selected:
        return {
            "status": "UNKNOWN_NO_NEW_TEST_FUNCTION",
            "qualified": False, "selected_test_functions": [],
            "selector": selection, "native": None, "ablation": None,
            "withdrawal": None, "source": expected,
            "all_process_ms": selection["wall_ms"],
        }
    selected_names = sorted(x["function"] for x in selected)
    # Original unchanged qualified executor verifies native Go test actions.
    pristine = pathlib.Path(src["old"]).parent / "pristine-original"
    bare = pathlib.Path(src["old"]).parent / "upstream"
    run(["git", "-C", bare, "worktree", "add", "-q", "--detach", pristine,
         src["old_sha"]])
    if run(["git", "-C", pristine, "rev-parse", "HEAD"]).stdout.strip() != src["old_sha"]:
        raise AssertionError("PRISTINE_SOURCE_GUARD_FAIL")
    executor = HERE / "run_test_operation.py"
    native_report = folder / "native-author-tests.json"
    ablate_report = folder / "physical-absence.json"
    withdrawn_report = folder / "withdrawn-authority.json"
    common = [
        sys.executable, executor, "--manifest", selector_out,
        "--base", src["old"], "--head", src["head"],
    ]
    native = execute_logged(common + ["--out", native_report], folder, "native", timeout=500)
    ablate = execute_logged(common + ["--out", ablate_report,
                                      "--pristine", pristine, "--ablate"],
                            folder, "ablation", timeout=500)
    withdrawn = execute_logged(common + ["--out", withdrawn_report, "--withdraw"],
                               folder, "withdrawal", timeout=60)
    n = load(native_report) if native_report.exists() else {}
    a = load(ablate_report) if ablate_report.exists() else {}
    w = load(withdrawn_report) if withdrawn_report.exists() else {}
    qual = (
        native["exit"] == 0
        and n.get("result") ==
        "WARRANTED_BOUNDED_ORIGINAL_AUTHORED_TEST_RED_BASE_GREEN_HEAD"
        and ablate["exit"] == 0
        and a.get("result") == "UNKNOWN_REQUIRED_TEST_OPERATION_REMOVED"
        and withdrawn["exit"] == 0
        and w.get("result") == "STALE_EVIDENCE_WITHDRAWN"
    )
    if n.get("result", "").startswith("WARRANTED") and not qual:
        raise AssertionError("ORIGINAL_NATIVE_TEST_WARRANT_WITHOUT_CAUSAL_CONTROLS")
    return {
        "status": n.get("result", "UNKNOWN_NATIVE_GO_TEST_NOT_QUALIFIED"),
        "qualified": qual,
        "selected_test_functions": selected_names,
        "selector": selection,
        "native": {"call": native, "result": n.get("result"),
                   "named_test_executions": n.get("native_test_records", {})},
        "ablation": {"call": ablate, "result": a.get("result")},
        "withdrawal": {"call": withdrawn, "result": w.get("result")},
        "source": expected,
        "all_process_ms": sum(x["wall_ms"] for x in
                              (selection, native, ablate, withdrawn)),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=["protected", "cold"], required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--reference", type=pathlib.Path)
    args = p.parse_args()
    verifier_digest_check()
    args.out.mkdir(parents=True, exist_ok=True)
    subjects = load(HERE / "protected.json")["subjects"]
    import tempfile
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="mgcheck-native-observer-gate-"))
    fixed_go = scratch / "go-parser-learner"
    fixed_test = scratch / "previously-qualified-test-selector"
    build_native_binary(ROOT, fixed_go)
    build_selection_tool(fixed_test)
    # A default retained original parser method. This is the SAME frozen prior
    # operator, not a new candidate added after looking at protected PRs.
    a_plan = scratch / "original-identity.json"
    put(a_plan, candidate_plan("IDENTITY"))
    records = []
    for entry in subjects:
        src = prepare_source(entry, scratch / "sources")
        sub = args.out / entry["label"]
        # A and original finite stateless parser C are evaluated BEFORE a
        # test-only patch is applied to predecessor source by Test selector B.
        A = evaluate(fixed_go, src, "A:retained-original-identity",
                     sub / "A", mode="transfer", retained=a_plan)
        Cparse = evaluate(fixed_go, src, "C:full-old-parser-inventory",
                          sub / "Cparse", mode="acquire")
        B = source_test_observer(fixed_test, src, sub / "B")
        # A fully informed conventional executable INVENTORY can do everything
        # in this qualified finite two-observer portfolio (and more).
        C_success = Cparse["native_qualified"] or B["qualified"]
        rec = {
            "label": entry["label"], "repo": entry["repo"], "pr": entry["pr"],
            "source": {"base": entry["base"], "head": entry["head"]},
            "A_parser_old": A["status"], "A_success": A["native_qualified"],
            "B_existing_test_observer": B["status"], "B_success": B["qualified"],
            "B_selected_original_author_test_functions": B["selected_test_functions"],
            "C_parser_full": Cparse["status"],
            "C_full_existing_observer_inventory_success": C_success,
            "B_beats_A": B["qualified"] and not A["native_qualified"],
            "B_ties_C": B["qualified"] == C_success,
            "B_native_assertions_were_authored_by_original_PR": True,
            "B_observer_source_blobs": [SEL_BLOB, EXE_BLOB],
            "source_setup_ms": src["fetch_setup_ms"],
            "A_process_ms": A["total_process_ms"],
            "C_parser_ms": Cparse["total_process_ms"],
            "B_process_ms": B["all_process_ms"],
            "B_diagnostics": B["native"],
            "B_ablation": B["ablation"],
            "B_withdrawal": B["withdrawal"],
            "B_selector_log_tail": B["selector"]["log_tail"],
        }
        put(sub / "subject-evidence.json", rec)
        records.append(rec)
        print("NATIVE_OBSERVER_SUBJECT", json.dumps({
            "label": rec["label"], "A": rec["A_parser_old"],
            "B": rec["B_existing_test_observer"],
            "B_tests": rec["B_selected_original_author_test_functions"],
            "C": rec["C_full_existing_observer_inventory_success"],
            "B_beats_A": rec["B_beats_A"],
        }, sort_keys=True), flush=True)
    gained = [x["label"] for x in records if x["B_beats_A"]]
    ties = [x["label"] for x in records if x["B_ties_C"] and x["B_success"]]
    summary = {
        "schema": "mgcheck.native-existing-observer-activation.v1",
        "phase": args.phase,
        "frozen_original_observer_source_blobs": {
            "qualified_test_selector": SEL_BLOB, "qualified_test_executor": EXE_BLOB,
            "qualified_original_parser": "c5c4af86620d87fa0222ac2092ba0e529b16cc3e",
        },
        "records": records,
        "B_improves_A_native_on": gained,
        "B_ties_full_inventory_native_on": ties,
        "verdict": (
            "WARRANTED_BOUNDED_PROSPECTIVE_EXISTING_OBSERVER_ACTIVATION"
            if gained else "REJECTED_B_GREATER_THAN_A_ON_FROZEN_OBSERVER_HOLDOUTS"
        ),
        "economic_claim": "UNKNOWN_STRONG_MODEL_AND_FULL_LIFETIME_COSTS",
        "scientific_L7": "UNKNOWN_NO_NEW_METHOD_GENERATOR",
        "contract_authority": "ORIGINAL_AUTHOR_TESTS_NOT_INDEPENDENT_REQUIREMENTS",
        "cost": {
            "native_invocations_min": len(records) * 2,
            "total_experiment_steps_including_B_native_controls": len(records) * 6,
            "reported_source_setup_ms": sum(x["source_setup_ms"] for x in records),
            "reported_A_process_ms": sum(x["A_process_ms"] for x in records),
            "reported_C_parser_process_ms":
                sum(x["C_parser_ms"] for x in records),
            "reported_B_process_ms": sum(x["B_process_ms"] for x in records),
        },
        "negative_method_selection_lineage": "FIRST_EVAL_38641109338_REJECTED_0_OF_3",
        "new_ops_written": 0,
        "external_source_writes": 0,
    }
    # Independent cold job compares ONLY identity and observable source
    # outcomes, never raw Go timings, ephemeral paths or native stderr.
    stable = [{
        "label": x["label"], "source": x["source"],
        "A": x["A_parser_old"], "B": x["B_existing_test_observer"],
        "test_names": x["B_selected_original_author_test_functions"],
        "C": x["C_full_existing_observer_inventory_success"],
        "causal_status": (x["B_ablation"] or {}).get("result"),
        "withdrawn_status": (x["B_withdrawal"] or {}).get("result"),
    } for x in records]
    put(args.out / "semantic-summary.json", stable)
    put(args.out / "full-result.json", summary)
    if args.phase == "cold":
        if args.reference is None:
            raise ValueError("MISSING_PRIOR_FRESH_RUN_ARTIFACT_FOR_COLD")
        original = load(args.reference / "semantic-summary.json")
        if original != stable:
            raise AssertionError("COLD_RESTART_OR_SOURCE_SEMANTICS_DIVERGED")
        print("INDEPENDENT_COLD_RESTART_MATCHED_BOUNDED_NATIVE_SEMANTIC_RESULTS")
    print("QUALIFIED_EXISTING_OBSERVER_VERDICT", summary["verdict"])
    print("STRONG_AGENT_ECONOMIC_ADVANTAGE_UNKNOWN; NO_NEW_PRIMITIVE")


if __name__ == "__main__":
    main()
