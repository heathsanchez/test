#!/usr/bin/env python3
"""Exact counterexample to a translation-uniform origin envelope, NOT to Collatz.

The actual fixed-origin candidate remains UNKNOWN. Shifted supports are controls,
not asserted to be Collatz-legal supports. No floating-point decision is used.
"""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from collatz_live_origin_bridge_v1 import language_counts

PARENT = '52175c9239cf63c806fc4f1ad4ff76a4f691508e'
LIVE_PARENT_SHA256 = '75df2f2590f53777bc3a7d9a2a198553059512eb4adfad2976d57b968be02168'


def first_crossing(n: int, depth: int) -> int | None:
    y, power3 = n, 1
    for k in range(1, depth + 1):
        if y & 1:
            y = (3 * y + 1) // 2
            power3 *= 3
        else:
            y //= 2
        if power3 < 1 << k:
            return k
    return None


def autocorrelation(support: list[int], modulus: int) -> list[int]:
    """Exact integer circular autocorrelation: full Fourier-power information."""
    answer = [0] * modulus
    for x in support:
        for y in support:
            answer[(x - y) % modulus] += 1
    return answer


def symbolic_controls(max_depth: int = 16) -> list[dict]:
    qmin, live, _ = language_counts(max_depth)
    frontier = [(0, 0, 0)]
    rows = []
    for j in range(1, max_depth + 1):
        nxt = []
        for q, r, y in frontier:
            for lift in (0, 1):
                rp = r + lift * (1 << (j - 1))
                z = y + lift * 3 ** q
                odd = z % 2
                yp = (3 * z + 1) // 2 if odd else z // 2
                qp = q + odd
                if qp >= qmin[j]:
                    nxt.append((qp, rp, yp))
        frontier = nxt
        support = sorted(r for _, r, _ in frontier)
        N = 1 << j
        assert len(support) == len(set(support)) == live[j]
        assert N - 1 in support
        if j < 4:
            continue
        direct = [n for n in range(1, N, 2) if first_crossing(n, j) is None]
        assert support == direct
        shifted = sorted((r + 2) % N for r in support)
        original_origin = sum(1 <= r < 4 for r in support)
        shifted_origin = sum(1 <= r < 4 for r in shifted)
        assert original_origin == 0 and shifted_origin >= 1
        corr = autocorrelation(support, N)
        shifted_corr = autocorrelation(shifted, N)
        assert corr == shifted_corr
        assert sum(corr) == len(support) ** 2
        assert corr[0] == len(support)
        # The shift-by-two control also preserves the odd-count slice labels.
        labels = Counter(q for q, _, _ in frontier)
        control_labels = Counter(q for q, _, _ in [(q, (r+2)%N, y) for q,r,y in frontier])
        assert labels == control_labels
        rows.append({
            'depth': j, 'modulus': N, 'live_words': len(support),
            'origin_window': [1, 4], 'actual_origin_count': original_origin,
            'translated_control_origin_count': shifted_origin,
            'all_fourier_power_coefficients_equal_via_autocorrelation': True,
            'autocorrelation_sha256': hashlib.sha256(','.join(map(str,corr)).encode()).hexdigest()
        })
    return rows


def certify() -> dict:
    parent_path = Path(__file__).with_name('collatz_live_origin_bridge_v1.py')
    assert hashlib.sha256(parent_path.read_bytes()).hexdigest() == LIVE_PARENT_SHA256
    small = symbolic_controls()
    depth, X = 333, 512
    qmin, F, _ = language_counts(depth)

    # Independently traverse the legal-prefix DP backwards from its root.
    @lru_cache(maxsize=None)
    def completions(k: int, q: int) -> int:
        if q < qmin[k]:
            return 0
        if k == depth:
            return 1
        return completions(k + 1, q) + completions(k + 1, q + 1)

    assert completions(0, 0) == F[depth]
    expected = 260078867390036221398561220601054468654692164639803459182799561454442032878319722731506262999
    assert F[depth] == expected
    # U = 2 * 2^(6j/125) * F_j * X / 2^j. Check U<1 by raising to 125.
    lhs = 2 ** (125 * depth)
    rhs = 2 ** (125 + 6 * depth) * (F[depth] * X) ** 125
    assert rhs < lhs
    assert all(2 ** (125*k) <= 2 ** (125+6*k)*(F[k]*X)**125
               for k in range(60, depth))
    sources = list(range(1, X, 2))
    crossings = [first_crossing(n, depth) for n in sources]
    assert all(k is not None for k in crossings)
    # Explicit actual support witness, with no numerical approximation.
    n = (1 << depth) - 1
    y, p3 = n, 1
    for k in range(1, depth + 1):
        assert y % 2 == 1
        y = (3*y + 1) // 2
        p3 *= 3
        assert y + 1 == p3 * (1 << (depth-k))
        assert p3 >= 1 << k
    assert (n + 2) % (1 << depth) == 1
    # Thus actual support is nonempty but actual origin count is zero;
    # its translated control has a point at 1 and the same Fourier magnitudes.
    return {
        'schema': 'COLLATZ_ORIGIN_PHASE_BARRIER_V1', 'parent_state_head': PARENT,
        'global_collatz': 'UNKNOWN',
        'status': 'EXACT_OBSTRUCTION_TO_TRANSLATION_UNIFORM_PHASE_BLIND_CLOSURE',
        'fixed_origin_candidate': 'UNKNOWN_NOT_REFUTED',
        'generic_theorem': 'Every uniform upper bound for counts in all nonempty cyclic windows of a nonempty support is at least one.',
        'fourier_consequence': 'A full absolute-value Fourier inversion majorant is translation uniform and cannot prove an origin count <1, even with exact Fourier magnitudes.',
        'deep_witness': {
            'depth': depth, 'window_X': X, 'window_width': X-1,
            'live_count': str(F[depth]), 'independent_backward_dp_states': completions.cache_info().currsize,
            'actual_origin_count': 0, 'odd_origin_sources_checked': len(sources),
            'largest_origin_source_first_crossing': max(crossings),
            'actual_nonempty_support_source': '2^333-1',
            'control_shift': 2, 'translated_control_source': 1,
            'translated_control_origin_count_lower_bound': 1,
            'target_K': 2, 'target_eta': '6/125',
            'exact_125th_power_subunit_check': True,
            'first_subunit_depth_for_X512_checked_from': 60,
            'first_subunit_depth_for_X512': depth,
            'shifted_control_is_collatz_language': 'NOT_ASSERTED'
        },
        'small_exact_controls': small,
        'verification_boundary': 'Integer Python computation; full autocorrelation equality through depth16; two DP directions at depth333; Lean generic cyclic-window barrier and all-odd family require the separate hosted qualification. Fourier translation formula and application are a written elementary argument, not Lean complex analysis.',
        'not_proved': ['universal fixed-origin anti-concentration', 'canonical M-negativity at unbounded depths', 'absence of positive never-crossing sources'],
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    }


if __name__ == '__main__':
    print(json.dumps(certify(), indent=2, sort_keys=True))
