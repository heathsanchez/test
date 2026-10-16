#!/usr/bin/env python3
"""Once-only V4.1 independent admission runner; metadata in, envelopes out."""
import argparse
import hashlib
import json
import os
import resource
from pathlib import Path
import subprocess
import sys
import time


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, sort_keys=True, separators=(',', ':'))
        handle.write('\n')


def canonical_path(raw):
    path = Path(raw)
    if not path.is_absolute() or path.resolve() != path or path.is_symlink():
        raise ValueError('absolute canonical path required: ' + str(path))
    return path


def index_path(repo):
    dotgit = repo / '.git'
    if dotgit.is_dir():
        directory = dotgit
    elif dotgit.is_file():
        pointer = dotgit.read_text().strip()
        if not pointer.startswith('gitdir: '):
            raise ValueError('unsupported .git pointer')
        directory = Path(pointer[8:])
        if not directory.is_absolute():
            directory = repo / directory
        directory = directory.resolve()
    else:
        raise ValueError('repository Git metadata unavailable')
    path = directory / 'index'
    if not path.is_file():
        raise ValueError('raw repository Git index unavailable')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--authority', required=True)
    parser.add_argument('--authority-sha256', required=True)
    parser.add_argument('--requests', required=True)
    parser.add_argument('--count', required=True, type=int)
    parser.add_argument('--output-root', required=True)
    parser.add_argument('--runtimes', required=True)
    parser.add_argument('--controller-python', default=sys.executable)
    args = parser.parse_args()
    runner = Path(__file__).resolve().parent
    repo = canonical_path(args.repo)
    authority = canonical_path(args.authority)
    requests = canonical_path(args.requests)
    output_root = canonical_path(args.output_root)
    runtimes = canonical_path(args.runtimes)
    if (len(args.authority_sha256) != 64
            or any(c not in '0123456789abcdef' for c in args.authority_sha256)
            or sha(authority.read_bytes()) != args.authority_sha256):
        raise ValueError('root-supplied immutable authority SHA256 differs')
    if args.count <= 0 or output_root.exists():
        raise ValueError('positive complete pool size and wholly new output root required')
    expected_requests = [requests / ('request-%03d.json' % index) for index in range(args.count)]
    if set(requests.glob('request-*.json')) != set(expected_requests):
        raise ValueError('requests must be the exact complete ordered pool')
    for path in expected_requests:
        if not path.is_file() or path.is_symlink():
            raise ValueError('canonical existing request required')
    if 'GIT_INDEX_FILE' in os.environ:
        raise ValueError('unexpected inherited alternate Git index')
    ledger_path = runner / 'RUN_LEDGER.json'
    summary_path = runner / 'PUBLIC_SCREENING_SUMMARY.json'
    before_path = runner / 'GIT_INDEX_BEFORE.bin'
    after_path = runner / 'GIT_INDEX_AFTER.bin'
    index_audit_path = runner / 'GIT_INDEX_AUDIT.json'
    outputs = [ledger_path, summary_path, before_path, after_path, index_audit_path]
    outputs += [runner / ('case-%03d.controller.log' % index) for index in range(args.count)]
    if any(path.exists() for path in outputs):
        raise ValueError('refusing existing runner outputs; no retry or rescreen is permitted')
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')
    raw_index_path = index_path(repo)
    before = raw_index_path.read_bytes()
    with before_path.open('xb') as handle:
        handle.write(before)
    ledger = {
        'schema': 'UDM_V41_INDEPENDENT_ONCE_ONLY_RUNNER_LEDGER',
        'started_at_unix': time.time(), 'repo': str(repo),
        'authority': {'path': str(authority), 'sha256': args.authority_sha256},
        'runtimes': {'path': str(runtimes), 'sha256': sha(runtimes.read_bytes())},
        'requests': [{'path': str(path), 'sha256': sha(path.read_bytes())} for path in expected_requests],
        'count': args.count, 'output_root': str(output_root),
        'raw_git_index': str(raw_index_path), 'raw_git_index_before_sha256': sha(before),
        'no_retries_or_rescreens': True,
    }
    committed_head = subprocess.check_output(
        ['git', '--no-replace-objects', '-C', str(repo), 'rev-parse', 'HEAD'],
        env=env, text=True, stderr=subprocess.PIPE).strip()
    if not committed_head.startswith('bd46699e'):
        raise ValueError('root-authorized committed source differs')
    ledger['committed_head'] = committed_head
    write_new(ledger_path, ledger)
    public = {
        'schema': 'UDM_V41_INDEPENDENT_PUBLIC_SCREENING_SUMMARY',
        'authority': ledger['authority'], 'pool_size': args.count,
        'cases': [], 'all_pool_members_attempted_once': False,
        'search_or_policy_outcomes_accessed': False,
        'learner_future_source_accessed': False,
    }
    try:
        for index, request in enumerate(expected_requests):
            destination = output_root / ('case-%03d' % index)
            command = [args.controller_python, '-B', '-m',
                'research.unified_consequence_runtime.qualify_native_frontier_v41',
                '--screen-spec', str(request), '--authority', str(authority),
                '--authority-sha256', args.authority_sha256,
                '--runtimes', str(runtimes), '--out', str(destination)]
            started = time.monotonic()
            usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
            with (runner / ('case-%03d.controller.log' % index)).open('xb') as log:
                result = subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
            usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
            envelope_path = destination / 'SCREENING_ENVELOPE.json'
            row = {'index': index, 'controller_returncode': result.returncode,
                   'controller_wall_seconds': time.monotonic() - started,
                   'child_user_cpu_seconds': usage_after.ru_utime - usage_before.ru_utime,
                   'child_system_cpu_seconds': usage_after.ru_stime - usage_before.ru_stime,
                   'child_maxrss_kib_lifetime_nonadditive': usage_after.ru_maxrss,
                   'raw_directory': str(destination),
                   'controller_log': str(runner / ('case-%03d.controller.log' % index))}
            if envelope_path.is_file():
                raw = envelope_path.read_bytes()
                envelope = json.loads(raw)
                allowed = {'schema', 'repository', 'spec_sha256', 'status', 'eligible',
                           'screening_mode', 'sealed_report', 'costs', 'total_wall_seconds'}
                if set(envelope) != allowed:
                    raise ValueError('public envelope contains unexpected fields')
                row.update(envelope=envelope, envelope_path=str(envelope_path), envelope_sha256=sha(raw))
            else:
                row.update(status='UNKNOWN_NO_PUBLIC_ENVELOPE', all_raw_costs_retained=True)
            public['cases'].append(row)
            print(json.dumps({'index': index, 'returncode': result.returncode,
                              'public_status': row.get('envelope', {}).get('status', row.get('status'))},
                             sort_keys=True), flush=True)
        public['all_pool_members_attempted_once'] = True
        meter_path = output_root / 'SCREENING_METER.json'
        if meter_path.is_file():
            meter_raw = meter_path.read_bytes()
            meter = json.loads(meter_raw)
            public['meter'] = {
                'path': str(meter_path), 'sha256': sha(meter_raw),
                'cases': len(meter.get('cases', [])), 'pending': meter.get('pending'),
                'native_calls': meter.get('native_calls'),
                'collection_calls': meter.get('collection_calls'),
                'accounting_complete': meter.get('accounting_complete'),
                'source_commit': meter.get('source_commit'),
            }
        public['sum_case_wall_seconds'] = sum(row.get('envelope', {}).get('total_wall_seconds', 0)
                                              for row in public['cases'])
    finally:
        after = raw_index_path.read_bytes()
        with after_path.open('xb') as handle:
            handle.write(after)
        audit = {'schema': 'UDM_RAW_GIT_INDEX_FILESYSTEM_AUDIT',
                 'index_path': str(raw_index_path),
                 'before_path': str(before_path), 'after_path': str(after_path),
                 'before_sha256': sha(before), 'after_sha256': sha(after),
                 'byte_identical': before == after,
                 'copied_via_pure_filesystem': True, 'reset_or_restore_used': False}
        write_new(index_audit_path, audit)
        public['raw_git_index_audit'] = audit
        public['finished_at_unix'] = time.time()
        write_new(summary_path, public)
    print(json.dumps({'summary_path': str(summary_path),
                      'all_pool_members_attempted_once': public['all_pool_members_attempted_once'],
                      'raw_git_index_byte_identical': public['raw_git_index_audit']['byte_identical']},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
