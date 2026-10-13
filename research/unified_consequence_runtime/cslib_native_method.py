#!/usr/bin/env python3
"""CSLib native certificate compiler, from existing frozen source.

This repairs a previous native proof backend failure. It does NOT establish
method invention outside a supplied finite relation algorithm or close an
independently open CSLib theorem. The original source solver, independent
reference and target cases are reused unmodified. New native proof terms are
accepted only when checked by pinned upstream CSLib and Lean.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import runpy
from pathlib import Path

UPSTREAM_COMMIT = "4b88bcac4c0dec65b3f45b59e85f5397045efd8d"
PINNED_LEAN = "leanprover/lean4:v4.35.0-rc4"

def encode(obj):
    return json.dumps(obj, sort_keys=True, indent=2) + "\n"

def bisim_ref(case):
    """Independent symmetric greatest-fixed-point reference."""
    n, labels = case["n"], case["labels"]
    table = {(x, a): set() for x in range(n) for a in range(labels)}
    for x, a, y in case["edges"]:
        table[x, a].add(y)
    r = {(x, y) for x in range(n) for y in range(n)}
    while True:
        after = {
            (x, y) for x, y in r
            if all(
                all(any((u, v) in r for v in table[y, a])
                    for u in table[x, a])
                and all(any((u, v) in r for u in table[x, a])
                        for v in table[y, a])
                for a in range(labels)
            )
        }
        if after == r:
            return r
        r = after

def rewrite_native_certificate(source_lean, bisimulation):
    old = """theorem certified : LTS.IsSimulation sys sys relation := by
  intro s₁ s₂ hrel μ s₁' htr
  fin_cases s₁ <;> fin_cases s₂ <;> fin_cases μ <;> fin_cases s₁'
  all_goals simp_all [sys, relation]
"""
    new = """theorem certified : LTS.IsSimulation sys sys relation := by
  decide
"""
    if source_lean.count(old) != 1:
        raise ValueError("frozen original proof block changed")
    code = source_lean.replace(old, new)
    code = code.replace(
        "import Cslib.Foundations.Semantics.LTS.Simulation",
        "import Cslib.Foundations.Semantics.LTS.Bisimulation", 1,
    )
    if bisimulation:
        code = code.replace(
            "theorem seed :", 
            "theorem certified_bisimulation : LTS.IsBisimulation sys sys relation := by\n"
            "  decide\n"
            "theorem seed :", 1,
        )
        if "theorem certified_bisimulation" not in code:
            # A negative-seed case has no seed theorem.
            code = code.replace(
                "theorem seed_rejected :",
                "theorem certified_bisimulation : LTS.IsBisimulation sys sys relation := by\n"
                "  decide\n"
                "theorem seed_rejected :", 1,
            )
    if "fin_cases" in code or "sorry" in code or "admit" in code:
        raise AssertionError("untrusted proof path")
    return code

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    frozen = json.loads((args.original / "frozen.json").read_text())
    if frozen["upstream_sha"] != UPSTREAM_COMMIT:
        raise ValueError("CSLib source changed")
    if frozen["upstream_toolchain"] != PINNED_LEAN:
        raise ValueError("Lean checker changed")
    original = runpy.run_path(str(args.original / "run.py"))
    assert original["F"] == frozen
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for split in ("development", "holdout", "controls"):
        for case in frozen[split]:
            relation, history = original["synthesize"](case)
            if relation != original["independent"](case):
                raise AssertionError("independent original oracle mismatch")
            bisim = bisim_ref(case)
            proves_bisim = relation == bisim
            seed = tuple(case["seed"]) in relation
            assert seed == case["expect"]
            native = original["lean"](case, relation)
            if not seed:
                native = native[:native.index("theorem seed :")]
                native += (
                    f"theorem seed_rejected : ¬relation {case['seed'][0]} "
                    f"{case['seed'][1]} := by\n  decide\nend V10_{case['id']}\n"
                )
            native = rewrite_native_certificate(native, proves_bisim)
            out = args.out / (split + "_" + case["id"] + ".lean")
            out.write_text(native)
            rows.append({
                "id": case["id"], "split": split,
                "seed_proven": seed, "seed_refuted": not seed,
                "source_simulation_pairs": len(relation),
                "independent_bisimulation_pairs": len(bisim),
                "bisimulation_proof_requested": proves_bisim,
                "reference": "PASS",
                "proof_filename": out.name,
                "proof_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "native_lean": "PENDING",
            })

    case = next(c for c in frozen["controls"] if c["id"] == "mismatch")
    relation, _ = original["synthesize"](case)
    unsound = original["lean"](case, relation)
    unsound = unsound[:unsound.index("theorem certified :")]
    unsound += (
        "theorem forged_universal : LTS.IsSimulation sys sys "
        "(fun _ _ => True) := by\n  decide\nend V10_mismatch\n"
    )
    unsound = unsound.replace(
        "import Cslib.Foundations.Semantics.LTS.Simulation",
        "import Cslib.Foundations.Semantics.LTS.Bisimulation", 1)
    (args.out / "control_unsound_universal.lean").write_text(unsound)
    (args.out / "manifest.json").write_text(encode({
        "schema": "metalogic.cslib-native-proof-closure.v1",
        "original_case_sha256": hashlib.sha256((args.original / "frozen.json").read_bytes()).hexdigest(),
        "original_generator_sha256": hashlib.sha256((args.original / "run.py").read_bytes()).hexdigest(),
        "source_repo": "leanprover/cslib",
        "source_commit": UPSTREAM_COMMIT,
        "toolchain": PINNED_LEAN,
        "cases": rows,
        "negative_control_filename": "control_unsound_universal.lean",
        "scope": "previously frozen finite LTSs, checked under real CSLib Lean definitions",
        "proof_backend": "known Lean decidable proposition reflection",
        "new_scientific_generator": "NOT_CLAIMED",
        "native_verdict": "PENDING",
        "old_failed_native_run": 38237298379,
    }))
    print("NATIVE_CERTIFICATES_PREPARED=" + str(len(rows)))
    print("NATIVE_VERIFICATION=PENDING")

if __name__ == "__main__":
    main()
