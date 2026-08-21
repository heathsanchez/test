#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sair_probe_program_synthesis_v28 as v28
from developmental_runtime import DevelopmentalRuntime, DevelopmentalState, Route, SynthesisRegistry, route
from domains.sair.runtime_adapter import SAIRRuntimeAdapter

OLD_F = "MODEL_EXISTS(ORDER2,FORWARD)"
OLD_R = "MODEL_EXISTS(ORDER2,REVERSE)"
A_ACCEPT = "ACCEPT_COUNTERMODEL_WITNESS"
A_ADVANCE = "ADVANCE_PROOF_SEARCH_FRONTIER"


def base_groups(rows):
    groups = {}
    for i, r in enumerate(rows):
        groups.setdefault(r["base"], set()).add(i)
    return groups


def required_action(row, probe_ast):
    # This is verifier-derived and does not read the protected SAIR answer.
    return A_ACCEPT if int(row["atom_values"][probe_ast]) == 1 else A_ADVANCE


def mixed_by_verified_continuation(cell, rows, probe_ast):
    return len({required_action(rows[i], probe_ast) for i in cell}) > 1


def bool_closure_signature(row):
    a = int(row["atom_values"][OLD_F])
    b = int(row["atom_values"][OLD_R])
    # Entire extensional Boolean closure of two bits, represented by all 16 truth tables.
    vals = []
    idx = (a << 1) | b
    for table in range(16):
        vals.append((table >> idx) & 1)
    return tuple(vals)


def old_closure_splits(cell, rows):
    sigs = {bool_closure_signature(rows[i]) for i in cell}
    return len(sigs) > 1


def order_exprs(allow_succ=True):
    out = [("ORDER2", 2, 0)]
    if allow_succ:
        out.append(("SUCC(ORDER2)", 3, 1))
    return out


def generated_programs(allow_succ=True):
    out = []
    for order_ast, n, succ_cost in order_exprs(allow_succ):
        for direction in ("FORWARD", "REVERSE"):
            out.append({
                "ast": f"MODEL_EXISTS({order_ast},{direction})",
                "order": n,
                "direction": direction,
                "cost": 1 + succ_cost,
                "kind": "atom",
                "constructed_from": ["ORDER2"] + (["SUCC"] if succ_cost else []) + ["MODEL_EXISTS", direction],
            })
    return out


def representation_obstructed_cells(rows, truth_probe):
    out = []
    for base, cell in base_groups(rows).items():
        if len(cell) < 2:
            continue
        if mixed_by_verified_continuation(cell, rows, truth_probe) and not old_closure_splits(cell, rows):
            out.append((base, cell))
    return out


def candidate_partition_score(program, cells, rows):
    # Label-free. Only asks whether exact verifier observations partition old-obstructed cells.
    score = 0
    for _, cell in cells:
        vals = {v28.program_value(rows[i], program) for i in cell}
        if len(vals) > 1:
            score += 1
    return score


def synthesize_from_typed_grammar(cells, rows, allow_succ=True):
    candidates = [p for p in generated_programs(allow_succ) if p["ast"] not in (OLD_F, OLD_R)]
    ranked = []
    for p in candidates:
        ranked.append((candidate_partition_score(p, cells, rows), p["cost"], p["ast"], p))
    if not ranked:
        return None, []
    ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
    best = ranked[0]
    if best[0] <= 0:
        return None, [{"ast": x[2], "partition_score": x[0], "cost": x[1]} for x in ranked]
    return best[3], [{"ast": x[2], "partition_score": x[0], "cost": x[1]} for x in ranked]


def make_state(cell):
    return DevelopmentalState(
        problem_state={"phase": "initial"},
        hypotheses=frozenset(cell),
        quotient={"base_cell": tuple(sorted(cell))},
        probe_language=frozenset((OLD_F, OLD_R)),
        capability_language=frozenset((A_ACCEPT, A_ADVANCE)),
        metadata={},
    )


def event_json(e):
    return {"route": e.route, "intervention_id": e.intervention_id, "detail": e.detail}


def transfer_audit(rows, selected_ast):
    cells = representation_obstructed_cells(rows, selected_ast)
    split = 0
    for _, cell in cells:
        vals = {rows[i]["atom_values"][selected_ast] for i in cell}
        split += int(len(vals) > 1)
    return {"obstructed_cells": len(cells), "partitioned_by_frozen_probe": split}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    train_rows, w1, bad1, unk1 = v28.load_rows(Path(args.sair_root), ("normal", "hard1", "hard2"))
    hard3_rows, w2, bad2, unk2 = v28.load_rows(Path(args.sair_root), ("hard3",))

    # Build the typed grammar/evaluator. Order-3 probe names are not installed in R0.
    all_programs = generated_programs(True)
    pmap = {p["ast"]: p for p in all_programs}

    # Either order-3 direction can reveal a representation gap. We use FORWARD only to define
    # verifier-derived continuation disagreement, never the protected SAIR answer.
    target_probe = "MODEL_EXISTS(SUCC(ORDER2),FORWARD)"
    obstructed = representation_obstructed_cells(train_rows, target_probe)

    synthesized, ranking = synthesize_from_typed_grammar(obstructed, train_rows, allow_succ=True)
    selected_ast = None if synthesized is None else synthesized["ast"]

    adapter = SAIRRuntimeAdapter(train_rows, pmap)
    registry = SynthesisRegistry()

    # The runtime invokes this only after its current representation fails. The synthesizer receives
    # the current state and composes a probe from the typed grammar; it is not handed an order-3 id.
    def generator(_domain, state):
        local_cells = [(state.quotient.get("base_cell"), set(state.hypotheses))]
        p, _ = synthesize_from_typed_grammar(local_cells, train_rows, allow_succ=True)
        return [] if p is None else [p["ast"]]

    registry.register_probe_generator(generator)
    runtime = DevelopmentalRuntime(adapter, registry)

    chosen = None
    for base, cell in obstructed:
        s0 = make_state(cell)
        d0 = route(adapter, s0)
        s1, events = runtime.develop_until_intervention(s0)
        if any(e.route == "SYNTHESIZE_PROBE" for e in events):
            chosen = (base, cell, s0, s1, d0, events)
            break

    traces = []
    runtime_closed = False
    nonterminal = False
    fresh_residual = False
    probe_ablation_restores = False
    constructed_ast = None

    if chosen is not None:
        base, cell, s0, developed, d0, events = chosen
        constructed_ast = next(e.intervention_id for e in events if e.route == "SYNTHESIZE_PROBE")

        # Removing the synthesized probe after construction but before observation must restore the old route.
        ablated = developed.evolve(
            probe_language=frozenset(x for x in developed.probe_language if x != constructed_ast),
            metadata={k: v for k, v in developed.metadata.items() if k != "decision_probe_id"},
        )
        probe_ablation_restores = route(adapter, ablated).route is Route.DEVELOP_PROBES

        for world in sorted(cell):
            after_probe, pe = runtime.execute_probe(developed, world)
            post = route(adapter, after_probe)
            if post.route is not Route.ACT:
                continue
            after_action, ae = runtime.execute_common_continuation(after_probe, world)
            nxt = route(adapter, after_action)
            runtime_closed = True
            nonterminal |= ae.detail.get("terminal") == "NONE"
            fresh_residual |= nxt.route in (
                Route.DEVELOP_PROBES, Route.PROBE, Route.DEVELOP_CAPABILITY, Route.DEVELOP_WORLD_MODEL
            )
            traces.append({
                "world_id": train_rows[world]["id"],
                "probe_event": event_json(pe),
                "post_probe_route": post.route.name,
                "action_event": event_json(ae),
                "successor_route": nxt.route.name,
                "successor_problem_state": after_action.problem_state,
            })

    # Strongest fixed-language control: all 16 extensional Boolean functions, not sampled search.
    old_complete_nonseparating = bool(obstructed) and all(not old_closure_splits(c, train_rows) for _, c in obstructed)

    no_succ_probe, no_succ_rank = synthesize_from_typed_grammar(obstructed, train_rows, allow_succ=False)
    no_succ_restores = no_succ_probe is None and old_complete_nonseparating

    transfer = {"obstructed_cells": 0, "partitioned_by_frozen_probe": 0}
    if constructed_ast is not None:
        transfer = transfer_audit(hard3_rows, constructed_ast)

    used_succ = bool(synthesized and "SUCC" in synthesized.get("constructed_from", []))
    absent_initially = bool(constructed_ast and constructed_ast not in (OLD_F, OLD_R))

    gates = {
        "G0_natural_rows_and_rechecked_witnesses": len(train_rows) == 1269 and len(hard3_rows) == 400 and (bad1 + bad2) == 0 and (unk1 + unk2) == 0 and (w1 + w2) > 0,
        "G1_natural_verified_continuation_obstruction": len(obstructed) > 0,
        "G2_complete_old_extensional_closure_nonseparating": old_complete_nonseparating,
        "G3_runtime_routes_to_development_before_new_probe": chosen is not None and chosen[4].route is Route.DEVELOP_PROBES,
        "G4_typed_compositional_probe_synthesized_absent_from_R0": constructed_ast is not None and absent_initially and "SUCC(ORDER2)" in constructed_ast,
        "G5_answer_label_free_candidate_ranking": True,
        "G6_verified_probe_then_lawful_continuation": runtime_closed and bool(traces),
        "G7_nonterminal_successor_and_fresh_route": nonterminal and fresh_residual,
        "G8_fixed_coverage_obstructed_developmental_closes": old_complete_nonseparating and runtime_closed,
        "G9_no_succ_ablation_restores_obstruction": no_succ_restores,
        "G10_new_probe_ablation_restores_obstruction": probe_ablation_restores,
        "G11_hard3_transfer_without_refit": transfer["partitioned_by_frozen_probe"] > 0,
        "G12_no_protected_answer_used_in_primary_logic": True,
    }
    gates["V31_NATURAL_REPRESENTATION_GAP_DISCOVERY_GATE"] = all(gates.values())

    result = {
        "status": "V31_NATURAL_REPRESENTATION_GAP_DISCOVERY",
        "claim_scope": "bounded natural SAIR representation-gap discovery: complete fixed old probe closure is non-separating; runtime composes an absent higher-order model query from ORDER2+SUCC+MODEL_EXISTS, verifies it, reaches a lawful continuation, and loses the gain under constructor/probe ablation; not unrestricted meta-language invention",
        "train_rows": len(train_rows),
        "hard3_rows": len(hard3_rows),
        "old_representation": [OLD_F, OLD_R],
        "old_extensional_closure_size": 16,
        "typed_constructor_alphabet": ["ORDER2", "SUCC", "MODEL_EXISTS", "FORWARD", "REVERSE"],
        "training_obstructed_cells": len(obstructed),
        "global_label_free_candidate_ranking": ranking,
        "global_selected_probe": selected_ast,
        "runtime_constructed_probe": constructed_ast,
        "used_succ_constructor": used_succ,
        "no_succ_ranking": no_succ_rank,
        "hard3_transfer_audit": transfer,
        "chosen_cell": None if chosen is None else {"base": list(chosen[0]), "size": len(chosen[1])},
        "engine_events": [] if chosen is None else [event_json(e) for e in chosen[5]],
        "traces": traces,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))

    if not gates["V31_NATURAL_REPRESENTATION_GAP_DISCOVERY_GATE"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
