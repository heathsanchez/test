#!/usr/bin/env python3
"""V76: forget observed switch adjacency and close the exact residual law alphabet.

V75 proved that two consecutive zero-only source-precision refinements are absent
from the frozen source-free V53/V58 transition graph. That graph still remembers
which law-to-law edges happened to be observed in the finite prospective corpus.

V76 removes exactly that distinction. It keeps only the exact residual affine
return-law alphabet, grouped by anchor, and over-approximates the transition
relation by permitting every same-anchor change to a distinct affine centre.
No source key and no observed adjacency is retained.

The exact dyadic factorization avoids a naive cubic search. For consecutive
local centres c_i,c_{i+1} and prefix affine map with denominator depth H_i,
the pulled-centre separation satisfies
    v2(C_i-C_{i+1}) = H_i + v2(c_i-c_{i+1}),
because every return multiplier A is odd and P=2^D. Thus candidate next laws
can be grouped by their local centre-separation order without changing the
mathematical search.

A positive zero-zero witness is decisive and the search stops immediately:
law identity alone is insufficient and source/key/edge admission is necessary.
If no witness exists, the grouped scan is exhaustive over the complete finite
law alphabet, so observed adjacency and source keys are forgettable for this
protected question.

This remains a finite grammar result, not a universal Collatz theorem.
"""
from __future__ import annotations

from collections import defaultdict
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
    complete_edges = 0

    pair_prefixes = 0
    factorization_checks = 0
    strict_precision_triples = 0
    first_zero_triples = 0
    strict_quads_after_first_zero = 0
    first_zero_samples = []
    witness = None

    for anchor, ls in laws_by_anchor.items():
        cs = {L: centre(L) for L in ls}

        # The residual alphabet has one centre per exact law on this boundary.
        assert len(set(cs.values())) == len(ls)
        for L in ls:
            A, _, P, D = L
            assert A % 2 == 1
            assert P == 1 << D

        # Group every possible target law by the local dyadic order of the
        # centre separation. This is the exact quotient that removes the
        # 567M-entry naive triple expansion.
        hgroups = {}
        for L0 in ls:
            g = defaultdict(list)
            c0 = cs[L0]
            for L1 in ls:
                if L1 == L0:
                    continue
                h = rat_v2(c0 - cs[L1])
                assert h is not None and h >= 0
                g[h].append(L1)
            hgroups[L0] = {h: tuple(v) for h, v in g.items()}
            complete_edges += sum(len(v) for v in g.values())

        for L0 in ls:
            A0, B0, P0, D0 = L0
            c0 = cs[L0]
            comp1 = advance((1, 0, 1), L0)

            for h01, L1s in hgroups[L0].items():
                p0_formula = D0 + h01
                for L1 in L1s:
                    pair_prefixes += 1
                    c1 = cs[L1]
                    C1 = pull(comp1, c1)

                    # Exact numeric validation of the factorization used for
                    # grouping. Since c0 is L0's fixed point, pulling c1 through
                    # L0 scales c0-c1 by P0/A0.
                    p0_direct = rat_v2(c0 - C1)
                    assert p0_direct == p0_formula
                    factorization_checks += 1
                    p0 = p0_formula

                    _, _, _, D1 = L1
                    comp2 = advance(comp1, L1)

                    for h12, L2s in hgroups[L1].items():
                        p1 = D0 + D1 + h12
                        if p1 <= p0:
                            continue
                        strict_precision_triples += len(L2s)

                        if not zero_interval(C1, p0, p1):
                            continue

                        first_zero_triples += len(L2s)
                        if len(first_zero_samples) < 20:
                            first_zero_samples.append({
                                "anchor": anchor,
                                "laws01": [encode_law(L0), encode_law(L1)],
                                "target_group_size": len(L2s),
                                "target_local_separation_order": h12,
                                "pulled_C1": [C1.numerator, C1.denominator],
                                "precisions": [p0, p1],
                                "first_width": p1 - p0,
                            })

                        for L2 in L2s:
                            c2 = cs[L2]
                            C2 = pull(comp2, c2)
                            p1_direct = rat_v2(C1 - C2)
                            assert p1_direct == p1
                            factorization_checks += 1

                            _, _, _, D2 = L2
                            comp3 = advance(comp2, L2)

                            for h23, L3s in hgroups[L2].items():
                                p2 = D0 + D1 + D2 + h23
                                if p2 <= p1:
                                    continue
                                strict_quads_after_first_zero += len(L3s)

                                if not zero_interval(C2, p1, p2):
                                    continue

                                # One exact witness is decisive for this
                                # over-approximation, so do not pay to count
                                # irrelevant additional witnesses.
                                L3 = L3s[0]
                                c3 = cs[L3]
                                C3 = pull(comp3, c3)
                                p2_direct = rat_v2(C2 - C3)
                                assert p2_direct == p2
                                factorization_checks += 1
                                r = rational_residue(C2, p2 + 1)
                                witness = {
                                    "anchor": anchor,
                                    "laws": [
                                        encode_law(L0), encode_law(L1),
                                        encode_law(L2), encode_law(L3),
                                    ],
                                    "pulled_centres": [
                                        [c0.numerator, c0.denominator],
                                        [C1.numerator, C1.denominator],
                                        [C2.numerator, C2.denominator],
                                        [C3.numerator, C3.denominator],
                                    ],
                                    "precisions": [p0, p1, p2],
                                    "interval_widths": [p1 - p0, p2 - p1],
                                    "natural_congruence_witness": r ^ (1 << p2),
                                }
                                break
                            if witness is not None:
                                break
                        if witness is not None:
                            break
                    if witness is not None:
                        break
                if witness is not None:
                    break
            if witness is not None:
                break
        if witness is not None:
            break

    exhaustive = witness is None

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
        "law_complete_distinct_centre_edges": complete_edges,
        "pair_prefixes_tested": pair_prefixes,
        "factorization_checks": factorization_checks,
        "strict_precision_triples_examined": strict_precision_triples,
        "first_zero_triples_examined": first_zero_triples,
        "strict_quads_after_first_zero_examined": strict_quads_after_first_zero,
        "zero_zero_paths": 1 if witness is not None else 0,
        "zero_zero_status": (
            "FEASIBLE_IN_LAW_COMPLETE_OVERAPPROX"
            if witness is not None
            else "ABSENT_IN_LAW_COMPLETE_OVERAPPROX"
        ),
        "exhaustive_if_absent": exhaustive,
        "sample_first_zero_groups": first_zero_samples,
        "first_zero_zero_witness": witness,
        "interpretation": (
            "Every same-anchor distinct-centre transition among the frozen exact "
            "residual law alphabet is allowed, so this strictly over-approximates "
            "the observed V75 graph. A zero-zero witness means law identity alone "
            "is insufficient and localizes necessary information to source/key/edge "
            "admission. If absent after exhaustive grouped closure, observed adjacency "
            "and source keys are unnecessary for excluding zero-zero on this finite alphabet."
        ),
        "next_if_absent": (
            "Generate the residual return-law alphabet from episode/certificate "
            "constructors rather than observed corpus rows; universal promotion still "
            "requires all-depth source-admitted grammar completeness."
        ),
        "next_if_present": (
            "Intersect the exact witness target-law admissibility congruences with "
            "source-cylinder constraints to find the minimum source/key separator "
            "that forbids or realizes this law-only zero-zero path."
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
