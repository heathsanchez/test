#!/usr/bin/env python3
"""Crystal V27: cost-aware 12/19 chamber joined to the V26 natural adversary.

Parent authority:
  collatz-crystal-post-p36-adversary-v26@9c68bf8f64f83ac90aa892157bd24806b511ec06

Purpose:
1. Recompile the complete 12-odd reverse chamber with the correct cost-aware
   identity notion: for each endpoint residue mod 3^12, minimize total two-cost
   S, then maximize the reverse cocycle C at fixed S.
2. Compute the exact identity-only transition graph and its recurrent SCCs.
3. Locate the V26 periodic 110/-5 corridor inside that quotient.
4. Follow the exact V26 natural source beyond depth 448 and certify its first
   simple OrdinaryExit among direct descent / quarter splice / one-step
   inverse-odd lower merge.

This is a theorem-discovery/qualification experiment. A recurrent identity SCC
is not a Collatz counterexample, and closing one concrete V26 adversary is not a
universal proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
import json
import sys

O = 12
MOD = 3**O

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
T_V26 = 685408643048678703309842726690675779814441196540003599299583389096836936979689649632335566636234945811040497388265518


def shortcut(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2


def compositions(total: int, parts: int):
    for cuts in combinations(range(1, total), parts - 1):
        p = 0
        w = []
        for c in cuts + (total,):
            w.append(c - p)
            p = c
        yield tuple(w)


def cocycle(w: tuple[int, ...]) -> int:
    c = 0
    for i, a in enumerate(w):
        c = (1 << a)*c + 3**i
    return c


# Best exact reverse representation per endpoint residue:
# minimize total two-cost S; at fixed S maximize C, which minimizes predecessor.
all_by_res = defaultdict(list)
for S in range(12, 20):
    inv = pow(1 << S, -1, MOD)
    for w in compositions(S, O):
        C = cocycle(w)
        r = (C*inv) % MOD
        all_by_res[r].append((S, C, w))

best = {}
for r, vals in all_by_res.items():
    best[r] = min(vals, key=lambda x: (x[0], -x[1], x[2]))

assert len(best) == 27_469
cost_hist = Counter(S for S, _C, _w in best.values())
assert dict(sorted(cost_hist.items())) == {
    12: 1, 13: 12, 14: 66, 15: 286,
    16: 991, 17: 2892, 18: 7274, 19: 15947,
}


def word_to_bits(w: tuple[int, ...]) -> tuple[int, ...]:
    # Reverse actions are ordered endpoint-backwards; forward segments reverse.
    out = []
    for a in reversed(w):
        out.append(1)
        out.extend([0]*(a - 1))
    return tuple(out)


def bits_to_word(bits: tuple[int, ...]) -> tuple[int, ...]:
    assert bits and bits[0] == 1 and sum(bits) == O
    ones = [i for i, b in enumerate(bits) if b]
    seg = []
    for j, i in enumerate(ones):
        nxt = ones[j + 1] if j + 1 < len(ones) else len(bits)
        seg.append(nxt - i)
    return tuple(reversed(seg))


def next_window(w: tuple[int, ...], bit: int) -> tuple[int, ...]:
    bits = list(word_to_bits(w))
    bits.append(bit)
    if bit == 1:
        ones = [i for i, b in enumerate(bits) if b]
        assert len(ones) == O + 1
        bits = bits[ones[1]:]
    assert sum(bits) == O
    return bits_to_word(tuple(bits))


def classify_word(w: tuple[int, ...]):
    S = sum(w)
    if S > 19:
        return "B", None
    C = cocycle(w)
    r = (C*pow(1 << S, -1, MOD)) % MOD
    bS, bC, bw = best[r]
    if (S, C) == (bS, bC):
        assert w == bw
        return "I", r
    assert bS < S or (bS == S and bC > C)
    return "K", r


graph = {}
outcomes = Counter()
for r, (_S, _C, w) in best.items():
    row = {}
    for bit in (0, 1):
        nw = next_window(w, bit)
        cls, nr = classify_word(nw)
        row[bit] = (cls, nr)
        outcomes[(bit, cls)] += 1
    graph[r] = row

assert outcomes == Counter({
    (0, "B"): 15_947,
    (0, "I"): 11_422,
    (0, "K"): 100,
    (1, "I"): 23_287,
    (1, "K"): 4_182,
})

# Tarjan SCCs on identity-only transitions.
sys.setrecursionlimit(200_000)
adj = {
    r: [nr for _bit, (cls, nr) in row.items() if cls == "I"]
    for r, row in graph.items()
}
index = {}
low = {}
stack = []
on_stack = set()
sccs = []
counter = 0


def strong(v: int):
    global counter
    index[v] = counter
    low[v] = counter
    counter += 1
    stack.append(v)
    on_stack.add(v)
    for w in adj[v]:
        if w not in index:
            strong(w)
            low[v] = min(low[v], low[w])
        elif w in on_stack:
            low[v] = min(low[v], index[w])
    if low[v] == index[v]:
        cc = []
        while True:
            w = stack.pop()
            on_stack.remove(w)
            cc.append(w)
            if w == v:
                break
        sccs.append(cc)


for v in adj:
    if v not in index:
        strong(v)

recurrent = []
for cc in sccs:
    if len(cc) > 1:
        recurrent.append(cc)
    elif cc[0] in adj[cc[0]]:
        recurrent.append(cc)

recurrent.sort(key=len, reverse=True)
assert len(recurrent) == 1
assert len(recurrent[0]) == 3302
recurrent_set = set(recurrent[0])

# Exact 110/-5 local identity.
minus5 = (-5) % MOD
S5, C5, W5 = best[minus5]
assert S5 == 18
assert W5 == (2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1)
assert C5 == 5*(3**12 - 2**18) == 1_346_485
assert minus5 in recurrent_set
assert word_to_bits(W5) == tuple([1, 1, 0]*6)

# F(y)=T^3(y) on the 110 corridor obeys F(y)+5=(9/8)(y+5).
# Therefore six blocks reproduce exactly the chamber identity
# 2^18*y' = 3^12*y + 5(3^12-2^18).
def F110(y: int) -> int:
    assert y % 2 == 1
    y1 = shortcut(y)
    assert y1 % 2 == 1
    y2 = shortcut(y1)
    assert y2 % 2 == 0
    return shortcut(y2)

# Exact V26 natural source and its post-448 continuation.
source = N0 + NC*T_V26
assert T_V26.bit_length() == 389

first_simple_exit = None
y = source
for depth in range(0, 700):
    # D: direct strict descent.
    if 0 < y < source:
        first_simple_exit = {
            "kind": "D",
            "depth": depth,
            "endpoint": y,
        }
        break

    # S: quarter-splice owner exists when y == 5 mod 8 and y <= 4n.
    if y % 8 == 5 and y <= 4*source:
        first_simple_exit = {
            "kind": "S",
            "depth": depth,
            "endpoint": y,
            "owner": (y - 1)//4,
        }
        break

    # M1: exact one-step odd predecessor p=(2y-1)/3.
    if y % 3 == 2:
        p = (2*y - 1)//3
        if 0 < p < source:
            assert shortcut(p) == y
            first_simple_exit = {
                "kind": "M1",
                "depth": depth,
                "endpoint": y,
                "lower_source": p,
            }
            break

    y = shortcut(y)

assert first_simple_exit == {
    "kind": "M1",
    "depth": 518,
    "endpoint": 3153565806063595623192292008776706962930529753538302578739291932144932526913539883989481655795148231465975864968669212452582684208085340111,
    "lower_source": 2102377204042397082128194672517804641953686502358868385826194621429955017942359922659654437196765487643983909979112808301721789472056893407,
}
assert first_simple_exit["lower_source"] < source

result = {
    "schema": "COLLATZ_CRYSTAL_COST_AWARE_CHAMBER_V27",
    "parent": "collatz-crystal-post-p36-adversary-v26@9c68bf8f64f83ac90aa892157bd24806b511ec06",
    "cost_aware_chamber": {
        "identity_contexts": len(best),
        "best_cost_histogram": dict(sorted(cost_hist.items())),
        "identity_transition_outcomes": {
            f"{bit}:{cls}": n for (bit, cls), n in sorted(outcomes.items())
        },
        "recurrent_identity_sccs": len(recurrent),
        "largest_recurrent_identity_scc": len(recurrent[0]),
    },
    "corridor_110_minus5": {
        "residue_mod_3pow12": minus5,
        "best_cost": S5,
        "best_reverse_word": list(W5),
        "cocycle": C5,
        "in_recurrent_identity_scc": True,
        "three_step_law": "F(y)+5=(9/8)*(y+5)",
        "eighteen_step_law": "2^18*y' = 3^12*y + 5*(3^12-2^18)",
        "interpretation": (
            "The archived cost-19 K/I/B label is too coarse here: the "
            "cost-18 reverse word is exactly the inverse of the actual "
            "(110)^6 forward block, so it is identity/replay, not progress."
        ),
    },
    "v26_natural_adversary": {
        "t": T_V26,
        "source": source,
        "first_simple_ordinary_exit": first_simple_exit,
        "closed_as_counterfactual_obstruction": True,
    },
    "scientific_verdict": (
        "COST_AWARE_CHAMBER_ALONE_REJECTED_AS_UNIVERSAL_CLOSEOUT; "
        "V26_389_BIT_ADVERSARY_RETIRED_BY_EXACT_ONE_STEP_LOWER_MERGE_AT_DEPTH_518"
    ),
    "next_residual": (
        "Intersect the 3302-state recurrent cost-aware identity SCC with the "
        "exact source-relative/canonical-M no-OrdinaryExit register. Refine "
        "only the first reachable SCC state whose M/source consequence differs; "
        "do not deepen raw parameter or residue censuses."
    ),
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}

print(json.dumps(result, indent=2))
