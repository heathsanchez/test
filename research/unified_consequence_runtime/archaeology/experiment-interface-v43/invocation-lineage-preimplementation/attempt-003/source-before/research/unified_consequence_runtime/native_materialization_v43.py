"""Retained original-backend materialization instrument over existing Machine.

Its generic program invokes the source-pinned builder; invocation requests and
independent wheel witnesses carry individual source identities. Materialization
readiness supplies no native pytest result or external-effect authority.
"""
from __future__ import annotations

import base64
from dataclasses import asdict
import json
from pathlib import Path
import secrets
import time

from . import native_admission_v42 as admission
from . import native_build_v43 as build
from . import native_source_v42 as source
from . import developmental_machine as original_machine
from . import developmental_machine_v43 as framework
from . import cross_frontier_v43 as frontier
from .generated_overlay_gate import _members, wheel_content_digest
from .native_runtime_v2 import AUTHORITY as _ORIGINAL_AUTHORITY

canonical, digest, Capability = framework.canonical, framework.digest, framework.Capability
fingerprint = build.fingerprint
OPERATION = 'source.materialize_declared_backend'
VERIFICATION_KIND = frontier.MATERIALIZATION_VERIFICATION
REQUEST_SCHEMA = 'UDM_NATIVE_MATERIALIZATION_REQUEST_V43'
AUTHORITY = json.loads(canonical(_ORIGINAL_AUTHORITY))
FRONTIER_CONTRACT = {'input_type': 'NativeDeclaredBackendSourceV43',
    'output_type': 'AuthenticatedGeneratedBuildV43',
    'authority_snapshot': 'udm-local-original-backend-research-v43',
    'verifier_id': 'native-build-v43-independent-original-backend'}
_CONTRACT_FIELDS = frozenset(('schema', 'repository', 'repo_path', 'commit', 'git_tree',
    'tracked_tree_sha256', 'file_count', 'interpreter', 'environment_sha256',
    'protocol_binding', 'horizon_seconds', 'generated_build'))
_POLICY_FIELDS = frozenset(('schema', 'collection_seconds', 'execution_seconds', 'pytest_version', 'plugins'))
_SOURCE_PATHS = (Path(__file__), Path(build.__file__), Path(admission.__file__),
                 Path(source.__file__), Path(framework.__file__), Path(frontier.__file__),
                 Path(original_machine.__file__))
_SOURCE_PINS = {str(path): digest(path.read_bytes()) for path in _SOURCE_PATHS}


def _copy(value):
    try:
        return json.loads(canonical(value))
    except (TypeError, ValueError) as error:
        raise ValueError('materialization inputs require strict JSON') from error


def _guard():
    build._guard()
    framework._guard()
    admission.assert_source_identity()
    if any(digest(Path(path).read_bytes()) != expected for path, expected in _SOURCE_PINS.items()):
        raise ValueError('UNKNOWN_V43_MATERIALIZATION_SOURCE_CHANGED')


def request(contract, authority, policy):
    """Copy and authenticate the original source request, without building it."""
    _guard()
    contract, authority, policy = map(_copy, (contract, authority, policy))
    if (not isinstance(contract, dict) or set(contract) != _CONTRACT_FIELDS
            or contract['schema'] != build.CONTRACT_SCHEMA or contract['generated_build'] is not None):
        raise ValueError('wrong original materialization contract')
    if (not isinstance(policy, dict) or set(policy) != _POLICY_FIELDS
            or policy['schema'] != build.POLICY_SCHEMA
            or any(type(policy[key]) is not int or not 1 <= policy[key] <= 600
                   for key in ('collection_seconds', 'execution_seconds'))
            or contract['horizon_seconds'] != policy['execution_seconds']):
        raise ValueError('wrong original materialization policy')
    identity, files, manifest = source.snapshot(contract['repo_path'], contract['commit'])
    source.require_executable(manifest)
    if any(contract[key] != value for key, value in identity.items()):
        raise ValueError('materialization request source identity differs')
    admission.validate_suite_contract(contract, authority)
    _, original_files, _ = source.snapshot(contract['repo_path'], authority['baseline_commit'])
    if build.declared_outputs(original_files) != build.declared_outputs(files):
        raise ValueError('materialization declaration differs from original source')
    return {'schema': REQUEST_SCHEMA, 'contract': contract, 'authority': authority, 'policy': policy}


def _request(value):
    if not isinstance(value, dict) or set(value) != {'schema', 'contract', 'authority', 'policy'}:
        raise ValueError('wrong strict materialization request fields')
    expected = request(value['contract'], value['authority'], value['policy'])
    if value != expected:
        raise ValueError('wrong materialization request schema or identity')
    return expected


def _program():
    return {'schema': 'UDM_NATIVE_MATERIALIZATION_PROGRAM_V43', 'operation': OPERATION,
            'backend': 'hatchling.build', 'version_source': 'vcs',
            'recipe_sha256': build.recipe_digest(),
            'builder_sha256': digest(Path(build.__file__).read_bytes()),
            'adapter_sha256': digest(Path(__file__).read_bytes())}


def _profile(value):
    return 'original-hatch-vcs-v43:' + fingerprint({
        'program': _program(), 'environment_sha256': value['contract']['environment_sha256'],
        'policy': value['policy']})


def _scope(value):
    return {'backend': 'hatchling.build', 'version_source': 'vcs',
            'recipe_sha256': build.recipe_digest(),
            'environment_sha256': value['contract']['environment_sha256'],
            'policy_sha256': fingerprint(value['policy']),
            'authority_ceiling': _copy(AUTHORITY), 'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
            'frontier_contract': _copy(FRONTIER_CONTRACT), 'frontier_profiles': [_profile(value)]}


def _source_descriptor():
    return {'schema': 'UDM_NATIVE_MATERIALIZATION_OPERATOR_SOURCE_V43',
            'source_sha256': dict(_SOURCE_PINS), 'operation': OPERATION,
            'recipe_sha256': build.recipe_digest(), 'authority_ceiling': _copy(AUTHORITY)}


def _wheel(evidence):
    try:
        return evidence['wheel_evidence']
    except (KeyError, TypeError) as error:
        raise ValueError('missing retained materialization wheel evidence') from error


class MaterializationRuntime:
    def __init__(self, machine, output):
        _guard()
        self.machine, self.output = machine, Path(output).absolute()
        if self.output.resolve() != self.output:
            raise ValueError('materialization output must be canonical')

    def _live(self, *identifiers):
        live = set(self.machine.mt.live_ids(self.machine.log)) & self.machine.flash_live_ids()
        if any(ident not in live for ident in identifiers):
            raise PermissionError('materialization causal support is withdrawn')

    def _nodes(self):
        return {node.id: node for node in self.machine.log}

    def _record_once(self, kind, payload, premises=()):
        for node in self.machine.log:
            if node.kind == kind and node.payload == payload and tuple(node.premises) == tuple(premises):
                return node.id
        return self.machine.append(kind, payload, premises)

    def register(self, frontier_id, value):
        value = _request(value)
        return frontier.register_frontier(self.machine, frontier_id, contract=FRONTIER_CONTRACT,
                                          profile=_profile(value), request=value)

    def _retain_wheel(self, evidence):
        wheel = _wheel(evidence)
        path = Path(wheel['wheel_path'])
        if path.resolve() != path or path.is_symlink() or not path.is_file():
            raise ValueError('missing or redirected materialization artifact')
        raw = path.read_bytes()
        if digest(raw) != wheel['wheel_sha256'] or wheel_content_digest(path) != wheel['wheel_content_sha256']:
            raise ValueError('materialization wheel artifact differs')
        return self.machine.put({'schema': 'UDM_RETAINED_MATERIALIZATION_WHEEL_V43',
                                 'filename': path.name, 'base64': base64.b64encode(raw).decode()})

    def _artifact(self, evidence, artifact_key):
        """CAS authorizes recovery of this exact retained transport artifact."""
        retained = self.machine.get(artifact_key)
        wheel = _wheel(evidence)
        name = retained.get('filename')
        if (retained.get('schema') != 'UDM_RETAINED_MATERIALIZATION_WHEEL_V43'
                or not isinstance(name, str) or Path(name).name != name or not name.endswith('.whl')):
            raise ValueError('wrong retained materialization artifact schema')
        try:
            raw = base64.b64decode(retained['base64'], validate=True)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('corrupt retained materialization wheel') from error
        if digest(raw) != wheel['wheel_sha256']:
            raise ValueError('retained materialization wheel digest differs')
        path = Path(wheel['wheel_path']).absolute()
        if path.resolve() != path or path.name != name or path.is_symlink():
            raise ValueError('retained materialization output is redirected')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.parent.resolve() != path.parent:
                raise ValueError('retained materialization parent is redirected')
            with path.open('xb') as stream:
                stream.write(raw)
        if not path.is_file() or path.read_bytes() != raw or wheel_content_digest(path) != wheel['wheel_content_sha256']:
            raise ValueError('retained materialization artifact bytes differ')
        return path

    def _validate_invocation(self, invocation):
        if (not isinstance(invocation, dict) or set(invocation) != {
                'schema', 'request', 'evidence', 'artifact', 'generated', 'verification', 'independent_artifact'}
                or invocation['schema'] != 'UDM_RETAINED_MATERIALIZATION_INVOCATION_V43'):
            raise ValueError('wrong retained materialization invocation')
        value = _request(self.machine.get(invocation['request']))
        evidence = self.machine.get(invocation['evidence'])
        self._artifact(evidence, invocation['artifact'])
        generated = build.read_generated(value['contract'], value['authority'], value['policy'], evidence)
        expected_generated = {name: base64.b64encode(raw).decode() for name, raw in generated.items()}
        if self.machine.get(invocation['generated']) != expected_generated:
            raise ValueError('retained generated bytes differ')
        verified = self.machine.get(invocation['verification'])
        if (verified.get('schema') != 'UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43'
                or verified.get('status') != 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
                or verified.get('evidence_sha256') != fingerprint(evidence)
                or verified.get('binding') != evidence['binding']
                or verified.get('costs', {}).get('build_calls') != 1):
            raise ValueError('retained independent materialization verification differs')
        independent_evidence = {'wheel_evidence': verified['build']['generated_wheel_evidence']}
        independent = self._artifact(independent_evidence, invocation['independent_artifact'])
        if _members(independent) != _members(Path(_wheel(evidence)['wheel_path'])):
            raise ValueError('retained independent wheel differs from materialization')
        return value, evidence, verified

    def _run(self, value, label):
        """All actual backend invocations and failed-attempt costs are retained."""
        started, before, receipt = time.perf_counter(), build.attempt_snapshot(), None
        folder = self.output / label / secrets.token_hex(16)
        try:
            evidence = build.prepare(value['contract'], value['authority'], value['policy'], folder / 'prepare')
            generated, receipt = build.verify(value['contract'], value['authority'], value['policy'],
                                              evidence, folder / 'independent')
            invocation = {'schema': 'UDM_RETAINED_MATERIALIZATION_INVOCATION_V43',
                'request': self.machine.put(value), 'evidence': self.machine.put(evidence),
                'artifact': self._retain_wheel(evidence),
                'generated': self.machine.put({name: base64.b64encode(raw).decode()
                                               for name, raw in generated.items()}),
                'verification': self.machine.put(receipt),
                'independent_artifact': self._retain_wheel(
                    {'wheel_evidence': receipt['build']['generated_wheel_evidence']})}
            self._validate_invocation(invocation)
            return evidence, invocation, receipt
        finally:
            after = build.attempt_snapshot()
            attempts = {key: after[key] - before[key] for key in before if type(before[key]) is int
                        and type(after.get(key)) is int}
            self.machine.costs.append({'phase': 'native_materialization_v43_' + label,
                'seconds': time.perf_counter() - started, 'output': str(folder),
                'status': receipt.get('status') if receipt else 'UNKNOWN_BUILD_ERROR',
                'costs': receipt.get('costs', {}) if receipt else {}, 'builder_attempts': attempts})

    def admit(self, value, *, supersedes=None):
        value = _request(value)
        scope, program = _scope(value), self.machine.put(_program())
        prior = [node for node in self.machine.log if node.kind == 'executable_capability'
                 and node.payload.get('operation') == OPERATION and node.payload.get('scope') == scope]
        if supersedes is not None:
            old = self.machine.descriptor(supersedes)
            live = set(self.machine.mt.live_ids(self.machine.log)) | self.machine.flash_live_ids()
            if (not prior or prior[-1].id != supersedes or old.operation != OPERATION
                    or old.program != program or old.scope != scope or old.source != _source_descriptor()
                    or any(node.id in live for node in prior) or old.dependencies[0] in live):
                raise ValueError('materialization restoration requires withdrawn exact prior scope')
        elif prior:
            raise ValueError('existing materialization scope requires explicit supersession')
        # Obligations must predate discovery/admission of the resolving operation.
        registrations = [node for node in self.machine.log if node.kind == frontier.REGISTRATION
                         and node.payload.get('contract') == FRONTIER_CONTRACT
                         and node.payload.get('profile') == _profile(value)]
        if not registrations:
            raise ValueError('materialization obligation must be registered before admission')
        evidence, invocation, verification = self._run(value, 'admission')
        generation, nonce = len(prior) + 1, secrets.token_hex(32)
        authority = self._record_once('execution_authority_ceiling', AUTHORITY)
        origin = self._record_once('native_materialization_source_v43', _source_descriptor(), (authority,))
        observation = self.machine.put(invocation)
        receipt = {'schema': 'UDM_NATIVE_MATERIALIZATION_ADMISSION_V43',
            'status': 'INDEPENDENT_MATERIALIZATION_ONLY', 'program': program,
            'generation': generation, 'nonce': nonce, 'request': invocation['request'],
            'invocation': observation, 'costs': verification['costs']}
        support_payload = {'family': 'native-materialization-v43', 'program': program,
            'generation': generation, 'nonce': nonce, 'supersedes': supersedes,
            'observation': observation, 'request': invocation['request']}
        support = self.machine.append('source_support', support_payload, (origin, authority))
        verified = self.machine.append(VERIFICATION_KIND,
            {'program': program, 'receipt': self.machine.put(receipt)}, (support,))
        cap = Capability(OPERATION, _source_descriptor(), scope, observation, program, generation,
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
            raise ValueError('wrong retained materialization executable or source')
        self._live(*cap.dependencies, *cap.evidence)
        invocation = self.machine.get(cap.observation)
        value, _, _ = self._validate_invocation(invocation)
        support, verified = nodes[cap.dependencies[0]], nodes[cap.evidence[0]]
        receipt = self.machine.get(verified.payload['receipt'])
        expected_receipt = {'schema': 'UDM_NATIVE_MATERIALIZATION_ADMISSION_V43',
            'status': 'INDEPENDENT_MATERIALIZATION_ONLY', 'program': cap.program,
            'generation': cap.generation, 'nonce': receipt.get('nonce'),
            'request': invocation['request'], 'invocation': cap.observation,
            'costs': self.machine.get(invocation['verification'])['costs']}
        expected_support = {'family': 'native-materialization-v43', 'program': cap.program,
            'generation': cap.generation, 'nonce': receipt.get('nonce'), 'supersedes': cap.supersedes,
            'observation': cap.observation, 'request': invocation['request']}
        if (cap.scope != _scope(value) or receipt != expected_receipt
                or not isinstance(receipt.get('nonce'), str) or len(receipt['nonce']) != 64
                or support.kind != 'source_support' or support.payload != expected_support
                or len(support.premises) != 2 or verified.kind != VERIFICATION_KIND
                or verified.payload.get('program') != cap.program
                or tuple(verified.premises) != (support.id,)
                or tuple(nodes[capability_id].premises) != (support.id, verified.id)):
            raise ValueError('materialization retained receipt, scope or lineage differs')
        origin, authority = (nodes[key] for key in support.premises)
        self._live(origin.id, authority.id)
        if (origin.kind != 'native_materialization_source_v43' or origin.payload != _source_descriptor()
                or tuple(origin.premises) != (authority.id,) or authority.kind != 'execution_authority_ceiling'
                or authority.payload != AUTHORITY or authority.premises):
            raise ValueError('materialization external authority lineage differs')
        prior = [node.id for node in self.machine.log[:self.machine.log.index(nodes[capability_id]) + 1]
                 if node.kind == 'executable_capability' and node.payload.get('operation') == OPERATION
                 and node.payload.get('scope') == cap.scope]
        if cap.generation != len(prior):
            raise ValueError('materialization generation differs from retained history')
        return cap

    def execute(self, capability_id, value):
        cap = self._validated(capability_id)
        value = _request(value)
        if cap.scope != _scope(value):
            raise ValueError('source request is outside independently qualified materialization scope')
        evidence, invocation, verification = self._run(value, 'execution')
        self._validated(capability_id)
        receipt = {'schema': 'UDM_NATIVE_MATERIALIZATION_EXECUTION_V43',
            'status': 'INDEPENDENT_MATERIALIZATION_ONLY', 'program': cap.program,
            'instrument': capability_id, 'generation': cap.generation,
            'invocation': self.machine.put(invocation), 'costs': verification['costs']}
        consequence = self.machine.append('verified_consequence', {
            'family': 'native-materialization-v43', 'receipt': self.machine.put(receipt),
            'request': invocation['request'], 'evidence': invocation['evidence']}, (capability_id,))
        self.machine.flush()
        return evidence, consequence

    def bind_native(self, capability_id, contract, authority, policy):
        """Authenticate exact source evidence under this live instrument generation."""
        cap = self._validated(capability_id)
        value = request(dict(contract, generated_build=None), authority, policy)
        if cap.scope != _scope(value):
            raise ValueError('native request differs from materialization instrument scope')
        request_key, evidence_key = fingerprint(value), fingerprint(contract['generated_build'])
        matches = []
        for node in self.machine.log:
            if (node.kind != 'verified_consequence' or tuple(node.premises) != (capability_id,)
                    or node.payload.get('family') != 'native-materialization-v43'
                    or node.payload.get('request') != request_key or node.payload.get('evidence') != evidence_key):
                continue
            self._live(node.id)
            retained = self.machine.get(node.payload['receipt'])
            if (retained.get('schema') != 'UDM_NATIVE_MATERIALIZATION_EXECUTION_V43'
                    or retained.get('instrument') != capability_id or retained.get('generation') != cap.generation
                    or retained.get('program') != cap.program):
                raise ValueError('native materialization consequence generation differs')
            invocation = self.machine.get(retained['invocation'])
            actual_request, evidence, _ = self._validate_invocation(invocation)
            if actual_request != value or evidence != contract['generated_build']:
                raise ValueError('native generated evidence differs from retained invocation')
            matches.append(node.id)
        if not matches:
            raise ValueError('native generated evidence lacks this generation\'s retained materialization consequence')
        return {'capability_id': capability_id, 'generation': cap.generation,
                'consequence_id': matches[0], 'request_sha256': request_key, 'evidence_sha256': evidence_key}

    def restore(self, capability_id, value):
        return self.admit(value, supersedes=capability_id)
