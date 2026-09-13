#!/usr/bin/env python3
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
V10 = ROOT / "prior_v10" / "final_evidence.json"
V11 = ROOT / "prior_v11" / "final_evidence.json"
V12 = ROOT / "prior_v12" / "final_evidence.json"
V8_RUN = ROOT.parent / "hex_truth_table_meta_language_growth_v8" / "run.py"

spec = importlib.util.spec_from_file_location("v8run", V8_RUN)
v8run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v8run)

P_KEY = "KEY_TYPE_IS_INT"
P_BATCH = "BATCH_SIZE_IN_OBSERVED_SET"

def applicability(active_predicates, residual_keys, observed_batch_sizes):
    residual_keys = list(residual_keys)
    if not residual_keys:
        return False, ["EMPTY_RESIDUAL"]
    failures = []
    if P_KEY in active_predicates:
        if not all(isinstance(k, int) and not isinstance(k, bool) for k in residual_keys):
            failures.append(P_KEY)
    if P_BATCH in active_predicates:
        if len(residual_keys) not in observed_batch_sizes:
            failures.append(P_BATCH)
    return len(failures) == 0, failures

def all_admissible(active_predicates, residual_sets, observed_batch_sizes):
    checks = [applicability(active_predicates, r, observed_batch_sizes) for r in residual_sets]
    return all(ok for ok, _ in checks), checks

def one_predicate_repairs(active, blocked_residual, prior_residuals, observed_batch_sizes):
    blocked_ok, blocked_failures = applicability(active, blocked_residual, observed_batch_sizes)
    if blocked_ok:
        return blocked_failures, []
    candidates = []
    for dropped in sorted(active):
        new_active = set(active)
        new_active.remove(dropped)
        now_ok, now_failures = applicability(new_active, blocked_residual, observed_batch_sizes)
        prior_ok, prior_checks = all_admissible(new_active, prior_residuals, observed_batch_sizes)
        candidates.append({
            "dropped_predicate": dropped,
            "was_falsified_by_residual": dropped in blocked_failures,
            "blocked_residual_admitted_after_drop": now_ok,
            "remaining_blockers": now_failures,
            "prior_consequences_preserved": prior_ok,
            "lawful": (
                dropped in blocked_failures
                and now_ok
                and prior_ok
            ),
            "active_after": sorted(new_active),
        })
    return blocked_failures, candidates

def position_tag(i, m):
    if i == 0:
        pos = "LEFT"
    elif i == m - 1:
        pos = "RIGHT"
    else:
        pos = "INTERIOR"
    return (pos, i % 5)

def key_text(k):
    if isinstance(k, tuple):
        return f"{k[0]}|{k[1]}"
    return str(k)

def required_keys(m):
    return sorted({position_tag(i, m) for i in range(m)}, key=key_text)

def selected_relations(state, m):
    out = []
    for i in range(m):
        k = position_tag(i, m)
        if k not in state:
            raise KeyError(k)
        if state[k]:
            out.append(i)
    return out

def state_json(state):
    return {key_text(k): v for k, v in sorted(state.items(), key=lambda kv: key_text(kv[0]))}

def apply_constitutional_extension(active_predicates, observed_batch_sizes, state, residual_keys, assignment):
    ok, failures = applicability(active_predicates, residual_keys, observed_batch_sizes)
    if not ok:
        return None, {"status": "SCOPE_BLOCKED", "failures": failures}
    if any(k in state for k in residual_keys):
        return None, {"status": "REJECT_OVERWRITE"}
    if set(assignment) != set(residual_keys):
        return None, {"status": "REJECT_NONRESIDUAL_BINDING"}
    new_state = dict(state)
    new_state.update(assignment)
    return new_state, {"status": "CANDIDATE"}

def search_stage(active_predicates, observed_batch_sizes, state, residual, evaluate, m):
    records = []
    for bits in itertools.product((0, 1), repeat=len(residual)):
        assignment = dict(zip(residual, bits))
        candidate, meta = apply_constitutional_extension(
            active_predicates, observed_batch_sizes, state, residual, assignment
        )
        rec = {
            "assignment": {key_text(k): v for k, v in assignment.items()},
            **meta,
        }
        if candidate is not None:
            selected = selected_relations(candidate, m)
            mm, first = evaluate(selected)
            rec.update({
                "selected_relations": selected,
                "mismatch_count": mm,
                "qualified": mm == 0,
                "first_mismatch": first,
            })
        records.append(rec)
    winners = [r for r in records if r.get("qualified")]
    return records, winners

def main():
    v10 = json.loads(V10.read_text())
    v11 = json.loads(V11.read_text())
    v12 = json.loads(V12.read_text())

    if v10.get("final_verdict") != "VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER":
        raise RuntimeError("V10 authority missing")
    if v11.get("final_verdict") != "VERIFIED_REPAIR_SCHEMA_ANTI_UNIFICATION_AND_TRANSFER":
        raise RuntimeError("V11 authority missing")
    if v12.get("final_verdict") != "VERIFIED_REPAIR_SCHEMA_GENERALITY_SELECTION_AND_TRANSFER":
        raise RuntimeError("V12 authority missing")

    v10_residuals = [list(s["undefined_residual_patterns"]) for s in v10["stages"]]
    observed_batch_sizes = {len(r) for r in v10_residuals}
    observed_key_types = sorted({type(k).__name__ for r in v10_residuals for k in r})

    active = {P_KEY, P_BATCH}
    initial_scope = {
        "active_predicates": sorted(active),
        "observed_key_types": observed_key_types,
        "observed_batch_sizes": sorted(observed_batch_sizes),
    }

    # Consequence 1: exact V11 categorical residuals.
    v11_residuals = [list(s["typed_residual_keys"]) for s in v11["transfer_stages"]]
    v11_blocked = v11_residuals[0]
    failures1, repairs1 = one_predicate_repairs(
        active, v11_blocked, v10_residuals, observed_batch_sizes
    )
    lawful1 = [r for r in repairs1 if r["lawful"]]
    if len(lawful1) == 1:
        active.remove(lawful1[0]["dropped_predicate"])

    # Preserve all exact V11 residuals after the first repair.
    v11_all_ok, v11_checks_after = all_admissible(active, v11_residuals, observed_batch_sizes)

    # Consequence 2: exact first V12 residual, batch size 3.
    v12_first_residual = list(v12["transfer_stages"][0]["typed_residual_keys"])
    prior_after1 = v10_residuals + v11_residuals
    failures2, repairs2 = one_predicate_repairs(
        active, v12_first_residual, prior_after1, observed_batch_sizes
    )
    lawful2 = [r for r in repairs2 if r["lawful"]]
    if len(lawful2) == 1:
        active.remove(lawful2[0]["dropped_predicate"])

    all_prior_residuals = v10_residuals + v11_residuals + [v12_first_residual]
    all_prior_ok, all_prior_checks = all_admissible(active, all_prior_residuals, observed_batch_sizes)

    # New structured-key transfer begins with a batch of four.
    four_objs, four_eval = v8run.world(2, 4, "one_arc_each")
    five_objs, five_eval = v8run.world(2, 5, "one_arc_each")
    six_objs, six_eval = v8run.world(2, 6, "one_arc_each")
    worlds = [
        ("four_relations", 4, four_objs, four_eval),
        ("five_relations", 5, five_objs, five_eval),
        ("six_relations", 6, six_objs, six_eval),
    ]

    state = {}
    transfer = []
    earning_stage = {}
    for stage_index, (name, m, objs, evaluate) in enumerate(worlds):
        req = required_keys(m)
        residual = [k for k in req if k not in state]
        for k in residual:
            earning_stage[k] = (m, evaluate)
        records, winners = search_stage(
            active, observed_batch_sizes, state, residual, evaluate, m
        )
        winner = winners[0] if len(winners) == 1 else None
        if winner is not None:
            assignment = {k: winner["assignment"][key_text(k)] for k in residual}
            candidate, meta = apply_constitutional_extension(
                active, observed_batch_sizes, state, residual, assignment
            )
            if candidate is None or meta["status"] != "CANDIDATE":
                raise RuntimeError(meta)
            state = candidate
        transfer.append({
            "stage": stage_index,
            "world": name,
            "relation_count": m,
            "object_count": len(objs),
            "ordered_pairs": len(objs) ** 2,
            "required_keys": [key_text(k) for k in req],
            "typed_residual_keys": [key_text(k) for k in residual],
            "candidate_count": len(records),
            "candidates": records,
            "winner": winner,
            "state_after": state_json(state),
        })

    replay = {
        "four_relations": four_eval(selected_relations(state, 4))[0],
        "five_relations": five_eval(selected_relations(state, 5))[0],
        "six_relations": six_eval(selected_relations(state, 6))[0],
    }

    flip_controls = []
    for key, (m, evaluate) in sorted(earning_stage.items(), key=lambda kv: key_text(kv[0])):
        mutated = dict(state)
        mutated[key] = 0
        selected = selected_relations(mutated, m)
        mm, first = evaluate(selected)
        flip_controls.append({
            "key": key_text(key),
            "witness_relation_count": m,
            "selected_relations": selected,
            "mismatch_count": mm,
            "fails": mm > 0,
            "first_mismatch": first,
        })

    # Restore-scope controls on the new first residual.
    first_target_residual = required_keys(4)
    restored_key_ok, restored_key_failures = applicability(
        {P_KEY}, first_target_residual, observed_batch_sizes
    )
    restored_batch_ok, restored_batch_failures = applicability(
        {P_BATCH}, first_target_residual, observed_batch_sizes
    )

    overwrite_status = None
    if state:
        k = next(iter(state))
        _, overwrite_meta = apply_constitutional_extension(
            active, observed_batch_sizes, state, [k], {k: 1 - state[k]}
        )
        overwrite_status = overwrite_meta["status"]

    matches_v12 = (
        not active
        and v12["selected_schema"]["key_scope"] == "ANY_KEY"
        and v12["selected_schema"]["batch_scope"] == "ANY_NONEMPTY_BATCH"
    )

    candidate_comparisons = sum(
        s["candidate_count"] * s["ordered_pairs"] for s in transfer
    )

    gates = {
        "G1_initial_scope_induced_from_v10": (
            observed_key_types == ["int"] and observed_batch_sizes == {1, 2}
        ),
        "G2_v11_falsifies_only_key_scope": failures1 == [P_KEY],
        "G3_v11_unique_minimal_drop": (
            len(lawful1) == 1 and lawful1[0]["dropped_predicate"] == P_KEY
        ),
        "G4_v11_all_residuals_preserved_after_drop": v11_all_ok,
        "G5_v12_falsifies_only_batch_scope": failures2 == [P_BATCH],
        "G6_v12_unique_minimal_drop": (
            len(lawful2) == 1 and lawful2[0]["dropped_predicate"] == P_BATCH
        ),
        "G7_all_prior_consequences_preserved": all_prior_ok,
        "G8_final_scope_unrestricted": len(active) == 0,
        "G9_matches_v12_selected_generality": matches_v12,
        "G10_new_first_residual_batch4": bool(transfer) and len(transfer[0]["typed_residual_keys"]) == 4,
        "G11_unique_winner_each_transfer_stage": all(s["winner"] is not None for s in transfer),
        "G12_final_policy_all_one": bool(state) and all(v == 1 for v in state.values()),
        "G13_replay_exact": all(v == 0 for v in replay.values()),
        "G14_flip_controls_fail": bool(flip_controls) and all(x["fails"] for x in flip_controls),
        "G15_restore_key_scope_reblocks": not restored_key_ok and P_KEY in restored_key_failures,
        "G16_restore_batch_scope_reblocks": not restored_batch_ok and P_BATCH in restored_batch_failures,
        "G17_overwrite_rejected": overwrite_status == "REJECT_OVERWRITE",
        "G18_candidate_comparisons_24576": candidate_comparisons == 24576,
    }

    verdict = (
        "QUALIFIED_SCOPE_PREDICATE_GROWTH_FOR_HEX_HELDOUT"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )
    evidence = {
        "verdict": verdict,
        "classification": "FINITE_TYPED_RESIDUAL_GUIDED_SCHEMA_SCOPE_RELAXATION",
        "initial_scope": initial_scope,
        "consequence_1_v11": {
            "blocked_residual": v11_blocked,
            "falsified_predicates": failures1,
            "one_predicate_repairs": repairs1,
            "selected_repair": lawful1[0] if len(lawful1) == 1 else None,
            "all_v11_residuals_preserved_after": v11_all_ok,
        },
        "consequence_2_v12": {
            "blocked_residual": v12_first_residual,
            "falsified_predicates": failures2,
            "one_predicate_repairs": repairs2,
            "selected_repair": lawful2[0] if len(lawful2) == 1 else None,
        },
        "active_scope_predicates_after_growth": sorted(active),
        "matches_v12_generality": matches_v12,
        "transfer_key_representation": "(POSITION, i mod 5)",
        "transfer_stages": transfer,
        "final_policy": state_json(state),
        "semantic_replay_mismatches": replay,
        "value_flip_controls": flip_controls,
        "restore_scope_controls": {
            "KEY_TYPE_IS_INT": {
                "admitted": restored_key_ok,
                "failures": restored_key_failures,
            },
            "BATCH_SIZE_IN_OBSERVED_SET": {
                "admitted": restored_batch_ok,
                "failures": restored_batch_failures,
            },
        },
        "overwrite_control_status": overwrite_status,
        "candidate_level_semantic_pair_comparisons": candidate_comparisons,
        "gates": gates,
        "claim_boundary": [
            "schema represented as conjunction of scope predicates",
            "generic DROP_ONE_FAILED_SCOPE_PREDICATE operation supplied",
            "finite prior and transfer consequences",
            "subject and verifier supplied",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (OUT / "final_scope.json").write_text(json.dumps({
        "active_scope_predicates": sorted(active),
        "constitutional_invariants": [
            "preserve_existing",
            "forbid_overwrite",
            "keys_equal_typed_residual",
            "values_require_verifier",
        ],
    }, indent=2, sort_keys=True) + "\n")
    (OUT / "final_policy.json").write_text(json.dumps(state_json(state), indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
