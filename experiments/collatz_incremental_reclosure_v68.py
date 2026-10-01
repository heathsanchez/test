"""V68: incremental dyadic reclosure after compiled earlier-source collision.

Start from the exact 14,574 V66 survivors at depth 18.  Refine only the
parameter bit required to expose a new fixed shortcut prefix.  At each child:
  1. replay the already-qualified direct/quarter-splice constructors;
  2. replay the 15 frozen V65 collision words, with no new reverse search;
  3. split only survivors.

This is consequence reclosure, not a new semantic representation.  The dyadic
parameter is a proof/search index; the protected present remains
(original_source,current_endpoint).
"""
import argparse
import hashlib
import json
from collections import Counter

import collatz_crystal_parameter_quotient_v25 as bank

STATE_SHA = "a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6"
V66_SHA = "3b3c73f2dab776e7218652baa1271322c1b8d6eab8dbfb950b3a7f628add2012"
START_DEPTH = 18
TARGET_DEPTH = 22


def checked_json(path, expected):
    d = json.load(open(path))
    claimed = d.pop("certificate_sha256")
    actual = hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
    assert claimed == actual == expected
    d["certificate_sha256"] = claimed
    return d


def apply_word(a, c, word):
    for ch in word:
        if ch == "E":
            a *= 2
            c *= 2
        elif ch == "O":
            if a % 3 != 2 or c % 3:
                return None
            a = (2 * a - 1) // 3
            c = (2 * c) // 3
        else:
            raise AssertionError(ch)
    return a, c


def classify(d, r, words):
    N = bank.N0 + bank.NC * r
    S = bank.NC * (1 << d)
    pref = bank.fixed_prefix(N, S)
    assert pref[-1][0] == 59 + d

    old = bank.direct_or_splice(pref, N, S)
    if old is not None:
        return {
            "closed": True,
            "kind": old["kind"],
            "depth": old["depth"],
        }

    j, A, C, q = pref[-1]
    for word in words:
        z = apply_word(A, C, word)
        if z is None:
            continue
        p0, ps = z
        if p0 <= 0:
            continue
        if (p0 < N and ps <= S) or (p0 <= N and ps < S):
            return {
                "closed": True,
                "kind": "C",
                "word": word,
                "depth": j,
                "endpoint0": str(A),
                "endpointSlope": str(C),
                "lower0": str(p0),
                "lowerSlope": str(ps),
            }

    return {
        "closed": False,
        "interface": {
            "depth": j,
            "endpoint0": str(A),
            "endpointSlope": str(C),
            "q": q,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--v66", required=True)
    args = ap.parse_args()

    state = checked_json(args.state, STATE_SHA)
    v66 = checked_json(args.v66, V66_SHA)

    live = state["joined_reclosure"]["residual_residues"]
    assert len(live) == 14934
    assert v66["input_residual_cells"] == len(live)
    assert v66["remaining_cells"] == 14574

    words = list(v66["frozen_words"])
    assert len(words) == 15
    assert words == sorted(set(words), key=lambda w: (len(w), w))

    frontier = list(v66["remaining_residues"])
    levels = []
    closure_kind_slots = Counter()
    collision_word_slots = Counter()
    raw_closed = Counter()

    # V66 whole-cell closures already occupy all descendants at target depth.
    v66_slots = v66["total_closures"] * (1 << (TARGET_DEPTH - START_DEPTH))

    for d in range(START_DEPTH + 1, TARGET_DEPTH + 1):
        children = []
        bit = 1 << (d - 1)
        for r in frontier:
            children.extend((r, r + bit))

        survivors = []
        kinds = Counter()
        words_used = Counter()
        for r in children:
            z = classify(d, r, words)
            if not z["closed"]:
                survivors.append(r)
                continue
            kind = z["kind"]
            kinds[kind] += 1
            raw_closed[kind] += 1
            slots = 1 << (TARGET_DEPTH - d)
            closure_kind_slots[kind] += slots
            if kind == "C":
                w = z["word"]
                words_used[w] += 1
                collision_word_slots[w] += slots

        levels.append({
            "depth": d,
            "input_children": len(children),
            "closed_cells": sum(kinds.values()),
            "closed_by_kind": dict(sorted(kinds.items())),
            "collision_words": dict(sorted(words_used.items(), key=lambda kv: (len(kv[0]), kv[0]))),
            "survivors": len(survivors),
            "first_survivors": survivors[:64],
        })
        frontier = survivors

    total_target_slots = len(live) * (1 << (TARGET_DEPTH - START_DEPTH))
    new_slots = sum(closure_kind_slots.values())
    survivor_slots = len(frontier)
    assert v66_slots + new_slots + survivor_slots == total_target_slots

    result = {
        "schema": "COLLATZ_INCREMENTAL_RECLOSURE_V68",
        "parent_state_sha256": STATE_SHA,
        "compiled_bank_sha256": V66_SHA,
        "start_depth": START_DEPTH,
        "target_depth": TARGET_DEPTH,
        "protected_present": ["original_source", "current_endpoint"],
        "start_cells": len(live),
        "v66_closed_cells": v66["total_closures"],
        "v66_survivor_cells": v66["remaining_cells"],
        "frozen_capability_count": len(words),
        "new_reverse_search_states": 0,
        "levels": levels,
        "target_equivalent_slots": total_target_slots,
        "v66_closed_equivalent_slots": v66_slots,
        "new_closed_equivalent_slots": new_slots,
        "new_closed_slots_by_kind": dict(sorted(closure_kind_slots.items())),
        "new_collision_slots_by_word": dict(sorted(
            collision_word_slots.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))),
        "final_survivor_slots": survivor_slots,
        "covered_equivalent_slots": v66_slots + new_slots,
        "covered_fraction_of_v61_residual": (v66_slots + new_slots) / total_target_slots,
        "remaining_residues": frontier,
        "status": "EXACT_INCREMENTAL_RECLOSURE_CANDIDATE",
        "promotion_boundary": (
            "All closures are exact affine D/S constructors or frozen exact collision-word "
            "applications.  No fresh reverse discovery occurs.  The compiled collision "
            "word laws still require generic Lean binding before their C-labeled closures "
            "are promoted to WARRANTED; survivors remain UNKNOWN."
        ),
        "global_collatz": "UNKNOWN",
        "qed": False,
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
