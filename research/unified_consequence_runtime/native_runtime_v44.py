"""Original native runtime with a retained metadata-observation prerequisite.

The old native worker and materialization algorithms stay byte-exact. This
subclass transports an independently checked bootstrap invocation into native
observations, executable capabilities and dependent consequences.
"""
from . import native_runtime_v43 as previous
from . import native_environment_v44 as environment


_LOADED_SHA256 = previous.frozen._sha(__file__)
_PREVIOUS_SHA256 = 'ddd23a08b30e9f7eb861a48f67630f48ca03c941391507d9a916473d849225ab'


def _check_sources():
    previous._check_sources()
    environment._guard()
    if (previous.frozen._sha(__file__) != _LOADED_SHA256
            or previous.frozen._sha(previous.__file__) != _PREVIOUS_SHA256):
        raise ValueError('UNKNOWN_V44_NATIVE_RUNTIME_SOURCE_CHANGED')


class NativeRuntimeV44(previous.NativeRuntimeV43):
    def __init__(self, machine, contract, authority, certificate, policy, output, *,
                 materialization_capability=None, bootstrap_binding=None):
        _check_sources()
        self.bootstrap_binding = previous.frozen._copy(bootstrap_binding)
        # Establish bootstrap liveness before the inherited initializer can
        # construct a source or perform native context validation.
        if self.bootstrap_binding is not None:
            environment.preflight_bootstrap(machine, self.bootstrap_binding, contract, authority, policy)
        super().__init__(machine, contract, authority, certificate, policy, output,
                         materialization_capability=materialization_capability)

    def _bootstrap_preflight(self):
        if self.bootstrap_binding is not None:
            actual = environment.preflight_bootstrap(
                self.machine, self.bootstrap_binding, self.contract, self.suite_authority, self.policy)
            if actual != self.bootstrap_binding:
                raise ValueError('native metadata bootstrap invocation or generation differs')

    def _bootstrap_dependencies(self):
        if self.bootstrap_binding is None:
            return ()
        return (self.bootstrap_binding['capability_id'], self.bootstrap_binding['consequence_id'],
                *((self.bootstrap_binding['environment_selection_id'],)
                  if 'environment_selection_id' in self.bootstrap_binding else ()))

    def _inputs(self):
        inputs = super()._inputs()
        if self.bootstrap_binding is not None:
            inputs['bootstrap_binding'] = previous.frozen._copy(self.bootstrap_binding)
        return inputs

    def _scope(self):
        self._bootstrap_preflight()
        _check_sources()
        super()._scope()

    def _expected_scope(self):
        return {**super()._expected_scope(), 'native_runtime_version': 44,
                'metadata_bootstrap': previous.frozen._copy(self.bootstrap_binding)}

    def _observation_premises(self):
        return (*super()._observation_premises(), *self._bootstrap_dependencies())

    def admit(self, candidate, dependencies=(), supersedes=None):
        self._bootstrap_preflight()
        dependencies = tuple(dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise ValueError('duplicate native causal dependencies')
        required = self._bootstrap_dependencies()
        return super().admit(candidate,
            (*required, *(ident for ident in dependencies if ident not in required)), supersedes)

