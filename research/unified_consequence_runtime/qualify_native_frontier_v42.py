"""Typed-source admission binding for the existing prospective MSI/V104 loop.

This installs source transport, worker and runtime V42 into private copies of
the previous controller. Search, policy selection, budgets and protected-result
rules retain their original executable code. Importing performs no task query.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
from types import FunctionType, SimpleNamespace

os.environ['GIT_OPTIONAL_LOCKS'] = '0'

from . import qualify_native_frontier_v4 as _carrier
from . import native_environment_v42 as _environment_v42
from . import native_execution_v42 as _worker_v42
from . import native_source_v42 as _source_v42
from . import decisive_native as _catalog_carrier
from .qualify_native_authority_v42 import SOURCE_GATE_FILES as _gate_files

_CARRIER_SHA256 = '37cbd2de7d69350d2208afbb4d8fb6bdf8c417bf53cac842ea3e466d566518cc'
_CATALOG_CARRIER_SHA256 = '1c4143ea4f136298cca2885a5ff63d4ad83c85eeb64f2f1d1b3d7ba701e82b04'
if _carrier.digest(Path(_carrier.__file__).read_bytes()) != _CARRIER_SHA256:
    raise ValueError('frozen V4 prospective source differs')
if _carrier.digest(Path(_catalog_carrier.__file__).read_bytes()) != _CATALOG_CARRIER_SHA256:
    raise ValueError('frozen original native constructor catalog source differs')

for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-authority-v42'
PROTOCOL = RECORDS/'FRONTIER_PROTOCOL.json'
METADATA = RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v42'
CATALOG_PATH = 'research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
_BASELINE = 'dc59c8fcee6efede520c531eba5e42e7b84a1a9f'
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v42.py'
environment = _environment_v42
worker = _worker_v42
DEFAULTS = copy.deepcopy(_carrier.DEFAULTS)
DEFAULTS['schema'] = 'UDM_NATIVE_FRONTIER_PROTOCOL_V42'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
ENVIRONMENT_GATE_FILES = tuple(dict.fromkeys((*_gate_files,
    CATALOG_PATH, *(('research/unified_consequence_runtime/'+name) for name in (
        'qualify_native_frontier_v42.py', 'test_qualify_native_frontier_v42.py',
        'native_source_v42.py', 'native_admission_v42.py', 'native_environment_v42.py',
        'native_execution_v42.py', 'native_runtime_v42.py',
        'archaeology/native-authority-v42/curate_frontier.py',
        'archaeology/native-authority-v42/prepare_records.py')),
    '.github/workflows/udm-prospective-native-selection-v42.yml')))

_OLD_SOURCE = 'research/unified_consequence_runtime/qualify_native_frontier_v4.py'
_OLD_BASE = '95029db0d0b2122836bee7268299461bfbdb5a66'
_LITERAL_BINDINGS = {
    'require_screening_manifest': {':'+_OLD_SOURCE: ':'+_SOURCE_PATH},
    'cli_authority': {_OLD_SOURCE: _SOURCE_PATH},
    'write_freeze': {_OLD_BASE: _BASELINE,
                     'UDM_NATIVE_FRONTIER_FREEZE_V4': 'UDM_NATIVE_FRONTIER_FREEZE_V42'},
    'check_freeze': {_OLD_BASE: _BASELINE,
                     'UDM_NATIVE_FRONTIER_FREEZE_V4': 'UDM_NATIVE_FRONTIER_FREEZE_V42'},
    'screening_request': {_OLD_BASE: _BASELINE},
    'qualify': {'UDM_NATIVE_FRONTIER_RESULT_V4': 'UDM_NATIVE_FRONTIER_RESULT_V42'},
    'require_environment_gate': {
        'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V4': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V42',
        'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V4': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V42',
        'independent v4 environment qualification is required before prospective freeze':
            'independent V42 environment qualification is required before prospective freeze',
        'v4 environment qualification is not a separate admission-only gate':
            'V42 environment qualification is not a separate admission-only gate',
        'current environment bridge differs from qualified v4 source: ':
            'current environment bridge differs from qualified V42 source: ',
        'v4 environment qualification does not bind exact catalog':
            'V42 environment qualification does not bind exact catalog'},
}

for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _code = _value.__code__
        if _name in _LITERAL_BINDINGS:
            _code = _carrier._literal_code(_code, _LITERAL_BINDINGS[_name])
        if _name == '_prepare':
            # The old function imports its runtime locally: rebinding globals
            # alone cannot select the versioned runtime in a fresh process.
            _names = {'native_runtime_v3': 'native_runtime_v42',
                      'NativeRuntimeV3': 'NativeRuntimeV42'}
            if any(_code.co_names.count(old) != 1 for old in _names):
                raise ValueError('UNKNOWN_V42_RUNTIME_IMPORT_BINDING_SITE')
            _code = _code.replace(co_names=tuple(_names.get(n, n) for n in _code.co_names))
            # IMPORT_FROM also uses the fromlist stored in co_consts.
            _consts = tuple(('NativeRuntimeV42',) if x == ('NativeRuntimeV3',) else x
                            for x in _code.co_consts)
            if _code.co_consts.count(('NativeRuntimeV3',)) != 1:
                raise ValueError('UNKNOWN_V42_RUNTIME_FROMLIST_BINDING_SITE')
            _code = _code.replace(co_consts=_consts)
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

_qualified_environment_gate = require_environment_gate

# The constructor algorithm itself is unchanged. Only its independently
# reconstructed source inventory dependency changes, including in the -m CLI.
_catalog_globals = dict(vars(_catalog_carrier))
_catalog_globals['verifier'] = SimpleNamespace(**dict(vars(_catalog_carrier.verifier),
    _snapshot=_source_v42.snapshot, source_identity=_source_v42.source_identity))
catalog = FunctionType(_catalog_carrier.catalog.__code__, _catalog_globals, 'catalog',
                       _catalog_carrier.catalog.__defaults__, _catalog_carrier.catalog.__closure__)
catalog.__kwdefaults__ = _catalog_carrier.catalog.__kwdefaults__


def _guard():
    if (digest(Path(_carrier.__file__).read_bytes()) != _CARRIER_SHA256
            or digest(Path(_catalog_carrier.__file__).read_bytes()) != _CATALOG_CARRIER_SHA256
            or digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('frozen V42 prospective controller source changed')
    _carrier._guard()
    worker._runner_hash()


def require_environment_gate(value):
    """Admission V42 needs its own archived independent qualification."""
    _guard()
    descriptor = value.get('catalog')
    if not isinstance(descriptor, dict) or descriptor.get('path') != CATALOG_PATH:
        raise ValueError('exact unchanged catalog authority is required for V42')
    return _qualified_environment_gate(value)


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    """Importable V42 checker over the unchanged native profile algorithm."""
    return _reconstruct_profiles(machine, candidates, futures, evidence_ids)


if __name__ == '__main__':
    import importlib
    importlib.import_module(MODULE).main()
