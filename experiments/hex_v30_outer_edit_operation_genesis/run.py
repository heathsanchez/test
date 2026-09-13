#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT / "prior_v13"
OUT = ROOT / "results"

BIT_ORDER = [(0,0),(0,1),(1,0),(1,1)]

def load_v13():
    fs = list(PRIOR.rglob("final_evidence.json"))
    if not fs:
        raise RuntimeError("missing V13 final_evidence.json")
    e = json.loads(fs[0].read_text())
    verdict = e.get("final_verdict") or e.get("verdict")
    if verdict != "VERIFIED_RESIDUAL_GUIDED_SCHEMA_SCOPE_GROWTH_AND_TRANSFER":
        raise RuntimeError(f"unexpected V13 verdict: {verdict}")
    return e

def tt(mask):
    return tuple((mask >> i) & 1 for i in range(4))

def apply(table, universe, active, falsified):
    active = set(active)
    falsified = set(falsified)
    out = set()
    for p in universe:
        a = int(p in active)
        f = int(p in falsified)
        idx = BIT_ORDER.index((a,f))
        if table[idx]:
            out.add(p)
    return out

def exact_transition(table, universe, active, falsified, expected):
    got = apply(table, universe, active, falsified)
    return got == set(expected), sorted(got)

def main():
    OUT.mkdir(exist_ok=True)
    v13 = load_v13()

    # Recover the exact sealed V13 transition facts.
    c1 = v13["consequence_1_v11"]
    c2 = v13["consequence_2_v12"]

    U12 = {"KEY_TYPE_IS_INT", "BATCH_SIZE_IN_OBSERVED_SET"}

    prior1 = {
        "universe": U12,
        "active": {"KEY_TYPE_IS_INT", "BATCH_SIZE_IN_OBSERVED_SET"},
        "falsified": set(c1["falsified_predicates"]),
        "expected": set(c1["selected_repair"]["active_after"]),
    }
    prior2 = {
        "universe": U12,
        "active": {"BATCH_SIZE_IN_OBSERVED_SET"},
        "falsified": set(c2["falsified_predicates"]),
        "expected": set(c2["selected_repair"]["active_after"]),
    }

    # Independent continuations exposing the remaining input cells.
    stale = {
        "universe": {"A","B"},
        "active": {"A"},
        "falsified": {"B"},  # B is already absent: 01 must not resurrect it.
        "expected": {"A"},
    }
    preserve = {
        "universe": {"A","B"},
        "active": {"A"},
        "falsified": set(),
        "expected": {"A"},   # exercises 10 and 00.
    }

    candidates = []
    for mask in range(16):
        table = tt(mask)
        checks = {}
        outputs = {}
        for name,case in [("v13_1",prior1),("v13_2",prior2),("stale",stale),("preserve",preserve)]:
            ok, got = exact_transition(
                table, case["universe"], case["active"], case["falsified"], case["expected"]
            )
            checks[name] = ok
            outputs[name] = got
        candidates.append({
            "operator_id": mask,
            "truth_table": list(table),
            "checks": checks,
            "outputs": outputs,
            "qualified": all(checks.values()),
        })

    survivors = [c for c in candidates if c["qualified"]]
    selected = survivors[0] if len(survivors) == 1 else None

    mutations = []
    if selected:
        base = tuple(selected["truth_table"])
        witness_cases = {
            0: preserve,   # 00
            1: stale,      # 01
            2: preserve,   # 10
            3: prior1,     # 11
        }
        for bit in range(4):
            m = list(base)
            m[bit] = 1 - m[bit]
            m = tuple(m)
            case = witness_cases[bit]
            ok, got = exact_transition(
                m, case["universe"], case["active"], case["falsified"], case["expected"]
            )
            mutations.append({
                "bit": bit,
                "mutated_truth_table": list(m),
                "fails": not ok,
                "observed_next": got,
            })

    heldout = {
        "universe": {"A","B","C","D","E"},
        "active": {"A","B","C"},
        "falsified": {"B","D"},
        "expected": {"A","C"},
    }
    heldout_ok = False
    heldout_got = None
    if selected:
        heldout_ok, heldout_got = exact_transition(
            tuple(selected["truth_table"]),
            heldout["universe"], heldout["active"], heldout["falsified"], heldout["expected"]
        )

    # Ablation: without any edit operator, the first V13 blocked state remains unchanged,
    # so the falsified KEY_TYPE predicate still blocks the residual.
    ablated_next = set(prior1["active"])
    ablation_unresolved = "KEY_TYPE_IS_INT" in ablated_next

    expected_table = [0,0,1,0]  # active_next = active_now AND NOT falsified

    gates = {
        "G1_v13_verdict_exact": True,
        "G2_complete_16_transducer_substrate": len(candidates) == 16,
        "G3_exactly_one_survivor": len(survivors) == 1,
        "G4_selected_table_expected": selected is not None and selected["truth_table"] == expected_table,
        "G5_replays_v13_transition_1": selected is not None and selected["checks"]["v13_1"],
        "G6_replays_v13_transition_2": selected is not None and selected["checks"]["v13_2"],
        "G7_stale_residual_no_resurrection": selected is not None and selected["checks"]["stale"],
        "G8_no_residual_preservation": selected is not None and selected["checks"]["preserve"],
        "G9_all_single_bit_mutations_fail": len(mutations) == 4 and all(m["fails"] for m in mutations),
        "G10_ablation_leaves_blockage_unresolved": ablation_unresolved,
        "G11_heldout_all_four_cells_transfer": heldout_ok and set(heldout_got) == {"A","C"},
    }

    verdict = (
        "VERIFIED_OUTER_EDIT_OPERATION_GENESIS_FROM_ANONYMOUS_TRANSDUCER_SUBSTRATE"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )

    result = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_OUTER_EDIT_OPERATION_GENESIS",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "selected_operator": selected,
        "single_bit_mutations": mutations,
        "heldout": {
            "active": sorted(heldout["active"]),
            "falsified": sorted(heldout["falsified"]),
            "expected": sorted(heldout["expected"]),
            "observed": heldout_got,
            "passed": heldout_ok,
        },
        "ablation": {
            "next_state_without_operator": sorted(ablated_next),
            "residual_unresolved": ablation_unresolved,
        },
        "gates": gates,
        "claim_boundary": [
            "complete anonymous 16-member local Boolean state-transducer substrate supplied",
            "residual typing supplied by sealed V13 evidence",
            "finite state-transition qualification and held-out transfer",
            "subject and verifier supplied",
        ],
        "remaining_frontier": (
            "genesis of the generic transducer substrate / lower edit calculus itself"
        ),
    }

    (OUT / "final_evidence.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not verdict.startswith("VERIFIED_"):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
