"""Versioned metadata-bootstrap bindings for the original MSI/V104 experiment.

The scientific catalog, search, policy choice, eligibility and counterfactual
algorithms retain their original code. V44 adds independently qualified setup
observation premises; the native collection/assertion worker remains V43.
"""
from __future__ import annotations

import copy
import inspect
from pathlib import Path
import re
import textwrap
from types import CodeType, FunctionType

from . import qualify_native_frontier_v43 as _previous_controller
from . import native_environment_v44 as _environment
from . import native_execution_v43 as _worker
from .developmental_machine_v44 import Machine

for _name, _value in vars(_previous_controller).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-bootstrap-v44/prospective'
PROTOCOL, METADATA = RECORDS/'FRONTIER_PROTOCOL.json', RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v44'
AUTHORITY_SCHEMA = 'UDM_NATIVE_CLI_AUTHORITY_V44'
AGENT_SCHEMA = 'UDM_CODING_AGENT_NATIVE_ARM_V44'
environment, worker = _environment, _worker
DEFAULTS = copy.deepcopy(_previous_controller.DEFAULTS)
DEFAULTS.update(schema='UDM_NATIVE_FRONTIER_PROTOCOL_V44', bootstrap_gate=None, bootstrap_archive_audit=None)
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v44.py'
_BASELINE = '8830a66fcb261b192d98da495b6cb91697d21f28'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
_PREVIOUS_SHA256 = 'd25a02b0fdeba507073b54b8297b73b488638f154de39fc53ef03a1fff246358'
_LITERALS = {
    'UDM_NATIVE_CLI_AUTHORITY_V43': AUTHORITY_SCHEMA,
    'UDM_CODING_AGENT_NATIVE_ARM_V43': AGENT_SCHEMA,
    'UDM_PREPARED_NATIVE_CONTEXT_V43': 'UDM_PREPARED_NATIVE_CONTEXT_V44',
    'UDM_NATIVE_SOURCE_RELEASE_V43': 'UDM_NATIVE_SOURCE_RELEASE_V44',
    'UDM_NATIVE_AGENT_PARENT_RECEIPT_V43': 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V44',
    'UDM_NATIVE_AGENT_METER_V43': 'UDM_NATIVE_AGENT_METER_V44',
    'UDM_NATIVE_AGENT_EXECUTION_V43': 'UDM_NATIVE_AGENT_EXECUTION_V44',
    'UDM_ADMISSION_ONLY_CASE_V43': 'UDM_ADMISSION_ONLY_CASE_V44',
    'UDM_SEALED_ADMISSION_ENVELOPE_V43': 'UDM_SEALED_ADMISSION_ENVELOPE_V44',
    'UDM_ADMISSION_ONLY_SCREENING_V43': 'UDM_ADMISSION_ONLY_SCREENING_V44',
    'UDM_ORDERED_SCREENING_METER_V43': 'UDM_ORDERED_SCREENING_METER_V44',
    'UDM_NATIVE_MACHINE_CONTEXT_V43': 'UDM_NATIVE_MACHINE_CONTEXT_V44',
    'UDM_NATIVE_FRONTIER_FREEZE_V43': 'UDM_NATIVE_FRONTIER_FREEZE_V44',
    'UDM_NATIVE_FRONTIER_RESULT_V43': 'UDM_NATIVE_FRONTIER_RESULT_V44',
    '8c1ff8db64415b9ce6db865f2744f40a866293c9': _BASELINE,
    'research/unified_consequence_runtime/qualify_native_frontier_v43.py': _SOURCE_PATH,
    ':research/unified_consequence_runtime/qualify_native_frontier_v43.py': ':'+_SOURCE_PATH,
}


def _literal_binding(code):
    constants = tuple(_literal_binding(value) if isinstance(value, CodeType)
        else _LITERALS.get(value, value) if isinstance(value, str) else value for value in code.co_consts)
    return code if constants == code.co_consts else code.replace(co_consts=constants)


for _name, _value in tuple(vars(_previous_controller).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _previous_controller.__name__:
        _bound = FunctionType(_literal_binding(_value.__code__), globals(), _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


def _guard():
    if (digest(Path(__file__).read_bytes()) != _LOADED_SHA256
            or digest(Path(_previous_controller.__file__).read_bytes()) != _PREVIOUS_SHA256):
        raise ValueError('UNKNOWN_V44_PROSPECTIVE_SOURCE_CHANGED')
    _previous_controller._guard()
    environment._guard()
    worker._runner_hash()


def _bootstrap_gate_descriptor(value):
    fields = {'status', 'source_commit', 'run_id', 'artifact_id', 'artifact_sha256',
              'qualification_result_sha256', 'result_path'}
    if (not isinstance(value, dict) or set(value) != fields
            or value.get('status') != 'ADMISSION_ONLY_QUALIFIED'
            or not re.fullmatch('[0-9a-f]{40}', value.get('source_commit', ''))
            or any(type(value.get(key)) is not int or value[key] <= 0 for key in ('run_id', 'artifact_id'))
            or any(not re.fullmatch('[0-9a-f]{64}', value.get(key, ''))
                   for key in ('artifact_sha256', 'qualification_result_sha256'))):
        raise ValueError('independently archived V44 bootstrap gate required')
    return value


def require_environment_gate(value):
    _guard()
    old = _previous_controller.require_environment_gate(value)
    gate = _bootstrap_gate_descriptor(value.get('bootstrap_gate'))
    result = _bound_json({'path': gate['result_path'], 'sha256': gate['qualification_result_sha256']})
    if (result.get('schema') != 'UDM_NATIVE_BOOTSTRAP_QUALIFICATION_V44'
            or result.get('status') != 'QUALIFIED_BOUNDED_NATIVE_METADATA_BOOTSTRAP_ONLY'
            or result.get('source_commit') != gate['source_commit']
            or result.get('freeze', {}).get('schema') != 'UDM_NATIVE_BOOTSTRAP_FREEZE_V44'
            or result['freeze'].get('source_commit') != gate['source_commit']
            or result['freeze'].get('catalog_sha256') != value['catalog']['sha256']
            or any(result.get('verdicts', {}).get('G'+str(index)) != 'UNKNOWN' for index in range(2, 7))):
        raise ValueError('V44 bootstrap gate is not the exact admission-only native qualification')
    from .qualify_native_bootstrap_v44 import BOOTSTRAP_GATE_FILES
    counts = result.get('contracts', {}).get('junit', {})
    if (type(counts.get('tests')) is not int or counts['tests'] <= 0
            or any(counts.get(key) != 0 for key in ('failures', 'errors', 'skipped'))):
        raise ValueError('V44 bootstrap gate lacks complete passing independent controls')
    files = result['freeze'].get('files', {})
    for name in BOOTSTRAP_GATE_FILES:
        path = HERE.parents[1]/name
        if path.is_symlink() or not path.is_file() or files.get(name) != digest(path.read_bytes()):
            raise ValueError('V44 bootstrap gate does not bind current source: '+name)
    nodes = result.get('contracts', {}).get('collection', [])
    if any(not any(node.startswith('research/unified_consequence_runtime/'+test+'::') for node in nodes)
           for test in ('test_qualify_native_frontier_v44.py', 'test_native_runtime_v44.py')):
        raise ValueError('V44 bootstrap gate omits controller or native dependency controls')
    descriptor = value.get('bootstrap_archive_audit')
    audit = _bound_json(descriptor)
    if (audit.get('schema') != 'UDM_V44_INDEPENDENT_BOOTSTRAP_AUDIT'
            or audit.get('status') != 'PASS_INDEPENDENT_NATIVE_BOOTSTRAP_AUDIT'
            or audit.get('bootstrap_gate') != gate
            or audit.get('gate_files_sha256') != {name: files[name] for name in BOOTSTRAP_GATE_FILES}):
        raise ValueError('independent V44 bootstrap archive audit does not bind exact qualified source and artifact')
    return {**old, 'bootstrap': gate, 'independent_bootstrap_audit': descriptor}


def _source_binding_v44(function, substitutions):
    source = textwrap.dedent(inspect.getsource(function))
    for before, after in substitutions:
        if source.count(before) != 1:
            raise ValueError('UNKNOWN_V44_CONTROLLER_BINDING_SITE:'+function.__name__+':'+before[:70])
        source = source.replace(before, after)
    namespace = dict(globals())
    exec(compile(source, __file__+':bound-'+function.__name__, 'exec'), namespace)
    original = namespace[function.__code__.co_name]
    result = FunctionType(_literal_binding(original.__code__), globals(), function.__name__,
                          original.__defaults__, original.__closure__)
    result.__kwdefaults__ = original.__kwdefaults__
    return result


_original_binding = _binding
_original_preflight_setup = _preflight_setup


def _binding(machine, contract, authority, policy, descriptor):
    materialization = _original_binding(machine, contract, authority, policy, descriptor)
    bootstrap = None
    if descriptor.get('bootstrap_binding') is not None:
        bootstrap = machine.get(descriptor['bootstrap_binding'])
        environment.preflight_bootstrap(machine, bootstrap, contract, authority, policy)
    return {'materialization': materialization, 'bootstrap': bootstrap}


def _prefix(binding):
    if binding is None:
        return ()
    if 'materialization' not in binding:
        return (binding['capability_id'], binding['consequence_id'],
                *((binding['environment_selection_id'],) if 'environment_selection_id' in binding else ()))
    return (*_prefix(binding['materialization']), *_prefix(binding['bootstrap']))


def _preflight_setup(machine, setup):
    original = _original_preflight_setup(machine, setup)
    bootstrap = environment.preflight_bootstrap(machine, setup, setup['contract'], setup['authority'], setup['policy'])
    return {'materialization': original, 'bootstrap': bootstrap}


def _check_episode(machine, episode, order, budget, *, contract=None, dependencies=None, **kwargs):
    # Metadata may be needed even when every native source file is tracked.
    # Derive exact live premises from the retained source, then delegate to the
    # unchanged original order/budget/receipt checker. Prefix deduplication is
    # the same transport used when the native probe was produced.
    if dependencies is not None and contract is not None:
        if not isinstance(episode, dict) or not episode.get('attempts'):
            return False
        binding = _preflight_record(machine.get(episode['attempts'][0]), machine)
        dependencies = _dependencies(_prefix(binding), dependencies)
    return _original_check_episode(machine, episode, order, budget,
                                   contract=contract, dependencies=dependencies, **kwargs)


_prepare = _source_binding_v44(_previous_controller._source_controller._prepare, (
    ('from .native_runtime_v3 import NativeRuntimeV3', 'from .native_runtime_v44 import NativeRuntimeV44'),
    ("runtimes=value['_runtime_inventory'], collection_seconds=value['collection_seconds'],",
     "runtimes=value['_runtime_inventory'], machine=machine, collection_seconds=value['collection_seconds'],"),
    ('runtime = NativeRuntimeV3(', 'runtime = NativeRuntimeV44('),
    ("destination/'native-evidence')", "destination/'native-evidence', materialization_capability=setup.get('materialization_capability'), bootstrap_binding=setup.get('bootstrap_binding'))"),
    ("certificate = worker.collect(setup['contract'], setup['authority'], destination/'collection', policy=setup['policy'])",
     "_preflight_setup(machine, setup)\n        certificate = worker.collect(setup['contract'], setup['authority'], destination/'collection', policy=setup['policy'])"),
    ("checked = worker.validate_certificate(setup['contract'], setup['authority'], certificate,",
     "_preflight_setup(machine, setup)\n        checked = worker.validate_certificate(setup['contract'], setup['authority'], certificate,"),
    ("'source_repos': execution['source_repos'], 'setup': setup,", "'source_repos': execution['source_repos'], 'machine_context': _machine_context(machine), 'setup': setup,"),
    ("'_execution': execution, '_prepared_context': parent,", "'_execution': execution, '_prepared_context': parent, '_machine_context': _machine_context(machine),"),
))
# The original source carrier uses V3 outer schemas. Only these outer transport
# literals change; the V43 native contract and verifier schemas never change.
_prepare = FunctionType(_previous_controller._outer_code(_prepare.__code__), globals(), '_prepare',
                        _prepare.__defaults__, _prepare.__closure__)
_prepare = FunctionType(_literal_binding(_prepare.__code__), globals(), '_prepare',
                        _prepare.__defaults__, _prepare.__closure__)


def native_probe(machine, runtime, candidate, label, dependencies=()):
    runtime._scope()
    binding = {'materialization': getattr(runtime, 'materialization_binding', None),
               'bootstrap': getattr(runtime, 'bootstrap_binding', None)}
    return _original_native_probe(machine, runtime, candidate, label,
        dependencies=_dependencies(_prefix(binding), dependencies))


_BOOTSTRAP_COST_COVERAGE = (
    'Original-backend metadata observations and independent verification in this screening interval; '
    'native counters remain separate and parent wall time includes these nested operations.')


def _bootstrap_snapshot():
    return environment.bootstrap_snapshot()


def _screening_bootstrap_costs(report):
    snapshots = report['bootstrap_attempts']
    before, after = snapshots['before'], snapshots['after']
    value = {'coverage': _BOOTSTRAP_COST_COVERAGE,
             'inclusive_parent_wall_seconds': report['total_wall_seconds'],
             'backend_calls': after['backend_calls']-before['backend_calls'],
             'backend_seconds': after['backend_seconds']-before['backend_seconds']}
    _validate_screening_bootstrap_costs(value)
    return value


def _validate_screening_bootstrap_costs(value):
    if (not isinstance(value, dict) or set(value) != {
            'coverage', 'inclusive_parent_wall_seconds', 'backend_calls', 'backend_seconds'}
            or value['coverage'] != _BOOTSTRAP_COST_COVERAGE
            or type(value['backend_calls']) is not int or value['backend_calls'] < 0
            or any(type(value[key]) not in (int, float) or not 0 <= value[key] < float('inf')
                   for key in ('backend_seconds', 'inclusive_parent_wall_seconds'))):
        raise ValueError('incomplete V44 bootstrap accounting')


_screen_original = admission_only_screen


def admission_only_screen(*args, **kwargs):
    before = _bootstrap_snapshot()
    result = _screen_original(*args, **kwargs)
    result['bootstrap_attempts'] = {'before': before, 'after': _bootstrap_snapshot()}
    path = Path(result['retained_raw_directory'])/'SCREENING_CASE.json'
    path.write_text(canonical(result)+'\n')
    return result


_envelope_original = screening_envelope


def screening_envelope(report, path):
    value = _envelope_original(report, path)
    value['bootstrap_costs'] = _screening_bootstrap_costs(report)
    (Path(path).parent/'SCREENING_ENVELOPE.json').write_text(canonical(value)+'\n')
    return value


_manifest_original = require_screening_manifest


_original_screening_manifest = _source_binding_v44(_previous_controller._source_controller.require_screening_manifest, (
    ("'sealed_report', 'costs', 'total_wall_seconds'}", "'sealed_report', 'costs', 'build_costs', 'bootstrap_costs', 'total_wall_seconds'}"),
    ("metadata = json.loads(METADATA.read_text())", "for row in screening['reports']:\n        _validate_screening_build_costs(row['build_costs'])\n        _validate_screening_bootstrap_costs(row['bootstrap_costs'])\n    metadata = json.loads(METADATA.read_text())"),
    (":research/unified_consequence_runtime/qualify_native_frontier_v3.py", ':'+_SOURCE_PATH),
))
_original_screening_manifest = FunctionType(
    _literal_binding(_previous_controller._outer_code(_original_screening_manifest.__code__)), globals(),
    '_original_screening_manifest', _original_screening_manifest.__defaults__, _original_screening_manifest.__closure__)


screening_request = _source_binding_v44(_previous_controller._source_controller.screening_request, (
    ("value = protocol()", "value = protocol()\n    _screening_components(ticket, descriptor)\n"
     "    if any(ticket.get(key) != value.get(key) for key in ('interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit')):\n"
     "        raise ValueError('screening authority has wrong independently audited bootstrap gate chain')"),
    ("{'environment_gate', 'catalog'}", "{'environment_gate', 'catalog', 'interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit'}"),
    ("or wrapper['catalog'] != value['catalog']", "or wrapper['catalog'] != value['catalog'] or any(wrapper.get(key) != value.get(key) for key in ('interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit'))"),
    ("'fa6bb190eff9b374ab7a95aaf9c618ad2db31419'", repr(_BASELINE)),
))
screening_request = FunctionType(_literal_binding(_previous_controller._outer_code(screening_request.__code__)),
    globals(), 'screening_request', screening_request.__defaults__, screening_request.__closure__)


def require_screening_manifest(value):
    screening = _manifest_original(value)
    if any(screening.get(key) != value.get(key) for key in ('bootstrap_gate', 'bootstrap_archive_audit')):
        raise ValueError('screening manifest omits exact independently audited bootstrap authority')
    for row in screening['reports']:
        _validate_screening_bootstrap_costs(row['bootstrap_costs'])
    return screening


if __name__ == '__main__':
    import importlib
    importlib.import_module(MODULE).main()
