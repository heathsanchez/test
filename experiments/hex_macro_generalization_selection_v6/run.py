#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
V5_RUN = ROOT.parent / "hex_relational_primitive_promotion_v5" / "run.py"
V4_AUTH = ROOT.parent / "hex_digraph_compositional_repair_genesis_v4" / "AUTHORITY.json"
V5_AUTH = ROOT.parent / "hex_relational_primitive_promotion_v5" / "AUTHORITY.json"

spec = importlib.util.spec_from_file_location("v5run", V5_RUN)
v5run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v5run)

def main():
    v4 = json.loads(V4_AUTH.read_text())
    v5 = json.loads(V5_AUTH.read_text())
    assert v4["verdict"] == "VERIFIED_COMPOSITIONAL_REPAIR_GENESIS"
    assert v5["verdict"] == "VERIFIED_PRIMITIVE_PROMOTION_AND_TRANSFER"

    prior = {
        "A_ALL": [0, 1],
        "B_FIRST": [0, 1],
        "C_LAST": [0, 1],
    }
    prior_identical = len({tuple(x) for x in prior.values()}) == 1

    objects = v5run.qualification_objects()
    source_sigs = [v5run.source_canon(x, 3) for x in objects]
    maps = v5run.role_maps(3, 5)

    subsets = {
        "A_ALL": (0, 1, 2, 3),
        "B_FIRST": (0, 1),
        "C_LAST": (2, 3),
    }
    future = {}
    for name, subset in subsets.items():
        mm, first = v5run.mismatch_count(objects, source_sigs, maps, subset)
        future[name] = {
            "anchor_subset": list(subset),
            "mismatch_count": mm,
            "qualified": mm == 0,
            "first_mismatch": first,
        }

    retained = [k for k, v in future.items() if v["qualified"]]
    selected = retained[0] if len(retained) == 1 else None
    matches_v5 = (
        selected == "A_ALL"
        and v5["promoted_pattern"]["couple_to"] == "all_active_relation_roles"
    )

    gates = {
        "G1_prior_candidates_identical": prior_identical,
        "G2_prior_behavior_matches_v4": prior["A_ALL"] == [0, 1],
        "G3_complete_future_world": len(objects) == 36 and len(objects) ** 2 == 1296,
        "G4_first_only_fails": future["B_FIRST"]["mismatch_count"] > 0,
        "G5_last_only_fails": future["C_LAST"]["mismatch_count"] > 0,
        "G6_all_zero_disagreement": future["A_ALL"]["mismatch_count"] == 0,
        "G7_unique_retained_candidate": retained == ["A_ALL"],
        "G8_matches_v5_hex_checked_pattern": matches_v5,
    }
    verdict = (
        "VERIFIED_FUTURE_CONSEQUENCE_GENERALIZATION_SELECTION"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )
    evidence = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_NONCANONICAL_MACRO_GENERALIZATION",
        "prior_instantiations": prior,
        "prior_extensionally_identical": prior_identical,
        "future": future,
        "retained_candidates": retained,
        "selected_candidate": selected,
        "selected_matches_v5_hex_checked_pattern": matches_v5,
        "prior_authority": {
            "v4_run": v4["workflow_run_id"],
            "v5_run": v5["workflow_run_id"],
            "v5_artifact": v5["artifact_id"],
        },
        "gates": gates,
        "claim_boundary": [
            "candidate extrapolation family supplied",
            "finite future consequence",
            "no autonomous candidate-family generation",
        ],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("VERIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
