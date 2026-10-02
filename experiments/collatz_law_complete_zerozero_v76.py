#!/usr/bin/env python3
"""V76: forget observed switch adjacency and close the exact residual law alphabet.

V75 proved that two consecutive zero-only source-precision refinements are absent
from the frozen source-free V53/V58 transition graph. That graph still remembers
which law-to-law edges happened to be observed in the finite prospective corpus.

V76 removes exactly that distinction. It keeps only the exact residual affine
return-law alphabet, grouped by anchor, and over-approximates the transition
relation by permitting every same-anchor change to a distinct affine centre.
No source key and no observed adjacency is retained.

For each four-law sequence L0,L1,L2,L3 in this law-complete supergrammar, pull
the four affine centres back through the preceding affine maps and compute
  p0 = v2(C0-C1), p1 = v2(C1-C2), p2 = v2(C2-C3).
A genuine precision-refining three-switch path requires
  0 <= p0 < p1 < p2.
The newly earned intervals are [p0,p1) and [p1,p2). We test whether both
intervals can be all zero.

Because this is an over-approximation, absence of a zero-zero path is stronger
than absence in the observed graph: observed adjacency and source keys may then
be forgotten for this protected question. Presence of a zero-zero path is also
useful: its first exact law sequence is the separator showing that source/key
admission carries necessary information.

This remains a finite grammar result, not a universal Collatz theorem.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json
import os
import sys

frozen = os.environ.get("V60_EXPERIMENTS_DIR")
if frozen:
    sys.path.insert(0, frozen)

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53

PARENT_V75_QUAL = "678569748525ba669343247a900f2b27276d1977ae4e0a6c4fa1374f87479796"


def law(z):
    return (z["A"], z["B"], z["P"], z["D"])


def centre(L):
    A, B, P, _ = L
    den = P - A
    assert den != 0
    return Fraction(B, den)


def v2z(x: int):
    x = abs(x)
    if x == 0:
        return None
    return (x & -x).bit_length() - 1


def rat_v2(q: Fraction):
    if q == 0:
        return None
    return v2z(q.numerator) - v2z(q.denominator)


def rational_residue(q: Fraction, bits: int):
    assert bits >= 0
    if bits == 0:
        return 0
    mod = 1 << bits
    den = q.denominator % mod
    assert den & 1
    return (q.numerator * pow(den, -1, mod)) % mod


def zero_interval(q: Fraction, lo: int, hi: int):
    assert 0 <= lo < hi
    residue = rational_residue(q, hi)
    return ((residue >> lo) & ((1 << (hi - lo)) - 1)) == 0


def advance(comp, L):
    Abar, Bbar, Pbar = comp
    A, B, P, _ = L
    return (
        A * Abar,
        A * Bbar + B * Pbar,
        P * Pbar,
    )


def pull(comp, c):
    Abar, Bbar, Pbar = comp
    return (Pbar * c - Bbar) / Abar


def encode_law(L):
    return list(map(int, L))


def main():
    # Exact residual law alphabet from the frozen V53 prospective corpus.
    laws_by_anchor = defaultdict(set)
    residual_rows = 0
    for tr in v53.transitions:
        s = tr["src"]
        if s["residual"]:
            laws_by_anchor[s["anchor"]].add(law(s))
            residual_rows += 1
        if tr["kind"] == "RESIDUAL":
            d = tr["dst"]
            assert d["residual"]
            laws_by_anchor[d["anchor"]].add(law(d))

    laws_by_anchor = {
        a: tuple(sorted(ls))
        for a, ls in sorted(laws_by_anchor.items())
    }
    unique_laws = sum(len(v) for v in laws_by_anchor.values())
    assert unique_laws > 0

    law_counts = {str(a): len(ls) for a, ls in laws_by_anchor.items()}
    centre_counts = {
        str(a): len({centre(L) for L in ls})
        for a, ls in laws_by_anchor.items()
    }

    # Complete same-anchor distinct-centre directed edge count.
    complete_edges = 0
    for a, ls in laws_by_anchor.items():
        cs = {L: centre(L) for L in ls}
        complete_edges += sum(
            1 for L0 in ls for L1 in ls if cs[L0] != cs[L1]
        )

    pair_prefixes = 0
    nonnegative_pair_prefixes = 0
    strict_precision_triples = 0
    first_zero_triples = 0
    strict_quads_after_first_zero = 0
    second_zero_after_first_zero = 0
    zero_zero = []
    first_zero_samples = []
    precision_hist = Counter()
    width_hist = Counter()

    # O(sum n_anchor^3) until a first-zero triple is found; the fourth law is
    # only explored from those exact first-zero prefixes.
    for anchor, ls in laws_by_anchor.items():
        cs = {L: centre(L) for L in ls}
        for L0 in ls:
            C0 = cs[L0]
            comp1 = advance((1, 0, 1), L0)
            for L1 in ls:
                if cs[L1] == cs[L0]:
                    continue
                pair_prefixes += 1
                C1 = pull(comp1, cs[L1])
                p0 = rat_v2(C0 - C1)
                if p0 is None or p0 < 0:
                    continue
                nonnegative_pair_prefixes += 1
                comp2 = advance(comp1, L1)

                for L2 in ls:
                    if cs[L2] == cs[L1]:
                        continue
                    C2 = pull(comp2, cs[L2])
                    p1 = rat_v2(C1 - C2)
                    if p1 is None or not (p0 < p1):
                        continue
                    strict_precision_triples += 1
                    z1 = zero_interval(C1, p0, p1)
                    precision_hist[(anchor, p0, p1)] += 1
                    width_hist[(p1 - p0, z1)] += 1
                    if not z1:
                        continue

                    first_zero_triples += 1
                    if len(first_zero_samples) < 20:
                        first_zero_samples.append({
                            "anchor": anchor,
                            "laws": [encode_law(L0), encode_law(L1), encode_law(L2)],
                            "pulled_centres": [
                                [C0.numerator, C0.denominator],
                                [C1.numerator, C1.denominator],
                                [C2.numerator, C2.denominator],
                            ],
                            "precisions": [p0, p1],
                            "first_width": p1 - p0,
                        })

                    comp3 = advance(comp2, L2)
                    for L3 in ls:
                        if cs[L3] == cs[L2]:
                            continue
                        C3 = pull(comp3, cs[L3])
                        p2 = rat_v2(C2 - C3)
                        if p2 is None or not (p1 < p2):
                            continue
                        strict_quads_after_first_zero += 1
                        z2 = zero_interval(C2, p1, p2)
                        if not z2:
                            continue
                        second_zero_after_first_zero += 1

                        if len(zero_zero) < 20:
                            # Construct one natural congruence representative
                            # compatible with the second precision condition.
                            r = rational_residue(C2, p2 + 1)
                            witness = r ^ (1 << p2)
                            zero_zero.append({
                                "anchor": anchor,
                                "laws": [
                                    encode_law(L0), encode_law(L1),
                                    encode_law(L2), encode_law(L3),
                                ],
                                "pulled_centres": [
                                    [C0.numerator, C0.denominator],
                                    [C1.numerator, C1.denominator],
                                    [C2.numerator, C2.denominator],
                                    [C3.numerator, C3.denominator],
                                ],
                                "precisions": [p0, p1, p2],
                                "interval_widths": [p1 - p0, p2 - p1],
                                "natural_congruence_witness": witness,
                            })

    result = {
        "schema": "COLLATZ_LAW_COMPLETE_ZEROZERO_V76",
        "parent_v75_qualification_sha256": PARENT_V75_QUAL,
        "source_keys_retained": False,
        "observed_adjacency_retained": False,
        "alphabet_source": "exact residual affine laws occurring in frozen V53 transitions",
        "residual_transition_rows_seen": residual_rows,
        "anchors": len(laws_by_anchor),
        "unique_residual_laws": unique_laws,
        "laws_by_anchor": law_counts,
        "distinct_centres_by_anchor": centre_counts,
        "law_complete_distinct_centre_edges": complete_edges,
        "pair_prefixes_tested": pair_prefixes,
        "nonnegative_pair_prefixes": nonnegative_pair_prefixes,
        "strict_precision_triples": strict_precision_triples,
        "first_zero_triples": first_zero_triples,
        "strict_quads_after_first_zero": strict_quads_after_first_zero,
        "zero_zero_paths": second_zero_after_first_zero,
        "zero_zero_status": (
            "FEASIBLE_IN_LAW_COMPLETE_OVERAPPROX"
            if second_zero_after_first_zero
            else "ABSENT_IN_LAW_COMPLETE_OVERAPPROX"
        ),
        "sample_first_zero_triples": first_zero_samples,
        "sample_zero_zero_paths": zero_zero,
        "width_histogram": {
            repr(k): v for k, v in sorted(width_hist.items(), key=lambda z: (-z[1], repr(z[0])))
        },
        "precision_histogram_top": {
            repr(k): v for k, v in sorted(precision_hist.items(), key=lambda z: (-z[1], repr(z[0])))[:100]
        },
        "interpretation": (
            "Every same-anchor distinct-centre transition among the frozen exact "
            "residual law alphabet is allowed, so this is a strict over-approximation "
            "of the observed V75 graph. A zero-zero witness means law identity alone "
            "is insufficient and the exact witness localizes the missing information "
            "to source/key/edge admission. Absence means observed adjacency and source "
            "keys are unnecessary for excluding zero-zero on this finite law alphabet."
        ),
        "next_if_absent": (
            "Generate the residual return-law alphabet from the episode/certificate "
            "constructors rather than observed corpus rows; universal promotion still "
            "requires all-depth source-admitted grammar completeness."
        ),
        "next_if_present": (
            "Take the first exact zero-zero law sequence and intersect the target-law "
            "admissibility congruences with the source-cylinder constraints to find "
            "the minimum source/key separator that forbids or realizes it."
        ),
        "global_collatz": "UNKNOWN",
        "qed": False,
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
