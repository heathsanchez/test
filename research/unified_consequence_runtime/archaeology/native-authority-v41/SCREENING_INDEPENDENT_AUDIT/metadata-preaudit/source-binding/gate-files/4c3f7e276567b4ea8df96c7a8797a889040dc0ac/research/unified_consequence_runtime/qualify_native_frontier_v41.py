"""V4.1 prospective binding over source-pinned V4 MSI/V104 machinery.

Only metadata/environment authority and external frontier identity change.
Native worker/runtime V3, policy algorithms, budgets and prior evidence remain.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
from types import FunctionType

os.environ['GIT_OPTIONAL_LOCKS'] = '0'

from . import qualify_native_frontier_v4 as _carrier
from . import native_environment_v41 as _environment_v41
from .qualify_environment_selection_v41 import SOURCE_GATE_FILES as _metadata_gate_files

_CARRIER_SHA256 = '37cbd2de7d69350d2208afbb4d8fb6bdf8c417bf53cac842ea3e466d566518cc'
if _carrier.digest(Path(_carrier.__file__).read_bytes()) != _CARRIER_SHA256:
    raise ValueError('frozen V4 prospective source differs')

for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-authority-v41'
PROTOCOL = RECORDS/'FRONTIER_PROTOCOL.json'
METADATA = RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v41'
CATALOG_PATH = 'research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
_BASELINE = '7edf1018342b50f73ca226de3e0d0b7acdb31647'
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v41.py'
environment = _environment_v41
DEFAULTS = copy.deepcopy(_carrier.DEFAULTS)
DEFAULTS['schema'] = 'UDM_NATIVE_FRONTIER_PROTOCOL_V41'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
ENVIRONMENT_GATE_FILES = tuple(dict.fromkeys((*_metadata_gate_files, *_carrier.ENVIRONMENT_GATE_FILES,
    CATALOG_PATH, *(('research/unified_consequence_runtime/'+name) for name in (
        'qualify_native_frontier_v41.py', 'test_qualify_native_frontier_v41.py',
        'archaeology/native-authority-v41/curate_frontier.py',
        'archaeology/native-authority-v41/prepare_records.py')),
    '.github/workflows/udm-prospective-native-selection-v41.yml')))

_OLD_SOURCE = 'research/unified_consequence_runtime/qualify_native_frontier_v4.py'
_OLD_BASE = '95029db0d0b2122836bee7268299461bfbdb5a66'
_LITERAL_BINDINGS = {
    'require_screening_manifest': {':'+_OLD_SOURCE: ':'+_SOURCE_PATH},
    'cli_authority': {_OLD_SOURCE: _SOURCE_PATH},
    'write_freeze': {_OLD_BASE: _BASELINE,
                     'UDM_NATIVE_FRONTIER_FREEZE_V4': 'UDM_NATIVE_FRONTIER_FREEZE_V41'},
    'check_freeze': {_OLD_BASE: _BASELINE,
                     'UDM_NATIVE_FRONTIER_FREEZE_V4': 'UDM_NATIVE_FRONTIER_FREEZE_V41'},
    'screening_request': {_OLD_BASE: _BASELINE},
    'qualify': {'UDM_NATIVE_FRONTIER_RESULT_V4': 'UDM_NATIVE_FRONTIER_RESULT_V41'},
    'require_environment_gate': {
        'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V4': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V41',
        'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V4': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V41',
        'independent v4 environment qualification is required before prospective freeze':
            'independent V41 environment qualification is required before prospective freeze',
        'v4 environment qualification is not a separate admission-only gate':
            'V41 environment qualification is not a separate admission-only gate',
        'current environment bridge differs from qualified v4 source: ':
            'current environment bridge differs from qualified V41 source: ',
        'v4 environment qualification does not bind exact catalog':
            'V41 environment qualification does not bind exact catalog'},
}

# Preserve each existing inner alias by its name. Recapturing a wrapped
# reconstruct_profiles as its own inner body would introduce recursion.
for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _code = _value.__code__
        if _name in _LITERAL_BINDINGS:
            _code = _carrier._literal_code(_code, _LITERAL_BINDINGS[_name])
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

_qualified_environment_gate = require_environment_gate


def _guard():
    if (digest(Path(_carrier.__file__).read_bytes()) != _CARRIER_SHA256
            or digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('frozen V41 prospective controller source changed')
    _carrier._guard()


def require_environment_gate(value):
    """The new metadata policy needs its own qualified artifact and catalog."""
    _guard()
    descriptor = value.get('catalog')
    if not isinstance(descriptor, dict) or descriptor.get('path') != CATALOG_PATH:
        raise ValueError('exact V41 catalog authority is required')
    return _qualified_environment_gate(value)


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    """Importable V41 checker over the preserved original inner algorithm."""
    return _reconstruct_profiles(machine, candidates, futures, evidence_ids)


if __name__ == '__main__':
    import importlib
    importlib.import_module(MODULE).main()
