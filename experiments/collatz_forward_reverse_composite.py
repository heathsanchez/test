#!/usr/bin/env python3
"""Compose exact forward strong-sieve states with reverse-predecessor laws.

Input rows are unresolved binary affine families from
collatz_strong_sieve_export.cpp:

    n(a) = a*2^B + b,                       a >= 1
    T^B(n(a)) = a*3^c + d.

A retained reverse-predecessor certificate has

    m == r (mod 3^o)
    p = (2^s*m - C)/3^o < m
    T^s(p) = m.

If c >= o, then 3^o divides a*3^c for every a, so certificate applicability
to the entire future family depends only on

    d == r (mod 3^o).

Substitution gives one exact affine predecessor family

    p(a) = a * [2^s * 3^(c-o)] + (2^s*d-C)/3^o.

We then compare p(a) directly with the ORIGINAL n(a), not merely with m.
If

    L = 2^s*3^(c-o) - 2^B < 0
    L < b - (2^s*d-C)/3^o,

then p(a) < n(a) for every a>=1.  Since both n(a) and p(a) reach the same m,
strong induction closes the entire binary residue family.

This is a genuinely composed constructor: the binary strong sieve did not
close the input class, and the reverse certificate is applied to its future
affine image rather than to n directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collatz_reverse_predecessor_sparse import (  # type: ignore
    enumerate_first_contractions,
    sparse_quotient,
)


def T(n: int) -> int:
    return (3 * n + 1) // 2 if n & 1 else n // 2


def iterate(n: int, steps: int) -> int:
    for _ in range(steps):
        n = T(n)
    return n


def read_states(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        b, c, d = map(int, line.split())
        rows.append((b, c, d))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--q", type=int, required=True)
    ap.add_argument("--states", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    B = args.bits
    Q = args.q
    states = read_states(args.states)
    assert states

    certs = enumerate_first_contractions(Q)
    _, _, selected, _ = sparse_quotient(certs, Q)

    # Prefix-free retained bank: at most one retained certificate can match a
    # given integer along its chain of residues modulo 3,9,27,...
    lookup = {(c.o, c.residue): c for c in selected}
    powers3 = [1]
    for _ in range(Q):
        powers3.append(powers3[-1] * 3)

    accepted = []
    matched = 0
    matched_but_not_lower = 0
    no_uniform_modulus = 0
    by_o = Counter()
    by_steps = Counter()

    for b, c, d in states:
        cert = None
        for o in range(1, min(c, Q) + 1):
            z = lookup.get((o, d % powers3[o]))
            if z is not None:
                cert = z
                break

        if cert is None:
            # This includes both "no selected cylinder matches d" and states
            # whose potentially matching reverse law is deeper than c, where
            # applicability would still depend on a mod 3^(o-c).
            no_uniform_modulus += 1
            continue

        matched += 1
        den = powers3[cert.o]
        num_const = (1 << cert.steps) * d - cert.c
        assert num_const % den == 0, (b, c, d, cert)
        p_const = num_const // den
        p_coef = (1 << cert.steps) * powers3[c - cert.o]

        L = p_coef - (1 << B)
        R = b - p_const
        universal_lower = L < 0 and L < R and p_coef + p_const > 0

        if not universal_lower:
            matched_but_not_lower += 1
            continue

        accepted.append((b, c, d, cert, p_coef, p_const))
        by_o[cert.o] += 1
        by_steps[cert.steps] += 1

    # Independent concrete replay on a deterministic spread of accepted
    # classes.  Exact closure itself comes from the affine inequalities above.
    concrete = 0
    if accepted:
        count = min(4096, len(accepted))
        chosen = [
            accepted[(i * (len(accepted) - 1)) // max(count - 1, 1)]
            for i in range(count)
        ]
        for b, c, d, cert, p_coef, p_const in chosen:
            for a in (1, 3, 17):
                n = a * (1 << B) + b
                m = a * powers3[c] + d
                p = a * p_coef + p_const

                assert 0 < p < n, (B, b, c, d, cert, a, p, n)
                assert iterate(n, B) == m
                assert iterate(p, cert.steps) == m
                concrete += 1

    before = len(states)
    new_closed = len(accepted)
    after = before - new_closed
    odd_total = 1 << (B - 1)

    result = {
        "kind": "forward_reverse_composite_constructor",
        "bits": B,
        "q": Q,
        "input_binary_live": before,
        "selected_reverse_certificates": len(selected),
        "uniform_reverse_match": matched,
        "uniform_match_not_lower_than_original": matched_but_not_lower,
        "no_uniform_reverse_match": no_uniform_modulus,
        "newly_closed_binary_classes": new_closed,
        "remaining_binary_classes": after,
        "input_odd_fraction": before / odd_total,
        "remaining_odd_fraction": after / odd_total,
        "relative_residual_reduction": (new_closed / before) if before else 0.0,
        "by_reverse_depth": {str(k): v for k, v in sorted(by_o.items())},
        "by_reverse_steps": {str(k): v for k, v in sorted(by_steps.items())},
        "concrete_replay_checks": concrete,
    }

    print(
        "FORWARD_REVERSE_COMPOSITE",
        f"B={B}",
        f"Q={Q}",
        f"input_live={before}",
        f"uniform_matches={matched}",
        f"new_closed={new_closed}",
        f"remaining={after}",
        f"relative_reduction={result['relative_residual_reduction']:.12f}",
        f"remaining_odd_fraction={result['remaining_odd_fraction']:.12f}",
    )
    for o, count in sorted(by_o.items()):
        print("FORWARD_REVERSE_DEPTH", f"o={o}", f"new_closed={count}")
    print("FORWARD_REVERSE_CONCRETE_CONTROLS", concrete)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("VERIFIED_FORWARD_REVERSE_COMPOSITE_CONSTRUCTOR")


if __name__ == "__main__":
    main()
