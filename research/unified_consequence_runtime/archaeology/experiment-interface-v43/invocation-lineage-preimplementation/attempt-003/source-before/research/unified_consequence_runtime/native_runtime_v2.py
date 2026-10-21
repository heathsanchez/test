"""Thin v2 native adapter over existing Machine/CAS/Metatron/FLASH support.

The supplied suite authority, certificate and policy authorize only bounded local
research. Native success grants no external effect or containment guarantee.
Inherited v1 typed-frontier publication is deliberately unavailable for v2.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import secrets
import time

from . import decisive_native_frontier as original
from . import decisive_native_verify as underlying_verifier
from . import developmental_machine as framework
from . import native_admission_v2 as admission
from . import native_execution_v2 as verifier
from .developmental_machine import Capability

AUTHORITY = original._copy(original.AUTHORITY)
_copy = original._copy
_sha = original._sha


class NativeRuntimeV2(original.NativeFrontierRuntime):
    """Persisted native executables; Machine owns every causal state record."""

    def __init__(self, machine, contract, authority, certificate, policy, output):
        self.machine, self.contract = machine, _copy(contract)
        self.suite_authority, self.certificate, self.policy = map(_copy, (authority, certificate, policy))
        self.contract_sha256 = verifier.fingerprint(self.contract)
        self.output = Path(output).absolute()
        self._check_output()
        self.authority_ceiling = _copy(AUTHORITY)
        self.source_descriptor = {key: self.contract[key] for key in (
            'repository', 'commit', 'git_tree', 'tracked_tree_sha256', 'protocol_binding', 'environment_sha256')}
        self.source_descriptor['adapter_sha256'] = _sha(__file__)
        self.source_descriptor.update({key: _sha(module.__file__) for key, module in (
            ('inherited_adapter_sha256', original), ('machine_adapter_sha256', framework),
            ('ast_sha256', admission), ('verifier_sha256', verifier), ('inherited_verifier_sha256', underlying_verifier))})
        for key, value in self._inputs().items():
            self.source_descriptor[key] = machine.put(value)
        self.source_descriptor_sha256 = verifier.fingerprint(self.source_descriptor)
        self.authority = self._record_once('execution_authority_ceiling', AUTHORITY)
        self.source = self._record_once('generic_native_source', self._source_payload(), (self.authority,))
        self.output.mkdir(parents=True, exist_ok=True)
        self.machine.flush()
        self._scope()

    def _inputs(self):
        return {'contract': self.contract, 'suite_authority': self.suite_authority,
                'certificate': self.certificate, 'policy': self.policy}

    def _source_payload(self):
        return {'source': self.source_descriptor, 'contract': self.source_descriptor['contract'],
                'authority': 'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH_ONLY'}

    def _check_output(self):
        repo = Path(self.contract['repo_path']).absolute()
        if self.output.resolve() != self.output or self.output == repo or self.output.is_relative_to(repo):
            raise ValueError('native output must be canonical and outside source')

    def _scope(self):
        self._live(self.authority, self.source)
        if (self.authority_ceiling != AUTHORITY or AUTHORITY != original.AUTHORITY
                or verifier.fingerprint(self.source_descriptor) != self.source_descriptor_sha256):
            raise ValueError('native external authority ceiling changed')
        for key, path in (('adapter_sha256', __file__), ('inherited_adapter_sha256', original.__file__),
                          ('machine_adapter_sha256', framework.__file__), ('ast_sha256', admission.__file__),
                          ('verifier_sha256', verifier.__file__), ('inherited_verifier_sha256', underlying_verifier.__file__)):
            if self.source_descriptor[key] != _sha(path):
                raise ValueError('native controller, AST or worker source changed: '+key)
        for key, value in self._inputs().items():
            if (self.source_descriptor[key] != verifier.fingerprint(value)
                    or self.machine.get(self.source_descriptor[key]) != value):
                raise ValueError('native external input or CAS binding changed')
        self._check_output()
        verifier._context(self.contract, self.suite_authority, self.policy)
        binding = {'contract_sha256': self.contract_sha256,
                   'authority_sha256': verifier.fingerprint(self.suite_authority),
                   'policy_sha256': verifier.fingerprint(self.policy),
                   'runner_sha256': self.source_descriptor['verifier_sha256']}
        if any(self.certificate.get(key) != value for key, value in binding.items()):
            raise ValueError('native certificate has wrong external source binding')
        nodes = {node.id: node for node in self.machine.log}
        source, authority = nodes[self.source], nodes[self.authority]
        if (source.kind != 'generic_native_source' or source.payload != self._source_payload()
                or tuple(source.premises) != (self.authority,) or authority.kind != 'execution_authority_ceiling'
                or authority.payload != AUTHORITY or authority.premises):
            raise ValueError('native source or external authority lineage changed')

    def _expected_scope(self):
        return {**super()._expected_scope(), 'native_runtime_version': 2,
                'suite_authority_sha256': verifier.fingerprint(self.suite_authority),
                'policy_sha256': verifier.fingerprint(self.policy)}

    def _verify(self, candidate):
        self._scope()
        run = self.output/'native-runs'/secrets.token_hex(16)
        started, receipt = time.perf_counter(), None
        try:
            receipt = verifier.verify(self.contract, candidate, run, authority=self.suite_authority,
                                      admission_certificate=self.certificate, policy=self.policy)
            self._scope()
            return receipt
        finally:
            if receipt is None and (run/'receipt.json').is_file():
                receipt = json.loads((run/'receipt.json').read_text())
            self.machine.costs.append({'phase': 'generic_native_v2_independent_verification',
                'seconds': time.perf_counter()-started, 'output': str(run),
                'status': receipt['status'] if receipt else 'UNKNOWN_VERIFIER_ERROR',
                'costs': receipt['costs'] if receipt else {}})

    def _receipt(self, receipt, candidate, *, require_pass=True):
        verifier.validate_receipt(self.contract, candidate, self.suite_authority, self.certificate,
                                  receipt, policy=self.policy, independent=False)
        if require_pass and receipt.get('status') != 'PASS_NATIVE':
            raise ValueError('native receipt does not warrant successful execution')

    def admit(self, candidate, dependencies=(), supersedes=None):
        candidate, dependencies = _copy(candidate), tuple(dependencies)
        self._scope()
        if len(set(dependencies)) != len(dependencies):
            raise ValueError('duplicate native causal dependencies')
        self._live(*dependencies)
        program = self.machine.put(candidate)
        prior = [node for node in self.machine.log if node.kind == 'executable_capability'
                 and node.payload.get('operation') == 'native.pytest_suite'
                 and node.payload.get('scope') == self._expected_scope()]
        previous = [node for node in prior if node.payload.get('program') == program]
        if supersedes is not None:
            old = self.machine.descriptor(supersedes)
            live = set(self.machine.mt.live_ids(self.machine.log)) | self.machine.flash_live_ids()
            stable = lambda source: {key: value for key, value in source.items() if key != 'certificate'}
            fresh = self.certificate.get('packet_sha256', {}).get('checked-report.json')
            used = [self.machine.get(node.payload['source']['certificate'])['packet_sha256']['checked-report.json']
                    for node in previous]
            if (not previous or supersedes != previous[-1].id or any(node.id in live for node in previous)
                    or old.operation != 'native.pytest_suite' or old.scope != self._expected_scope()
                    or stable(old.source) != stable(self.source_descriptor) or old.program != program
                    or tuple(old.dependencies[2:]) != dependencies or not old.dependencies
                    or old.dependencies[0] in live or supersedes in live
                    or old.source.get('certificate') == self.source_descriptor['certificate']
                    or not fresh or fresh in used):
                raise ValueError('restoration requires withdrawn exact ancestry and fresh certificate evidence')
        elif any(node.payload.get('program') == program for node in prior):
            raise ValueError('existing native candidate requires explicit source-qualified supersession')
        first = self._verify(candidate)
        observation = self._observation(candidate, first)
        if first['status'] != 'PASS_NATIVE':
            raise ValueError(first['status']+': native observation retained without admission')
        self._receipt(first, candidate)
        second = self._verify(candidate)
        if second['status'] != 'PASS_NATIVE':
            self._observation(candidate, second)
            raise ValueError(second['status']+': independent repeat rejected admission')
        self._receipt(second, candidate)
        self._live(*dependencies)
        generation, nonce = len(prior)+1, secrets.token_hex(32)
        bundle = {'schema': 'UDM_GENERIC_NATIVE_ADMISSION_V1', 'contract_sha256': self.contract_sha256,
                  'program': program, 'generation': generation, 'nonce': nonce, 'runs': [first, second]}
        support = self.machine.append('source_support', {'family': 'generic-native-frontier', 'program': program,
            'generation': generation, 'nonce': nonce, 'supersedes': supersedes, 'dependencies': list(dependencies)},
            (self.source, self.authority, observation['observation_id'], *dependencies))
        verified = self.machine.append(original.VERIFICATION_KIND,
            {'program': program, 'receipt': self.machine.put(bundle)}, (support,))
        cap = Capability('native.pytest_suite', self.source_descriptor, self._expected_scope(),
            self.machine.put(observation), program, generation,
            (support, observation['observation_id'], *dependencies), (verified,),
            'CAPABILITY_LANGUAGE_EXTENSION' if candidate['replacements'] else 'ACTIVATION', supersedes)
        result = self.machine.append('executable_capability', asdict(cap),
                                     (support, verified, observation['observation_id'], *dependencies))
        self.machine.flush()
        return result

    def _validated(self, capability_id):
        cap, candidate, bundle = super()._validated(capability_id)
        prior = []
        for node in self.machine.log:
            if node.kind == 'executable_capability' and node.payload.get('operation') == cap.operation and node.payload.get('scope') == cap.scope:
                prior.append(node.id)
            if node.id == capability_id:
                break
        if cap.generation != len(prior) or bundle['runs'][0] == bundle['runs'][1]:
            raise ValueError('native generation or independent repeat binding changed')
        return cap, candidate, bundle

    def restore(self, capability_id):
        cap = self.machine.descriptor(capability_id)
        return self.admit(self.machine.get(cap.program), cap.dependencies[2:], supersedes=capability_id)

    def projection_payload(self, capability_id):
        raise ValueError('UNKNOWN: v2 typed frontier publication has no licensed source checker')
