"""Versioned activation of one existing operation in the original V45 loop.

Search, policy selection, native authority, scopes and budgets remain the
original algorithms. This adapter exposes the original request recorder and
retains actual bootstrap counters when an interrupted call reaches the original
screening finally block. Qualification of this transport establishes no G2.
"""
from __future__ import annotations

import copy as _copy
from pathlib import Path
from types import CodeType, FunctionType

from . import qualify_native_frontier_v45 as _qualified_controller
from . import native_environment_request_v1 as _request_environment

for _name, _value in vars(_qualified_controller).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

ACTIVATION_VERSION = _request_environment.ACTIVATION_VERSION
HERE = _qualified_controller.HERE
RECORDS = HERE/'archaeology/native-request-activation-v1/prospective'
PROTOCOL, METADATA = RECORDS/'FRONTIER_PROTOCOL.json', RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_request_v1'
environment, worker = _request_environment, _qualified_controller.worker
DEFAULTS = _copy.deepcopy(_qualified_controller.DEFAULTS)
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_request_v1.py'
_QUALIFIED_CONTROLLER_SHA256 = 'ece5d43d25fb470b89a043c32767e3e72976d000134cad8ddccd184dc3e7cbbb'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
_REQUEST_ENVIRONMENT_SHA256 = digest(Path(environment.__file__).read_bytes())
_CALLER_LITERALS = {
    _qualified_controller._SOURCE_PATH: _SOURCE_PATH,
    ':'+_qualified_controller._SOURCE_PATH: ':'+_SOURCE_PATH,
    _qualified_controller.MODULE: MODULE,
}


def _transport_constant(value):
    if isinstance(value, CodeType):
        return _transport_code(value)
    if isinstance(value, str):
        return _CALLER_LITERALS.get(value, value)
    if isinstance(value, tuple):
        return tuple(_transport_constant(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(_transport_constant(item) for item in value)
    return value


def _transport_code(code):
    constants = tuple(_transport_constant(value) for value in code.co_consts)
    return code if constants == code.co_consts else code.replace(co_consts=constants)


def _literal_binding(code):
    return _transport_code(_qualified_controller._literal_binding(code))


def _bind(function, namespace=None):
    value = FunctionType(_transport_code(function.__code__),
        globals() if namespace is None else namespace, function.__name__,
        function.__defaults__, function.__closure__)
    value.__kwdefaults__ = function.__kwdefaults__
    return value


for _name, _value in tuple(vars(_qualified_controller).items()):
    if (isinstance(_value, FunctionType)
            and _value.__globals__ is vars(_qualified_controller)
            and _name not in ('_guard', 'require_environment_gate', 'execute_screening_request',
                             '_transport_constant', '_transport_code', '_literal_binding')):
        globals()[_name] = _bind(_value)


def _guard():
    if (digest(Path(__file__).read_bytes()) != _LOADED_SHA256
            or digest(Path(_qualified_controller.__file__).read_bytes()) != _QUALIFIED_CONTROLLER_SHA256
            or digest(Path(environment.__file__).read_bytes()) != _REQUEST_ENVIRONMENT_SHA256):
        raise ValueError('UNKNOWN_NATIVE_REQUEST_ACTIVATION_V1_CONTROLLER_SOURCE_CHANGED')
    _qualified_controller._guard()
    environment._guard()


def require_environment_gate(value):
    _guard()
    return _qualified_controller.require_environment_gate(value)


_execute_original = _bind(_qualified_controller.execute_screening_request)
_qualified_reconstruct_profiles = _bind(_qualified_controller.reconstruct_profiles)


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    """Truthful local source identity for the unchanged independent checker."""
    return _qualified_reconstruct_profiles(machine, candidates, futures, evidence_ids)


def execute_screening_request(request, ticket, descriptor, inventory, destination):
    """Add measured bootstrap evidence at the unchanged original finally write."""
    _guard()
    before = _copy.deepcopy(_bootstrap_snapshot())
    case_path = Path(destination).resolve()/'SCREENING_CASE.json'
    original_write = _write_record

    def retained_write(path, value):
        if (Path(path).resolve() == case_path and isinstance(value, dict)
                and value.get('schema') == 'UDM_ADMISSION_ONLY_CASE_V45'
                and 'bootstrap_attempts' not in value):
            value['bootstrap_attempts'] = {
                'before': before, 'after': _copy.deepcopy(_bootstrap_snapshot())}
        return original_write(path, value)

    namespace = dict(globals(), _write_record=retained_write)
    return _bind(_execute_original, namespace)(request, ticket, descriptor, inventory, destination)


_guard()
del _name, _value

if __name__ == '__main__':
    import importlib
    importlib.import_module(MODULE).main()
