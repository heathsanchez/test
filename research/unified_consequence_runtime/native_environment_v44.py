"""Source-native metadata observation before original environment selection.

Only a declared dynamic metadata residual activates the existing original
backend operation. The independent native collector, imports, assertions,
external catalog and effect ceiling remain their original authorities.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import FunctionType, SimpleNamespace
import time
import tomllib

from . import native_environment_v43 as previous
from . import native_environment_v42 as source_environment
from . import native_environment_selection_v41 as static_selection

# Preserve the original inventory consumer API and its unchanged catalog checker.
selection = static_selection
canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
_ORIGINAL_PINS = {str(Path(module.__file__)): sha256(Path(module.__file__).read_bytes())
                  for module in (previous, source_environment, static_selection)}
_DYNAMIC = frozenset(('requires-python', 'dependencies', 'classifiers'))


def _guard():
    previous._guard()
    if sha256(Path(__file__).read_bytes()) != _LOADED_SHA256 or any(
            sha256(Path(name).read_bytes()) != digest for name, digest in _ORIGINAL_PINS.items()):
        raise ValueError('UNKNOWN_V44_ENVIRONMENT_SOURCE_CHANGED')


for _name in ('freeze_runtime', 'validate_runtime', 'installed_package_identity',
              'package_requirements', 'execution_policy', 'record_admission_request'):
    globals()[_name] = getattr(previous, _name)


def diagnose(files, catalog):
    """Choose only an existing justified operation; this grants no native warrant."""
    _guard()
    original = static_selection.select_profile(files, catalog)
    result = {'schema': 'UDM_ENVIRONMENT_RESIDUAL_V44', 'route': 'UNKNOWN',
              'operation': None, 'original_selection': original,
              'native_authority': 'NOT_ESTABLISHED', 'grammar_exhaustion': 'UNKNOWN'}
    if original['status'] == 'CANDIDATE_SOURCE_ENVIRONMENT':
        result['route'] = 'ACTIVATE_EXISTING_ENVIRONMENT'
    elif original.get('reason') == 'UNKNOWN_DYNAMIC_METADATA' and 'setup.py' not in files:
        try:
            data = tomllib.loads(files.get('pyproject.toml', b'').decode())
            dynamic = data.get('project', {}).get('dynamic', [])
            if (isinstance(dynamic, list) and all(isinstance(x, str) for x in dynamic)
                    and set(dynamic) & _DYNAMIC and 'optional-dependencies' not in dynamic
                    and isinstance(data.get('build-system'), dict)):
                result.update(route='ACTIVATE_EXISTING_METADATA_OBSERVATION',
                              operation='source.observe_native_metadata')
        except (ValueError, TypeError, UnicodeError, AttributeError):
            pass
    return result


def build_profile_constraints(files, profile):
    """A finite build candidate check, independent of test-execution authority."""
    _guard()
    data = tomllib.loads(files['pyproject.toml'].decode())
    requirements = data['build-system'].get('requires', [])
    if not isinstance(requirements, list) or any(not isinstance(x, str) for x in requirements):
        raise ValueError('UNKNOWN_ORIGINAL_BUILD_REQUIREMENTS')
    python = data.get('project', {}).get('requires-python')
    constraints = {'declared_python': [], 'python_specifiers': [] if python is None else [python],
                   'python_implementations': [], 'requirements': [
                       {'requirement': str(static_selection.Requirement(value)), 'extra': '',
                        'path': 'pyproject.toml', 'field': 'build-system.requires'}
                       for value in requirements]}
    row = static_selection._evaluate(profile, constraints)
    return dict(row, native_authority='NOT_ESTABLISHED')


def can_repair_native_refusal(status):
    # A backend observation never authorizes suppression or reinterpretation of
    # protected pytest outcomes, collection errors or original skip conditions.
    return False


def bootstrap_snapshot():
    """Actual original backend attempts, including refused/failed invocations."""
    from . import native_metadata_v44 as metadata
    value = metadata.attempt_snapshot()
    return dict(value, backend_calls=value['build_calls'], backend_seconds=value['build_seconds'])


def metadata_environment_identity(interpreter):
    # The original backend observer and the extended native verifier have
    # distinct identity schemas. Neither digest may stand in for the other.
    from . import decisive_native_verify as original
    return original.environment_identity(interpreter)


def profile_attempt_costs(before, after):
    if (after['build_calls'] < before['build_calls'] or after['build_seconds'] < before['build_seconds']
            or after['records'][:len(before['records'])] != before['records']):
        raise ValueError('metadata attempt counters changed or regressed')
    return {'build_calls': after['build_calls']-before['build_calls'],
            'build_seconds': after['build_seconds']-before['build_seconds'],
            'records': after['records'][len(before['records']):], 'inclusive_not_additive': True}


def bind_bootstrap_environment(machine, setup, catalog, observation):
    """Retain the actual verified choice and its exact native environment use."""
    from . import native_environment_selection_v44 as selection
    from . import native_source_v42 as source
    from .native_bootstrap_runtime_v44 import MetadataRuntime
    contract, authority, policy = (setup[key] for key in ('contract', 'authority', 'policy'))
    if setup.get('status') != 'PREPARED':
        raise ValueError('prepared native environment required for selection witness')
    binding = setup['bootstrap_binding']
    value, retained = MetadataRuntime(machine, machine.state.parent/'bootstrap-selection').preflight(binding)
    if dict(observation) != retained:
        raise ValueError('environment choice used another metadata observation')
    identity, files, _ = source.snapshot(contract['repo_path'], authority['baseline_commit'])
    if (identity != retained['source_identity'] or value['commit'] != authority['baseline_commit']
            or value['protocol_binding'] != contract['protocol_binding']):
        raise ValueError('environment selection uses another source or protocol')
    selected = selection.validate_selection(files, catalog, setup['selection'], observation)
    if selected['status'] != 'CANDIDATE_SOURCE_ENVIRONMENT':
        raise ValueError('independent environment choice remains unresolved')
    profile = selected['selected_profile']
    _, _, actual_environment, _ = previous.execution._context(contract, authority, policy)
    runtime_identity = actual_environment['runtime_identity']
    if ('.'.join(map(str, runtime_identity['version_info'][:3])) != profile['python_version']
            or actual_environment['pytest_version'] != profile['pytest_version']
            or runtime_identity['implementation'].lower() != profile['python_implementation'].lower()):
        raise ValueError('selected profile differs from actual native environment')
    build_packages = installed_package_identity(value['interpreter'], profile)
    native_packages = installed_package_identity(contract['interpreter'], profile)
    if fingerprint(native_packages) != setup['pinned_packages_sha256']:
        raise ValueError('native pinned packages differ from independently prepared environment')
    payload = {'schema': 'UDM_VERIFIED_NATIVE_ENVIRONMENT_SELECTION_V44',
        'binding': binding, 'contract_sha256': fingerprint(contract),
        'authority_sha256': fingerprint(authority), 'policy_sha256': fingerprint(policy),
        'catalog': machine.put(catalog), 'selection': machine.put(selected),
        'profile': profile, 'build_packages_sha256': fingerprint(build_packages),
        'native_packages_sha256': fingerprint(native_packages),
        'environment_operation_sha256': _LOADED_SHA256}
    ident = machine.append('native_environment_selection_v44', payload,
                           (binding['capability_id'], binding['consequence_id']))
    machine.flush()
    return dict(binding, environment_selection_id=ident)


def preflight_bootstrap(machine, setup_or_binding, contract, authority, policy):
    from .native_bootstrap_runtime_v44 import MetadataRuntime
    from . import native_source_v42 as source
    binding = setup_or_binding.get('bootstrap_binding') if 'bootstrap_binding' in setup_or_binding else setup_or_binding
    if binding is None:
        return None
    if not isinstance(binding, dict) or 'environment_selection_id' not in binding:
        raise ValueError('native bootstrap requires an exact environment selection witness')
    metadata_binding = {key: value for key, value in binding.items() if key != 'environment_selection_id'}
    value, observation = MetadataRuntime(machine, machine.state.parent/'bootstrap-preflight').preflight(metadata_binding)
    identity, _, _ = source.snapshot(contract['repo_path'], authority['baseline_commit'])
    if (value['commit'] != authority['baseline_commit'] or value['protocol_binding'] != contract['protocol_binding']
            or identity != observation['source_identity']):
        raise ValueError('native environment bootstrap belongs to another source or protocol')
    # The original provisioner independently validates the new execution venv.
    # The observed build interpreter is a separately pinned profile environment.
    # Neither environment is silently substituted for the other.
    nodes = {node.id: node for node in machine.log}
    ident = binding['environment_selection_id']
    if ident not in set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids():
        raise PermissionError('native environment selection witness is withdrawn')
    node = nodes[ident]
    payload = node.payload
    if (node.kind != 'native_environment_selection_v44'
            or tuple(node.premises) != (binding['capability_id'], binding['consequence_id'])
            or payload.get('schema') != 'UDM_VERIFIED_NATIVE_ENVIRONMENT_SELECTION_V44'
            or payload.get('binding') != metadata_binding
            or payload.get('contract_sha256') != fingerprint(contract)
            or payload.get('authority_sha256') != fingerprint(authority)
            or payload.get('policy_sha256') != fingerprint(policy)
            or payload.get('environment_operation_sha256') != _LOADED_SHA256):
        raise ValueError('native environment selection witness belongs to another execution context')
    catalog, selected = machine.get(payload['catalog']), machine.get(payload['selection'])
    static_selection._catalog(catalog)
    if (selected.get('selected_profile') != payload['profile']
            or selected.get('catalog_sha256') != fingerprint(catalog)
            or selected.get('constraints', {}).get('observation_evidence', {}).get('observation_sha256')
                != fingerprint(observation)
            or fingerprint(installed_package_identity(value['interpreter'], payload['profile']))
                != payload['build_packages_sha256']
            or fingerprint(installed_package_identity(contract['interpreter'], payload['profile']))
                != payload['native_packages_sha256']):
        raise ValueError('native selection, metadata or pinned environment identity changed')
    previous.execution._context(contract, authority, policy)
    return binding


def provision(spec, root, protocol_binding, *, catalog, runtimes, machine,
              collection_seconds=60, execution_seconds=600):
    from . import native_environment_selection_v44 as selection
    from .native_bootstrap_runtime_v44 import MetadataRuntime, request
    _guard()
    request_id = record_admission_request(machine, spec, protocol_binding)
    root = Path(root).absolute()
    attempts, chosen_binding = [], None
    candidate_observation = None
    selected_profile = None
    started = time.monotonic()

    def choose(files, external_catalog):
        nonlocal chosen_binding, candidate_observation, selected_profile
        diagnosis = diagnose(files, external_catalog)
        if diagnosis['route'] != 'ACTIVATE_EXISTING_METADATA_OBSERVATION':
            return diagnosis['original_selection']
        residual = machine.append('developmental_residual', diagnosis, (request_id,))
        machine.flush()
        for profile in static_selection._catalog(external_catalog):
            ident = profile['id']
            attempt = {'profile_id': ident, 'build_calls': 0, 'residual': residual}
            attempts.append(attempt)
            before = time.monotonic()
            builds_before = bootstrap_snapshot()
            try:
                if ident not in runtimes:
                    attempt['status'] = 'UNKNOWN_INTERPRETER_UNAVAILABLE'
                    continue
                checked = build_profile_constraints(files, profile)
                attempt['constraints'] = checked
                if checked['status'] != 'COMPATIBLE':
                    attempt['status'] = 'UNKNOWN_BUILD_PROFILE'
                    continue
                runtime = runtimes[ident]
                validate_runtime(profile, runtime)
                installed = installed_package_identity(runtime['interpreter'], profile)
                environment = metadata_environment_identity(runtime['interpreter'])
                value = request(root/'metadata-source', spec['base_commit'], runtime['interpreter'],
                    environment_sha256=fingerprint(environment), protocol_binding=protocol_binding,
                    horizon_seconds=min(execution_seconds, 300))
                adapter = MetadataRuntime(machine, root/'native-metadata-bootstrap')
                frontier_id = 'native-metadata-v44:'+fingerprint(value)
                adapter.register(frontier_id, value)
                route = machine.frontiers['frontiers'][frontier_id]
                if route['status'] == 'UNKNOWN_SEARCH':
                    adapter.admit(value)
                activated = machine.select_and_execute_frontier(frontier_id, adapter)
                observation = activated['metadata_observation']
                native_choice = selection.select_profile(files, external_catalog, observation)
                if (native_choice['status'] != 'CANDIDATE_SOURCE_ENVIRONMENT'
                        or native_choice['selected_profile']['id'] != ident):
                    attempt.update(status='UNKNOWN_METADATA_PROFILE', selection=native_choice)
                    continue
                validate_runtime(profile, runtime)
                if installed_package_identity(runtime['interpreter'], profile) != installed:
                    raise ValueError('metadata backend changed independently pinned environment')
                chosen_binding = adapter.bind(activated['capability_id'], activated['consequence'])
                candidate_observation, selected_profile = observation, profile
                attempt.update(status='VERIFIED_METADATA_OBSERVATION_NOT_NATIVE_AUTHORITY',
                               binding=chosen_binding, selection=native_choice)
                return native_choice
            except (ValueError, RuntimeError, OSError, TypeError, KeyError) as error:
                attempt.update(status='UNKNOWN_METADATA_BOOTSTRAP', reason=type(error).__name__+': '+str(error))
            finally:
                attempt['seconds'] = time.monotonic()-before
                attempt.update(profile_attempt_costs(builds_before, bootstrap_snapshot()))
        return diagnosis['original_selection']

    def validate(files, external_catalog, selected):
        if candidate_observation is None:
            return static_selection.validate_selection(files, external_catalog, selected)
        if selected['selected_profile'] != selected_profile:
            raise ValueError('metadata observation selected another environment profile')
        return selection.validate_selection(files, external_catalog, selected, candidate_observation)

    proxy = SimpleNamespace(**dict(vars(static_selection), select_profile=choose, validate_selection=validate))
    original = source_environment._original_provision
    provisioner = FunctionType(original.__code__, dict(original.__globals__, selection=proxy),
                               original.__code__.co_name, original.__defaults__, original.__closure__)
    provisioner.__kwdefaults__ = original.__kwdefaults__
    result = provisioner(spec, root, protocol_binding, catalog=catalog, runtimes=runtimes,
                         collection_seconds=collection_seconds, execution_seconds=execution_seconds)
    result = previous._attach_interface(machine, result, root/'causal-materialization')
    result.update(schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V44', admission_request=request_id,
                  bootstrap_binding=chosen_binding, bootstrap_attempts=attempts)
    if chosen_binding is not None and result['status'] == 'PREPARED':
        result['bootstrap_binding'] = bind_bootstrap_environment(machine, result, catalog, candidate_observation)
        preflight_bootstrap(machine, result, result['contract'], result['authority'], result['policy'])
    result['bootstrap_wall_seconds'] = time.monotonic()-started
    (root/'admission-v44.json').write_text(canonical(result)+'\n')
    machine.costs.append({'phase': 'native_environment_bootstrap_v44',
        'seconds': result['bootstrap_wall_seconds'], 'inclusive_not_additive': True,
        'status': result['status'], 'attempts': attempts})
    return result
