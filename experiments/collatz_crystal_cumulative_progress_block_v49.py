#!/usr/bin/env python3
"""V49: compose V47 eventual-progress waits into one affine macro.

V47 established on the frozen V41 corpus that every observed post-zero-tail
same-anchor return state either progresses immediately, progresses after later
contiguous same-anchor returns, or reaches an already-certified OrdinaryExit.

V45 + ReturnFixedPointDescent.lean established the reusable algebraic criterion
for one affine map:
  P*m' = A*m+B, A<P, m>=L, B<(P-A)L  ==>  m'<m.

V49 asks whether every *cumulative* progress witness from V47 also satisfies
that same source-independent V23 live-floor criterion. If yes, the 1..15
return waits are presentation only: each can be collapsed to one certified
affine macro. If not, emit the first exact cumulative block requiring a
source-specific or different rank argument.

Bounded corpus only; no global Collatz claim.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_paradoxical_return_audit_v45 as v45
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

stats = Counter()
bad_floor = []
examples = []
tested_sources = 0
max_ratio = Fraction(0, 1)
max_ratio_row = None


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def compose(block):
    A, B, D = 1, 0, 0
    for e in block:
        c = e["cert"]
        # New map after current accumulated map:
        # 2^d z = a y + b, 2^D y = A x + B
        # => 2^(D+d) z = a*A*x + a*B + b*2^D.
        B = c["A"] * B + c["B"] * (1 << D)
        A = c["A"] * A
        D += c["D"]
    return A, B, D


for r in v45.LIVE:
    for a3 in range(v45.MOD3):
        for motif in v45.MOTIFS:
            t = v45.crt_parameter(r, a3, motif)
            n = v25.N0 + v25.NC * t
            rr = v40.actual_episode_returns(f"r{r}-a{a3}-{motif}", n, v45.CAP)
            tested_sources += 1
            if rr["note"] == "ordinary exit before zero-tail":
                continue

            by = defaultdict(list)
            for e in rr["events"]:
                by[e["anchor"]].append(e)

            for anchor, es in by.items():
                es.sort(key=lambda z: (z["k0"], z["k1"]))
                L = ceil_div(v25.N0 + 1, 1 << anchor)

                for i, e in enumerate(es):
                    stats["RETURN_STATES"] += 1
                    if e["m1"] < e["m0"]:
                        stats["IMMEDIATE_DESCENT"] += 1
                        continue

                    stats["NONCONTRACTING_STARTS"] += 1
                    start_m = e["m0"]
                    j = i
                    hit = None
                    while True:
                        # Prefix i..j is a candidate cumulative macro.
                        block = es[i:j+1]
                        A, B, D = compose(block)
                        end_m = block[-1]["m1"]
                        assert A * start_m + B == (1 << D) * end_m

                        P = 1 << D
                        if A < P:
                            stats["PREFIX_COEFFICIENT_CONTRACTING"] += 1
                            if B < (P - A) * L:
                                stats["PREFIX_FIXED_BELOW_V23_FLOOR"] += 1
                                if hit is None:
                                    hit = (j, A, B, D, end_m)
                                    break

                        if j + 1 >= len(es) or es[j]["k1"] != es[j+1]["k0"]:
                            break
                        j += 1

                    if hit is not None:
                        jh, A, B, D, end_m = hit
                        stats["MACRO_FIXED_FLOOR_PROGRESS"] += 1
                        assert end_m < start_m
                        P = 1 << D
                        fp = Fraction(B, P - A)
                        ratio = fp / L
                        row = {
                            "source": str(n), "t": str(t), "motif": motif,
                            "anchor": anchor,
                            "return_count": jh - i + 1,
                            "depth": [es[i]["k0"], es[jh]["k1"]],
                            "A": str(A), "B": str(B), "D": D,
                            "m0": str(start_m), "m_end": str(end_m),
                            "v23_live_floor": str(L),
                            "fixed_point": [fp.numerator, fp.denominator],
                            "fixed_point_over_v23_floor": [
                                ratio.numerator, ratio.denominator
                            ],
                        }
                        if ratio > max_ratio:
                            max_ratio = ratio
                            max_ratio_row = row
                        if len(examples) < 30:
                            examples.append(row)
                        continue

                    # No floor-certified cumulative macro in contiguous returns.
                    # If an ordinary exit follows, V48's new socket closes it.
                    last = es[j]
                    ex = rr["first_exit"]
                    if ex is not None and ex["depth"] >= last["k1"]:
                        stats["CLOSED_BY_ORDINARY_EXIT"] += 1
                        continue

                    stats["OPEN_OR_NONFLOOR_MACRO"] += 1
                    if len(bad_floor) < 30:
                        A, B, D = compose(es[i:j+1])
                        P = 1 << D
                        bad_floor.append({
                            "source": str(n), "t": str(t), "motif": motif,
                            "anchor": anchor,
                            "return_count": j - i + 1,
                            "depth": [es[i]["k0"], es[j]["k1"]],
                            "A": str(A), "B": str(B), "D": D,
                            "coefficient_contracting": A < P,
                            "fixed_below_v23_floor":
                                (A < P and B < (P-A)*L),
                            "m0": str(start_m), "m_end": str(es[j]["m1"]),
                            "v23_live_floor": str(L),
                            "first_exit": ex,
                        })

if bad_floor:
    verdict = "CUMULATIVE_FIXED_FLOOR_PROGRESS_SEPARATOR"
else:
    verdict = "ALL_OBSERVED_NONEXIT_WAITS_COLLAPSE_TO_FIXED_FLOOR_MACRO"

res = {
    "schema": "COLLATZ_CRYSTAL_CUMULATIVE_PROGRESS_BLOCK_V49",
    "parents": {
        "V45": "collatz-crystal-paradoxical-return-audit-v45@06da33f331d3603c7dee6ec3c467ffbba178db65",
        "V47": "collatz-crystal-eventual-macro-progress-v47@71ba2aba60d0fa342eaf06fcd5e3c0bb17fb1dbc",
    },
    "tested_sources": tested_sources,
    "stats": dict(sorted(stats.items())),
    "bad_floor_blocks": bad_floor,
    "examples": examples,
    "max_fixed_point_over_v23_floor": (
        [max_ratio.numerator, max_ratio.denominator] if max_ratio_row else None
    ),
    "max_ratio_witness": max_ratio_row,
    "verdict": verdict,
    "interpretation": (
        "Tests whether every V47 delayed non-exit progress witness can be "
        "collapsed to one exact affine macro satisfying the already-formalized "
        "source-independent fixed-point-below-live-floor descent criterion."
    ),
    "promotion_boundary": (
        "A green corpus does not prove that every lawful infinite return "
        "itinerary eventually admits such a macro. The remaining theorem is "
        "source-coupled all-depth boundary loss / macro existence."
    ),
    "global_collatz": "UNKNOWN",
}
res["certificate_sha256"] = hashlib.sha256(
    json.dumps(res, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(res, indent=2, sort_keys=True))
