#!/usr/bin/env python3
"""Bounded canonical first-crossing closure. Global Collatz remains UNKNOWN.

The two full-range prefix covers share the C++ implementation; they are not
represented as two independent implementations. Independent direct C++ and
Python checks cover the declared smaller regression domain only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from collatz_live_origin_bridge_v1 import language_counts, first_crossing


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def replay(binary: Path, out: Path, mode: str, bits: int, prefix: int) -> dict:
    data = subprocess.run([str(binary.resolve()), mode, str(bits), str(prefix), '1024'],
                          capture_output=True, text=True, check=True, timeout=300)
    result = json.loads(data.stdout)
    assert result['odd_sources_accounted'] == 2 ** (bits - 1)
    assert sum(result['first_crossing_histogram']) == 2 ** (bits - 1)
    for key in ('unresolved', 'overflow', 'nontrivial_nondescending', 'first_bad_source'):
        assert result[key] == 0, (key, result[key])
    assert result['global_collatz'] == 'UNKNOWN'
    (out / f'{mode}-{bits}-{prefix}.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def certify(binary: Path, cap_binary: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    large24 = replay(binary, out, 'prefix', 33, 24)
    large20 = replay(binary, out, 'prefix', 33, 20)
    assert large24['first_crossing_histogram'] == large20['first_crossing_histogram']
    assert large24['max_first_crossing'] == large20['max_first_crossing'] == 447
    assert large24['live_prefixes'] == 286581
    assert large20['live_prefixes'] == 27328
    assert large24['continued_sources'] == 146729472
    assert large20['continued_sources'] == 223870976
    small_direct = replay(binary, out, 'direct', 20, 16)
    small_prefix = replay(binary, out, 'prefix', 20, 12)
    assert small_direct['first_crossing_histogram'] == small_prefix['first_crossing_histogram']
    qm, _, _ = language_counts(1024)
    histogram = [0] * 1025
    for n in range(1, 2 ** 20, 2):
        crossing = first_crossing(n, qm)
        assert crossing is not None
        j, y, _ = crossing
        assert n == 1 or y < n
        histogram[j] += 1
    assert small_direct['max_first_crossing'] == 183
    assert small_direct['first_crossing_histogram'] == histogram[:184]
    assert sum(histogram[184:]) == 0
    cap_run = subprocess.run([str(cap_binary.resolve())], capture_output=True,
                             text=True, check=True, timeout=120)
    cap = json.loads(cap_run.stdout)
    assert cap == {'depth': 271782, 'types': 171476, 'max_cap': 7216089270,
                   'j': 125743, 'q': 79335, 'all_caps_below_2_pow_33': True,
                   'global_collatz': 'UNKNOWN'}
    (out / 'type-cap-replay.json').write_text(json.dumps(cap, indent=2) + '\n')
    result = {
        'schema': 'COLLATZ_BOUNDED_CANONICAL_CLOSURE_V1',
        'parent_state_head': '5242a12a17fadf50a028fde5eb7817230971e6bf',
        'status': 'EXACT_COMPUTATIONAL_BOUNDED_CLOSURE',
        'source_floor_exclusive': 2 ** 33,
        'odd_sources_accounted_in_each_cover': 2 ** 32,
        'full_cover_prefix_widths': [20, 24],
        'continued_sources_by_prefix_width': {'20': 223870976, '24': 146729472},
        'all_source_first_crossings_at_most': 447,
        'nontrivial_nondescending_sources': 0,
        'overflow_or_unresolved': 0,
        'full_histogram_sha256': digest(large24['first_crossing_histogram']),
        'independent_direct_regression_exclusive': 2 ** 20,
        'necessary_coefficient_types': 171476,
        'bounded_canonical_residual_depth_inclusive': 271782,
        'max_source_cap': 7216089270,
        'max_source_cap_type': {'j': 125743, 'q': 79335},
        'prior_qualified_type_rows_sha256': '8216be5be97304bc66f6ae6b5f94c04ed93b083768cf0ea4140642b840dfb663',
        'consequence': 'Every nontrivial legal first-crossing canonical cylinder with j<=271782 has M<0.',
        'deduction': 'M>=0 implies R<=7216089270<2^33 by the V10 elementary bound and exact type-cap replay; the source cover proves strict descent at the first crossing for every 1<R<2^33, contradiction.',
        'external_convergence_assumption': 'NONE_FOR_THIS_BOUNDED_CONSEQUENCE',
        'verification_boundary': 'Exact C++ computations with overflow rejection; two full prefix partitions share code; independent Python/direct-C++ regression is bounded to 2^20; coefficient checker replays the V10 C++ cap; the earlier Python/C++ qualification is retained rather than presented as a fresh Python large-depth replay. This finite computation is not emitted as a full Lean proof term.',
        'not_proved': ['canonical M<0 at all greater depths', 'universal live-origin estimate', 'absence of a positive never-crossing source'],
        'failed_local_attempts': ['Unaccelerated direct 2^33 scan exceeded a 120-second runtime limit and supplied no certificate; it is not counted as an independent full-range replay.', 'An initial aggregate rerun exceeded 120 seconds after the source covers, during the redundant Python large-depth cap replay; final aggregation reuses the qualified V10 C++ checker.'],
        'global_collatz': 'UNKNOWN',
        'cpp_sha256': hashlib.sha256(Path(__file__).with_suffix('.cpp').read_bytes()).hexdigest(),
        'python_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (out / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--cap-binary', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(certify(args.binary, args.cap_binary, args.out), indent=2, sort_keys=True))
