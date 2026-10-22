"""Revocable native metadata instruments over the existing warrant Machine.

Every invocation runs the original exact-source build and an independent fresh
build. Metadata warrants only the declared experiment prerequisite. Original
protected-test authority and externally supplied permission remain separate.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
import secrets
import time

from . import decisive_native_verify as original
from . import native_metadata_v44 as metadata
from . import native_source_v42 as source
from . import native_materialization_v43 as previous
from . import developmental_machine_v44 as framework
from . import cross_frontier_v44 as frontier
from .native_runtime_v2 import AUTHORITY as _AUTHORITY

canonical, digest, Capability = framework.canonical, framework.digest, framework.Capability
fingerprint = original.fingerprint
OPERATION = 'source.observe_native_metadata'
VERIFICATION_KIND = frontier.METADATA_VERIFICATION
REQUEST_SCHEMA = 'UDM_SOURCE_NATIVE_METADATA_REQUEST_V44'
AUTHORITY = json.loads(canonical(_AUTHORITY))
FRONTIER_CONTRACT = {'input_type': 'ExactOriginalBackendSourceV44',
    'output_type': 'IndependentSourceNativeMetadataV44',
    'authority_snapshot': 'udm-local-source-native-metadata-v44',
    'verifier_id': 'original-backend-independent-metadata-rebuild-v44'}
_FIELDS = {'schema', 'repo_path', 'commit', 'source_identity', 'interpreter',
           'environment_sha256', 'protocol_binding', 'horizon_seconds', 'authority_ceiling'}
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
_PINS = {module.__name__: (module, digest(Path(module.__file__).read_bytes()))
         for module in (metadata, source, previous, framework, frontier)}


def _copy(value):
    return json.loads(canonical(value))


def _guard():
    framework._guard()
    source._guard()
    previous._guard()
    if (digest(Path(__file__).read_bytes()) != _LOADED_SHA256
            or any(digest(Path(module.__file__).read_bytes()) != expected
                   for module, expected in _PINS.values())):
        raise ValueError('UNKNOWN_V44_METADATA_INSTRUMENT_SOURCE_CHANGED')


def request(repo, commit, interpreter, *, environment_sha256, protocol_binding, horizon_seconds=300):
    """Bind immutable source and an external executable environment; never build."""
    _guard()
    repo, interpreter = Path(repo).absolute(), Path(interpreter).absolute()
    if repo.resolve() != repo or not repo.is_dir() or not interpreter.is_file():
        raise ValueError('canonical original source and executable interpreter required')
    if (any(not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None
            for value in (environment_sha256, protocol_binding))
            or type(horizon_seconds) is not int or not 1 <= horizon_seconds <= 600):
        raise ValueError('exact external environment, protocol and finite budget required')
    identity, _, manifest = source.snapshot(repo, commit)
    source.require_executable(manifest)
    if fingerprint(original.environment_identity(str(interpreter))) != environment_sha256:
        raise ValueError('source metadata request executable environment differs')
    return {'schema': REQUEST_SCHEMA, 'repo_path': str(repo), 'commit': commit,
        'source_identity': identity, 'interpreter': str(interpreter),
        'environment_sha256': environment_sha256, 'protocol_binding': protocol_binding,
        'horizon_seconds': horizon_seconds, 'authority_ceiling': _copy(AUTHORITY)}


def _request(value):
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError('strict metadata instrument request required')
    result = request(value['repo_path'], value['commit'], value['interpreter'],
        environment_sha256=value['environment_sha256'], protocol_binding=value['protocol_binding'],
        horizon_seconds=value['horizon_seconds'])
    if value != result:
        raise ValueError('metadata request source identity or authority differs')
    return result


def _program():
    return {'schema': 'UDM_SOURCE_NATIVE_METADATA_PROGRAM_V44', 'operation': OPERATION,
        'metadata_source_sha256': digest(Path(metadata.__file__).read_bytes()),
        'adapter_sha256': _LOADED_SHA256, 'native_outcome_authority': False,
        'source_algorithm': 'original-qualified-pip-wheel-plus-independent-normalized-rebuild'}


def _profile(value):
    return 'exact-source-native-metadata-v44:'+fingerprint(value)


def _scope(value):
    return {'request_sha256': fingerprint(value), 'environment_sha256': value['environment_sha256'],
        'authority_ceiling': _copy(AUTHORITY), 'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
        'frontier_contract': _copy(FRONTIER_CONTRACT), 'frontier_profiles': [_profile(value)]}


def _source_descriptor():
    return {'schema': 'UDM_SOURCE_NATIVE_METADATA_OPERATOR_SOURCE_V44', 'operation': OPERATION,
        'source_sha256': {str(Path(module.__file__)): expected for module, expected in _PINS.values()},
        'adapter_sha256': _LOADED_SHA256, 'authority_ceiling': _copy(AUTHORITY)}


def _wheel_evidence(value):
    """Locate retained original builder witnesses, without trusting path strings."""
    found = {}
    def walk(item):
        if isinstance(item, dict):
            if {'wheel_path', 'wheel_sha256', 'wheel_content_sha256'} <= item.keys():
                key = item['wheel_path']
                if key in found and found[key] != item:
                    raise ValueError('conflicting original wheel witnesses')
                found[key] = item
            for child in item.values():
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
    walk(value)
    if len(found) != 2:
        raise ValueError('independent original metadata invocation must retain two actual wheels')
    return [found[key] for key in sorted(found)]


class MetadataRuntime(previous.MaterializationRuntime):
    """Thin typed adapter; liveness and CAS-wheel recovery reuse V43 helpers."""
    def __init__(self, machine, output):
        _guard()
        if not isinstance(machine, framework.Machine):
            raise ValueError('the existing versioned V44 Machine is required')
        super().__init__(machine, output)

    def register(self, frontier_id, value):
        value = _request(value)
        return frontier.register_frontier(self.machine, frontier_id, contract=FRONTIER_CONTRACT,
                                          profile=_profile(value), request=value)

    def _validate_invocation(self, invocation):
        if (not isinstance(invocation, dict) or set(invocation) != {
                'schema', 'request', 'observation', 'artifacts'}
                or invocation['schema'] != 'UDM_RETAINED_SOURCE_NATIVE_METADATA_INVOCATION_V44'):
            raise ValueError('wrong retained metadata invocation')
        value = _request(self.machine.get(invocation['request']))
        observation = self.machine.get(invocation['observation'])
        wheels = _wheel_evidence(observation)
        artifacts = invocation['artifacts']
        if (not isinstance(artifacts, list) or len(artifacts) != 2
                or [row.get('evidence') for row in artifacts] != wheels):
            raise ValueError('retained metadata wheel inventory differs')
        for row in artifacts:
            if set(row) != {'evidence', 'artifact'}:
                raise ValueError('wrong retained metadata artifact fields')
            self._artifact({'wheel_evidence': row['evidence']}, row['artifact'])
        checked = metadata.validate_observation(value['repo_path'], value['commit'], value['interpreter'],
            observation, environment_sha256=value['environment_sha256'])
        if checked != observation['metadata']:
            raise ValueError('retained metadata observation differs from independent original artifacts')
        return value, observation

    def _run(self, value, label):
        folder = self.output/label/secrets.token_hex(16)
        before = time.perf_counter()
        observation, evidence = None, None
        try:
            evidence = metadata.observe(value['repo_path'], value['commit'], value['interpreter'],
                folder/'observe', environment_sha256=value['environment_sha256'],
                timeout=value['horizon_seconds'])
            observation = metadata.verify(value['repo_path'], value['commit'], value['interpreter'],
                evidence, folder/'independent', environment_sha256=value['environment_sha256'],
                timeout=value['horizon_seconds'])
            invocation = {'schema': 'UDM_RETAINED_SOURCE_NATIVE_METADATA_INVOCATION_V44',
                'request': self.machine.put(value), 'observation': self.machine.put(dict(observation)),
                'artifacts': [{'evidence': wheel,
                    'artifact': self._retain_wheel({'wheel_evidence': wheel})}
                    for wheel in _wheel_evidence(observation)]}
            self._validate_invocation(invocation)
            return observation, invocation
        finally:
            attempts = []
            for phase in ('observe', 'independent'):
                path = folder/phase/'build-attempt.json'
                if path.is_file() and not path.is_symlink():
                    attempts.append({'phase': phase, 'path': str(path),
                        'sha256': digest(path.read_bytes()), 'record': json.loads(path.read_text())})
            self.machine.costs.append({'phase': 'source_native_metadata_v44_'+label,
                'seconds': time.perf_counter()-before, 'output': str(folder),
                'status': observation.get('status') if observation is not None else 'UNKNOWN_METADATA_BUILD',
                'inclusive_not_additive': True,
                'actual_build_attempts': attempts,
                'actual_build_calls': sum(row['record'].get('build_calls', 0) for row in attempts),
                'acquisition_costs': _copy(evidence.get('costs', {})) if evidence is not None else None,
                'verification_costs': _copy(observation.get('costs', {})) if observation is not None else None})

    def admit(self, value, *, supersedes=None):
        value = _request(value)
        program, scope = self.machine.put(_program()), _scope(value)
        prior = [node for node in self.machine.log if node.kind == 'executable_capability'
                 and node.payload.get('operation') == OPERATION and node.payload.get('scope') == scope]
        if supersedes is None and prior:
            raise ValueError('an existing metadata scope requires explicit supersession')
        if supersedes is not None:
            old = self.machine.descriptor(supersedes)
            live = set(self.machine.mt.live_ids(self.machine.log)) | self.machine.flash_live_ids()
            if (not prior or prior[-1].id != supersedes or old.program != program or old.scope != scope
                    or old.source != _source_descriptor() or any(node.id in live for node in prior)
                    or old.dependencies[0] in live):
                raise ValueError('metadata restoration requires the exact withdrawn prior scope')
        if not any(node.kind == frontier.REGISTRATION and node.payload.get('contract') == FRONTIER_CONTRACT
                   and node.payload.get('profile') == _profile(value) for node in self.machine.log):
            raise ValueError('metadata obligation must be registered before admission')
        _, invocation = self._run(value, 'admission')
        generation, nonce = len(prior)+1, secrets.token_hex(32)
        authority = self._record_once('execution_authority_ceiling', AUTHORITY)
        origin = self._record_once('native_metadata_source_v44', _source_descriptor(), (authority,))
        invocation_key = self.machine.put(invocation)
        support_payload = {'family': 'source-native-metadata-v44', 'program': program,
            'generation': generation, 'nonce': nonce, 'supersedes': supersedes,
            'request': invocation['request'], 'invocation': invocation_key}
        support = self.machine.append('source_support', support_payload, (origin, authority))
        receipt = {'schema': 'UDM_SOURCE_NATIVE_METADATA_ADMISSION_V44',
            'status': 'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME', **support_payload}
        verified = self.machine.append(VERIFICATION_KIND,
            {'program': program, 'receipt': self.machine.put(receipt)}, (support,))
        cap = Capability(OPERATION, _source_descriptor(), scope, invocation_key, program, generation,
            (support,), (verified,), 'SCOPED_ADMISSION', supersedes)
        ident = self.machine.append('executable_capability', asdict(cap), (support, verified))
        self.machine.flush()
        self._validated(ident)
        frontier.publish_frontier_route(self.machine, ident, contract=FRONTIER_CONTRACT,
            profiles=scope['frontier_profiles'], verification_id=verified, validate=self._validated)
        return ident

    def _validated(self, capability_id):
        self._live(capability_id)
        _guard()
        cap, nodes = self.machine.descriptor(capability_id), self._nodes()
        if (cap.operation != OPERATION or cap.source != _source_descriptor()
                or len(cap.dependencies) != 1 or len(cap.evidence) != 1
                or cap.transition != 'SCOPED_ADMISSION' or self.machine.get(cap.program) != _program()):
            raise ValueError('wrong metadata capability source, program or transition')
        self._live(*cap.dependencies, *cap.evidence)
        invocation = self.machine.get(cap.observation)
        value, _ = self._validate_invocation(invocation)
        support, verified = nodes[cap.dependencies[0]], nodes[cap.evidence[0]]
        receipt = self.machine.get(verified.payload['receipt'])
        nonce = receipt.get('nonce')
        expected_support = {'family': 'source-native-metadata-v44', 'program': cap.program,
            'generation': cap.generation, 'nonce': nonce, 'supersedes': cap.supersedes,
            'request': invocation['request'], 'invocation': cap.observation}
        expected_receipt = {'schema': 'UDM_SOURCE_NATIVE_METADATA_ADMISSION_V44',
            'status': 'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME', **expected_support}
        if (not isinstance(nonce, str) or re.fullmatch('[0-9a-f]{64}', nonce) is None
                or cap.scope != _scope(value) or support.kind != 'source_support'
                or support.payload != expected_support or len(support.premises) != 2
                or verified.kind != VERIFICATION_KIND
                or verified.payload != {'program': cap.program, 'receipt': fingerprint(receipt)}
                or receipt != expected_receipt or tuple(verified.premises) != (support.id,)
                or tuple(nodes[capability_id].premises) != (support.id, verified.id)):
            raise ValueError('metadata evidence, scope or causal lineage differs')
        origin, authority = (nodes[key] for key in support.premises)
        self._live(origin.id, authority.id)
        if (origin.kind != 'native_metadata_source_v44' or origin.payload != _source_descriptor()
                or tuple(origin.premises) != (authority.id,)
                or authority.kind != 'execution_authority_ceiling' or authority.payload != AUTHORITY
                or authority.premises):
            raise ValueError('metadata capability external authority differs')
        earlier = self.machine.log[:self.machine.log.index(nodes[capability_id])+1]
        if cap.generation != sum(node.kind == 'executable_capability'
                and node.payload.get('operation') == OPERATION
                and node.payload.get('scope') == cap.scope for node in earlier):
            raise ValueError('metadata retained generation differs')
        return cap

    validate = _validated

    def execute(self, capability_id, value):
        cap = self._validated(capability_id)
        value = _request(value)
        if cap.scope != _scope(value):
            raise ValueError('metadata invocation is outside warranted exact request scope')
        observation, invocation = self._run(value, 'execution')
        self._validated(capability_id)
        receipt = {'schema': 'UDM_SOURCE_NATIVE_METADATA_EXECUTION_V44',
            'status': 'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME',
            'instrument': capability_id, 'generation': cap.generation, 'program': cap.program,
            'invocation': self.machine.put(invocation)}
        consequence = self.machine.append('verified_consequence', {
            'family': 'source-native-metadata-v44', 'receipt': self.machine.put(receipt),
            'request': invocation['request'], 'observation': invocation['observation']}, (capability_id,))
        self.machine.flush()
        return observation, consequence

    def bind(self, capability_id, consequence_id):
        cap = self._validated(capability_id)
        self._live(consequence_id)
        node = self._nodes()[consequence_id]
        if node.kind != 'verified_consequence' or tuple(node.premises) != (capability_id,):
            raise ValueError('metadata exact invocation consequence is not this instrument')
        receipt = self.machine.get(node.payload['receipt'])
        if (receipt.get('schema') != 'UDM_SOURCE_NATIVE_METADATA_EXECUTION_V44'
                or receipt.get('status') != 'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME'
                or receipt.get('instrument') != capability_id or receipt.get('generation') != cap.generation
                or receipt.get('program') != cap.program
                or node.payload.get('family') != 'source-native-metadata-v44'):
            raise ValueError('metadata invocation evidence or generation differs')
        invocation = self.machine.get(receipt['invocation'])
        value, observation = self._validate_invocation(invocation)
        if (node.payload.get('request') != fingerprint(value)
                or node.payload.get('observation') != fingerprint(observation)
                or cap.scope != _scope(value)):
            raise ValueError('metadata consequence request or observation differs')
        return {'capability_id': capability_id, 'generation': cap.generation,
            'consequence_id': consequence_id, 'request_sha256': fingerprint(value),
            'observation_sha256': fingerprint(observation)}

    def preflight(self, binding):
        if (not isinstance(binding, dict) or set(binding) != {
                'capability_id', 'generation', 'consequence_id', 'request_sha256', 'observation_sha256'}):
            raise ValueError('strict retained metadata binding required')
        # Liveness is checked before re-reading or executing any source operation.
        self._live(binding['capability_id'], binding['consequence_id'])
        if self.bind(binding['capability_id'], binding['consequence_id']) != binding:
            raise ValueError('metadata binding differs from exact live instrument invocation')
        node = self._nodes()[binding['consequence_id']]
        receipt = self.machine.get(node.payload['receipt'])
        return self._validate_invocation(self.machine.get(receipt['invocation']))

    def restore(self, capability_id, value):
        return self.admit(value, supersedes=capability_id)
