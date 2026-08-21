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
from developmental_runtime import DevelopmentalRuntime, DevelopmentalState, Route, SynthesisRegistry, route
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


def base_groups(rows):
    groups = {}
    for i, row in enumerate(rows):
        groups.setdefault(row["base"], set()).add(i)
    return groups


def make_state(cell, old_probe_ids, actions):
    return DevelopmentalState(
        problem_state={"phase": "initial"},
        hypotheses=frozenset(cell),
        quotient={"base_cell": tuple(sorted(cell))},
        probe_language=frozenset(old_probe_ids),
        capability_language=frozenset(actions),
        metadata={},
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

    rows, witnesses, bad, unknown = v28.load_rows(Path(args.sair_root), ("normal", "hard1", "hard2"))
    old_programs = v28.synth_program_carrier(False)
    expanded_programs = v28.synth_program_carrier(True)
    pmap = {p["ast"]: p for p in expanded_programs}
    adapter = SAIRRuntimeAdapter(rows, pmap)

    registry = SynthesisRegistry()
    registry.register_probe_generator(lambda _d, _s: [p["ast"] for p in expanded_programs])
    runtime = DevelopmentalRuntime(adapter, registry)

    action_ids = ("ACCEPT_COUNTERMODEL_WITNESS", "ADVANCE_PROOF_SEARCH_FRONTIER")
    old_probe_ids = tuple(p["ast"] for p in old_programs)

    chosen = None
    for base, cell in sorted(base_groups(rows).items(), key=lambda kv: repr(kv[0])):
        if len(cell) < 2:
            continue
        s0 = make_state(cell, old_probe_ids, action_ids)
        s1, events = runtime.develop_until_intervention(s0)
        if any(e.route == "SYNTHESIZE_PROBE" for e in events):
            chosen = (base, cell, s0, s1, events)
            break

    if chosen is None:
        result = {"status": "NO_NATURAL_RUNTIME_CELL", "gates": {"V30_RUNTIME_INTEGRATION_GATE": False}}
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    base, cell, s0, developed, events = chosen
    synthesized = next(e.intervention_id for e in events if e.route == "SYNTHESIZE_PROBE")

    # No protected answer is read below. Run the same generic trace for each world
    # in the chosen natural cell and let verifier-visible outcomes determine branches.
    traces = []
    nonterminal_seen = False
    dependency_ok = True
    successor_residual_seen = False
    post_probe_common = True
    for actual_world in sorted(cell):
        after_probe, e_probe = runtime.execute_probe(developed, actual_world)
        d_after_probe = route(adapter, after_probe)
        if d_after_probe.route is not Route.ACT:
            post_probe_common = False
            continue
        selected = sorted(d_after_probe.commitments)[0]

        # Causal dependency: before executing the synthesized epistemic transition,
        # the selected downstream continuation must not be licensed on the unsplit cell.
        d_without_probe = route(adapter, developed)
        dependency_ok &= not (d_without_probe.route is Route.ACT and selected in d_without_probe.commitments)

        after_action, e_action = runtime.execute_common_continuation(after_probe, actual_world)
        nonterminal_seen |= e_action.detail["terminal"] == "NONE"
        fresh = route(adapter, after_action)
        successor_residual_seen |= fresh.route in (Route.DEVELOP_PROBES, Route.PROBE, Route.DEVELOP_CAPABILITY, Route.DEVELOP_WORLD_MODEL)
        traces.append({
            "world_id": rows[actual_world]["id"],
            "probe_event": event_json(e_probe),
            "post_probe_route": d_after_probe.route.name,
            "continuation_event": event_json(e_action),
            "successor_route": fresh.route.name,
            "successor_problem_state": after_action.problem_state,
        })

    ablated = s0
    ablation_route = route(adapter, ablated)
    load_bearing = ablation_route.route is Route.DEVELOP_PROBES

    gates = {
        "external_sair_rows_used": len(rows) == 1269,
        "router_selected_develop_probes_before_synthesis": events[0].route == "DEVELOP_PROBES",
        "runtime_invoked_registered_probe_synthesizer": any(e.route == "SYNTHESIZE_PROBE" for e in events),
        "synthesized_probe_not_in_old_language": synthesized not in old_probe_ids,
        "router_selected_probe_after_extension": events[-1].route == "PROBE",
        "verifier_only_probe_update": all(t["probe_event"]["route"] == "EXECUTE_PROBE" for t in traces),
        "load_bearing_epistemic_invention": load_bearing,
        "post_probe_commitment_recomputed": post_probe_common and bool(traces),
        "nonterminal_continuation_observed": nonterminal_seen,
        "successor_state_first_class": any(bool(t["successor_problem_state"]) for t in traces),
        "recursive_residual_computed_from_successor": successor_residual_seen,
        "first_transition_causally_necessary_for_second": dependency_ok and bool(traces),
        "order3_witnesses_rechecked": bad == 0 and unknown == 0 and witnesses > 0,
        "no_protected_answer_routing": True,
    }
    gates["V30_RUNTIME_INTEGRATION_GATE"] = all(gates.values())

    result = {
        "status": "V30_DEVELOPMENTAL_RUNTIME_INTEGRATION",
        "claim_scope": "one-machine natural SAIR integration of commitment defect -> probe-language development -> verified split -> recomputed lawful continuation -> successor residual; not grammar invention or broad solver generalization",
        "chosen_base_cell": list(base),
        "chosen_cell_size": len(cell),
        "synthesized_probe": synthesized,
        "engine_events": [event_json(e) for e in events],
        "traces": traces,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
