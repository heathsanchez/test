#!/usr/bin/env python3
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
V10 = ROOT / "prior_v10" / "final_evidence.json"
V11 = ROOT / "prior_v11" / "final_evidence.json"
V8_RUN = ROOT.parent / "hex_truth_table_meta_language_growth_v8" / "run.py"

spec = importlib.util.spec_from_file_location("v8run", V8_RUN)
v8run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v8run)

KEY_SCOPES = ("PRIOR_INTEGER_KEY", "ANY_KEY")
BATCH_SCOPES = ("OBSERVED_BATCH_SIZE", "ANY_NONEMPTY_BATCH")

def schema_candidates(observed_batch_sizes):
    out = []
    for key_scope in KEY_SCOPES:
        for batch_scope in BATCH_SCOPES:
            out.append({
                "key_scope": key_scope,
                "batch_scope": batch_scope,
                "observed_batch_sizes": sorted(observed_batch_sizes),
                "preserve_existing": True,
                "forbid_overwrite": True,
                "keys_equal_typed_residual": True,
                "values_require_verifier": True,
            })
    return out

def schema_applicable(schema, residual_keys):
    residual_keys = list(residual_keys)
    if not residual_keys:
        return False, "EMPTY_RESIDUAL"
    if schema["key_scope"] == "PRIOR_INTEGER_KEY":
        if not all(isinstance(k, int) and not isinstance(k, bool) for k in residual_keys):
            return False, "KEY_SCOPE_MISMATCH"
    elif schema["key_scope"] != "ANY_KEY":
        return False, "UNKNOWN_KEY_SCOPE"

    n = len(residual_keys)
    if schema["batch_scope"] == "OBSERVED_BATCH_SIZE":
        if n not in schema["observed_batch_sizes"]:
            return False, "BATCH_SCOPE_MISMATCH"
    elif schema["batch_scope"] == "ANY_NONEMPTY_BATCH":
        if n < 1:
            return False, "EMPTY_RESIDUAL"
    else:
        return False, "UNKNOWN_BATCH_SCOPE"
    return True, "APPLICABLE"

def apply_schema(schema, state, residual_keys, assignment):
    ok, status = schema_applicable(schema, residual_keys)
    if not ok:
        return None, status
    if any(k in state for k in residual_keys):
        return None, "REJECT_OVERWRITE"
    if set(assignment) != set(residual_keys):
        return None, "REJECT_NONRESIDUAL_BINDING"
    new_state = dict(state)
    new_state.update(assignment)
    return new_state, "CANDIDATE"

def position_tag(i, m):
    if i == 0:
        pos = "LEFT"
    elif i == m - 1:
        pos = "RIGHT"
    else:
        pos = "INTERIOR"
    return (pos, i % 3)

def key_text(k):
    return f"{k[0]}|{k[1]}" if isinstance(k, tuple) else str(k)

def state_json(state):
    return {key_text(k): v for k, v in sorted(state.items(), key=lambda kv: key_text(kv[0]))}

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

def search_stage(schema, state, residual, evaluate, m):
    records = []
    for bits in itertools.product((0, 1), repeat=len(residual)):
        assignment = dict(zip(residual, bits))
        candidate, status = apply_schema(schema, state, residual, assignment)
        rec = {
            "assignment": {key_text(k): v for k, v in assignment.items()},
            "status": status,
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
    if v10.get("final_verdict") != "VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER":
        raise RuntimeError("V10 authority missing")
    if v11.get("final_verdict") != "VERIFIED_REPAIR_SCHEMA_ANTI_UNIFICATION_AND_TRANSFER":
        raise RuntimeError("V11 authority missing")

    v10_residuals = [
        list(stage["undefined_residual_patterns"])
        for stage in v10["stages"]
    ]
    observed_batch_sizes = {len(x) for x in v10_residuals}

    v11_residuals = [
        list(stage["typed_residual_keys"])
        for stage in v11["transfer_stages"]
    ]

    candidates = schema_candidates(observed_batch_sizes)
    qualification = []
    for schema in candidates:
        v10_checks = [schema_applicable(schema, r) for r in v10_residuals]
        fits_v10 = all(ok for ok, _ in v10_checks)
        v11_checks = [schema_applicable(schema, r) for r in v11_residuals]
        fits_v11 = fits_v10 and all(ok for ok, _ in v11_checks)
        qualification.append({
            "schema": schema,
            "v10_checks": [{"ok": ok, "status": status} for ok, status in v10_checks],
            "fits_v10": fits_v10,
            "v11_checks": [{"ok": ok, "status": status} for ok, status in v11_checks],
            "fits_v11": fits_v11,
        })

    # New consequence exposes a residual batch of three tuple keys.
    first_required = required_keys(3)
    stage_c_checks = []
    for q in qualification:
        ok, status = schema_applicable(q["schema"], first_required)
        survives = q["fits_v11"] and ok
        q["new_batch3_check"] = {"ok": ok, "status": status}
        q["survives_all_generality_consequences"] = survives
        stage_c_checks.append(survives)

    survivors = [q for q in qualification if q["survives_all_generality_consequences"]]
    selected_schema = survivors[0]["schema"] if len(survivors) == 1 else None

    three_objs, three_eval = v8run.world(2, 3, "one_arc_each")
    four_objs, four_eval = v8run.world(2, 4, "one_arc_each")
    five_objs, five_eval = v8run.world(2, 5, "one_arc_each")
    worlds = [
        ("three_relations", 3, three_objs, three_eval),
        ("four_relations", 4, four_objs, four_eval),
        ("five_relations", 5, five_objs, five_eval),
    ]

    state = {}
    transfer = []
    first_stage = {}
    if selected_schema is not None:
        for stage_index, (name, m, objs, evaluate) in enumerate(worlds):
            req = required_keys(m)
            residual = [k for k in req if k not in state]
            for k in residual:
                first_stage[k] = (m, evaluate)
            records, winners = search_stage(selected_schema, state, residual, evaluate, m)
            winner = winners[0] if len(winners) == 1 else None
            if winner is not None:
                assignment = {
                    k: winner["assignment"][key_text(k)]
                    for k in residual
                }
                candidate, status = apply_schema(selected_schema, state, residual, assignment)
                if status != "CANDIDATE":
                    raise RuntimeError(status)
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

    replay = {}
    if selected_schema is not None:
        replay = {
            "three_relations": three_eval(selected_relations(state, 3))[0],
            "four_relations": four_eval(selected_relations(state, 4))[0],
            "five_relations": five_eval(selected_relations(state, 5))[0],
        }

    flip_controls = []
    if selected_schema is not None:
        for key, (m, evaluate) in sorted(first_stage.items(), key=lambda kv: key_text(kv[0])):
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

    overwrite_status = None
    if selected_schema is not None and state:
        k = next(iter(state))
        _, overwrite_status = apply_schema(
            selected_schema, state, [k], {k: 1 - state[k]}
        )

    extensional_all = False
    if selected_schema is not None:
        extensional_all = all(
            all(position_tag(i, m) in state and state[position_tag(i, m)] == 1 for i in range(m))
            for m in range(3, 9)
        )

    candidate_comparisons = sum(
        s["candidate_count"] * s["ordered_pairs"] for s in transfer
    )

    schema_match_v11 = bool(
        selected_schema
        and selected_schema["key_scope"] == "ANY_KEY"
        and selected_schema["batch_scope"] == "ANY_NONEMPTY_BATCH"
        and v11["induced_schema"]["effect"]["allow_nonempty_finite_batch"] is True
    )

    gates = {
        "G1_four_grammar_schemas": len(candidates) == 4,
        "G2_all_four_fit_v10": all(q["fits_v10"] for q in qualification),
        "G3_v11_removes_exactly_integer_key_schemas": (
            sum(q["fits_v11"] for q in qualification) == 2
            and all(
                q["fits_v11"] == (q["schema"]["key_scope"] == "ANY_KEY")
                for q in qualification
            )
        ),
        "G4_batch3_leaves_one_schema": len(survivors) == 1,
        "G5_selected_any_key_any_nonempty": bool(
            selected_schema
            and selected_schema["key_scope"] == "ANY_KEY"
            and selected_schema["batch_scope"] == "ANY_NONEMPTY_BATCH"
        ),
        "G6_matches_v11_independent_generality": schema_match_v11,
        "G7_unique_winner_each_target_stage": len(transfer) == 3 and all(s["winner"] is not None for s in transfer),
        "G8_final_policy_all_one": bool(state) and all(v == 1 for v in state.values()),
        "G9_replay_exact": bool(replay) and all(v == 0 for v in replay.values()),
        "G10_flip_controls_fail": bool(flip_controls) and all(x["fails"] for x in flip_controls),
        "G11_overwrite_rejected": overwrite_status == "REJECT_OVERWRITE",
        "G12_extensional_all_relations_3_to_8": extensional_all,
        "G13_first_residual_batch_is_3": bool(transfer) and len(transfer[0]["typed_residual_keys"]) == 3,
        "G14_candidate_comparisons_5632": candidate_comparisons == 5632,
    }

    verdict = (
        "QUALIFIED_SCHEMA_GENERALITY_SELECTION_FOR_HEX_HELDOUT"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )
    evidence = {
        "verdict": verdict,
        "classification": "FINITE_CONSEQUENCE_SELECTED_REPAIR_SCHEMA_GENERALITY",
        "observed_v10_batch_sizes": sorted(observed_batch_sizes),
        "v10_residuals": v10_residuals,
        "v11_residuals": v11_residuals,
        "schema_grammar": {
            "key_scopes": list(KEY_SCOPES),
            "batch_scopes": list(BATCH_SCOPES),
        },
        "schema_qualification": qualification,
        "selected_schema": selected_schema,
        "matches_v11_induced_generality": schema_match_v11,
        "transfer_key_representation": "POSITION|TAG with TAG=i mod 3",
        "transfer_stages": transfer,
        "final_policy": state_json(state),
        "semantic_replay_mismatches": replay,
        "value_flip_controls": flip_controls,
        "overwrite_control_status": overwrite_status,
        "candidate_level_semantic_pair_comparisons": candidate_comparisons,
        "gates": gates,
        "claim_boundary": [
            "schema-description grammar supplied",
            "finite prior and transfer consequences",
            "subject and verifier supplied",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if selected_schema:
        (OUT / "selected_schema.json").write_text(json.dumps(selected_schema, indent=2, sort_keys=True) + "\n")
    (OUT / "final_policy.json").write_text(json.dumps(state_json(state), indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
