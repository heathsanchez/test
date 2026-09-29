#!/usr/bin/env python3
"""V50: prospective eventual-progress gate on a wider exact source family.

V47/V49 closed every observed same-anchor return state on the frozen V41
31,104-source corpus by exactly one of:
  * already-certified OrdinaryExit; or
  * immediate same-anchor m descent; or
  * a later cumulative same-anchor affine macro
        P*m' = A*m+B
    satisfying A<P and B < (P-A)*L_r, where
        L_r = ceil((V23_N0+1)/2^r).
The last condition is exactly the reusable source-independent fixed-point
criterion formalized in ReturnFixedPointDescent.lean.

V50 freezes that consequence before a disjoint wider challenge:
  64 V25 depth-9 live binary cells
  x all t mod 3^5 classes
  x six 24-bit suffix motifs
= 93,312 exact sources.

Fail closed on any post-zero source with an unresolved same-anchor return
state, zero-defect event, or horizon censoring. Report the longest wait and
the largest fixed-point/live-floor ratio among successful macros.

Bounded evidence only. Global QED still requires an all-depth theorem that
every live zero-tail path eventually reaches such an exit or macro.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
from contextlib import redirect_stdout
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40
    import collatz_crystal_paradoxical_return_audit_v45 as v45

BASE_DEPTH = 9
SUFFIX_BITS = 24
MOD3 = 3**5
CAP = 1200

MOTIFS = {
    "P001101": "001101",
    "P111001": "111001",
    "P010011": "010011",
    "P101100": "101100",
    "P00010111": "00010111",
    "P01111000": "01111000",
}

M2 = 1 << (BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)


def pattern_bits(pattern: str) -> int:
    x = 0
    for i in range(SUFFIX_BITS):
        x |= int(pattern[i % len(pattern)]) << i
    return x


def crt_parameter(r: int, a: int, pattern: str) -> int:
    t2 = r + (pattern_bits(pattern) << BASE_DEPTH)
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % (1 << BASE_DEPTH) == r
    assert t % MOD3 == a
    return t


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def compose(block):
    A, B, D = 1, 0, 0
    for e in block:
        c = e["cert"]
        B = c["A"] * B + c["B"] * (1 << D)
        A = c["A"] * A
        D += c["D"]
    return A, B, D


stats = Counter()
sources = 0
residuals = []
zero_defects = []
max_wait_returns = -1
max_wait_depth = -1
max_wait_witness = None
max_ratio = Fraction(0, 1)
max_ratio_witness = None

for r in v45.LIVE:
    for a3 in range(MOD3):
        for motif, pattern in MOTIFS.items():
            t = crt_parameter(r, a3, pattern)
            n = v25.N0 + v25.NC * t
            rr = v40.actual_episode_returns(
                f"r{r}-a{a3}-{motif}", n, CAP
            )
            sources += 1

            if rr["note"] == "ordinary exit before zero-tail":
                stats["EXIT_PRE_ZERO"] += 1
                continue

            stats["POST_ZERO_SOURCES"] += 1
            if rr["first_exit"] is None:
                stats["SOURCE_CENSORED"] += 1

            if any(e["zero_defect"] for e in rr["events"]):
                stats["ZERO_DEFECT_EVENTS"] += sum(
                    1 for e in rr["events"] if e["zero_defect"]
                )
                if len(zero_defects) < 20:
                    for e in rr["events"]:
                        if e["zero_defect"]:
                            zero_defects.append({
                                "source": str(n), "t": str(t), "motif": motif,
                                "anchor": e["anchor"],
                                "depth": [e["k0"], e["k1"]],
                                "m0": str(e["m0"]),
                                "law": [
                                    str(e["cert"]["A"]), str(e["cert"]["B"]),
                                    e["cert"]["D"], str(e["cert"]["rho"])
                                ],
                            })
                            break

            by = defaultdict(list)
            for e in rr["events"]:
                by[e["anchor"]].append(e)

            for anchor, es in by.items():
                es.sort(key=lambda z: (z["k0"], z["k1"]))
                L = ceil_div(v25.N0 + 1, 1 << anchor)

                for i, e in enumerate(es):
                    stats["RETURN_STATES"] += 1

                    if e["m1"] < e["m0"]:
                        stats["IMMEDIATE_PROGRESS"] += 1
                        continue

                    stats["NONCONTRACTING_STARTS"] += 1
                    start_m = e["m0"]
                    j = i
                    solved = False

                    while True:
                        block = es[i:j+1]
                        A, B, D = compose(block)
                        end_m = block[-1]["m1"]
                        assert A * start_m + B == (1 << D) * end_m
                        P = 1 << D

                        if A < P and B < (P - A) * L:
                            assert end_m < start_m
                            stats["FIXED_FLOOR_MACRO_PROGRESS"] += 1
                            waits = j - i + 1
                            wait_depth = es[j]["k1"] - es[i]["k0"]
                            if waits > max_wait_returns or (
                                waits == max_wait_returns and
                                wait_depth > max_wait_depth
                            ):
                                max_wait_returns = waits
                                max_wait_depth = wait_depth
                                max_wait_witness = {
                                    "source": str(n), "t": str(t),
                                    "motif": motif, "anchor": anchor,
                                    "return_count": waits,
                                    "depth": [es[i]["k0"], es[j]["k1"]],
                                    "m0": str(start_m), "m_end": str(end_m),
                                    "A": str(A), "B": str(B), "D": D,
                                    "v23_live_floor": str(L),
                                }
                            fp = Fraction(B, P - A)
                            ratio = fp / L
                            if ratio > max_ratio:
                                max_ratio = ratio
                                max_ratio_witness = {
                                    "source": str(n), "t": str(t),
                                    "motif": motif, "anchor": anchor,
                                    "return_count": waits,
                                    "depth": [es[i]["k0"], es[j]["k1"]],
                                    "A": str(A), "B": str(B), "D": D,
                                    "fixed_point": [fp.numerator, fp.denominator],
                                    "v23_live_floor": str(L),
                                    "ratio": [ratio.numerator, ratio.denominator],
                                }
                            solved = True
                            break

                        if j + 1 >= len(es) or es[j]["k1"] != es[j+1]["k0"]:
                            break
                        j += 1

                    if solved:
                        continue

                    # If this source has an actual ordinary exit after the last
                    # available same-anchor return, V48's progress-or-exit
                    # theorem socket treats that branch as terminal progress.
                    ex = rr["first_exit"]
                    if ex is not None and ex["depth"] >= es[j]["k1"]:
                        stats["CLOSED_BY_ORDINARY_EXIT"] += 1
                        continue

                    stats["UNRESOLVED_RETURN_STATES"] += 1
                    if len(residuals) < 30:
                        A, B, D = compose(es[i:j+1])
                        residuals.append({
                            "source": str(n), "t": str(t), "motif": motif,
                            "anchor": anchor,
                            "depth": [es[i]["k0"], es[j]["k1"]],
                            "return_count": j - i + 1,
                            "m0": str(start_m), "m_end": str(es[j]["m1"]),
                            "A": str(A), "B": str(B), "D": D,
                            "coefficient_contracting": A < (1 << D),
                            "fixed_below_v23_floor": (
                                A < (1 << D) and
                                B < ((1 << D) - A) * L
                            ),
                            "first_exit": ex,
                        })

if stats["ZERO_DEFECT_EVENTS"]:
    verdict = "ZERO_DEFECT_OBSTRUCTION_EMITTED"
elif stats["SOURCE_CENSORED"] or stats["UNRESOLVED_RETURN_STATES"]:
    verdict = "PROSPECTIVE_EVENTUAL_PROGRESS_SEPARATOR"
else:
    verdict = "ALL_PROSPECTIVE_RETURN_STATES_HAVE_EXIT_OR_FIXED_FLOOR_PROGRESS"

res = {
    "schema": "COLLATZ_CRYSTAL_PROSPECTIVE_EVENTUAL_PROGRESS_V50",
    "parents": {
        "V47": "collatz-crystal-eventual-macro-progress-v47@71ba2aba60d0fa342eaf06fcd5e3c0bb17fb1dbc",
        "V49": "collatz-crystal-cumulative-progress-block-v49@cf849fa7cce85cb1b7bb2daaa4a63f570909653b",
    },
    "challenge": {
        "live_binary_cells": len(v45.LIVE),
        "ternary_classes": MOD3,
        "suffix_bits": SUFFIX_BITS,
        "motifs": list(MOTIFS),
        "exact_sources": sources,
        "cap": CAP,
    },
    "stats": dict(sorted(stats.items())),
    "residuals": residuals,
    "zero_defects": zero_defects,
    "max_wait_returns": max_wait_returns if max_wait_returns >= 0 else None,
    "max_wait_depth": max_wait_depth if max_wait_depth >= 0 else None,
    "max_wait_witness": max_wait_witness,
    "max_fixed_point_over_v23_floor": (
        [max_ratio.numerator, max_ratio.denominator]
        if max_ratio_witness else None
    ),
    "max_ratio_witness": max_ratio_witness,
    "verdict": verdict,
    "interpretation": (
        "Prospective falsifier for the exact theorem-shaped dichotomy now "
        "supported by V47/V48/V49: every post-zero protected return state must "
        "eventually hit OrdinaryExit or an affine macro whose fixed point is "
        "below the source-independent V23 live floor."
    ),
    "promotion_boundary": (
        "Even a green 93,312-source challenge is bounded. The irreducible "
        "global theorem remains source-coupled all-depth macro existence / "
        "boundary loss on every ZeroTailLive path."
    ),
    "global_collatz": "UNKNOWN",
}
res["certificate_sha256"] = hashlib.sha256(
    json.dumps(res, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(res, indent=2, sort_keys=True))
