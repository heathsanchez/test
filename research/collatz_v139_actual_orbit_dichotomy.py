"""V139 exact controls for the formal actual-orbit residual dichotomy.

No finite loop is evidence that ALL positive shortcut orbits terminate.
No high-endpoint prefix is an unbounded-orbit certificate for fixed n.
No source-capped proxy is substituted for general source-to-source merging.
"""
from __future__ import annotations
import hashlib
import json


def shortcut(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def shortcut_minus(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3 * n - 1) // 2


def finite_orbit(a: int, step_limit: int = 2000):
    seen = {}
    value = a
    max_value = a
    first_below = None
    for k in range(step_limit + 1):
        max_value = max(max_value, value)
        if first_below is None and value < a:
            first_below = k
        if value in seen:
            return {
                "start":a, "first_repeat":seen[value],
                "repeat_clock":k, "period":k-seen[value],
                "repeated_value":value, "max_value":max_value,
                "first_below_clock":first_below,
            }
        seen[value] = k
        value = shortcut(value)
    raise AssertionError(f"sample orbit did not repeat before {step_limit}: {a}")


def exact_controls():
    checks = [finite_orbit(n) for n in range(1, 2001)]
    assert len(checks) == 2000
    assert all(c["period"]==2 and c["repeated_value"] in (1,2)
               for c in checks)
    assert all(c["max_value"] >= c["start"] for c in checks)
    first27 = next(c for c in checks if c["start"]==27)
    assert first27["first_below_clock"] == 59
    x = 27
    for _ in range(59):
        x = shortcut(x)
    assert x == 23
    mersenne = []
    for K in (4, 8, 16, 32, 64):
        n = (1 << K) - 1
        x = n
        for j in range(K + 1):
            assert x == 3**j * (1 << (K-j)) - 1
            assert x >= n
            if j < K:
                x=shortcut(x)
        mersenne.append({
            "K":K, "source_digits":len(str(n)),
            "no_direct_descent_through_K":True,
            "source_capped_hit_checked":False,
            "general_merger_absence_claimed":False,
        })
    negative_cycle=[5]
    for _ in range(3):
        negative_cycle.append(shortcut_minus(negative_cycle[-1]))
    assert negative_cycle == [5,7,10,5]
    assert min(negative_cycle[:-1]) > 2

    # This is a closed finite regression on genuine positive 3n+1.
    # The minus-map example demonstrates that the abstract orbit
    # dichotomy does not by itself prohibit nonterminal positive cycles.
    return {
      "schema":"COLLATZ_V139_ACTUAL_ORBIT_OBSTRUCTION_CONTROLS",
      "scope":"finite exact arithmetic plus independently formal generic pigeonhole",
      "finite_positive_starts":2000,
      "finite_sample_terminal_cycles":2000,
      "sampled_orbit_max_first_repeat":max(c["repeat_clock"] for c in checks),
      "source27_first_below_clock":59,
      "source27_at_59":23,
      "mersenne_corridors":mersenne,
      "alternate_3n_minus_1_nonterminal_cycle":negative_cycle,
      "countercontrol_does_not_describe_positive_3n_plus_1":True,
      "positive_3n_plus_1_nonterminal_cycle_excluded_universally":False,
      "positive_3n_plus_1_unbounded_orbit_excluded_universally":False,
      "least_bad_no_earlier_source_meeting_proven_only_conditionally":True,
      "global_collatz":"UNKNOWN",
      "qed":False,
    }


if __name__ == "__main__":
    print(json.dumps(exact_controls(),sort_keys=True,indent=2))
