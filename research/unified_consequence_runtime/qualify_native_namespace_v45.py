"""Independently qualify bounded V45 admission; scientific G2--G6 stay UNKNOWN."""
from __future__ import annotations

import argparse
import base64
from contextlib import redirect_stderr, redirect_stdout
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import time
from types import FunctionType

from . import qualify_native_bootstrap_v44 as bootstrap

original = bootstrap.original
HERE, ROOT, PREFIX = original.HERE, original.ROOT, original.PREFIX
BASE = '88aa5090c310d2f75683a019a5bc958cdb3b576e'
RECORDS = HERE/'archaeology/native-namespace-v45'
SEAL_SHA256 = '48584499e067742a877b0ebf3c662ab96004e4ed628ebdc88a68bb42dbed2cce'
FREEZE_SCHEMA = 'UDM_NATIVE_NAMESPACE_FREEZE_V45'
RESULT_SCHEMA = 'UDM_NATIVE_NAMESPACE_QUALIFICATION_V45'
SCOPE = 'NATIVE_NAMESPACE_ADMISSION_INFRASTRUCTURE_ONLY'
QUALIFIED = 'QUALIFIED_BOUNDED_NATIVE_NAMESPACE_ADMISSION_ONLY'
TESTS = ('test_native_admission_v45.py', 'test_native_execution_v45.py',
         'test_native_environment_v45.py', 'test_native_runtime_v45.py',
         'test_qualify_native_namespace_v45.py',
         'test_qualify_native_frontier_v45.py',
         'test_native_admission_v2.py', 'test_native_admission_v2_adversarial.py')
GATE_FILES = tuple(PREFIX+name for name in (
    'native_admission_v45.py', 'native_execution_v45.py', 'native_v45_test_support.py',
    'native_environment_v45.py', 'native_runtime_v45.py',
    'qualify_native_namespace_v45.py', 'qualify_native_frontier_v45.py', *TESTS,
    'archaeology/native-namespace-v45/prospective/curate_frontier.py',
    'archaeology/native-namespace-v45/prospective/prepare_records.py',
    'archaeology/native-namespace-v45/prospective/watch_actual_agent.py',
    'archaeology/native-namespace-v45/prospective/training_history_projection_v45.py',
    )) + ('.github/workflows/udm-native-namespace-v45.yml',)
canonical, sha, write, file_sha = original.canonical, original.sha, original.write, original.file_sha


def sealed_controls(root=None):
    """Check the complete independent seal before source or native operations."""
    root = Path(root) if root is not None else RECORDS/'control-freeze'
    seal = root/'FINAL_SEAL.json'
    if seal.is_symlink() or not seal.is_file() or file_sha(seal) != SEAL_SHA256:
        raise ValueError('independent control seal SHA256 differs')
    value = json.loads(seal.read_text())
    files = value.get('files', {})
    if (value.get('base_commit') != BASE or len(files) != 257
            or value.get('source_cases') != 30 or value.get('replay_controls') != 18
            or any(value.get(key) != 0 for key in ('collection_calls', 'native_calls',
                'git_mutations', 'product_mutations', 'repository_imports', 'task_queries'))):
        raise ValueError('independent control seal scope differs')
    actual = {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()}
    if actual != set(files)|{'FINAL_SEAL.json'} or any(path.is_symlink() for path in root.rglob('*')):
        raise ValueError('sealed control fixture topology/inventory differs')
    for name, expected in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or str(relative) != name:
            raise ValueError('noncanonical sealed control path')
        raw = (root/name).read_bytes()
        if sha(raw) != expected['sha256'] or len(raw) != expected['bytes']:
            raise ValueError('sealed control fixture bytes differ: '+name)
    index = json.loads((root/'FIXTURE_INDEX.json').read_text())
    for case in index['cases']:
        for variant, rows in case['source_variants'].items():
            for name, expected in rows.items():
                path = root/'fixtures'/case['id']/variant/name
                if expected['mode'] not in ('100644', '100755') or bool(path.stat().st_mode & 0o111) != (expected['mode'] == '100755'):
                    raise ValueError('sealed control fixture Git mode differs: '+str(path))
    return {'seal_sha256': SEAL_SHA256, 'files': files, 'source_cases': 30,
            'replay_controls': 18, 'baseline_commit': BASE}


def _preserve_baseline(before, after):
    if len(before) != 3011 or any(after.get(name) != row for name, row in before.items()):
        raise ValueError('complete 3011-file baseline bytes/modes changed')
    return len(before)


def _source(repo):
    value = original._source(repo)
    before = original._tree(repo, BASE)
    count = _preserve_baseline(before, value['source_tree'])
    if any(name not in value['files'] for name in GATE_FILES):
        raise ValueError('commit complete V45 source, runtime tests and workflow before freeze')
    index_name = PREFIX+'capability_index.json'
    raw = (Path(repo)/index_name).read_bytes()
    if raw != original._git(repo, 'show', BASE+':'+index_name):
        raise ValueError('original capability inventory bytes changed')
    inventory = json.loads(raw)
    if len(inventory.get('capabilities', [])) != 70:
        raise ValueError('original 70-entry capability inventory differs')
    return dict(value, baseline_commit=BASE, preserved_baseline_files=count,
                original_inventory={'path': index_name, 'entries': 70, 'sha256': sha(raw)})


def _check_source_identity(frozen, source):
    if any(frozen.get(key) != value for key, value in source.items()):
        raise ValueError('committed source identity differs from freeze')


def _runtime_freeze(paths):
    # Reuse every original profile/package/stdlib check. Only its historical
    # fixture-specific path is bound to the caller's exact supplied modern path.
    code = original._runtime_freeze.__code__
    old = '/workspace/qualification/native-authority-v41-profile-preparation/modern-runtime-final/venv/bin/python'
    if code.co_consts.count(old) != 1:
        raise ValueError('original runtime path binding changed')
    modern = next(profile for profile in json.loads(original.CATALOG.read_text())['profiles']
                  if profile['python_version'] == '3.12.14')
    code = code.replace(co_consts=tuple(paths[modern['id']] if value == old else value for value in code.co_consts))
    return FunctionType(code, dict(vars(original)), '_runtime_freeze')(paths)


def _controller_identity():
    import packaging
    import pytest
    from . import native_execution_v43 as worker
    from . import decisive_native_verify as original_v2
    if sys.version_info[:3] != (3, 12, 14) or pytest.__version__ != '8.3.5' or packaging.__version__ != '26.3':
        raise ValueError('controller requires exact Python 3.12.14 pytest 8.3.5 packaging 26.3')
    return {'interpreter': sys.executable, 'packaging_version': packaging.__version__,
            'environment': worker.environment_identity(sys.executable),
            'original_v2_environment': original_v2.environment_identity(sys.executable)}


def _control_tests():
    return [PREFIX+name for name in TESTS]


def _collect_controls(repo, out):
    import pytest
    from . import native_execution_v45 as worker
    inventory = original._PytestInventory()
    before, compilation = worker.attempt_snapshot(), worker.compilation_snapshot()
    previous = Path.cwd()
    try:
        os.chdir(repo)
        with Path(out).open('w') as stream, redirect_stdout(stream), redirect_stderr(stream):
            code = int(pytest.main(['-q', '-p', 'no:cacheprovider', '--import-mode=importlib',
                '--collect-only', *_control_tests()], plugins=[inventory]))
    finally:
        os.chdir(previous)
    if (code or not inventory.collected or len(set(inventory.collected)) != len(inventory.collected)
            or worker.attempt_snapshot() != before or worker.compilation_snapshot() != compilation):
        raise ValueError('actual qualification collection failed or executed native work')
    adversarial = PREFIX+'test_native_admission_v2_adversarial.py::'
    if sum(node.startswith(adversarial) for node in inventory.collected) != 27:
        raise ValueError('complete original 27-method adversarial inventory required')
    return inventory.collected


def _test_environment(runtime_paths):
    modern = next(value for key, value in runtime_paths.items() if '3.12.14' in key)
    legacy = next(value for key, value in runtime_paths.items() if '3.6.5' in key)
    os.environ.update(UDM_V45_MODERN_PYTHON=modern, UDM_V45_LEGACY_PYTHON=legacy,
                      PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')


def write_freeze(repo, out, runtime_paths):
    acceptance = sealed_controls()
    out = Path(out).absolute()
    if out.exists():
        raise ValueError('refusing to overwrite a source/runtime freeze')
    _test_environment(runtime_paths)
    with original.index_interval(repo, out.with_name(out.name+'.INDEX')):
        value = {'schema': FREEZE_SCHEMA, **_source(repo), 'acceptance': acceptance,
                 'controller': _controller_identity(), **_runtime_freeze(runtime_paths),
                 'control_collection': _collect_controls(repo, out.with_name(out.name+'.COLLECTION.log')),
                 'scope': SCOPE, 'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
        write(out, value)
    return value


def check_freeze(repo, path):
    acceptance = sealed_controls()
    frozen = json.loads(Path(path).read_text())
    if frozen.get('schema') != FREEZE_SCHEMA or frozen.get('acceptance') != acceptance:
        raise ValueError('wrong V45 freeze or sealed control pack changed')
    _check_source_identity(frozen, _source(repo))
    paths = {key: row['interpreter'] for key, row in frozen['runtimes'].items()}
    if frozen.get('controller') != _controller_identity():
        raise ValueError('selected controller executable/environment changed')
    if any(frozen.get(key) != value for key, value in _runtime_freeze(paths).items()):
        raise ValueError('original native executable/package/stdlib identity changed')
    _test_environment(paths)
    return frozen


class _RetainOriginalCases:
    """Original V43 cleanup-retention algorithm; original test bodies untouched."""
    def __init__(self, destination):
        self.destination = Path(destination)
        self.restore = None

    def pytest_collection_modifyitems(self, items):
        from . import test_native_admission_v2_adversarial as controls
        cls = controls.NativeAdmissionV2AdversarialTests
        original_setup = cls.setUp
        destination = self.destination
        def retained_setup(case):
            try:
                original_setup(case)
            finally:
                if hasattr(case, 'root'):
                    def retain():
                        target = destination/case.id()
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(case.root, target, symlinks=True)
                    case.addCleanup(retain)
        if any(getattr(item, 'cls', None) is cls for item in items):
            self.restore = (cls, original_setup)
            cls.setUp = retained_setup

    def pytest_unconfigure(self):
        if self.restore is not None:
            cls, setup = self.restore
            cls.setUp = setup


def _validate_contracts(record, frozen_nodes, tests):
    nodes, counts = record['collection'], record['junit']
    if (record['pytest_exit_code'] or nodes != frozen_nodes or len(set(nodes)) != len(nodes)
            or counts['tests'] != len(nodes) or counts['passed'] != len(nodes)
            or any(counts[key] for key in ('failures', 'errors', 'skipped'))
            or any(not any(node.startswith(name+'::') for node in nodes) for name in tests)):
        raise ValueError('frozen qualification collection/inventory or JUnit differs')
    reports = record['reports']
    if any(row.get('wasxfail') or row.get('outcome') != 'passed' for row in reports):
        raise ValueError('qualification report has failed/skipped/xfail execution')
    for phase in ('setup', 'call', 'teardown'):
        if [row['nodeid'] for row in reports if row['when'] == phase] != nodes:
            raise ValueError('qualification reports omit required execution phase')


def _artifact_path(root, path):
    path = Path(path)
    if (not path.is_absolute() or not path.resolve().is_relative_to(root)
            or path.is_symlink() or not path.is_file()):
        raise ValueError('child/native artifact path escapes retained evidence or is missing')
    return path


def _retained_files(root, filename):
    """Exclude tracked fixture source and Git internals from evidence discovery."""
    root = Path(root).resolve()
    for path in sorted(root.rglob(filename)):
        parents = list(path.relative_to(root).parents)[:-1]
        if any('.git' in parent.parts or (root/parent/'.git').exists() for parent in parents):
            continue
        yield path


def native_invocation_inventory(root):
    """Inventory actual controller packets, including refused/UNKNOWN launches.

    A complete raw invocation is not a suite-admission warrant. Positive verdicts
    require the separately authenticated collection certificate and receipt.
    """
    root = Path(root).resolve()
    rows, native, collection = [], 0, 0
    controller_fields = {'process_exit_code', 'timeout', 'source_mutations', 'unexpected_imports', 'costs'}
    for path in _retained_files(root, 'checked-report.json'):
        directory = path.parent
        row = {'path': str(directory), 'checked_report_sha256': file_sha(path),
               'classification': 'RAW_INVOCATION_ONLY_NO_ADMISSION_WARRANT'}
        try:
            checked = json.loads(path.read_text())
            costs = checked['costs']
            if any(type(costs.get(key)) is not int or costs[key] < 0 for key in ('native_calls', 'collection_calls')):
                raise ValueError('invalid raw native attempt counters')
            if costs['native_calls']+costs['collection_calls'] != 1:
                raise ValueError('raw packet does not describe one native invocation')
            native += costs['native_calls']; collection += costs['collection_calls']
            row.update(mode=checked.get('mode', 'UNKNOWN_PRODUCER_MODE'), costs=costs)
            packet = {}
            for name in ('report.json', 'checked-report.json', 'stdout.log', 'stderr.log', 'tracked-source-manifest.json'):
                sidecar = _artifact_path(root, directory/name)
                packet[name] = file_sha(sidecar)
            if (directory/'native.xml').is_file():
                packet['native.xml'] = file_sha(_artifact_path(root, directory/'native.xml'))
                row['junit'] = original._junit((directory/'native.xml').read_bytes())
            raw = json.loads((directory/'report.json').read_text())
            if raw != {key: value for key, value in checked.items() if key not in controller_fields}:
                raise ValueError('raw producer/controller packet relation differs')
            row.update(packet_sha256=packet, packet_status='PASS_RAW_CONTROLLER_BINDING')
        except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
            row.update(packet_status='UNKNOWN_PARTIAL_NATIVE_PACKET',
                       smallest_obstruction=type(error).__name__+': '+str(error))
        rows.append(row)
    return {'schema': 'UDM_V45_RETAINED_NATIVE_INVOCATION_INVENTORY',
            'invocations': rows, 'native_calls': native, 'collection_calls': collection,
            'unique_invocation_paths': len(rows),
            'boundary': 'Every retained controller checked-report outside tracked fixture source; UNKNOWN/partial packets retained. No raw-only entry grants admission. Launches without a checked report remain in controller/compiler attempt ledgers.'}


def _checked_delta(record, fields):
    before, after, delta = record['before'], record['after'], record['delta']
    for field in fields:
        values = (before[field], after[field], delta[field])
        if (any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values)
                or not math.isclose(after[field]-before[field], delta[field], rel_tol=1e-12, abs_tol=1e-12)):
            raise ValueError('child counter before/after/delta differs: '+field)
        if field.endswith('calls') or field == 'subprocess_attempts':
            if any(type(value) is not int for value in values):
                raise ValueError('child invocation counter is not an integer')


def child_attempts(root, required=True):
    """Bind child counters to captured stdout, compiler files and native outputs."""
    root = Path(root).resolve()
    paths = list(_retained_files(root, 'CHILD_NATIVE_ATTEMPTS.json'))
    if required and not paths:
        raise ValueError('required child native attempt summary is missing')
    descriptors = []
    for path in paths:
        path = _artifact_path(root, path)
        value = json.loads(path.read_text())
        if value.get('schema') != 'UDM_NATIVE_V45_CHILD_ATTEMPTS':
            raise ValueError('wrong child attempt summary schema')
        native, compiler = value['native_attempts'], value['compilation_attempts']
        _checked_delta(native, ('native_calls', 'collection_calls', 'subprocess_attempts'))
        _checked_delta(compiler, ('compilation_calls', 'compilation_seconds'))
        if (native['delta']['subprocess_attempts'] != native['delta']['native_calls']+native['delta']['collection_calls']
                or native['delta']['native_calls'] <= 0 or native['delta']['collection_calls'] <= 0
                or compiler['delta']['compilation_calls'] <= 0):
            raise ValueError('child native/compiler invocation accounting is incomplete')
        stdout = _artifact_path(root, path.with_name('RESTART_STDOUT.log'))
        stderr = _artifact_path(root, path.with_name('RESTART_STDERR.log'))
        report = json.loads(stdout.read_text())
        if (report.get('attempts') != value or report.get('status') != value.get('status')
                or report.get('native_calls') != native['delta']['native_calls']):
            raise ValueError('child summary differs from captured child stdout')
        records = compiler['after']['records']
        earlier = compiler['before']['records']
        if records[:len(earlier)] != earlier or not records[len(earlier):]:
            raise ValueError('child compiler ledger is missing or rewritten')
        for record in records[len(earlier):]:
            output = Path(record['output'])
            metadata = _artifact_path(root, output/'compilation.json')
            if json.loads(metadata.read_text()) != record:
                raise ValueError('child compiler ledger differs from retained compilation metadata')
            if file_sha(_artifact_path(root, output/'compiler.py')) != record['compiler_sha256']:
                raise ValueError('child compiler source bytes differ')
            payload = json.loads(_artifact_path(root, output/'original-input.json').read_text())
            if sha(canonical(payload).encode()) != record['input_sha256']:
                raise ValueError('child compiler original input differs')
            if record.get('report_sha256') and file_sha(_artifact_path(root, output/'expected-code.json')) != record['report_sha256']:
                raise ValueError('child compiler output differs')
            _artifact_path(root, output/'stdout.log'); _artifact_path(root, output/'stderr.log')
        if (sum(record['compilation_calls'] for record in records)-sum(record['compilation_calls'] for record in earlier)
                != compiler['delta']['compilation_calls']):
            raise ValueError('child compiler launch ledger differs from counters')
        if not math.isclose(sum(record['seconds'] for record in records)-sum(record['seconds'] for record in earlier),
                            compiler['delta']['compilation_seconds'], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('child compiler elapsed intervals differ from ledger')
        outputs = []
        for output in value['native_run_outputs']:
            if not Path(output).resolve().is_relative_to((path.parent/'restart').resolve()):
                raise ValueError('child native output is outside its exact restart output root')
            receipt_path = _artifact_path(root, Path(output)/'receipt.json')
            receipt = json.loads(receipt_path.read_text())
            if receipt.get('schema') != 'UDM_GENERIC_NATIVE_PYTEST_V45' or receipt.get('status') != value['status']:
                raise ValueError('child native output schema/status differs')
            costs = receipt['costs']
            if costs.get('native_calls') != 1 or costs.get('collection_calls') != 1:
                raise ValueError('child native receipt does not bind one execution and recollection')
            packet = {name: base64.b64decode(raw, validate=True) for name, raw in receipt['packet'].items()}
            if receipt['packet_sha256'] != {name: sha(raw) for name, raw in packet.items()}:
                raise ValueError('child native receipt packet hash differs')
            for name, raw in packet.items():
                if _artifact_path(root, Path(output)/'execution'/name).read_bytes() != raw:
                    raise ValueError('child native receipt packet differs from its exact output')
            outputs.append({'path': str(receipt_path), 'sha256': file_sha(receipt_path)})
        if len({row['path'] for row in outputs}) != native['delta']['native_calls']:
            raise ValueError('child native output count differs from actual launch counters')
        descriptors.append({'path': str(path), 'sha256': file_sha(path), 'summary': value,
            'stdout': {'path': str(stdout), 'sha256': file_sha(stdout)},
            'stderr': {'path': str(stderr), 'sha256': file_sha(stderr)}, 'native_outputs': outputs})
    return descriptors


def known_attempt_totals(native, compiler, children):
    totals = {key: native.get(key, 0) for key in ('native_calls', 'collection_calls', 'subprocess_attempts')}
    totals.update({key: compiler.get(key, 0) for key in ('compilation_calls', 'compilation_seconds')})
    for descriptor in children:
        child = descriptor['summary']
        for key in ('native_calls', 'collection_calls', 'subprocess_attempts'):
            totals[key] += child['native_attempts']['delta'][key]
        for key in ('compilation_calls', 'compilation_seconds'):
            totals[key] += child['compilation_attempts']['delta'][key]
    totals.update(wall_intervals_additive=False, child_processes=len(children),
                  boundary='Known V45 main-controller plus authenticated child call counts; compiler durations are elapsed compiler-process intervals, not an additional end-to-end wall duration. Original V2 regression calls are separately visible in the raw invocation inventory. Other lifecycle costs remain UNKNOWN.')
    return totals


def audit_native_packets(root, frozen):
    """Apply the original raw packet/status reconstruction to genuine V45 rows.

    Frozen tests explicitly enumerate genuine evidence. Deliberately tampered
    negative packets remain archived but cannot masquerade as successful rows.
    """
    root = Path(root).resolve()
    entries = {}
    manifests = list(_retained_files(root, 'V45_NATIVE_EVIDENCE.json'))
    for manifest in manifests:
        value = json.loads(manifest.read_text())
        if manifest.is_symlink() or value.get('schema') != 'UDM_NATIVE_V45_TEST_EVIDENCE':
            raise ValueError('invalid genuine native evidence manifest')
        for row in value['records']:
            path = Path(row['path'])
            if not path.is_absolute():
                path = manifest.parent/path
            if (not path.resolve().is_relative_to(root) or path.is_symlink()
                    or not path.is_file() or file_sha(path) != row['sha256']):
                raise ValueError('genuine native evidence bytes/path differ')
            if row['role'] not in ('certificate', 'receipt', 'independent_reexecution'):
                raise ValueError('unrecognized genuine native evidence role')
            entries[(row['role'], str(path))] = json.loads(path.read_text())
    # Include retained V45 inherited adversarial and original V2 regression
    # packets, even where the frozen tests supplied no success manifest.
    for filename, role in (('admission-certificate.json', 'certificate'), ('receipt.json', 'retained_receipt')):
        for path in _retained_files(root, filename):
            if any(name == str(path) for _, name in entries):
                continue
            value = json.loads(path.read_text())
            if value.get('schema') in ('UDM_NATIVE_ADMISSION_CERTIFICATE_V2', 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42',
                    'UDM_NATIVE_ADMISSION_CERTIFICATE_V43', 'UDM_NATIVE_ADMISSION_CERTIFICATE_V45',
                    'UDM_GENERIC_NATIVE_PYTEST_V2', 'UDM_GENERIC_NATIVE_PYTEST_V42',
                    'UDM_GENERIC_NATIVE_PYTEST_V43', 'UDM_GENERIC_NATIVE_PYTEST_V45'):
                entries[(role, str(path))] = value
    raw_inventory = native_invocation_inventory(root)
    raw_paths = {row['path']: row for row in raw_inventory['invocations']}
    certificates, receipts = {}, []
    for (role, name), value in entries.items():
        if role != 'certificate':
            continue
        version = value.get('schema', '').rsplit('_', 1)[-1]
        if version not in ('V2', 'V42', 'V43', 'V45') or not value.get('schema', '').startswith('UDM_NATIVE_ADMISSION_CERTIFICATE_'):
            raise ValueError('native certificate schema differs')
        packet = {key: base64.b64decode(raw, validate=True) for key, raw in value['packet'].items()}
        if value['packet_sha256'] != {key: sha(raw) for key, raw in packet.items()}:
            raise ValueError('native certificate packet hashes differ')
        environments = [row['environment'] for row in frozen['profile_identities'].values()]
        if version == 'V2':
            environments.append(frozen['controller']['original_v2_environment'])
        if value['environment'] not in environments:
            raise ValueError('native certificate environment differs from original profiles')
        runner = PREFIX+'native_execution_'+version.lower()+'.py'
        if value.get('runner_sha256') != frozen['files'][runner]:
            raise ValueError('native certificate runner differs from frozen original/versioned source')
        data = json.loads(packet['checked-report.json'])
        if (value['collection'] != {key: data[key] for key in value['collection']}
                or data['mode'] != 'collect' or data['process_exit_code'] != 0
                or data['timeout'] or data.get('collection_errors') or data.get('deselected_test_nodes')):
            raise ValueError('native certificate collection is incomplete')
        for key, raw in packet.items():
            sidecar = Path(name).parent/key
            if sidecar.is_symlink() or not sidecar.is_file() or sidecar.read_bytes() != raw:
                raise ValueError('collection packet sidecar differs')
        if str(Path(name).parent) not in raw_paths:
            raise ValueError('certificate lacks retained raw invocation inventory')
        certificates[sha(canonical(value).encode())] = value
    passes = failures = replays = 0
    counted_paths = set()
    for (role, name), value in entries.items():
        if role not in ('receipt', 'independent_reexecution', 'retained_receipt'):
            continue
        version = value.get('schema', '').rsplit('_', 1)[-1]
        if version not in ('V2', 'V42', 'V43', 'V45') or not value.get('schema', '').startswith('UDM_GENERIC_NATIVE_PYTEST_'):
            raise ValueError('native receipt schema differs')
        if 'certificate_sha256' not in value:
            raise ValueError('native receipt certificate binding missing: '+name)
        certificate = certificates.get(value['certificate_sha256'])
        if certificate is None:
            raise ValueError('genuine receipt lacks genuine retained certificate')
        if value['runner_sha256'] != frozen['files'][PREFIX+'native_execution_'+version.lower()+'.py']:
            raise ValueError('native receipt runner differs from committed worker')
        packet = {key: base64.b64decode(raw, validate=True) for key, raw in value['packet'].items()}
        if value['packet_sha256'] != {key: sha(raw) for key, raw in packet.items()}:
            raise ValueError('native receipt packet hashes differ')
        data, raw_report = json.loads(packet['checked-report.json']), json.loads(packet['report.json'])
        fields = {'process_exit_code', 'timeout', 'source_mutations', 'unexpected_imports', 'costs'}
        if raw_report != {key: item for key, item in data.items() if key not in fields}:
            raise ValueError('native checked report differs from raw producer report')
        for key, raw in packet.items():
            sidecar = Path(name).parent/'execution'/key
            if sidecar.is_symlink() or not sidecar.is_file() or sidecar.read_bytes() != raw:
                raise ValueError('native execution packet sidecar differs')
        counts = original._junit(packet.get('native.xml', b'<testsuite/>'))
        status = original._inferred_status(data, counts, certificate['collection'])
        if data != value['execution'] or counts != value['junit'] or status != value['status']:
            raise ValueError('native outcome differs from raw protected execution')
        invocation = str(Path(name).parent/'execution')
        if invocation not in raw_paths:
            raise ValueError('receipt lacks retained raw invocation inventory')
        if role in ('receipt', 'independent_reexecution') and status not in ('PASS_NATIVE', 'FAIL_NATIVE'):
            raise ValueError('adversarial/UNKNOWN packet mislabeled as genuine native evidence')
        if invocation in counted_paths:
            raise ValueError('duplicate receipt roles cannot inflate one actual native invocation')
        counted_paths.add(invocation)
        if version == 'V45':
            passes += status == 'PASS_NATIVE'
            failures += status == 'FAIL_NATIVE'
            replays += role == 'independent_reexecution' and status in ('PASS_NATIVE', 'FAIL_NATIVE')
        receipts.append({'path': name, 'invocation_path': invocation, 'schema': value['schema'],
                         'role': role, 'status': status, 'junit': counts})
    if not manifests or not passes or not failures or not replays:
        raise ValueError('missing actual V45 native PASS/FAIL or independent replay')
    return {'schema': 'UDM_V45_RAW_NATIVE_PACKET_AUDIT', 'status': 'PASS_BOUNDED_RAW_NATIVE_PACKETS',
            'certificates': len(certificates),
            'native_passes': passes, 'native_failures': failures, 'independent_replays': replays,
            'receipts': receipts, 'manifest_paths': [str(path) for path in manifests],
            'retained_invocation_inventory': raw_inventory,
            'unbound_invocation_paths': sorted(set(raw_paths)-counted_paths-
                {str(Path(name).parent) for role, name in entries if role == 'certificate'}),
            'boundary': 'Every retained raw controller invocation is inventoried, including UNKNOWN/unbound negatives. Original packet/status reconstruction authenticates complete retained V2/V42/V43/V45 certificates and receipts. Positive counters count unique V45 execution paths only. Complete compiler/source sidecars remain archived for independent declaration-authority inspection.'}


def _validate_claims(result):
    if (result.get('scope') != SCOPE or result.get('prospective_task_sources_accessed') is not False
            or result.get('coding_agent_executed') is not False
            or result.get('verdicts') != {f'G{i}': 'UNKNOWN' for i in range(2, 7)}):
        raise ValueError('bounded admission scope requires scientific UNKNOWN verdicts')
    if result.get('index_audit', {}).get('changes') != []:
        raise ValueError('source index changed or its audit is missing')
    native = result.get('native_attempts', {}).get('delta', {})
    if any(type(native.get(key)) is not int or native[key] <= 0 for key in ('native_calls', 'collection_calls')):
        raise ValueError('actual native/collection attempt accounting missing')
    compiler = result.get('compilation_attempts', {}).get('delta', {})
    if type(compiler.get('compilation_calls')) is not int or compiler['compilation_calls'] <= 0:
        raise ValueError('actual declaration compiler attempt accounting missing')
    audit = result.get('raw_native_audit', {})
    if any(type(audit.get(key)) is not int or audit[key] <= 0
           for key in ('native_passes', 'native_failures', 'independent_replays')):
        raise ValueError('actual native PASS/FAIL or independent replay missing')
    if any(result.get(key, {}).get('scope') != 'MAIN_CONTROLLER_CONTEXT_ONLY'
           for key in ('native_attempts', 'compilation_attempts')):
        raise ValueError('main native/compiler counters lack their exact process scope')
    children = result.get('child_attempts')
    if not isinstance(children, list) or not children:
        raise ValueError('authenticated child attempt descriptors are missing')
    for descriptor in children:
        summary = descriptor.get('summary', {})
        if summary.get('schema') != 'UDM_NATIVE_V45_CHILD_ATTEMPTS':
            raise ValueError('child summary schema differs')
        child_native = summary.get('native_attempts', {}).get('delta', {})
        child_compiler = summary.get('compilation_attempts', {}).get('delta', {})
        if (any(type(child_native.get(key)) is not int or child_native[key] <= 0
                for key in ('native_calls', 'collection_calls', 'subprocess_attempts'))
                or child_native['subprocess_attempts'] != child_native['native_calls']+child_native['collection_calls']
                or type(child_compiler.get('compilation_calls')) is not int or child_compiler['compilation_calls'] <= 0
                or type(child_compiler.get('compilation_seconds')) not in (int, float)
                or not math.isfinite(child_compiler['compilation_seconds']) or child_compiler['compilation_seconds'] < 0):
            raise ValueError('child native/compiler counter claims are incomplete')
        artifacts = [descriptor, descriptor.get('stdout', {}), descriptor.get('stderr', {})]
        outputs = descriptor.get('native_outputs')
        if not isinstance(outputs, list) or not outputs:
            raise ValueError('child native output descriptors are missing')
        artifacts.extend(outputs)
        if any(not isinstance(row.get('path'), str) or not row['path']
               or not isinstance(row.get('sha256'), str) or len(row['sha256']) != 64
               or any(char not in '0123456789abcdef' for char in row['sha256']) for row in artifacts):
            raise ValueError('child artifact path/SHA256 binding is missing')
    expected = known_attempt_totals(native, compiler, children)
    known = result.get('known_attempt_totals', {})
    if (known.get('wall_intervals_additive') is not False
            or any(known.get(key) != expected[key] or type(known.get(key)) is not type(expected[key])
                   for key in ('native_calls', 'collection_calls', 'subprocess_attempts',
                               'compilation_calls', 'compilation_seconds', 'child_processes'))):
        raise ValueError('known attempt totals disagree with exact main/child accounting')


def qualify(repo, freeze_path, out, components):
    import pytest
    repo, out = Path(repo).resolve(), Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    result = {'schema': RESULT_SCHEMA, 'status': 'UNKNOWN_NATIVE_NAMESPACE_QUALIFICATION',
        'scope': SCOPE, 'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
        'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
    started, worker, before, compilation = time.monotonic(), None, {}, {}
    previous_tempdir, previous_tmpdir = tempfile.tempdir, os.environ.get('TMPDIR')
    previous_inherited = os.environ.get('UDM_V45_CONTROL_EVIDENCE_ROOT')
    try:
        result['phase'] = 'sealed-controls'
        sealed_controls()
        temporary = out/'default-temporaries'
        temporary.mkdir()
        tempfile.tempdir = str(temporary)
        os.environ['TMPDIR'] = str(temporary)
        os.environ['UDM_V45_CONTROL_EVIDENCE_ROOT'] = str(temporary/'inherited-v45-evidence')
        from . import native_execution_v45 as worker
        before, compilation = worker.attempt_snapshot(), worker.compilation_snapshot()
        with original.index_interval(repo, out/'index-interval'):
            result['phase'] = 'source-controller-native-freeze'
            frozen = check_freeze(repo, freeze_path)
            result.update(source_commit=frozen['source_commit'], freeze=frozen)
            component_source = original.component_inventory(components, out/'components-before')
            inventory = original._PytestInventory()
            previous = Path.cwd()
            result['phase'] = 'declared-engineering-tests'
            try:
                os.chdir(repo)
                with (out/'stdout.log').open('w') as stdout, (out/'stderr.log').open('w') as stderr:
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        code = int(pytest.main(['-q', '-p', 'no:cacheprovider', '--import-mode=importlib',
                            '--basetemp='+str(out/'pytest'), '--junitxml='+str(out/'contracts.xml'),
                            *_control_tests()], plugins=[inventory, _RetainOriginalCases(out/'original-adversarial-cases')]))
            finally:
                os.chdir(previous)
            result['contracts'] = {'collection': inventory.collected, 'reports': inventory.reports,
                'junit': original._junit((out/'contracts.xml').read_bytes()), 'pytest_exit_code': code}
            write(out/'PYTEST_INVENTORY.json', result['contracts'])
            _validate_contracts(result['contracts'], frozen['control_collection'], _control_tests())
            result['phase'] = 'independent-raw-native-audit'
            result['raw_native_audit'] = audit_native_packets(out, frozen)
            write(out/'RAW_NATIVE_AUDIT.json', result['raw_native_audit'])
            result['child_attempts'] = child_attempts(out)
            result['phase'] = 'post-source-runtime-component-audit'
            if original.component_inventory(components, out/'components-after') != component_source:
                raise ValueError('original pinned component source changed')
            check_freeze(repo, freeze_path)
        result['index_audit'] = json.loads((out/'index-interval/AUDIT.json').read_text())
        after, compiled = worker.attempt_snapshot(), worker.compilation_snapshot()
        result['native_attempts'] = {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY', 'before': before, 'after': after,
            'delta': {key: after[key]-before[key] for key in after if type(after[key]) in (int, float)}}
        result['compilation_attempts'] = {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY', 'before': compilation, 'after': compiled,
            'delta': {key: compiled[key]-compilation[key] for key in compiled if type(compiled[key]) in (int, float)}}
        result['known_attempt_totals'] = known_attempt_totals(result['native_attempts']['delta'],
            result['compilation_attempts']['delta'], result['child_attempts'])
        _validate_claims(result)
        result.update(status=QUALIFIED, phase='qualified-bounded-admission-only')
    except (Exception, KeyboardInterrupt) as error:
        result['smallest_obstruction'] = type(error).__name__+': '+str(error)
    finally:
        if worker is not None:
            after, compiled = worker.attempt_snapshot(), worker.compilation_snapshot()
            result['native_attempts'] = {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY', 'before': before, 'after': after,
                'delta': {key: after[key]-before.get(key, 0) for key in after if type(after[key]) in (int, float)}}
            result['compilation_attempts'] = {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY', 'before': compilation, 'after': compiled,
                'delta': {key: compiled[key]-compilation.get(key, 0) for key in compiled if type(compiled[key]) in (int, float)}}
            try:
                result['child_attempts'] = child_attempts(out)
            except Exception as error:
                result['child_attempts_obstruction'] = type(error).__name__+': '+str(error)
                result['unvalidated_child_summaries'] = [
                    {'path': str(path), 'sha256': file_sha(path), 'summary': json.loads(path.read_text())}
                    for path in _retained_files(out, 'CHILD_NATIVE_ATTEMPTS.json') if path.is_file() and not path.is_symlink()]
            result['known_attempt_totals'] = known_attempt_totals(result['native_attempts']['delta'],
                result['compilation_attempts']['delta'], result.get('child_attempts', []))
        if (out/'index-interval/AUDIT.json').is_file():
            result['index_audit'] = json.loads((out/'index-interval/AUDIT.json').read_text())
        result['wall_seconds'] = time.monotonic()-started
        try:
            result['retained_invocation_inventory'] = native_invocation_inventory(out)
            write(out/'NATIVE_INVOCATION_INVENTORY.json', result['retained_invocation_inventory'])
        except Exception as error:
            result['retained_invocation_inventory_obstruction'] = type(error).__name__+': '+str(error)
        result['cost_boundary'] = 'Main controller ContextVars and authenticated child summaries are separate. Known V45-controller/child call counts are aggregated; original V2 regression launches are separately inventoried from raw packets. Nested/overlapping wall intervals are not additive. Raw-only/failed artifacts are retained even where their inventory has an explicit obstruction; complete engineering/model lifecycle cost remains UNKNOWN.'
        write(out/'RESULT.json', result)
        tempfile.tempdir = previous_tempdir
        if previous_tmpdir is None:
            os.environ.pop('TMPDIR', None)
        else:
            os.environ['TMPDIR'] = previous_tmpdir
        if previous_inherited is None:
            os.environ.pop('UDM_V45_CONTROL_EVIDENCE_ROOT', None)
        else:
            os.environ['UDM_V45_CONTROL_EVIDENCE_ROOT'] = previous_inherited
    return result


# Keep the original complete source/component/raw-output archive algorithm.
_archive_code = original.archive.__code__
_archive_code = _archive_code.replace(co_consts=tuple(value.replace(
    'EXPERIMENT_INTERFACE_V43_EVIDENCE', 'NATIVE_NAMESPACE_V45_EVIDENCE').replace(
    'UDM_EXPERIMENT_INTERFACE_ARCHIVE_MANIFEST_V43', 'UDM_NATIVE_NAMESPACE_ARCHIVE_MANIFEST_V45')
    if isinstance(value, str) else value for value in _archive_code.co_consts))
archive = FunctionType(_archive_code, dict(vars(original)), 'archive', original.archive.__defaults__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--runtimes', type=Path)
    parser.add_argument('--write-freeze', action='store_true')
    parser.add_argument('--archive', action='store_true')
    parser.add_argument('--preparation', type=Path, action='append', default=[])
    parser.add_argument('--components', type=Path, default=Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')))
    args = parser.parse_args()
    if args.archive:
        try:
            sealed_controls()
        except Exception as error:
            # Preserve source and every negative artifact even if qualification
            # refused the seal. Archival grants no admission or native authority.
            write(args.out/'SEALED_CONTROL_ARCHIVE_OBSTRUCTION.json',
                  {'status': 'UNKNOWN_SEALED_CONTROLS', 'smallest_obstruction': type(error).__name__+': '+str(error)})
        result = archive(args.repo, args.out, args.freeze, args.preparation, args.components)
    elif args.write_freeze:
        if args.runtimes is None:
            parser.error('--runtimes is required for source/runtime freeze')
        result = write_freeze(args.repo, args.out, json.loads(args.runtimes.read_text()))
    else:
        if args.freeze is None:
            parser.error('--freeze is required for qualification')
        result = qualify(args.repo, args.freeze, args.out, args.components)
    print(canonical({key: result[key] for key in ('schema', 'status', 'source_commit', 'smallest_obstruction') if key in result}))
    return int(result.get('status', '').startswith('UNKNOWN_'))


if __name__ == '__main__':
    raise SystemExit(main())
