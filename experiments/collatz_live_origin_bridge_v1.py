#!/usr/bin/env python3
"""Exact finite probe and conditional closure arithmetic, NOT a Collatz proof.

Causal parent: heathsanchez/test@7ef09fc8080d15fdb5c211e3e716518ea3cc1431.
New object: live/no-coefficient-crossing source-prefix windows.
All arithmetic used for decisions is integer arithmetic. Floating logarithms
are used only to describe the worst observed distortion, never to certify it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def language_counts(depth: int) -> tuple[list[int], list[int], list[int]]:
    qmin = [0] * (depth + 1)
    q, p3 = 0, 1
    for j in range(1, depth + 1):
        while p3 < 2 ** j:
            p3 *= 3
            q += 1
        qmin[j] = q
    counts = {0: 1}
    live, terminal = [1], [0]
    for j in range(1, depth + 1):
        nxt: dict[int, int] = defaultdict(int)
        leaves = 0
        for q, count in counts.items():
            for bit in (0, 1):
                if q + bit < qmin[j]:
                    leaves += count
                else:
                    nxt[q + bit] += count
        counts = dict(nxt)
        live.append(sum(counts.values()))
        terminal.append(leaves)
        assert live[j] + terminal[j] == 2 * live[j - 1]
    return qmin, live, terminal


def first_crossing(n: int, qmin: list[int]) -> tuple[int, int, int] | None:
    y, q = n, 0
    for j in range(1, len(qmin)):
        if y % 2:
            y = (3 * y + 1) // 2
            q += 1
        else:
            y //= 2
        if q < qmin[j]:
            return j, y, q
    return None


def certify(source_bits: int = 20, depth: int = 512,
            symbolic_depth: int = 18) -> dict:
    if not 4 <= source_bits <= 24:
        raise ValueError("source_bits must be in [4,24]")
    if not 60 <= depth <= 2000:
        raise ValueError("depth must be in [60,2000]")
    if not 1 <= symbolic_depth <= min(18, source_bits, depth):
        raise ValueError("symbolic_depth must be <= min(18,source_bits,depth)")
    qmin, live, terminal = language_counts(depth)
    assert (terminal[27], terminal[31], terminal[34]) == (
        312455, 1900470, 13472296)

    histogram = [[0] * (source_bits + 1) for _ in range(depth + 1)]
    unresolved, nondescending = [], []
    max_crossing, max_crossing_source = 0, 0
    for n in range(1, 2 ** source_bits, 2):
        crossing = first_crossing(n, qmin)
        if crossing is None:
            unresolved.append(n)
            continue
        j, y, q = crossing
        histogram[j][n.bit_length()] += 1
        if j > max_crossing:
            max_crossing, max_crossing_source = j, n
        if n > 1 and y >= n:
            nondescending.append({"source": n, "depth": j, "endpoint": y})

    C = [[0] * (source_bits + 1) for _ in range(depth + 1)]
    P = [[0] * (source_bits + 1) for _ in range(depth + 1)]
    for j in range(1, depth + 1):
        for m in range(1, source_bits + 1):
            C[j][m] = C[j][m - 1] + histogram[j][m]
    for m in range(1, source_bits + 1):
        remaining = 2 ** (m - 1)
        P[0][m] = remaining
        for j in range(1, depth + 1):
            remaining -= C[j][m]
            P[j][m] = remaining

    # Independent exact source-product enumeration, NOT the forward scanner.
    # A state is (odd_count, canonical_source, canonical_endpoint).
    states = [(0, 0, 0)]
    symbolic_states, checks = 0, 0
    for j in range(1, symbolic_depth + 1):
        nxt, leaves = [], []
        for q, R, Y in states:
            for bit in (0, 1):
                lift = (bit - Y) % 2
                Rp = R + lift * 2 ** (j - 1)
                z = Y + 3 ** q * lift
                assert z % 2 == bit
                Yp = (3 * z + 1) // 2 if bit else z // 2
                state = (q + bit, Rp, Yp)
                (leaves if q + bit < qmin[j] else nxt).append(state)
        assert len(nxt) == live[j] and len(leaves) == terminal[j]
        assert len({R for _, R, _ in nxt}) == len(nxt)
        assert len({R for _, R, _ in leaves}) == len(leaves)
        for m in range(1, min(j, source_bits) + 1):
            bound = 2 ** m
            assert sum(0 < R < bound for _, R, _ in nxt) == P[j][m]
            assert sum(0 < R < bound for _, R, _ in leaves) == C[j][m]
            checks += 2
        symbolic_states += len(nxt) + len(leaves)
        states = nxt

    conservation_checks = 0
    for j in range(2, depth + 1):
        for m in range(1, min(source_bits, j - 1) + 1):
            assert P[j - 1][m] == P[j][m] + C[j][m]
            conservation_checks += 1

    observations, violations, worst = 0, [], None
    for j in range(60, depth + 1):
        for m in range(1, min(source_bits, j) + 1):
            count = P[j][m]
            if not count:
                continue
            observations += 1
            # K=2 and eta=6/125, with a stronger floor envelope.
            if count * 2 ** (j - m) > live[j] * 2 ** (1 + (6 * j) // 125):
                violations.append({"depth": j, "source_bits": m, "count": count})
            exponent = (math.log2(count) + j - m - math.log2(live[j])) / j
            if worst is None or exponent > worst["diagnostic_exponent"]:
                worst = {"depth": j, "source_bits": m, "count": count,
                         "live_words": str(live[j]),
                         "diagnostic_exponent": exponent}

    # Exact rational certificate: live[j] < 2^(951*j/1000), j>0.
    # All live words have q/j > 63/100. With t=17/10:
    # live[j] <= (1+t)^j * t^(-63*j/100).
    assert 3 ** 63 < 2 ** 100
    assert 27 ** 1000 < 2 ** 951 * 17 ** 630 * 10 ** 370
    # If P_j((j+1)^15) <= 2*2^(6*j/125)*live[j]*(j+1)^15/2^j,
    # then P_j((j+1)^15) < 2*(j+1)^15*2^(-j/1000).
    cutoff = 271782
    assert 2 ** cutoff > 2 ** 1000 * (cutoff + 1) ** 15000
    assert 2 ** (cutoff - 1) <= 2 ** 1000 * cutoff ** 15000
    # Propagation: for j+1 >= 30000,
    # (1+1/(j+1))^15000 < sum_{i>=0}(15000/(j+1))^i <= 2.
    assert cutoff + 1 >= 30000

    return {
        "schema": "COLLATZ_LIVE_ORIGIN_BRIDGE_V1",
        "parent_head": "7ef09fc8080d15fdb5c211e3e716518ea3cc1431",
        "status": "FINITE_TESTS_AND_CONDITIONAL_ARITHMETIC_ONLY",
        "canonical_residual": "nontrivial legal first-crossing cylinders with M>=0",
        "new_object": "live source-prefix count P_j(X), no coefficient crossing through j",
        "coverage_identity": "P_(j-1)(X)=P_j(X)+C_j(X) for 0<X<=2^(j-1)",
        "source_bits": source_bits, "max_depth": depth,
        "odd_sources_scanned": 2 ** (source_bits - 1),
        "max_observed_first_crossing": max_crossing,
        "first_source_attaining_max_crossing": max_crossing_source,
        "unresolved_source_count": len(unresolved),
        "unresolved_examples": unresolved[:10],
        "nontrivial_nondescending_terminal_count": len(nondescending),
        "nondescending_examples": nondescending[:10],
        "symbolic_depth": symbolic_depth,
        "symbolic_nodes_examined": symbolic_states,
        "independent_symbolic_window_checks": checks,
        "window_conservation_checks": conservation_checks,
        "nonempty_live_origin_windows_j_ge_60": observations,
        "tested_exact_envelope": "P_j(2^m)*2^(j-m)<=F_j*2^(1+floor(6*j/125))",
        "envelope_violations": len(violations),
        "violation_examples": violations[:10],
        "worst_observed": worst,
        "rational_live_entropy_upper_exponent": "951/1000",
        "conditional_origin_distortion_exponent": "6/125",
        "conditional_net_exponent": "1/1000",
        "conditional_integer_cutoff_K2_X_(j+1)^15": cutoff,
        "conditional_sufficiency": (
            "A universal live-origin envelope at X=(j+1)^15, with an explicit "
            "onset, forces eventual window emptiness. Cofinality excludes "
            "never-crossing positive sources; the P16/Rhin actual-source cap "
            "excludes late nondescending terminal crossings via their live parents."
        ),
        "not_proved": [
            "the all-depth live-origin envelope at polynomial windows",
            "a derivation of the live envelope from the earlier terminal envelope",
            "finite terminal M<0 coverage through the eventual analytic/onset cutoff",
            "a complete Lean proof importing all number-theoretic and finite certificates"
        ],
        "lean_status": "NEW_BRIDGE_NOT_FORMALIZED_IN_LEAN",
        "global_collatz": "UNKNOWN",
        "rejected_routes_reopened": []
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bits", type=int, default=20)
    parser.add_argument("--depth", type=int, default=512)
    parser.add_argument("--symbolic-depth", type=int, default=18)
    args = parser.parse_args()
    result = certify(args.source_bits, args.depth, args.symbolic_depth)
    result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["envelope_violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
