"""Harness-only: fail-closed original-Go-test qualification for sealed V5.

No source-specific repairs or new constructor code; this script cannot promote
G2, G3, a new mathematical theorem, or owner effect authority.
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'g3_constructor_v5'))
from execute import run_target


def original_suite_receipt(test_events: str, exit_code: int) -> dict:
    passed = set()
    failed = set()
    parse_errors = 0
    for line in test_events.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            parse_errors += 1
            continue
        if not isinstance(row, dict):
            parse_errors += 1
            continue
        name = row.get('Test')
        pkg = row.get('Package')
        if isinstance(name, str) and isinstance(pkg, str) and name:
            pair = (pkg, name)
            if row.get('Action') == 'pass':
                passed.add(pair)
            if row.get('Action') == 'fail':
                failed.add(pair)
    n = len(passed)
    if exit_code != 0 or failed:
        status = 'UNKNOWN_ORIGINAL_TEST_FAILURE'
    elif parse_errors:
        status = 'UNKNOWN_TEST_EVENT_STREAM'
    elif n == 0:
        status = 'UNKNOWN_ZERO_RECOGNIZED_TESTS'
    else:
        status = 'ORIGINAL_SUITE_PASS_NONEMPTY'
    return {'status': status, 'exit_code': exit_code, 'recognized_passes': n,
            'failed_tests': len(failed), 'malformed_events': parse_errors}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--sha', required=True)
    ap.add_argument('--native-events', type=Path, required=True)
    ap.add_argument('--native-exit', type=int, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    suite = original_suite_receipt(args.native_events.read_text(), args.native_exit)
    native = run_target(args.source, args.sha, args.output/'v5', repo_name=args.repo)
    scientific = ('WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY'
                  if suite['status']=='ORIGINAL_SUITE_PASS_NONEMPTY' and
                     native['status']=='WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY'
                  else 'UNKNOWN_SOURCE_NATIVE_ADMISSION')
    receipt = {'schema':'mathgraph.g3.v5.independent-qualification.v1',
               'repo': args.repo, 'source_sha':args.sha,
               'original_suite':suite, 'native':native,
               'qualification':scientific,
               'strict_g3':'UNKNOWN', 'fair_equal_info_comparator':'NOT_TESTED'}
    path=args.output/'qualification.json'
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('SCIENTIFIC_QUALIFICATION',scientific)
    print('ORIGINAL_SUITE',suite['status'],'tests',suite['recognized_passes'])
    print('NATIVE',native['status'])
    # The workflow distinguishes infrastructure execution from science. A valid
    # UNKNOWN is an observed outcome, not an Actions failure.
    if native.get('source_sha_confirmed') is not True:
        print('SOURCE_IDENTITY_NOT_QUALIFIED',file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
