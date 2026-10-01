#!/usr/bin/env python3
"""Crystal V54: exact parameter-cylinder reclosure with canonical owner returns.

The sole V23 residual family is n(t)=N0+NC*t.  A cell t=r+2^d*u carries
both the protected source y=N+S*u and its current coalescent owner x=X+R*u.
We execute renewal blocks symbolically whenever their valuations are uniform.
If the next valuation depends on u, we split only that forced parameter bit.

Each owner block is checked against V53's exact affine law.  A cell closes
when the V25 D/S/M constructor bank closes it or when 4*x<=3*y holds uniformly.
This is an exact bounded CEGAR/reclosure gate.  A finite-depth empty frontier
would still need a recursive cover theorem; a surviving cell is the next exact
counterexample to the current quotient.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import argparse
import hashlib
import json

import collatz_crystal_parameter_quotient_v25 as v25
import collatz_owner_renewal_affine_v0 as v53


@dataclass(frozen=True)
class Family:
    d: int
    r: int
    source0: int
    source_slope: int
    current0: int
    current_slope: int
    blocks: int


def uniform_v2(a: int, c: int):
    """Return v2(a+c*u), or None when it is not fixed for every u>=0."""
    s = v53.v2(a)
    return s if c % (1 << (s + 1)) == 0 else None


def symbolic_block(x0: int, xs: int, guard: int = 100_000):
    """Return a uniform owner family and V53 map, or the forced split seam."""
    assert x0 > 0 and x0 % 2 == 1 and xs % 2 == 0
    a, c = x0, xs
    low_depth = 0
    intercept = 0
    word = []
    for _ in range(guard):
        s = uniform_v2(3 * a + 1, 3 * c)
        if s is None:
            return {"split": True, "word": tuple(word), "at0": a, "slope": c}
        assert s >= 1
        na = (3 * a + 1) >> s
        nc = (3 * c) >> s
        if s >= 3:
            k = (s - 1) // 2
            strip = (4**k - 1) // 3
            if c % 4**k:
                return {"split": True, "word": tuple(word), "at0": a, "slope": c}
            assert a >= strip and (a - strip) % 4**k == 0
            p0 = (a - strip) // 4**k
            ps = c // 4**k
            amap = v53.AffineMap(
                2 ** (low_depth + 2 * k),
                3 ** len(word),
                intercept - 2**low_depth * strip,
            )
            assert amap.apply_exact(x0) == p0
            assert amap.A * xs == amap.P * ps
            # Concrete representatives independently replay the same block.
            for u in (0, 1, 3):
                b = v53.renewal_block(x0 + xs * u)
                assert b.owner == p0 + ps * u
                assert b.word == tuple(word) and b.high_s == s
                assert b.affine == amap
            return {
                "split": False, "owner0": p0, "owner_slope": ps,
                "word": tuple(word), "high_s": s, "affine": amap,
            }
        assert s in (1, 2)
        intercept = 3 * intercept + 2**low_depth
        low_depth += s
        word.append(s)
        a, c = na, nc
    raise RuntimeError("symbolic low-valuation guard exhausted")


def uniform_three_quarter(f: Family) -> bool:
    return (4 * f.current0 <= 3 * f.source0 and
            4 * f.current_slope <= 3 * f.source_slope)


def uniform_lower_source(f: Family) -> bool:
    """Every owner in the cylinder is a positive source below its source."""
    return (f.current0 < f.source0 and
            f.current_slope <= f.source_slope)


def split(f: Family, bit: int) -> Family:
    assert bit in (0, 1)
    return Family(
        f.d + 1,
        f.r + (bit << f.d),
        f.source0 + bit * f.source_slope,
        2 * f.source_slope,
        f.current0 + bit * f.current_slope,
        2 * f.current_slope,
        f.blocks,
    )


def advance_until_seam(f: Family, block_cap: int):
    path = []
    while f.blocks < block_cap:
        if uniform_lower_source(f):
            return "OWNER_LOWER", f, path
        if uniform_three_quarter(f):
            return "OWNER_3Q", f, path
        b = symbolic_block(f.current0, f.current_slope)
        if b["split"]:
            return "SPLIT", f, path
        f = Family(f.d, f.r, f.source0, f.source_slope,
                   b["owner0"], b["owner_slope"], f.blocks + 1)
        path.append(b)
    return "BLOCK_CAP", f, path


def pack(f: Family):
    return {
        "d": f.d, "r": str(f.r), "blocks": f.blocks,
        "source0": str(f.source0), "sourceSlope": str(f.source_slope),
        "current0": str(f.current0), "currentSlope": str(f.current_slope),
        "margin0": str(3 * f.source0 - 4 * f.current0),
        "marginSlope": str(3 * f.source_slope - 4 * f.current_slope),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--block-cap", type=int, default=256)
    args = ap.parse_args()

    root = Family(0, 0, v25.N0, v25.NC, v25.N0, v25.NC, 0)
    frontier = [root]
    levels = []
    totals = Counter()
    certificate = hashlib.sha256()
    first_survivor = None
    first_block_cap = None
    capped_residual = []
    max_blocks = 0
    distinct_extended_words = set()

    for depth in range(args.depth + 1):
        assert all(f.d == depth for f in frontier)
        nxt = []
        level = Counter()
        for f in frontier:
            # Reclose against the pre-V53 exact D/S/M constructor bank first.
            old = v25.classify_cell(f.d, f.r, with_merge=True)
            if old["terminal"]:
                kind = "BANK_" + old["exit"]["kind"]
                level[kind] += 1; totals[kind] += 1
                continue

            status, end, path = advance_until_seam(f, args.block_cap)
            max_blocks = max(max_blocks, end.blocks)
            for b in path:
                distinct_extended_words.add((b["word"], b["high_s"]))
            certificate.update(
                f"{f.d},{f.r},{status},{end.current0},{end.current_slope},{end.blocks},"
                f"{[(b['word'],b['high_s'],b['affine'].P,b['affine'].A,b['affine'].C) for b in path]}\n".encode()
            )
            level[status] += 1; totals[status] += 1
            if status == "SPLIT":
                if depth < args.depth:
                    nxt.extend((split(end, 0), split(end, 1)))
                else:
                    capped_residual.append(end)
                    if first_survivor is None:
                        first_survivor = pack(end)
            elif status == "BLOCK_CAP":
                capped_residual.append(end)
                if first_block_cap is None:
                    first_block_cap = pack(end)

        levels.append({"depth": depth, "input": len(frontier),
                       "outcomes": dict(sorted(level.items())),
                       "next": len(nxt),
                       "capped_residual": len(capped_residual)})
        if not nxt:
            break
        frontier = nxt

    residual_count = len(capped_residual)
    residual_groups = Counter((f.blocks, f.current_slope) for f in capped_residual)
    residual_group_rows = [
        {
            "blocks": blocks,
            "currentSlope": str(slope),
            "count": count,
            "residues": [f.r for f in capped_residual
                         if (f.blocks, f.current_slope) == (blocks, slope)],
        }
        for (blocks, slope), count in sorted(
            residual_groups.items(), key=lambda row: (-row[1], row[0]))
    ]
    owner_closures = totals["OWNER_LOWER"] + totals["OWNER_3Q"]

    result = {
        "schema": "COLLATZ_CRYSTAL_OWNER_CYLINDER_RECLOSURE_V54",
        "parents": {
            "V25": "collatz-crystal-parameter-quotient-v25",
            "V53": "collatz-owner-renewal-affine-v0@f63ab0dce12b900dec14777b5cfb00c9e663df84",
        },
        "depth_cap": args.depth,
        "block_cap": args.block_cap,
        "levels": levels,
        "totals": dict(sorted(totals.items())),
        "frontier": residual_count,
        "first_frontier_cell": first_survivor,
        "first_block_cap_cell": first_block_cap,
        "residual_owner_groups": residual_group_rows,
        "incremental_owner_closures": owner_closures,
        "max_blocks_before_seam": max_blocks,
        "distinct_extended_words": len(distinct_extended_words),
        "certificate_sha256": certificate.hexdigest(),
        "verdict": ("BOUNDED_FRONTIER_EMPTY" if residual_count == 0
                    else "EXACT_CYLINDER_FRONTIER_SURVIVES"),
        "interpretation": (
            "Every transition is symbolic over an infinite parameter cylinder. "
            "A split occurs only when the next valuation is not uniform; D/S/M "
            "and owner lower-source/three-quarter exits are reclosed before refinement."
        ),
        "promotion_boundary": (
            "Even an empty bounded frontier is not QED without a recursive cover. "
            "A survivor is the exact minimum counterexample cell for the next separator."
        ),
        "next_action": (
            "If incremental_owner_closures is zero, freeze this refinement as a negative "
            "result and separate the residual by source-relative affine phase; do not "
            "increase raw cylinder depth as a substitute for a recursive cover."
        ),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
