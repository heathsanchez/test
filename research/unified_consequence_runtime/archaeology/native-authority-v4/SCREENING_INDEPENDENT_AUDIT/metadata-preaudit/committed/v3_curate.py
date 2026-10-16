"""Metadata-only frontier curation after a committed, qualified admission gate.

No query runs on import or while writing the prequery.  The original metadata
curator supplies its scanner, classifications and commit/tree binding unchanged.
This extension fixes the source universe, retains every screening candidate, and
requires actual Git commitment before claiming that any prequery was committed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import time
import types
from typing import Any

UNIVERSE = (
    'davidhalter/parso',
    'grantjenks/python-sortedcontainers',
    'jd/tenacity',
    'keleshev/schema',
    'mahmoud/boltons',
    'mverleg/pyjson_tricks',
    'python-humanize/humanize',
    'tartley/colorama',
    'tkem/cachetools',
)
ORIGINAL_PATH = 'archaeology/native-frontier-v2/curate_metadata.py'
ORIGINAL_SHA256 = 'b2885099eb904395cb297ba17a0c3f1270975061b24d46ac5742a07804b8e251'
EXTRA_HISTORY = (
    'archaeology/native-frontier-v2/PREQUERY.json',
    'archaeology/native-frontier-v2/FRESH_TASK_METADATA.json',
)
SCHEMA = 'UDM_NATIVE_ENVIRONMENT_V3_METADATA_PREQUERY_V1'
METADATA_SECONDS = 900
SCREENING_BUDGET = {
    'maximum_cases': 9,
    'maximum_native_executions_per_case': 2,
    'collection_seconds_per_call': 60,
    'execution_seconds_per_call': 600,
    'total_screening_wall_seconds': 7200,
    'native_and_independent_verification_costs_charged': True,
    'all_refusals_and_partial_costs_retained': True,
}
_LOADED_SHA256 = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_once(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def original(research: pathlib.Path):
    path = research / ORIGINAL_PATH
    if path.is_symlink() or sha256(path.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError('original metadata curator source differs')
    spec = importlib.util.spec_from_file_location('_udm_v3_original_metadata_curator', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def rebound(function, namespace):
    result = types.FunctionType(function.__code__, namespace, function.__name__,
                                function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def exclusions(research: pathlib.Path, old):
    namespace = dict(old.__dict__, RESEARCH=research,
                     HISTORICAL_METADATA=(*old.HISTORICAL_METADATA, *EXTRA_HISTORY))
    evidence, inputs = rebound(old.historical_exclusions, namespace)()
    prefix = str(research) + '/'
    # Portable receipts retain the same exact historic file hashes and evidence.
    for row in inputs:
        row['path'] = row['path'].removeprefix(prefix)
    return {repo: [path.removeprefix(prefix) for path in paths]
            for repo, paths in sorted(evidence.items())}, inputs


def plan(research: pathlib.Path) -> dict[str, Any]:
    old = original(research)
    touched, inputs = exclusions(research, old)
    return {
        'schema': SCHEMA,
        'state': 'PREQUERY_PREPARED_NO_QUERIES',
        'curation_code_sha256': sha256(pathlib.Path(__file__).read_bytes()),
        'original_curator': {'path': ORIGINAL_PATH, 'sha256': ORIGINAL_SHA256},
        'repository_universe_fixed_before_github_queries': list(UNIVERSE),
        'universe_order': 'Ascending lexicographic full name; no expansion on shortfall.',
        'requested_roles': 2,
        'role_assignment_after_independent_admission': ['TRAINING', 'PROTECTED_FUTURE_1'],
        'metadata_seconds': METADATA_SECONDS,
        'screening_budget': SCREENING_BUDGET,
        'selection_algorithm': (
            'Inspect the latest at most 100 closed PRs per nonexcluded repository, '
            'page=1, per_page=100, sort=updated, direction=desc. Retain every PR '
            'and fixed-predicate reason. Take the first qualifying PR per repository '
            'in returned order. Bind every chosen base/head commit and changed blob '
            'using Git metadata only, retaining any binding failure without retargeting. '
            'The complete resulting pool, in fixed repository order, is committed '
            'before independent admission screening. Screen every pool member; choose '
            'the first two source-distinct admitted members. Native PASS and FAIL '
            'are identical for eligibility and remain sealed from the learner. '
            'If the selected training case has no failing native residual, stop G2 '
            'UNKNOWN; do not replace it.'),
        'metadata_predicates': {
            'merged': True,
            'title_or_label': 'Case-insensitive title starts fix OR a label contains bug.',
            'production_py_files_min': 1,
            'test_py_files_min': 1,
            'production_total_deletions_inclusive': [1, 4],
            'production_total_additions_max': 6,
            'production_changed_status': 'Every production .py file is modified, hence preexisting.',
            'no_changed_file_renamed_or_removed': True,
            'tests_classifier': 'Original v2 is_test: .py plus test/tests/testing component, test_ basename, _test.py suffix, or conftest.py.',
            'file_metadata_pagination': 'Original v2 scan: per_page=100 until fewer than 100; refusal if 3000-file API ceiling is not closed.',
        },
        'historical_metadata_inputs': inputs,
        'historically_touched_repository_exclusions': touched,
        'untouched_assessment': {
            'basis': 'Exact frozen historical metadata, both prior frontier universes and selected tasks, and original known native-domain identifier.',
            'boundary': 'Bounded accessible-record unfamiliarity only; no claim about all prior human/model knowledge or all inaccessible research.',
        },
        'api_allowlist': {
            'closed_pr_list': old.PR_FIELDS,
            'changed_file_pages': old.FILE_FIELDS,
            'git_commit_metadata': old.COMMIT_FIELDS,
            'git_tree_metadata': old.TREE_FIELDS,
        },
        'exposure_boundary': {
            'target_source_read': False, 'test_contents_read': False,
            'production_patches_read': False, 'pr_bodies_read': False,
            'ci_results_read': False, 'outcomes_read': False,
            'native_execution': False, 'git_fetch_or_clone': False,
            'raw_patch_or_body_persisted': False,
            'projection': 'Original gh api --jq allowed fields only; never contents/blob/raw endpoints, PR bodies, patches, CI or commit messages.',
        },
        'commitment_rule': 'A separate PREQUERY_EXECUTION.json may claim commitment only after exact plan and code bytes are verified against an existing Git commit before any target query.',
        'scientific_verdict': 'NONE_METADATA_AND_ADMISSION_SCREENING_CANNOT_ESTABLISH_G2_G3_OR_G4',
    }


def committed(root: pathlib.Path, path: pathlib.Path) -> dict[str, str]:
    resolved = path.resolve()
    if path.is_symlink() or not resolved.is_relative_to(root):
        raise ValueError('committed input must be an ordinary in-repository file')
    relative = resolved.relative_to(root).as_posix()
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    data = subprocess.check_output(['git', '-C', str(root), 'show', f'{head}:{relative}'])
    if data != path.read_bytes():
        raise ValueError('working bytes differ from committed input: ' + relative)
    return {'path': relative, 'sha256': sha256(data), 'source_commit': head}


def metadata_api(old, deadline):
    allowed = (
        (re.compile(r'repos/[^/]+/[^/]+/pulls\?state=closed&sort=updated&direction=desc&per_page=100&page=1'), old.PR_FIELDS),
        (re.compile(r'repos/[^/]+/[^/]+/pulls/[1-9][0-9]*/files\?per_page=100&page=[1-9][0-9]*'), old.FILE_FIELDS),
        (re.compile(r'repos/[^/]+/[^/]+/git/commits/[0-9a-f]{40}'), old.COMMIT_FIELDS),
        (re.compile(r'repos/[^/]+/[^/]+/git/trees/[0-9a-f]{40}\?recursive=1'), old.TREE_FIELDS),
    )

    def gh(endpoint, projection, coverage):
        if not any(pattern.fullmatch(endpoint) and projection == fields for pattern, fields in allowed):
            raise RuntimeError('REFUSED_NONALLOWLIST_METADATA_QUERY')
        repo = '/'.join(endpoint.split('/')[1:3])
        if repo not in UNIVERSE:
            raise RuntimeError('REFUSED_REPOSITORY_OUTSIDE_FROZEN_UNIVERSE')
        remaining = deadline - time.monotonic()
        record = {'endpoint': endpoint, 'projection': projection, 'requested_at_utc': old.now()}
        coverage.append(record)
        if remaining <= 0:
            record.update(status='METADATA_BUDGET_EXHAUSTED', wall_seconds=0)
            raise RuntimeError('METADATA_BUDGET_EXHAUSTED')
        started = time.monotonic()
        try:
            proc = subprocess.run(['gh', 'api', endpoint, '--jq', projection], text=True,
                                  capture_output=True, timeout=min(60, remaining))
        except subprocess.TimeoutExpired:
            record.update(status='METADATA_API_TIMEOUT', wall_seconds=time.monotonic()-started)
            raise RuntimeError('METADATA_API_TIMEOUT') from None
        record.update(returncode=proc.returncode, wall_seconds=time.monotonic()-started)
        if proc.returncode:
            status = re.search(r'HTTP (\d{3})', proc.stderr)
            record['status'] = 'API_ERROR'
            if status:
                record['http_status'] = int(status.group(1))
            raise RuntimeError('GITHUB_METADATA_API_ERROR' + (f'_HTTP_{status.group(1)}' if status else ''))
        try:
            value = json.loads(proc.stdout)
        except json.JSONDecodeError:
            record['status'] = 'INVALID_PROJECTED_METADATA_JSON'
            raise RuntimeError('INVALID_PROJECTED_METADATA_JSON') from None
        record['status'] = 'OK'
        if isinstance(value, list):
            record['entries_returned'] = len(value)
        return value
    return gh


def filter_existing_production(result, old):
    for candidate in result.get('candidates', []):
        if not candidate['reasons']:
            production = [row for row in candidate['files']
                          if row['filename'].endswith('.py') and not old.is_test(row['filename'])]
            if any(row['status'] != 'modified' for row in production):
                candidate['reasons'].append('PRODUCTION_PY_NOT_ALL_PREEXISTING_MODIFIED')
                candidate['status'] = 'REJECTED_METADATA_PREDICATES'
        candidate.pop('selection_disposition', None)
    if result['status'] in ('QUALIFYING_METADATA_CANDIDATE', 'NO_QUALIFYING_CANDIDATE'):
        qualifiers = [row for row in result['candidates'] if not row['reasons']]
        result['status'] = 'QUALIFYING_METADATA_CANDIDATE' if qualifiers else 'NO_QUALIFYING_CANDIDATE'
        result['qualifying_prs'] = [row['number'] for row in qualifiers]
        result.pop('first_qualifying_pr', None)
        if qualifiers:
            result['first_qualifying_pr'] = qualifiers[0]['number']
            for candidate in qualifiers[1:]:
                candidate['selection_disposition'] = 'NOT_FIRST_ELIGIBLE_PR_IN_FIXED_ORDER'
    return result


def query(research, plan_path, gate_path, artifact_path, out):
    outer_started = time.monotonic()
    root = research.parents[1]
    if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']).strip():
        raise ValueError('commit the complete research worktree before any target query')
    prepared = json.loads(plan_path.read_text())
    if prepared != plan(research):
        raise ValueError('prequery differs from exact code, historical inputs or fixed rules')
    code_record = committed(root, pathlib.Path(__file__))
    if code_record['sha256'] != _LOADED_SHA256:
        raise ValueError('loaded curator differs from committed source')
    plan_record = committed(root, plan_path)
    gate_record = committed(root, gate_path)
    gate = json.loads(gate_path.read_text())
    if set(gate) != {'environment_gate', 'catalog'}:
        raise ValueError('qualified gate descriptor must contain environment_gate and catalog')
    if sha256(artifact_path.read_bytes()) != gate['environment_gate']['artifact_sha256']:
        raise ValueError('archived qualification artifact digest differs')
    sys.path.insert(0, str(root))
    from research.unified_consequence_runtime.qualify_native_frontier_v3 import require_environment_gate
    verified_gate = require_environment_gate(gate)
    out.mkdir(parents=True, exist_ok=True)
    names = ('PREQUERY_EXECUTION.json', 'METADATA_CURATION.json', 'FROZEN_POOL.json')
    if any((out/name).exists() for name in names):
        raise ValueError('preserve the first query/receipt/pool; refusing replacement')
    old = original(research)
    started = time.monotonic()
    receipt = {
        'schema': 'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V3',
        'state': 'PREQUERY_COMMITTED_BEFORE_QUERIES',
        'source_commit': code_record['source_commit'],
        'plan': plan_record, 'code': code_record, 'gate_descriptor': gate_record,
        'environment_gate': verified_gate,
        'archive_sha256': sha256(artifact_path.read_bytes()),
        'committed_bytes_verified_at_utc': old.now(),
        'target_query_count_before_receipt': 0,
        'repository_universe_fixed_before_github_queries': list(UNIVERSE),
        'requested_roles': prepared['requested_roles'],
        'screening_budget': prepared['screening_budget'],
    }
    write_once(out/names[0], receipt)
    deadline = started + METADATA_SECONDS
    namespace = dict(old.__dict__, gh=metadata_api(old, deadline))
    scan = rebound(old.scan, namespace)
    bind = rebound(old.bind_tree_metadata, namespace)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {repo: pool.submit(scan, repo, prepared['historically_touched_repository_exclusions'])
                   for repo in UNIVERSE}
        for repo in UNIVERSE:
            results.append(filter_existing_production(pending[repo].result(), old))
    selected = []
    for result in results:
        if result['status'] != 'QUALIFYING_METADATA_CANDIDATE':
            continue
        first = next(row for row in result['candidates'] if not row['reasons'])
        first['selection_disposition'] = 'FIRST_METADATA_ELIGIBLE_IN_FROZEN_REPOSITORY_ORDER'
        candidate = {
            'repo': result['repo'], 'pr': first['number'], 'metadata_url': first['url'],
            'base_commit': first['base']['sha'], 'head_commit': first['head']['sha'],
            'merge_commit_sha': first['merge_commit_sha'], 'files': first['files'],
            'metadata_stats': first['metadata_stats'],
            'selection_status': 'FROZEN_ORDERED_POOL_CANDIDATE_NOT_AN_ADMITTED_TASK',
        }
        try:
            bind(candidate)
        except RuntimeError as error:
            candidate.update(metadata_binding_status='BINDING_ERROR_SELECTION_NOT_RETARGETED',
                             metadata_binding_error=str(error))
        selected.append(candidate)
    report = {
        'schema': 'UDM_NATIVE_FRONTIER_METADATA_CURATION_V3',
        'state': 'METADATA_ONLY_NO_SOURCE_OR_NATIVE_OUTCOMES_ACCESSED',
        'prequery_execution_sha256': sha256((out/names[0]).read_bytes()),
        'prequery_plan_sha256': sha256(plan_path.read_bytes()),
        'repositories': results, 'pool': selected,
        'costs': {'metadata_wall_seconds': time.monotonic()-started,
                  'total_curation_wall_seconds': time.monotonic()-outer_started,
                  'metadata_api_calls': sum(len(row.get('query_coverage', [])) for row in results)
                    + sum(len(row.get('tree_query_coverage', [])) for row in selected),
                  'metadata_budget_seconds': METADATA_SECONDS,
                  'native_calls': 0, 'collection_calls': 0},
        'selection_shortfall_before_admission': max(0, 2-len(selected)),
        'scientific_verdict': 'NONE_METADATA_CURATION_IS_NOT_DEVELOPMENTAL_EVIDENCE',
    }
    write_once(out/names[1], report)
    write_once(out/names[2], {
        'schema': 'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V3',
        'state': 'MUST_COMMIT_BEFORE_ADMISSION_SCREENING',
        'prequery_execution_sha256': sha256((out/names[0]).read_bytes()),
        'metadata_curation_sha256': sha256((out/names[1]).read_bytes()),
        'pool': selected,
        'requested_roles': prepared['requested_roles'],
        'screening_budget': prepared['screening_budget'],
        'selection_rule': 'First two source-distinct independent native admissions; PASS and FAIL identical; do not replace a passing training task.',
    })
    return {'out': str(out), 'pool_size': len(selected),
            'artifacts': {name: sha256((out/name).read_bytes()) for name in names},
            'scientific_verdict': report['scientific_verdict']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research-root', type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[2])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write-prequery', type=pathlib.Path)
    mode.add_argument('--query-after-committed-prequery', type=pathlib.Path)
    parser.add_argument('--environment-gate', type=pathlib.Path)
    parser.add_argument('--qualification-artifact', type=pathlib.Path)
    parser.add_argument('--out', type=pathlib.Path)
    args = parser.parse_args()
    research = args.research_root.resolve()
    if args.write_prequery:
        write_once(args.write_prequery, plan(research))
        result = {'path': str(args.write_prequery), 'sha256': sha256(args.write_prequery.read_bytes()),
                  'state': 'PREQUERY_PREPARED_NO_QUERIES', 'network_queries': 0}
    else:
        if not all((args.environment_gate, args.qualification_artifact, args.out)):
            parser.error('query requires --environment-gate, --qualification-artifact and --out')
        result = query(research, args.query_after_committed_prequery.resolve(),
                       args.environment_gate.resolve(), args.qualification_artifact.resolve(), args.out.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
