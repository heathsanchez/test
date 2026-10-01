#!/usr/bin/env python3
"""V75: exact zero-zero feasibility in the frozen source-free V53/V58 grammar.

V58 found 613 genuine centre-switch edges and proved on the frozen corpus that
at every such edge the next actual affine centre is strictly closer 2-adically
than the old one. V72/V74 then found no two consecutive zero-only newly earned
precision intervals on actual source trajectories.

V75 removes the source sample. It composes every exact three-switch path
available in the frozen source-free transition grammar. For four pulled centres
C0,C1,C2,C3, strict switch orientation determines
    p0 = v2(C0-C1), p1 = v2(C1-C2), p2 = v2(C2-C3)
with p0 < p1 < p2.
The first newly earned source-bit interval is [p0,p1), read from C1 modulo
2^p1; the second is [p1,p2), read from C2 modulo 2^p2. We ask whether both can
be all-zero on any grammar path.

No new state or law is introduced. A zero-zero path would be an exact
source-coherence residual. Absence of one would make no-two-zero a property of
this finite grammar only; universal Collatz would still require completeness of
the grammar for every no-exit zero-tail continuation.
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

PARENT_V58_CERT = "94e3df2bb438baaf203b70c5367bf79fa8dcfa24dcf29242fde4bb46ab966e53"
PARENT_V72_QUAL = "fe3149242a1499e40efcab04c0c9da908984304de974613d924361b9d8ee9946"
PARENT_V74_QUAL = "b8a0ed3637f3598a026fee9ce35be4d54e7f7a6fab415ec6586c0d6bd89a7bda"


def law(z):
    return (z["A"], z["B"], z["P"], z["D"])


def centre_from_law(L):
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
    mask = (1 << (hi - lo)) - 1
    return ((residue >> lo) & mask) == 0


def pulled_centres(laws):
    Abar, Bbar, Pbar = 1, 0, 1
    out = []
    for L in laws:
        c = centre_from_law(L)
        out.append((Pbar * c - Bbar) / Abar)
        A, B, P, _ = L
        Abar, Bbar, Pbar = (
            A * Abar,
            A * Bbar + B * Pbar,
            P * Pbar,
        )
    return out


def encode_state(state):
    key, L = state
    return {"key": repr(key), "law": list(L)}


def main():
    # Deduplicate exact source-free residual transitions by (key,law)->(key,law).
    edges = {}
    for tr in v53.transitions:
        if not tr["src"]["residual"] or tr["kind"] != "RESIDUAL":
            continue
        s, d = tr["src"], tr["dst"]
        sl, dl = law(s), law(d)
        if centre_from_law(sl) == centre_from_law(dl):
            continue
        src = (s["key"], sl)
        dst = (d["key"], dl)
        edges[(src, dst)] = {
            "src": src,
            "dst": dst,
        }

    outgoing = defaultdict(list)
    for e in edges.values():
        outgoing[e["src"]].append(e)

    switch_edges = len(edges)
    raw_paths = 0
    strict_paths = 0
    first_zero_paths = 0
    second_zero_paths = 0
    zero_zero = []
    interval_hist = Counter()
    precision_hist = Counter()

    for e0 in edges.values():
        for e1 in outgoing.get(e0["dst"], ()):
            for e2 in outgoing.get(e1["dst"], ()):
                raw_paths += 1
                states = [e0["src"], e0["dst"], e1["dst"], e2["dst"]]
                laws = [s[1] for s in states]
                C = pulled_centres(laws)
                p0 = rat_v2(C[0] - C[1])
                p1 = rat_v2(C[1] - C[2])
                p2 = rat_v2(C[2] - C[3])
                if None in (p0, p1, p2):
                    continue
                if not (0 <= p0 < p1 < p2):
                    continue
                strict_paths += 1
                z1 = zero_interval(C[1], p0, p1)
                z2 = zero_interval(C[2], p1, p2)
                first_zero_paths += int(z1)
                second_zero_paths += int(z2)
                interval_hist[(p1-p0, p2-p1, z1, z2)] += 1
                precision_hist[(p0,p1,p2)] += 1
                if z1 and z2:
                    # Exact natural compatibility: the congruence m ≡ C2 mod
                    # 2^p2 has natural representatives; choose the p2 bit
                    # opposite C2 to make v2(m-C2)=p2 exactly.
                    r2 = rational_residue(C[2], p2 + 1)
                    witness_m = r2 ^ (1 << p2)
                    zero_zero.append({
                        "states": [encode_state(s) for s in states],
                        "pulled_centres": [[q.numerator, q.denominator] for q in C],
                        "precisions": [p0,p1,p2],
                        "interval_widths": [p1-p0,p2-p1],
                        "natural_congruence_witness": witness_m,
                    })

    result = {
        "schema": "COLLATZ_ZEROZERO_SYMBOLIC_V75",
        "parent_v58_certificate_sha256": PARENT_V58_CERT,
        "parent_v72_qualification_sha256": PARENT_V72_QUAL,
        "parent_v74_qualification_sha256": PARENT_V74_QUAL,
        "deduplicated_genuine_switch_edges": switch_edges,
        "raw_three_switch_paths": raw_paths,
        "strict_precision_three_switch_paths": strict_paths,
        "paths_with_first_zero_interval": first_zero_paths,
        "paths_with_second_zero_interval": second_zero_paths,
        "zero_zero_paths": len(zero_zero),
        "zero_zero_status": "SOURCE_FREE_FEASIBLE" if zero_zero else "ABSENT_IN_FROZEN_GRAMMAR",
        "sample_zero_zero_paths": zero_zero[:20],
        "interval_pattern_histogram": {
            repr(k): v for k,v in sorted(interval_hist.items(), key=lambda z: (-z[1], repr(z[0])))
        },
        "precision_triple_histogram": {
            repr(k): v for k,v in sorted(precision_hist.items(), key=lambda z: (-z[1], repr(z[0])))[:100]
        },
        "interpretation": (
            "This gate over-approximates source trajectories by composing exact "
            "source-free V53 transition states. If a zero-zero path exists here, "
            "actual-source absence must come from source coherence/admission, not "
            "the local switch grammar. If none exists, the no-two-zero property "
            "belongs to this frozen finite grammar, leaving universal grammar "
            "completeness as the remaining promotion boundary."
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
