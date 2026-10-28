"""Private V45 bindings of the original source-native provisioner.

Profile choice, package checks, typed source transport and backend operations
retain their original algorithms. Namespace authority is never projected into
an earlier verifier. The existing V44 Machine owns all causal records.
"""
from __future__ import annotations

from pathlib import Path
from types import FunctionType, SimpleNamespace

from . import native_environment_v44 as previous
from . import native_environment_v43 as interface
from . import native_environment_v42 as source_environment
from . import native_environment_v3 as portable
from . import native_admission_v45 as admission
from . import native_execution_v45 as execution
from . import native_materialization_v43 as original_materialization
from . import developmental_machine_v44 as framework

canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
selection = previous.selection
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
_PINS = {module.__name__: (module, sha256(Path(module.__file__).read_bytes())) for module in
         (previous, interface, source_environment, portable, admission, execution,
          original_materialization, framework)}


def _guard():
    previous._guard()
    original_materialization._guard()
    framework._guard()
    admission.assert_source_identity()
    execution._runner_hash()
    if (sha256(Path(__file__).read_bytes()) != _LOADED_SHA256
            or any(sha256(Path(module.__file__).read_bytes()) != expected
                   for module, expected in _PINS.values())):
        raise ValueError('UNKNOWN_V45_ENVIRONMENT_SOURCE_CHANGED')


def _bind(function, namespace):
    result = FunctionType(function.__code__, namespace, function.__name__,
                          function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def _provision_context(contract, authority, policy):
    # The original V2 constructor precedes the generated-build field. Its
    # tracked-only output is extended before entering the explicit V45 worker.
    return execution._context(dict(contract, generated_build=None), authority, policy)


_provision_execution = SimpleNamespace(**dict(vars(execution), _context=_provision_context))
_v2_namespace = dict(source_environment._v2_globals, execution=_provision_execution,
                     derive_suite_contract=admission.derive_suite_contract)
for _name, _function in list(_v2_namespace.items()):
    if isinstance(_function, FunctionType) and _function.__module__ == source_environment._v2.__name__:
        _v2_namespace[_name] = _bind(_function, _v2_namespace)
_v2 = SimpleNamespace(**_v2_namespace)
_portable_namespace = dict(vars(portable), previous=_v2, selection=selection,
                           execution=_provision_execution, _snapshot=source_environment.source.snapshot, _guard=_guard)
for _name, _function in vars(portable).items():
    if isinstance(_function, FunctionType) and _function.__module__ == portable.__name__ and _name != '_guard':
        _portable_namespace[_name] = _bind(_function, _portable_namespace)
        globals()[_name] = _portable_namespace[_name]
_original_provision = _portable_namespace['provision']

# Generated materialization retains the original V43 instrument algorithm and
# receipt format, with explicit V45 contract and namespace dependencies.
_materialization_namespace = dict(vars(original_materialization), build=execution.build,
    admission=admission, framework=framework, _guard=_guard, __file__=__file__,
    _SOURCE_PINS={**original_materialization._SOURCE_PINS,
                  str(Path(__file__)): _LOADED_SHA256,
                  str(Path(admission.__file__)): sha256(Path(admission.__file__).read_bytes()),
                  str(Path(execution.__file__)): sha256(Path(execution.__file__).read_bytes())})
for _name, _function in vars(original_materialization).items():
    if isinstance(_function, FunctionType) and _function.__module__ == original_materialization.__name__:
        if _name != '_guard':
            _materialization_namespace[_name] = _bind(_function, _materialization_namespace)
MaterializationRuntime = type('MaterializationRuntime', (original_materialization.MaterializationRuntime,),
    {name: _bind(function, _materialization_namespace)
     for name, function in vars(original_materialization.MaterializationRuntime).items()
     if isinstance(function, FunctionType)})
_materialization_namespace['MaterializationRuntime'] = MaterializationRuntime
materialization = SimpleNamespace(**_materialization_namespace)

_interface_namespace = dict(vars(interface), execution=execution, build=execution.build,
    materialization=materialization, framework=framework, _guard=_guard,
    previous=SimpleNamespace(execution=execution))
_original_attach = _bind(interface._attach_interface, _interface_namespace)


def _attach_interface(machine, setup, output):
    _guard()
    if setup.get('status') == 'PREPARED':
        if (setup.get('contract', {}).get('schema') != execution.SCHEMA
                or setup.get('policy', {}).get('schema') != execution.POLICY_SCHEMA):
            raise ValueError('explicit V45 prepared contract and policy required')
        if setup['contract'].get('generated_build') is not None:
            raise ValueError('UNKNOWN_V45_PREPARED_GENERATED_HANDOFF_ALREADY_BOUND')
        setup = dict(setup, contract=dict(setup['contract'], generated_build=None))
    return dict(_original_attach(machine, setup, output), schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V45')


_previous_proxy = SimpleNamespace(**dict(vars(interface), execution=execution, _attach_interface=_attach_interface))
_namespace = dict(vars(previous), previous=_previous_proxy, source_environment=SimpleNamespace(
    **dict(vars(source_environment), _original_provision=_original_provision)), _guard=_guard,
    _LOADED_SHA256=_LOADED_SHA256)
for _name, _function in vars(previous).items():
    if isinstance(_function, FunctionType) and _function.__module__ == previous.__name__ and _name not in ('_guard', 'provision'):
        _namespace[_name] = _bind(_function, _namespace)
        globals()[_name] = _namespace[_name]
_provision = _bind(previous.provision, _namespace)


def provision(spec, root, protocol_binding, *, catalog, runtimes, machine,
              collection_seconds=60, execution_seconds=600):
    _guard()
    if not isinstance(machine, framework.Machine):
        raise ValueError('V45 admission requires the existing V44 Machine')
    result = _provision(spec, root, protocol_binding, catalog=catalog, runtimes=runtimes,
                        machine=machine, collection_seconds=collection_seconds,
                        execution_seconds=execution_seconds)
    result = dict(result, schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V45',
        typed_source_operation={'environment_sha256': _LOADED_SHA256,
            'source_sha256': sha256(Path(source_environment.source.__file__).read_bytes()),
            'admission_sha256': sha256(Path(admission.__file__).read_bytes()),
            'execution_sha256': execution._runner_hash(),
            'inherited_selection_sha256': source_environment._SOURCE_PINS['native_environment_selection_v41.py']})
    (Path(root)/'admission-v45.json').write_text(canonical(result)+'\n')
    return result


_guard()
del _name, _function
