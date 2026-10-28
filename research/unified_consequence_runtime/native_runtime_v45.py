"""V45 namespace authority through the existing native Machine/CAS runtime.

Original repeated verification, restoration and causal withdrawal algorithms
remain in force. The new binding supplies no external permission.
"""
from pathlib import Path
from types import FunctionType
import json
import secrets
import time

from . import native_runtime_v44 as previous
from . import native_runtime_v43 as materialized
from . import native_runtime_v3 as portable
from . import native_execution_v45 as verifier
from . import native_admission_v45 as admission
from . import developmental_machine_v44 as framework
from . import native_environment_v45 as environment

frozen = materialized.frozen
AUTHORITY = frozen._copy(frozen.AUTHORITY)
_LOADED_SOURCE_SHA256 = frozen._sha(__file__)
_PINS = {module.__name__: (module, frozen._sha(module.__file__)) for module in
         (previous, materialized, portable, verifier, admission, framework, environment)}
_runtime_globals = dict(vars(frozen), verifier=verifier, admission=admission, framework=framework,
    AUTHORITY=AUTHORITY, __file__=__file__, json=json, secrets=secrets, time=time)


def _check_sources():
    previous._check_sources()
    environment._guard()
    if (frozen._sha(__file__) != _LOADED_SOURCE_SHA256
            or any(frozen._sha(module.__file__) != expected for module, expected in _PINS.values())):
        raise ValueError('UNKNOWN_V45_NATIVE_RUNTIME_SOURCE_CHANGED')
    verifier._runner_hash()


def _bind(function):
    value = FunctionType(function.__code__, _runtime_globals, function.__name__,
                         function.__defaults__, function.__closure__)
    value.__kwdefaults__ = function.__kwdefaults__
    return value


_runtime_init = _bind(frozen.NativeRuntimeV2.__init__)
_runtime_inputs = _bind(frozen.NativeRuntimeV2._inputs)
_runtime_scope = _bind(frozen.NativeRuntimeV2._scope)
_runtime_expected_scope = _bind(frozen.NativeRuntimeV2._expected_scope)
_runtime_admit = _bind(frozen.NativeRuntimeV2.admit)


class NativeRuntimeV45(materialized.NativeRuntimeV43):
    def __init__(self, machine, contract, authority, certificate, policy, output, *,
                 materialization_capability=None, bootstrap_binding=None):
        _check_sources()
        if not isinstance(machine, framework.Machine):
            raise ValueError('V45 native runtime requires the existing V44 Machine')
        self.bootstrap_binding = frozen._copy(bootstrap_binding)
        if self.bootstrap_binding is not None:
            environment.preflight_bootstrap(machine, self.bootstrap_binding, contract, authority, policy)
        self.machine, self.contract = machine, frozen._copy(contract)
        self.suite_authority, self.policy = map(frozen._copy, (authority, policy))
        self.output = Path(output).absolute()
        self.materialization_capability = materialization_capability
        self.materialization_binding = None
        self._check_output()
        self._materialization_preflight()
        _runtime_init(self, machine, contract, authority, certificate, policy, output)

    def _materialization_preflight(self):
        generated = self.contract.get('generated_build')
        if generated is None:
            if self.materialization_capability is not None:
                raise ValueError('tracked-only native runtime has no materialization premise')
            return
        if self.materialization_capability is None:
            raise ValueError('generated native runtime requires a retained live materialization instrument')
        adapter = environment.MaterializationRuntime(self.machine, self.output/'materialization')
        binding = adapter.bind_native(self.materialization_capability, self.contract,
                                      self.suite_authority, self.policy)
        if self.materialization_binding is not None and binding != self.materialization_binding:
            raise ValueError('native materialization generation or retained invocation changed')
        self.materialization_binding = binding

    def _bootstrap_preflight(self):
        if self.bootstrap_binding is not None:
            actual = environment.preflight_bootstrap(self.machine, self.bootstrap_binding,
                self.contract, self.suite_authority, self.policy)
            if actual != self.bootstrap_binding:
                raise ValueError('native metadata bootstrap invocation or generation differs')

    def _bootstrap_dependencies(self):
        if self.bootstrap_binding is None:
            return ()
        return (self.bootstrap_binding['capability_id'], self.bootstrap_binding['consequence_id'],
                *((self.bootstrap_binding['environment_selection_id'],)
                  if 'environment_selection_id' in self.bootstrap_binding else ()))

    def _inputs(self):
        inputs = _runtime_inputs(self)
        if self.materialization_binding is not None:
            inputs['materialization_binding'] = frozen._copy(self.materialization_binding)
        if self.bootstrap_binding is not None:
            inputs['bootstrap_binding'] = frozen._copy(self.bootstrap_binding)
        return inputs

    def _scope(self):
        self._bootstrap_preflight()
        self._materialization_preflight()
        _check_sources()
        _runtime_scope(self)

    def _expected_scope(self):
        return {**_runtime_expected_scope(self), 'native_runtime_version': 45,
            'materialization': frozen._copy(self.materialization_binding),
            'metadata_bootstrap': frozen._copy(self.bootstrap_binding)}

    def _observation_premises(self):
        return (self.source, self.authority, *self._materialization_dependencies(), *self._bootstrap_dependencies())

    def admit(self, candidate, dependencies=(), supersedes=None):
        self._bootstrap_preflight()
        self._materialization_preflight()
        dependencies = tuple(dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise ValueError('duplicate native causal dependencies')
        required = (*self._materialization_dependencies(), *self._bootstrap_dependencies())
        return _runtime_admit(self, candidate,
            (*required, *(ident for ident in dependencies if ident not in required)), supersedes)


for _name, _function in vars(frozen.NativeRuntimeV2).items():
    if isinstance(_function, FunctionType) and _name not in (
            '__init__', '_inputs', '_scope', '_expected_scope', '_verify', 'admit'):
        setattr(NativeRuntimeV45, _name, _bind(_function))
NativeRuntimeV45._verify = _bind(portable.NativeRuntimeV3._verify)
_check_sources()
del _name, _function
