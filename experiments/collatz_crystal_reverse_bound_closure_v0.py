#!/usr/bin/env python3
"""Crystal actual-orbit reverse-bound consequence closure V0.

This is deliberately not a reverse-language automaton and not a population
argument.  It compiles already-qualified exact reverse predecessor
certificates into necessary inequalities for one hypothetical minimal bad
source.

For a reverse certificate
    d*p + c = a*y,   T^b(p)=y,
minimal-bad no-lower-merge implies p >= n, hence
    a*y - c >= d*n.                                    (1)

On the exact source-product cylinder
    n = R + 2^k*t,   y = Y + 3^q*t,
(1) is the exact integer affine constraint
    (a*Y-c-d*R) + (a*3^q-d*2^k)*t >= 0.               (2)

We intersect (2) for every applicable certificate with direct no-descent
y>=n, branch only by the exact next source bit, and carry the same tail t
forward.  Empty finite closure would be a candidate global certificate;
non-empty closure names the surviving actual-source residual.

No entropy, fixed block, return map, or statistical independence premise is
used.  The certificate bank is finite (Q<=14), so non-empty output is UNKNOWN.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "source_product_v1"))

from collatz_reverse_predecessor_tree import T, enumerate_first_contractions
from collatz_reverse_target_audit import enumerate_target, verify_certificates
from source_product import initial, advance

QMAX = 14
DEPTH = 24


@dataclass(frozen=True)
class Node:
    # All represented sources/endpoints have
    # n=R+2^k*t and y=Y+3^q*t for integer t in [L,U].
    k: int
    q: int
    R: int
    Y: int
    L: int
    U: int | None  # None = +infinity


def ceil_div(a: int, b: int) -> int:
    assert b > 0
    return -((-a) // b)


def intersect_ge(L: int, U: int | None, C: int, S: int):
    """Intersect integer interval with C+S*t >= 0."""
    before = (L, U)
    if S > 0:
        L = max(L, ceil_div(-C, S))
    elif S < 0:
        ub = C // (-S)
        U = ub if U is None else min(U, ub)
    elif C < 0:
        return None, before != (L, U)

    L = max(L, 0)
    if U is not None and L > U:
        return None, before != (L, U)
    return (L, U), before != (L, U)


def shortcut(x: int) -> int:
    return (3 * x + 1) // 2 if x & 1 else x // 2


def branch(s: Node, bit: int, p2: list[int], p3: list[int]) -> Node | None:
    """Exact SourceProduct.step restricted to the next tail parity."""
    lo = max(0, ceil_div(s.L - bit, 2))
    hi = None if s.U is None else (s.U - bit) // 2
    if hi is not None and lo > hi:
        return None

    v = s.Y + p3[s.q] * bit
    odd = v & 1
    return Node(
        k=s.k + 1,
        q=s.q + odd,
        R=s.R + p2[s.k] * bit,
        Y=shortcut(v),
        L=lo,
        U=hi,
    )


def build_bank():
    # Two already-existing sound banks:
    #  * every first-contracting reverse word through Q14;
    #  * the qualified target-directed 3/4 descendants through Q14.
    first = enumerate_first_contractions(QMAX)
    target = enumerate_target(QMAX, 3, 4)
    target_replays = verify_certificates(target, 3, 4)

    uniq = {}
    for c in first + target:
        uniq[(c.word, c.a, c.c, c.d, c.residue)] = c
    bank = list(uniq.values())

    inverse_odd = [
        c for c in bank
        if c.word == "O" and c.a == 2 and c.c == 1
        and c.d == 3 and c.residue == 2
    ]
    assert inverse_odd, "inverse-odd capability missing from compiled bank"

    index = defaultdict(list)
    for c in bank:
        index[(c.odd_inverse_steps, c.residue)].append(c)

    return first, target, target_replays, bank, index


def close_node(
    s: Node,
    index,
    p2: list[int],
    p3: list[int],
    use_reverse: bool,
    cert_kills: Counter,
):
    """Close every currently decidable necessary consequence on one cylinder."""
    L, U = s.L, s.U
    reverse_tightenings = 0

    # Direct no-exit: endpoint y >= fixed source n.
    z, _ = intersect_ge(L, U, s.Y - s.R, p3[s.q] - p2[s.k])
    if z is None:
        return None, "DIRECT_DESCENT", reverse_tightenings
    L, U = z

    if use_reverse:
        # If r<=q then y mod 3^r is fixed over this entire exact source
        # cylinder, so applying the certificate does not guess a residue.
        for r in range(1, min(s.q, QMAX) + 1):
            mod = p3[r]
            for c in index.get((r, s.Y % mod), ()):
                C = c.a * s.Y - c.c - c.d * s.R
                S = c.a * p3[s.q] - c.d * p2[s.k]
                z, tightened = intersect_ge(L, U, C, S)
                if z is None:
                    cert_kills[(c.word, r, c.a, c.c, c.d)] += 1
                    return None, "LOWER_MERGE_CERT", reverse_tightenings
                if tightened:
                    reverse_tightenings += 1
                L, U = z

    # Minimal positive bad source is odd and not terminal; root already fixes
    # oddness, this retains n>=3 under every later cylinder.
    L = max(L, ceil_div(3 - s.R, p2[s.k]))
    if U is not None and L > U:
        return None, "SOURCE_DOMAIN", reverse_tightenings

    return Node(s.k, s.q, s.R, s.Y, L, U), "LIVE", reverse_tightenings


def compiler_crosscheck() -> int:
    """Check our (R,Y,q,tail) transition against canonical source_product.py."""
    checks = 0
    for n in range(3, 512, 2):
        p = initial(n)
        k = q = R = Y = 0
        tail = n
        for _ in range(14):
            assert p.depth == k and p.odd_steps == q
            assert p.source_residue == R and p.endpoint_residue == Y
            assert p.tail == tail and p.source == n
            assert p.endpoint == Y + 3**q * tail
            checks += 1

            bit = tail & 1
            v = Y + 3**q * bit
            odd = v & 1
            R = R + 2**k * bit
            Y = shortcut(v)
            q += odd
            k += 1
            tail //= 2
            p = advance(p)
    return checks


def run_closure(index, use_reverse: bool):
    p2 = [1]
    for _ in range(DEPTH + 2):
        p2.append(2 * p2[-1])
    p3 = [1]
    for _ in range(DEPTH + 2):
        p3.append(3 * p3[-1])

    # Lean proves a minimal positive bad source is odd.  Every odd n>=3 is
    # n=1+2*t with t>=1, and after its first shortcut step
    # y=(3n+1)/2 = 2+3*t.
    front = [Node(k=1, q=1, R=1, Y=2, L=1, U=None)]
    stats = []
    cert_kills = Counter()
    total_reverse_tightenings = 0

    for depth in range(1, DEPTH + 1):
        nxt = []
        kills = Counter()
        finite_upper = 0
        positive_lower = 0
        depth_tightenings = 0

        for raw in front:
            live, reason, tightened = close_node(
                raw, index, p2, p3, use_reverse, cert_kills
            )
            depth_tightenings += tightened
            total_reverse_tightenings += tightened
            if live is None:
                kills[reason] += 1
                continue
            finite_upper += int(live.U is not None)
            positive_lower += int(live.L > 0)
            for bit in (0, 1):
                child = branch(live, bit, p2, p3)
                if child is not None:
                    nxt.append(child)

        stats.append({
            "depth": depth,
            "input_cylinders": len(front),
            "surviving_children": len(nxt),
            "kills": dict(kills),
            "surviving_finite_upper_bounds": finite_upper,
            "surviving_positive_tail_lower_bounds": positive_lower,
            "reverse_interval_tightenings": depth_tightenings,
        })
        front = nxt
        if not front:
            break

    samples = [
        {
            "k": s.k, "q": s.q, "R": s.R, "Y": s.Y,
            "L": s.L, "U": s.U,
            "coefficient_sign": (3**s.q > 2**s.k) - (3**s.q < 2**s.k),
        }
        for s in front[:20]
    ]
    top_cert_kills = [
        {
            "word": key[0], "odd_inverse_steps": key[1],
            "a": key[2], "c": key[3], "d": key[4], "kills": count,
        }
        for key, count in cert_kills.most_common(20)
    ]

    return {
        "emptied": not front,
        "last_depth": stats[-1]["depth"] if stats else 0,
        "final_survivor_cylinders": len(front),
        "total_reverse_interval_tightenings": total_reverse_tightenings,
        "depth_stats": stats,
        "top_certificate_kills": top_cert_kills,
        "survivor_samples": samples,
    }


def main():
    crosschecks = compiler_crosscheck()
    first, target, target_replays, bank, index = build_bank()

    direct = run_closure(index, use_reverse=False)
    combined = run_closure(index, use_reverse=True)

    if combined["emptied"]:
        status = "FINITE_CONSEQUENCE_KERNEL_EMPTY_CANDIDATE"
        residual = {
            "name": "LEAN_FORMALIZATION_REQUIRED",
            "statement": (
                "The finite exact consequence closure emptied using only direct "
                "descent and verified reverse lower-merge certificates.  Promote "
                "only after the closure certificate and bridge are checked in Lean."
            ),
        }
    else:
        status = "EXACT_BOUNDED_CONSEQUENCE_CLOSURE_NONEMPTY"
        residual = {
            "name": "ALL_DEPTH_REVERSE_BOUND_CAPACITY",
            "statement": (
                "Q<=14 reverse certificates prune actual source-coherent cylinders "
                "but do not empty the no-exit kernel.  The next capability must "
                "either generate source-valid reverse bounds at unbounded strength "
                "relative to the actual forward prefix, or prove a forward "
                "coefficient-capacity obstruction for the surviving cylinders."
            ),
            "not_allowed": (
                "Do not multiply finite pruning fractions, replace this with a "
                "stationary reverse automaton, or infer global Collatz from bounded emptiness."
            ),
        }

    result = {
        "schema": "COLLATZ_CRYSTAL_REVERSE_BOUND_CLOSURE_V0",
        "authority": {
            "forward": "experiments/source_product_v1/source_product.py",
            "formal": [
                "formal/Collatz/SourceProduct.lean:minimal_path_live",
                "formal/Collatz/SourceProduct.lean:at_source",
                "formal/Collatz/SourceProduct.lean:at_endpoint",
                "formal/Collatz/SourceProductAffine.lean:exact_affine",
            ],
            "reverse": [
                "experiments/collatz_reverse_predecessor_tree.py",
                "experiments/collatz_reverse_target_audit.py",
            ],
        },
        "identity": (
            "reverse certificate d*p+c=a*y plus no lower merge p<n "
            "gives exact necessary inequality a*y-c>=d*n"
        ),
        "inverse_odd_regression": {
            "certificate": "p=(2*y-1)/3 on y=2 mod 3",
            "live_consequence": "2*y-1>=3*n, hence y>=(3*n+1)/2",
        },
        "compiler_crosschecks": crosschecks,
        "bank": {
            "Qmax": QMAX,
            "first_contracting": len(first),
            "target_directed_3_over_4": len(target),
            "target_positive_replay_checks": target_replays,
            "deduplicated_certificates": len(bank),
            "indexed_residue_classes": len(index),
        },
        "depth_limit": DEPTH,
        "direct_only": direct,
        "direct_plus_reverse": combined,
        "incremental_survivor_reduction_at_depth_limit": (
            direct["final_survivor_cylinders"]
            - combined["final_survivor_cylinders"]
        ),
        "status": status,
        "residual": residual,
        "global_collatz": "UNKNOWN" if not combined["emptied"] else "CANDIDATE_PENDING_LEAN",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
