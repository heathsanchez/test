"""Original native runtime algorithms with a live materialization prerequisite.

The instrument generation and exact retained invocation extend source scope.
Collection, assertion authority, repeated native admission and receipt checking
continue through the versioned original worker. Pytest publication stays closed.
"""
import json
import inspect
from pathlib import Path
import secrets
import textwrap
import time
from types import FunctionType

from . import native_runtime_v42 as previous
from . import native_runtime_v3 as portable
from . import native_execution_v43 as verifier
from . import native_admission_v42 as admission
from . import developmental_machine_v43 as framework
from . import native_materialization_v43 as materialization

frozen = previous.frozen
AUTHORITY = frozen._copy(previous.AUTHORITY)
_LOADED_SOURCE_SHA256 = frozen._sha(__file__)
_PREVIOUS_SOURCE_SHA256 = 'bc680199a8c718f51067f021d1cf0bf137dc4e1d2073964e9b4f100eb070de65'
_VERIFIER_SOURCE_SHA256 = '7d449419909c94ce6186d984545ce218c15ee97dc407104bd4e903180c564827'
_ORIGINAL_FRONTIER_SHA256 = '9b0e6ecd90b3b52a2d7d673844faf5618a614a5857460349d71852a1423843f6'
_runtime_globals = dict(vars(frozen), verifier=verifier, admission=admission, framework=framework,
                        AUTHORITY=AUTHORITY, __file__=__file__, json=json, secrets=secrets, time=time)


def _check_sources():
    previous._check_sources()
    materialization._guard()
    if (frozen._sha(__file__) != _LOADED_SOURCE_SHA256
            or frozen._sha(previous.__file__) != _PREVIOUS_SOURCE_SHA256
            or frozen._sha(verifier.__file__) != _VERIFIER_SOURCE_SHA256
            or frozen._sha(frozen.original.__file__) != _ORIGINAL_FRONTIER_SHA256):
        raise ValueError('UNKNOWN_V43_NATIVE_RUNTIME_SOURCE_CHANGED')
    verifier._runner_hash()


def _bind(function):
    value = FunctionType(function.__code__, _runtime_globals, function.__name__,
                         function.__defaults__, function.__closure__)
    value.__kwdefaults__ = function.__kwdefaults__
    return value


_runtime_scope = _bind(frozen.NativeRuntimeV2._scope)
_runtime_expected_scope = _bind(frozen.NativeRuntimeV2._expected_scope)
_runtime_init = _bind(frozen.NativeRuntimeV2.__init__)
_runtime_inputs = _bind(frozen.NativeRuntimeV2._inputs)
_runtime_admit = _bind(frozen.NativeRuntimeV2.admit)


def _observation_transport(function, before, after):
    """Change only the exact witness-premise transport in original source."""
    if frozen._sha(frozen.original.__file__) != _ORIGINAL_FRONTIER_SHA256:
        raise ValueError('UNKNOWN_V43_ORIGINAL_FRONTIER_SOURCE_CHANGED')
    original_source = textwrap.dedent(inspect.getsource(function))
    if original_source.count(before) != 1:
        raise ValueError('UNKNOWN_V43_OBSERVATION_PREMISE_BINDING_SITE')
    namespace = dict(vars(frozen.original))
    exec(compile(original_source.replace(before, after),
                 __file__ + ':original-observation-premises:' + function.__name__, 'exec'), namespace)
    return namespace[function.__name__]


class _MaterializationFrontier(frozen.original.NativeFrontierRuntime):
    _observation = _observation_transport(frozen.original.NativeFrontierRuntime._observation,
        "report, (self.source, self.authority))", "report, self._observation_premises())")
    _validated = _observation_transport(frozen.original.NativeFrontierRuntime._validated,
        "tuple(observation.premises) != (self.source, self.authority)",
        "tuple(observation.premises) != self._observation_premises()")


class NativeRuntimeV43(frozen.NativeRuntimeV2, _MaterializationFrontier):
    def __init__(self, machine, contract, authority, certificate, policy, output, *,
                 materialization_capability=None):
        _check_sources()
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
        adapter = materialization.MaterializationRuntime(self.machine, self.output / 'materialization')
        binding = adapter.bind_native(self.materialization_capability, self.contract,
                                      self.suite_authority, self.policy)
        if self.materialization_binding is not None and binding != self.materialization_binding:
            raise ValueError('native materialization generation or retained invocation changed')
        self.materialization_binding = binding

    def _inputs(self):
        inputs = _runtime_inputs(self)
        if self.materialization_binding is not None:
            inputs['materialization_binding'] = self.materialization_binding
        return inputs

    def _scope(self):
        # Liveness and retained executable checks precede original context
        # validation, independent builds, native collection and assertion runs.
        self._materialization_preflight()
        _check_sources()
        _runtime_scope(self)

    def _expected_scope(self):
        return {**_runtime_expected_scope(self), 'native_runtime_version': 43,
                'materialization': frozen._copy(self.materialization_binding)}

    def _materialization_dependencies(self):
        if self.materialization_binding is None:
            return ()
        return (self.materialization_capability, self.materialization_binding['consequence_id'])

    def _observation_premises(self):
        return (self.source, self.authority, *self._materialization_dependencies())

    def admit(self, candidate, dependencies=(), supersedes=None):
        self._materialization_preflight()
        dependencies = tuple(dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise ValueError('duplicate native causal dependencies')
        required = self._materialization_dependencies()
        dependencies = (*required, *(ident for ident in dependencies if ident not in required))
        return _runtime_admit(self, candidate, dependencies, supersedes)


for _name, _function in vars(frozen.NativeRuntimeV2).items():
    if isinstance(_function, FunctionType) and _name not in (
            '__init__', '_inputs', '_scope', '_expected_scope', '_verify', 'admit'):
        setattr(NativeRuntimeV43, _name, _bind(_function))
NativeRuntimeV43._verify = _bind(portable.NativeRuntimeV3._verify)
if NativeRuntimeV43.__mro__[1:3] != (frozen.NativeRuntimeV2, _MaterializationFrontier):
    raise ValueError('UNKNOWN_V43_ORIGINAL_NATIVE_SUPER_BINDING')
_check_sources()
