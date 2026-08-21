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
import sair_bounded_model_adequacy_v25 as v25
import sair_raw_adequacy_v24 as v24
from developmental_runtime import DevelopmentalRuntime, DevelopmentalState, Route, SynthesisRegistry, route
from domains.sair.probe_operator import induce_numeric_literal_shift, expand_numeric_literal_shift
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


ORDER4 = "MODEL_EXISTS(4,FORWARD)"
ORDER1 = "MODEL_EXISTS(1,FORWARD)"


def base_groups(rows):
    groups = {}
    for i, row in enumerate(rows):
        groups.setdefault(row["base"], set()).add(i)
    return groups


def make_state(cell, old_probe_ids, actions):
    return DevelopmentalState(
        problem_state={"phase": "initial", "countermodel_exhausted_through_order": 0},
        hypotheses=frozenset(cell),
        quotient={"base_cell": tuple(sorted(cell))},
        probe_language=frozenset(old_probe_ids),
        capability_language=frozenset(actions),
        metadata={},
    )


def event_json(e):
    return {"route": e.route, "intervention_id": e.intervention_id, "detail": e.detail}


def raw_problem_map(root: Path):
    out = {}
    for src in ("normal", "hard1", "hard2"):
        for raw in v24.load_jsonl(root / "examples" / "problems" / f"{src}.jsonl"):
            out[str(raw["id"])] = raw
    return out


def add_exact_order_values(root: Path, rows, indices, program_id: str, order: int):
    raw_map = raw_problem_map(root)
    witnesses = bad = unknown = 0
    for i in sorted(indices):
        row = rows[i]
        raw = raw_map[str(row["id"])]
        _, _, eqs = v24.observations(raw)
        e1, e2 = eqs
        ok, table, status = v25.sat_counterexample(e1, e2, N=order)
        unknown += int(status == "unknown")
        if ok:
            witnesses += 1
            if not v25.recheck(e1, e2, table):
                bad += 1
        row["atom_values"][program_id] = int(ok)
    return witnesses, bad, unknown


def learned_ops(state):
    return [dict(x) for x in state.metadata.get("learned_probe_operators", ())]


def make_registry(expanded_ids):
    reg = SynthesisRegistry()
    reg.register_probe_generator(lambda _d, _s: tuple(expanded_ids))
    reg.register_probe_operator_inducer(induce_numeric_literal_shift)
    reg.register_probe_operator_expander(expand_numeric_literal_shift)
    return reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = Path(args.sair_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows, witnesses3, bad3, unknown3 = v28.load_rows(root, ("normal", "hard1", "hard2"))
    # Remove protected answers entirely before any runtime object is constructed.
    for row in rows:
        row.pop("y", None)

    old_programs = v28.synth_program_carrier(False)
    expanded_programs = v28.synth_program_carrier(True)
    pmap = {p["ast"]: dict(p) for p in expanded_programs}
    pmap[ORDER4] = {"ast": ORDER4, "order": 4, "direction": "FORWARD", "cost": 3, "kind": "atom"}
    pmap[ORDER1] = {"ast": ORDER1, "order": 1, "direction": "FORWARD", "cost": 2, "kind": "atom"}

    adapter = SAIRRuntimeAdapter(rows, pmap)
    expanded_ids = tuple(p["ast"] for p in expanded_programs)
    old_ids = tuple(p["ast"] for p in old_programs)
    action_ids = ("ACCEPT_COUNTERMODEL_WITNESS", "ADVANCE_PROOF_SEARCH_FRONTIER")

    registry = make_registry(expanded_ids)
    runtime = DevelopmentalRuntime(adapter, registry)

    # Select an answer-blind natural cell for which the frozen V30 runtime must
    # develop its probe language and whose selected order-3 branch has an exact
    # no-countermodel outcome, enabling the nonterminal successor.
    chosen = None
    for base, cell in sorted(base_groups(rows).items(), key=lambda kv: repr(kv[0])):
        if len(cell) < 2:
            continue
        s0 = make_state(cell, old_ids, action_ids)
        developed, events = runtime.develop_until_intervention(s0)
        synth = next((e.intervention_id for e in events if e.route == "SYNTHESIZE_PROBE"), None)
        if synth is None:
            continue
        zero_worlds = [i for i in sorted(cell) if adapter.probe_outcome(developed, i, synth) == 0]
        if not zero_worlds:
            continue
        chosen = (base, cell, s0, developed, events, synth, zero_worlds[0])
        break

    if chosen is None:
        result = {"status": "NO_V30_NONTERMINAL_NATURAL_CELL", "gates": {"V31_RUNTIME_PROBE_OPERATOR_RECURSION_GATE": False}}
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    base, cell, s0, developed, events1, first_probe, actual = chosen
    after_probe1, probe_event1 = runtime.execute_probe(developed, actual)
    learned1 = learned_ops(after_probe1)
    decision1 = route(adapter, after_probe1)
    after_action1, action_event1 = runtime.execute_common_continuation(after_probe1, actual)
    successor_route = route(adapter, after_action1)

    # Before enabling any recursively generated order-4 observation, audit whether
    # the supplied pre-operator V28 extension carrier can already repair the new
    # successor residual. If yes, promotion to operator use is not licensed.
    ablated_registry = SynthesisRegistry()
    ablated_registry.register_probe_generator(lambda _d, _s: expanded_ids)
    old_successor_candidate = ablated_registry.synthesize_probe_extension(adapter, after_action1)
    old_grammar_exhausted = old_successor_candidate is None

    if not old_grammar_exhausted:
        gates = {
            "stage1_v30_trace_reproduced": events1[0].route == "DEVELOP_PROBES" and decision1.route is Route.ACT,
            "operator_induced_automatically": bool(learned1),
            "operator_retained_in_state": bool(after_probe1.lawbook),
            "nonterminal_successor_produced": action_event1.detail["terminal"] == "NONE",
            "successor_old_probe_completecover_obstruction": False,
            "V31_RUNTIME_PROBE_OPERATOR_RECURSION_GATE": False,
        }
        result = {
            "status": "OLD_PROBE_GRAMMAR_STILL_VIABLE",
            "chosen_base_cell": list(base),
            "chosen_cell_size": len(cell),
            "first_probe": first_probe,
            "old_successor_candidate": old_successor_candidate,
            "learned_probe_operators": learned1,
            "gates": gates,
        }
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    # The old carrier is exhausted. Only now make the raw verifier capable of
    # evaluating the recursively generated +1 and wrong-sign control queries.
    w4, b4, u4 = add_exact_order_values(root, rows, after_action1.hypotheses, ORDER4, 4)
    w1, b1, u1 = add_exact_order_values(root, rows, after_action1.hypotheses, ORDER1, 1)

    # Prefer a nonterminal order-4 branch if one exists; rebuild the stage-1 trace
    # for that same world so the entire causal chain uses one natural problem.
    order4_zero = [i for i in sorted(after_action1.hypotheses) if rows[i]["atom_values"][ORDER4] == 0]
    if order4_zero and order4_zero[0] != actual:
        actual = order4_zero[0]
        after_probe1, probe_event1 = runtime.execute_probe(developed, actual)
        decision1 = route(adapter, after_probe1)
        after_action1, action_event1 = runtime.execute_common_continuation(after_probe1, actual)
        learned1 = learned_ops(after_probe1)

    developed2, events2 = runtime.develop_until_intervention(after_action1)
    second_probe = next((e.intervention_id for e in events2 if e.route == "SYNTHESIZE_PROBE"), None)

    second_trace = None
    second_restored = False
    recursive_residual = False
    if second_probe is not None and events2[-1].route == "PROBE":
        after_probe2, probe_event2 = runtime.execute_probe(developed2, actual)
        decision2 = route(adapter, after_probe2)
        second_restored = decision2.route is Route.ACT and bool(decision2.commitments)
        if second_restored:
            after_action2, action_event2 = runtime.execute_common_continuation(after_probe2, actual)
            fresh2 = route(adapter, after_action2)
            recursive_residual = fresh2.route in (Route.DEVELOP_PROBES, Route.PROBE, Route.DEVELOP_CAPABILITY, Route.DEVELOP_WORLD_MODEL)
            second_trace = {
                "probe_event": event_json(probe_event2),
                "post_probe_route": decision2.route.name,
                "continuation_event": event_json(action_event2),
                "successor_route": fresh2.route.name,
                "successor_problem_state": after_action2.problem_state,
            }

    # Ablate retained operator from explicit developmental state. The already
    # audited static carrier remains available; if synthesis still succeeds the
    # operator was not load-bearing.
    meta_ablated = dict(after_action1.metadata)
    meta_ablated.pop("learned_probe_operators", None)
    op_ablated_state = after_action1.evolve(metadata=meta_ablated, lawbook=())
    op_ablated_candidate = registry.synthesize_probe_extension(adapter, op_ablated_state)

    # Wrong-sign control gets the same operator interface but delta=-1.
    wrong = {
        "id": "NUMERIC_LITERAL_SHIFT(-1)",
        "kind": "NUMERIC_LITERAL_SHIFT",
        "delta": -1,
        "source_probe": first_probe,
        "verified_probe": first_probe,
        "cost": 2,
    }
    wrong_state = after_action1.evolve(metadata={**after_action1.metadata, "learned_probe_operators": (wrong,)}, lawbook=(wrong["id"],))
    wrong_registry = SynthesisRegistry()
    wrong_registry.register_probe_operator_expander(expand_numeric_literal_shift)
    wrong_candidate = wrong_registry.synthesize_probe_extension(adapter, wrong_state)

    learned_plus_one = any(op.get("kind") == "NUMERIC_LITERAL_SHIFT" and int(op.get("delta", 0)) == 1 for op in learned1)
    order4_generated = second_probe == ORDER4
    preoperator_ids = set(expanded_ids) | set(old_ids)

    gates = {
        "external_sair_rows_used_without_answers": len(rows) == 1269 and all("y" not in r for r in rows),
        "stage1_router_selected_develop_probes": events1[0].route == "DEVELOP_PROBES",
        "stage1_probe_verified_and_split": probe_event1.route == "EXECUTE_PROBE" and decision1.route is Route.ACT,
        "operator_induced_automatically": learned_plus_one,
        "operator_retained_in_explicit_state": learned_plus_one and any("NUMERIC_LITERAL_SHIFT" in x for x in after_probe1.lawbook),
        "first_continuation_nonterminal": action_event1.detail["terminal"] == "NONE",
        "first_successor_is_fresh_epistemic_residual": successor_route.route is Route.DEVELOP_PROBES,
        "successor_old_probe_completecover_obstruction": old_grammar_exhausted,
        "second_extension_generated_by_retained_operator": order4_generated and second_probe not in preoperator_ids,
        "all_order3_and_order4_witnesses_rechecked_no_unknown": bad3 == 0 and unknown3 == 0 and b4 == 0 and u4 == 0,
        "second_probe_restores_common_lawful_continuation": second_restored,
        "operator_ablation_restores_successor_obstruction": op_ablated_candidate is None,
        "wrong_sign_shift_does_not_repair_successor": wrong_candidate is None,
        "second_extension_causally_depends_on_first": learned_plus_one and op_ablated_candidate is None and order4_generated,
        "no_protected_answer_routing_or_selection": all("y" not in r for r in rows),
    }
    gates["V31_RUNTIME_PROBE_OPERATOR_RECURSION_GATE"] = all(gates.values())

    result = {
        "status": "V31_RUNTIME_PROBE_OPERATOR_RECURSION",
        "claim_scope": "bounded natural recursive epistemic development from verified probe-program synthesis to retained numeric probe-operator reuse; not mutation-grammar invention or broad SAIR generalization",
        "chosen_base_cell": list(base),
        "chosen_cell_size": len(cell),
        "actual_world": rows[actual]["id"],
        "first_probe": first_probe,
        "first_engine_events": [event_json(e) for e in events1],
        "first_probe_event": event_json(probe_event1),
        "first_continuation_event": event_json(action_event1),
        "learned_probe_operators": learned1,
        "successor_route_before_second_development": successor_route.route.name,
        "old_successor_candidate_without_operator": old_successor_candidate,
        "order4_witnesses_rechecked": w4,
        "order4_unknown_queries": u4,
        "second_engine_events": [event_json(e) for e in events2],
        "second_probe": second_probe,
        "second_trace": second_trace,
        "operator_ablation_candidate": op_ablated_candidate,
        "wrong_sign_candidate": wrong_candidate,
        "recursive_residual_after_second_action": recursive_residual,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V31_RUNTIME_PROBE_OPERATOR_RECURSION_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
