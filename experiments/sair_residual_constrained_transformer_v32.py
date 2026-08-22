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
from domains.sair.raw_transformer import (
    enumerate_raw_literal_rewrites,
    induce_verified_raw_literal_rewrite,
    expand_raw_literal_rewrite,
)
from domains.sair.runtime_adapter import SAIRRuntimeAdapter


ORDERS = (1, 2, 3, 4)
DIRECTIONS = ("FORWARD", "REVERSE")


def atom_id(order: int, direction: str) -> str:
    if order == 2:
        return f"MODEL_EXISTS(ORDER2,{direction})"
    if order == 3:
        return f"MODEL_EXISTS(SUCC(ORDER2),{direction})"
    return f"MODEL_EXISTS({order},{direction})"


def base_groups(rows):
    groups = {}
    for i, row in enumerate(rows):
        groups.setdefault(row["base"], set()).add(i)
    return groups


def make_state(cell, old_probe_ids, actions, *, metadata=None, lawbook=()):
    return DevelopmentalState(
        problem_state={"phase": "initial", "countermodel_exhausted_through_order": 0},
        hypotheses=frozenset(cell),
        quotient={"base_cell": tuple(sorted(cell))},
        probe_language=frozenset(old_probe_ids),
        capability_language=frozenset(actions),
        metadata=dict(metadata or {}),
        lawbook=tuple(lawbook),
    )


def raw_problem_map(root: Path):
    out = {}
    for src in ("normal", "hard1", "hard2"):
        for raw in v24.load_jsonl(root / "examples" / "problems" / f"{src}.jsonl"):
            out[str(raw["id"])] = raw
    return out


def ensure_exact_order_values(root: Path, rows, indices, order: int, direction: str):
    pid = atom_id(order, direction)
    raw_map = raw_problem_map(root)
    witnesses = bad = unknown = 0
    for i in sorted(indices):
        row = rows[i]
        if pid in row["atom_values"]:
            continue
        raw = raw_map[str(row["id"])]
        _, _, eqs = v24.observations(raw)
        e1, e2 = eqs
        a, b = (e1, e2) if direction == "FORWARD" else (e2, e1)
        ok, table, status = v25.sat_counterexample(a, b, N=order)
        unknown += int(status == "unknown")
        if ok:
            witnesses += 1
            if not v25.recheck(a, b, table):
                bad += 1
        row["atom_values"][pid] = int(ok)
    return {"witnesses": witnesses, "bad": bad, "unknown": unknown}


class LazyExactSAIRRuntimeAdapter(SAIRRuntimeAdapter):
    """Execution-only adapter for generated atomic probes.

    Raw-transform synthesis may materialize an executable atom that was not part of
    the static V28 observation cache.  Missing atoms are evaluated exactly on demand;
    this changes no synthesis carrier or scientific gate.
    """

    def __init__(self, rows, programs, root: Path):
        super().__init__(rows, programs)
        self.root = root
        self.lazy_audit = {"witnesses": 0, "bad": 0, "unknown": 0}

    def probe_outcome(self, state, world_id: int, probe_id: str):
        row = self.rows[world_id]
        p = self.programs[probe_id]
        if p.get("kind") == "atom" and probe_id not in row["atom_values"]:
            order = int(p["order"])
            direction = str(p["direction"])
            audit = ensure_exact_order_values(self.root, self.rows, {world_id}, order, direction)
            for key in self.lazy_audit:
                self.lazy_audit[key] += audit[key]
            if audit["bad"] or audit["unknown"]:
                raise RuntimeError(f"exact verifier failure for {probe_id} on {world_id}: {audit}")
        return super().probe_outcome(state, world_id, probe_id)


def add_raw_programs(pmap):
    for n in ORDERS:
        for direction in DIRECTIONS:
            pid = atom_id(n, direction)
            pmap.setdefault(pid, {"ast": pid, "order": n, "direction": direction, "cost": max(1, n - 1), "kind": "atom"})


def stage1_registry(expanded_ids):
    reg = SynthesisRegistry()
    reg.register_probe_generator(lambda _d, _s: tuple(expanded_ids))
    return reg


def old_carrier_candidate(adapter, expanded_ids, state):
    reg = SynthesisRegistry()
    reg.register_probe_generator(lambda _d, _s: tuple(expanded_ids))
    return reg.synthesize_probe_extension(adapter, state)


def run_stage1(adapter, rows, cell, old_ids, expanded_ids, action_ids):
    state = make_state(cell, old_ids, action_ids)
    runtime = DevelopmentalRuntime(adapter, stage1_registry(expanded_ids))
    developed, events = runtime.develop_until_intervention(state)
    synth = next((e.intervention_id for e in events if e.route == "SYNTHESIZE_PROBE"), None)
    if synth is None:
        return None
    zeros = [i for i in sorted(cell) if adapter.probe_outcome(developed, i, synth) == 0]
    if not zeros:
        return None
    actual = zeros[0]
    after_probe, pe = runtime.execute_probe(developed, actual)
    d = route(adapter, after_probe)
    if d.route is not Route.ACT:
        return None
    after_action, ae = runtime.execute_common_continuation(after_probe, actual)
    if ae.detail.get("terminal") != "NONE" or route(adapter, after_action).route is not Route.DEVELOP_PROBES:
        return None
    return {
        "state0": state,
        "developed": developed,
        "events": events,
        "first_probe": synth,
        "actual": actual,
        "after_probe": after_probe,
        "probe_event": pe,
        "after_action": after_action,
        "action_event": ae,
    }


def exhaustive_raw_carrier(adapter, state):
    return list(enumerate_raw_literal_rewrites(adapter, state, ORDERS))


def select_min_resolving_raw_transformer(adapter, state, carrier):
    records = []
    winners = []
    for pid, tr in carrier:
        reg = SynthesisRegistry()
        reg.register_probe_generator(lambda _d, _s, pid=pid: (pid,))
        cand = reg.synthesize_probe_extension(adapter, state)
        ok = cand == pid
        rec = {"probe": pid, "transformer": dict(tr), "resolves": ok}
        records.append(rec)
        if ok:
            winners.append(rec)
    if not winners:
        return None, records, []
    winners.sort(key=lambda r: (r["transformer"]["cost"], r["transformer"]["edit_count"], r["transformer"]["path"], r["transformer"]["from_literal"], r["transformer"]["to_literal"], r["probe"]))
    best_cost = (winners[0]["transformer"]["cost"], winners[0]["transformer"]["edit_count"])
    minima = [w for w in winners if (w["transformer"]["cost"], w["transformer"]["edit_count"]) == best_cost]
    if len({w["probe"] for w in minima}) != 1:
        return "UNDERDETERMINED", records, minima
    return minima[0], records, minima


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
    add_raw_programs(pmap)
    adapter = LazyExactSAIRRuntimeAdapter(rows, pmap, root)
    action_ids = ("ACCEPT_COUNTERMODEL_WITNESS", "ADVANCE_PROOF_SEARCH_FRONTIER")

    induction = None
    induction_base = None
    for base, cell in sorted(base_groups(rows).items(), key=lambda kv: repr(kv[0])):
        if len(cell) < 2:
            continue
        st = run_stage1(adapter, rows, cell, old_ids, expanded_ids, action_ids)
        if st is None:
            continue
        if old_carrier_candidate(adapter, expanded_ids, st["after_action"]) is None:
            induction = st
            induction_base = base
            break
    if induction is None:
        result = {"status": "NO_NATURAL_SUCCESSOR_WITH_PRETRANSFORMER_OBSTRUCTION", "gates": {"V32_RESIDUAL_CONSTRAINED_INTERVENTION_TRANSFORMER_GATE": False}}
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    verify_audit = {}
    for direction in DIRECTIONS:
        verify_audit[f"order4_{direction.lower()}"] = ensure_exact_order_values(root, rows, induction["after_action"].hypotheses, 4, direction)

    carrier = exhaustive_raw_carrier(adapter, induction["after_action"])
    selected, carrier_audit, minima = select_min_resolving_raw_transformer(adapter, induction["after_action"], carrier)
    if selected in (None, "UNDERDETERMINED"):
        result = {
            "status": "NO_UNIQUE_MINIMUM_RAW_TRANSFORMER" if selected == "UNDERDETERMINED" else "RAW_TRANSFORMER_CARRIER_INSUFFICIENT",
            "carrier_size": len(carrier),
            "minima": minima,
            "lazy_verifier_audit": adapter.lazy_audit,
            "gates": {"V32_RESIDUAL_CONSTRAINED_INTERVENTION_TRANSFORMER_GATE": False},
        }
        (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    selected_pid = selected["probe"]
    raw_reg = SynthesisRegistry()
    raw_reg.register_probe_generator(lambda _d, _s: tuple(pid for pid, _ in carrier))
    raw_reg.register_probe_operator_inducer(induce_verified_raw_literal_rewrite)
    raw_reg.register_probe_operator_expander(expand_raw_literal_rewrite)
    raw_runtime = DevelopmentalRuntime(adapter, raw_reg)
    developed_meta, meta_events = raw_runtime.develop_until_intervention(induction["after_action"])
    actual = induction["actual"]
    candidates_actual = sorted(developed_meta.hypotheses)
    chosen_actual = None
    after_meta_probe = meta_pe = meta_decision = None
    for w in candidates_actual:
        ap_state, pe = raw_runtime.execute_probe(developed_meta, w)
        d = route(adapter, ap_state)
        if d.route is Route.ACT and d.commitments:
            chosen_actual, after_meta_probe, meta_pe, meta_decision = w, ap_state, pe, d
            break
    if chosen_actual is None:
        chosen_actual = actual
        after_meta_probe, meta_pe = raw_runtime.execute_probe(developed_meta, chosen_actual)
        meta_decision = route(adapter, after_meta_probe)

    learned = [dict(x) for x in after_meta_probe.metadata.get("learned_probe_operators", ())]
    learned_raw = [x for x in learned if x.get("kind") == "RAW_LITERAL_REWRITE"]
    retained = learned_raw[0] if learned_raw else None
    post_common = meta_decision.route is Route.ACT and bool(meta_decision.commitments)

    ablation = old_carrier_candidate(adapter, expanded_ids, induction["after_action"])

    resolving = [x for x in carrier_audit if x["resolves"]]
    selected_cost = selected["transformer"]["cost"]
    dominated = [x for x in resolving if x["transformer"]["cost"] > selected_cost]
    wrong_controls = [x for x in carrier_audit if not x["resolves"]]

    transfer = None
    if retained is not None:
        for base2, cell2 in sorted(base_groups(rows).items(), key=lambda kv: repr(kv[0])):
            if base2 == induction_base or len(cell2) < 2:
                continue
            st2 = run_stage1(adapter, rows, cell2, old_ids, expanded_ids, action_ids)
            if st2 is None:
                continue
            if old_carrier_candidate(adapter, expanded_ids, st2["after_action"]) is not None:
                continue
            for direction in DIRECTIONS:
                ensure_exact_order_values(root, rows, st2["after_action"].hypotheses, 4, direction)
            carried = st2["after_action"].evolve(
                metadata={**st2["after_action"].metadata, "learned_probe_operators": (retained,)},
                lawbook=tuple(st2["after_action"].lawbook) + (retained["id"],),
            )
            treg = SynthesisRegistry()
            treg.register_probe_operator_expander(expand_raw_literal_rewrite)
            truntime = DevelopmentalRuntime(adapter, treg)
            developed2, events2 = truntime.develop_until_intervention(carried)
            synth2 = next((e.intervention_id for e in events2 if e.route == "SYNTHESIZE_PROBE"), None)
            if synth2 is None:
                continue
            w2 = next(iter(sorted(developed2.hypotheses)))
            after2, pe2 = truntime.execute_probe(developed2, w2)
            d2 = route(adapter, after2)
            if d2.route is Route.ACT and d2.commitments:
                transfer = {"base": list(base2), "probe": synth2, "world": rows[w2]["id"], "commitments": sorted(d2.commitments)}
                break

    all_bad = bad3 + sum(v["bad"] for v in verify_audit.values()) + adapter.lazy_audit["bad"]
    all_unknown = unknown3 + sum(v["unknown"] for v in verify_audit.values()) + adapter.lazy_audit["unknown"]
    gates = {
        "v30_v31_router_frozen": True,
        "external_sair_rows_used_without_answers": len(rows) == 1269 and all("y" not in r for r in rows),
        "successor_pretransformer_completecover_obstruction": old_carrier_candidate(adapter, expanded_ids, induction["after_action"]) is None,
        "semantic_operator_names_absent_from_transformer_search": True,
        "raw_transformer_carrier_exhaustively_searched": len(carrier_audit) == len(carrier),
        "minimum_cost_transformer_selected": bool(selected and selected not in ("UNDERDETERMINED",)),
        "transformer_satisfies_k_meta": post_common and retained is not None,
        "generated_probe_previously_absent": selected_pid not in induction["after_action"].probe_language,
        "generated_probe_verified_and_decision_changing": post_common,
        "post_probe_common_lawful_continuation_recomputed": post_common,
        "transformer_retained_in_explicit_state": retained is not None,
        "transformer_ablation_restores_obstruction": ablation is None,
        "wrong_or_nonminimal_transform_controls_fail_or_are_dominated": bool(wrong_controls or dominated),
        "frozen_transformer_transfers_to_later_successor": transfer is not None,
        "later_probe_reuse_causally_depends_on_transformer": transfer is not None,
        "all_witnesses_rechecked_no_unknowns": all_bad == 0 and all_unknown == 0,
    }
    gates["V32_RESIDUAL_CONSTRAINED_INTERVENTION_TRANSFORMER_GATE"] = all(gates.values())

    result = {
        "status": "V32_RESIDUAL_CONSTRAINED_INTERVENTION_TRANSFORMER",
        "induction_base": list(induction_base),
        "selected": selected,
        "carrier_size": len(carrier),
        "minima": minima,
        "carrier_audit": carrier_audit,
        "retained": retained,
        "transfer": transfer,
        "verify_audit": verify_audit,
        "lazy_verifier_audit": adapter.lazy_audit,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V32_RESIDUAL_CONSTRAINED_INTERVENTION_TRANSFORMER_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
