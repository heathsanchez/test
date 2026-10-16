"""Versioned portable-worker binding over the unchanged v2 Machine adapter.

The existing native algorithms retain their event and evidence formats. The
portable worker, explicit scope version, and controller attempt cost envelope
are versioned here. This is bounded local research execution, without a
constructor-support or G3 claim.
"""
import json
import secrets
import time
from types import FunctionType

from . import native_execution_v3 as verifier
from . import native_runtime_v2 as frozen

AUTHORITY = frozen._copy(frozen.AUTHORITY)
_FROZEN_RUNTIME_SHA256 = '0707f9938d74c358fd8c21f9881c18a51c4e2062a7fcc79eee48b3a8499573bb'
_LOADED_SOURCE_SHA256 = frozen._sha(__file__)


def _check_sources():
    if frozen._sha(__file__) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_RUNTIME_SOURCE_MUTATION')
    if frozen._sha(frozen.__file__) != _FROZEN_RUNTIME_SHA256:
        raise ValueError('UNKNOWN_FROZEN_RUNTIME_SOURCE_MUTATION')
    verifier._runner_hash()


_check_sources()
_runtime_globals = dict(vars(frozen), verifier=verifier, AUTHORITY=AUTHORITY, __file__=__file__)


def _bind(function):
    bound = FunctionType(function.__code__, _runtime_globals, function.__name__,
                         function.__defaults__, function.__closure__)
    bound.__kwdefaults__ = function.__kwdefaults__
    return bound


_runtime_scope = _bind(frozen.NativeRuntimeV2._scope)
_runtime_expected_scope = _bind(frozen.NativeRuntimeV2._expected_scope)


class NativeRuntimeV3(frozen.NativeRuntimeV2):
    """Keep v2 causal validation while selecting the portable v3 worker."""

    def _scope(self):
        _check_sources()
        _runtime_scope(self)

    def _expected_scope(self):
        return {**_runtime_expected_scope(self), 'native_runtime_version': 3}

    def _verify(self, candidate):
        """Retain controller launch costs even when producer evidence is broken."""
        self._scope()
        run = self.output/'native-runs'/secrets.token_hex(16)
        started, receipt = time.perf_counter(), None
        before = verifier.attempt_snapshot()
        try:
            receipt = verifier.verify(self.contract, candidate, run, authority=self.suite_authority,
                                      admission_certificate=self.certificate, policy=self.policy)
            self._scope()
            return receipt
        finally:
            if receipt is None and (run/'receipt.json').is_file():
                try:
                    receipt = json.loads((run/'receipt.json').read_text())
                except (OSError, ValueError):
                    pass
            seconds = time.perf_counter()-started
            attempts, complete = {}, False
            try:
                after = verifier.attempt_snapshot()
                keys = ('native_calls', 'collection_calls', 'subprocess_attempts')
                if all(type(snapshot.get(key)) is int and snapshot[key] >= 0
                       for snapshot in (before, after) for key in keys):
                    attempts = {key: after[key]-before[key] for key in keys}
                    complete = (all(value >= 0 for value in attempts.values())
                                and attempts['subprocess_attempts'] ==
                                attempts['native_calls']+attempts['collection_calls'])
            except Exception:
                pass
            retained_costs = receipt.get('costs') if isinstance(receipt, dict) else None
            costs = dict(retained_costs) if isinstance(retained_costs, dict) else {}
            if complete:
                for key in ('native_calls', 'collection_calls'):
                    retained = costs.get(key, 0)
                    costs[key] = max(retained, attempts[key]) if type(retained) is int and retained >= 0 else attempts[key]
            if not isinstance(retained_costs, dict):
                costs.update(total_seconds=seconds)
                if complete:
                    costs['subprocess_attempts'] = attempts['subprocess_attempts']
            status = receipt.get('status', 'UNKNOWN_VERIFIER_ERROR') if isinstance(receipt, dict) else 'UNKNOWN_VERIFIER_ERROR'
            if not complete:
                status = 'UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING'
            self.machine.costs.append({'phase': 'generic_native_v2_independent_verification',
                'seconds': seconds, 'output': str(run), 'status': status, 'costs': costs,
                'controller_attempts': attempts, 'accounting_complete': complete})
            if not complete:
                raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING')


# The v2 __class__ closure is retained, so its zero-argument super() still
# reaches the original adapter through this subclass. No old globals change.
for _name, _function in vars(frozen.NativeRuntimeV2).items():
    if isinstance(_function, FunctionType) and _name not in ('_scope', '_expected_scope', '_verify'):
        setattr(NativeRuntimeV3, _name, _bind(_function))
