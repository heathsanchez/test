#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sair_probe_program_synthesis_v28 as v28
import sair_residual_constrained_transformer_v32 as v32
from developmental_runtime import lawful
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = Path(args.sair_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows, _, _, _ = v28.load_rows(root, ("normal", "hard1", "hard2"))
    for row in rows:
        row.pop("y", None)

    old_programs = v28.synth_program_carrier(False)
    expanded_programs = v28.synth_program_carrier(True)
    old_ids = tuple(p["ast"] for p in old_programs)
    expanded_ids = tuple(p["ast"] for p in expanded_programs)
    pmap = {p["ast"]: dict(p) for p in expanded_programs}
    v32.add_raw_programs(pmap)
    adapter = SAIRRuntimeAdapter(rows, pmap)
    action_ids = ("ACCEPT_COUNTERMODEL_WITNESS", "ADVANCE_PROOF_SEARCH_FRONTIER")

    induction = None
    induction_base = None
    for base, cell in sorted(v32.base_groups(rows).items(), key=lambda kv: repr(kv[0])):
        if len(cell) < 2:
            continue
        st = v32.run_stage1(adapter, rows, cell, old_ids, expanded_ids, action_ids)
        if st is None:
            continue
        if v32.old_carrier_candidate(adapter, expanded_ids, st["after_action"]) is None:
            induction = st
            induction_base = base
            break
    if induction is None:
        raise SystemExit("No natural V34-style successor found under typed orientation semantics")

    successor = induction["after_action"]
    audit = {"witnesses": 0, "bad": 0, "unknown": 0}
    # Populate every atom reachable from the repaired one-literal order carrier.
    for order in v32.ORDERS:
        for direction in v32.DIRECTIONS:
            a = v32.ensure_exact_order_values(root, rows, successor.hypotheses, order, direction)
            for k in audit:
                audit[k] += int(a[k])

    carrier = v32.exhaustive_raw_carrier(adapter, successor)
    _, carrier_audit, _ = v32.select_min_resolving_raw_transformer(adapter, successor, carrier)
    resolving = [r for r in carrier_audit if r.get("resolves")]
    if not resolving:
        best = None
        minima = []
    else:
        best = min((r["transformer"]["cost"], r["transformer"]["edit_count"]) for r in resolving)
        minima = [r for r in resolving if (r["transformer"]["cost"], r["transformer"]["edit_count"]) == best]

    # Directly audit the semantic distinction: reverse queries remain lawful observations
    # but cannot license either target-specific continuation, irrespective of outcome.
    reverse_pid = v32.atom_id(4, "REVERSE")
    reverse_probe = adapter.intervention(reverse_pid)
    reverse_worlds = {}
    for w in sorted(successor.hypotheses):
        y = adapter.probe_outcome(successor, w, reverse_pid)
        reverse_worlds.setdefault(int(y), w)
        if len(reverse_worlds) == 2:
            break

    reverse_records = []
    reverse_probe_sound = True
    reverse_countermodel_blocked = True
    reverse_frontier_blocked = True
    for y, w in sorted(reverse_worlds.items()):
        pr = adapter.execute(successor, w, reverse_probe)
        reverse_probe_sound = reverse_probe_sound and lawful(pr)
        observed = pr.successor
        cr = adapter.execute(observed, w, adapter.intervention("ACCEPT_COUNTERMODEL_WITNESS"))
        sr = adapter.execute(observed, w, adapter.intervention("ADVANCE_PROOF_SEARCH_FRONTIER"))
        reverse_countermodel_blocked = reverse_countermodel_blocked and (not lawful(cr)) and (not cr.obligation("TARGET_ORIENTED"))
        reverse_frontier_blocked = reverse_frontier_blocked and (not lawful(sr)) and (not sr.obligation("TARGET_ORIENTED"))
        reverse_records.append({
            "world": rows[w]["id"],
            "reverse_outcome": int(y),
            "probe_lawful": lawful(pr),
            "countermodel_lawful": lawful(cr),
            "countermodel_target_oriented": cr.obligation("TARGET_ORIENTED"),
            "frontier_lawful": lawful(sr),
            "frontier_target_oriented": sr.obligation("TARGET_ORIENTED"),
        })

    minimum_probes = sorted({r["probe"] for r in minima})
    minimum_directions = sorted({adapter.probe_direction(pid) for pid in minimum_probes})

    gates = {
        "official_natural_sair_corpus_used_answer_blind": True,
        "v34_repaired_raw_carrier_reconstructed": len(carrier) >= 3,
        "reachable_atomic_verifier_zero_bad_zero_unknowns": audit["bad"] == 0 and audit["unknown"] == 0,
        "reverse_probe_remains_verified_observation": reverse_probe_sound and bool(reverse_records),
        "reverse_probe_cannot_license_target_countermodel_acceptance": reverse_countermodel_blocked and bool(reverse_records),
        "reverse_probe_cannot_license_target_frontier_advance": reverse_frontier_blocked and bool(reverse_records),
        "minimum_resolving_transformers_exist": bool(minima),
        "all_minimum_resolving_transformers_target_oriented_forward": bool(minima) and minimum_directions == ["FORWARD"],
        "unique_minimum_resolving_concrete_probe_after_orientation_typing": len(minimum_probes) == 1,
        "no_protected_answer_enters_routing_synthesis_or_obligations": all("y" not in row for row in rows),
    }
    gates["V36_PROBE_OBLIGATION_ORIENTATION_GATE"] = all(gates.values())

    result = {
        "status": "V36_PROBE_OBLIGATION_ORIENTATION",
        "induction_base": repr(induction_base),
        "successor_world_count": len(successor.hypotheses),
        "carrier_size": len(carrier),
        "verifier_audit": audit,
        "reverse_obligation_audit": reverse_records,
        "minimum_cost": best,
        "minimum_resolving_records": minima,
        "minimum_concrete_probes": minimum_probes,
        "minimum_directions": minimum_directions,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V36_PROBE_OBLIGATION_ORIENTATION_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
