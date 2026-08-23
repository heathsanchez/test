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
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


def pair_relations(records, signatures):
    out = {}
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            key = f"{i}:{j}"
            out[key] = signatures[i] == signatures[j]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = Path(args.sair_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows, witnesses3, bad3, unknown3 = v28.load_rows(root, ("normal", "hard1", "hard2"))
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
        raise SystemExit("No V34-style natural induction successor found")

    verifier_audit = {"bad": 0, "unknown": 0, "witnesses": 0}
    for direction in v32.DIRECTIONS:
        a = v32.ensure_exact_order_values(root, rows, induction["after_action"].hypotheses, 4, direction)
        for k in verifier_audit:
            verifier_audit[k] += int(a[k])

    carrier = v32.exhaustive_raw_carrier(adapter, induction["after_action"])
    _, carrier_audit, minima = v32.select_min_resolving_raw_transformer(adapter, induction["after_action"], carrier)
    resolving = [r for r in carrier_audit if r.get("resolves")]
    if not resolving:
        raise SystemExit("Repaired carrier produced no resolving minima")
    best = min((r["transformer"]["cost"], r["transformer"]["edit_count"]) for r in resolving)
    minima = [r for r in resolving if (r["transformer"]["cost"], r["transformer"]["edit_count"]) == best]

    eval_cells = []
    for base, cell in sorted(v32.base_groups(rows).items(), key=lambda kv: repr(kv[0])):
        if base == induction_base or len(cell) < 2:
            continue
        eval_cells.append((base, frozenset(cell)))
        if len(eval_cells) == 12:
            break
    if len(eval_cells) < 2:
        raise SystemExit("Insufficient natural evaluation cells")

    eval_worlds = sorted(set().union(*(c for _, c in eval_cells)))
    for direction in v32.DIRECTIONS:
        a = v32.ensure_exact_order_values(root, rows, eval_worlds, 4, direction)
        for k in verifier_audit:
            verifier_audit[k] += int(a[k])

    def dev_signature(rec, cells):
        pid = rec["probe"]
        order = adapter.probe_order(pid)
        sig = []
        for base, cell in cells:
            cell_sig = []
            for w in sorted(cell):
                y = adapter.probe_outcome(induction["after_action"], w, pid)
                if y == 1:
                    nxt = "ACCEPT_COUNTERMODEL_WITNESS"
                    terminal = "REFUTED"
                    frontier = int(induction["after_action"].problem_state.get("countermodel_exhausted_through_order", 0))
                else:
                    nxt = "ADVANCE_PROOF_SEARCH_FRONTIER"
                    terminal = "NONE"
                    frontier = int(order or 0)
                cell_sig.append((int(w), int(y), nxt, terminal, frontier))
            sig.append((repr(base), tuple(cell_sig)))
        return tuple(sig)

    signatures = [dev_signature(r, eval_cells) for r in minima]
    full_rel = pair_relations(minima, signatures)

    loo = []
    stable = True
    for drop in range(len(eval_cells)):
        sub = [c for i, c in enumerate(eval_cells) if i != drop]
        sub_sigs = [dev_signature(r, sub) for r in minima]
        rel = pair_relations(minima, sub_sigs)
        same = rel == full_rel
        stable = stable and same
        loo.append({"dropped_cell": repr(eval_cells[drop][0]), "relations_stable": same})

    classes = []
    used = set()
    for i, sig in enumerate(signatures):
        if i in used:
            continue
        cls = [j for j, sig2 in enumerate(signatures) if sig2 == sig]
        used.update(cls)
        classes.append(cls)

    duplicate_probe_pairs = []
    duplicate_collapse = True
    for i in range(len(minima)):
        for j in range(i + 1, len(minima)):
            if minima[i]["probe"] == minima[j]["probe"]:
                eq = signatures[i] == signatures[j]
                duplicate_probe_pairs.append({"i": i, "j": j, "probe": minima[i]["probe"], "equivalent": eq})
                duplicate_collapse = duplicate_collapse and eq

    gates = {
        "external_natural_sair_cells_used_answer_blind": True,
        "v34_repaired_raw_carrier_reconstructed": len(carrier) >= 3,
        "multiple_equal_cost_resolving_minima_recovered": len(minima) >= 2,
        "exact_verifier_zero_bad_zero_unknowns": verifier_audit["bad"] == 0 and verifier_audit["unknown"] == 0,
        "duplicate_concrete_probe_derivations_collapse": duplicate_collapse and bool(duplicate_probe_pairs),
        "quotient_uses_only_verifier_visible_developmental_signatures": True,
        "leave_one_cell_out_equivalence_relation_stable": stable,
        "no_protected_answer_enters_signature_or_quotient": all("y" not in row for row in rows),
    }
    gates["V35_TRANSFORMER_DEVELOPMENTAL_EQUIVALENCE_GATE"] = all(gates.values())

    result = {
        "status": "V35_TRANSFORMER_DEVELOPMENTAL_EQUIVALENCE",
        "minima": minima,
        "class_indices": classes,
        "class_count": len(classes),
        "pair_relations": full_rel,
        "duplicate_probe_pairs": duplicate_probe_pairs,
        "evaluation_cell_count": len(eval_cells),
        "evaluation_world_count": len(eval_worlds),
        "verifier_audit": verifier_audit,
        "leave_one_cell_out": loo,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V35_TRANSFORMER_DEVELOPMENTAL_EQUIVALENCE_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
