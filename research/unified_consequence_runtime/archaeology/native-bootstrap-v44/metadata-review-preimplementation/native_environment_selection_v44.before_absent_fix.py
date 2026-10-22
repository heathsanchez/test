"""Verified native metadata can close declared pyproject environment unknowns.

The original V41 derivation and finite catalog selection code still execute.
Only a private tomllib semantic view supplies independently observed values for
three declared dynamic fields. Raw source bytes/hashes, test requirements, tox
configuration and all native execution authority remain original inputs.
"""
from __future__ import annotations

import copy
from pathlib import Path
from types import FunctionType, SimpleNamespace
import tomllib

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from . import native_environment_selection_v41 as previous
from . import native_metadata_v44 as metadata

CONSTRAINT_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_CONSTRAINTS_V44'
SELECTION_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_SELECTION_V44'
CATALOG_SCHEMA = previous.CATALOG_SCHEMA
canonicalize_name = previous.canonicalize_name
Requirement = previous.Requirement
_ALLOWED_DYNAMIC = {'requires-python', 'dependencies', 'classifiers'}
_ENVIRONMENT_DYNAMIC = _ALLOWED_DYNAMIC | {'optional-dependencies'}
_ORIGINAL_PIN = '951776b61bcb90df29e106e7555d1bcd972f218744b00faa9a17cc9a4827317a'
_LOADED_SHA256 = metadata.source.sha256(Path(__file__).read_bytes())


def _guard():
    previous._guard()
    metadata._guard()
    if (metadata.source.sha256(Path(previous.__file__).read_bytes()) != _ORIGINAL_PIN
            or metadata.source.sha256(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_V44_METADATA_SELECTOR_SOURCE_CHANGED')


def _signature(text):
    requirement = Requirement(text)
    if requirement.url:
        raise ValueError('dependency URL is not frozen authority')
    return (canonicalize_name(requirement.name), tuple(sorted(requirement.extras)),
            str(requirement.specifier), str(requirement.marker or ''))


def _view(files, observation):
    metadata.require_verified(observation)
    observed = metadata.validate_observation(observation['repo_path'], observation['commit'],
        observation['interpreter'], observation, environment_sha256=observation['environment_sha256'])
    if metadata._file_digest(files) != observation['source_files_sha256']:
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_SOURCE_FILES_DIFFER')
    if 'setup.py' in files:
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_SCOPE: setup.py metadata remains independent')
    original = tomllib.loads(files['pyproject.toml'].decode('utf-8'))
    project = original.get('project', {})
    dynamic = project.get('dynamic', [])
    if (not isinstance(project, dict) or not isinstance(dynamic, list)
            or any(not isinstance(field, str) for field in dynamic) or len(dynamic) != len(set(dynamic))):
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_SCOPE: dynamic field grammar')
    fields = set(dynamic) & _ENVIRONMENT_DYNAMIC
    if fields - _ALLOWED_DYNAMIC:
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_SCOPE: unsupported dynamic optional dependencies')
    if any(field in project for field in fields):
        raise ValueError('UNKNOWN_CONFLICTING_METADATA: field is static and dynamic')
    if ('name' in project and canonicalize_name(project['name']) != canonicalize_name(observed['name'])
            or 'version' in project and Version(project['version']) != Version(observed['version'])):
        raise ValueError('UNKNOWN_CONFLICTING_METADATA: source and wheel distribution identity')
    if 'requires-python' in project and (observed['requires_python'] is None
            or SpecifierSet(project['requires-python']) != SpecifierSet(observed['requires_python'])):
        raise ValueError('UNKNOWN_CONFLICTING_METADATA: static Python requirement')
    if 'classifiers' in project and set(project['classifiers']) != set(observed['classifiers']):
        raise ValueError('UNKNOWN_CONFLICTING_METADATA: static classifiers')
    if 'dependencies' in project:
        required = {_signature(text) for text in project['dependencies']}
        runtime = set()
        marker_variables = previous._namespace['_marker_variables']
        for text in observed['requires_dist']:
            requirement = Requirement(text)
            if not requirement.marker or 'extra' not in marker_variables(requirement.marker._markers):
                runtime.add(_signature(text))
        if required != runtime:
            raise ValueError('UNKNOWN_CONFLICTING_METADATA: static dependencies')
    result = copy.deepcopy(original)
    project = result.setdefault('project', {})
    if 'requires-python' in fields:
        if observed['requires_python'] is None:
            raise ValueError('UNKNOWN_METADATA_OBSERVATION_SCOPE: absent dynamic Requires-Python')
        project['requires-python'] = observed['requires_python']
    if 'classifiers' in fields:
        project['classifiers'] = list(observed['classifiers'])
    if 'dependencies' in fields:
        # Extra markers remain intact. The original evaluator activates only
        # declared test extras from the unchanged static optional table.
        project['dependencies'] = list(observed['requires_dist'])
    project['dynamic'] = [field for field in dynamic if field not in fields]
    return result, sorted(fields)


def derive_constraints(files, observation=None):
    _guard()
    if observation is None:
        result = previous.derive_constraints(files)
        return dict(result, schema=CONSTRAINT_SCHEMA)
    # Forged/altered process-local authority and wrong source are hard refusals,
    # not parser fallbacks that could accidentally discard unknown constraints.
    metadata.require_verified(observation)
    metadata.validate_observation(observation['repo_path'], observation['commit'],
        observation['interpreter'], observation, environment_sha256=observation['environment_sha256'])
    if metadata._file_digest(files) != observation['source_files_sha256']:
        raise ValueError('UNKNOWN_METADATA_OBSERVATION_SOURCE_FILES_DIFFER')
    try:
        semantic, fields = _view(files, observation)
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        result = previous.derive_constraints(files)
        result.update(schema=CONSTRAINT_SCHEMA, status='UNKNOWN')
        result['reasons'].insert(0, {'reason': str(error).split(':', 1)[0], 'detail': str(error)})
        return result
    original_raw = files['pyproject.toml'].decode('utf-8')
    def loads(raw, *args, **kwargs):
        if raw != original_raw:
            raise ValueError('UNKNOWN_METADATA_SEMANTIC_VIEW_SCOPE')
        return copy.deepcopy(semantic)
    namespace = dict(vars(previous))
    namespace['_namespace'] = dict(previous._namespace, __file__=__file__,
        CONSTRAINT_SCHEMA=CONSTRAINT_SCHEMA, SELECTION_SCHEMA=SELECTION_SCHEMA)
    namespace['_walker_namespace'] = dict(previous._walker_namespace, __file__=__file__,
        CONSTRAINT_SCHEMA=CONSTRAINT_SCHEMA, SELECTION_SCHEMA=SELECTION_SCHEMA,
        tomllib=SimpleNamespace(loads=loads))
    result = FunctionType(previous.derive_constraints.__code__, namespace, 'derive_constraints')(files)
    result['schema'] = CONSTRAINT_SCHEMA
    result['observation_evidence'] = {
        'schema': metadata.OBSERVATION_SCHEMA,
        'observation_sha256': metadata.source.fingerprint(observation),
        'source_identity': observation['source_identity'],
        'source_files_sha256': observation['source_files_sha256'],
        'environment_sha256': observation['environment_sha256'],
        'metadata_sha256': metadata.source.fingerprint(observation['metadata']),
        'replaced_declared_dynamic_fields': fields,
        'scope': 'Original source-native packaging observation; no native execution warrant.'}
    return result


def select_profile(files, catalog, observation=None):
    _guard()
    namespace = dict(previous._namespace, __file__=__file__,
        CONSTRAINT_SCHEMA=CONSTRAINT_SCHEMA, SELECTION_SCHEMA=SELECTION_SCHEMA,
        derive_constraints=lambda original: derive_constraints(original, observation=observation))
    original = previous._namespace['select_profile']
    return FunctionType(original.__code__, namespace, 'select_profile')(files, catalog)


def validate_selection(files, catalog, selection, observation=None):
    expected = select_profile(files, catalog, observation=observation)
    if not isinstance(selection, dict) or metadata.source.canonical(selection) != metadata.source.canonical(expected):
        raise ValueError('UNKNOWN_SELECTION_IDENTITY: selection differs from source/catalog/observation')
    return expected


# Existing finite catalog validation, requirement types and policy authority.
_catalog = previous._catalog
_evaluate = previous._evaluate
