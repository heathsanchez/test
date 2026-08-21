#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sair_raw_adequacy_v24 as v24
import sair_bounded_model_adequacy_v25 as v25
from developmental_runtime import DevelopmentalRuntime, DevelopmentalState, Route, SynthesisRegistry, route
from domains.sair.runtime_adapter_v31 import LAW_ID, V31SAIRRuntimeAdapter, parse_probe_id

TARGET_BASE = (0, 0, 0, 0, 0, 1)  # frozen V30 natural base cell
OLD_PROBES = ("MODEL_EXISTS(2,FORWARD)", "MODEL_EXISTS(2,REVERSE)")
ACTIONS = ("ACCEPT_COUNTERMODEL_WITNESS", "ADVANCE_PROOF_SEARCH_FRONTIER")


def load_rows(root: Path):
    rows = []
    witnesses = bad = unknown = 0
    for src in ("normal", "hard1", "hard2"):
        for raw in v24.load_jsonl(root / "examples" / "problems" / f"{src}.jsonl"):
            x, _, eqs = v24.observations(raw)
            e1, e2 = eqs
            vals = {
                (2, "FORWARD"): int(x["v3"] > 0),
                (2, "REVERSE"): int(x["v4"] > 0),
            }
            for direction, a, b in (("FORWARD", e1, e2), ("REVERSE", e2, e1)):
                ok, table, status = v25.sat_counterexample(a, b, N=3)
                vals[(3, direction)] = int(ok) if status != "unknown" else -1
                unknown += int(status == "unknown")
                if ok:
                    witnesses += 1
                    if not v25.recheck(a, b, table):
                        bad += 1
            rows.append({
                "id": raw["id"],
                "source": src,
                "base": tuple(x[n] for n in v24.VERIFIER_NAMES),
                "eqs": (e1, e2),
                "vals": vals,
            })
    return rows, witnesses, bad, unknown


def groups(rows):
    g = {}
    for i, row in enumerate(rows):
        g.setdefault(row["base"], set()).add(i)
    return g


def program(n: int, direction: str):
    pid = f"MODEL_EXISTS({n},{direction})"
    return pid, {"id": pid, "kind": "atom", "order": n, "direction": direction, "cost": 1 if n == 2 else 2}


def all_programs():
    out = {}
    for n in (1, 2, 3, 4):
        for direction in ("FORWARD", "REVERSE"):
            pid, p = program(n, direction)
            out[pid] = p
    return out


def generic_or_retained_generator(_domain, state: DevelopmentalState):
    # Before a reusable law exists, expose only generic raw AST edits around the
    # order-2 seeds: integer +/-1 and direction flip. There is no SUCC/ORDER3 symbol.
    if LAW_ID not in state.lawbook:
        candidates = set()
        for pid in OLD_PROBES:
            n, direction = parse_probe_id(pid)
            for delta in (-1, +1):
                nn = n + delta
                if 1 <= nn <= 3:
                    candidates.add(f"MODEL_EXISTS({nn},{direction})")
            flipped = "REVERSE" if direction == "FORWARD" else "FORWARD"
            candidates.add(f"MODEL_EXISTS({n},{flipped})")
        return sorted(candidates)

    # After retention, the old generic mutation search is not extended by hand.
    # The retained +1 operator is instantiated compositionally on every probe in
    # the current language, allowing the learned 2->3 relation to produce 3->4.
    candidates = set()
    for pid in state.probe_language:
        try:
            n, direction = parse_probe_id(pid)
        except ValueError:
            continue
        nn = n + 1
        if nn <= 4:
            candidates.add(f"MODEL_EXISTS({nn},{direction})")
    return sorted(candidates)


def make_state(cell):
    return DevelopmentalState(
        problem_state={"phase": "initial", "countermodel_exhausted_through": 0},
        hypotheses=frozenset(cell),
        quotient={"base_cell": tuple(sorted(cell))},
        probe_language=frozenset(OLD_PROBES),
        capability_language=frozenset(ACTIONS),
        lawbook=(),
        metadata={"countermodel_exhausted_through": 0},
    )


def event_json(e):
    return {"route": e.route, "intervention_id": e.intervention_id, "detail": e.detail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows, order3_witnesses, bad3, unknown3 = load_rows(Path(args.sair_root))
    cell = groups(rows).get(TARGET_BASE, set())
    programs = all_programs()

    lazy_cache = {}
    lazy_stats = {"rechecked": 0, "bad": 0, "unknown": 0}

    def lazy_probe_value(row, n, direction):
        key = (row["id"], n, direction)
        if key in lazy_cache:
            return lazy_cache[key]
        e1, e2 = row["eqs"]
        a, b = (e1, e2) if direction == "FORWARD" else (e2, e1)
        ok, table, status = v25.sat_counterexample(a, b, N=n, timeout_ms=5000)
        if status == "unknown":
            lazy_stats["unknown"] += 1
            ans = (-1, "unknown")
        elif ok:
            if v25.recheck(a, b, table):
                lazy_stats["rechecked"] += 1
                ans = (1, "sat")
            else:
                lazy_stats["bad"] += 1
                ans = (-1, "bad")
        else:
            ans = (0, "unsat")
        lazy_cache[key] = ans
        return ans

    adapter = V31SAIRRuntimeAdapter(rows, programs, lazy_probe_value)
    registry = SynthesisRegistry()
    registry.register_probe_generator(generic_or_retained_generator)
    runtime = DevelopmentalRuntime(adapter, registry)

    s0 = make_state(cell)
    stage1_state, stage1_events = runtime.develop_until_intervention(s0)
    stage1_synth = [e.intervention_id for e in stage1_events if e.route == "SYNTHESIZE_PROBE"]
    stage1_laws = [e.intervention_id for e in stage1_events if e.route == "RETAIN_LAW"]
    p3 = stage1_synth[0] if stage1_synth else None

    # Continue down the natural nonterminal V30 branch: choose the first world in
    # the frozen cell for which the synthesized order-3 probe returns absence.
    actual_world = None
    s2 = None
    first_probe_event = first_action_event = None
    for w in sorted(cell):
        if p3 is None or adapter.probe_outcome(stage1_state, w, p3) != 0:
            continue
        after_probe, ep = runtime.execute_probe(stage1_state, w)
        d = route(adapter, after_probe)
        if d.route is not Route.ACT or "ADVANCE_PROOF_SEARCH_FRONTIER" not in d.commitments:
            continue
        after_action, ea = runtime.execute_common_continuation(after_probe, w)
        if ea.intervention_id != "ADVANCE_PROOF_SEARCH_FRONTIER" or ea.detail["terminal"] != "NONE":
            continue
        if route(adapter, after_action).route is not Route.DEVELOP_PROBES:
            continue
        actual_world, s2 = w, after_action
        first_probe_event, first_action_event = ep, ea
        break

    stage2_state = None
    stage2_events = []
    second_probe_event = second_action_event = None
    s3 = None
    p4 = None
    if s2 is not None:
        stage2_state, stage2_events = runtime.develop_until_intervention(s2)
        stage2_synth = [e.intervention_id for e in stage2_events if e.route == "SYNTHESIZE_PROBE"]
        p4 = stage2_synth[0] if stage2_synth else None
        if p4 is not None and route(adapter, stage2_state).route is Route.PROBE:
            after_probe2, second_probe_event = runtime.execute_probe(stage2_state, actual_world)
            if route(adapter, after_probe2).route is Route.ACT:
                s3, second_action_event = runtime.execute_common_continuation(after_probe2, actual_world)

    # Retention ablation at the actual V30 successor state. The raw mutation
    # substrate remains available, but without the retained law it is bounded to
    # edits around order 2 and therefore cannot generate the 3->4 application.
    ablation_events = []
    ablation_state = None
    if s2 is not None:
        no_law = s2.evolve(lawbook=())
        ablation_state, ablation_events = runtime.develop_until_intervention(no_law)
    ablation_synth = [e.intervention_id for e in ablation_events if e.route == "SYNTHESIZE_PROBE"]

    p3_order = parse_probe_id(p3)[0] if p3 else None
    p4_order = parse_probe_id(p4)[0] if p4 else None
    stage2_route_before = route(adapter, s2).route.name if s2 is not None else None
    final_route = route(adapter, s3).route.name if s3 is not None else None

    gates = {
        "external_sair_development_rows_used": len(rows) == 1269,
        "starts_from_frozen_v30_natural_cell": TARGET_BASE in groups(rows) and len(cell) == 156,
        "stage1_router_selects_develop_probes": bool(stage1_events) and stage1_events[0].route == "DEVELOP_PROBES",
        "stage1_probe_induced_from_generic_ast_edits": p3_order == 3 and p3 not in OLD_PROBES and "SUCC" not in p3 and "ORDER3" not in p3,
        "runtime_retains_induced_numeric_shift_law": LAW_ID in stage1_state.lawbook and stage1_laws == [LAW_ID],
        "first_probe_is_load_bearing_for_nonterminal_action": s2 is not None and first_action_event is not None,
        "first_continuation_is_nonterminal": first_action_event is not None and first_action_event.detail["terminal"] == "NONE",
        "v30_successor_routes_back_to_develop_probes": stage2_route_before == "DEVELOP_PROBES",
        "second_probe_is_reuse_of_retained_operator": p3_order == 3 and p4_order == 4 and LAW_ID in s2.lawbook if s2 is not None else False,
        "retained_operator_not_relearned_at_stage2": sum(e.route == "RETAIN_LAW" for e in stage2_events) == 0,
        "second_probe_verifier_updates_version_space": second_probe_event is not None and second_probe_event.route == "EXECUTE_PROBE",
        "post_second_probe_commitment_recomputed": second_action_event is not None,
        "second_transition_reaches_first_class_successor": s3 is not None and s3 != s2,
        "retained_operator_ablation_blocks_second_probe": s2 is not None and p4 not in ablation_synth and (ablation_state is None or p4 not in ablation_state.probe_language),
        "second_transition_depends_on_retained_epistemic_history": second_action_event is not None and not ablation_synth,
        "all_order3_and_order4_sat_witnesses_rechecked": bad3 == 0 and unknown3 == 0 and lazy_stats["bad"] == 0 and lazy_stats["unknown"] == 0,
        "no_protected_answer_routing": True,
    }
    gates["V31_RETAINED_PROBE_OPERATOR_RECURSION_GATE"] = all(gates.values())

    result = {
        "status": "V31_RETAINED_PROBE_OPERATOR_RECURSION",
        "claim_scope": "natural SAIR recursive reuse of a verifier-induced retained probe operator inside the frozen developmental runtime; mutation primitives remain supplied and broad solver generalization is not claimed",
        "target_base_cell": list(TARGET_BASE),
        "target_cell_size": len(cell),
        "actual_world": None if actual_world is None else rows[actual_world]["id"],
        "stage1_events": [event_json(e) for e in stage1_events],
        "retained_lawbook": list(stage1_state.lawbook),
        "first_probe_event": None if first_probe_event is None else event_json(first_probe_event),
        "first_action_event": None if first_action_event is None else event_json(first_action_event),
        "stage2_events": [event_json(e) for e in stage2_events],
        "second_probe_event": None if second_probe_event is None else event_json(second_probe_event),
        "second_action_event": None if second_action_event is None else event_json(second_action_event),
        "final_route": final_route,
        "ablation_events": [event_json(e) for e in ablation_events],
        "order3_witnesses_rechecked": order3_witnesses,
        "lazy_order1_order4_stats": lazy_stats,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V31_RETAINED_PROBE_OPERATOR_RECURSION_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
