"""Exact minimum basis for the observational quotient of three scored suites.

This is a finite, in-sample certificate. It preserves equivalence classes of
the 55 supplied implementations under 144 observed tests, not the unknown
behavior of other programs or previously unseen inputs.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
import sys
import zipfile

from mathgraph_check_basis_certificate import MODES, TASK, calculate


def certify(archive: bytes) -> dict:
    # Validates the upstream evidence hashes, reference correctness, number of
    # mutants and minimum reference-versus-mutant detection claim first.
    detection = calculate(archive)
    test_kills: dict[str, set[str]] = {}
    with zipfile.ZipFile(__import__('io').BytesIO(archive)) as z:
        sources = {
            mode: json.loads(z.read(f'{mode}/{TASK}/{TASK}.test_eval.json'))
            for mode in MODES
        }
    all_mutants: set[str] = set()
    for doc in sources.values():
        for binary in doc['binary_results']:
            if binary['role'] == 'ground_truth':
                continue
            mutant = binary['binary_id']
            all_mutants.add(mutant)
            for test in binary['test_results']:
                if test['status'] != 'passed':
                    test_kills.setdefault(test['name'], set()).add(mutant)

    mutants = sorted(all_mutants)
    assert len(mutants) == 54
    mutant_bit = {mutant: 1 << i for i, mutant in enumerate(mutants)}
    representative: dict[int, str] = {}
    for name, kills in test_kills.items():
        row = sum(mutant_bit[mutant] for mutant in kills)
        if row and (row not in representative or name < representative[row]):
            representative[row] = name
    rows = sorted(representative)
    assert len(rows) == 20

    # -1 identifies the passing reference, whose failure profile is all-zero.
    representatives = [-1, *range(len(mutants))]
    profiles = [tuple((row >> j) & 1 if j >= 0 else 0 for row in rows)
                for j in representatives]
    classes: dict[tuple[int, ...], list[str]] = {}
    for index, fingerprint in zip(representatives, profiles):
        classes.setdefault(fingerprint, []).append('reference' if index == -1 else mutants[index])
    assert len(classes) == 17

    # Only pairs separated by some original test are eligible obligations.
    pairs = [(a, b) for a in representatives for b in representatives
             if a < b and any(((row >> a) & 1 if a >= 0 else 0)
                              != ((row >> b) & 1 if b >= 0 else 0) for row in rows)]
    assert len(pairs) == 852
    pair_coverage = {
        row: sum(1 << i for i, (a, b) in enumerate(pairs)
                 if (((row >> a) & 1) if a >= 0 else 0)
                 != (((row >> b) & 1) if b >= 0 else 0))
        for row in rows
    }
    full = (1 << len(pairs)) - 1

    def covers(subset: tuple[int, ...]) -> bool:
        acc = 0
        for row in subset:
            acc |= pair_coverage[row]
        return acc == full

    # Exact lower bound: enumerate every candidate subset of <12 distinct
    # vectors. Duplicate rows cannot improve any smaller solution.
    checked = 0
    for size in range(12):
        for subset in itertools.combinations(rows, size):
            checked += 1
            if covers(subset):
                raise AssertionError(f'found size-{size} pairwise cover')
    assert checked == sum(math.comb(20, k) for k in range(12)) == 784626

    witness = next((subset for subset in itertools.combinations(rows, 12)
                    if covers(subset)), None)
    assert witness is not None
    assert len(witness) == 12 and covers(witness)

    # This is stronger than preserving reference-vs-mutant detections: the
    # selected probes preserve every original observable equivalence class.
    new_profiles = {tuple((row >> j) & 1 if j >= 0 else 0 for row in witness)
                    for j in representatives}
    assert len(new_profiles) == len(classes) == 17

    selected = detection['selected_tests']
    detection_names = {item['name'] for item in selected}
    row_by_name = {name: row for row, name in representative.items()}
    assert len(detection_names) == 11 and detection_names <= set(row_by_name)
    classes_under_detection_only = len({
        tuple((row_by_name[name] >> j) & 1 if j >= 0 else 0 for name in sorted(detection_names))
        for j in representatives
    })

    return {
        'claim': 'MINIMUM_OBSERVED_PAIRWISE_BEHAVIORAL_FINGERPRINT',
        'epistemic_status': 'WARRANTED_BOUNDED_EXHAUSTIVE_IN_SAMPLE',
        'source_actions_run_id': 40802435111,
        'source_actions_artifact_id': 12867250385,
        'source_json_sha256': detection['source_json_sha256'],
        'benchmark_commit': detection['benchmark_commit'],
        'test_count': 144,
        'mutants': 54,
        'implementations_including_reference': 55,
        'observed_behavior_classes': 17,
        'originally_distinguishable_implementation_pairs': 852,
        'distinct_nonempty_test_vectors': len(rows),
        'minimum_detection_basis': detection['minimum_basis_size'],
        'classes_preserved_by_detection_basis': classes_under_detection_only,
        'minimum_pairwise_basis': len(witness),
        'pairwise_witness_tests': [representative[row] for row in witness],
        'proof': {
            'method': 'exhaustive_strict_lower_bound_plus_constructive_witness',
            'all_subsets_smaller_than_12_checked': checked,
            'smaller_pairwise_cover_exists': False,
            'all_852_originally_distinguishable_pairs_preserved': True,
        },
        'observational_equivalence_class_sizes': sorted((len(group) for group in classes.values()), reverse=True),
        'claim_boundary': 'Only 55 given implementations, their 144 test outcomes, and the observed 17 classes; unseen behavior and implementation correctness UNKNOWN.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', help='Pinned evidence ZIP, or - for stdin')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    archive = sys.stdin.buffer.read() if args.archive == '-' else Path(args.archive).read_bytes()
    verdict = certify(archive)
    packet = json.dumps(verdict, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(packet)
    print('CERTIFIED', 'minimum_pairwise_basis', verdict['minimum_pairwise_basis'],
          'classes', verdict['observed_behavior_classes'],
          'pairs', verdict['originally_distinguishable_implementation_pairs'],
          'lower_bound_checked', verdict['proof']['all_subsets_smaller_than_12_checked'])
