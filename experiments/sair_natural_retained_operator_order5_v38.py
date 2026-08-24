#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sair_probe_program_synthesis_v28 as v28
import sair_residual_constrained_transformer_v32 as v32
from developmental_runtime import DevelopmentalRuntime, DevelopmentalState, Route, SynthesisRegistry, route
from developmental_runtime.intervention import lawful
from domains.sair.probe_operator import induce_numeric_literal_shift, expand_numeric_literal_shift
from domains.sair.runtime_adapter import SAIRRuntimeAdapter

ORDER3 = "MODEL_EXISTS(SUCC(ORDER2),FORWARD)"
ORDER4 = "MODEL_EXISTS(4,FORWARD)"
ORDER5 = "MODEL_EXISTS(5,FORWARD)"
CERT_PATH = ROOT / "experiments" / "fixtures" / "v37_natural_continuation_certificate.json"


def ev(e):
    return None if e is None else {"route": e.route, "intervention_id": e.intervention_id, "detail": e.detail}


def load_rows_fast(root: Path):
    """Load native syntax + exact Fin-2 ports only; do not replay V25/V37 order-3 work."""
    rows = []
    raw_map = {}
    for src in ("normal", "hard1", "hard2"):
        for raw in v32.v24.load_jsonl(root / "examples" / "problems" / f"{src}.jsonl"):
            x, _, _ = v32.v24.observations(raw)
            rows.append({
                "id": raw["id"],
                "source": src,
                "base": tuple(x[n] for n in v28.BASE),
                "atom_values": {
                    "MODEL_EXISTS(ORDER2,FORWARD)": int(x["v3"] > 0),
                    "MODEL_EXISTS(ORDER2,REVERSE)": int(x["v4"] > 0),
                },
            })
            raw_map[str(raw["id"])] = raw
    return rows, raw_map


def eval_order5_task(task):
    idx, raw = task
    _, _, eqs = v32.v24.observations(raw)
    e1, e2 = eqs
    ok, table, status = v32.v25.sat_counterexample(e1, e2, N=5)
    bad = int(bool(ok) and not v32.v25.recheck(e1, e2, table))
    return idx, int(ok), status, bad


def ensure_order5_parallel(rows, raw_map, indices):
    tasks = [(i, raw_map[str(rows[i]["id"])]) for i in sorted(indices)]
    workers = max(1, min(4, os.cpu_count() or 1))
    witnesses = bad = unknown = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for idx, value, status, bad_one in ex.map(eval_order5_task, tasks, chunksize=1):
            rows[idx]["atom_values"][ORDER5] = value
            witnesses += int(value == 1)
            bad += int(bad_one)
            unknown += int(status == "unknown")
    return {"witnesses": witnesses, "bad": bad, "unknown": unknown, "workers": workers, "queries": len(tasks)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sair-root", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    root = Path(a.sair_root)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cert = json.loads(CERT_PATH.read_text())
    v37 = bool(cert.get("v37_gate"))
    rows, raw_map = load_rows_fast(root)
    survivors = frozenset(int(i) for i in cert["survivor_indices"])
    actual = min(survivors)

    certificate_valid = (
        cert.get("schema") == "v37_natural_continuation_certificate_v1"
        and cert.get("source_run_id") == 32676591950
        and cert.get("source_head_sha") == "5981253e2531b3d5049a09226f793812b15de79e"
        and cert.get("source_artifact_sha256") == "570c4b8264a8112efb740f8d5de09daaff1043060c23c1ef51d96b1604a88a9d"
        and v37
        and cert.get("probe4") == ORDER4
        and cert.get("probe4_outcome") == 0
        and cert.get("successor_route") == "DEVELOP_PROBES"
        and cert.get("verifier_audit", {}).get("bad") == 0
        and cert.get("verifier_audit", {}).get("unknown") == 0
        and len(rows) == 1269
        and len(survivors) == 153
        and rows[actual]["id"] == cert.get("actual_world") == "normal_0001"
    )
    if not certificate_valid:
        raise SystemExit("Frozen V37 certificate does not match the natural corpus/runtime boundary")

    # Restore only verifier-certified historical observations on the certified live cell.
    for i in survivors:
        rows[i]["atom_values"][ORDER3] = int(cert["probe3_outcome_on_live_cell"])
        rows[i]["atom_values"][ORDER4] = int(cert["probe4_outcome"])

    old = v28.synth_program_carrier(False)
    old_ids = tuple(p["ast"] for p in old)
    expanded = v28.synth_program_carrier(True)
    pmap = {p["ast"]: dict(p) for p in expanded}
    v32.add_raw_programs(pmap)
    # Executable verifier target only: deliberately absent from starting language/static generator.
    pmap[ORDER5] = {"ast": ORDER5, "order": 5, "direction": "FORWARD", "cost": 4, "kind": "atom"}
    adapter = SAIRRuntimeAdapter(rows, pmap)
    actions = ("ACCEPT_COUNTERMODEL_WITNESS", "ADVANCE_PROOF_SEARCH_FRONTIER")

    before4 = DevelopmentalState(
        problem_state={"source": cert["actual_world"], "countermodel_exhausted_through_order": 3},
        hypotheses=survivors,
        quotient={"probe": ORDER3, "outcome": 0, "cell": tuple(sorted(survivors))},
        probe_language=frozenset(set(old_ids) | {ORDER3}),
        capability_language=frozenset(actions),
        certificates=({"source_run_id": cert["source_run_id"], "stage": "pre-order4"},),
        metadata={"decision_probe_id": ORDER3, "last_probe": ORDER3, "last_probe_outcome": 0},
    )
    after_probe4 = before4.evolve(
        probe_language=frozenset(set(before4.probe_language) | {ORDER4}),
        quotient={"probe": ORDER4, "outcome": 0, "cell": tuple(sorted(survivors))},
        certificates=before4.certificates + ({"source_run_id": cert["source_run_id"], "probe": ORDER4, "outcome": 0},),
        metadata={**before4.metadata, "candidate_probe_id": ORDER4, "decision_probe_id": ORDER4, "last_probe": ORDER4, "last_probe_outcome": 0},
    )

    registry = SynthesisRegistry()
    registry.register_probe_operator_inducer(induce_numeric_literal_shift)
    registry.register_probe_operator_expander(expand_numeric_literal_shift)
    after_probe4 = registry.observe_verified_probe_transition(
        adapter,
        before4,
        after_probe4,
        ORDER4,
        {"source_run_id": cert["source_run_id"], "verified": True},
    )
    learned = tuple(after_probe4.metadata.get("learned_probe_operators", ()))

    # Restore the certified nonterminal V37 successor after the order-4 action.
    after_action4 = after_probe4.evolve(
        problem_state=dict(cert["successor_problem_state"]),
        certificates=after_probe4.certificates + ({"source_run_id": cert["source_run_id"], "continuation": cert["continuation"]},),
        metadata={**after_probe4.metadata, "proof_frontier_advanced_to": 4},
    )
    succ4 = route(adapter, after_action4)

    static_carrier = {p["ast"] for p in expanded}
    absent_initial = ORDER5 not in after_action4.probe_language and ORDER5 not in static_carrier

    # This is the only new expensive verifier work in V38: exact order-5 on the 153-world live cell.
    a5 = ensure_order5_parallel(rows, raw_map, after_action4.hypotheses)

    candidate5 = registry.synthesize_probe_extension(adapter, after_action4)
    meta = dict(after_action4.metadata)
    meta.pop("learned_probe_operators", None)
    ablated = after_action4.evolve(metadata=meta, lawbook=())
    ablated_candidate = registry.synthesize_probe_extension(adapter, ablated)

    runtime = DevelopmentalRuntime(adapter, registry)
    developed5, events5 = runtime.develop_until_intervention(after_action4) if succ4.route is Route.DEVELOP_PROBES else (after_action4, [])
    probe5 = next((e.intervention_id for e in events5 if e.route == "SYNTHESIZE_PROBE"), None)

    eprobe5 = None
    post5 = None
    eact5 = None
    final = None
    lawful5 = True
    if probe5 == ORDER5 and events5 and events5[-1].route == "PROBE":
        after_probe5, eprobe5 = runtime.execute_probe(developed5, actual)
        post5 = route(adapter, after_probe5)
        state5 = after_probe5
        if post5.route is Route.ACT:
            state5, eact5 = runtime.execute_common_continuation(after_probe5, actual)
            rec = adapter.execute(after_probe5, actual, adapter.intervention(eact5.intervention_id))
            lawful5 = lawful(rec)
        final = route(adapter, state5)

    plus1 = any(op.get("kind") == "NUMERIC_LITERAL_SHIFT" and int(op.get("delta", 0)) == 1 for op in learned)
    gates = {
        "official_natural_sair_corpus_answer_blind": len(rows) == 1269 and all("y" not in r for r in rows),
        "verified_v37_successor_certificate_restored": certificate_valid,
        "v37_successor_routes_develop_probes": succ4.route is Route.DEVELOP_PROBES,
        "plus_one_operator_induced_and_retained": plus1 and any("NUMERIC_LITERAL_SHIFT" in x for x in after_probe4.lawbook),
        "order5_absent_from_starting_carrier": absent_initial,
        "retained_operator_selects_order5_forward": candidate5 == ORDER5 and probe5 == ORDER5,
        "operator_ablation_blocks_order5_extension": ablated_candidate is None,
        "order5_exact_verifier_zero_bad_zero_unknown": int(a5["bad"]) == 0 and int(a5["unknown"]) == 0 and int(a5["queries"]) == 153,
        "order5_executes_and_recomputes_route": eprobe5 is not None and post5 is not None,
        "licensed_order5_continuation_is_lawful": lawful5,
        "successor_routed_again": final is not None,
        "no_protected_answer_used": all("y" not in r for r in rows),
    }
    gates["V38_NATURAL_RETAINED_OPERATOR_ORDER5_GATE"] = all(gates.values())
    result = {
        "status": "V38_NATURAL_RETAINED_OPERATOR_ORDER5",
        "v37_certificate": {
            "source_run_id": cert["source_run_id"],
            "source_head_sha": cert["source_head_sha"],
            "source_artifact_id": cert["source_artifact_id"],
            "source_artifact_sha256": cert["source_artifact_sha256"],
        },
        "actual_world": rows[actual]["id"],
        "live_world_count": len(survivors),
        "learned_operators": list(learned),
        "successor4_route": succ4.route.name,
        "candidate5": candidate5,
        "ablated_candidate": ablated_candidate,
        "order5_verifier_audit": a5,
        "events5": [ev(e) for e in events5],
        "probe5_event": ev(eprobe5),
        "post5_route": post5.route.name if post5 else None,
        "action5_event": ev(eact5),
        "final_route": final.route.name if final else None,
        "final_reason": final.reason if final else None,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V38_NATURAL_RETAINED_OPERATOR_ORDER5_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
