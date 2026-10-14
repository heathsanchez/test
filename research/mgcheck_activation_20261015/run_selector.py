#!/usr/bin/env python3
"""Frozen inventory-selection experiment; unchanged native Go learner is the verifier.

This is an owned read-only research harness. It NEVER mutates an upstream repo.
Train and protected tasks execute in independent GitHub Actions jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OPS = ("IDENTITY", "EDGE_SPACE", "RUNE_SUBSTITUTION", "CASE_VARIANT", "CONCAT_SMALL")
NATIVE_PASS = {
    "WARRANTED_BOUNDED_RETAINED_PLAN_TRANSFER",
    "WARRANTED_BOUNDED_NEW_METHOD_PLAN_ACQUISITION",
}
FROZEN_LEARNER_BLOB = "c5c4af86620d87fa0222ac2092ba0e529b16cc3e"


def run(args, *, cwd=None, timeout=540, check=True):
    p = subprocess.run(
        [str(x) for x in args], cwd=str(cwd) if cwd else None, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
        env={**os.environ, "GOWORK": "off", "GOFLAGS": "-mod=mod"},
    )
    if check and p.returncode != 0:
        raise RuntimeError("RUN_FAILED " + " ".join(map(str, args)) +
                           " code=" + str(p.returncode) + " " + p.stdout[-3500:])
    return p


def put(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare_source(subject, workspace):
    name = subject["label"]
    local = workspace / name
    local.mkdir(parents=True, exist_ok=True)
    bare = local / "upstream"
    old = local / "base"
    head = local / "head"
    begun = time.monotonic()
    run(["git", "clone", "-q", "--no-checkout",
         "https://github.com/" + subject["repo"] + ".git", bare], timeout=360)
    ref = "refs/pull/" + str(subject["pr"]) + "/head"
    run(["git", "-C", bare, "fetch", "-q", "origin",
         ref + ":refs/heads/mg-frozen-author-head"], timeout=180)
    got = run(["git", "-C", bare, "rev-parse",
               "refs/heads/mg-frozen-author-head"]).stdout.strip()
    if got != subject["head"]:
        raise ValueError("FROZEN_AUTHOR_HEAD_MISMATCH " + name + " " + got)
    run(["git", "-C", bare, "cat-file", "-e", subject["base"] + "^{commit}"])
    run(["git", "-C", bare, "worktree", "add", "-q", "--detach", old, subject["base"]])
    run(["git", "-C", bare, "worktree", "add", "-q", "--detach", head, subject["head"]])
    for d, expected in ((old, subject["base"]), (head, subject["head"])):
        actual = run(["git", "-C", d, "rev-parse", "HEAD"]).stdout.strip()
        if actual != expected:
            raise ValueError("SOURCE_SHA_GUARD_REJECT " + name + " " + actual)
    return {
        "old": str(old), "head": str(head), "fetch_setup_ms":
        int(1000 * (time.monotonic() - begun)),
        "repo": subject["repo"], "pr": subject["pr"], "label": name,
        "old_sha": subject["base"], "head_sha": subject["head"],
    }


def build_native_binary(root, out):
    path = root / "research/mgcheck_nonregex_genesis_20261015/nonregex_method_learner.go"
    blob = run(["git", "hash-object", path]).stdout.strip()
    if blob != FROZEN_LEARNER_BLOB:
        raise ValueError("FROZEN_OPERATOR_IMPLEMENTATION_MUTATED " + blob)
    run(["go", "build", "-o", out, path], timeout=180)
    return blob


def candidate_plan(op):
    return {
        "Operator": op,
        "Observe": "GO_LAST_RETURN_ERROR_NIL",
        "InterfaceShape": "one_string_or_any_arg_two_returns_last_error",
        "AcquiredFrom": "PREEXISTING_FROZEN_HUMAN_AUTHORED_GRAMMAR",
        "Function": "",
        "Witness": "",
        "PlanLanguage": "human_fixed_primitives_composed_at_runtime",
    }


def evaluate(binary, source, arm, folder, *, mode, retained=None, invalid_head=False):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report_file = folder / "native.json"
    output_plan = folder / "method.json"
    call = [
        binary, "-mode", mode,
        "-old", source["old"], "-head", source["head"],
        "-old-sha", source["old_sha"],
        "-head-sha", "0" * 40 if invalid_head else source["head_sha"],
        "-out", report_file, "-plan", output_plan,
    ]
    if retained is not None:
        call += ["-retained", retained]
    start = time.monotonic()
    p = run(call, timeout=240, check=False)
    wall = int(1000 * (time.monotonic() - start))
    (folder / "stdout.log").write_text(p.stdout, encoding="utf-8")
    obj = load(report_file) if report_file.is_file() else {}
    result = {
        "arm": arm, "mode": mode, "repo": source["repo"], "pr": source["pr"],
        "base": source["old_sha"], "head": source["head_sha"],
        "exit": p.returncode, "status": obj.get("Status", "UNKNOWN_NO_NATIVE_REPORT"),
        "source_guard": obj.get("SourceGuard"),
        "operator": ((obj.get("AcquiredMethod") or
                      obj.get("RetainedMethod") or {}).get("Operator")),
        "functions": obj.get("FunctionCandidates", 0),
        "inputs": obj.get("InputCount", 0),
        "full_native_baseline_witnesses": obj.get("BaselineWitnessCount", 0),
        "old_focus_exit": obj.get("FocusOldExit"),
        "head_focus_exit": obj.get("FocusHeadExit"),
        "wrong_oracle_exit": obj.get("WrongOracleExit"),
        "no_test_ablation": obj.get("NoTestAblation"),
        "run_errors": obj.get("RunErrors", []),
        "learner_ms": obj.get("FullBudgetMillis"),
        "survey_ms": obj.get("SearchMillis"),
        "focused_replay_ms": obj.get("ReplayMillis"),
        "total_process_ms": wall,
        "observations_upper_bound": (2 * obj.get("FunctionCandidates", 0) *
                                     obj.get("InputCount", 0)),
    }
    result["native_qualified"] = (
        p.returncode == 0 and result["status"] in NATIVE_PASS
        and result["source_guard"] == "EXACT_HEADS_REVERIFIED"
        and not result["run_errors"]
        and result["old_focus_exit"] != 0
        and result["head_focus_exit"] == 0
        and result["wrong_oracle_exit"] != 0
        and result["no_test_ablation"] ==
        "EXECUTED_NO_GENERATED_TEST_NO_OBSERVATION"
    )
    put(folder / "meter.json", result)
    return result


def choose_policy(trials):
    """Freeze independent-source qualification, lower input cost, old stable order."""
    by_op = {}
    for idx, op in enumerate(OPS):
        ok = [row for row in trials if row["operator_candidate"] == op
              and row["native_qualified"]]
        families = {r["repo"] for r in ok}
        probes = sum(r["inputs"] for r in ok)
        by_op[op] = {
            "qualifying_distinct_training_repositories": len(families),
            "training_repositories": sorted(families),
            "sum_successful_operator_input_counts": probes,
            "fixed_prior_rank": idx,
        }
    eligible = [o for o in OPS if by_op[o]["qualifying_distinct_training_repositories"]]
    if not eligible:
        return None, by_op
    choice = min(
        eligible,
        key=lambda o: (-by_op[o]["qualifying_distinct_training_repositories"],
                       by_op[o]["sum_successful_operator_input_counts"],
                       by_op[o]["fixed_prior_rank"]),
    )
    return choice, by_op


def train(args, root, work, binary):
    manifest = load(root / "research/mgcheck_activation_20261015/train.json")
    subjects = manifest["subjects"]
    source_data = [prepare_source(row, work / "sources") for row in subjects]
    records = []
    store = Path(args.out)
    # A remains the unchanged production-originating first-witness policy.
    original = evaluate(binary, source_data[0], "A:old-selector-acquire",
                        store / "A" / "initial", mode="acquire")
    records.append(original)
    first_plan = store / "A" / "initial" / "method.json"
    a_plan = store / "a_method.json"
    if original["native_qualified"] and first_plan.exists():
        a_plan.write_bytes(first_plan.read_bytes())
    for source in source_data[1:]:
        if a_plan.exists():
            records.append(evaluate(
                binary, source, "A:retained-original",
                store / "A" / source["label"], mode="transfer", retained=a_plan,
            ))
    # B enumerates exactly the pre-existing 5 operators against the SAME
    # original source pairs. No heldout subjects loaded or visible to selector.
    candidates = []
    for source in source_data:
        for op in OPS:
            plan = store / "seed-inventory" / (op + ".json")
            put(plan, candidate_plan(op))
            row = evaluate(
                binary, source, "B:qualify-existing-" + op,
                store / "B" / source["label"] / op,
                mode="transfer", retained=plan,
            )
            row["operator_candidate"] = op
            candidates.append(row)
            records.append(row)
    chosen, scores = choose_policy(candidates)
    b_plan = store / "b_method.json"
    if chosen:
        put(b_plan, candidate_plan(chosen))
    selection = {
        "schema": "mgcheck.existing-inventory-selection.v1",
        "status": "CANDIDATE_RETAINED_EXISTING_OP" if chosen else "UNKNOWN_NO_QUALIFIED_OPERATOR",
        "policy": "max distinct training source families native error-to-success;"
                  " then min qualified input counts; then old fixed precedence",
        "selected_operator": chosen, "scores": scores,
        "A_native_status": original["status"],
        "A_operator": original["operator"],
        "training_rows": records,
        "training_source_pins": subjects,
        "frozen_learner_blob": FROZEN_LEARNER_BLOB,
        "cost": {
            "native_invocations": len(records),
            "reported_process_ms": sum(r["total_process_ms"] for r in records),
            "source_setup_ms": sum(s["fetch_setup_ms"] for s in source_data),
            "total_observation_upper_bound":
                sum(r["observations_upper_bound"] for r in records),
        },
        "no_new_method_primitive": True,
        "protected_outcome_visibility": "NONE_TRAIN_JOB_NO_PROTECTED_JSON_OPENED",
        "purpose": "historical training only; all training semantics already known",
    }
    put(store / "train-summary.json", selection)
    print("FROZEN_INVENTORY_SELECTION", chosen, scores, flush=True)


def protected(args, root, work, binary):
    subjects = load(root / "research/mgcheck_activation_20261015/protected.json")["subjects"]
    store = Path(args.out)
    plans = Path(args.plans)
    info = load(plans / "train-summary.json")
    # Files handed over only by GitHub Actions artefact between FRESH runners.
    A = plans / "a_method.json"
    B = plans / "b_method.json"
    chosen = info.get("selected_operator")
    if B.exists() and load(B)["Operator"] != chosen:
        raise AssertionError("PERSISTED_SELECTION_HASH_OR_OPERATOR_MISMATCH")
    if A.exists() and load(A)["Operator"] != info.get("A_operator"):
        raise AssertionError("A_OPERATOR_RETENTION_MISMATCH")
    records = []
    checks = []
    timings = []
    for subject in subjects:
        src = prepare_source(subject, work / "sources")
        timings.append(src["fetch_setup_ms"])
        # Equal-op conventional stateless enumerator sees ALL frozen methods.
        C = evaluate(binary, src, "C:full-stateless-enumerator",
                     store / subject["label"] / "C", mode="acquire")
        if A.exists():
            a = evaluate(binary, src, "A:old-selector-retained",
                         store / subject["label"] / "A", mode="transfer", retained=A)
        else:
            a = {"arm": "A", "status": "UNKNOWN_MISSING_A_PLAN",
                 "native_qualified": False, "total_process_ms": 0,
                 "observations_upper_bound": 0}
        if B.exists():
            b = evaluate(binary, src, "B:preselected-existing-inventory",
                         store / subject["label"] / "B", mode="transfer", retained=B)
        else:
            b = {"arm": "B", "status": "UNKNOWN_NO_B_PLAN",
                 "native_qualified": False, "total_process_ms": 0,
                 "observations_upper_bound": 0}
        records.extend([C, a, b])
        # PHYSICAL plan absence; the original unchanged native verifier must refuse.
        removed = evaluate(
            binary, src, "CONTROL:physically-absent-B-plan",
            store / subject["label"] / "removed",
            mode="transfer", retained=store / "nonexistent-method.json",
        )
        # Incorrect original source pin; independently refuses source authority.
        wrong = evaluate(
            binary, src, "CONTROL:wrong-SHA",
            store / subject["label"] / "wrong-head", mode="transfer",
            retained=B if B.exists() else store / "nonexistent-method.json",
            invalid_head=True,
        )
        records.extend([removed, wrong])
        ablation_ok = (removed["status"] == "UNKNOWN_RETAINED_METHOD_REMOVED"
                       and removed["exit"] != 0)
        guard_ok = wrong["status"] == "UNKNOWN_SOURCE_IDENTITY" and wrong["exit"] != 0
        checks.append({
            "subject": subject["label"], "repo": subject["repo"],
            "A": a["status"], "B": b["status"], "C": C["status"],
            "A_success": a["native_qualified"],
            "B_success": b["native_qualified"],
            "C_success": C["native_qualified"],
            "B_beats_A": b["native_qualified"] and not a["native_qualified"],
            "A_beats_B": a["native_qualified"] and not b["native_qualified"],
            "B_native_plan_removal_control": ablation_ok,
            "wrong_source_SHA_refusal": guard_ok,
        })
    any_gain = any(x["B_beats_A"] for x in checks)
    controls_good = all(x["B_native_plan_removal_control"] and
                        x["wrong_source_SHA_refusal"] for x in checks)
    if not controls_good:
        verdict = "UNKNOWN_FAILED_CAUSAL_OR_SOURCE_CONTROLS"
    elif any_gain:
        verdict = "WARRANTED_BOUNDED_PROSPECTIVE_EXISTING_OPERATOR_ACTIVATION_NOT_ECONOMIC"
    else:
        verdict = "REJECTED_PROSPECTIVE_B_BEATS_A_ON_FROZEN_TASKS"
    result = {
        "schema": "mgcheck.frozen-native-holdout.v1",
        "verdict": verdict,
        "old_selector": info.get("A_operator"),
        "new_selector": chosen,
        "protected_results": checks, "native_calls": records,
        "source_pins": subjects,
        "cold_restart": "PERSISTED_TRAIN_PLANS_NEW_GITHUB_ACTIONS_JOB",
        "cost": {
            "training_native_invocations": info["cost"]["native_invocations"],
            "training_process_ms": info["cost"]["reported_process_ms"],
            "training_setup_ms": info["cost"]["source_setup_ms"],
            "protected_process_ms": sum(r["total_process_ms"] for r in records),
            "protected_native_invocations": len(records),
            "protected_source_setup_ms": sum(timings),
            "all_reported_process_ms":
                info["cost"]["reported_process_ms"] +
                sum(r["total_process_ms"] for r in records),
            "all_native_observation_upper_bound":
                info["cost"]["total_observation_upper_bound"] +
                sum(r["observations_upper_bound"] for r in records),
        },
        "evidence_scope": [
            "Historical pre-disclosed PR source version delta, not new defect detection",
            "C is full finite source-native differential enumerator, not LLM coding agent",
            "No true normative independent contract for author head",
            "No source-family method invention or complete grammar inexpressibility proof",
            "No FLASH/Metatron live downstream integration in this selector experiment",
            "No full user/LLM labor, external setup economics, or strict commercial advantage",
            "No upstream writes, automatic patching, app deployment, or merge",
        ],
        "status_economics": "UNKNOWN_VS_FULLY_INFORMED_STRONG_AGENT",
        "status_general_L7": "UNKNOWN",
    }
    put(store / "holdout-summary.json", result)
    print("FROZEN_NATIVE_PROTECTED_VERDICT", verdict, flush=True)
    for c in checks:
        print("SUBJECT_VERDICT", json.dumps(c, sort_keys=True), flush=True)
    # Workflow GREEN signifies the measurement completed, NEVER scientific win.
    # Breached causal/source integrity does not permit promotion.
    if not controls_good:
        raise AssertionError("NATIVE_SOURCE_OR_ABLATION_CONTROLS_FAILED")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=["train", "protected", "self-check"], required=True)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--out", type=Path)
    p.add_argument("--plans", type=Path)
    args = p.parse_args()
    choice, score = choose_policy([
        {"operator_candidate": op, "native_qualified": True, "repo": family,
         "inputs": n}
        for op, family, n in (
            ("IDENTITY", "one", 2), ("EDGE_SPACE", "one", 9),
            ("EDGE_SPACE", "two", 9), ("RUNE_SUBSTITUTION", "three", 1)
        )
    ])
    if choice != "EDGE_SPACE":
        raise AssertionError("DETERMINISTIC_SCORE_SELF_CHECK " + str((choice, score)))
    if args.phase == "self-check":
        print("PASS_DETERMINISTIC_SCORE_SELF_CHECK")
        return
    if args.out is None:
        p.error("--out is required")
    root = args.root.resolve()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.phase == "protected" and args.plans is None:
        p.error("--plans is required for protected phase")
    # SOURCE VALIDATOR ITSELF IS THE SAME ORIGINAL GO CODE in both jobs.
    work = Path(tempfile.mkdtemp(prefix="mgcheck-inventory-native-"))
    binary = work / "frozen-go-learner"
    build_native_binary(root, binary)
    if args.phase == "train":
        train(args, root, work, binary)
    else:
        protected(args, root, work, binary)


if __name__ == "__main__":
    main()
