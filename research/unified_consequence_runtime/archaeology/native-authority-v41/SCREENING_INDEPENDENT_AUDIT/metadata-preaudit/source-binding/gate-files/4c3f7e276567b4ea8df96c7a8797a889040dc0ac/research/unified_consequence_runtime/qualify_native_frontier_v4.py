"""Thin prospective binding for metadata-only environment authority v4.

Original MSI/V104 policy, native admission/execution/runtime v3 and all v3
files remain unchanged. Only the environment metadata authority, external
frontier records and exact source bindings are versioned here.
"""
from __future__ import annotations

import copy
from pathlib import Path
import re
from types import CodeType, FunctionType

from . import qualify_native_frontier_v3 as _prior
from . import native_environment_v4 as _environment_v4
from .qualify_environment_selection_v4 import SOURCE_GATE_FILES as _metadata_gate_files

_PRIOR_SHA256 = 'd40d188be3565ed5127e06b033dd9cbf8fa32d60977d27ec47b5ae6698189418'
_BASELINE = '95029db0d0b2122836bee7268299461bfbdb5a66'
_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v4.py'

# Copy values, then clone only functions defined by q3 into this new module's
# namespace. No existing module/function globals or native worker are mutated.
for _name, _value in vars(_prior).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-authority-v4'
PROTOCOL = RECORDS/'FRONTIER_PROTOCOL.json'
METADATA = RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v4'
environment = _environment_v4
DEFAULTS = copy.deepcopy(_prior.DEFAULTS)
DEFAULTS['schema'] = 'UDM_NATIVE_FRONTIER_PROTOCOL_V4'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
ENVIRONMENT_GATE_FILES = tuple(dict.fromkeys((*_metadata_gate_files, *_prior.ENVIRONMENT_GATE_FILES,
    *(('research/unified_consequence_runtime/'+name) for name in (
        'qualify_native_frontier_v4.py', 'test_qualify_native_frontier_v4.py',
        'test_native_frontier_v4_entrypoint.py', 'test_frontier_v4_preparation_tools.py',
        'test_frontier_v4_curation_lineage.py',
        'test_frontier_v4_historical_portability.py',
        'archaeology/native-authority-v4/HISTORICAL_REPOSITORIES.json',
        'archaeology/native-authority-v4/curate_frontier.py',
        'archaeology/native-authority-v4/prepare_records.py')),
    '.github/workflows/udm-prospective-native-selection-v4.yml')))

# These literals are external controller identities, not native algorithms or
# receipt semantics. Fail closed if a pinned function loses its reviewed site.
_OLD_SOURCE_PATH = 'research/unified_consequence_runtime/qualify_native_frontier_v3.py'
_OLD_BASELINE = 'fa6bb190eff9b374ab7a95aaf9c618ad2db31419'
_LITERAL_BINDINGS = {
    'require_screening_manifest': {':'+_OLD_SOURCE_PATH: ':'+_SOURCE_PATH},
    'cli_authority': {_OLD_SOURCE_PATH: _SOURCE_PATH},
    'write_freeze': {_OLD_BASELINE: _BASELINE,
                     'UDM_NATIVE_FRONTIER_FREEZE_V3': 'UDM_NATIVE_FRONTIER_FREEZE_V4'},
    'check_freeze': {_OLD_BASELINE: _BASELINE,
                     'UDM_NATIVE_FRONTIER_FREEZE_V3': 'UDM_NATIVE_FRONTIER_FREEZE_V4'},
    'screening_request': {_OLD_BASELINE: _BASELINE},
    'qualify': {'UDM_NATIVE_FRONTIER_RESULT_V3': 'UDM_NATIVE_FRONTIER_RESULT_V4'},
}


def _literal_code(code, replacements):
    found = set()
    def visit(current):
        constants = []
        for value in current.co_consts:
            if isinstance(value, CodeType):
                value = visit(value)
            elif isinstance(value, str) and value in replacements:
                found.add(value)
                value = replacements[value]
            constants.append(value)
        return current.replace(co_consts=tuple(constants))
    result = visit(code)
    if found != set(replacements):
        raise ValueError('UNKNOWN_V4_CONTROLLER_BINDING_SITE: '+code.co_name)
    return result


for _name, _value in vars(_prior).items():
    if isinstance(_value, FunctionType) and _value.__module__ == _prior.__name__:
        _code = _value.__code__
        if _name in _LITERAL_BINDINGS:
            _code = _literal_code(_code, _LITERAL_BINDINGS[_name])
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

_reconstruct_profiles = reconstruct_profiles


def _guard():
    if (digest(Path(_prior.__file__).read_bytes()) != _PRIOR_SHA256
            or digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('frozen metadata-only prospective controller source changed')
    _prior._guard()


def require_environment_gate(value):
    """Require qualified v4 metadata inference over unchanged native authority."""
    _guard()
    gate = value.get('environment_gate')
    fields = {'status', 'source_commit', 'run_id', 'artifact_id', 'artifact_sha256',
              'qualification_result_sha256', 'result_path'}
    if (not isinstance(gate, dict) or set(gate) != fields
            or gate['status'] != 'ADMISSION_ONLY_QUALIFIED'
            or not re.fullmatch('[0-9a-f]{40}', gate.get('source_commit', ''))
            or any(type(gate[k]) is not int or gate[k] <= 0 for k in ('run_id', 'artifact_id'))
            or any(not re.fullmatch('[0-9a-f]{64}', gate.get(k, ''))
                   for k in ('artifact_sha256', 'qualification_result_sha256'))):
        raise ValueError('independent v4 environment qualification is required before prospective freeze')
    result = _bound_json({'path': gate['result_path'], 'sha256': gate['qualification_result_sha256']})
    if (result.get('status') != gate['status'] or result.get('source_commit') != gate['source_commit']
            or result.get('schema') != 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V4'
            or result.get('freeze', {}).get('schema') != 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V4'
            or result.get('first_task_gate', {}).get('status') != 'PASS'
            or any(result.get('verdicts', {}).get('G'+str(i)) != 'UNKNOWN' for i in range(2, 7))):
        raise ValueError('v4 environment qualification is not a separate admission-only gate')
    qualified = result['freeze'].get('files', {})
    for name in ENVIRONMENT_GATE_FILES:
        path = HERE.parents[1]/name
        if not path.is_file() or path.is_symlink() or qualified.get(name) != digest(path.read_bytes()):
            raise ValueError('current environment bridge differs from qualified v4 source: '+name)
    catalog = _bound_json(value['catalog'])
    if (qualified.get(value['catalog']['path']) != value['catalog']['sha256']
            or result['freeze'].get('catalog_sha256') != worker.fingerprint(catalog)):
        raise ValueError('v4 environment qualification does not bind exact catalog')
    return gate


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    """Real importable v4 checker identity over unchanged profile validation."""
    return _reconstruct_profiles(machine, candidates, futures, evidence_ids)


if __name__ == '__main__':
    # The independent checker must have a canonical import identity even when
    # the user invokes this file through Python's -m entrypoint.
    import importlib
    importlib.import_module(MODULE).main()
