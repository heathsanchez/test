"""Frozen environment admission on two previously exposed development diagnostics.

This entrypoint acquires no capability and evaluates no genuine frontier. A green
result means both original suites actually failed protected calls in two complete
independent native executions under source-selected, externally pinned profiles.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import packaging

from .decisive_native_verify import _path, canonical, fingerprint, sha256
from . import native_environment_v3 as environment
from . import native_execution_v3 as execution
from .qualify_native_admission_v2 import preserve_authority, state_snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECORDS = HERE / 'archaeology/native-environment-v3'
PROTOCOL = RECORDS / 'PROTOCOL.json'
FREEZE_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V3'


def _development_spec(raw, origin):
    keys = ('repo', 'pr', 'base_commit', 'head_commit', 'files', 'metadata_url')
    return {**{key: raw[key] for key in keys}, 'original_role': raw['role'],
            'role': 'DEVELOPMENT_DIAGNOSTICS_ONLY', 'origin': origin, 'origin_index': 0}


def inputs():
    protocol = json.loads(PROTOCOL.read_text())
    if protocol.get('schema') != 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_PROTOCOL_V3':
        raise ValueError('wrong frozen environment qualification protocol')
    loaded = {}
    for key, row in {**protocol['origin'], 'catalog': protocol['catalog'],
                     'package_metadata': protocol['package_metadata']}.items():
        path = ROOT / _path(row['path'])
        if sha256(path.read_bytes()) != row['sha256']:
            raise ValueError('frozen qualification input changed: ' + key)
        loaded[key] = json.loads(path.read_text())
    expected = [_development_spec(loaded['legacy']['selected'][0], 'legacy'),
                _development_spec(loaded['modern']['diagnostics'][0], 'modern')]
    if (protocol['diagnostics'] != expected or protocol['mode'] != 'DEVELOPMENT_DIAGNOSTICS_ONLY'
            or [(row['repo'].lower(), row['pr']) for row in expected] != [
                ('grahamdumpleton/wrapt', 99), ('more-itertools/more-itertools', 1309)]
            or protocol['acquisitions'] != 0 or protocol['candidates'] != 0
            or any(protocol['verdicts'][f'G{i}'] != 'UNKNOWN' for i in range(2, 7))):
        raise ValueError('only two exact previously exposed development diagnostics are licensed')
    catalog = loaded['catalog']; environment.selection._catalog(catalog)
    if (catalog.get('package_metadata_sha256') != protocol['package_metadata']['sha256']
            or len(catalog['profiles']) != 2):
        raise ValueError('complete independently fixed two-profile catalog required')
    return protocol, catalog


def _git(repo, *args):
    return subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE)


def _preserved_baseline(repo, base, head):
    _git(repo, 'merge-base', '--is-ancestor', base, head)
    changes = _git(repo, 'diff', '--name-status', '--no-renames', base, head).decode().splitlines()
    if any(not row.startswith('A\t') for row in changes):
        raise ValueError('prior baseline files changed; only new versioned source is permitted')


def freeze_source(repo, base, paths):
    """Require a clean commit and retain every prior Git file unchanged."""
    repo = Path(repo).resolve()
    if _git(repo, 'status', '--porcelain').strip():
        raise ValueError('commit clean source and protocol before diagnostic execution')
    head = _git(repo, 'rev-parse', 'HEAD').decode().strip()
    _preserved_baseline(repo, base, head)
    files = {}
    for name in sorted(set(paths)):
        _path(name); raw = _git(repo, 'show', head + ':' + name)
        if raw != (repo / name).read_bytes():
            raise ValueError('working source differs from committed source')
        files[name] = sha256(raw)
    return {'source_commit': head, 'baseline_commit': base, 'files': files,
            'all_baseline_files_preserved': True}


def _source_paths(repo, head):
    return _git(repo, 'ls-tree', '-r', '--name-only', head, '--',
                'research/unified_consequence_runtime', '.github/workflows').decode().splitlines()


def write_freeze(repo, out, runtime_paths):
    started = time.monotonic()
    protocol, catalog = inputs(); repo = Path(repo).resolve()
    head = _git(repo, 'rev-parse', 'HEAD').decode().strip()
    source = freeze_source(repo, protocol['base_commit'], _source_paths(repo, head))
    profiles = {profile['id']: profile for profile in catalog['profiles']}
    if not isinstance(runtime_paths, dict) or set(runtime_paths) != set(profiles):
        raise ValueError('both exact external runtime paths must precede source access')
    runtimes = {}
    for ident in sorted(profiles):
        runtimes[ident] = environment.freeze_runtime(runtime_paths[ident])
        environment.validate_runtime(profiles[ident], runtimes[ident])
    value = {'schema': FREEZE_SCHEMA, **source, 'protocol_sha256': sha256(PROTOCOL.read_bytes()),
             'catalog_sha256': fingerprint(catalog), 'runtimes': runtimes,
             'metadata_parser_packaging_version': packaging.__version__,
             'mode': protocol['mode'], 'exposure': protocol['exposure'],
             'diagnostic_source_access_started': False, 'freeze_wall_seconds': time.monotonic() - started}
    path = Path(out); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value) + '\n'); return value


def check_freeze(repo, path):
    protocol, catalog = inputs(); repo = Path(repo).resolve()
    frozen = json.loads(Path(path).read_text()); head = _git(repo, 'rev-parse', 'HEAD').decode().strip()
    if (frozen.get('schema') != FREEZE_SCHEMA or frozen.get('source_commit') != head
            or frozen.get('baseline_commit') != protocol['base_commit']
            or frozen.get('all_baseline_files_preserved') is not True
            or frozen.get('protocol_sha256') != sha256(PROTOCOL.read_bytes())
            or frozen.get('catalog_sha256') != fingerprint(catalog)
            or frozen.get('metadata_parser_packaging_version') != packaging.__version__
            or frozen.get('diagnostic_source_access_started') is not False
            or set(frozen.get('files', {})) != set(_source_paths(repo, head))):
        raise ValueError('qualification source, catalog, or protocol differs from frozen authority')
    _preserved_baseline(repo, protocol['base_commit'], head)
    if _git(repo, 'diff', '--name-only', 'HEAD').strip() or any(
            sha256((repo / _path(name)).read_bytes()) != digest for name, digest in frozen['files'].items()):
        raise ValueError('frozen qualification source changed')
    profiles = {profile['id']: profile for profile in catalog['profiles']}
    if set(frozen.get('runtimes', {})) != set(profiles):
        raise ValueError('frozen complete runtime inventory changed')
    for ident, record in frozen['runtimes'].items():
        environment.validate_runtime(profiles[ident], record)
    return frozen


def task_gate(authority, certificate, receipt):
    """Additional full-suite gate after the worker's independent replay."""
    protected = []; reason = 'UNKNOWN_INCOMPLETE_ORIGINAL_NATIVE_EXECUTION'; nodes = []
    try:
        collection = certificate['collection']; nodes = collection['selected_test_nodes']
        data = receipt['execution']; counts = receipt['junit']; reports = data['reports']
        calls = [row for row in reports if row['when'] == 'call']
        protected = [row['nodeid'] for row in calls if row['outcome'] == 'failed' and any(
            row['nodeid'] == prefix or row['nodeid'].startswith(prefix + '[')
            or row['nodeid'].startswith(prefix + '::') for prefix in authority['required_test_nodes'])]
        good = (receipt['status'] == 'FAIL_NATIVE' and nodes and len(set(nodes)) == len(nodes)
            and len(collection['collected_test_nodes']) == len(nodes)
            and set(collection['collected_test_nodes']) == set(nodes) and not collection['deselected_test_nodes']
            and data['collected_test_nodes'] == collection['collected_test_nodes']
            and data['selected_test_nodes'] == nodes and not data['deselected_test_nodes']
            and not data['timeout'] and data['process_exit_code'] == 1 and protected
            and all(not data[key] for key in ('collection_errors', 'source_mutations', 'unexpected_imports',
                'external_project_imports', 'changed_test_code', 'plugin_violations'))
            and all(not row['wasxfail'] and row['outcome'] in ('passed', 'failed') for row in reports)
            and all([row['nodeid'] for row in reports if row['when'] == phase] == nodes
                    for phase in ('setup', 'call', 'teardown'))
            and len(reports) == 3 * len(nodes)
            and all(row['outcome'] == 'passed' for row in reports if row['when'] != 'call')
            and counts['tests'] == counts['passed'] + counts['failures'] == len(nodes)
            and counts['passed'] == sum(row['outcome'] == 'passed' for row in calls)
            and counts['failures'] == sum(row['outcome'] == 'failed' for row in calls) > 0
            and not counts['errors'] and not counts['skipped']
            and receipt['costs']['native_calls'] == 1
            and receipt['independent_reexecution']['costs']['native_calls'] == 1)
    except (KeyError, TypeError, ValueError):
        good = False
    return {'status': 'PASS' if good else 'UNKNOWN', 'selected_nodes': len(nodes),
            'protected_failed_nodes': protected, 'reason': None if good else reason}


def first_task_gate(gates):
    good = isinstance(gates, list) and len(gates) == 2 and all(row.get('status') == 'PASS' for row in gates)
    return {'status': 'PASS' if good else 'UNKNOWN', 'diagnostics': gates,
            'requirement': 'Both exposed diagnostics require complete independently repeated protected native failures'}


def attempt_delta(before):
    """Charge controller launch attempts even when a native packet is malformed."""
    after = execution.attempt_snapshot()
    result = {key: after[key] - before[key] for key in
              ('native_calls', 'collection_calls', 'subprocess_attempts')}
    if any(value < 0 for value in result.values()):
        raise ValueError('native attempt accounting moved backwards')
    return result


def qualify(args):
    started = time.monotonic(); attempts_before = execution.attempt_snapshot()
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    protocol, catalog = inputs(); frozen = check_freeze(args.repo, args.freeze)
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    binding = sha256(Path(args.freeze).read_bytes())
    result = {'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V3', 'status': 'UNKNOWN_QUALIFICATION',
        'source_commit': frozen['source_commit'], 'mode': protocol['mode'], 'exposure': protocol['exposure'],
        'freeze': frozen, 'protocol_binding': binding, 'runtime_inventory': frozen['runtimes'],
        'verdicts': protocol['verdicts'], 'tasks': [], 'first_task_gate': first_task_gate([]),
        'cost_boundary': protocol['costs'], 'acquisitions': 0, 'candidates': 0}
    def save():
        result['total_wall_seconds'] = time.monotonic() - started
        result['attempt_costs'] = attempt_delta(attempts_before)
        result['attempt_cost_boundary'] = 'Inclusive native/collection launch attempts; nested receipt counts are not additive'
        (out / 'RESULT.json').write_text(canonical(result) + '\n')
    for path in (PROTOCOL, RECORDS / 'ENVIRONMENT_CATALOG.json', RECORDS / 'PACKAGE_METADATA.json'):
        (out / path.name).write_bytes(path.read_bytes())
    (out / 'FREEZE.json').write_bytes(Path(args.freeze).read_bytes())
    try:
        result['retention'] = preserve_authority(out, args.components, protocol); save()
        gates = []
        for index, spec in enumerate(protocol['diagnostics']):
            item = {'repository': spec['repo'], 'role': spec['role'], 'status': 'UNKNOWN_SETUP'}
            result['tasks'].append(item); task_started = time.monotonic()
            task_attempts_before = execution.attempt_snapshot()
            try:
                check_freeze(args.repo, args.freeze)
                folder = out / ('task-' + str(index))
                setup = environment.provision(spec, folder, binding, catalog=catalog, runtimes=frozen['runtimes'])
                item['setup'] = setup; item['status'] = setup['status']
                if setup['status'] == 'PREPARED':
                    contract, authority, policy = (setup[key] for key in ('contract', 'authority', 'policy'))
                    certificate = execution.collect(contract, authority, folder / 'collection', policy=policy)
                    receipt = execution.verify(contract, {'replacements': []}, folder / 'native-execution',
                        authority=authority, admission_certificate=certificate, policy=policy)
                    checked = execution.validate_receipt(contract, {'replacements': []}, authority, certificate,
                        receipt, policy=policy, output_dir=folder / 'independent-native-execution', independent=True)
                    (folder / 'independently-validated-receipt.json').write_text(canonical(checked) + '\n')
                    item.update(status=checked['status'], collection={'nodes': len(certificate['collection']['selected_test_nodes']),
                        'costs': certificate['costs'], 'certificate_sha256': fingerprint(certificate)},
                        receipt={key: checked[key] for key in ('status', 'junit', 'costs', 'independent_reexecution')},
                        gate=task_gate(authority, certificate, checked))
                else:
                    item['gate'] = {'status': 'UNKNOWN', 'reason': setup.get('reason', setup['status'])}
            except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as error:
                item.update(status='UNKNOWN_DIAGNOSTIC', error=type(error).__name__ + ': ' + str(error),
                            gate={'status': 'UNKNOWN', 'reason': str(error)})
            finally:
                item['attempt_costs'] = attempt_delta(task_attempts_before)
                item['total_wall_seconds'] = time.monotonic() - task_started
                save()
            gates.append(item['gate'])
            result['first_task_gate'] = first_task_gate(gates); save()
        check_freeze(args.repo, args.freeze)
        if result['first_task_gate']['status'] == 'PASS':
            result['status'] = 'ADMISSION_ONLY_QUALIFIED'
        return result
    except (OSError, ValueError, RuntimeError, TypeError, subprocess.SubprocessError) as error:
        result.update(status='UNKNOWN_QUALIFICATION', error=type(error).__name__ + ': ' + str(error))
        return result
    finally:
        save()


def main(argv=None):
    started = time.monotonic(); attempts_before = execution.attempt_snapshot()
    parser = argparse.ArgumentParser(); parser.add_argument('--repo', required=True); parser.add_argument('--out', required=True)
    parser.add_argument('--runtimes'); parser.add_argument('--components'); parser.add_argument('--source-repos')
    parser.add_argument('--freeze'); parser.add_argument('--write-freeze', action='store_true'); args = parser.parse_args(argv)
    output_existed = Path(args.out).exists()
    try:
        if args.write_freeze:
            if not args.runtimes: parser.error('--runtimes is required before any target access')
            result = write_freeze(args.repo, args.out, json.loads(Path(args.runtimes).read_text()))
        else:
            if not args.components or not args.freeze: parser.error('--components and --freeze are required')
            result = qualify(args)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result = {'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_ERROR_V3', 'status': 'UNKNOWN_PREFLIGHT',
                  'error': type(error).__name__ + ': ' + str(error),
                  'total_wall_seconds': time.monotonic() - started, 'attempt_costs': attempt_delta(attempts_before),
                  'acquisitions': 0, 'candidates': 0}
        # A refusal must not overwrite a prior run or a prior freeze artifact.
        if not output_existed:
            folder = Path(args.out).parent if args.write_freeze else Path(args.out)
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / 'ERROR.json'
            if not path.exists(): path.write_text(canonical(result) + '\n')
        print(canonical(result)); raise SystemExit(1)
    print(canonical({'status': result.get('status', 'FROZEN'), 'verdicts': result.get('verdicts', {})}))
    if not args.write_freeze and result['status'] != 'ADMISSION_ONLY_QUALIFIED': raise SystemExit(1)


if __name__ == '__main__':
    main()
