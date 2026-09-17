#!/usr/bin/env python3
"""Exact bounded first-crossing certificate. NOT a global Collatz proof.

For a first coefficient crossing with Q odd steps, L=bit_length(3**Q).
The additive numerator is at most
  H_Q = sum(3**(Q-j) * 2**floor(log2(3**(j-1))), j=1..Q).
Thus any failure of descent at this crossing requires
  2 <= n <= floor(H_Q / (2**L-3**Q)).
All sources above the maximum such window are handled by this inequality.
Only the finite exception window is replayed below. Neither the existence of
an eventual coefficient crossing nor the case of an unbounded Q is assumed.
"""
from __future__ import annotations
import argparse
import json


def certificate(odd_cap: int, source_limit: int = 6_000_000) -> dict:
    if type(odd_cap) is not int or not 1 <= odd_cap <= 10_000:
        raise ValueError('odd_cap must be between 1 and 10000')
    A, H = 1, 0
    bits = [1]
    maximum, maximizing_Q = 0, 0
    for q in range(1, odd_cap+1):
        H = 3*H + (1 << (A.bit_length()-1))
        A *= 3
        length = A.bit_length()
        bits.append(length)
        bound = H // ((1 << length)-A)
        if bound > maximum:
            maximum, maximizing_Q = bound, q
    if maximum > source_limit:
        raise ValueError('exact source window exceeds the explicit resource cap')
    crossed = outside = steps = max_time = max_odds = max_seed = peak = 0
    horizon = bits[-1]
    for n in range(2, maximum+1):
        x, odds = n, 0
        for j in range(1, horizon+1):
            if x & 1:
                x = (3*x+1)//2
                odds += 1
            else:
                x //= 2
            steps += 1
            if x > peak:
                peak = x
            if odds > odd_cap:
                outside += 1
                break
            if bits[odds] <= j:
                if x >= n:
                    raise AssertionError({'source': n, 'first_crossing': j,
                                          'odds': odds, 'endpoint': x})
                crossed += 1
                if j > max_time:
                    max_time, max_seed = j, n
                max_odds = max(max_odds, odds)
                break
        else:
            outside += 1
    return {
        'status': 'CONDITIONAL_FIRST_CROSSING_VERIFIED',
        'odd_count_cap': odd_cap,
        'source_window_max': maximum,
        'maximizing_envelope_Q': maximizing_Q,
        'step_cap': horizon,
        'checked_sources': max(0, maximum-1),
        'crossed_and_descended': crossed,
        'outside_event_window': outside,
        'scalar_steps': steps,
        'maximum_observed_first_crossing': max_time,
        'maximizing_source': max_seed,
        'maximum_observed_odd_count': max_odds,
        'maximum_replayed_value': str(peak),
        'counterexamples': 0,
        'first_crossing_existence_proved': False,
        'global_collatz_proof': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--odd-cap', type=int, default=10000)
    parser.add_argument('--source-limit', type=int, default=6000000)
    args = parser.parse_args()
    print(json.dumps(certificate(args.odd_cap, args.source_limit), indent=2))
