#!/usr/bin/env python3
"""Crystal V27: apply the qualified 12/19 reverse chamber to the V26 adversary.

Parent:
  collatz-crystal-post-p36-adversary-v26@9c68bf8f64f83ac90aa892157bd24806b511ec06

This replays every 12-odd reverse block of total 2-cost 12..19 against the
concrete V26 natural source, at every shortcut state from the V24 interface
until the source's first existing direct/splice exit.

A reverse predecessor counts only if it is a positive integer and is strictly
below the ORIGINAL source n. This is stricter and more consequential than merely
being cheaper than another reverse representation of the current endpoint.

Result is bounded to this exact adversary. It is not a global Collatz theorem.
"""

from itertools import combinations
import json

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
A59 = 91_182_490_942_926_966_077
C59 = 3**46

T_V26 = 685408643048678703309842726690675779814441196540003599299583389096836936979689649632335566636234945811040497388265518

O = 12
MOD = 3**O


def shortcut(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2


def comps(total: int, parts: int):
    for cuts in combinations(range(1, total), parts - 1):
        p = 0
        w = []
        for c in cuts + (total,):
            w.append(c - p)
            p = c
        yield tuple(w)


def cocycle(w):
    c = 0
    for i, a in enumerate(w):
        c = (1 << a)*c + 3**i
    return c


def compile_best():
    # residue -> lexicographically best (lowest S, then largest C -> smaller p)
    best = {}
    counts = {}
    for S in range(12, 20):
        inv = pow(1 << S, -1, MOD)
        cS = 0
        for w in comps(S, O):
            cS += 1
            C = cocycle(w)
            r = C*inv % MOD
            cand = (S, -C, w, C)
            if r not in best or cand[:2] < best[r][:2]:
                best[r] = cand
        counts[S] = cS
    return best, counts


def main():
    best, block_counts = compile_best()

    n = N0 + NC*T_V26
    y = A59 + C59*T_V26

    first_lower = None
    first_exit = None
    closest = None
    admitted_states = 0
    min_cost_hist = {}
    blocked_states = 0

    s = 0
    while s < 2000:
        k = 59 + s
        r = y % MOD

        if r in best:
            admitted_states += 1
            S, _negC, w, C = best[r]
            min_cost_hist[S] = min_cost_hist.get(S, 0) + 1
            numerator = (1 << S)*y - C
            assert numerator % MOD == 0
            p = numerator // MOD
            assert p > 0
            gap = p - n
            row = {
                "offset": s,
                "ordinary_depth": k,
                "residue_mod_3_12": r,
                "reverse_cost": S,
                "predecessor": p,
                "source_gap": gap,
                "actions": list(w),
            }
            if closest is None or gap < closest["source_gap"]:
                closest = row
            if p < n and first_lower is None:
                first_lower = row
        else:
            blocked_states += 1

        if y < n:
            first_exit = {"kind": "D", "offset": s, "ordinary_depth": k, "value": y}
            break
        if y % 8 == 5 and y <= 4*n:
            first_exit = {"kind": "S", "offset": s, "ordinary_depth": k, "value": y}
            break

        y = shortcut(y)
        s += 1

    assert first_exit is not None
    assert first_exit["kind"] == "S"
    assert first_exit["ordinary_depth"] == 525
    assert first_lower is None
    assert closest is not None and closest["source_gap"] > 0

    result = {
        "schema": "COLLATZ_CRYSTAL_110_CHAMBER_V27",
        "parent": "collatz-crystal-post-p36-adversary-v26@9c68bf8f64f83ac90aa892157bd24806b511ec06",
        "v26_parameter": T_V26,
        "source": n,
        "reverse_language": {
            "odd_inverse_steps": O,
            "modulus": MOD,
            "cost_range": [12, 19],
            "block_shapes_by_cost": block_counts,
            "unique_contexts": len(best),
        },
        "trajectory_audit": {
            "from_depth": 59,
            "through_first_exit_depth": first_exit["ordinary_depth"],
            "admitted_chamber_states": admitted_states,
            "blocked_chamber_states": blocked_states,
            "minimum_cost_histogram": min_cost_hist,
            "first_lower_source_predecessor": first_lower,
            "closest_reverse_predecessor": closest,
            "first_existing_exit": first_exit,
        },
        "scientific_verdict": (
            "REJECTED_ON_V26_ADVERSARY: the complete 12-odd reverse chamber with "
            "cost <=19 supplies no predecessor below the original source before "
            "the source reaches its existing quarter-splice at ordinary depth 525."
        ),
        "next_residual": (
            "The old 12/19 K/I/B chamber is replay/normalization on this corridor, "
            "not the missing source-lowering mechanism. The live universal target is "
            "a joint canonical-M/origin-carry rank or a strictly richer reverse block "
            "whose source-lowering consequence can be proved uniformly."
        ),
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
