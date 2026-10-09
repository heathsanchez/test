"""V136 exact cross-check: primitive parity charts and phase-sensitive guards.

This is a deterministic bounded regression companion to the Lean general
theorems. Neither sample coverage nor chart construction proves Collatz.
"""
from __future__ import annotations

import json


def shortcut(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def trajectory(n: int, k: int) -> tuple[int, int]:
    odds = 0
    for _ in range(k):
        odds += n % 2
        n = shortcut(n)
    return n, odds


def witness(a: int, p: int, i: int, j: int) -> dict:
    ea, alpha = trajectory(a, i)
    ep, beta = trajectory(p, j)
    assert a > p > 0 and ea == ep
    m = min(alpha, beta)
    u, v = 3 ** (beta - m), 3 ** (alpha - m)
    old_u, old_v = 3 ** beta, 3 ** alpha
    sa, sp = (2 ** i) * u, (2 ** j) * v
    assert 3 ** alpha * u == 3 ** beta * v
    assert (sa >= sp) == (2 ** i * old_u >= 2 ** j * old_v)
    assert u == 1 or v == 1
    assert old_u == u * 3 ** m and old_v == v * 3 ** m
    return {
        "base_source": a,
        "earlier_source": p,
        "source_clock": i,
        "earlier_clock": j,
        "odd_source": alpha,
        "odd_earlier": beta,
        "common_endpoint": ea,
        "common_power_removed": 3 ** m,
        "source_slope": sa,
        "earlier_slope": sp,
        "primitive_source_coefficient": u,
        "primitive_earlier_coefficient": v,
        "guard": sp <= sa,
    }


def run() -> dict:
    roots = [(23, 3, 7, 1), (5, 3, 1, 2), (21, 3, 3, 2),
             (9, 3, 9, 1), (15, 3, 8, 1), (27, 23, 59, 0)]
    families = []
    for a, p, i, j in roots:
        w = witness(a, p, i, j)
        assert w["guard"]
        for t in range(201):
            source = a + w["source_slope"] * t
            earlier = p + w["earlier_slope"] * t
            assert 0 < earlier < source
            assert trajectory(source, i)[0] == trajectory(earlier, j)[0]
        w["tested_offsets"] = 201
        families.append(w)

    root23 = families[0]
    root5 = families[1]
    assert (root23["source_slope"], root23["earlier_slope"]) == (128, 18)
    assert root23["common_power_removed"] == 3
    assert (root5["source_slope"], root5["earlier_slope"]) == (6, 4)
    assert root5["common_power_removed"] == 3
    assert (families[-1]["source_slope"], families[-1]["earlier_slope"]) == (
        2 ** 59, 3 ** 37)

    # A genuine common endpoint but an adverse global-source slope.
    hostile = witness(5, 3, 3, 8)
    assert not hostile["guard"] and hostile["source_slope"] == 648
    assert hostile["earlier_slope"] == 768
    # t=a+1 is a constructive failure for every hostile slope pair.
    a = hostile["base_source"]
    p = hostile["earlier_source"]
    assert p + hostile["earlier_slope"] * (a + 1) >= (
        a + hostile["source_slope"] * (a + 1))

    # Adding a common actual suffix never changes the direction.
    for a, p, i, j in [(5, 3, 3, 8), (5, 3, 1, 2),
                       (23, 3, 7, 1), (27, 23, 59, 0)]:
        initial = witness(a, p, i, j)
        q = initial["common_endpoint"]
        for k in range(31):
            c = trajectory(q, k)[1]
            ai = trajectory(a, i + k)[1]
            bj = trajectory(p, j + k)[1]
            assert ai == initial["odd_source"] + c
            assert bj == initial["odd_earlier"] + c
            new_guard = 2 ** (j + k) * 3 ** ai <= 2 ** (i + k) * 3 ** bj
            assert new_guard == initial["guard"]

    # A true earlier-source meeting already refutes minimal badness;
    # no favourable lift is needed for that conditional conclusion.
    return {
        "schema": "COLLATZ_V136_PRIMITIVE_CHART_AND_SUFFIX_BOUNDARY",
        "status": "BOUNDED_EXACT_REGRESSION_NOT_FORMAL_WARRANT",
        "families": families,
        "hostile_control": hostile,
        "suffix_phase_cases": 4,
        "suffix_steps_per_case": 31,
        "original_guard_equivalent_to_primitive_guard": True,
        "reduced_cross_power_slope_match": True,
        "guard_required_for_all_offset_strict_lower_source": True,
        "no_claim_of_universal_base_meeting": True,
        "universal_collatz": "UNKNOWN",
        "qed": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
