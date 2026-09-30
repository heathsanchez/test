#!/usr/bin/env python3
"""V55: exact source-product -> accelerated least-realizer adapter.

Purpose
-------
The Collatz origin programme counts low canonical source residues R among
ordinary shortcut prefixes that have not yet crossed the coefficient barrier.
The external EOC formalization counts positive accelerated valuation words by
their exact least natural realizer modulo 2^(S_N+1).

This gate tests the exact finite adapter needed to reuse that machinery.

For a live ordinary prefix of depth j with 0 < R < 2^K and
    qmin(j) - 1 > K,
the last odd state occurs at some depth p > K. Since the source residue is
still below 2^K, every source lift at depths >= K is necessarily zero. Thus
the source has frozen before p. Group the parity prefix through p into the
completed accelerated valuation word d=(d_0,...,d_{N-1}), where
    N = q - 1,  S_N = p.
V55 independently computes the EOC-style least realizer
    3^N r + Q_N(d) == 2^S_N  (mod 2^(S_N+1))
and requires r == R.

It also checks:
  * every accelerated prefix is critically confined: 2^(S_i) <= 3^i;
  * the affine carry endpoint matches the shortcut endpoint at p;
  * for each fixed (j,K), the map from low-origin live states to valuation
    words is injective.

This is an exact bounded semantic-adapter gate, not a proof of the external
shellwise hypothesis and not a Collatz proof.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json

MAX_DEPTH = 20
MAX_K = 12


def qmins(depth: int):
    out = [0] * (depth + 1)
    q = 0
    p3 = 1
    for j in range(1, depth + 1):
        while p3 < (1 << j):
            p3 *= 3
            q += 1
        out[j] = q
    return out


QMIN = qmins(MAX_DEPTH)


def shortcut(x: int) -> int:
    return (3 * x + 1) // 2 if x & 1 else x // 2


def eoc_carry(ds):
    s = 0
    q = 0
    for d in ds:
        q = 3 * q + (1 << s)
        s += d
    return s, q


def least_realizer(ds):
    N = len(ds)
    S, Q = eoc_carry(ds)
    mod = 1 << (S + 1)
    inv = pow(3**N, -1, mod)
    r = ((1 << S) - Q) * inv % mod
    return r, S, Q


def odd_positions(mask: int, j: int):
    return [i for i in range(j) if (mask >> i) & 1]


# State = (odd_count, canonical source residue R, canonical endpoint Y, bits).
states = [(0, 0, 0, 0)]
checks = defaultdict(int)
windows = []
first_examples = []
global_words = set()
global_pairs = set()

for j in range(1, MAX_DEPTH + 1):
    nxt = []
    for q, R, Y, mask in states:
        for bit in (0, 1):
            lift = (bit - Y) & 1
            Rp = R + lift * (1 << (j - 1))
            z = Y + (3**q) * lift
            assert (z & 1) == bit
            Yp = (3 * z + 1) // 2 if bit else z // 2
            qp = q + bit
            mp = mask | (bit << (j - 1))
            if qp >= QMIN[j]:
                nxt.append((qp, Rp, Yp, mp))

    # Canonical source residues are unique among live prefixes.
    assert len({R for _, R, _, _ in nxt}) == len(nxt)

    for K in range(1, min(MAX_K, j - 1) + 1):
        # This is the theorem-shaped safe range: p >= q-1 >= qmin(j)-1 > K.
        if QMIN[j] - 1 <= K:
            continue
        bound = 1 << K
        eligible = []
        word_seen = {}

        for q, R, Y, mask in nxt:
            if not (0 < R < bound):
                continue
            # Positive natural minimal-bad/canonical origins are odd.
            if not (R & 1):
                continue

            pos = odd_positions(mask, j)
            assert len(pos) == q
            assert pos and pos[0] == 0
            p = pos[-1]
            assert p >= q - 1
            assert p > K

            # All bits after p and before depth j are even by definition of p.
            assert all(((mask >> i) & 1) == 0 for i in range(p + 1, j))

            # Low R and p>K force source freeze: replay R exactly.
            y = R
            replay_mask = 0
            snapshots = [R]
            for i in range(j):
                b = y & 1
                replay_mask |= b << i
                y = shortcut(y)
                snapshots.append(y)
            assert replay_mask == mask
            assert y == Y
            assert snapshots[p] & 1

            # Completed odd-to-odd valuation word ends at the last odd state p.
            # Odd positions are 0=p_0<...<p_N=p; d_i=p_(i+1)-p_i.
            ds = tuple(b - a for a, b in zip(pos, pos[1:]))
            N = len(ds)
            assert N == q - 1
            assert all(d >= 1 for d in ds)
            assert sum(ds) == p

            # Critical confinement of every completed accelerated prefix.
            s = 0
            for i, d in enumerate(ds, start=1):
                s += d
                assert (1 << s) <= 3**i
                checks["critical_confinement"] += 1

            # EOC exact-realizer congruence, computed independently.
            lr, S, Q = least_realizer(ds)
            assert S == p
            assert lr == R
            checks["least_realizer_identity"] += 1

            # Exact accelerated affine/carry endpoint at depth p.
            num = 3**N * R + Q
            assert num % (1 << S) == 0
            endpoint = num >> S
            assert endpoint == snapshots[p]
            assert endpoint & 1
            checks["carry_endpoint"] += 1

            # Terminal-parity extra bit is essential and satisfied.
            assert (3**N * R + Q - (1 << S)) % (1 << (S + 1)) == 0
            checks["terminal_parity_modulus"] += 1

            if ds in word_seen:
                # Same valuation word has a unique least realizer; therefore it
                # must be the same canonical state. Fail closed on any alias.
                assert word_seen[ds] == (R, p)
            else:
                word_seen[ds] = (R, p)

            eligible.append((R, ds, p, q))
            global_words.add(ds)
            global_pairs.add((j, K, R))

            if len(first_examples) < 20:
                first_examples.append({
                    "j": j,
                    "K": K,
                    "R": R,
                    "endpoint_at_j": Y,
                    "odd_count_q": q,
                    "last_odd_depth_p": p,
                    "valuation_length_N": N,
                    "valuation_word": list(ds),
                    "least_realizer": lr,
                    "total_S": S,
                })

        assert len(word_seen) == len(eligible)
        checks["injective_windows"] += 1
        windows.append({
            "j": j,
            "K": K,
            "low_odd_origins": len(eligible),
            "distinct_valuation_words": len(word_seen),
            "qmin_j": QMIN[j],
            "guaranteed_last_odd_gt_K": True,
        })

    states = nxt

nonempty = [w for w in windows if w["low_odd_origins"]]
max_window = max(nonempty, key=lambda w: w["low_odd_origins"], default=None)

result = {
    "schema": "COLLATZ_CRYSTAL_EOC_REALIZER_BRIDGE_V55",
    "bounds": {
        "max_ordinary_depth": MAX_DEPTH,
        "max_low_origin_bits_K": MAX_K,
    },
    "checks": dict(sorted(checks.items())),
    "windows_checked": len(windows),
    "nonempty_windows": len(nonempty),
    "distinct_adapter_pairs": len(global_pairs),
    "distinct_accelerated_words_seen": len(global_words),
    "largest_window": max_window,
    "examples": first_examples,
    "adapter": {
        "ordinary_depth": "j",
        "ordinary_odd_count": "q",
        "last_odd_depth": "p",
        "accelerated_length": "N=q-1",
        "accelerated_total_valuation": "S_N=p",
        "source_identity": "canonical R = accelerated leastRealizer(d,N)",
        "safe_low_origin_condition": "qmin(j)-1 > K and 0<R<2^K",
        "critical_confinement": "for every completed prefix i: 2^(S_i) <= 3^i",
        "terminal_parity": "least realizer uses modulus 2^(S_N+1), not merely 2^S_N",
    },
    "earned_if_green": (
        "On the tested exact boundary, every low odd canonical origin in the "
        "safe range injects into a critically confined accelerated valuation "
        "word with the identical EOC-style least natural realizer. This is the "
        "finite semantic adapter required before importing a shellwise "
        "least-realizer counting theorem."
    ),
    "promotion_boundary": (
        "Bounded exhaustion is not the universal adapter theorem. The next "
        "formal step is to prove source freeze after K and the last-odd "
        "valuation-word construction for arbitrary j,K, then align the exact "
        "critical-barrier convention with the external confinedWords API."
    ),
    "external_open_input_not_assumed": (
        "No LowFreqDecay, PowerOfTwoDangerousWindowSparsity, Tao mixing, EOC, "
        "or Collatz statement is assumed."
    ),
    "verdict": "BOUNDED_EXACT_REALIZER_ADAPTER_GREEN",
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
