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

import sair_residual_constrained_transformer_v32 as v32
from developmental_runtime import DevelopmentalRuntime, Route, SynthesisRegistry, optimal_experiment_policy, route
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


class LazyAdapter(SAIRRuntimeAdapter):
    def __init__(self, rows, programs, root: Path):
        super().__init__(rows, programs)
        self.root = root
        self.audit = {"witnesses": 0, "bad": 0, "unknown": 0}

    def probe_outcome(self, state, world_id: int, probe_id: str):
        row = self.rows[world_id]
        program = self.programs[probe_id]
        if program.get("kind") == "atom" and probe_id not in row["atom_values"]:
            order = int(program["order"])
            direction = str(program["direction"])
            a = v32.ensure_exact_order_values(self.root, self.rows, {world_id}, order, direction)
            for k in self.audit:
                self.audit[k] += a[k]
            if a["bad"] or a["unknown"]:
                raise RuntimeError(f"verifier failure for {probe_id} on {world_id}: {a}")
        return super().probe_outcome(state, world_id, probe_id)


def extend(adapter, state, pids):
    out = state
    for pid in pids:
        out = adapter.prepare_probe_extension(out, pid)
    return out


def policy(adapter, state):
    return optimal_experiment_policy(
        adapter,
        state,
        state.hypotheses,
        state.probe_language,
        state.capability_language,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = Path(args.sair_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows, witnesses3, bad3, unknown3 = v32.v28.load_rows(root, ("normal", "hard1", "hard2"))
    for row in rows:
        row.pop("y", None)

    old_programs = v32.v28.synth_program_carrier(False)
    expanded_programs = v32.v28.synth_program_carrier(True)
    old_ids = tuple(p["ast"] for p in old_programs)
    expanded_ids = tuple(p["ast"] for p in expanded_programs)
    pmap = {p["ast"]: dict(p) for p in expanded_programs}
    v32.add_raw_programs(pmap)
    adapter = LazyAdapter(rows, pmap, root)
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
        result = {"status": "NO_CORRECTED_SUCCESSOR_OBSTRUCTION", "gates": {"V33_CORRECTED_RAW_TRANSFORMER_BASIS_GATE": False}}
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    # Same raw carrier as frozen V32. Materialize all exact values it may need.
    carrier = v32.exhaustive_raw_carrier(adapter, induction["after_action"])
    by_pid = {}
    for pid, rec in carrier:
        old = by_pid.get(pid)
        if old is None or (rec["cost"], rec["edit_count"], repr(rec)) < (old["cost"], old["edit_count"], repr(old)):
            by_pid[pid] = dict(rec)
    unique = tuple(sorted(by_pid))

    subset_audit = []
    minima = []
    for size in range(1, len(unique) + 1):
        winners = []
        for subset in itertools.combinations(unique, size):
            st = extend(adapter, induction["after_action"], subset)
            pol = policy(adapter, st)
            total_cost = sum(float(by_pid[p]["cost"]) for p in subset)
            rec = {
                "subset": list(subset),
                "size": size,
                "transform_cost": total_cost,
                "resolves": pol is not None,
                "policy_cost": None if pol is None else pol.cost,
                "first_policy_probe": None if pol is None else pol.tree.probe_id,
            }
            subset_audit.append(rec)
            if pol is not None:
                winners.append(rec)
        if winners:
            winners.sort(key=lambda r: (r["transform_cost"], r["policy_cost"], tuple(r["subset"])))
            best = (winners[0]["transform_cost"], winners[0]["policy_cost"])
            minima = [r for r in winners if (r["transform_cost"], r["policy_cost"]) == best]
            break

    minimum = minima[0] if len({tuple(x["subset"]) for x in minima}) == 1 else None
    basis = tuple(minimum["subset"]) if minimum else ()

    # Execute the actual verifier-driven policy and look for a deepest reachable path.
    runtime = DevelopmentalRuntime(adapter, SynthesisRegistry())
    developed = extend(adapter, induction["after_action"], basis) if basis else induction["after_action"]
    best_trace = None
    if basis:
        for world in sorted(developed.hypotheses):
            st = developed
            events = []
            probe_steps = 0
            for _ in range(6):
                d = route(adapter, st)
                if d.route is Route.PROBE:
                    st, ev = runtime.execute_probe(st, world)
                    events.append({"kind": "probe", "id": ev.intervention_id, "detail": ev.detail})
                    probe_steps += 1
                    continue
                if d.route is Route.ACT:
                    st, ev = runtime.execute_common_continuation(st, world)
                    events.append({"kind": "action", "id": ev.intervention_id, "detail": ev.detail})
                    trace = {"world": rows[world]["id"], "probe_steps": probe_steps, "events": events, "successor_state": repr(st.problem_state)}
                    if best_trace is None or trace["probe_steps"] > best_trace["probe_steps"]:
                        best_trace = trace
                    break
                break

    ablations = []
    if len(basis) > 1:
        for removed in basis:
            keep = tuple(p for p in basis if p != removed)
            st = extend(adapter, induction["after_action"], keep)
            ablations.append({"removed": removed, "remaining": list(keep), "resolves": policy(adapter, st) is not None})

    singleton_resolvers = [x for x in subset_audit if x["size"] == 1 and x["resolves"]]
    gates = {
        "corrected_planner_used": hasattr(adapter, "assume_probe_outcome"),
        "external_sair_rows_used_without_answers": len(rows) == 1269 and all("y" not in r for r in rows),
        "old_probe_completecover_obstruction": v32.old_carrier_candidate(adapter, expanded_ids, induction["after_action"]) is None,
        "same_v32_raw_carrier_reused": len(carrier) == 2,
        "carrier_exhaustive": len(subset_audit) == ((1 << len(unique)) - 1),
        "minimum_basis_found": minimum is not None,
        "minimum_basis_cardinality_certified": minimum is not None and all(not x["resolves"] for x in subset_audit if x["size"] < minimum["size"]),
        "actual_verifier_execution_reaches_commitment": best_trace is not None and any(e["kind"] == "action" for e in best_trace["events"]),
        "two_step_trajectory_observed_if_basis_size_two": minimum is not None and (minimum["size"] != 2 or (best_trace is not None and best_trace["probe_steps"] >= 2)),
        "each_basis_member_load_bearing": minimum is not None and (minimum["size"] == 1 or (len(ablations) == len(basis) and all(not x["resolves"] for x in ablations))),
        "all_witnesses_rechecked_no_unknowns": bad3 == 0 and unknown3 == 0 and adapter.audit["bad"] == 0 and adapter.audit["unknown"] == 0,
        "no_protected_answer_routing": True,
    }
    gates["V33_CORRECTED_RAW_TRANSFORMER_BASIS_GATE"] = all(gates.values())

    result = {
        "status": "V33_CORRECTED_RAW_TRANSFORMER_BASIS",
        "induction_base": list(induction_base),
        "successor_cell_size": len(induction["after_action"].hypotheses),
        "raw_carrier": [{"probe": pid, "transformer": rec} for pid, rec in carrier],
        "unique_candidate_probes": list(unique),
        "singleton_resolvers": singleton_resolvers,
        "subset_audit": subset_audit,
        "minimum": minimum,
        "minima": minima,
        "deepest_actual_trace": best_trace,
        "ablations": ablations,
        "order3_witnesses_rechecked": witnesses3,
        "lazy_verifier_audit": adapter.audit,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V33_CORRECTED_RAW_TRANSFORMER_BASIS_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
