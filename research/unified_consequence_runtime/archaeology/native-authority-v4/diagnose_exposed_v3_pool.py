"""Reconcile only the seven exposed V3 static-admission cases against V4.

No head repairs, external author assertions, agent, source execution, test collection,
candidate search, native tests, or prospective claim. Sources are read as Git objects.
The raw test/source bytes are never emitted; output has bounded reason categories.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os

from research.unified_consequence_runtime import (
    native_environment_selection_v3 as old,
    native_environment_selection_v4 as new,
)

HERE = Path(__file__).resolve().parent
POOL = HERE.parent / 'native-environment-v3/FROZEN_POOL.json'
CATALOG = HERE.parent / 'native-environment-v3/ENVIRONMENT_CATALOG.json'
EXPECTED_POOL_SHA256 = 'e99dbf7ed11554561f3584cbe7216cf7f847b78364ef1cac70841bec97c08bb3'


def git(*args, cwd=None, timeout=100, input=None):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    return subprocess.run(
        ['git', *map(str, args)], cwd=cwd, env=env, input=input,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=timeout,
    ).stdout


def original_tree(repository, commit):
    if not isinstance(repository, str) or not all(
            part and all(c.isalnum() or c in '._-' for c in part)
            for part in repository.split('/')) or len(repository.split('/')) != 2:
        raise ValueError('noncanonical public repository')
    if len(commit) != 40 or not all(c in '0123456789abcdef' for c in commit):
        raise ValueError('noncanonical pinned commit')
    with tempfile.TemporaryDirectory(prefix='udm-v4-exposed-') as folder:
        git('init', '-q', folder)
        git('-C', folder, 'fetch', '--quiet', '--depth=1',
            'https://github.com/' + repository + '.git', commit, timeout=120)
        entries = git('-C', folder, 'ls-tree', '-r', '-z', commit).split(b'\0')
        files = {}
        regular = []
        omitted = Counter()
        for item in entries:
            if not item:
                continue
            left, name = item.split(b'\t', 1)
            mode, kind, oid = left.decode().split(' ')
            if mode not in {'100644', '100755'} or kind != 'blob':
                omitted[mode + '/' + kind] += 1
                continue
            path = name.decode('utf-8', errors='strict')
            if path in files or path in {entry[0] for entry in regular}:
                raise ValueError('duplicate source path')
            regular.append((path, oid))
        requests = ''.join(oid + '\n' for _, oid in regular).encode()
        output = git('-C', folder, 'cat-file', '--batch', input=requests, timeout=120)
        offset = 0
        for name, expected_oid in regular:
            end = output.index(b'\n', offset)
            head = output[offset:end].decode().split(' ')
            if len(head) != 3 or head[0] != expected_oid or head[1] != 'blob':
                raise ValueError('invalid raw Git object header')
            size = int(head[2])
            start = end + 1
            data = output[start:start + size]
            if len(data) != size or output[start + size:start + size + 1] != b'\n':
                raise ValueError('malformed blob transport')
            files[name] = data
            offset = start + size + 1
        if offset != len(output):
            raise ValueError('unconsumed raw Git objects')
        return files, dict(omitted)


def category(receipt):
    if not isinstance(receipt, dict):
        return {'status': 'UNKNOWN_RETURN_TYPE'}
    value = {'status': receipt.get('status')}
    if receipt.get('status') != 'CANDIDATE_SOURCE_ENVIRONMENT':
        value['reason'] = receipt.get('reason', 'UNKNOWN_UNSPECIFIED')
    return value


def main():
    raw_pool = POOL.read_bytes()
    actual = hashlib.sha256(raw_pool).hexdigest()
    if actual != EXPECTED_POOL_SHA256:
        raise ValueError('changed original frozen V3 pool')
    pool = json.loads(raw_pool)
    if pool.get('schema') != 'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V3' or len(pool.get('pool', [])) != 7:
        raise ValueError('not the exact exposed seven-case pool')
    catalog = json.loads(CATALOG.read_text())
    results = []
    for i, case in enumerate(pool['pool']):
        info = {'index': i, 'repo': case['repo'], 'pr': case['pr'],
                'base_commit': case['base_commit']}
        try:
            files, omitted = original_tree(case['repo'], case['base_commit'])
            a, b = old.select_profile(files, catalog), new.select_profile(files, catalog)
            info.update(v3=category(a), v4=category(b),
                        regular_file_count=len(files),
                        nonregular_mode_counts=omitted,
                        source_sha256=new._hash(new._canonical({
                            name: new._hash(data) for name, data in sorted(files.items())
                        }).encode()),
                        deferred_parse_count=len(b.get('constraints', {}).get('deferred_source_parse', [])))
            if b.get('status') == 'CANDIDATE_SOURCE_ENVIRONMENT':
                new.validate_selection(files, catalog, b)
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, TimeoutError) as error:
            info.update(v3={'status': 'NOT_EVALUATED'}, v4={'status': 'UNKNOWN_SOURCE_TRANSPORT'},
                        error_class=type(error).__name__)
        results.append(info)
        print(json.dumps({'index':i,'v3':info['v3'], 'v4':info['v4'],
                          'deferred_parse_count':info.get('deferred_parse_count', 0)}, sort_keys=True),
              file=sys.stderr, flush=True)
    summary = {
        'schema': 'UDM_V4_EXPOSED_STATIC_ADMISSION_DIAGNOSTICS',
        'source_pool_sha256': actual,
        'classification': 'EXPOSED_DIAGNOSTICS_NOT_PROSPECTIVE',
        'read_only_raw_git_objects': True, 'native_test_calls': 0,
        'fresh_scientific_trials': 0, 'coding_agent_calls': 0,
        'G2': 'UNKNOWN', 'G3': 'UNKNOWN', 'G4': 'UNKNOWN',
        'cases': results,
        'v3_categories': dict(Counter(v['v3'].get('reason', v['v3']['status']) for v in results)),
        'v4_categories': dict(Counter(v['v4'].get('reason', v['v4']['status']) for v in results)),
        'admission_candidate_count_v4': sum(
            x['v4']['status'] == 'CANDIDATE_SOURCE_ENVIRONMENT' for x in results),
        'native_admission_qualified_v4': False,
    }
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
