#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

V16 = ROOT / "prior_v16" / "final_evidence.json"
V17 = ROOT / "v17_frozen.json"
V18 = ROOT / "v18_frozen.json"

EXPECTED_V17_SHA = "4bd358531d126a753f5a88c794ceb61d9ae882ddc5514e63a7c5e63e81fb5606"
EXPECTED_V18_SHA = "dc5054e53f2cec05cec1696f113d448c89cbfe5fee2f158e44a29d658e11151c"

LAWS = ("OBSERVED_ONLY", "OBSERVED_PLUS_BOUNDARY", "ALL_ACTIVE")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def subset_for(law, arity):
    observed = set(range(min(3, arity)))
    if law == "OBSERVED_ONLY":
        return tuple(sorted(observed))
    if law == "OBSERVED_PLUS_BOUNDARY":
        return tuple(sorted(observed | {0, arity - 1}))
    if law == "ALL_ACTIVE":
        return tuple(range(arity))
    raise ValueError(law)

def mismatch(evidence, subset):
    key = str(tuple(subset))
    return evidence["cold_search"]["mismatch_counts"][key]

def main():
    if sha(V17) != EXPECTED_V17_SHA:
        raise RuntimeError("V17 frozen evidence hash mismatch")
    if sha(V18) != EXPECTED_V18_SHA:
        raise RuntimeError("V18 frozen evidence hash mismatch")

    v16 = json.loads(V16.read_text())
    v17 = json.loads(V17.read_text())
    v18 = json.loads(V18.read_text())

    if v16.get("final_verdict") != "VERIFIED_TERNARY_COHERENCE_EXPANSION_AND_HELDOUT_TRANSFER":
        raise RuntimeError("V16 external authority missing")
    if v16.get("lean_kernel_check") != "PASS":
        raise RuntimeError("V16 kernel authority missing")
    if v16["growth_substrate"]["selected_subset"] != [0, 1, 2]:
        raise RuntimeError("unexpected V16 selected subset")

    prior = {law: list(subset_for(law, 3)) for law in LAWS}
    prior_identical = len({tuple(x) for x in prior.values()}) == 1

    stage4 = {}
    for law in LAWS:
        subset = subset_for(law, 4)
        mm = mismatch(v17, subset)
        stage4[law] = {
            "subset": list(subset),
            "mismatch_count": mm,
            "qualified": mm == 0,
        }
    survivors4 = [law for law in LAWS if stage4[law]["qualified"]]

    stage5 = {}
    for law in survivors4:
        subset = subset_for(law, 5)
        mm = mismatch(v18, subset)
        stage5[law] = {
            "subset": list(subset),
            "mismatch_count": mm,
            "qualified": mm == 0,
        }
    survivors5 = [law for law in survivors4 if stage5[law]["qualified"]]
    selected = survivors5[0] if len(survivors5) == 1 else None

    v17_pairs = v17["qualification"]["ordered_pair_count"]
    v18_pairs = v18["qualification"]["ordered_pair_count"]
    cold_candidate_evals = v17["cold_search"]["candidate_connection_subsets"] + v18["cold_search"]["candidate_subsets"]
    staged_candidate_evals = len(LAWS) + len(survivors4)
    cold_pair_comparisons = (
        v17["cold_search"]["candidate_level_pair_comparisons"]
        + v18["cold_search"]["conceptual_pair_comparison_budget"]
    )
    staged_pair_comparisons = len(LAWS) * v17_pairs + len(survivors4) * v18_pairs

    gates = {
        "G1_v16_external_authority": v16["lean_kernel_check"] == "PASS",
        "G2_frozen_v17_v18_hashes": sha(V17) == EXPECTED_V17_SHA and sha(V18) == EXPECTED_V18_SHA,
        "G3_all_laws_identical_at_arity3": prior_identical and next(iter(prior.values())) == [0,1,2],
        "G4_v17_eliminates_observed_only": (
            stage4["OBSERVED_ONLY"]["mismatch_count"] > 0
            and set(survivors4) == {"OBSERVED_PLUS_BOUNDARY", "ALL_ACTIVE"}
        ),
        "G5_v18_eliminates_boundary_generalization": (
            stage5["OBSERVED_PLUS_BOUNDARY"]["mismatch_count"] > 0
        ),
        "G6_all_active_unique_survivor": survivors5 == ["ALL_ACTIVE"],
        "G7_selected_matches_v17_full_star": (
            selected == "ALL_ACTIVE"
            and stage4["ALL_ACTIVE"]["subset"] == v17["cold_search"]["qualified_subsets"][0]
        ),
        "G8_selected_matches_v18_full_star": (
            selected == "ALL_ACTIVE"
            and stage5["ALL_ACTIVE"]["subset"] == v18["cold_search"]["qualified_subsets"][0]
        ),
        "G9_staged_candidate_search_cheaper": staged_candidate_evals < cold_candidate_evals,
        "G10_staged_pair_comparisons_cheaper": staged_pair_comparisons < cold_pair_comparisons,
    }

    verdict = (
        "QUALIFIED_ALL_ACTIVE_ARITY_LAW_FOR_HEX_HELDOUT"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )

    evidence = {
        "verdict": verdict,
        "classification": "FINITE_FUTURE_CONSEQUENCE_SELECTION_OF_CROSS_ARITY_REPRESENTATION_LAW",
        "prior_arity3_instantiations": prior,
        "stage4": stage4,
        "stage4_survivors": survivors4,
        "stage5": stage5,
        "stage5_survivors": survivors5,
        "selected_law": selected,
        "cold_vs_staged": {
            "cold_candidate_evaluations": cold_candidate_evals,
            "staged_candidate_evaluations": staged_candidate_evals,
            "candidate_evaluation_reduction": cold_candidate_evals / staged_candidate_evals,
            "cold_pair_comparisons": cold_pair_comparisons,
            "staged_pair_comparisons": staged_pair_comparisons,
            "pair_comparison_reduction": cold_pair_comparisons / staged_pair_comparisons,
        },
        "frozen_sources": {
            "v16_artifact_id": 10311390727,
            "v17_sha256": EXPECTED_V17_SHA,
            "v18_sha256": EXPECTED_V18_SHA,
        },
        "gates": gates,
        "claim_boundary": [
            "three-member cross-arity generalization family supplied",
            "finite frozen arity4 and arity5 consequences",
            "held-out Hex checks performed separately after selection"
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (OUT / "selected_law.json").write_text(
        json.dumps({"selected_law": selected}, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
