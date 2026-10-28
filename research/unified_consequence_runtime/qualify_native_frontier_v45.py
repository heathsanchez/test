"""V45 native namespace transport for the unchanged MSI/V104 experiment.

Original search, policy choice, comparator, budgets and selection remain the
V44 algorithms. This carrier adds no tasks or outcomes and grants no scientific
warrant from admission infrastructure. All earlier independent gates remain.
"""
from __future__ import annotations

import copy
from pathlib import Path
import re
from types import CodeType, FunctionType

from . import qualify_native_frontier_v44 as _previous_controller
from . import native_environment_v45 as _environment
from . import native_execution_v45 as _worker
from .developmental_machine_v44 import Machine

for _name, _value in vars(_previous_controller).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-namespace-v45/prospective'
PROTOCOL, METADATA = RECORDS/'FRONTIER_PROTOCOL.json', RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v45'
AUTHORITY_SCHEMA = 'UDM_NATIVE_CLI_AUTHORITY_V45'
AGENT_SCHEMA = 'UDM_CODING_AGENT_NATIVE_ARM_V45'
environment, worker = _environment, _worker
_materialization = environment.materialization
DEFAULTS = copy.deepcopy(_previous_controller.DEFAULTS)
DEFAULTS.update(schema='UDM_NATIVE_FRONTIER_PROTOCOL_V45', namespace_gate=None, namespace_archive_audit=None)
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v45.py'
_BASELINE = '88aa5090c310d2f75683a019a5bc958cdb3b576e'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
_PREVIOUS_SHA256 = '5006932fedc8b321d6f36002d1c3086790dd49ad18ca8327feb6148bb0948f02'
_LITERALS = {value: value.replace('_V44', '_V45')
             for value in _previous_controller._LITERALS.values()
             if isinstance(value, str) and value.startswith('UDM_')}
_LITERALS.update({
    _previous_controller._BASELINE: _BASELINE,
    _previous_controller._SOURCE_PATH: _SOURCE_PATH,
    ':'+_previous_controller._SOURCE_PATH: ':'+_SOURCE_PATH,
})
_NAMES = {'native_runtime_v44': 'native_runtime_v45', 'NativeRuntimeV44': 'NativeRuntimeV45'}
GATE_KEYS = ('environment_gate', 'interface_gate', 'interface_archive_audit',
             'bootstrap_gate', 'bootstrap_archive_audit', 'namespace_gate', 'namespace_archive_audit')


def _transport_constant(value):
    if isinstance(value, CodeType):
        return _transport_code(value)
    if isinstance(value, str):
        return _LITERALS.get(value, value)
    if isinstance(value, (tuple, frozenset)) and 'bootstrap_gate' in value:
        added = tuple(value) + tuple(key for key in ('namespace_gate', 'namespace_archive_audit') if key not in value)
        return frozenset(added) if isinstance(value, frozenset) else added
    return value


def _transport_code(code):
    constants = tuple(_transport_constant(value) for value in code.co_consts)
    names = tuple(_NAMES.get(name, name) for name in code.co_names)
    return code if constants == code.co_consts and names == code.co_names else code.replace(co_consts=constants, co_names=names)


_literal_binding = _transport_code
for _name, _value in tuple(vars(_previous_controller).items()):
    if (isinstance(_value, FunctionType) and _value.__module__ == _previous_controller.__name__
            and _name not in ('_literal_binding', '_guard', 'require_environment_gate')):
        _bound = FunctionType(_transport_code(_value.__code__), globals(), _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


def _guard():
    if (digest(Path(__file__).read_bytes()) != _LOADED_SHA256
            or digest(Path(_previous_controller.__file__).read_bytes()) != _PREVIOUS_SHA256):
        raise ValueError('UNKNOWN_V45_PROSPECTIVE_SOURCE_CHANGED')
    _previous_controller._guard()
    environment._guard()
    worker._runner_hash()


def _namespace_gate_descriptor(value):
    fields = {'status', 'source_commit', 'run_id', 'artifact_id', 'artifact_sha256',
              'qualification_result_sha256', 'result_path'}
    if (not isinstance(value, dict) or set(value) != fields
            or value.get('status') != 'ADMISSION_ONLY_QUALIFIED'
            or not isinstance(value.get('source_commit'), str)
            or not re.fullmatch('[0-9a-f]{40}', value['source_commit'])
            or any(type(value.get(key)) is not int or value[key] <= 0 for key in ('run_id', 'artifact_id'))
            or any(not isinstance(value.get(key), str) or not re.fullmatch('[0-9a-f]{64}', value[key])
                   for key in ('artifact_sha256', 'qualification_result_sha256'))
            or not isinstance(value.get('result_path'), str)):
        raise ValueError('independently archived V45 namespace gate required')
    return value


def _namespace_native_evidence(result):
    raw = result.get('raw_native_audit')
    if (not isinstance(raw, dict) or raw.get('schema') != 'UDM_V45_RAW_NATIVE_PACKET_AUDIT'
            or raw.get('status') != 'PASS_BOUNDED_RAW_NATIVE_PACKETS'
            or any(type(raw.get(key)) is not int or raw[key] <= 0
                   for key in ('native_passes', 'native_failures', 'independent_replays', 'certificates'))
            or not isinstance(raw.get('manifest_paths'), list) or not raw['manifest_paths']
            or not isinstance(raw.get('receipts'), list) or not raw['receipts']):
        raise ValueError('V45 namespace gate lacks actual passing, failing and independent native packet evidence')
    receipts = raw['receipts']
    schemas = {'UDM_GENERIC_NATIVE_PYTEST_'+version for version in ('V2', 'V42', 'V43', 'V45')}
    if any(not isinstance(row, dict) or row.get('schema') not in schemas
           or not isinstance(row.get('invocation_path'), str) or not row['invocation_path']
           or not isinstance(row.get('path'), str) or not row['path']
           for row in receipts):
        raise ValueError('V45 namespace gate lacks exact versioned native invocation identities')
    identities = [row['invocation_path'] for row in receipts]
    if len(identities) != len(set(identities)):
        raise ValueError('V45 namespace gate duplicates an actual native invocation')
    versioned = [row for row in receipts if row['schema'] == 'UDM_GENERIC_NATIVE_PYTEST_V45']
    for status in ('PASS_NATIVE', 'FAIL_NATIVE'):
        if not any(row.get('status') == status for row in versioned):
            raise ValueError('V45 namespace gate omits original native outcomes')
        rows = [row for row in receipts if row.get('status') == status]
        for row in rows:
            counts = row.get('junit', {})
            if (not isinstance(counts, dict)
                    or any(type(counts.get(key)) is not int or counts[key] < 0
                           for key in ('tests', 'passed', 'failures', 'errors', 'skipped'))
                    or counts['tests'] <= 0 or counts['errors'] or counts['skipped']
                    or counts['tests'] != counts['passed']+counts['failures']
                    or status == 'PASS_NATIVE' and counts['failures'] != 0
                    or status == 'FAIL_NATIVE' and counts['failures'] <= 0):
                raise ValueError('V45 namespace native outcome lacks actual complete assertion counts')
    actual = {'native_passes': sum(row.get('status') == 'PASS_NATIVE' for row in versioned),
              'native_failures': sum(row.get('status') == 'FAIL_NATIVE' for row in versioned),
              'independent_replays': sum(row.get('role') == 'independent_reexecution'
                  and row.get('status') in ('PASS_NATIVE', 'FAIL_NATIVE') for row in versioned)}
    if any(raw[key] != value for key, value in actual.items()):
        raise ValueError('V45 namespace native execution counters differ from exact audited receipts')
    return raw


def require_environment_gate(value):
    """Require exact archived namespace authority after every original gate.

    The independent archive audit is supplied authority. Parser acceptance of
    internally consistent files cannot manufacture that independent provenance.
    """
    _guard()
    old = _previous_controller.require_environment_gate(value)
    gate = _namespace_gate_descriptor(value.get('namespace_gate'))
    result = _bound_json({'path': gate['result_path'], 'sha256': gate['qualification_result_sha256']})
    if (result.get('schema') != 'UDM_NATIVE_NAMESPACE_QUALIFICATION_V45'
            or result.get('status') != 'QUALIFIED_BOUNDED_NATIVE_NAMESPACE_ADMISSION_ONLY'
            or result.get('source_commit') != gate['source_commit']
            or result.get('freeze', {}).get('schema') != 'UDM_NATIVE_NAMESPACE_FREEZE_V45'
            or result['freeze'].get('source_commit') != gate['source_commit']
            or result['freeze'].get('catalog_sha256') != value['catalog']['sha256']
            or any(result.get('verdicts', {}).get('G'+str(index)) != 'UNKNOWN' for index in range(2, 7))):
        raise ValueError('V45 namespace gate is not the exact admission-only qualification')
    from .qualify_native_namespace_v45 import GATE_FILES, _validate_claims
    _validate_claims(result)
    counts = result.get('contracts', {}).get('junit', {})
    if (type(counts.get('tests')) is not int or counts['tests'] <= 0
            or any(type(counts.get(key)) is not int or counts[key] != 0 for key in ('failures', 'errors', 'skipped'))):
        raise ValueError('V45 namespace gate lacks complete passing independent controls')
    files = result['freeze'].get('files', {})
    for name in GATE_FILES:
        path = HERE.parents[1]/name
        if path.is_symlink() or not path.is_file() or files.get(name) != digest(path.read_bytes()):
            raise ValueError('V45 namespace gate does not bind current source: '+name)
    nodes = result.get('contracts', {}).get('collection', [])
    if any(not any(isinstance(node, str) and node.startswith('research/unified_consequence_runtime/'+test+'::') for node in nodes)
           for test in ('test_native_admission_v45.py', 'test_native_execution_v45.py',
                        'test_native_runtime_v45.py', 'test_qualify_native_frontier_v45.py')):
        raise ValueError('V45 namespace gate omits assertion, native, runtime or scientific carrier controls')
    raw = _namespace_native_evidence(result)
    descriptor = value.get('namespace_archive_audit')
    audit = _bound_json(descriptor)
    if (audit.get('schema') != 'UDM_V45_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT'
            or audit.get('status') != 'PASS_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT'
            or audit.get('namespace_gate') != gate
            or audit.get('gate_files_sha256') != {name: files[name] for name in GATE_FILES}
            or audit.get('all_native_packets_checked') is not True):
        raise ValueError('independent V45 namespace archive audit differs from exact source/run/artifact/result')
    if _bound_json(audit.get('raw_native_audit')) != raw:
        raise ValueError('independent V45 namespace archive audit has foreign native evidence')
    return {**old, 'namespace': gate, 'independent_namespace_audit': descriptor}


if __name__ == '__main__':
    import importlib
    importlib.import_module(MODULE).main()
