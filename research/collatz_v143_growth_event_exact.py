"""V143 exact source-attached two-step growth event diagnostics.

A bounded trace is NEVER promoted to a universal no-merge bar. The
unbounded-growth theorem is discharged only by the separately pinned
Lean proof and an independent same-SHA CI seal.
"""
from __future__ import annotations
import hashlib
import json


def shortcut(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def test_exact_two_step(n: int):
    value = shortcut(shortcut(n))
    if n % 4 == 3:
        assert 4 * value == 9 * n + 5
        assert value > n
        return "two_step_riser"
    assert value <= n
    return "two_step_nonexpanding"


def trace(source: int, steps: int):
    x = source
    xs = [x]
    for _ in range(steps):
        x = shortcut(x)
        xs.append(x)
    return xs


def sample_bound(source: int, steps: int):
    xs = trace(source, steps)
    B = max((x for x in xs if x % 4 == 3), default=0)
    result_bound = 2 * source + 6 * B + 5
    assert all(x <= result_bound for x in xs)
    return {"source": source, "trace_steps": steps,
            "max_actual_growing_source": B,
            "proved_form_bound_tested_only_on_prefix": result_bound,
            "peak": max(xs)}


def mersenne_corridor(K: int):
    n = 2**K - 1
    x = n
    k_growth = 0
    for j in range(K - 1):
        assert x == 3**j * 2**(K - j) - 1
        if j < K - 2:
            assert x % 4 == 3
            assert 4 * shortcut(shortcut(x)) == 9 * x + 5
            k_growth += 1
        x = shortcut(x)
    assert x == 3**(K-1) * 2 - 1
    return {"K": K, "source_decimal_digits": len(str(n)),
            "checked_two_step_growth_positions": k_growth,
            "this_is_only_a_finite_prefix": True,
            "source_varies_with_K": True}


def main():
    domain_size = 10001
    counts = {"two_step_riser": 0, "two_step_nonexpanding": 0}
    for n in range(domain_size):
        counts[test_exact_two_step(n)] += 1
    assert sum(counts.values()) == domain_size
    assert counts["two_step_riser"] == 2500
    samples = [sample_bound(n, 256) for n in range(1, 2001)]
    corridors = [mersenne_corridor(K)
                 for K in (4, 8, 16, 32, 64, 128)]
    assert samples[26]["source"] == 27
    assert all(r["peak"] <= r["proved_form_bound_tested_only_on_prefix"]
               for r in samples)
    return {
        "schema": "COLLATZ_V143_SOURCE_ATTACHED_GROWTH_EVENT_BARRIER",
        "exact_two_step_domain_size": domain_size,
        "exact_two_step_counts": counts,
        "bounded_trace_sources": len(samples),
        "bounded_trace_depth": 256,
        "sample_source27": samples[26],
        "source_changing_mersenne_negative_controls": corridors,
        "bounded_trace_is_not_infinite_proof": True,
        "unbounded_positive_source_exhibited": False,
        "all_3_mod4_growth_events_universally_bounded": False,
        "unbounded_actual_growth_event_branch_eliminated": False,
        "global_collatz": "UNKNOWN",
        "qed": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
