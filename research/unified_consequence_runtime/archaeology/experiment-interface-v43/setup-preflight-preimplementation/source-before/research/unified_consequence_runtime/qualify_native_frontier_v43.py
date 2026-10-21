"""Causal interface bindings around the unchanged prospective MSI/V104 loop.

Importing reads installed source only. New sources remain behind both the old
qualified environment gate and a separately archived whole-interface gate.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import re
import textwrap
from types import CodeType, FunctionType

from . import qualify_native_frontier_v42 as _previous_controller
from . import qualify_native_frontier_v3 as _source_controller
from . import native_environment_v43 as _environment
from . import native_execution_v43 as _worker
from . import native_materialization_v43 as _materialization
from .developmental_machine_v43 import Machine

for _name, _value in vars(_previous_controller).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/experiment-interface-v43/prospective'
PROTOCOL, METADATA = RECORDS/'FRONTIER_PROTOCOL.json', RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v43'
AUTHORITY_SCHEMA = 'UDM_NATIVE_CLI_AUTHORITY_V43'
AGENT_SCHEMA = 'UDM_CODING_AGENT_NATIVE_ARM_V43'
environment, worker = _environment, _worker
DEFAULTS = copy.deepcopy(_previous_controller.DEFAULTS)
DEFAULTS.update(schema='UDM_NATIVE_FRONTIER_PROTOCOL_V43', interface_gate=None, interface_archive_audit=None)
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v43.py'
_BASELINE = '8c1ff8db64415b9ce6db865f2744f40a866293c9'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
_PREVIOUS_SHA256 = digest(Path(_previous_controller.__file__).read_bytes())
# The OLD environment freeze is checked by its OLD installed validator and file
# list. New files belong solely to the independent whole-interface freeze.
ENVIRONMENT_GATE_FILES = _previous_controller.ENVIRONMENT_GATE_FILES
INTERFACE_GATE_FILES = tuple('research/unified_consequence_runtime/'+name for name in (
    'native_build_v43.py', 'native_execution_v43.py', 'native_materialization_v43.py',
    'native_runtime_v43.py', 'cross_frontier_v43.py', 'developmental_machine_v43.py',
    'native_environment_v43.py', 'qualify_native_frontier_v43.py',
    'qualify_experiment_interface_v43.py', 'test_native_build_v43.py',
    'test_native_execution_v43.py', 'test_native_materialization_v43.py',
    'test_qualify_native_frontier_v43.py', 'developmental_sources.json',
    'archaeology/experiment-interface-v43/PROSPECTIVE_BINDINGS.md'))
_OUTER_LITERALS = {
    'UDM_NATIVE_CLI_AUTHORITY_V3': AUTHORITY_SCHEMA,
    'UDM_PREPARED_NATIVE_CONTEXT_V3': 'UDM_PREPARED_NATIVE_CONTEXT_V43',
    'UDM_NATIVE_SOURCE_RELEASE_V3': 'UDM_NATIVE_SOURCE_RELEASE_V43',
    'UDM_NATIVE_AGENT_PARENT_RECEIPT_V3': 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V43',
    'UDM_NATIVE_AGENT_METER_V3': 'UDM_NATIVE_AGENT_METER_V43',
    'UDM_ADMISSION_ONLY_CASE_V3': 'UDM_ADMISSION_ONLY_CASE_V43',
    'UDM_SEALED_ADMISSION_ENVELOPE_V3': 'UDM_SEALED_ADMISSION_ENVELOPE_V43',
    'UDM_ADMISSION_ONLY_SCREENING_V3': 'UDM_ADMISSION_ONLY_SCREENING_V43',
    'UDM_ORDERED_SCREENING_METER_V3': 'UDM_ORDERED_SCREENING_METER_V43',
    'UDM_NATIVE_FRONTIER_FREEZE_V42': 'UDM_NATIVE_FRONTIER_FREEZE_V43',
    'UDM_NATIVE_FRONTIER_RESULT_V42': 'UDM_NATIVE_FRONTIER_RESULT_V43',
    'dc59c8fcee6efede520c531eba5e42e7b84a1a9f': _BASELINE,
    'research/unified_consequence_runtime/qualify_native_frontier_v42.py': _SOURCE_PATH,
    ':research/unified_consequence_runtime/qualify_native_frontier_v42.py': ':'+_SOURCE_PATH,
}


def _outer_code(code):
    return code.replace(co_consts=tuple(_outer_code(value) if isinstance(value, CodeType)
        else _OUTER_LITERALS.get(value, value) if isinstance(value, str) else value for value in code.co_consts))


for _name, _value in tuple(vars(_previous_controller).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _previous_controller.__name__:
        _code = _outer_code(_value.__code__)
        # Preserve actual code-object identity where no reviewed literal changes.
        if _code == _value.__code__:
            _code = _value.__code__
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


def _guard():
    if (digest(Path(__file__).read_bytes()) != _LOADED_SHA256 or
            digest(Path(_previous_controller.__file__).read_bytes()) != _PREVIOUS_SHA256):
        raise ValueError('UNKNOWN_V43_PROSPECTIVE_SOURCE_CHANGED')
    _previous_controller._guard()
    environment._guard()
    worker._runner_hash()


def _gate_descriptor(value):
    fields = {'status', 'source_commit', 'run_id', 'artifact_id', 'artifact_sha256',
              'qualification_result_sha256', 'result_path'}
    if (not isinstance(value, dict) or set(value) != fields or value.get('status') != 'ADMISSION_ONLY_QUALIFIED'
            or not re.fullmatch('[0-9a-f]{40}', value.get('source_commit', ''))
            or any(type(value.get(key)) is not int or value[key] <= 0 for key in ('run_id', 'artifact_id'))
            or any(not re.fullmatch('[0-9a-f]{64}', value.get(key, ''))
                   for key in ('artifact_sha256', 'qualification_result_sha256'))):
        raise ValueError('independently archived whole V43 interface gate required')
    return value


def require_environment_gate(value):
    _guard()
    old_gate = _previous_controller.require_environment_gate(value)
    gate = _gate_descriptor(value.get('interface_gate'))
    result = _bound_json({'path': gate['result_path'], 'sha256': gate['qualification_result_sha256']})
    if (result.get('schema') != 'UDM_EXPERIMENT_INTERFACE_QUALIFICATION_V43'
            or result.get('status') != 'QUALIFIED_BOUNDED_CAUSAL_NATIVE_INTERFACE_ONLY'
            or result.get('mode') != 'whole' or result.get('source_commit') != gate['source_commit']
            or result.get('freeze', {}).get('schema') != 'UDM_EXPERIMENT_INTERFACE_FREEZE_V43'
            or result['freeze'].get('source_commit') != gate['source_commit']
            or any(result.get('verdicts', {}).get('G'+str(index)) != 'UNKNOWN' for index in range(2, 7))):
        raise ValueError('V43 gate is not a whole admission-only interface qualification')
    counts = result.get('contracts', {}).get('junit', {})
    if (not counts.get('tests') or any(counts.get(key) != 0 for key in ('failures', 'errors', 'skipped'))
            or result['freeze'].get('catalog_sha256') != value['catalog']['sha256']):
        raise ValueError('V43 gate lacks complete passing controls or exact original catalog')
    files = result['freeze'].get('files', {})
    for name in INTERFACE_GATE_FILES:
        path = HERE.parents[1]/name
        if path.is_symlink() or not path.is_file() or files.get(name) != digest(path.read_bytes()):
            raise ValueError('V43 gate does not bind current interface source: '+name)
    collected = result.get('contracts', {}).get('collection', [])
    if any(not any(node.startswith('research/unified_consequence_runtime/'+test+'::') for node in collected)
           for test in ('test_native_materialization_v43.py', 'test_qualify_native_frontier_v43.py')):
        raise ValueError('V43 gate omits causal or prospective binding controls')
    audit_record = value.get('interface_archive_audit')
    audit = _bound_json(audit_record)
    if (audit.get('schema') != 'UDM_V43_INDEPENDENT_INTERFACE_ARCHIVE_AUDIT_V1'
            or audit.get('status') != 'PASS_INDEPENDENT_ARCHIVE_AUDIT'
            or audit.get('interface_gate') != gate or audit.get('all_native_packets_checked') is not True
            or audit.get('gate_files_sha256') != {name: files[name] for name in INTERFACE_GATE_FILES}):
        raise ValueError('independent V43 archive audit does not bind exact artifact and interface files')
    return {'environment': old_gate, 'interface': gate, 'independent_archive_audit': audit_record}


def _components_record(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path or path.is_symlink() or not path.is_dir():
        raise ValueError('canonical independently supplied components root required')
    return {'path': str(path), 'pins_sha256': digest((HERE/'developmental_sources.json').read_bytes())}


def _screening_components(ticket, descriptor):
    if ticket.get('schema') != AUTHORITY_SCHEMA or ticket.get('operation') != 'screen':
        raise ValueError('wrong versioned screening authority')
    if _committed_record(ticket['repo'], descriptor) != ticket:
        raise ValueError('screening ticket differs from committed authority')
    record = ticket.get('machine_components')
    if not isinstance(record, dict) or set(record) != {'path', 'pins_sha256'}:
        raise ValueError('screening authority omits exact component pins')
    if _components_record(record['path']) != record:
        raise ValueError('screening authority component pins differ')
    return Path(record['path'])


def _machine_context(machine):
    return {'schema': 'UDM_NATIVE_MACHINE_CONTEXT_V43', 'components': _components_record(machine.components),
            'state': str(machine.state)}


def _load_machine(context):
    if (not isinstance(context, dict) or set(context) != {'schema', 'components', 'state'}
            or context['schema'] != 'UDM_NATIVE_MACHINE_CONTEXT_V43'
            or _components_record(context['components']['path']) != context['components']):
        raise ValueError('wrong retained native Machine context')
    state = Path(context['state'])
    if (not state.is_absolute() or state.resolve() != state or state.is_symlink()
            or not (state/'metatron-ledger.jsonl').is_file()):
        raise ValueError('retained native warrant state is missing or redirected')
    return Machine(Path(context['components']['path']), state, state.parent/'evaluator', state.parent/'unused-native-config.json')


def _binding(machine, contract, authority, policy, descriptor):
    if contract.get('generated_build') is None:
        if descriptor.get('materialization_binding') is not None:
            raise ValueError('tracked-only source has a materialization binding')
        return None
    retained = machine.get(descriptor['materialization_binding'])
    actual = _materialization.MaterializationRuntime(machine, machine.state.parent/'materialization-preflight').bind_native(
        retained['capability_id'], contract, authority, policy)
    if retained != actual:
        raise ValueError('materialization source/request/evidence/generation differs')
    return actual


def _prefix(binding):
    return () if binding is None else (binding['capability_id'], binding['consequence_id'])


def _dependencies(prefix, dependencies):
    return (*prefix, *(ident for ident in dependencies if ident not in prefix))


def _preflight_record(record, machine):
    if machine is None or record.get('schema') != 'UDM_NATIVE_PROFILE_RECORD_V2':
        raise ValueError('exact retained native profile and Machine required')
    nodes = {node.id: node for node in machine.log}
    producer = record['producer']
    source, authority = nodes[producer['source']], nodes[producer['authority']]
    descriptor = source.payload.get('source', {})
    if (source.kind != 'generic_native_source' or tuple(source.premises) != (authority.id,)
            or authority.kind != 'execution_authority_ceiling' or authority.payload != AUTHORITY or authority.premises
            or any(machine.get(descriptor[key]) != record[field] for key, field in (
                ('contract', 'contract'), ('suite_authority', 'authority'), ('certificate', 'certificate'), ('policy', 'policy')))):
        raise ValueError('profile source or fixed external authority differs')
    binding = _binding(machine, record['contract'], record['authority'], record['policy'], descriptor)
    prefix = _prefix(binding)
    if tuple(producer['dependencies'][:len(prefix)]) != prefix:
        raise ValueError('native profile omits exact instrument and invocation witness premises')
    premises = (source.id, authority.id, *producer['dependencies'])
    live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    key = worker.fingerprint(record)
    if (any(ident not in live for ident in premises) or not any(node.kind == 'native_frontier_v2_probe'
            and node.payload.get('record') == key and tuple(node.premises) == premises and node.id in live
            for node in machine.log)):
        raise PermissionError('native profile producer or exact materialization witness is withdrawn')
    return binding


def _preflight_agent(arm):
    machine = _load_machine(arm['machine_context'])
    contract = arm['contract']
    matches = [node for node in machine.log if node.kind == 'generic_native_source'
               and all(machine.get(node.payload['source'][key]) == arm[field] for key, field in (
                   ('contract', 'contract'), ('suite_authority', 'authority'), ('certificate', 'certificate'), ('policy', 'policy')))]
    if len(matches) != 1:
        raise ValueError('agent arm lacks one exact retained native source context')
    binding = _binding(machine, contract, arm['authority'], arm['policy'], matches[0].payload['source'])
    live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    if matches[0].id not in live or any(ident not in live for ident in _prefix(binding)):
        raise PermissionError('agent native source or exact materialization witness is withdrawn')
    return {'machine_context': arm['machine_context'], 'materialization_binding': binding, 'costs': machine.costs}


def _source_binding(function, substitutions):
    text = textwrap.dedent(inspect.getsource(function))
    for old, new in substitutions:
        if text.count(old) != 1:
            raise ValueError('UNKNOWN_V43_CONTROLLER_BINDING_SITE:'+function.__name__+':'+old[:70])
        text = text.replace(old, new)
    namespace = dict(globals())
    exec(compile(text, __file__+':bound-'+function.__name__, 'exec'), namespace)
    value = namespace[function.__name__]
    bound = FunctionType(_outer_code(value.__code__), globals(), value.__name__, value.__defaults__, value.__closure__)
    bound.__kwdefaults__ = value.__kwdefaults__
    return bound


_prepare = _source_binding(_source_controller._prepare, (
    ('from .native_runtime_v3 import NativeRuntimeV3', 'from .native_runtime_v43 import NativeRuntimeV43'),
    ("runtimes=value['_runtime_inventory'], collection_seconds=value['collection_seconds'],",
     "runtimes=value['_runtime_inventory'], machine=machine, collection_seconds=value['collection_seconds'],"),
    ('runtime = NativeRuntimeV3(', 'runtime = NativeRuntimeV43('),
    ("destination/'native-evidence')", "destination/'native-evidence', materialization_capability=setup.get('materialization_capability'))"),
    ("'source_repos': execution['source_repos'], 'setup': setup,", "'source_repos': execution['source_repos'], 'machine_context': _machine_context(machine), 'setup': setup,"),
    ("'_execution': execution, '_prepared_context': parent,", "'_execution': execution, '_prepared_context': parent, '_machine_context': _machine_context(machine),"),
))
admission_only_screen = _source_binding(_source_controller.admission_only_screen, (
    ('*, catalog, runtimes):', '*, catalog, runtimes, components):'),
    ("destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)",
     "destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)\n"
     "    machine = Machine(Path(components), destination/'machine-state', Path(components)/'evaluator', destination/'unused-native-config.json')\n"
     "    environment.record_admission_request(machine, spec, binding)\n    builds_before = worker.build_snapshot()"),
    ('catalog=catalog, runtimes=runtimes)', 'catalog=catalog, runtimes=runtimes, machine=machine)'),
    ("(destination/'SCREENING_CASE.json').write_text(canonical(report)+'\\n')",
     "report['machine_context'] = _machine_context(machine)\n    "
     "    report['machine_costs'] = machine.costs\n        report['build_attempts'] = {'before': builds_before, 'after': worker.build_snapshot()}\n"
     "        (destination/'SCREENING_CASE.json').write_text(canonical(report)+'\\n')"),
))
execute_screening_request = _source_binding(_source_controller.execute_screening_request, (
    ('runtimes=inventory[\'runtimes\'])', "runtimes=inventory['runtimes'], components=_screening_components(ticket, descriptor))"),
))
_execute_agent_candidate = _source_binding(_source_controller._execute_agent_candidate, (
    ("attempts = _attempt_snapshot(); result = None", "attempts = _attempt_snapshot(); result = None; preflight = None; builds_before = worker.build_snapshot()"),
    ("receipt = worker.verify(arm['contract'], candidate, destination,", "preflight = _preflight_agent(arm)\n        receipt = worker.verify(arm['contract'], candidate, destination,"),
    ("'invalid_raw_reports': raw_errors}", "'invalid_raw_reports': raw_errors, 'materialization_preflight': preflight, 'build_attempts_before': builds_before, 'build_attempts_after': worker.build_snapshot()}"),
))
agent_arm = _source_binding(_source_controller.agent_arm, (
    ("'certificate': context['certificate'], 'policy': context['setup']['policy'],", "'certificate': context['certificate'], 'policy': context['setup']['policy'], 'machine_context': context['_machine_context'],"),
))
screening_request = _source_binding(_source_controller.screening_request, (
    ("value = protocol()", "value = protocol()\n    _screening_components(ticket, descriptor)\n"
     "    if any(ticket.get(key) != value.get(key) for key in ('interface_gate', 'interface_archive_audit')):\n"
     "        raise ValueError('screening authority has wrong independently audited interface gate')"),
    ("{'environment_gate', 'catalog'}", "{'environment_gate', 'catalog', 'interface_gate', 'interface_archive_audit'}"),
    ("or wrapper['catalog'] != value['catalog']", "or wrapper['catalog'] != value['catalog'] or any(wrapper.get(key) != value.get(key) for key in ('interface_gate', 'interface_archive_audit'))"),
    ("'fa6bb190eff9b374ab7a95aaf9c618ad2db31419'", repr(_BASELINE)),
))

_original_native_probe = native_probe
_original_checked_record = checked_record
_original_check_episode = _check_episode
_original_prepared_context = _prepared_context
_original_agent_request = agent_request
_original_screening_manifest = require_screening_manifest


def native_probe(machine, runtime, candidate, label, dependencies=()):
    runtime._scope()
    return _original_native_probe(machine, runtime, candidate, label,
        dependencies=_dependencies(_prefix(getattr(runtime, 'materialization_binding', None)), dependencies))


def checked_record(record, machine=None, **kwargs):
    _preflight_record(record, machine)
    return _original_checked_record(record, machine, **kwargs)


def _check_episode(machine, episode, order, budget, *, contract=None, dependencies=None, **kwargs):
    if dependencies is not None and contract is not None and contract.get('generated_build') is not None:
        if not episode or not episode.get('attempts'):
            return False
        binding = _preflight_record(machine.get(episode['attempts'][0]), machine)
        dependencies = _dependencies(_prefix(binding), dependencies)
    return _original_check_episode(machine, episode, order, budget, contract=contract, dependencies=dependencies, **kwargs)


def _prepared_context(parent, freeze_descriptor):
    setup = parent['setup']
    _preflight_agent({'machine_context': parent['machine_context'], 'contract': setup['contract'],
                      'authority': setup['authority'], 'certificate': parent['certificate'], 'policy': setup['policy']})
    return _original_prepared_context(parent, freeze_descriptor)


def agent_request(arm_path, ticket, parent):
    arm = _original_agent_request(arm_path, ticket, parent)
    prepared = _external_json(parent['prepared_context'])
    if arm.get('machine_context') != prepared.get('machine_context'):
        raise ValueError('agent Machine context differs from its sealed prepared parent')
    _preflight_agent(arm)
    return arm


def require_screening_manifest(value):
    screening = _original_screening_manifest(value)
    if any(screening.get(key) != value.get(key) for key in ('interface_gate', 'interface_archive_audit')):
        raise ValueError('screening manifest omits exact audited V43 interface authority')
    return screening


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    return _reconstruct_profiles(machine, candidates, futures, evidence_ids)


if __name__ == '__main__':
    import importlib
    importlib.import_module(MODULE).main()
