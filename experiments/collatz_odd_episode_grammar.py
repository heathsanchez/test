#!/usr/bin/env python3
"""Exact odd-episode transition grammar for shortcut Collatz.

For odd x>0 write

    x = 2^r m - 1,     r=v2(x+1), m odd.

After r consecutive odd shortcut steps,

    T^r(x) = 3^r m - 1.

Let

    s = v2(3^r m - 1),

and divide the resulting even run completely.  The next odd state is

    x' = (3^r m - 1)/2^s.

Writing x'=2^r' m' -1 gives the exact branch map

    m' = (3^r m + 2^s - 1) / 2^(s+r').

A branch is indexed by (r,s,r').  Its slope is 3^r/2^(s+r').

This experiment has two purposes:

1. derive and replay the exact branch grammar on the hard boundary seeds
   already found by the shell compiler;
2. enumerate exact residue classes for bounded r and classify every
   non-descending branch, SCC, and repeated-cycle affine map.

For a fixed branch/cycle, repeated traversal imposes an exact congruence on m
modulo increasing powers of 2.  The experiment reports this "2-adic
countdown" rather than treating expanding branches as free recurrence.

This is an exploratory algebra certificate.  It does NOT claim Collatz unless
the resulting grammar is proven closed for unbounded r and all SCCs receive a
well-founded rank.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


def v2(n: int) -> int:
    assert n > 0
    return (n & -n).bit_length() - 1


def T(n: int) -> int:
    return (3 * n + 1) // 2 if n & 1 else n // 2


@dataclass(frozen=True)
class Branch:
    r: int
    s: int
    rp: int
    residue: int
    modulus: int
    A: int
    B: int
    D: int

    @property
    def slope(self) -> Fraction:
        return Fraction(self.A, 1 << self.D)

    def map_m(self, m: int) -> int:
        num = self.A * m + self.B
        assert num % (1 << self.D) == 0
        return num >> self.D


def episode(x: int):
    assert x > 0 and x & 1
    r = v2(x + 1)
    m = (x + 1) >> r
    assert m & 1

    y = x
    for _ in range(r):
        assert y & 1
        y = T(y)

    s = v2(y)
    for _ in range(s):
        y = T(y)
    assert y & 1

    rp = v2(y + 1)
    mp = (y + 1) >> rp

    # Exact closed-form controls.
    assert y == ((3**r) * m - 1) >> s
    assert mp == ((3**r) * m + (1 << s) - 1) >> (s + rp)
    return r, m, s, rp, mp, y


def branch_for_residue(r: int, m: int) -> Branch:
    assert m & 1
    x = (1 << r) * m - 1
    rr, mm, s, rp, mp, xp = episode(x)
    assert rr == r and mm == m

    D = s + rp
    # Exact valuation r' needs one bit beyond denominator integrality:
    #   3^r m + 2^s - 1 == 2^D (mod 2^(D+1)).
    # Thus the exact branch cylinder is modulo 2^(D+1), not 2^D.
    mod = 1 << (D + 1)
    residue = m % mod
    b = Branch(
        r=r, s=s, rp=rp,
        residue=residue, modulus=mod,
        A=3**r, B=(1 << s) - 1, D=D,
    )
    assert b.map_m(m) == mp
    return b


def first_branch_partition(r: int, precision: int):
    """Exact distinct branch cylinders seen modulo 2^precision.

    m is odd.  An exact branch (r,s,r') needs m modulo 2^(s+r'+1):
    denominator integrality consumes s+r' bits and exact oddness of the next
    cofactor consumes one additional valuation bit.  Once this exact cylinder
    is identified, every extension of that residue has the same schema.
    """
    M = 1 << precision
    cylinders: dict[tuple[int, int, int, int], Branch] = {}
    for m in range(1, M, 2):
        b = branch_for_residue(r, m)
        if b.D + 1 > precision:
            # Exact branch identity needs D+1 bits.  Keep more singular
            # residues as precision-boundary witnesses rather than merging
            # the two incompatible top-bit extensions.
            continue
        key = (b.s, b.rp, b.residue, b.modulus)
        cylinders.setdefault(key, b)

    # Coverage is decided directly by the exact branch precision; avoid an
    # O(residues × cylinders) rematch pass.
    covered = 0
    unresolved = 0
    for m in range(1, M, 2):
        exact = branch_for_residue(r, m)
        if exact.D + 1 <= precision:
            covered += 1
        else:
            unresolved += 1
    return list(cylinders.values()), covered, unresolved


def compose_cycle(branches: list[Branch]):
    """Compose m -> (A*m+B)/2^D exactly."""
    A, B, D = 1, 0, 0
    for b in branches:
        # b((A m+B)/2^D)
        # = (b.A*(A m+B) + b.B*2^D) / 2^(D+b.D)
        B = b.A * B + b.B * (1 << D)
        A = b.A * A
        D = D + b.D
    return A, B, D


def fixed_point_sign(A: int, B: int, D: int):
    den = (1 << D) - A
    if den == 0:
        return "neutral", None
    q = Fraction(B, den)
    return ("positive" if q > 0 else "zero" if q == 0 else "negative"), q


def boundary_seeds():
    # Exact H512 boundary seeds established by prior green workflows.
    return {
        33: [12235060455, 14500812391],
        34: [20646664519, 26130934783],
        40: [
            1176549020911, 1178426794975, 1267630141951,
            1287402586111, 1488356764159, 1491446412391,
            1502556899839, 1522645159327, 1649531356143,
            1737777889599, 1776647942143, 1986500752615,
            2022066832383, 2081751768559, 2087688122619,
            2121326731431,
        ],
    }


def analyze_boundary(limit_episodes: int):
    schema = Counter()
    r_edges = Counter()
    growth = Counter()
    samples = []

    for K, seeds in boundary_seeds().items():
        for n in seeds:
            x = n
            local = []
            for j in range(limit_episodes):
                if x == 1:
                    break
                r, m, s, rp, mp, xp = episode(x)
                b = branch_for_residue(r, m)
                assert b.map_m(m) == mp
                descending = xp < x
                schema[(r, s, rp)] += 1
                r_edges[(r, rp)] += 1
                growth[(r, s, rp, descending)] += 1
                if j < 16:
                    local.append({
                        "episode": j, "x": x, "r": r, "m": m,
                        "s": s, "rp": rp, "mp": mp,
                        "next_x": xp, "descending": descending,
                        "slope_num": b.A, "slope_den": 1 << b.D,
                    })
                x = xp
            samples.append({"K": K, "n": n, "first": local})

    return {
        "unique_schemas": len(schema),
        "top_schemas": [
            {"r": k[0], "s": k[1], "rp": k[2], "count": v}
            for k, v in schema.most_common(100)
        ],
        "r_edges": [
            {"r": k[0], "rp": k[1], "count": v}
            for k, v in r_edges.most_common()
        ],
        "samples": samples,
    }


def tarjan(nodes, edges):
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
    index = 0
    stack = []
    on = set()
    idx = {}
    low = {}
    comps = []

    def visit(v):
        nonlocal index
        idx[v] = low[v] = index
        index += 1
        stack.append(v); on.add(v)
        for w in graph[v]:
            if w not in idx:
                visit(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = stack.pop(); on.remove(w); comp.append(w)
                if w == v: break
            comps.append(sorted(comp))

    for v in sorted(nodes):
        if v not in idx:
            visit(v)
    return comps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-r", type=int, default=16)
    ap.add_argument("--precision", type=int, default=18)
    ap.add_argument("--boundary-episodes", type=int, default=128)
    ap.add_argument("--out")
    a = ap.parse_args()

    assert 2 <= a.max_r <= 32
    assert 8 <= a.precision <= 22

    rows = []
    edges = set()
    branch_bank = {}
    total_unresolved = 0

    for r in range(1, a.max_r + 1):
        branches, covered, unresolved = first_branch_partition(r, a.precision)
        total_unresolved += unresolved
        slope_counts = Counter(
            "contracting" if b.slope < 1
            else "neutral" if b.slope == 1 else "expanding"
            for b in branches
        )
        for b in branches:
            edges.add((b.r, b.rp))
            branch_bank.setdefault((b.r, b.rp), []).append(b)
        rows.append({
            "r": r,
            "precision": a.precision,
            "odd_residues": 1 << (a.precision - 1),
            "covered": covered,
            "unresolved": unresolved,
            "branches": len(branches),
            "next_r_values": sorted({b.rp for b in branches}),
            "slope_classes": dict(slope_counts),
            "max_D": max((b.D for b in branches), default=0),
        })

    nodes = set(range(1, a.max_r + 1))
    nodes.update(b for _, b in edges if b <= a.max_r)
    internal_edges = {(x, y) for x, y in edges if x in nodes and y in nodes}
    sccs = tarjan(nodes, internal_edges)
    cyclic = [c for c in sccs if len(c) > 1 or any((x, x) in internal_edges for x in c)]

    # Analyze exact self-branch affine maps. These are the simplest possible
    # recurrence cycles and expose the divisibility-countdown mechanism.
    self_maps = []
    for (r, rp), bs in sorted(branch_bank.items()):
        if r != rp:
            continue
        for b in bs:
            sign, q = fixed_point_sign(b.A, b.B, b.D)
            self_maps.append({
                "r": r, "s": b.s, "rp": rp,
                "residue": b.residue, "modulus": b.modulus,
                "A": b.A, "B": b.B, "D": b.D,
                "slope": f"{b.A}/{1<<b.D}",
                "fixed_point_sign": sign,
                "fixed_point": str(q) if q is not None else None,
            })

    # Concrete exact control for the canonical r=2 self-expanding branch.
    #
    # s=1,r'=2 gives
    #     m'=(9m+1)/8,   m'+1=9(m+1)/8.
    #
    # Exact membership in the same branch requires m == 15 (mod 16), i.e.
    # v2(m+1)>=4.  One traversal lowers v2(m+1) by exactly 3.  Thus k
    # consecutive traversals require v2(m+1)>=3k+1 and consume precisely
    # three 2-adic valuation units per repetition.
    countdown_control = []
    for k in range(1, 9):
        m = (1 << (3*k + 1)) - 1
        repeats = 0
        mm = m
        valuations = []
        while repeats < k:
            valuations.append(v2(mm + 1))
            rr, m0, s, rp, mp, xp = episode((1 << 2)*mm - 1)
            if (rr, s, rp) != (2, 1, 2):
                break
            assert mp + 1 == 9 * (mm + 1) // 8
            assert v2(mp + 1) == v2(mm + 1) - 3
            repeats += 1
            mm = mp
        countdown_control.append({
            "k": k, "m": m, "v2_m_plus_1": v2(m + 1),
            "self_repeats": repeats,
            "valuations": valuations,
        })
        assert repeats == k, (k, repeats)

    out = {
        "kind": "collatz_odd_episode_transition_grammar",
        "max_r": a.max_r,
        "precision": a.precision,
        "rows": rows,
        "total_precision_boundary_unresolved": total_unresolved,
        "sccs": sccs,
        "cyclic_sccs": cyclic,
        "self_maps": self_maps,
        "r2_self_countdown_control": countdown_control,
        "boundary": analyze_boundary(a.boundary_episodes),
        "proof_status": "exploratory_exact_bounded_grammar_not_global_proof",
    }

    raw = json.dumps(out, indent=2, sort_keys=True)
    if a.out:
        p = Path(a.out); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(raw + "\n")

    print("ODD_EPISODE_GRAMMAR",
          f"max_r={a.max_r}",
          f"precision={a.precision}",
          f"precision_boundary_unresolved={total_unresolved}",
          f"sccs={len(sccs)}",
          f"cyclic_sccs={len(cyclic)}",
          f"self_maps={len(self_maps)}")
    print("R2_SELF_DIVISIBILITY_COUNTDOWN",
          json.dumps(countdown_control, separators=(",", ":")))
    print("ODD_EPISODE_CYCLIC_SCCS",
          json.dumps(cyclic, separators=(",", ":")))
    print("VERIFIED_BOUNDED_ODD_EPISODE_TRANSITION_GRAMMAR")


if __name__ == "__main__":
    main()
