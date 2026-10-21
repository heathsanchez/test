"""Native V43 infrastructure qualification, with no developmental promotion.

The frozen tests execute the actual installed backend and original native
authority.  This driver retains their attempts, independently reads raw native
packets, and archives a complete committed source/evidence inventory.  It does
not select a prospective task, execute a coding agent, or establish G2--G6.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET

from .audit_index_v4 import compare_indexes, snapshot_indexes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '8c1ff8db64415b9ce6db865f2744f40a866293c9'
ACCEPTANCE = '2c23ade6ea04a910ee16c08c780ca1dd2e9764fe'
PREFIX = 'research/unified_consequence_runtime/'
RECORDS = HERE/'archaeology/experiment-interface-v43'
CATALOG = HERE/'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
TESTS = ('test_native_build_v43.py', 'test_native_execution_v43.py')
REVIEW_TESTS = ('test_native_build_boundary_v43.py',)
RUNTIME_TESTS = ('test_native_execution_controls_v43.py',)
INHERITED_RUNNER = 'native_inherited_controls_v43.py'
HANDOFF_RUNNER = PREFIX+'archaeology/experiment-interface-v43/prospective-implementation/native_handoff_supplement.py'
REVIEW_COMMIT = '960d70ac'
REVIEW_TEST_SHA256 = '8add2e1051855ae757755e5e42f35a4ab87907995834a5609c4309a8dde2fab2'
CAUSAL_TEST = 'test_native_materialization_v43.py'
WHOLE_TESTS = ('test_native_materialization_lineage_v43.py', 'test_qualify_native_frontier_v43.py',
               'test_controller_setup_preflight_v43.py')
CAUSAL_FREEZE_SHA256 = '3fd6a8fa4cb5e4eb4dc26ef4aa465aca8748f1e1ba3faecd82c1bf0b7713e19e'
PROSPECTIVE_FREEZE_SHA256 = 'd37c811589c161de59b5dfdb64d5ec609acaf971e2028d7a8ba1736279332500'
LINEAGE_COMMIT = '72c721d5'
LINEAGE_TEST_SHA256 = '4efa295421048d4ee25e11f1b265be5fcb3471faef689672e9e73d9c52ee1826'
PREFLIGHT_COMMIT = '1df47379'
PREFLIGHT_FREEZE_SHA256 = '8d58a7779981adba2e4214f16c49f46fa105032a8c819f73b09c75d2a45f78d0'
PREFLIGHT_TEST_SHA256 = 'fff64c87fa772aa6c56ad285cb064852b5861653ee762e0180ba78638fdf5124'
FREEZE_SCHEMA = 'UDM_EXPERIMENT_INTERFACE_FREEZE_V43'
RESULT_SCHEMA = 'UDM_EXPERIMENT_INTERFACE_QUALIFICATION_V43'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024*1024):
            value.update(chunk)
    return value.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value)+'\n')


def _retain_indexes(snapshot, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for number, row in enumerate(snapshot['indexes']):
        if row['exists']:
            raw = Path(row['path']).read_bytes()
            if sha(raw) != row['sha256'] or len(raw) != row['size_bytes']:
                raise ValueError('index changed during raw-byte retention')
            (destination/('index-'+str(number)+'.bytes')).write_bytes(raw)
    write(destination/'SNAPSHOT.json', snapshot)


@contextmanager
def index_interval(repo, destination):
    """Snapshot and retain all index bytes before starting the first Git read."""
    before = snapshot_indexes(repo)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    _retain_indexes(before, destination/'before')
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    try:
        yield
    finally:
        after = snapshot_indexes(repo)
        _retain_indexes(after, destination/'after')
        changes = compare_indexes(before, after)
        write(destination/'AUDIT.json', {'before': before, 'after': after, 'changes': changes})
        if changes:
            raise ValueError('index changed during read-only qualification; evidence retained')


def _git(repo, *args):
    return subprocess.check_output(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false',
        '-C', str(repo), *args], env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'),
        stderr=subprocess.PIPE)


def _tree(repo, ref, *, allow_links=False):
    rows = {}
    for row in _git(repo, 'ls-tree', '-r', '-z', ref).split(b'\0'):
        if not row:
            continue
        header, raw_name = row.split(b'\t', 1)
        mode, kind, oid = header.decode('ascii').split()
        name = raw_name.decode('utf-8')
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name or '\\' in name:
            raise ValueError('noncanonical committed source path')
        if kind != 'blob' or mode not in (('100644', '100755', '120000') if allow_links else ('100644', '100755')):
            raise ValueError('unsupported source-archive topology: '+name)
        rows[name] = {'mode': mode, 'kind': kind, 'oid': oid}
    return rows


def component_inventory(components, destination):
    """Read exact original component Git trees, retaining pre-read index bytes."""
    from .developmental_machine import check_source, PINS
    components, destination = Path(components).resolve(), Path(destination)
    result = {}
    for key, pin in sorted(PINS.items()):
        root = components/key
        with index_interval(root, destination/key):
            check_source(root, key)
            tree = _tree(root, pin['commit'], allow_links=True)
            files = {}
            for name, row in tree.items():
                path = root/name
                if row['mode'] == '120000':
                    if not path.is_symlink():
                        raise ValueError('component source alias changed: '+key+'/'+name)
                    raw = os.readlink(path).encode('utf-8', errors='surrogateescape')
                else:
                    if not path.is_file() or path.resolve() != path or path.is_symlink():
                        raise ValueError('component executable source path changed: '+key+'/'+name)
                    raw = path.read_bytes()
                    if bool(path.stat().st_mode & 0o111) != (row['mode'] == '100755'):
                        raise ValueError('component source Git mode changed: '+key+'/'+name)
                blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                if blob != row['oid']:
                    raise ValueError('component working bytes differ from exact original Git object: '+key+'/'+name)
                files[name] = {**row, 'sha256': sha(raw), 'size_bytes': len(raw)}
            result[key] = {'repository': pin['repository'], 'commit': pin['commit'],
                           'files': files, 'original_entrypoint_pins': pin['files']}
    write(destination/'MANIFEST.json', result)
    return result


def loaded_authorities(components, inventory):
    """Record actual loaded authority module locations against original source."""
    components = Path(components).resolve()
    result = {}
    for name, module in sorted(sys.modules.items()):
        if not (name == 'metatron' or name.startswith('metatron.') or
                name == 'realitygraph' or name.startswith('realitygraph.') or name.startswith('qckn_flash_')):
            continue
        filename = inspect.getsourcefile(module)
        if filename is None:
            raise ValueError('loaded authority source is unavailable: '+name)
        path = Path(filename).resolve()
        key = 'metatron' if name == 'metatron' or name.startswith('metatron.') else 'flash'
        relative = path.relative_to(components/key).as_posix()
        expected = inventory[key]['files'].get(relative)
        if expected is None or sha(path.read_bytes()) != expected['sha256']:
            raise ValueError('loaded authority differs from exact component inventory: '+name)
        result[name] = {'path': str(path), 'component': key, 'relative_path': relative,
                        'sha256': expected['sha256'], 'commit': inventory[key]['commit']}
    return result


def archive_components(components, out):
    """Archive full pinned component trees, never Git administration files."""
    components, out = Path(components).resolve(), Path(out).absolute()
    inventory = component_inventory(components, out/'component-archive-source-indexes')
    archives = {}
    for key, expected in sorted(inventory.items()):
        target = out/('COMPONENT_'+key+'_SOURCE.tar.gz')
        if target.exists():
            raise ValueError('refusing to overwrite original component source archive')
        with index_interval(components/key, out/('component-'+key+'-archive-index')):
            subprocess.run(['git', '--no-replace-objects', '-C', str(components/key),
                '-c', 'tar.umask=022', 'archive', '--format=tar.gz',
                '--output='+str(target), expected['commit']],
                env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), check=True)
        actual = {}
        with tarfile.open(target, 'r:gz') as packet:
            for member in packet:
                if member.isdir():
                    continue
                if member.name in actual or member.name not in expected['files']:
                    raise ValueError('component source archive has unexpected or duplicate member')
                row = expected['files'][member.name]
                if member.issym() and row['mode'] == '120000':
                    raw = member.linkname.encode('utf-8', errors='surrogateescape')
                elif member.isfile() and row['mode'] in ('100644', '100755'):
                    raw = packet.extractfile(member).read()
                    if bool(member.mode & 0o111) != (row['mode'] == '100755'):
                        raise ValueError('component source archive mode differs from exact original Git tree')
                else:
                    raise ValueError('unsupported or altered component source archive topology')
                if sha(raw) != row['sha256'] or len(raw) != row['size_bytes']:
                    raise ValueError('component source archive bytes differ from exact original Git tree')
                actual[member.name] = row
            if packet.pax_headers.get('comment') != expected['commit']:
                raise ValueError('component source archive lacks exact original Git commit identity')
        if actual != expected['files']:
            raise ValueError('component archive does not contain every original tracked source file')
        archives[key] = {**expected, 'archive': target.name, 'archive_sha256': file_sha(target),
                         'boundary': 'Full tracked original source; Git administration and credentials excluded.'}
    write(out/'COMPONENT_SOURCE_MANIFEST.json', archives)
    return archives


def _source(repo):
    # Reuse the original clean-commit/baseline preservation contract.
    from .qualify_environment_selection_v3 import freeze_source
    repo = Path(repo).resolve()
    head = _git(repo, 'rev-parse', 'HEAD').decode().strip()
    _git(repo, 'merge-base', '--is-ancestor', ACCEPTANCE, head)
    tree = _tree(repo, head)
    value = freeze_source(repo, BASE, tuple(tree))
    base_tree = _tree(repo, BASE)
    if len(base_tree) != 2361 or any(tree.get(name) != row for name, row in base_tree.items()):
        raise ValueError('complete V42 baseline bytes/modes changed')
    for name, row in tree.items():
        path = repo/name
        observed = stat.S_IMODE(path.lstat().st_mode)
        expected = int(row['mode'][-3:], 8)
        if not stat.S_ISREG(path.lstat().st_mode) or bool(observed & 0o111) != bool(expected & 0o111):
            raise ValueError('working source type/mode differs: '+name)
    value.update(source_tree=tree, baseline_files=len(base_tree))
    return value


def _acceptance(repo):
    path = RECORDS/'preimplementation/TEST_FREEZE.json'
    value = json.loads(path.read_text())
    if (value.get('schema') != 'UDM_V43_PREIMPLEMENTATION_ACCEPTANCE_TEST_FREEZE_V1'
            or value.get('baseline_commit') != BASE
            or value.get('counts') != {'tests': 76, 'failures': 68, 'passed': 8, 'errors': 0, 'skipped': 0}
            or value.get('returncode') != 1):
        raise ValueError('preimplementation acceptance authority differs')
    for name, digest in value['files_sha256'].items():
        raw = (Path(repo)/name).read_bytes()
        if sha(raw) != digest or _git(repo, 'show', ACCEPTANCE+':'+name) != raw:
            raise ValueError('frozen acceptance test changed: '+name)
    for name, digest in value['artifacts_sha256'].items():
        if sha((path.parent/name).read_bytes()) != digest:
            raise ValueError('retained preimplementation RED evidence changed')
    review_name = PREFIX+REVIEW_TESTS[0]
    review_raw = (Path(repo)/review_name).read_bytes()
    _git(repo, 'merge-base', '--is-ancestor', REVIEW_COMMIT, 'HEAD')
    if (sha(review_raw) != REVIEW_TEST_SHA256
            or _git(repo, 'show', REVIEW_COMMIT+':'+review_name) != review_raw):
        raise ValueError('supplementary boundary acceptance changed')
    return {'commit': ACCEPTANCE, 'descriptor_sha256': sha(path.read_bytes()),
            'tests': value['files_sha256'], 'expected_base_controls': 76,
            'review': {'commit': REVIEW_COMMIT, 'path': review_name, 'sha256': REVIEW_TEST_SHA256}}


def _runtime_freeze(runtime_paths):
    from . import native_environment_v42 as environment
    from . import native_execution_v42 as worker
    catalog = json.loads(CATALOG.read_text())
    environment.selection._catalog(catalog)
    profiles = {row['id']: row for row in catalog['profiles']}
    if set(runtime_paths) != set(profiles):
        raise ValueError('complete original two-profile runtime inventory required')
    runtimes, identities = {}, {}
    for name, profile in sorted(profiles.items()):
        runtime = environment.freeze_runtime(runtime_paths[name])
        environment.validate_runtime(profile, runtime)
        runtimes[name] = runtime
        identities[name] = {'environment': worker.environment_identity(runtime['interpreter']),
            'package_files_sha256': sha(canonical(environment.installed_package_identity(
                runtime['interpreter'], profile)).encode())}
    modern = profiles[catalog['profiles'][1]['id']]
    required = '/workspace/qualification/native-authority-v41-profile-preparation/modern-runtime-final/venv/bin/python'
    if runtime_paths[modern['id']] != required:
        raise ValueError('frozen acceptance fixture requires original canonical native interpreter path')
    return {'catalog_sha256': sha(CATALOG.read_bytes()), 'runtimes': runtimes,
            'profile_identities': identities}


def write_freeze(repo, out, runtime_paths, mode):
    out = Path(out).absolute()
    if out.exists():
        raise ValueError('refusing to replace a prior source freeze')
    with index_interval(repo, out.with_name(out.name+'.INDEX')):
        source = _source(repo)
        acceptance = _acceptance(repo)
        causal = prospective = preflight = None
        if mode == 'whole':
            causal_path = RECORDS/'causal-preimplementation/TEST_FREEZE.json'
            if not (HERE/CAUSAL_TEST).is_file() or not causal_path.is_file():
                raise ValueError('UNKNOWN_CAUSAL_ACCEPTANCE_NOT_FROZEN')
            causal = json.loads(causal_path.read_text())
            if (sha(causal_path.read_bytes()) != CAUSAL_FREEZE_SHA256
                    or not causal.get('files_sha256') or causal.get('returncode') != 1
                    or not causal.get('production_modules_absent_before_and_after')):
                raise ValueError('causal test freeze lacks its actual preimplementation RED')
            for name, digest in causal['files_sha256'].items():
                if sha((Path(repo)/name).read_bytes()) != digest:
                    raise ValueError('frozen causal acceptance changed: '+name)
            for name, digest in causal['artifacts_sha256'].items():
                if sha((causal_path.parent/name).read_bytes()) != digest:
                    raise ValueError('retained causal preimplementation RED changed: '+name)
            prospective_path = RECORDS/'prospective-preimplementation/TEST_FREEZE.json'
            prospective = json.loads(prospective_path.read_text())
            if (sha(prospective_path.read_bytes()) != PROSPECTIVE_FREEZE_SHA256
                    or prospective.get('returncode') != 1
                    or prospective.get('counts') != {'tests': 8, 'failures': 8, 'passed': 0, 'errors': 0, 'skipped': 0}):
                raise ValueError('prospective-binding preimplementation freeze differs')
            for name, digest in prospective['files_sha256'].items():
                if sha((Path(repo)/name).read_bytes()) != digest:
                    raise ValueError('frozen prospective binding test changed: '+name)
            for name, digest in prospective['artifacts_sha256'].items():
                if sha((prospective_path.parent/name).read_bytes()) != digest:
                    raise ValueError('retained prospective wiring RED changed: '+name)
            lineage_name = PREFIX+WHOLE_TESTS[0]
            lineage_raw = (Path(repo)/lineage_name).read_bytes()
            _git(repo, 'merge-base', '--is-ancestor', LINEAGE_COMMIT, 'HEAD')
            if (sha(lineage_raw) != LINEAGE_TEST_SHA256
                    or _git(repo, 'show', LINEAGE_COMMIT+':'+lineage_name) != lineage_raw):
                raise ValueError('independently frozen exact-invocation lineage control changed')
            preflight_path = RECORDS/'setup-preflight-preimplementation/TEST_FREEZE.json'
            preflight = json.loads(preflight_path.read_text())
            if (sha(preflight_path.read_bytes()) != PREFLIGHT_FREEZE_SHA256
                    or preflight.get('returncode') != 1
                    or preflight.get('counts') != {'tests': 6, 'failures': 6, 'passed': 0, 'errors': 0, 'skipped': 0}):
                raise ValueError('setup-preflight pre-fix RED differs')
            _git(repo, 'merge-base', '--is-ancestor', PREFLIGHT_COMMIT, 'HEAD')
            for name, digest in preflight['files_sha256'].items():
                raw = _git(repo, 'show', PREFLIGHT_COMMIT+':'+name)
                if sha(raw) != digest:
                    raise ValueError('retained pre-fix setup controller source differs: '+name)
                retained = out.with_name(out.name+'.PRE_FIX_SOURCES')/name
                retained.parent.mkdir(parents=True, exist_ok=True)
                if retained.exists():
                    raise ValueError('refusing to overwrite retained pre-fix setup source')
                retained.write_bytes(raw)
            if sha((HERE/WHOLE_TESTS[2]).read_bytes()) != PREFLIGHT_TEST_SHA256:
                raise ValueError('frozen setup-preflight test changed')
            for name, digest in preflight['artifacts_sha256'].items():
                if sha((preflight_path.parent/name).read_bytes()) != digest:
                    raise ValueError('retained setup-preflight RED artifact changed: '+name)
        tests = [PREFIX+name for name in (*TESTS, *REVIEW_TESTS, *RUNTIME_TESTS)]
        if PREFIX+INHERITED_RUNNER not in source['files']:
            raise ValueError('commit the original-statement inherited-control runner before qualification')
        if mode == 'whole':
            tests.append(PREFIX+CAUSAL_TEST)
            tests.extend(PREFIX+name for name in WHOLE_TESTS)
            if HANDOFF_RUNNER not in source['files']:
                raise ValueError('commit the real native prepared-context handoff supplement before whole qualification')
        from .developmental_machine import PINS
        result = {'schema': FREEZE_SCHEMA, **source, **_runtime_freeze(runtime_paths),
            'mode': mode, 'scope': 'NATIVE_INTERFACE_INFRASTRUCTURE_ONLY',
            'acceptance': acceptance, 'tests': {name: source['files'][name] for name in tests},
            'causal_acceptance': causal,
            'prospective_binding_acceptance': prospective, 'original_component_pins': PINS,
            'setup_preflight_acceptance': preflight,
            'scientific_verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
        write(out, result)
        return result


def check_freeze(repo, path, mode):
    frozen = json.loads(Path(path).read_text())
    source = _source(repo)
    from .developmental_machine import PINS
    tests = [PREFIX+name for name in (*TESTS, *REVIEW_TESTS, *RUNTIME_TESTS)]
    if mode == 'whole':
        tests.extend(PREFIX+name for name in (CAUSAL_TEST, *WHOLE_TESTS))
    if (frozen.get('schema') != FREEZE_SCHEMA or frozen.get('mode') != mode
            or any(frozen.get(key) != value for key, value in source.items())
            or frozen.get('original_component_pins') != PINS
            or frozen.get('tests') != {name: source['files'][name] for name in tests}
            or frozen.get('acceptance') != _acceptance(repo)):
        raise ValueError('V43 committed source/frozen acceptance differs')
    actual_runtime = _runtime_freeze({name: row['interpreter'] for name, row in frozen['runtimes'].items()})
    if any(frozen.get(key) != value for key, value in actual_runtime.items()):
        raise ValueError('frozen native executable/package/runtime identity changed')
    return frozen


def _junit(raw):
    counts = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    for case in ET.fromstring(raw).iter('testcase'):
        counts['tests'] += 1
        key = next((key for key, tag in [('errors', 'error'), ('failures', 'failure'),
            ('skipped', 'skipped')] if case.find(tag) is not None), 'passed')
        counts[key] += 1
    return counts


def _inferred_status(data, counts, collection):
    """Independent packet interpretation; never calls the producer's _status."""
    if data['timeout']:
        return 'UNKNOWN_TIMEOUT'
    if any(data.get(key) for key in ('source_mutations', 'unexpected_imports',
            'external_project_imports', 'changed_test_code', 'plugin_violations')):
        return 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    if (any(data.get(key) != collection[key] for key in ('collected_test_nodes',
            'selected_test_nodes', 'plugin_manifest', 'test_items'))
            or data.get('deselected_test_nodes') or data.get('collection_errors')):
        return 'UNKNOWN_EXACT_COLLECTION'
    reports, nodes = data.get('reports', []), collection['selected_test_nodes']
    if any(not isinstance(row, dict) or set(row) != {'nodeid', 'when', 'outcome', 'wasxfail'}
            or row['when'] not in ('setup', 'call', 'teardown')
            or row['outcome'] not in ('passed', 'failed', 'skipped')
            or not isinstance(row['wasxfail'], str) for row in reports):
        return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
    if any(row['wasxfail'] or row['outcome'] == 'skipped' for row in reports) or counts['skipped']:
        return 'UNKNOWN_SKIPPED_OR_XFAIL'
    calls = [row for row in reports if row['when'] == 'call']
    if (any([row['nodeid'] for row in reports if row['when'] == phase] != nodes
            for phase in ('setup', 'call', 'teardown'))
            or any(row['outcome'] != 'passed' for row in reports if row['when'] != 'call')
            or counts['tests'] != len(nodes) or counts['errors']
            or counts['passed'] != sum(row['outcome'] == 'passed' for row in calls)
            or counts['failures'] != sum(row['outcome'] == 'failed' for row in calls)):
        return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
    if counts['failures'] and data.get('process_exit_code') == 1:
        return 'FAIL_NATIVE'
    if counts['passed'] == len(nodes) and data.get('process_exit_code') == 0:
        return 'PASS_NATIVE'
    return 'UNKNOWN_NATIVE_ERROR'


def audit_native_packets(root, frozen):
    """Read retained original packets without importing any fixture source."""
    certificates, receipts, findings = {}, [], []
    for path in sorted(Path(root).rglob('admission-certificate.json')):
        if path.is_symlink():
            raise ValueError('redirected certificate artifact')
        value = json.loads(path.read_text())
        if value.get('schema') not in ('UDM_NATIVE_ADMISSION_CERTIFICATE_V43',
                                        'UDM_NATIVE_ADMISSION_CERTIFICATE_V42'):
            continue
        packet = {key: base64.b64decode(raw, validate=True) for key, raw in value['packet'].items()}
        if value['packet_sha256'] != {key: sha(raw) for key, raw in packet.items()}:
            raise ValueError('retained collection packet hash differs')
        data = json.loads(packet['checked-report.json'])
        if value['environment'] not in [row['environment'] for row in frozen['profile_identities'].values()]:
            raise ValueError('native certificate executable/package environment differs from frozen profiles')
        if value['schema'].endswith('_V43') and value['runner_sha256'] != frozen['files'][PREFIX+'native_execution_v43.py']:
            raise ValueError('native certificate runner differs from exact committed source')
        for name, raw in packet.items():
            retained = path.parent/name
            if retained.is_symlink() or not retained.is_file() or retained.read_bytes() != raw:
                raise ValueError('retained collection sidecar differs from actual packet')
        if value['collection'] != {key: data[key] for key in value['collection']}:
            raise ValueError('certificate collection differs from raw native report')
        if (data['mode'] != 'collect' or data['process_exit_code'] != 0 or data['timeout']
                or data.get('collection_errors') or data.get('deselected_test_nodes')):
            raise ValueError('retained collection certificate contains failed admission')
        certificates[sha(canonical(value).encode())] = value
    generated_passes = generated_failures = 0
    for path in sorted(Path(root).rglob('receipt.json')):
        if path.is_symlink():
            raise ValueError('redirected receipt artifact')
        value = json.loads(path.read_text())
        if value.get('schema') not in ('UDM_GENERIC_NATIVE_PYTEST_V43', 'UDM_GENERIC_NATIVE_PYTEST_V42'):
            continue
        certificate = certificates.get(value['certificate_sha256'])
        if certificate is None:
            raise ValueError('native receipt lacks retained original collection certificate: '+str(path))
        packet = {key: base64.b64decode(raw, validate=True) for key, raw in value['packet'].items()}
        if value['packet_sha256'] != {key: sha(raw) for key, raw in packet.items()}:
            raise ValueError('retained native packet hashes differ')
        data = json.loads(packet['checked-report.json'])
        raw_report = json.loads(packet['report.json'])
        controller_fields = {'process_exit_code', 'timeout', 'source_mutations', 'unexpected_imports', 'costs'}
        if raw_report != {key: item for key, item in data.items() if key not in controller_fields}:
            raise ValueError('checked report differs from original native producer report')
        for name, raw in packet.items():
            retained = path.parent/'execution'/name
            if retained.is_symlink() or not retained.is_file() or retained.read_bytes() != raw:
                raise ValueError('retained native sidecar differs from actual packet')
        counts = _junit(packet.get('native.xml', b'<testsuite/>'))
        status = _inferred_status(data, counts, certificate['collection'])
        if data != value['execution'] or counts != value['junit'] or status != value['status']:
            raise ValueError('native outcome disagrees with independently read protected execution')
        generated = [row for row in data.get('import_manifest', [])
                     if row['path'].endswith('/_version.py')]
        if value['schema'].endswith('_V43') and generated:
            generated_passes += status == 'PASS_NATIVE'
            generated_failures += status == 'FAIL_NATIVE'
        receipts.append({'path': str(path), 'schema': value['schema'], 'status': status,
            'junit': counts, 'generated_imports': generated})
    if not certificates or not generated_passes or not generated_failures:
        raise ValueError('missing actual generated-source collection, protected failure or native pass')
    findings.append('Actual V43 generated-module native PASS and protected FAIL independently reconstructed')
    return {'schema': 'UDM_V43_RAW_NATIVE_PACKET_AUDIT', 'status': 'PASS_BOUNDED_RAW_NATIVE_PACKETS',
        'certificates': len(certificates), 'receipts': receipts, 'findings': findings,
        'generated_passes': generated_passes, 'generated_failures': generated_failures,
        'boundary': 'Complete packet/status reconstruction. Candidate/import bytes are additionally reconstructed for the explicit retained supplement; other contexts remain frozen pytest controls, not a universal source-refinement proof.'}


_CHILD_REPLAY = '''import json,pathlib,sys,time
from research.unified_consequence_runtime import native_execution_v43 as worker
context=json.loads(pathlib.Path(sys.argv[1]).read_text())
out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
before=worker.attempt_snapshot();build_before=worker.build_snapshot();start=time.monotonic()
result={'status':'UNKNOWN_CHILD_REPLAY'}
try:
 receipt=worker.validate_receipt(context['contract'],context['candidate'],context['authority'],
  context['certificate'],context['receipt'],policy=context['policy'],output_dir=out/'reexecution',independent=True)
 assert receipt['status']=='PASS_NATIVE' and receipt['junit']['passed']==2
 result['status']='PASS_SEPARATE_PROCESS_NATIVE_REPLAY'
except BaseException as error:
 result['error']=type(error).__name__+': '+str(error)
 raise
finally:
 after=worker.attempt_snapshot()
 result.update(seconds=time.monotonic()-start,attempts_before=before,attempts_after=after,
  attempt_delta={key:after[key]-before[key] for key in after},build_before=build_before,
  build_after=worker.build_snapshot(),controller=sys.executable,runner_sha256=worker._runner_hash())
 (out/'RESULT.json').write_text(json.dumps(result,sort_keys=True)+'\\n')
'''


def native_audit_supplement(out, worker):
    """Retain a complete candidate/import context, independently replayed natively.

    This extra qualification fixture closes archival context missing from the
    pytest locals.  It is explicitly infrastructure, not a prospective task.
    """
    from . import native_build_v43 as build
    from .native_v43_test_support import make_project, MODERN_PYTHON
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    case = make_project(out/'fixture', 'alpha', worker.environment_identity(str(MODERN_PYTHON)), expected=1)
    original_inventory = case.inventory()
    evidence = build.prepare(case.contract, case.authority, case.policy, out/'build')
    contract = case.with_evidence(evidence)
    certificate = worker.collect(contract, case.authority, out/'collection', policy=case.policy)
    failure = worker.verify(contract, {'replacements': []}, out/'protected-failure',
        authority=case.authority, admission_certificate=certificate, policy=case.policy)
    if failure['status'] != 'FAIL_NATIVE' or failure['junit']['failures'] != 1:
        raise ValueError('supplement failed to execute the protected original assertion')
    failed_nodes = [row['nodeid'] for row in failure['execution']['reports']
                    if row['when'] == 'call' and row['outcome'] == 'failed']
    if not any(node == prefix or node.startswith(prefix+'[') or node.startswith(prefix+'::')
               for node in failed_nodes for prefix in case.authority['required_test_nodes']):
        raise ValueError('supplement failure is not the independently required protected assertion')
    candidate = case.candidate(1)
    receipt = worker.verify(contract, candidate, out/'native-pass', authority=case.authority,
                            admission_certificate=certificate, policy=case.policy)
    checked = worker.validate_receipt(contract, candidate, case.authority, certificate, receipt,
        policy=case.policy, output_dir=out/'independent-native-pass', independent=True)
    if checked['status'] != 'PASS_NATIVE' or checked['junit']['passed'] != 2:
        raise ValueError('supplement original native assertion or independent replay failed')
    generated = build.read_generated(contract, case.authority, case.policy, evidence)
    expected = dict(case.files)
    expected.update(generated)
    for row in candidate['replacements']:
        expected[row['path']] = row['replacement'].encode()
    imported = receipt['execution']['import_manifest']
    if (not imported or any(row['path'] not in expected or sha(expected[row['path']]) != row['sha256']
                            for row in imported)
            or case.generated_path not in {row['path'] for row in imported}):
        raise ValueError('supplement native import bytes differ from exact candidate/generated source')
    context = {'scope': 'QUALIFICATION_INFRASTRUCTURE_ONLY', 'contract': contract,
        'authority': case.authority, 'candidate': candidate, 'policy': case.policy,
        'certificate': certificate, 'receipt': receipt, 'source_manifest': case.manifest,
        'source_files': {name: base64.b64encode(raw).decode() for name, raw in case.files.items()},
        'generated_files': {name: base64.b64encode(raw).decode() for name, raw in generated.items()},
        'expected_candidate_files_sha256': {name: sha(raw) for name, raw in expected.items()},
        'source_git_directory': str(case.repo), 'base_commit': case.base, 'augmented_commit': case.augmented}
    write(out/'REPLAY_CONTEXT.json', context)
    script = out/'CHILD_REPLAY.py'
    script.write_text(_CHILD_REPLAY)
    child_started = time.monotonic()
    argv = [sys.executable, '-B', str(script), str(out/'REPLAY_CONTEXT.json'), str(out/'separate-process')]
    child = None
    try:
        child = subprocess.run(argv, cwd=ROOT, env=dict(os.environ,
                PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        (out/'child-stdout.log').write_bytes(child.stdout)
        (out/'child-stderr.log').write_bytes(child.stderr)
    except subprocess.TimeoutExpired as error:
        (out/'child-stdout.log').write_bytes(error.stdout or b'')
        (out/'child-stderr.log').write_bytes(error.stderr or b'')
        raise
    finally:
        write(out/'child-controller.json', {'argv': argv, 'timeout_seconds': 300,
            'seconds': time.monotonic()-child_started,
            'returncode': None if child is None else child.returncode})
    child_result = json.loads((out/'separate-process/RESULT.json').read_text())
    result = {'status': 'PASS_EXPLICIT_NATIVE_CONTEXT_AND_RESTART', 'seconds': time.monotonic()-started,
        'child_seconds': time.monotonic()-child_started, 'child_returncode': child.returncode,
        'child_source_sha256': sha(script.read_bytes()), 'child_result': child_result,
        'failure': {'status': failure['status'], 'junit': failure['junit']},
        'pass': {'status': receipt['status'], 'junit': receipt['junit'], 'imports': imported},
        'context_sha256': sha((out/'REPLAY_CONTEXT.json').read_bytes())}
    write(out/'RESULT.json', result)
    if (child.returncode or child_result['status'] != 'PASS_SEPARATE_PROCESS_NATIVE_REPLAY'
            or child_result['attempt_delta']['native_calls'] < 1
            or child_result['attempt_delta']['collection_calls'] < 1):
        raise ValueError('actual separate-process native replay failed')
    if case.inventory() != original_inventory:
        raise ValueError('supplement original source inventory changed during independent execution')
    return result


class _PytestInventory:
    def __init__(self):
        self.collected, self.reports = [], []

    def pytest_collection_finish(self, session):
        self.collected = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report):
        self.reports.append({'nodeid': report.nodeid, 'when': report.when,
            'outcome': report.outcome, 'wasxfail': getattr(report, 'wasxfail', '')})


def inherited_controls(out, frozen):
    """Run original adversarial method statements through the explicit V43 binding."""
    from .native_v43_test_support import MODERN_PYTHON
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    temporary = out/'default-temporaries'
    temporary.mkdir()
    argv = [str(MODERN_PYTHON), '-B', '-m',
        'research.unified_consequence_runtime.native_inherited_controls_v43',
        '--output', str(out/'controls')]
    start, child = time.monotonic(), None
    try:
        child = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT),
            TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'),
            capture_output=True, timeout=720)
        (out/'stdout.log').write_bytes(child.stdout)
        (out/'stderr.log').write_bytes(child.stderr)
    except subprocess.TimeoutExpired as error:
        (out/'stdout.log').write_bytes(error.stdout or b'')
        (out/'stderr.log').write_bytes(error.stderr or b'')
        raise
    finally:
        write(out/'controller.json', {'argv': argv, 'seconds': time.monotonic()-start,
            'timeout_seconds': 720, 'returncode': None if child is None else child.returncode})
    result = json.loads((out/'controls/result.json').read_text())
    text = (out/'controls/unittest.log').read_text()
    if (child.returncode or result.get('status') != 'PASS' or result.get('tests') != 27
            or result.get('failures') or result.get('errors') or ' ... skipped' in text
            or len([line for line in text.splitlines() if line.endswith(' ... ok')]) != 27
            or 'Ran 27 tests' not in text or not text.rstrip().endswith('OK')
            or result.get('runner_sha256') != frozen['files'][PREFIX+INHERITED_RUNNER]
            or not result.get('test_method_code_objects_unchanged')
            or result.get('attempts', {}).get('native_calls', 0) < 1
            or result.get('attempts', {}).get('collection_calls', 0) < 1):
        raise ValueError('original inherited V43 assertion-bypass controls failed or were not completely executed')
    return result


def native_handoff(out, frozen):
    """Execute the fixed real native interface/controller handoff diagnostic."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    script = ROOT/HANDOFF_RUNNER
    if sha(script.read_bytes()) != frozen['files'][HANDOFF_RUNNER]:
        raise ValueError('native handoff runner differs from exact frozen source')
    temporary = out/'default-temporaries'
    temporary.mkdir()
    argv = [sys.executable, '-B', str(script), str(out/'handoff')]
    started, child = time.monotonic(), None
    try:
        with (out/'stdout.log').open('wb') as stdout, (out/'stderr.log').open('wb') as stderr:
            child = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT),
                TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'),
                stdout=stdout, stderr=stderr, timeout=720)
    finally:
        write(out/'controller.json', {'argv': argv, 'seconds': time.monotonic()-started,
            'timeout_seconds': 720, 'returncode': None if child is None else child.returncode,
            'runner_sha256': frozen['files'][HANDOFF_RUNNER]})
    result = json.loads((out/'handoff/RESULT.json').read_text())
    if (child.returncode or result.get('status') != 'PASS_BOUNDED_REAL_NATIVE_ENVIRONMENT_HANDOFF'
            or result.get('source_unchanged') is not True or result.get('closure_agrees') is not True
            or result.get('original_statuses') != {'alpha': 'PASS_NATIVE', 'beta': 'FAIL_NATIVE'}
            or result.get('unrelated_native_status') != 'PASS_NATIVE'
            or set(result.get('denied_before_any_producer', [])) != {'cached-profile', 'uncached-profile',
                'new-native-probe', 'actual-agent-worker-path'}
            or any(result.get('verdicts', {}).get(f'G{i}') != 'UNKNOWN' for i in range(2, 7))):
        raise ValueError('real native interface/controller handoff or exact-witness preflight failed')
    return result


def qualify(repo, freeze_path, out, mode, components):
    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    result = {'schema': RESULT_SCHEMA, 'status': 'UNKNOWN_INTERFACE_QUALIFICATION',
        'mode': mode, 'scope': 'NATIVE_INTERFACE_INFRASTRUCTURE_ONLY',
        'verdicts': {'G0_G1': 'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY',
                     **{f'G{i}': 'UNKNOWN' for i in range(2, 7)}},
        'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
        'cost_boundary': 'Actual V43 builder pip-wheel attempts and original native-controller launches; builder Git logs and total qualification wall retained. Fixture-oracle subprocesses and identity checks are not included in these counters. Child counters separate; engineering/model/tool/storage lifecycle costs UNKNOWN.',
        'external_enforcement': 'UNKNOWN_NONBYPASSABILITY'}
    started, worker, before, builds_before = time.monotonic(), None, None, None
    try:
        with index_interval(repo, out/'index-interval'):
            frozen = check_freeze(repo, freeze_path, mode)
            result.update(source_commit=frozen['source_commit'], freeze=frozen)
            original_components = component_inventory(components, out/'component-source-pre')
            result['component_source_pre_sha256'] = sha(canonical(original_components).encode())
            from . import native_execution_v43 as worker
            import pytest
            if any(os.environ.get(key) for key in ('PYTEST_ADDOPTS', 'PYTEST_PLUGINS')):
                raise ValueError('unfrozen controller pytest options or plugins')
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
            result['controller_environment'] = worker.environment_identity(sys.executable)
            before, builds_before = worker.attempt_snapshot(), worker.build_snapshot()
            inventory = _PytestInventory()
            args = ['-q', '--import-mode=importlib', '-p', 'no:cacheprovider',
                *frozen['tests'], '--basetemp='+str(out/'native-fixtures'), '--tb=short',
                '--junitxml='+str(out/'contracts.xml')]
            result['command'] = [sys.executable, '-B', '-m', 'pytest', *args]
            old_cwd = Path.cwd()
            try:
                os.chdir(repo)
                with (out/'stdout.log').open('w') as stdout, (out/'stderr.log').open('w') as stderr:
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        code = int(pytest.main(args, plugins=[inventory]))
            finally:
                os.chdir(old_cwd)
            result['pytest_exit_code'] = code
            result['contracts'] = {'collection': inventory.collected, 'reports': inventory.reports,
                'junit': _junit((out/'contracts.xml').read_bytes()),
                'expected_cases': 118 if mode == 'whole' else 100}
            write(out/'PYTEST_INVENTORY.json', result['contracts'])
            base_ids = [name for name in inventory.collected
                        if any(name.startswith(PREFIX+test+'::') for test in TESTS)]
            counts = result['contracts']['junit']
            if (code != 0 or len(base_ids) != 76 or len(set(inventory.collected)) != len(inventory.collected)
                    or len(inventory.collected) != result['contracts']['expected_cases']
                    or counts['tests'] != len(inventory.collected)
                    or any(counts[key] for key in ('failures', 'errors', 'skipped'))
                    or any(not any(node.startswith(name+'::') for node in inventory.collected)
                           for name in frozen['tests'])):
                raise ValueError('frozen native control suite failed or collection changed')
            if mode == 'whole' and not any(name.startswith(PREFIX+CAUSAL_TEST+'::')
                                           for name in inventory.collected):
                raise ValueError('whole interface gate lacks causal controls')
            result['inherited_controls'] = inherited_controls(out/'inherited-controls', frozen)
            if mode == 'whole':
                result['native_handoff'] = native_handoff(out/'native-handoff', frozen)
            result['explicit_native_context'] = native_audit_supplement(out/'native-context', worker)
            native_audit = audit_native_packets(out, frozen)
            write(out/'RAW_NATIVE_AUDIT.json', native_audit)
            result['raw_native_audit'] = native_audit
            post_components = component_inventory(components, out/'component-source-post')
            if post_components != original_components:
                raise ValueError('original component source changed during native qualification')
            result['loaded_authorities'] = loaded_authorities(components, post_components)
            if mode == 'whole' and not {'metatron.nucleus', 'qckn_flash_live_router', 'realitygraph.flash'} <= set(result['loaded_authorities']):
                raise ValueError('whole interface gate did not load the original independent warrant/closure authorities')
            write(out/'LOADED_AUTHORITIES.json', result['loaded_authorities'])
            check_freeze(repo, freeze_path, mode)
            result['status'] = ('QUALIFIED_BOUNDED_NATIVE_TRANSPORT_ONLY' if mode == 'build-native'
                                else 'QUALIFIED_BOUNDED_CAUSAL_NATIVE_INTERFACE_ONLY')
    except (Exception, KeyboardInterrupt) as error:
        result['smallest_obstruction'] = type(error).__name__+': '+str(error)
    finally:
        result['wall_seconds'] = time.monotonic()-started
        if worker is not None:
            after, builds_after = worker.attempt_snapshot(), worker.build_snapshot()
            result['attempts'] = {'before': before, 'after': after,
                'delta': {key: after[key]-before[key] for key in after
                          if before is not None and isinstance(after[key], (int, float))
                          and isinstance(before.get(key), (int, float))}}
            result['build_attempts'] = {'before': builds_before, 'after': builds_after}
            write(out/'BUILD_ATTEMPTS.json', result['build_attempts'])
            if (result['status'].startswith('QUALIFIED_')
                    and (not result['attempts']['delta'].get('native_calls')
                         or not result['attempts']['delta'].get('collection_calls')
                         or not builds_after.get('builder_attempts', {}).get('build_calls'))):
                result.update(status='UNKNOWN_INTERFACE_QUALIFICATION',
                    smallest_obstruction='Missing actual native, collection or builder launch accounting')
        if (out/'index-interval/AUDIT.json').is_file():
            result['index_audit'] = json.loads((out/'index-interval/AUDIT.json').read_text())
        write(out/'RESULT.json', result)
    return result


def archive(repo, out, freeze_path=None, preparation=(), components=None):
    """Archive regular bytes and link identities without following any links."""
    repo, out = Path(repo).resolve(), Path(out).absolute()
    out.mkdir(parents=True, exist_ok=True)
    source_tar, evidence_tar = out/'SOURCE.tar.gz', out/'EXPERIMENT_INTERFACE_V43_EVIDENCE.tar.gz'
    if any(path.exists() for path in (source_tar, evidence_tar, out/'MANIFEST.json')):
        raise ValueError('refusing to overwrite prior qualification archives')
    with index_interval(repo, out/'archive-index-interval'):
        commit = _git(repo, 'rev-parse', 'HEAD').decode().strip()
        subprocess.run(['git', '--no-replace-objects', '-C', str(repo), '-c', 'tar.umask=022',
            'archive', '--format=tar.gz', '--output='+str(source_tar), commit],
            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), check=True)
        files, modes = {}, {}
        with tarfile.open(source_tar, 'r:gz') as packet:
            for member in packet:
                if member.isdir():
                    continue
                if not member.isfile() or member.name in files:
                    raise ValueError('source archive has unsupported or duplicate member')
                files[member.name] = sha(packet.extractfile(member).read())
                modes[member.name] = '100'+format(member.mode, '03o')
        tree = _tree(repo, commit)
        if set(files) != set(tree) or any(modes[name] != tree[name]['mode'] for name in tree):
            raise ValueError('complete source archive modes/inventory differ from committed tree')
        if freeze_path and Path(freeze_path).is_file():
            frozen = json.loads(Path(freeze_path).read_text())
            if files != frozen['files'] or commit != frozen['source_commit']:
                raise ValueError('source archive differs from complete source freeze')
        write(out/'SOURCE_ARCHIVE_CHECK.json', {'status': 'PASS_EXACT_FULL_SOURCE',
            'source_commit': commit, 'files': len(files), 'source_sha256': file_sha(source_tar)})
    component_archives, component_error = {}, None
    try:
        if components is not None:
            component_archives = archive_components(components, out)
    except Exception as error:
        component_error = type(error).__name__+': '+str(error)
        write(out/'COMPONENT_SOURCE_ARCHIVE_OBSTRUCTION.json', {'status': 'UNKNOWN_COMPONENT_SOURCE_ARCHIVE',
            'smallest_obstruction': component_error, 'partial_evidence_retained': True})
    entries = {}
    excluded = {source_tar, evidence_tar, out/'MANIFEST.json'}
    for origin, prefix in [(out, ''), *((Path(path).absolute(), 'preparation/'+str(number)+'/')
                                      for number, path in enumerate(preparation))]:
        if not origin.exists():
            continue
        if origin.is_file():
            entries[prefix+origin.name] = origin
            continue
        for folder, dirs, names in os.walk(origin, followlinks=False):
            for name in sorted(dirs):
                path = Path(folder)/name
                if path.is_symlink():
                    entries[prefix+path.relative_to(origin).as_posix()] = path
            runtime_preparation = origin != out or Path(folder).relative_to(out).parts[:1] == ('original-runtimes',)
            omitted = {'venv', 'miniconda-base', 'wheels'} if runtime_preparation else set()
            dirs[:] = sorted(name for name in dirs if name not in omitted
                              and not (Path(folder)/name).is_symlink())
            for name in sorted(names):
                path = Path(folder)/name
                if path not in excluded and (path.is_file() or path.is_symlink()):
                    entries[prefix+path.relative_to(origin).as_posix()] = path
    manifest_files = {name: {'kind': 'symlink', 'target': os.readlink(path)} if path.is_symlink()
                      else {'kind': 'file', 'sha256': sha(path.read_bytes())}
                      for name, path in sorted(entries.items())}
    with tarfile.open(evidence_tar, 'w:gz', dereference=False) as packet:
        for name, path in sorted(entries.items()):
            packet.add(path, arcname=name, recursive=False)
    result = {'schema': 'UDM_EXPERIMENT_INTERFACE_ARCHIVE_MANIFEST_V43',
        'source_commit': commit, 'run_id': os.environ.get('GITHUB_RUN_ID'),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'), 'files': manifest_files,
        'component_source_manifest_sha256': file_sha(out/'COMPONENT_SOURCE_MANIFEST.json') if component_archives else None,
        'component_source_status': 'UNKNOWN_COMPONENT_SOURCE_ARCHIVE' if component_error else 'PASS_EXACT_ORIGINAL_COMPONENT_SOURCES',
        'source_sha256': file_sha(source_tar), 'archive_sha256': file_sha(evidence_tar),
        'boundary': 'Original links retained without dereference; inspect members safely without automatic extraction.'}
    write(out/'MANIFEST.json', result)
    if component_error:
        raise ValueError('component source archival failed; complete partial evidence retained: '+component_error)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('build-native', 'whole'), default='whole')
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--runtimes', type=Path)
    parser.add_argument('--write-freeze', action='store_true')
    parser.add_argument('--archive', action='store_true')
    parser.add_argument('--preparation', type=Path, action='append', default=[])
    parser.add_argument('--components', type=Path,
                        default=Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')))
    args = parser.parse_args()
    if args.write_freeze:
        if args.runtimes is None:
            parser.error('--runtimes is required to freeze original profiles')
        result = write_freeze(args.repo, args.out, json.loads(args.runtimes.read_text()), args.mode)
    elif args.archive:
        result = archive(args.repo, args.out, args.freeze, args.preparation, args.components)
    else:
        if args.freeze is None:
            parser.error('--freeze is required for qualification')
        result = qualify(args.repo, args.freeze, args.out, args.mode, args.components)
    print(canonical({key: result[key] for key in ('status', 'source_commit', 'verdicts') if key in result}))
    if not args.write_freeze and not args.archive and not result['status'].startswith('QUALIFIED_'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
