#!/usr/bin/env python3
"""Exact algebraic gates for the coupled Collatz residual.

This file does NOT claim Collatz.  It isolates and verifies the candidate
cycle-breaker suggested by the Complete-O coupled DAG experiment:

  * the apparent recurrent 3-adic state is d == -1 mod 3^J;
  * an odd shortcut refinement preserves that residue;
  * an even refinement leaves it;
  * an ordinary positive integer cannot take infinitely many consecutive
    odd shortcut steps because v2(n+1) drops by exactly one on each odd step.

The final missing global obligation is explicitly named: prove that every
reachable recurrent RIGID component of a sound finite abstraction is this
minus-one component (or otherwise break the additional components).
"""

from __future__ import annotations
import argparse


def T(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def v2(n: int) -> int:
    assert n > 0
    return (n & -n).bit_length() - 1


def odd_step(n: int) -> int:
    assert n > 0 and n & 1
    return (3 * n + 1) // 2


def minus_one_residue_preserved_odd(d: int, J: int) -> bool:
    """If d=-1 mod 3^J and d is odd, its odd shortcut image is also -1."""
    assert J >= 1 and d > 0 and d & 1
    m = 3 ** J
    assert (d + 1) % m == 0
    out = odd_step(d)
    return (out + 1) % m == 0


def minus_one_residue_not_preserved_even(d: int, J: int) -> bool:
    """An even d=-1 mod 3^J cannot remain -1 after an even shortcut step."""
    assert J >= 1 and d > 0 and d % 2 == 0
    m = 3 ** J
    assert (d + 1) % m == 0
    out = d // 2
    return (out + 1) % m != 0


def odd_countdown(n: int) -> bool:
    """Exact countdown: v2(T(n)+1)=v2(n+1)-1 for odd positive n."""
    assert n > 0 and n & 1
    return v2(odd_step(n) + 1) == v2(n + 1) - 1


def max_consecutive_odd_steps(n: int) -> int:
    """Number of consecutive odd shortcut steps before the first even state."""
    assert n > 0 and n & 1
    budget = v2(n + 1)
    x = n
    used = 0
    while x & 1:
        assert odd_countdown(x)
        x = odd_step(x)
        used += 1
    assert used == budget
    return used


def exhaustive_gate(N: int, Jmax: int) -> tuple[int, int, int]:
    countdown = 0
    odd_residue = 0
    even_exit = 0
    for n in range(1, N + 1, 2):
        assert odd_countdown(n)
        countdown += 1
        assert max_consecutive_odd_steps(n) == v2(n + 1)
    for J in range(1, Jmax + 1):
        m = 3 ** J
        # Check many positive representatives of the residue -1 mod 3^J.
        for q in range(1, 256):
            d = m * q - 1
            if d & 1:
                assert minus_one_residue_preserved_odd(d, J)
                odd_residue += 1
            else:
                assert minus_one_residue_not_preserved_even(d, J)
                even_exit += 1
    return countdown, odd_residue, even_exit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=1_000_000)
    ap.add_argument("--J", type=int, default=12)
    args = ap.parse_args()
    a, b, c = exhaustive_gate(args.N, args.J)
    print(f"COUNTDOWN_CASES {a}")
    print(f"MINUS_ONE_ODD_PRESERVATION_CASES {b}")
    print(f"MINUS_ONE_EVEN_EXIT_CASES {c}")
    print("VERIFIED_MINUS_ONE_CYCLE_BREAKER")
    print("GLOBAL_STATUS CONDITIONAL")
    print("MISSING_THEOREM universal_recurrent_rigid_components_are_minus_one")


if __name__ == "__main__":
    main()
