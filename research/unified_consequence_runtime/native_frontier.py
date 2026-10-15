"""Thin full-pytest native capabilities over the existing warrant authority.

The externally supplied contract grants local research execution only. Native
PASS is bounded evidence, not new external permission or a sandbox certificate.
Caller-supplied receipts are never an admission input; every admission and every
execution invokes the independent source-native worker afresh.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
import secrets
import time

from .developmental_machine import Capability, canonical, digest
from . import generic_native_verify as verifier

AUTHORITY = {'principal': 'independent user research mission',
             'allowed_effects': 'immutable source copies and local native tests',
             'external_effects': 'NONE', 'reference_monitor': 'UNKNOWN_NONBYPASSABILITY'}
FRONTIER_CONTRACT = {'input_type': 'NativeRepositoryFrontier',
    'output_type': 'NativePytestOutcome', 'authority_snapshot': 'udm-generic-native-research-v1',
    'verifier_id': 'upstream-full-pytest-v1'}
VERIFICATION_KIND = 'generic_native_verification'
REQUIRED_CONTRACT = frozenset(('schema', 'repository', 'repo_path', 'commit', 'git_tree',
    'tracked_tree_sha256', 'file_count', 'interpreter', 'environment_sha256',
    'protocol_binding', 'horizon_seconds'))


def _copy(value):
    import json
    return json.loads(canonical(value))


def _sha(path):
    return digest(Path(path).read_bytes())


class NativeFrontierRuntime:
    """One exact externally frozen native frontier; Machine owns all causal state."""
    def __init__(self, machine, contract, output, *, generated_wheel_evidence=None):
        self.machine, self.contract = machine, _copy(contract)
        self.generated_wheel_evidence = _copy(generated_wheel_evidence) if generated_wheel_evidence else None
        self.contract_sha256 = digest(canonical(self.contract).encode())
        self.output = Path(output).absolute()
        self._check_configuration()
        self.output.mkdir(parents=True, exist_ok=True)
        self.generated_wheel_digest = digest(canonical(self.generated_wheel_evidence).encode()) if self.generated_wheel_evidence else None
        self.authority_ceiling = _copy(AUTHORITY)
        self.source_descriptor = {
            'repository': self.contract['repository'], 'commit': self.contract['commit'],
            'git_tree': self.contract['git_tree'],
            'tracked_tree_sha256': self.contract['tracked_tree_sha256'],
            'protocol_binding': self.contract['protocol_binding'],
            'adapter_sha256': _sha(__file__), 'verifier_sha256': _sha(verifier.__file__),
            'generated_wheel_evidence_sha256': self.generated_wheel_digest}
        self.authority = self._record_once('execution_authority_ceiling', AUTHORITY)
        self.source = self._record_once('generic_native_source', {
            'source': self.source_descriptor, 'contract': self.machine.put(self.contract),
            'authority': 'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH_ONLY'}, (self.authority,))
        self.machine.flush()

    def _record_once(self, kind, payload, premises=()):
        for node in self.machine.log:
            if node.kind == kind and node.payload == payload and tuple(node.premises) == tuple(premises):
                return node.id
        return self.machine.append(kind, payload, premises)

    def _check_configuration(self):
        contract = self.contract
        if (not isinstance(contract, dict) or set(contract) != REQUIRED_CONTRACT or
                digest(canonical(contract).encode()) != self.contract_sha256):
            raise ValueError('native contract changed or has unsupported configuration')
        if (contract['schema'] != verifier.SCHEMA or type(contract['horizon_seconds']) is not int
                or contract['horizon_seconds'] != 7 or type(contract['file_count']) is not int
                or contract['file_count'] < 1 or not isinstance(contract['repository'], str)
                or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', contract['repository'])):
            raise ValueError('native contract schema, repository or budget mismatch')
        for key in ('protocol_binding', 'environment_sha256', 'tracked_tree_sha256'):
            if not isinstance(contract[key], str) or not re.fullmatch('[0-9a-f]{64}', contract[key]):
                raise ValueError('invalid native contract digest: '+key)
        repo = Path(contract['repo_path']).absolute()
        if self.output.resolve() != self.output or self.output == repo or self.output.is_relative_to(repo):
            raise ValueError('native output must be canonical and outside source')
        identity = verifier.source_identity(repo, contract['commit'])
        if any(contract[key] != value for key, value in identity.items()):
            raise ValueError('native source identity mismatch')
        environment = verifier.environment_identity(contract['interpreter'])
        if (verifier.fingerprint(environment) != contract['environment_sha256'] or
                environment.get('pytest_version') != verifier.PYTEST_VERSION):
            raise ValueError('native environment identity mismatch')

    def _live(self, *ids):
        live = set(self.machine.mt.live_ids(self.machine.log)) & self.machine.flash_live_ids()
        if any(node not in live for node in ids):
            raise PermissionError('native causal support or authority withdrawn')

    def _scope(self):
        self._live(self.authority, self.source)
        self._check_configuration()
        if (self.source_descriptor['adapter_sha256'] != _sha(__file__) or
                self.source_descriptor['verifier_sha256'] != _sha(verifier.__file__) or
                self.authority_ceiling != AUTHORITY):
            raise ValueError('native adapter, verifier or authority ceiling changed')
        nodes = {node.id: node for node in self.machine.log}
        source = nodes[self.source]
        if (source.kind != 'generic_native_source' or source.payload != {
                'source': self.source_descriptor, 'contract': self.machine.put(self.contract),
                'authority': 'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH_ONLY'} or
                tuple(source.premises) != (self.authority,)):
            raise ValueError('native source authority lineage changed')

    def _expected_scope(self):
        return {'repository': self.contract['repository'], 'commit': self.contract['commit'],
                'contract_sha256': self.contract_sha256, 'protocol_binding': self.contract['protocol_binding'],
                'authority_ceiling': AUTHORITY, 'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
                'frontier_contract': FRONTIER_CONTRACT,
                'frontier_profiles': [self.contract['repository']+'@'+self.contract['commit']]}

    def _verify(self, candidate):
        self._scope()
        run = self.output/'native-runs'/secrets.token_hex(16)
        started = time.perf_counter()
        generated = None
        if self.generated_wheel_evidence is not None:
            from .generated_wheel_evidence import authenticated_generated_modules
            if self.generated_wheel_digest != digest(canonical(self.generated_wheel_evidence).encode()):
                raise ValueError('generated wheel evidence changed')
            identity, source_files, _ = verifier._snapshot(self.contract['repo_path'], self.contract['commit'])
            evidence = self.generated_wheel_evidence
            if (evidence['source_commit'] != self.contract['commit'] or
                    evidence['source_tree_sha256'] != identity['tracked_tree_sha256']):
                raise ValueError('generated wheel wrong source identity')
            generated = authenticated_generated_modules(source_files, evidence)
        receipt = verifier.verify(self.contract, candidate, run, generated_modules=generated)
        self._scope()
        self.machine.costs.append({'phase': 'generic_native_independent_verification',
            'seconds': time.perf_counter()-started, 'costs': receipt['costs'],
            'status': receipt['status'], 'output': str(run)})
        return receipt

    def _receipt(self, receipt, candidate, *, require_pass=True):
        source = {key: self.contract[key] for key in ('git_tree', 'tracked_tree_sha256', 'file_count')}
        expected = {'schema': verifier.SCHEMA, 'repository': self.contract['repository'],
            'commit': self.contract['commit'], 'source': source,
            'contract_sha256': self.contract_sha256, 'candidate_sha256': verifier.fingerprint(candidate),
            'protocol_binding': self.contract['protocol_binding'],
            'runner_sha256': self.source_descriptor['verifier_sha256'],
            'authority': 'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH_ONLY',
            'external_enforcement': 'UNKNOWN_NONBYPASSABILITY'}
        if not isinstance(receipt, dict) or any(receipt.get(k) != v for k, v in expected.items()):
            raise ValueError('native receipt source, program, authority or protocol binding mismatch')
        if not require_pass:
            return
        counts, costs = receipt.get('junit', {}), receipt.get('costs', {})
        if (receipt.get('status') != 'PASS_NATIVE' or receipt.get('exit_code') != 0 or
                receipt.get('environment_sha256') != self.contract['environment_sha256'] or
                verifier.fingerprint(receipt.get('environment')) != self.contract['environment_sha256'] or
                counts.get('passed', 0) < 1 or counts.get('errors') != 0 or counts.get('failures') != 0 or
                counts.get('skipped') != 0 or
                costs.get('native_calls') != 1 or costs.get('horizon_seconds') != 7 or
                not all(re.fullmatch('[0-9a-f]{64}', receipt.get(key, ''))
                        for key in ('stdout_sha256', 'stderr_sha256', 'junit_sha256'))):
            raise ValueError('native receipt does not warrant a nonempty successful native execution')

    def _observation(self, candidate, receipt):
        self._receipt(receipt, candidate, require_pass=False)
        report = {'candidate': self.machine.put(candidate), 'receipt': self.machine.put(receipt),
                  'contract_sha256': self.contract_sha256, 'status': receipt['status']}
        node = self.machine.append('generic_native_observation', report, (self.source, self.authority))
        self.machine.flush()
        return dict(receipt, observation_id=node)

    def observe(self):
        """A failed or incomplete native suite supplies evidence, never a capability."""
        candidate = {'replacements': []}
        return self._observation(candidate, self._verify(candidate))

    def admit(self, candidate, dependencies=(), supersedes=None):
        candidate = _copy(candidate)
        self._scope()
        dependencies = tuple(dependencies)
        if len(set(dependencies)) != len(dependencies):
            raise ValueError('duplicate native causal dependencies')
        self._live(*dependencies)
        if supersedes is not None:
            old = self.machine.descriptor(supersedes)
            if (old.source != self.source_descriptor or old.scope != self._expected_scope() or
                    supersedes in self.machine.mt.live_ids(self.machine.log)):
                raise ValueError('restoration must supersede a withdrawn exact native capability')
        first = self._verify(candidate)
        observation = self._observation(candidate, first)
        if first['status'] != 'PASS_NATIVE':
            raise ValueError(first['status']+': native result retained without capability admission')
        self._receipt(first, candidate)
        second = self._verify(candidate)
        if second['status'] != 'PASS_NATIVE':
            self._observation(candidate, second)
            raise ValueError(second['status']+': independent repeat did not warrant admission')
        self._receipt(second, candidate)
        self._live(*dependencies)
        generation = 1+sum(node.kind == 'executable_capability' and
            node.payload.get('operation') == 'native.pytest_suite' and
            node.payload.get('scope') == self._expected_scope() for node in self.machine.log)
        program, nonce = self.machine.put(candidate), secrets.token_hex(32)
        bundle = {'schema': 'UDM_GENERIC_NATIVE_ADMISSION_V1', 'contract_sha256': self.contract_sha256,
                  'program': program, 'generation': generation, 'nonce': nonce, 'runs': [first, second]}
        support = self.machine.append('source_support', {
            'family': 'generic-native-frontier', 'program': program, 'generation': generation,
            'nonce': nonce, 'supersedes': supersedes, 'dependencies': list(dependencies)},
            (self.source, self.authority, observation['observation_id'], *dependencies))
        verified = self.machine.append(VERIFICATION_KIND,
            {'program': program, 'receipt': self.machine.put(bundle)}, (support,))
        cap = Capability('native.pytest_suite', self.source_descriptor, self._expected_scope(),
            self.machine.put(observation), program, generation,
            (support, observation['observation_id'], *dependencies), (verified,),
            'CAPABILITY_LANGUAGE_EXTENSION' if candidate['replacements'] else 'ACTIVATION', supersedes)
        node = self.machine.append('executable_capability', asdict(cap),
            (support, verified, observation['observation_id'], *dependencies))
        self.machine.flush()
        return node

    def _validated(self, capability_id):
        self._scope()
        self._live(capability_id)
        cap = self.machine.descriptor(capability_id)
        if (cap.operation != 'native.pytest_suite' or cap.source != self.source_descriptor or
                cap.scope != self._expected_scope() or len(cap.dependencies) < 2 or len(cap.evidence) != 1):
            raise ValueError('wrong native executable class, source, scope or dependencies')
        self._live(*cap.dependencies, *cap.evidence)
        nodes = {node.id: node for node in self.machine.log}
        support, observation = (nodes[key] for key in cap.dependencies[:2])
        verified = nodes[cap.evidence[0]]
        external = tuple(cap.dependencies[2:])
        candidate, bundle = self.machine.get(cap.program), self.machine.get(verified.payload['receipt'])
        expected_transition = 'CAPABILITY_LANGUAGE_EXTENSION' if candidate.get('replacements') else 'ACTIVATION'
        if (cap.transition != expected_transition or support.kind != 'source_support' or
                support.payload != {'family': 'generic-native-frontier', 'program': cap.program,
                    'generation': cap.generation, 'nonce': bundle.get('nonce'),
                    'supersedes': cap.supersedes, 'dependencies': list(external)} or
                tuple(support.premises) != (self.source, self.authority, observation.id, *external) or
                observation.kind != 'generic_native_observation' or
                tuple(observation.premises) != (self.source, self.authority) or
                verified.kind != VERIFICATION_KIND or tuple(verified.premises) != (support.id,) or
                verified.payload.get('program') != cap.program or
                tuple(nodes[capability_id].premises) != (support.id, verified.id, observation.id, *external)):
            raise ValueError('native capability causal lineage differs from descriptor')
        retained = self.machine.get(cap.observation)
        if (bundle.get('schema') != 'UDM_GENERIC_NATIVE_ADMISSION_V1' or
                bundle.get('program') != cap.program or bundle.get('generation') != cap.generation or
                bundle.get('contract_sha256') != self.contract_sha256 or
                not isinstance(bundle.get('nonce'), str) or not re.fullmatch('[0-9a-f]{64}', bundle['nonce']) or
                not isinstance(bundle.get('runs'), list) or len(bundle['runs']) != 2 or
                retained.get('observation_id') != observation.id or
                observation.payload.get('contract_sha256') != self.contract_sha256 or
                observation.payload.get('candidate') != cap.program or
                observation.payload.get('status') != 'PASS_NATIVE'):
            raise ValueError('native retained evidence or observation has wrong binding')
        original = self.machine.get(observation.payload['receipt'])
        if original != bundle['runs'][0] or retained != dict(original, observation_id=observation.id):
            raise ValueError('native admission replayed or replaced the original observation')
        for receipt in bundle['runs']:
            self._receipt(receipt, candidate)
        return cap, candidate, bundle

    def projection_payload(self, capability_id):
        cap, _, _ = self._validated(capability_id)
        return {'contract': dict(FRONTIER_CONTRACT), 'profiles': list(cap.scope['frontier_profiles']),
                'verification_id': cap.evidence[0]}

    def execute(self, capability_id):
        cap, candidate, _ = self._validated(capability_id)
        receipt = self._verify(candidate)
        self._validated(capability_id)
        if receipt['status'] != 'PASS_NATIVE':
            self._observation(candidate, receipt)
            raise ValueError(receipt['status']+': native execution did not warrant a consequence')
        self._receipt(receipt, candidate)
        consequence = self.machine.append('verified_consequence',
            {'family': 'generic-native-frontier', 'program': cap.program,
             'contract_sha256': self.contract_sha256, 'receipt': self.machine.put(receipt)}, (capability_id,))
        self.machine.flush()
        return receipt, consequence

    def withdraw(self, capability_id, reason='exact generic native ancestor withdrawal'):
        self._validated(capability_id)
        return self.machine.withdraw(capability_id, reason)

    def restore(self, capability_id):
        cap = self.machine.descriptor(capability_id)
        if (cap.operation != 'native.pytest_suite' or cap.source != self.source_descriptor or
                cap.scope != self._expected_scope() or capability_id in self.machine.mt.live_ids(self.machine.log)):
            raise ValueError('restoration requires a withdrawn exact native executable')
        return self.admit(self.machine.get(cap.program), cap.dependencies[2:], supersedes=capability_id)
