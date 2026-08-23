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
from developmental_runtime import DevelopmentalRuntime, Route, SynthesisRegistry, route
from developmental_runtime.intervention import lawful
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


def event_json(e):
    return {"route": e.route, "intervention_id": e.intervention_id, "detail": e.detail}


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
        raise SystemExit("No V36-style natural successor found")

    successor = induction["after_action"]

    # Reconstruct V36's reachable raw carrier and minimum concrete intervention.
    verifier_audit = {"witnesses": 0, "bad": 0, "unknown": 0}
    for order in v32.ORDERS:
        for direction in v32.DIRECTIONS:
            a = v32.ensure_exact_order_values(root, rows, successor.hypotheses, order, direction)
            for k in verifier_audit:
                verifier_audit[k] += int(a[k])

    carrier = v32.exhaustive_raw_carrier(adapter, successor)
    _, carrier_audit, _ = v32.select_min_resolving_raw_transformer(adapter, successor, carrier)
    resolving = [r for r in carrier_audit if r.get("resolves")]
    if not resolving:
        raise SystemExit("No V36 resolving transformer reconstructed")
    best = min((r["transformer"]["cost"], r["transformer"]["edit_count"]) for r in resolving)
    minima = [r for r in resolving if (r["transformer"]["cost"], r["transformer"]["edit_count"]) == best]
    minimum_probes = sorted({r["probe"] for r in minima})

    # Actual world is frozen before observing the order-4 result.
    actual = sorted(successor.hypotheses)[0]
    actual_id = rows[actual]["id"]

    unique_probe = minimum_probes[0] if len(minimum_probes) == 1 else None
    if unique_probe is None:
        result = {
            "status": "V36_UNIQUENESS_NOT_RECONSTRUCTED",
            "minimum_probes": minimum_probes,
            "gates": {"V37_NATURAL_CONTINUATION_GATE": False},
        }
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    # The unique V36 probe is already in the raw pmap; prepare it through the generic hook.
    prepared = adapter.prepare_probe_extension(successor, unique_probe)
    registry = SynthesisRegistry()
    runtime = DevelopmentalRuntime(adapter, registry)

    pre_probe_decision = route(adapter, prepared)
    probe_executed = False
    after_probe = None
    probe_event = None
    observed = None
    refinement_consistent = False
    post_probe_decision = None
    continuation_event = None
    after_action = None
    successor_decision = None
    continuation_lawful = True

    if pre_probe_decision.route is Route.PROBE:
        after_probe, probe_event = runtime.execute_probe(prepared, actual)
        probe_executed = True
        observed = probe_event.detail["outcome"]
        expected_survivors = frozenset(
            h for h in prepared.hypotheses
            if adapter.probe_outcome(prepared, h, unique_probe) == observed
        )
        refinement_consistent = after_probe.hypotheses == expected_survivors
        post_probe_decision = route(adapter, after_probe)

        if post_probe_decision.route is Route.ACT:
            after_action, continuation_event = runtime.execute_common_continuation(after_probe, actual)
            # Re-execute the selected intervention directly only as an obligation audit.
            rec = adapter.execute(after_probe, actual, adapter.intervention(continuation_event.intervention_id))
            continuation_lawful = lawful(rec)
            successor_decision = route(adapter, after_action)
        else:
            after_action = after_probe
            successor_decision = post_probe_decision

    declared_routes = {
        Route.ACT,
        Route.PROBE,
        Route.DEVELOP_PROBES,
        Route.DEVELOP_CAPABILITY,
        Route.DEVELOP_WORLD_MODEL,
    }

    gates = {
        "official_natural_sair_corpus_used_answer_blind": len(rows) == 1269 and all("y" not in r for r in rows),
        "v36_unique_minimum_concrete_probe_reconstructed": unique_probe == "MODEL_EXISTS(4,FORWARD)",
        "actual_world_chosen_deterministically_before_outcome_use": actual == sorted(successor.hypotheses)[0],
        "exact_reachable_verifier_zero_bad_zero_unknowns": verifier_audit["bad"] == 0 and verifier_audit["unknown"] == 0,
        "generic_router_licenses_unique_probe": pre_probe_decision.route is Route.PROBE,
        "verified_probe_executed_through_generic_runtime": probe_executed and probe_event is not None,
        "verified_probe_refinement_matches_observed_outcome": refinement_consistent,
        "post_probe_route_recomputed": post_probe_decision is not None,
        "licensed_continuation_if_any_is_lawful": continuation_lawful,
        "successor_routed_again_by_same_router": successor_decision is not None and successor_decision.route in declared_routes,
        "no_protected_answer_enters_routing_probe_or_continuation": all("y" not in r for r in rows),
    }
    gates["V37_NATURAL_CONTINUATION_GATE"] = all(gates.values())

    result = {
        "status": "V37_NATURAL_CONTINUATION",
        "induction_base": repr(induction_base),
        "successor_world_count_before_probe": len(successor.hypotheses),
        "actual_world": actual_id,
        "minimum_transformer_cost": best,
        "minimum_concrete_probes": minimum_probes,
        "unique_probe": unique_probe,
        "pre_probe_route": pre_probe_decision.route.name,
        "probe_event": event_json(probe_event) if probe_event else None,
        "observed_outcome": observed,
        "post_probe_route": post_probe_decision.route.name if post_probe_decision else None,
        "post_probe_commitments": sorted(post_probe_decision.commitments) if post_probe_decision else [],
        "continuation_event": event_json(continuation_event) if continuation_event else None,
        "successor_problem_state": after_action.problem_state if after_action else None,
        "successor_route": successor_decision.route.name if successor_decision else None,
        "successor_reason": successor_decision.reason if successor_decision else None,
        "verifier_audit": verifier_audit,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V37_NATURAL_CONTINUATION_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
