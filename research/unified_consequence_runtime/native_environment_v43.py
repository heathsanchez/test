"""Original environment provisioning with an explicit causal build handoff.

The original profile, package, source and assertion checks run unchanged. The
new handoff admits one fixed declared-backend operation for the actual target
environment; it never selects a source-specific repair or a scientific verdict.
"""
from __future__ import annotations

import json
from pathlib import Path
import secrets
import time

from . import native_environment_v42 as previous
from . import native_execution_v43 as execution
from . import native_build_v43 as build
from . import native_materialization_v43 as materialization
from . import native_runtime_v43 as native_runtime
from . import developmental_machine_v43 as framework

canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
selection = previous.selection
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
_PINS = {module.__name__: (module, sha256(Path(module.__file__).read_bytes()))
         for module in (previous, execution, build, materialization, native_runtime, framework)}


def _guard():
    if sha256(Path(__file__).read_bytes()) != _LOADED_SHA256:
        raise ValueError('UNKNOWN_V43_ENVIRONMENT_SOURCE_CHANGED')
    for module, expected in _PINS.values():
        if sha256(Path(module.__file__).read_bytes()) != expected:
            raise ValueError('UNKNOWN_V43_ENVIRONMENT_DEPENDENCY_CHANGED')
    previous._guard()
    execution._runner_hash()
    materialization._guard()


# Runtime/profile inference and pinned package provisioning retain their original
# executable definitions, including checks after the target distribution install.
for _name in ('freeze_runtime', 'validate_runtime', 'installed_package_identity',
              'package_requirements', 'execution_policy'):
    globals()[_name] = getattr(previous, _name)


def record_admission_request(machine, spec, binding):
    if not isinstance(machine, framework.Machine):
        raise ValueError('V43 admission requires the existing versioned Machine')
    payload = {'schema': 'UDM_REQUESTED_NATIVE_ADMISSION_V43', 'spec_sha256': fingerprint(spec),
               'spec': machine.put(spec), 'protocol_binding': binding,
               'authority_ceiling': json.loads(canonical(native_runtime.AUTHORITY))}
    for node in machine.log:
        if node.kind == 'native_admission_request_v43' and node.payload == payload:
            return node.id
    ident = machine.append('native_admission_request_v43', payload)
    machine.flush()
    return ident


def _attach_interface(machine, setup, output):
    """Authenticate an existing exact setup; also used by local native controls.

    This does not assert that its caller performed original source provisioning:
    the native context, source authority and actual environment are rechecked.
    """
    _guard()
    if not isinstance(machine, framework.Machine):
        raise ValueError('V43 interface requires a real Machine')
    result = json.loads(canonical(setup))
    if result.get('status') != 'PREPARED':
        return dict(result, schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V43')
    contract, policy = result['contract'], result['policy']
    if contract.get('schema') != previous.execution.SCHEMA or policy.get('schema') != previous.execution.POLICY_SCHEMA:
        raise ValueError('original V42 prepared contract and policy required')
    contract = dict(contract, schema=execution.SCHEMA, generated_build=None)
    policy = dict(policy, schema=execution.POLICY_SCHEMA)
    execution._context(contract, result['authority'], policy)
    result.update(schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V43', contract=contract, policy=policy,
                  materialization_capability=None, materialization_binding=None)
    _, files, _ = execution.source.snapshot(contract['repo_path'], result['authority']['baseline_commit'])
    try:
        build.declared_outputs(files)
    except ValueError as error:
        # The fixed tracked-only path still has to pass the original native
        # collector. A rejected generated declaration never licenses an import.
        result['materialization_status'] = 'TRACKED_ONLY_OR_UNKNOWN_UNSUPPORTED_DECLARATION'
        result['materialization_reason'] = str(error)
        return result
    request = materialization.request(contract, result['authority'], policy)
    adapter = materialization.MaterializationRuntime(machine, Path(output))
    frontier_id = 'native-materialization-v43:' + fingerprint(request)
    registration = adapter.register(frontier_id, request)
    route = machine.frontiers['frontiers'][frontier_id]
    if route['status'] == 'UNKNOWN_SEARCH':
        adapter.admit(request)
    activated = machine.select_and_execute_frontier(frontier_id, adapter)
    if activated['status'] != 'READY':
        return dict(result, status='UNKNOWN_NATIVE_MATERIALIZATION', materialization_status=activated['status'])
    contract = dict(contract, generated_build=activated['materialization'])
    binding = adapter.bind_native(activated['capability_id'], contract, result['authority'], policy)
    execution._context(contract, result['authority'], policy)
    result.update(contract=contract, materialization_capability=activated['capability_id'],
                  materialization_binding=binding, materialization_frontier=frontier_id,
                  materialization_registration=registration, materialization_status='AUTHENTICATED_BUILD_ONLY')
    return result


def provision(spec, root, protocol_binding, *, catalog, runtimes, machine,
              collection_seconds=60, execution_seconds=600):
    _guard()
    request_id = record_admission_request(machine, spec, protocol_binding)
    started, before = time.monotonic(), build.attempt_snapshot()
    attempt = machine.state.parent/'environment-v43-attempts'/secrets.token_hex(16)
    attempt.mkdir(parents=True, exist_ok=False)
    inputs = {'spec': spec, 'protocol_binding': protocol_binding, 'catalog': catalog, 'runtimes': runtimes,
              'collection_seconds': collection_seconds, 'execution_seconds': execution_seconds,
              'request_id': request_id, 'environment_source_sha256': _LOADED_SHA256}
    (attempt/'INPUT.json').write_text(canonical(inputs)+'\n')
    result = None
    try:
        result = previous.provision(spec, root, protocol_binding, catalog=catalog, runtimes=runtimes,
                                    collection_seconds=collection_seconds, execution_seconds=execution_seconds)
        result = _attach_interface(machine, result, Path(root)/'causal-materialization')
        result['admission_request'] = request_id
        return result
    except (ValueError, RuntimeError, OSError, TypeError) as error:
        result = {'schema': 'UDM_SOURCE_ENVIRONMENT_ADMISSION_V43', 'status': 'UNKNOWN_NATIVE_MATERIALIZATION',
                  'reason': type(error).__name__+': '+str(error), 'admission_request': request_id}
        return result
    finally:
        after = build.attempt_snapshot()
        row = {'phase': 'native_environment_v43_handoff', 'seconds': time.monotonic()-started,
               'output': str(attempt), 'status': result.get('status') if result else 'UNKNOWN_INTERRUPTED',
               'builder_attempts_before': before, 'builder_attempts_after': after,
               'inclusive_not_additive': True}
        machine.costs.append(row)
        (attempt/'ATTEMPT.json').write_text(canonical(row)+'\n')
        if result is not None:
            (attempt/'RESULT.json').write_text(canonical(result)+'\n')
            if Path(root).is_dir():
                (Path(root)/'admission-v43.json').write_text(canonical(result)+'\n')


