#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT / "prior_v13"
RESULT = ROOT / "results" / "final_evidence.json"
OUT = ROOT / "results" / "independent_verification.json"

def load_v13():
    fs = list(PRIOR.rglob("final_evidence.json"))
    if len(fs) != 1:
        raise RuntimeError(f"expected one V13 final evidence, found {len(fs)}")
    return json.loads(fs[0].read_text())

def step(mask, universe, active, falsified):
    nxt = set()
    for item in universe:
        a = 1 if item in active else 0
        f = 1 if item in falsified else 0
        idx = 2*a + f
        out = (mask >> idx) & 1
        if out:
            nxt.add(item)
    return nxt

def qualifies(mask, cases):
    return all(step(mask, *c[:3]) == c[3] for c in cases)

def main():
    v13 = load_v13()
    observed = json.loads(RESULT.read_text())

    if (v13.get("final_verdict") or v13.get("verdict")) != "VERIFIED_RESIDUAL_GUIDED_SCHEMA_SCOPE_GROWTH_AND_TRANSFER":
        raise RuntimeError("V13 authority mismatch")

    key = "KEY_TYPE_IS_INT"
    batch = "BATCH_SIZE_IN_OBSERVED_SET"
    c1 = v13["consequence_1_v11"]
    c2 = v13["consequence_2_v12"]

    cases = [
        (
            {key,batch},
            {key,batch},
            set(c1["falsified_predicates"]),
            set(c1["selected_repair"]["active_after"]),
        ),
        (
            {key,batch},
            {batch},
            set(c2["falsified_predicates"]),
            set(c2["selected_repair"]["active_after"]),
        ),
        (
            {"A","B"},
            {"A"},
            {"B"},
            {"A"},
        ),
        (
            {"A","B"},
            {"A"},
            set(),
            {"A"},
        ),
    ]

    survivors = [m for m in range(16) if qualifies(m, cases)]

    heldout = (
        {"A","B","C","D","E"},
        {"A","B","C"},
        {"B","D"},
        {"A","C"},
    )
    heldout_ok = len(survivors) == 1 and step(survivors[0], *heldout[:3]) == heldout[3]

    run_source = (ROOT / "run.py").read_text()
    implementation_name_control = "DROP_ONE_FAILED_SCOPE_PREDICATE" not in run_source

    gates = {
        "unique_survivor_mask_4": survivors == [4],
        "observed_selected_id_matches": observed["selected_operator"]["operator_id"] == 4,
        "observed_truth_table_matches": observed["selected_operator"]["truth_table"] == [0,0,1,0],
        "heldout_transfer_matches": heldout_ok,
        "named_v13_drop_operation_absent_from_implementation": implementation_name_control,
        "all_primary_v30_gates_true": all(bool(v) for v in observed["gates"].values()),
    }

    verdict = "INDEPENDENT_V30_REPLAY_PASS" if all(gates.values()) else "INDEPENDENT_V30_REPLAY_FAIL"
    out = {
        "verdict": verdict,
        "survivors": survivors,
        "gates": gates,
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    if verdict != "INDEPENDENT_V30_REPLAY_PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
