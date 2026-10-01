#!/usr/bin/env python3
"""V69: test the smallest natural-bar hypothesis on the first V67 residual.

Parent V68 proved:
  * r=30 is the first V67 residual;
  * the unsplit uniform-affine reverse grammar has only identity candidates;
  * after four additional parameter bits, one depth-22 child closes.

V69 does not add a state coordinate or a new merger constructor.  It repeatedly
replays only the already-compiled D/M1/S + q7 class-merger capabilities on the
remaining r=30 subtree.  It then tests the tempting natural-bar hypothesis that
there is a fixed bound B on the number of consecutive zero source bits required
before every residual cylinder closes.

A bounded counterexample rejects only the tested constant B; it is not evidence
for an infinite bad Collatz orbit.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json

import collatz_r30_separator_v68 as parent

START_DEPTH = 18
FIRST_SPLIT_DEPTH = 22
CAL_DEPTH = 30
DEEP_CAL_DEPTH = 34
FALSIFIER_DEPTH = 36
R30 = parent.R30
N0 = parent.N0
NC = parent.NC

# Exact depth-36 residual found by deterministic reclosure.
FALSIFIER_R = 38_208_274_462


def classify(r: int, h: int):
    c = parent.simple_certificate(r, h)
    q = parent.q7_mergers(r, h)
    if c is not None:
        return c["kind"]
    if q:
        return "Q7"
    return None


def refine(frontier, from_depth: int, to_depth: int):
    levels = []
    for h in range(from_depth + 1, to_depth + 1):
        bit = 1 << (h - 1)
        children = [x for r in frontier for x in (r, r + bit)]
        survivors = []
        kinds = Counter()
        for r in children:
            k = classify(r, h)
            if k is None:
                survivors.append(r)
            else:
                kinds[k] += 1
        levels.append({
            "depth": h,
            "input_children": len(children),
            "closed_cells": sum(kinds.values()),
            "closed_by_kind": dict(sorted(kinds.items())),
            "survivors": len(survivors),
        })
        frontier = survivors
    return frontier, levels


def min_zero_tail_close_h(r: int, start_h: int, max_h: int):
    """Earliest deeper zero-extension admitted by existing D/M1/S+q7 capability.

    For fixed residue r, the source n=N0+NC*r is fixed while h only increases
    the dyadic cylinder precision and available exact prefix length.  Therefore
    scan the literal source orbit once and solve the cylinder slope inequalities
    algebraically.
    """
    n = N0 + NC * r
    y = n
    odd = 0
    pow3 = 1
    best = None
    best_kind = None
    best_detail = None
    max_k = 59 + max_h

    for k in range(max_k + 1):
        two_k = 1 << k

        # D
        if 0 < y < n and pow3 <= two_k:
            hreq = max(start_h, k - 59, 0)
            if hreq <= max_h and (best is None or hreq < best):
                best, best_kind = hreq, "D"
                best_detail = {"orbit_step": k, "endpoint": str(y), "odd_count": odd}

        # M1
        if y % 3 == 2:
            p = (2 * y - 1) // 3
            if 0 < p < n and 2 * pow3 <= 3 * two_k:
                hreq = max(start_h, k - 59, 0)
                if hreq <= max_h and (best is None or hreq < best):
                    best, best_kind = hreq, "M1"
                    best_detail = {
                        "orbit_step": k, "endpoint": str(y),
                        "odd_count": odd, "lower": str(p),
                    }

        # S: the certified quarter-splice consumes three additional source bits.
        if y % 8 == 5 and y <= 4 * n and pow3 <= 4 * two_k:
            hreq = max(start_h, k - 56, 0)
            if hreq <= max_h and (best is None or hreq < best):
                best, best_kind = hreq, "S"
                best_detail = {
                    "orbit_step_after_splice": k + 3,
                    "pre_splice_endpoint": str(y),
                    "odd_count_before_splice": odd,
                    "lower": str((y - 1) // 4),
                }

        # q7 class-merger bank.
        for word, b, oq, a, cc, d, residue in parent.Q7_LAWS:
            if y % d != residue:
                continue
            p0 = (a * y - cc) // d
            if 0 < p0 < n and a * pow3 <= d * two_k:
                hreq = max(start_h, k - 59, 0)
                if hreq <= max_h and (best is None or hreq < best):
                    best, best_kind = hreq, "Q7"
                    best_detail = {
                        "orbit_step": k, "word": word,
                        "endpoint": str(y), "lower": str(p0),
                        "odd_count": odd,
                    }

        if best == start_h:
            break

        is_odd = y & 1
        if is_odd:
            odd += 1
            pow3 *= 3
        y = parent.shortcut(y)

    return best, best_kind, best_detail


def zero_tail_profile(frontier, depth: int, max_h: int):
    waits = []
    for r in frontier:
        h, kind, detail = min_zero_tail_close_h(r, depth, max_h)
        assert h is not None
        waits.append((h - depth, r, h, kind, detail))
    waits.sort(reverse=True)
    return {
        "frontier_cells": len(frontier),
        "max_zero_wait": waits[0][0],
        "max_wait_residue": waits[0][1],
        "max_wait_close_depth": waits[0][2],
        "max_wait_kind": waits[0][3],
        "max_wait_detail": waits[0][4],
        "top_waits": [
            {"wait": w, "r": r, "close_depth": h, "kind": k}
            for w, r, h, k, _ in waits[:16]
        ],
    }


def main():
    # Reproduce the parent first split using only current compiled consequences.
    cells22 = [R30 + m * (1 << START_DEPTH) for m in range(16)]
    closed22 = [(r, classify(r, FIRST_SPLIT_DEPTH)) for r in cells22
                if classify(r, FIRST_SPLIT_DEPTH) is not None]
    assert closed22 == [(3_670_046, "D")]
    frontier22 = [r for r in cells22 if r != 3_670_046]

    frontier36, levels = refine(frontier22, FIRST_SPLIT_DEPTH, FALSIFIER_DEPTH)
    by_depth = {x["depth"]: x for x in levels}

    expected = {
        23: (30, 2, 28),
        24: (56, 2, 54),
        25: (108, 6, 102),
        26: (204, 6, 198),
        27: (396, 38, 358),
        28: (716, 45, 671),
        29: (1342, 60, 1282),
        30: (2564, 288, 2276),
        31: (4552, 294, 4258),
        32: (8516, 429, 8087),
        33: (16174, 1914, 14260),
        34: (28520, 1849, 26671),
        35: (53342, 2804, 50538),
        36: (101076, 6858, 94218),
    }
    for h, (inp, closed, survivors) in expected.items():
        z = by_depth[h]
        assert (z["input_children"], z["closed_cells"], z["survivors"]) == (
            inp, closed, survivors)

    # Recover exact calibration frontiers without re-running any discovery.
    f30, _ = refine(frontier22, FIRST_SPLIT_DEPTH, CAL_DEPTH)
    f34, _ = refine(frontier22, FIRST_SPLIT_DEPTH, DEEP_CAL_DEPTH)
    assert len(f30) == 2276 and len(f34) == 26671
    assert len(frontier36) == 94218 and FALSIFIER_R in frontier36

    p30 = zero_tail_profile(f30, CAL_DEPTH, 220)
    assert p30["max_zero_wait"] == 152
    assert p30["max_wait_residue"] == 418_119_710
    assert p30["max_wait_close_depth"] == 182
    assert p30["max_wait_kind"] == "S"

    p34 = zero_tail_profile(f34, DEEP_CAL_DEPTH, 320)
    assert p34["max_zero_wait"] == 245
    assert p34["max_wait_residue"] == 3_526_098_974
    assert p34["max_wait_close_depth"] == 279
    assert p34["max_wait_kind"] == "S"
    beyond_152 = sum(
        1 for r in f34
        if min_zero_tail_close_h(r, DEEP_CAL_DEPTH, DEEP_CAL_DEPTH + 152)[0] is None
    )
    assert beyond_152 == 18

    # Exact deeper falsifier for the newly observed B=245 bound.
    before, _, _ = min_zero_tail_close_h(
        FALSIFIER_R, FALSIFIER_DEPTH, FALSIFIER_DEPTH + 245)
    assert before is None
    fh, fk, fd = min_zero_tail_close_h(FALSIFIER_R, FALSIFIER_DEPTH, 320)
    assert (fh, fk) == (284, "S")
    assert fh - FALSIFIER_DEPTH == 248

    total_slots36 = 1 << (FALSIFIER_DEPTH - START_DEPTH)
    survivors36 = len(frontier36)
    covered36 = total_slots36 - survivors36

    result = {
        "schema": "COLLATZ_NATURAL_BAR_FALSIFIER_V69",
        "parent": "collatz-r30-separator-v68",
        "protected_capability": "LowerClassMerge via existing D/M1/S + q7 only",
        "new_merger_constructors": 0,
        "new_state_coordinates": 0,
        "r30_reclosure": {
            "levels": levels,
            "depth36_total_equivalent_slots": total_slots36,
            "depth36_closed_equivalent_slots": covered36,
            "depth36_survivors": survivors36,
            "depth36_covered_fraction": covered36 / total_slots36,
        },
        "zero_tail_calibration_depth30": p30,
        "zero_tail_deeper_depth34": p34,
        "depth34_survivors_exceeding_B152": beyond_152,
        "fixed_bound_B152": "REJECTED",
        "fixed_bound_B245": {
            "verdict": "REJECTED",
            "falsifier_depth": FALSIFIER_DEPTH,
            "falsifier_residue": FALSIFIER_R,
            "no_close_through_depth": FALSIFIER_DEPTH + 245,
            "first_close_depth": fh,
            "required_zero_wait": fh - FALSIFIER_DEPTH,
            "kind": fk,
            "detail": fd,
        },
        "status": "WARRANTED_BOUNDED_IF_GATE_GREEN",
        "interpretation": (
            "Current merger capabilities continue to contract the r=30 subtree, "
            "but the smallest observed uniform zero-run bar is not stable under "
            "refinement (152 then 245 then an exact 248-bit falsifier).  Do not "
            "promote a fixed natural-bar bound from density decay.  The next "
            "residual is to find a structural/right-congruent zero-tail progress "
            "law or an exact survivor showing which capability is missing."
        ),
        "qed": False,
        "global_collatz": "UNKNOWN",
        "scope": (
            "The first V67 residual cylinder r=30 only.  All closure tests use "
            "existing exact D/M1/S and q7 class-merger laws.  Rejection applies "
            "only to B=152 and B=245, not to every possible global bound."
        ),
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
