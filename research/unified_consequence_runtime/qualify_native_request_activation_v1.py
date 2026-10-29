"""Qualify additive request transport; unchanged native45 remains the oracle."""
from __future__ import annotations

import inspect
import json
import os
from pathlib import Path, PurePosixPath
from types import FunctionType

from . import qualify_native_namespace_v45 as previous

original = previous.original
HERE, ROOT, PREFIX = previous.HERE, previous.ROOT, previous.PREFIX
BASE = 'cfab3f080cd199f367528e6631bcb93f3ebbc510'
PREIMPLEMENTATION_BASE = '866a107d111e4b64f753d57323ed2a89098cd046'
ORIGINAL_REQUEST_SEAL_SHA256 = 'ea1de5102aa0654d714890def4abbd07b63146d2b5525347c60a0fc5060ee3ef'
SEAL_COMMIT = 'f10f4745700911adc06293ecb1110134aa22d069'
SEAL_SHA256 = '49364dc36c6d5e3d0786ac50e36e20b8ee791ff3f99e32e7d7475bc2d28440a9'
RECORDS = HERE/'archaeology/native-request-activation-v1'
FREEZE_SCHEMA = 'UDM_NATIVE_REQUEST_ACTIVATION_FREEZE_V1'
RESULT_SCHEMA = 'UDM_NATIVE_REQUEST_ACTIVATION_QUALIFICATION_V1'
SCOPE = 'NATIVE_REQUEST_ACTIVATION_QUALIFICATION_ONLY'
QUALIFIED = 'QUALIFIED_BOUNDED_REQUEST_ACTIVATION_ONLY'
TESTS = ('test_native_request_activation_v1_revision2.py', 'test_qualify_native_request_activation_v1.py')
GATE_FILES = (*previous.GATE_FILES, *(PREFIX+name for name in (
    'native_environment_request_v1.py', 'qualify_native_frontier_request_v1.py',
    'qualify_native_request_activation_v1.py', *TESTS)),
    '.github/workflows/udm-native-request-activation-v1.yml')

# Keep original algorithms in an isolated namespace. The original native packet
# checker and inventory retain their exact function identity and source globals.
for _name, _value in vars(previous).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
_DIRECT = {'_controller_identity', '_runtime_freeze', '_validate_contracts',
           '_check_source_identity', 'native_invocation_inventory',
           'audit_native_packets', 'known_attempt_totals'}
_OVERRIDE = {'sealed_controls', '_preserve_baseline', '_source', '_collect_controls',
             '_test_environment', 'child_attempts', '_validate_claims'}
for _name, _value in vars(previous).items():
    if (isinstance(_value, FunctionType) and _value.__module__ == previous.__name__
            and _name not in _DIRECT | _OVERRIDE | {'archive'}):
        _code = _value.__code__.replace(co_consts=tuple(
            item.replace('UNKNOWN_NATIVE_NAMESPACE_QUALIFICATION', 'UNKNOWN_NATIVE_REQUEST_ACTIVATION_QUALIFICATION')
                .replace('qualified-bounded-admission-only', 'qualified-bounded-request-activation-only')
            if isinstance(item, str) else item for item in _value.__code__.co_consts))
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


def existing_gate():
    """Authenticate the already qualified four-gate source chain unchanged."""
    from . import qualify_native_frontier_v45 as frontier
    path = HERE/'archaeology/native-namespace-v45/prospective/GATE_WRAPPER.json'
    return frontier.require_environment_gate(json.loads(path.read_text()))


def _preserve_baseline(before, after):
    if not before or any(after.get(name) != row for name, row in before.items()):
        raise ValueError('complete fixed baseline blobs/modes were not preserved')
    return len(before)


def _source(repo):
    value = previous._source(repo)
    before = original._tree(repo, BASE)
    count = _preserve_baseline(before, value['source_tree'])
    sealed_before = original._tree(repo, PREIMPLEMENTATION_BASE)
    sealed_count = _preserve_baseline(sealed_before, value['source_tree'])
    if any(name not in value['files'] for name in GATE_FILES):
        raise ValueError('commit complete request activation source, controls and workflow before freeze')
    return dict(value, baseline_commit=BASE, preserved_baseline_files=count,
                preimplementation_baseline_commit=PREIMPLEMENTATION_BASE,
                preserved_preimplementation_files=sealed_count,
                prior_native_namespace_gate=existing_gate())


def _control_file(root, name, expected):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or str(relative) != name:
        raise ValueError('noncanonical request control path')
    path = Path(root)/name
    if path.is_symlink() or not path.is_file():
        raise ValueError('missing or redirected request control: '+name)
    raw = path.read_bytes()
    if (sha(raw) != expected['sha256'] or len(raw) != expected['bytes']
            or expected['mode'] not in ('100644', '100755')
            or bool(path.stat().st_mode & 0o111) != (expected['mode'] == '100755')):
        raise ValueError('request control bytes/mode differ: '+name)


def _original_request_controls():
    """Validate the independently committed preimplementation seal and W01."""
    old = previous.sealed_controls()
    root = RECORDS/'control-freeze'
    path = root/'FINAL_SEAL.json'
    if path.is_symlink() or not path.is_file() or file_sha(path) != ORIGINAL_REQUEST_SEAL_SHA256:
        raise ValueError('request control seal SHA256 differs')
    value = json.loads(path.read_text())
    if (value.get('schema') != 'UDM_NATIVE_REQUEST_ACTIVATION_CONTROLS_V1'
            or value.get('base_commit') != BASE or value.get('control_count') != 15
            or value.get('qualified_native_source_commit') != '8ecdf15598a2e67d39acd7a5a0e0f7c201000bb7'
            or value.get('original_control_seal_sha256') != old['seal_sha256']
            or value.get('scope') != 'REQUEST_TRANSPORT_ENGINEERING_CONTROLS_ONLY_NO_G2'
            or any(value.get(key) != 0 for key in ('task_queries', 'new_target_source_reads',
                'native_calls_before_seal', 'model_calls', 'product_mutations'))):
        raise ValueError('request control seal boundary differs')
    files = value.get('files', {})
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if (len(files) != 16 or actual != set(files) | {'FINAL_SEAL.json'}
            or any(p.is_symlink() for p in root.rglob('*'))):
        raise ValueError('request control seal inventory differs')
    for name, expected in files.items():
        _control_file(root, name, expected)
    _control_file(ROOT, value['test_file']['path'], value['test_file'])
    committed_seal = original._git(ROOT, 'show', PREIMPLEMENTATION_BASE+':'+path.relative_to(ROOT).as_posix())
    if committed_seal != path.read_bytes():
        raise ValueError('request seal differs from independently committed preimplementation bytes')
    return {'seal_sha256': ORIGINAL_REQUEST_SEAL_SHA256, 'seal_commit': PREIMPLEMENTATION_BASE,
            'files': files, 'test_file': value['test_file'], 'control_count': 15,
            'original_native_controls': old}


def sealed_controls(root=None):
    """Check the independent revision; never relabel the original 13/2 RED."""
    old = _original_request_controls()
    root = Path(root) if root is not None else RECORDS/'control-freeze-revision2'
    path = root/'FINAL_SEAL.json'
    if path.is_symlink() or not path.is_file() or file_sha(path) != SEAL_SHA256:
        raise ValueError('revision2 request seal SHA256 differs')
    value = json.loads(path.read_text())
    previous_pin = value.get('previous_request_control_seal', {})
    known = {'native_calls': 4, 'collection_calls': 9, 'subprocess_attempts': 13}
    retained = {'tests': 15, 'passed': 13, 'failures': 2,
                'corrected_fields_only': ['expected_collection_calls', 'expected_subprocess_attempts']}
    if (value.get('schema') != 'UDM_NATIVE_REQUEST_ACTIVATION_CONTROLS_V1_REVISION2'
            or value.get('base_commit') != BASE or value.get('control_revision') != 2
            or value.get('control_count') != 15
            or value.get('scope') != 'REQUEST_TRANSPORT_ENGINEERING_CONTROLS_ONLY_NO_G2'
            or value.get('qualified_native_source_commit') != '8ecdf15598a2e67d39acd7a5a0e0f7c201000bb7'
            or value.get('original_control_seal_sha256') != old['original_native_controls']['seal_sha256']
            or previous_pin.get('commit') != PREIMPLEMENTATION_BASE
            or previous_pin.get('sha256') != old['seal_sha256']
            or previous_pin.get('files') != old['files'] or previous_pin.get('test_file') != old['test_file']
            or value.get('known_engineering_invocations_before_revision2_seal') != known
            or value.get('retained_previous_result') != retained
            or value.get('original_test_bytes_unchanged') is not True
            or value.get('product_implementation_exists') is not True
            or value.get('revision2_native_execution_started') is not False
            or any(value.get(key) != 0 for key in ('task_queries', 'new_target_source_reads',
                'native_calls_for_independent_revision2_sealing', 'model_calls'))):
        raise ValueError('revision2 request seal boundary or original RED lineage differs')
    files = value.get('files', {})
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if (len(files) != 17 or actual != set(files) | {'FINAL_SEAL.json'}
            or any(p.is_symlink() for p in root.rglob('*'))):
        raise ValueError('revision2 request seal inventory differs')
    for name, expected in files.items():
        _control_file(root, name, expected)
    _control_file(ROOT, value['test_file']['path'], value['test_file'])
    # These hashes describe the implementation observed when revision2 was
    # sealed, including its retained earlier RED. They are not final code pins.
    # The complete committed CI source tree is independently frozen/rechecked
    # before and after execution; immutable native45 is additionally in both
    # preserved baselines and the existing four-gate proof.
    historical = value['source_pins_before_revision2_execution']
    if (set(historical) != {'native_environment_request_v1.py',
            'qualify_native_frontier_request_v1.py', 'native_execution_v45.py'}
            or any(not isinstance(pin, str) or len(pin) != 64
                   or any(char not in '0123456789abcdef' for char in pin) for pin in historical.values())
            or historical['native_execution_v45.py'] != file_sha(HERE/'native_execution_v45.py')):
        raise ValueError('revision2 historical source witness differs')
    if not SEAL_COMMIT:
        raise ValueError('independently committed revision2 seal pin is required')
    committed = original._git(ROOT, 'show', SEAL_COMMIT+':'+path.relative_to(ROOT).as_posix()) if root == RECORDS/'control-freeze-revision2' else None
    if committed is not None and committed != path.read_bytes():
        raise ValueError('revision2 request seal differs from independently committed bytes')
    return {'seal_sha256': SEAL_SHA256, 'seal_commit': SEAL_COMMIT,
            'control_revision': 2, 'files': files, 'test_file': value['test_file'],
            'control_count': 15, 'original_request_controls': old,
            'retained_previous_result': retained, 'known_prior_engineering_invocations': known,
            'historical_source_pins_at_revision2_sealing': historical}


def _test_environment(runtime_paths):
    previous._test_environment(runtime_paths)
    supplied = Path(os.environ.get('UDM_REQUEST_V1_RUNTIMES',
        '/workspace/qualification/native-namespace-v45-environment/RUNTIME_PATHS.json')).absolute()
    if supplied.is_symlink() or not supplied.is_file() or json.loads(supplied.read_text()) != runtime_paths:
        raise ValueError('request controls require the exact supplied runtime mapping')
    os.environ['UDM_REQUEST_V1_RUNTIMES'] = str(supplied)


def _collect_controls(repo, out):
    import pytest
    from . import native_execution_v45 as worker
    inventory = original._PytestInventory()
    before, compilation = worker.attempt_snapshot(), worker.compilation_snapshot()
    location = Path.cwd()
    try:
        os.chdir(repo)
        with Path(out).open('w') as stream, redirect_stdout(stream), redirect_stderr(stream):
            result = int(pytest.main(['-q', '-p', 'no:cacheprovider', '--import-mode=importlib',
                '--collect-only', *_control_tests()], plugins=[inventory]))
    finally:
        os.chdir(location)
    expected = json.loads((RECORDS/'control-freeze-revision2/TEST_INVENTORY.json').read_text())['nodes']
    actual = [node for node in inventory.collected if node.startswith(PREFIX+TESTS[0]+'::')]
    if (result or actual != expected or len(set(inventory.collected)) != len(inventory.collected)
            or not any(node.startswith(PREFIX+TESTS[1]+'::') for node in inventory.collected)
            or worker.attempt_snapshot() != before or worker.compilation_snapshot() != compilation):
        raise ValueError('sealed request collection failed, changed, or executed native work')
    return inventory.collected


def child_attempts(root):
    # A child is never invented for an in-process main() control. Any actual
    # retained summary must still pass every original source/output/cost check.
    return previous.child_attempts(root, required=False)


# Original strict bounded claims, with a single deliberate scope change: a
# separate native child is optional. Actual children are authenticated above.
_claims_source = inspect.getsource(previous._validate_claims)
_old = 'if not isinstance(children, list) or not children:'
if _claims_source.count(_old) != 1:
    raise ValueError('original child claim binding site changed')
exec(compile(_claims_source.replace(_old, 'if not isinstance(children, list):'),
             __file__+':original-claims', 'exec'), globals())

_archive_code = previous.archive.__code__.replace(co_consts=tuple(
    value.replace('NATIVE_NAMESPACE_V45_EVIDENCE', 'NATIVE_REQUEST_ACTIVATION_V1_EVIDENCE')
         .replace('UDM_NATIVE_NAMESPACE_ARCHIVE_MANIFEST_V45', 'UDM_NATIVE_REQUEST_ACTIVATION_ARCHIVE_MANIFEST_V1')
    if isinstance(value, str) else value for value in previous.archive.__code__.co_consts))
archive = FunctionType(_archive_code, dict(previous.archive.__globals__), 'archive', previous.archive.__defaults__)


if __name__ == '__main__':
    raise SystemExit(main())
