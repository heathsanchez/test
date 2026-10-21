"""Generated-source transport over the original independently replayed worker.

Tracked source and assertion authority remain V42.  A separate executable view
adds only independently rebuilt, declared generated modules.  This finite
authority check retains the original trusted-test execution ceiling; it is not
a hostile-process sandbox.
"""
from __future__ import annotations

import copy
from contextvars import ContextVar
import inspect
import json
import math
from pathlib import Path, PurePosixPath
import stat
import time
from types import FunctionType, SimpleNamespace

from . import native_execution_v42 as previous
from . import native_build_v43 as build

frozen = previous.frozen
source = previous.source
admission = previous.admission
original = previous.original
SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V43'
CERTIFICATE_SCHEMA = 'UDM_NATIVE_ADMISSION_CERTIFICATE_V43'
POLICY_SCHEMA = 'UDM_NATIVE_EXECUTION_POLICY_V43'
ADMISSION_REVISION = '4.3'
canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())
_PREVIOUS_SHA256 = 'da4a4b19a988145d690a288b7714cd1f6d2a24f021811059de679e6c2b585d53'
_BUILDER_SHA256 = '20f88ce36baa7e01c7e601c7840f72b9423a6ab04d093d35e36217d3049b8460'
_CONTRACT_KEYS = {'schema', 'repository', 'repo_path', 'commit', 'git_tree',
    'tracked_tree_sha256', 'file_count', 'interpreter', 'environment_sha256',
    'protocol_binding', 'horizon_seconds', 'generated_build'}
_build_records = ContextVar('udm_native_v43_build_records', default=())


def _runner_hash():
    previous._runner_hash()
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_V43_VERIFIER_SOURCE_MUTATION')
    if sha256(Path(previous.__file__).read_bytes()) != _PREVIOUS_SHA256:
        raise ValueError('UNKNOWN_V43_FROZEN_NATIVE_SOURCE_MUTATION')
    if sha256(Path(build.__file__).read_bytes()) != _BUILDER_SHA256:
        raise ValueError('UNKNOWN_V43_BUILD_SOURCE_MUTATION')
    build._guard()
    return _LOADED_SOURCE_SHA256


environment_identity = previous.environment_identity
runtime_identity = previous.runtime_identity
host_stdlib = previous.host_stdlib
attempt_snapshot = previous.attempt_snapshot
_BOOTSTRAP, _PLUGINS, _ENVIRONMENT = previous._BOOTSTRAP, previous._PLUGINS, previous._ENVIRONMENT


def build_snapshot():
    """Retain every verification attempt, including refusals before a warrant.

    Actual build charges are the builder's receipts/counters.  A verification
    attempt is deliberately not relabeled as a successfully launched build.
    """
    result = {'verification_attempts': len(_build_records.get()),
              'records': copy.deepcopy(list(_build_records.get()))}
    counter = getattr(build, 'attempt_snapshot', None)
    if counter is not None:
        result['builder_attempts'] = copy.deepcopy(counter())
    return result


def _tracked(files):
    return getattr(files, 'tracked_files', files)


class ExecutableView(dict):
    """Supplemental execution bytes, never a replacement tracked inventory."""
    def __init__(self, files, manifest, generated, authority, policy):
        super().__init__(files)
        self.update(generated)
        self.tracked_files = files
        self.manifest = copy.deepcopy(manifest)
        self.identity = copy.deepcopy(getattr(files, 'identity', None))
        self.generated = dict(generated)
        self.authority = copy.deepcopy(authority)
        self.policy = copy.deepcopy(policy)
        self.parent_inventory = {}
        self.leaf_inventory = {}


def _context(contract, authority, policy):
    _runner_hash()
    if not isinstance(contract, dict) or set(contract) != _CONTRACT_KEYS or contract['schema'] != SCHEMA:
        raise ValueError('wrong versioned V43 native contract')
    if not isinstance(policy, dict) or policy.get('schema') != POLICY_SCHEMA:
        raise ValueError('wrong external V43 native policy')
    projected = {key: value for key, value in contract.items() if key != 'generated_build'}
    projected['schema'] = previous.SCHEMA
    projected_policy = dict(policy, schema=previous.POLICY_SCHEMA)
    files, manifest, environment, plugins = previous._context(projected, authority, projected_policy)
    if contract['generated_build'] is None:
        return files, manifest, environment, plugins
    generated = build.read_generated(contract, authority, policy, contract['generated_build'])
    _validate_generated(files, manifest, generated)
    return ExecutableView(files, manifest, generated, authority, policy), manifest, environment, plugins


def _validate_generated(files, manifest, generated):
    tracked = _tracked(files)
    if (not isinstance(generated, dict) or not generated
            or set(generated) != set(build.declared_outputs(tracked))
            or set(generated) & set(tracked)
            or any(not isinstance(raw, bytes) for raw in generated.values())):
        raise ValueError('UNKNOWN_V43_GENERATED_EXECUTABLE_SET')
    source.safe_overlay(generated, manifest, tracked)


def _verify_executable_view(contract, files, manifest, out):
    if contract['generated_build'] is None:
        if isinstance(files, ExecutableView):
            raise ValueError('UNKNOWN_V43_UNBOUND_GENERATED_VIEW')
        return files
    if not isinstance(files, ExecutableView):
        raise ValueError('UNKNOWN_V43_MISSING_GENERATED_VIEW')
    started = time.monotonic()
    record = {'native_output': str(out), 'status': 'UNKNOWN',
              'verification_attempts': 1}
    counter = getattr(build, 'attempt_snapshot', None)
    if counter is not None:
        record['builder_attempts_before'] = copy.deepcopy(counter())
    try:
        generated, receipt = build.verify(contract, files.authority, files.policy,
            contract['generated_build'], out/'generated-build-verification')
        record['receipt'] = copy.deepcopy(receipt)
        _validate_generated(files, manifest, generated)
        if generated != files.generated:
            raise ValueError('UNKNOWN_V43_GENERATED_REBUILD_DIFFERS')
        _runner_hash()
        record['status'] = 'VERIFIED_GENERATED_BUILD'
        view = ExecutableView(files.tracked_files, manifest, generated, files.authority, files.policy)
        return view
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        record['seconds'] = time.monotonic() - started
        if counter is not None:
            record['builder_attempts_after'] = copy.deepcopy(counter())
        _build_records.set(_build_records.get() + (copy.deepcopy(record),))
        (out/'generated-build-verification.json').write_text(canonical(record)+'\n')


def _directory_identity(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink():
        raise ValueError('UNKNOWN_V43_GENERATED_PARENT_TOPOLOGY')
    return (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))


def _materialize_generated(world, files):
    if not isinstance(files, ExecutableView):
        return
    _validate_generated(files, files.manifest, files.generated)
    for name, raw in sorted(files.generated.items()):
        source._parents(world, name)
        path = world/name
        path.parent.mkdir(parents=True, exist_ok=True)
        source._parents(world, name)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o644)
        info = path.lstat()
        files.leaf_inventory[name] = (info.st_dev, info.st_ino, info.st_nlink)
    parents = {''}
    for name in files.generated:
        parents.update(parent.as_posix() for parent in PurePosixPath(name).parents if str(parent) != '.')
    files.parent_inventory = {name: _directory_identity(world/name) for name in sorted(parents)}


def _validate_executable_materialized(world, files, manifest, candidate, data):
    try:
        mutations = source.validate_materialized(world, _tracked(files), manifest,
            candidate=candidate, skip_bytecode=True)
    except (OSError, ValueError, RuntimeError):
        mutations = ['<tracked-source-root>']
    if isinstance(files, ExecutableView):
        for name, identity in files.parent_inventory.items():
            try:
                if _directory_identity(world/name) != identity:
                    mutations.append(name or '<generated-root>')
            except (OSError, ValueError, RuntimeError):
                mutations.append(name or '<generated-root>')
        for name, raw in files.generated.items():
            try:
                source._parents(world, name)
                path = world/name
                info = path.lstat()
                if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o644
                        or (info.st_dev, info.st_ino, info.st_nlink) != files.leaf_inventory[name]
                        or path.resolve(strict=True) != path or path.read_bytes() != raw):
                    mutations.append(name)
            except (OSError, ValueError, RuntimeError):
                mutations.append(name)
        for row in data.get('plugin_manifest', []):
            if isinstance(row, dict) and row.get('path') in files.generated:
                mutations.append('generated-pytest-plugin:' + row['path'])
    return sorted(set(mutations))


def _validate_candidate(candidate, files):
    return admission.validate_candidate(candidate, _tracked(files))


def _typed_roots(files):
    return previous._typed_roots(_tracked(files))


_admission = SimpleNamespace(**dict(vars(admission), validate_candidate=_validate_candidate))
_controller_globals = dict(previous._controller_globals, SCHEMA=SCHEMA,
    CERTIFICATE_SCHEMA=CERTIFICATE_SCHEMA, POLICY_SCHEMA=POLICY_SCHEMA,
    ADMISSION_REVISION=ADMISSION_REVISION, admission=_admission,
    _runner_hash=_runner_hash, _context=_context, _typed_roots=_typed_roots,
    _tracked=_tracked, _verify_executable_view=_verify_executable_view,
    _materialize_generated=_materialize_generated,
    _validate_executable_materialized=_validate_executable_materialized)

# Only source transport sites change.  Collection, assertion, outcome and receipt
# algorithms below retain the original V2 code objects and private globals.
_run_source = inspect.getsource(frozen._run)
_TRANSPORT_SITES = (
    ('    out.mkdir(parents=True);started=time.monotonic();expected=dict(files)\n',
     '    out.mkdir(parents=True)\n'
     '    files=_verify_executable_view(contract,files,manifest,out)\n'
     '    started=time.monotonic();expected=dict(files)\n'),
    ("        for name,raw in files.items():\n"
     "            if name.endswith(('.pyc','.pyo')):expected.pop(name,None);continue\n"
     "            p=world/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)\n"
     "        for row in manifest:\n"
     "            if row['path'] in expected:(world/row['path']).chmod(int(row['mode'],8)&0o777)\n",
     "        source.validate_candidate(candidate,_tracked(files),manifest)\n"
     "        source.materialize(world,_tracked(files),manifest,skip_bytecode=True)\n"
     "        _materialize_generated(world,files)\n"
     "        expected={name:raw for name,raw in files.items() if not name.endswith(('.pyc','.pyo'))}\n"),
    ("        mutations=[name for name,raw in expected.items() if not (world/name).is_file()\n"
     "            or (world/name).resolve()!=world/name or (world/name).read_bytes()!=raw]\n",
     "        mutations=_validate_executable_materialized(world,files,manifest,candidate,data)\n"),
    ('canonical(_roots(files))', 'canonical(_typed_roots(files))'),
)
for _before, _after in _TRANSPORT_SITES:
    if _run_source.count(_before) != 1:
        raise ValueError('UNKNOWN_V43_NATIVE_TRANSPORT_BINDING_SITE')
    _run_source = _run_source.replace(_before, _after)
exec(compile(_run_source, __file__+':generated-native-transport', 'exec'), _controller_globals)
_controller_run = _controller_globals['_run']

for _name in ('_roots', '_collection', '_binding', 'collect', 'validate_certificate',
              '_status', 'verify', 'validate_receipt'):
    _function = getattr(frozen, _name)
    _bound = FunctionType(_function.__code__, _controller_globals, _name,
                          _function.__defaults__, _function.__closure__)
    _bound.__kwdefaults__ = _function.__kwdefaults__
    globals()[_name] = _controller_globals[_name] = _bound
_controller_validate_certificate = validate_certificate
_controller_validate_receipt = validate_receipt


def validate_certificate(contract, authority, certificate, *, policy, output_dir=None):
    """Run the original validator, then expose its actual separate build charge."""
    result = _controller_validate_certificate(contract, authority, certificate,
        policy=policy, output_dir=output_dir)
    if contract['generated_build'] is not None:
        output = str(Path(result['independent_recollection']['output']).absolute())
        record = next((item for item in reversed(_build_records.get())
            if item['native_output'] == output and item['status'] == 'VERIFIED_GENERATED_BUILD'), None)
        if record is None:
            raise ValueError('UNKNOWN_V43_MISSING_BUILD_ACCOUNTING')
        result['independent_recollection']['build_verification'] = copy.deepcopy(record)
    return result


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _retained_json(path):
    path = Path(path).absolute()
    if path.resolve() != path or not path.is_file() or path.is_symlink():
        raise ValueError('UNKNOWN_V43_MISSING_BUILD_ACCOUNTING_ARTIFACT')
    return json.loads(path.read_bytes())


def _validate_build_accounting(contract, collection):
    """Validate controller-local accounting, separately from native authority.

    Retained timings are local measurements, not a signature or hostile-host
    attestation.  Fresh replay reports its own measured charges independently.
    """
    try:
        expected = {'output', 'costs'}
        if contract['generated_build'] is not None:
            expected.add('build_verification')
        if not isinstance(collection, dict) or set(collection) != expected:
            raise ValueError('UNKNOWN_V43_BUILD_ACCOUNTING_FIELDS')
        if contract['generated_build'] is None:
            return
        record = collection['build_verification']
        if (not isinstance(record, dict) or set(record) != {'native_output', 'status',
                'verification_attempts', 'seconds', 'receipt', 'builder_attempts_before', 'builder_attempts_after'}
                or record['status'] != 'VERIFIED_GENERATED_BUILD'
                or type(record['verification_attempts']) is not int or record['verification_attempts'] != 1
                or not _number(record['seconds'])
                or record['native_output'] != str(Path(collection['output']).absolute())):
            raise ValueError('UNKNOWN_V43_BUILD_ACCOUNTING_RECORD')
        output = Path(record['native_output'])
        if _retained_json(output/'generated-build-verification.json') != record:
            raise ValueError('UNKNOWN_V43_BUILD_ACCOUNTING_SIDECAR_DIFFERS')
        receipt = record['receipt']
        evidence = contract['generated_build']
        if (not isinstance(receipt, dict) or set(receipt) != {'schema', 'status', 'evidence_sha256',
                'binding', 'build', 'costs'}
                or receipt['schema'] != 'UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43'
                or receipt['status'] != 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
                or receipt['evidence_sha256'] != fingerprint(evidence)
                or receipt['binding'] != evidence['binding']
                or _retained_json(output/'generated-build-verification/verification.json') != receipt):
            raise ValueError('UNKNOWN_V43_BUILD_VERIFICATION_BINDING')
        report, costs = receipt['build'], receipt['costs']
        base_costs = {'build_calls', 'build_seconds', 'command_calls', 'total_seconds', 'wheel_bytes'}
        if (not isinstance(report, dict) or set(report) != {'schema', 'status', 'binding',
                'recipe_sha256', 'builder_sha256', 'commands', 'costs', 'generated_wheel_evidence', 'generated_sha256'}
                or report['schema'] != 'UDM_EXACT_BASE_BUILD_RECEIPT_V43'
                or report['status'] != 'BUILT_NOT_SCIENTIFICALLY_VERIFIED'
                or report['binding'] != receipt['binding']
                or report['recipe_sha256'] != build.recipe_digest()
                or report['builder_sha256'] != _BUILDER_SHA256
                or report['generated_sha256'] != evidence['generated_sha256']
                or not isinstance(report['costs'], dict) or not isinstance(costs, dict)
                or not isinstance(report['commands'], list)
                or any(not isinstance(row, dict) for row in report['commands'])
                or set(report['costs']) != base_costs or set(costs) != base_costs | {'verification_seconds'}
                or any(not _number(value) for value in costs.values())
                or any(costs[key] != report['costs'][key] for key in base_costs)
                or type(costs['build_calls']) is not int or costs['build_calls'] != 1
                or type(costs['command_calls']) is not int or costs['command_calls'] != len(report['commands'])
                or costs['total_seconds'] < costs['build_seconds']
                or record['seconds'] < costs['verification_seconds']):
            raise ValueError('UNKNOWN_V43_BUILD_COST_OR_RECIPE_BINDING')
        wheel_commands = [row for row in report['commands'] if row.get('phase') == 'base-native-wheel']
        if (len(wheel_commands) != 1 or any(row.get('status') != 'PASS' or row.get('returncode') != 0
                or not _number(row.get('seconds')) for row in report['commands'])
                or wheel_commands[0]['seconds'] != costs['build_seconds']):
            raise ValueError('UNKNOWN_V43_ACTUAL_BUILD_COMMAND_ACCOUNTING')
        before, after = record['builder_attempts_before'], record['builder_attempts_after']
        for counter in (before, after):
            if (not isinstance(counter, dict) or set(counter) != {'build_calls', 'build_seconds', 'records'}
                    or type(counter['build_calls']) is not int or counter['build_calls'] < 0
                    or not _number(counter['build_seconds']) or not isinstance(counter['records'], list)
                    or any(not isinstance(name, str) for name in counter['records'])):
                raise ValueError('UNKNOWN_V43_BUILD_COUNTER_FIELDS')
        if (after['build_calls'] != before['build_calls'] + 1
                or after['records'][:-1] != before['records']
                or len(after['records']) != len(before['records']) + 1
                or not math.isclose(after['build_seconds'] - before['build_seconds'],
                                    costs['build_seconds'], rel_tol=1e-9, abs_tol=1e-9)
                or _retained_json(after['records'][-1]) != report):
            raise ValueError('UNKNOWN_V43_BUILD_COUNTER_OR_RETAINED_RECEIPT')
    except (KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        raise ValueError('UNKNOWN_V43_MISSING_BUILD_ACCOUNTING') from error


def validate_receipt(contract, candidate, authority, certificate, receipt, *, policy,
                     output_dir=None, independent=True):
    """Preserve original native replay and validate separate V43 build accounting."""
    _runner_hash()
    if not isinstance(receipt, dict):
        raise ValueError('wrong V43 native receipt')
    _validate_build_accounting(contract, receipt.get('independent_collection'))
    before = build_snapshot()
    result = _controller_validate_receipt(contract, candidate, authority, certificate, receipt,
        policy=policy, output_dir=output_dir, independent=independent)
    if independent and contract['generated_build'] is not None:
        after = build_snapshot()
        result['independent_build_accounting'] = {
            'schema': 'UDM_NATIVE_BUILD_REPLAY_ACCOUNTING_V43',
            'measurement_scope': 'LOCAL_CONTROLLER_INVOCATIONS_NOT_HOSTILE_HOST_ATTESTATION',
            'verification_attempts': after['verification_attempts'] - before['verification_attempts'],
            'records': after['records'][before['verification_attempts']:],
            'builder_attempts_before': before.get('builder_attempts'),
            'builder_attempts_after': after.get('builder_attempts')}
    return result


def _run(contract, files, manifest, environment, plugins, out, mode, seconds, candidate):
    _runner_hash()
    source.require_executable(manifest)
    token = previous.previous._attempt_mode.set(mode)
    try:
        return _controller_run(contract, files, manifest, environment, plugins,
                               out, mode, seconds, candidate)
    finally:
        previous.previous._attempt_mode.reset(token)


_controller_globals.update(_context=_context, _run=_run, validate_certificate=validate_certificate,
                           validate_receipt=validate_receipt)
_runner_hash()
