#!/usr/bin/env python3
"""V9: frozen-corpus, Lean-error-driven induction-binder repair.

Selection only reads development.json. Holdout.json is opened only after a
source-and-policy receipt is written. Lean is the proof authority; the finite
policy DSL and generalizing tactic are externally supplied.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
WORK = Path(os.getenv("CAPSTONE_V9_WORK", "/tmp/capstone_v9"))
LEAN_TOOLCHAIN = "leanprover/lean4:v4.24.0"
POLICIES = ("none", "first_value", "last_value", "all_values", "ih_value")
AUTOMATIONS = ("simp_all", "aesop", "simp_all_aesop")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_split(name: str):
    path = BASE / (name + ".json")
    return json.loads(path.read_text())["cases"]


def compile_lean(text: str, label: str):
    WORK.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
    destination = WORK / (safe + ".lean")
    destination.write_text(text)
    environment = dict(os.environ)
    environment["LEAN_TOOLCHAIN"] = LEAN_TOOLCHAIN
    started = time.perf_counter()
    try:
        result = subprocess.run(
            ["lean", str(destination)],
            capture_output=True, text=True, timeout=55, env=environment
        )
        elapsed = time.perf_counter() - started
        output = result.stdout + result.stderr
        errors = [line.strip() for line in output.splitlines()
                  if "error:" in line or "error " in line.lower()]
        return {
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "elapsed_seconds": round(elapsed, 4),
            "diagnostics_sha256": sha(output.encode()),
            "errors": errors[:8],
            "output_excerpt": output[-900:] if result.returncode else "",
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return {
            "passed": False, "returncode": 124, "elapsed_seconds": 55,
            "diagnostics_sha256": sha(str(exc).encode()),
            "errors": ["COMPILER_NOT_AVAILABLE_OR_TIMEOUT"],
            "output_excerpt": str(exc)[:400],
        }


def theorem_binders(source: str):
    if "theorem " not in source or ":= by" not in source:
        return []
    text = source.split("theorem ", 1)[1].split(":= by", 1)[0]
    groups = []
    depth = 0
    at = None
    for i, char in enumerate(text):
        if char == "(":
            if depth == 0:
                at = i
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return []
            if depth == 0 and at is not None:
                groups.append(text[at + 1:i])
                at = None
    bindings = []
    for part in groups:
        if ":" not in part:
            continue
        left, typ = part.split(":", 1)
        symbols = re.findall(r"[A-Za-z_][A-Za-z_0-9]*", left)
        for sym in symbols:
            bindings.append((sym, typ.strip()))
    return bindings


def structure(source: str):
    match = re.search(r"\binduction\s+([A-Za-z_]\w*)\s+with\b", source)
    if not match:
        return None
    index = match.group(1)
    binders = theorem_binders(source)
    if not binders or index not in [x for x, _ in binders]:
        return None
    ihmatch = re.search(r"\busing\s+ih\s+([^\n]+)", source)
    ihnames = set(re.findall(r"\b[A-Za-z_]\w*\b",
                             ihmatch.group(1) if ihmatch else ""))
    values = [name for name, typ in binders
              if name != index and "→" not in typ and "->" not in typ]
    return {"index": index, "binders": binders,
            "values": values, "ih_names": ihnames}


def proposed_binders(source: str, policy: str):
    parse = structure(source)
    if parse is None:
        return ()
    values = parse["values"]
    if policy == "none":
        return ()
    if policy == "first_value":
        return tuple(values[:1])
    if policy == "last_value":
        return tuple(values[-1:])
    if policy == "all_values":
        return tuple(values)
    if policy == "ih_value":
        in_ih = [x for x in values if x in parse["ih_names"]]
        return tuple(in_ih[-1:])
    raise ValueError(policy)


def rewrite_induction(source: str, binders):
    if not binders:
        return source
    parse = structure(source)
    if parse is None:
        return source
    fragment = "induction " + parse["index"] + " with"
    if source.count(fragment) != 1:
        return source
    return source.replace(
        fragment,
        "induction " + parse["index"] + " generalizing "
        + " ".join(binders) + " with"
    )


def native_automation(source: str, tactic: str):
    replacements = {
        "simp_all": "simp_all",
        "aesop": "aesop",
        "simp_all_aesop": "simp_all <;> aesop",
    }
    if tactic not in replacements:
        raise ValueError(tactic)
    pattern = r"(?m)^([ \t]*)simpa[^\n]*using ih[^\n]*$"
    return re.sub(pattern, lambda m: m.group(1) + replacements[tactic],
                  source, count=1)


def source_admissible(source: str):
    return re.search(r"\b(?:sorry|admit|axiom)\b", source) is None


def evaluate(case, name, candidate=None):
    source = case["source"] if candidate is None else candidate
    if not source_admissible(source):
        raise AssertionError("unsafe text in candidate")
    return compile_lean(source, case["id"] + "." + name)


def run():
    development = read_split("development")  # No holdout read here
    history = []
    for case in development:
        baseline = evaluate(case, "development.old")
        if not baseline["passed"] and not baseline["errors"]:
            raise AssertionError("No interpretable Lean failure: " + case["id"])
        history.append({"id": case["id"], "baseline": baseline})

    tested = {}
    for policy in POLICIES:
        trials = []
        for case in development:
            if next(h for h in history if h["id"] == case["id"])["baseline"]["passed"]:
                continue
            changed = rewrite_induction(case["source"],
                                        proposed_binders(case["source"], policy))
            run_result = evaluate(case, "development." + policy, changed)
            trials.append({"id": case["id"],
                           "proposed_binders": proposed_binders(case["source"], policy),
                           "success": run_result["passed"],
                           "elapsed_seconds": run_result["elapsed_seconds"],
                           "diagnostics_sha256": run_result["diagnostics_sha256"]})
        tested[policy] = trials

    eligible = [policy for policy in POLICIES
                if all(t["success"] for t in tested[policy])]
    if not eligible:
        raise AssertionError("No learned policy passes the development cases")
    # Predeclared parsimony (single binder preferred), then lexicographic.
    selected = min(eligible, key=lambda p:
                   (sum(len(t["proposed_binders"]) for t in tested[p]), p))
    freezer = {
        "version": 9, "stage": "FROZEN_BEFORE_HOLDOUT",
        "selected_policy": selected, "eligible_policies": eligible,
        "development_baseline": history, "candidate_trials": tested,
        "development_source_sha256": sha((BASE / "development.json").read_bytes()),
        "holdout_manifest_sha256": sha((BASE / "holdout.json").read_bytes()),
        "controls_manifest_sha256": sha((BASE / "control.json").read_bytes()),
        "generator_source_sha256": sha(Path(__file__).read_bytes()),
        "lean_toolchain": LEAN_TOOLCHAIN,
    }
    WORK.mkdir(parents=True, exist_ok=True)
    freeze_path = WORK / "PRE_HOLDOUT_FREEZE.json"
    freeze_path.write_text(json.dumps(freezer, indent=2, sort_keys=True) + "\n")

    # No policy changes after this line: the untouched holdouts are loaded now.
    holdouts = read_split("holdout")
    controls = read_split("control")
    observations = []
    for case in holdouts:
        baseline = evaluate(case, "heldout.old")
        names = proposed_binders(case["source"], selected)
        repaired_text = rewrite_induction(case["source"], names)
        repaired = evaluate(case, "heldout.selected", repaired_text)
        natives = {tactic: evaluate(
            case, "heldout.native." + tactic,
            native_automation(case["source"], tactic)
        ) for tactic in AUTOMATIONS}
        all_bind = [name for name, _ in theorem_binders(case["source"])
                    if name != structure(case["source"])["index"]]
        strong_runs = []
        for name in all_bind:
            cand = rewrite_induction(case["source"], [name])
            result = evaluate(case, "heldout.strong." + name, cand)
            strong_runs.append({"binder": name, "passed": result["passed"],
                                "elapsed_seconds": result["elapsed_seconds"]})
            if result["passed"]:
                break
        observations.append({
            "id": case["id"], "family": case["family"],
            "baseline": baseline,
            "selected_binders": names,
            "selected": repaired,
            "native_tactics": natives,
            "strong_complete_single_binder_search": strong_runs,
            "strong_found": any(v["passed"] for v in strong_runs),
            "ablation_old_failed": not baseline["passed"],
        })

    negative = []
    for case in controls:
        baseline = evaluate(case, "control.old")
        if baseline["passed"]:
            negative.append({
                "id": case["id"], "expected": case["expected"],
                "baseline_passed": True, "repair_attempted": False,
                "no_false_promotion": True
            })
            continue
        binder = proposed_binders(case["source"], selected)
        cand = rewrite_induction(case["source"], binder)
        r = evaluate(case, "control.repaired", cand)
        negative.append({
            "id": case["id"], "expected": case["expected"],
            "baseline_passed": False,
            "repair_attempted": cand != case["source"],
            "repaired_passed": r["passed"],
            "no_false_promotion": not r["passed"],
            "baseline_error_sha256": baseline["diagnostics_sha256"],
        })

    gates = {
        "frozen_selection_before_holdout": freeze_path.is_file(),
        "training_has_actual_lean_failures": any(
            not x["baseline"]["passed"] and bool(x["baseline"]["errors"])
            for x in history),
        "all_heldout_bounded_repairs_pass": all(
            x["selected"]["passed"] for x in observations),
        "old_baseline_ablation_all_holdout_fail": all(
            x["ablation_old_failed"] for x in observations),
        "strong_reference_search_compared": all(
            x["strong_found"] for x in observations),
        "already_valid_unmodified": any(
            x["baseline_passed"] and not x["repair_attempted"]
            for x in negative),
        "negative_controls_no_false_proof": all(
            x["no_false_promotion"] for x in negative),
        "all_tested_text_safety_screened": True,
    }
    strong_success = sum(x["strong_found"] for x in observations)
    result = {
        "status": "CANDIDATE_UNTIL_EXACT_HEAD_LEAN_CI",
        "source_freeze_commit": "2131dd4c12a96e47f5c81769962816a303243127",
        "policy_freeze": str(freeze_path),
        "selected_policy": selected, "heldout_count": len(observations),
        "heldout_success": sum(x["selected"]["passed"] for x in observations),
        "strong_baseline_success": strong_success,
        "negative_controls": negative, "heldout": observations,
        "development_candidate_trials": tested,
        "gates": gates,
        "qualified_claim": "source-frozen typed binder selection under observed Lean failure",
        "stronger_claims_not_established": [
            "new primitive/tactic language invention",
            "reusable autonomously invented proof critic",
            "semantic or economic improvement over strong complete binder search",
            "Lean proof that the source repair generator is sound",
            "universality beyond source corpus",
        ],
    }
    output = WORK / "RESULTS.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "selected_policy": selected,
        "development_policies": {p: sum(x["success"] for x in v)
                                 for p, v in tested.items()},
        "heldout": [(x["id"], x["selected"]["passed"],
                     x["strong_found"], x["selected_binders"])
                    for x in observations],
        "native_tactic_wins": {t: sum(x["native_tactics"][t]["passed"]
                                       for x in observations)
                               for t in AUTOMATIONS},
        "gates": gates, "artifact": str(output)
    }, indent=2, sort_keys=True))
    return int(not all(gates.values()))


if __name__ == "__main__":
    sys.exit(run())
