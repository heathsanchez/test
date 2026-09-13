#!/usr/bin/env python3
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
PRIOR = ROOT / "prior_v10" / "final_evidence.json"
V8_RUN = ROOT.parent / "hex_truth_table_meta_language_growth_v8" / "run.py"

spec = importlib.util.spec_from_file_location("v8run", V8_RUN)
v8run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v8run)

def induce_schema(prior):
    if prior.get("final_verdict") != "VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER":
        raise RuntimeError("V10 final authority missing")
    stages = prior["stages"]
    prev = {}
    observations = []
    for stage in stages:
        after = {str(k): v for k, v in stage["table_after"].items()}
        residual = {str(k) for k in stage["undefined_residual_patterns"]}
        winner = stage["winner"]
        if winner is None or not winner["qualified"] or winner["mismatch_count"] != 0:
            raise RuntimeError("V10 stage lacks unique verifier-clean winner")
        winner_added = {str(k): v for k, v in winner["assignments"].items()}

        preserved = {k: v for k, v in prev.items() if after.get(k) == v}
        deleted = sorted(k for k in prev if k not in after)
        changed = sorted(k for k in prev if k in after and after[k] != prev[k])
        added = {k: v for k, v in after.items() if k not in prev}

        observations.append({
            "stage": stage["stage"],
            "residual_keys": sorted(residual),
            "preserved_count": len(preserved),
            "deleted_keys": deleted,
            "changed_keys": changed,
            "added_bindings": added,
            "winner_assignments": winner_added,
            "added_exactly_residual": set(added) == residual,
            "added_exactly_winner": added == winner_added,
        })
        prev = after

    lawful = all(
        not x["deleted_keys"]
        and not x["changed_keys"]
        and x["added_exactly_residual"]
        and x["added_exactly_winner"]
        and len(x["added_bindings"]) > 0
        for x in observations
    )
    if not lawful:
        return None, observations

    schema = {
        "kind": "MONOTONE_FRESH_BINDING_EXTENSION",
        "state_shape": "finite_partial_map",
        "precondition": {
            "keys_must_be_absent": True,
            "keys_must_equal_typed_residual": True,
        },
        "effect": {
            "preserve_all_existing_bindings": True,
            "add_only_residual_named_bindings": True,
            "allow_nonempty_finite_batch": True,
        },
        "authority": {
            "candidate_values_require_verifier_clean_semantics": True,
            "prior_bindings_immutable": True,
        },
        "induced_from_stage_count": len(observations),
        "observed_batch_sizes": [len(x["added_bindings"]) for x in observations],
    }
    return schema, observations

def position_key(i, m):
    if m == 1:
        return "SINGLE"
    if i == 0:
        return "LEFT"
    if i == m - 1:
        return "RIGHT"
    return "INTERIOR"

def required_keys(m):
    return sorted({position_key(i, m) for i in range(m)})

def selected_relations(table, m):
    out = []
    for i in range(m):
        key = position_key(i, m)
        if key not in table:
            raise KeyError(key)
        if table[key]:
            out.append(i)
    return out

def apply_schema_candidate(schema, state, residual_keys, assignment):
    if schema is None or schema.get("kind") != "MONOTONE_FRESH_BINDING_EXTENSION":
        return None, "UNKNOWN_SCHEMA"
    residual_keys = list(residual_keys)
    if not residual_keys:
        return None, "NO_RESIDUAL"
    if any(k in state for k in residual_keys):
        return None, "REJECT_OVERWRITE"
    if set(assignment) != set(residual_keys):
        return None, "REJECT_NONRESIDUAL_BINDING"
    new_state = dict(state)
    new_state.update(assignment)
    return new_state, "CANDIDATE"

def search_stage(schema, state, residual_keys, evaluate, m):
    records = []
    for bits in itertools.product((0, 1), repeat=len(residual_keys)):
        assignment = dict(zip(residual_keys, bits))
        candidate, status = apply_schema_candidate(schema, state, residual_keys, assignment)
        if candidate is None:
            records.append({"assignment": assignment, "status": status})
            continue
        selected = selected_relations(candidate, m)
        mm, first = evaluate(selected)
        records.append({
            "assignment": assignment,
            "status": status,
            "selected_relations": selected,
            "mismatch_count": mm,
            "qualified": mm == 0,
            "first_mismatch": first,
        })
    winners = [r for r in records if r.get("qualified")]
    return records, winners

def main():
    prior = json.loads(PRIOR.read_text())
    schema, induction_trace = induce_schema(prior)

    prior_objs, prior_eval = v8run.world(3, 1, "all_single_relation_graphs")
    two_objs, two_eval = v8run.world(3, 2, "one_arc_each")
    three_objs, three_eval = v8run.world(2, 3, "one_arc_each")

    worlds = [
        ("one_relation", 1, prior_objs, prior_eval),
        ("two_relations", 2, two_objs, two_eval),
        ("three_relations", 3, three_objs, three_eval),
    ]

    state = {}
    transfer_stages = []
    for stage_index, (name, m, objs, evaluate) in enumerate(worlds):
        req = required_keys(m)
        residual = [k for k in req if k not in state]
        records, winners = search_stage(schema, state, residual, evaluate, m)
        winner = winners[0] if len(winners) == 1 else None
        if winner is not None:
            candidate, status = apply_schema_candidate(
                schema, state, residual, winner["assignment"]
            )
            if status != "CANDIDATE":
                raise RuntimeError(status)
            state = candidate
        transfer_stages.append({
            "stage": stage_index,
            "world": name,
            "relation_count": m,
            "object_count": len(objs),
            "ordered_pairs": len(objs) ** 2,
            "required_keys": req,
            "typed_residual_keys": residual,
            "candidate_count": len(records),
            "candidates": records,
            "winner": winner,
            "state_after": state,
        })

    # Causal controls.
    disabled_candidate, disabled_status = apply_schema_candidate(
        None, {}, ["SINGLE"], {"SINGLE": 1}
    )

    overwrite_candidate, overwrite_status = apply_schema_candidate(
        schema, {"SINGLE": 1}, ["SINGLE"], {"SINGLE": 0}
    )

    stage_for_key = {
        "SINGLE": (1, prior_eval),
        "LEFT": (2, two_eval),
        "RIGHT": (2, two_eval),
        "INTERIOR": (3, three_eval),
    }
    flip_controls = []
    for key, (m, evaluate) in stage_for_key.items():
        mutated = dict(state)
        mutated[key] = 0
        selected = selected_relations(mutated, m)
        mm, first = evaluate(selected)
        flip_controls.append({
            "key": key,
            "witness_relation_count": m,
            "selected_relations": selected,
            "mismatch_count": mm,
            "fails": mm > 0,
            "first_mismatch": first,
        })

    replay = {
        "one_relation": prior_eval(selected_relations(state, 1))[0],
        "two_relations": two_eval(selected_relations(state, 2))[0],
        "three_relations": three_eval(selected_relations(state, 3))[0],
    }

    extensional_all = all(
        selected_relations(state, m) == list(range(m))
        for m in range(1, 8)
    )

    candidate_comparisons = sum(
        s["candidate_count"] * s["ordered_pairs"]
        for s in transfer_stages
    )
    full_policy_baseline = 16 * ((len(prior_objs) ** 2) + (len(two_objs) ** 2)) + 2 * (len(three_objs) ** 2)

    gates = {
        "G1_schema_induced_from_v10": schema is not None,
        "G2_all_v10_transitions_fit_schema": all(
            not x["deleted_keys"] and not x["changed_keys"]
            and x["added_exactly_residual"] and x["added_exactly_winner"]
            for x in induction_trace
        ),
        "G3_cross_representation_keys": set(state) == {"SINGLE", "LEFT", "RIGHT", "INTERIOR"},
        "G4_unique_winner_each_transfer_stage": all(s["winner"] is not None for s in transfer_stages),
        "G5_final_policy_all_one": all(v == 1 for v in state.values()),
        "G6_semantic_replay_exact": all(v == 0 for v in replay.values()),
        "G7_schema_disabled_stalls": disabled_candidate is None and disabled_status == "UNKNOWN_SCHEMA",
        "G8_overwrite_rejected": overwrite_candidate is None and overwrite_status == "REJECT_OVERWRITE",
        "G9_value_flip_controls_fail": all(x["fails"] for x in flip_controls),
        "G10_extensional_match_through_7_relations": extensional_all,
        "G11_sparse_budget_13504": candidate_comparisons == 13504,
        "G12_full_policy_baseline_86400": full_policy_baseline == 86400,
    }

    verdict = (
        "QUALIFIED_REPAIR_SCHEMA_TRANSFER_FOR_HEX_HELDOUT"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )
    evidence = {
        "verdict": verdict,
        "classification": "FINITE_REPAIR_SCHEMA_ANTI_UNIFICATION_AND_CROSS_REPRESENTATION_TRANSFER",
        "v10_source": {
            "final_verdict": prior.get("final_verdict"),
            "lean_kernel_check": prior.get("lean_kernel_check"),
        },
        "induced_schema": schema,
        "induction_trace": induction_trace,
        "transfer_key_representation": ["SINGLE", "LEFT", "RIGHT", "INTERIOR"],
        "transfer_stages": transfer_stages,
        "final_policy": state,
        "semantic_replay_mismatches": replay,
        "schema_disabled_control": {"status": disabled_status},
        "overwrite_control": {"status": overwrite_status},
        "value_flip_controls": flip_controls,
        "candidate_level_semantic_pair_comparisons": {
            "inferred_schema_transfer": candidate_comparisons,
            "complete_4_key_policy_baseline": full_policy_baseline,
            "reduction_factor": full_policy_baseline / candidate_comparisons,
        },
        "gates": gates,
        "claim_boundary": [
            "anti-unification procedure supplied",
            "finite prior trajectory",
            "finite transfer worlds",
            "subject and verifier supplied",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if schema:
        (OUT / "induced_schema.json").write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    (OUT / "final_policy.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
