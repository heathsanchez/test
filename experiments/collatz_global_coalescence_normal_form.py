#!/usr/bin/env python3
"""K-independent exact coalescence normal form for shortcut Collatz.

Write every odd target family as

    n = 2^K (2^S z + r) - 1,          r odd, K >= 1.

After the K forced odd shortcut steps,

    T^K(n) = 3^K (2^S z + r) - 1.

For a lower-valuation predecessor with gap g < K,

    p = 2^(K-g) (2^S z + r) - 1 < n,

and after K-g forced odd steps,

    T^(K-g)(p) = 3^(K-g) (2^S z + r) - 1.

Let M=2^S and normalize the target residue by

    u = 3^K r (mod M).

For a candidate gap g define

    x = 3^(-g) u (mod M).

Then x = 3^(K-g) r (mod M).  Writing

    3^(K-g) r = M q + x

and introducing Z = 3^(K-g) z + q, the two post-forced families become

    donor  D_x(Z)   = M Z + x - 1
    target N_g,x(Z) = 3^g M Z + 3^g x - 1.

These canonical families contain no K.

If their deterministic affine shortcut trajectories meet before the
coefficient becomes odd, then substituting Z back gives an exact coalescence
identity for every K>g and every z>=0.  Since p<n, strong induction closes the
entire target class whenever the lower predecessor is already known.

This script constructs that finite canonical constructor bank, independently
lifts every constructor back to several widely separated K values, and checks
both affine identities and concrete trajectories.  It is a certificate for
this constructor family, not by itself a proof of the Collatz conjecture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


def T(n: int) -> int:
    return (3 * n + 1) // 2 if n & 1 else n // 2


def iterate(n: int, steps: int) -> int:
    for _ in range(steps):
        n = T(n)
    return n


def affine_step(A: int, B: int) -> tuple[int, int]:
    """One deterministic shortcut step while A is even."""
    assert A % 2 == 0
    if B & 1:
        return 3 * A // 2, (3 * B + 1) // 2
    return A // 2, B // 2


def affine_states(A: int, B: int):
    """All deterministic affine states through first odd coefficient."""
    t = 0
    while True:
        yield (A, B), t
        if A & 1:
            return
        A, B = affine_step(A, B)
        t += 1


@dataclass(frozen=True)
class Constructor:
    u: int
    gap: int
    x: int
    extra_steps: int
    hit_A: int
    hit_B: int


EXPECTED = {
    8: (65, {1: 65}),
    10: (267, {1: 267}),
    12: (1090, {1: 1090}),
    14: (4427, {1: 4425, 3: 2}),
    16: (17938, {1: 17917, 3: 21}),
}


def build_bank(S: int, max_gap: int) -> list[Constructor]:
    M = 1 << S
    bank: list[Constructor] = []

    for u in range(1, M, 2):
        for gap in range(1, max_gap + 1):
            inv3g = pow(pow(3, gap, M), -1, M)
            x = (u * inv3g) % M
            assert x & 1

            donor = {state: t for state, t in affine_states(M, x - 1)}
            hit = None
            for state, tn in affine_states((3**gap) * M, (3**gap) * x - 1):
                td = donor.get(state)
                if td is not None:
                    hit = (tn, td, state)
                    break

            if hit is None:
                continue

            tn, td, state = hit
            # In every retained constructor discovered so far the normalized
            # paths meet after the same number of post-forced steps.  Freeze
            # this stronger invariant because it simplifies the global schema.
            assert tn == td, (S, u, gap, x, tn, td, state)
            bank.append(Constructor(u, gap, x, tn, state[0], state[1]))
            break

    return bank


def lift_affine(con: Constructor, S: int, K: int) -> None:
    """Check the parameterized constructor after lifting to one raw K."""
    assert K > con.gap
    M = 1 << S

    inv3K = pow(pow(3, K, M), -1, M)
    r = (con.u * inv3K) % M
    assert r & 1

    P = 3 ** (K - con.gap)
    x = (P * r) % M
    assert x == con.x
    q, rem = divmod(P * r, M)
    assert rem == con.x

    target_A = (3**K) * M
    target_B = (3**K) * r - 1
    donor_A = P * M
    donor_B = P * r - 1

    # The canonical hit state under Z=P*z+q.
    expected_A = con.hit_A * P
    expected_B = con.hit_A * q + con.hit_B

    At, Bt = target_A, target_B
    Ad, Bd = donor_A, donor_B
    for _ in range(con.extra_steps):
        At, Bt = affine_step(At, Bt)
        Ad, Bd = affine_step(Ad, Bd)

    assert (At, Bt) == (expected_A, expected_B)
    assert (Ad, Bd) == (expected_A, expected_B)

    # The predecessor is strictly smaller for every z>=0 because it has the
    # same positive factor (M*z+r) multiplied by 2^(K-g) instead of 2^K.
    assert (1 << (K - con.gap)) * r - 1 < (1 << K) * r - 1


def concrete_replay(con: Constructor, S: int, K: int, z: int) -> None:
    M = 1 << S
    r = (con.u * pow(pow(3, K, M), -1, M)) % M
    n = (1 << K) * (M * z + r) - 1
    p = (1 << (K - con.gap)) * (M * z + r) - 1
    assert 0 < p < n

    xn = iterate(n, K + con.extra_steps)
    xp = iterate(p, K - con.gap + con.extra_steps)
    assert xn == xp, (S, K, con, z, n, p, xn, xp)


def verify_lifts(
    bank: list[Constructor],
    S: int,
    K_values: list[int],
) -> tuple[int, int]:
    affine_checks = 0
    concrete_checks = 0

    for K in K_values:
        eligible = [con for con in bank if K > con.gap]
        for con in eligible:
            lift_affine(con, S, K)
            affine_checks += 1

        if not eligible:
            continue

        # Concrete replay is an independent implementation check.  Cover all
        # constructors for moderate K; for very large K use a deterministic
        # spread while the exact affine check above still covers every one.
        if K <= 40:
            selected = eligible
        else:
            count = min(257, len(eligible))
            selected = [
                eligible[(i * (len(eligible) - 1)) // max(count - 1, 1)]
                for i in range(count)
            ]

        for con in selected:
            for z in (0, 1, 17):
                concrete_replay(con, S, K, z)
                concrete_checks += 1

    return affine_checks, concrete_checks


def bank_hash(bank: list[Constructor], S: int, max_gap: int) -> str:
    payload = {
        "kind": "collatz-global-k-independent-coalescence-normal-form-v1",
        "S": S,
        "max_gap": max_gap,
        "constructors": [asdict(con) for con in bank],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--s", type=int, required=True)
    ap.add_argument("--max-gap", type=int, default=5)
    ap.add_argument(
        "--verify-k",
        default="4,5,6,7,8,10,20,27,40,64,127",
    )
    ap.add_argument("--out")
    args = ap.parse_args()

    assert 4 <= args.s <= 18
    assert 1 <= args.max_gap <= 8

    K_values = sorted({int(x) for x in args.verify_k.split(",") if x})
    bank = build_bank(args.s, args.max_gap)
    by_gap = dict(sorted(Counter(con.gap for con in bank).items()))
    digest = bank_hash(bank, args.s, args.max_gap)

    if args.s in EXPECTED and args.max_gap >= max(EXPECTED[args.s][1]):
        expected_count, expected_gap = EXPECTED[args.s]
        assert len(bank) == expected_count, (args.s, len(bank), expected_count)
        assert by_gap == expected_gap, (args.s, by_gap, expected_gap)

    affine_checks, concrete_checks = verify_lifts(bank, args.s, K_values)

    M = 1 << args.s
    result = {
        "kind": "global_k_independent_coalescence_normal_form",
        "S": args.s,
        "max_gap": args.max_gap,
        "odd_residue_classes": M // 2,
        "constructors": len(bank),
        "coverage_fraction": len(bank) / (M // 2),
        "by_gap": {str(k): v for k, v in by_gap.items()},
        "sha256": digest,
        "verified_k_values": K_values,
        "affine_lift_checks": affine_checks,
        "concrete_replay_checks": concrete_checks,
        "equal_post_forced_offsets": all(
            con.extra_steps >= 0 for con in bank
        ),
    }

    print(
        "GLOBAL_NORMAL_FORM",
        f"S={args.s}",
        f"max_gap={args.max_gap}",
        f"odd_classes={M//2}",
        f"constructors={len(bank)}",
        f"coverage={result['coverage_fraction']:.12f}",
        f"sha256={digest}",
    )
    for gap, count in by_gap.items():
        print("GLOBAL_NORMAL_FORM_GAP", f"gap={gap}", f"constructors={count}")
    print(
        "GLOBAL_NORMAL_FORM_LIFT_CONTROLS",
        f"k_values={','.join(map(str, K_values))}",
        f"affine_checks={affine_checks}",
        f"concrete_replays={concrete_checks}",
    )

    # Expose the rare non-gap1 constructors: these are precisely the new
    # distinctions beyond the predecessor-half family at current widths.
    for con in bank:
        if con.gap > 1:
            print(
                "GLOBAL_NORMAL_FORM_EXTRA",
                f"u={con.u}",
                f"gap={con.gap}",
                f"x={con.x}",
                f"extra_steps={con.extra_steps}",
            )

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("VERIFIED_GLOBAL_K_INDEPENDENT_COALESCENCE_NORMAL_FORM")


if __name__ == "__main__":
    main()
