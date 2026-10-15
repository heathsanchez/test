"""Source-pinned executable capabilities over the original Metatron warrant log.

FLASH is a dependency-closure consumer, not a universal empirical verifier.
Scientific admission uses the separate original domain-native verifier.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / 'developmental_sources.json').read_text())
EVIDENCE = PINS.pop('evidence')
TRANSITIONS = ('ACTIVATION', 'COMPOSITION', 'REPRESENTATION_REFINEMENT',
               'CAPABILITY_LANGUAGE_EXTENSION', 'CONSTRUCTOR_ACQUISITION',
               'DEVELOPMENTAL_POLICY_IMPROVEMENT', 'INDEPENDENT_VERIFICATION',
               'SCOPED_ADMISSION', 'SELECTIVE_REVOCATION', 'CONSEQUENCE_RECLOSURE',
               'COMPILATION_TRANSPORT')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def check_source(root: Path, key: str):
    pin = PINS[key]
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if head != pin['commit']:
        raise ValueError('source head changed: ' + key)
    # Includes all tracked source used by relative imports, not only entrypoints.
    subprocess.run(['git', '-C', str(root), 'diff', '--exit-code', 'HEAD'], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for name, expected in pin['files'].items():
        if digest((root/name).read_bytes()) != expected:
            raise ValueError('source bytes changed: ' + name)

def safe_task(task):
    if any(k in task for k in ('eval', 'reference_url', 'reference_answer')):
        raise ValueError('evaluation information in producer input')
    if EVIDENCE['task_sha256'].get(str(task.get('task_id'))) != digest(canonical(task).encode()):
        raise ValueError('task changed or outside original frozen scope')
    return json.loads(canonical(task))

@dataclass(frozen=True)
class Capability:
    """Reloadable thin adapter; program semantics remain in the pinned source."""
    operation: str
    source: dict
    scope: dict
    observation: str
    program: str
    generation: int
    dependencies: tuple[str, ...]
    evidence: tuple[str, ...]
    transition: str
    supersedes: str | None = None

class Machine:
    def __init__(self, components: Path, state: Path, evaluator: Path, config: Path,
                 previous_ledger: Path | None = None, previous_flash: Path | None = None):
        self.components, self.state = Path(components).resolve(), Path(state).resolve()
        self.evaluator, self.config = Path(evaluator).resolve(), Path(config).resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state/'objects').mkdir(exist_ok=True)
        self.costs = []
        for key in PINS:
            check_source(self.components/key, key)
        # A fresh cache location prevents loading source-unchecked old bytecode.
        old_prefix = sys.pycache_prefix
        sys.path.insert(0, str(self.components/'metatron'/'runtime'))
        sys.path.insert(0, str(self.components/'flash'))
        with tempfile.TemporaryDirectory(prefix='udm-source-cache-') as cache:
            sys.pycache_prefix = cache
            try:
                self.mt = importlib.import_module('metatron.nucleus')
                self.router = importlib.import_module('qckn_flash_live_router')
                self.envelope = importlib.import_module('realitygraph.flash').ExternalEventEnvelope
            finally:
                sys.pycache_prefix = old_prefix
        for module, expected in ((self.mt, self.components/'metatron'/'runtime'/'metatron'/'nucleus.py'),
                                 (self.router, self.components/'flash'/'qckn_flash_live_router.py')):
            if Path(module.__file__).resolve() != expected.resolve():
                raise ValueError('authority imported from different source')
        ledger = self.state/'metatron-ledger.jsonl'
        self.log = self.mt.loads(ledger.read_text()) if ledger.exists() else (
            self.mt.loads(previous_ledger.read_text()) if previous_ledger else ())
        prior = self.state/'prior-flash.json'
        if not prior.exists() and previous_flash:
            prior.write_text(previous_flash.read_text())
        self.prior_flash = prior.read_text() if prior.exists() else None
        self.flush()

    def put(self, value):
        raw = canonical(value).encode()
        key = digest(raw)
        file = self.state/'objects'/key
        if file.exists() and file.read_bytes() != raw:
            raise ValueError('content-addressed object conflict')
        file.write_bytes(raw)
        return key

    def get(self, key):
        raw = (self.state/'objects'/key).read_bytes()
        if digest(raw) != key:
            raise ValueError('persisted executable object changed')
        return json.loads(raw)

    def append(self, kind, payload, premises=()):
        node = self.mt.Node(kind, payload, premises)
        self.log = self.mt.append(self.log, node)
        return node.id

    def flush(self):
        started = time.perf_counter()
        ledger = self.state/'metatron-ledger.jsonl'
        temp = ledger.with_suffix('.tmp')
        temp.write_text(self.mt.dumps(self.log))
        temp.replace(ledger)
        if self.log or self.prior_flash:
            self.reclose()
        self.costs.append({'phase':'persistence_and_reclosure', 'seconds':time.perf_counter()-started})

    def reclose(self):
        """Project support records to FLASH; projection proves closure only."""
        paths = []
        for node in self.log:
            raw = canonical(node.record()).encode()
            event_id = 'udm:warrant:' + node.id
            if node.kind == 'revoke':
                event = self.envelope.capability_revocation(
                    event_id=event_id, repository='heathsanchez/test',
                    commit=PINS['development']['commit'], authority_snapshot='udm-local-warrant-log-v1',
                    verifier_id='metatron-causal-support-projection-v1', source_evidence=raw,
                    capability_id='udm:warrant:'+node.payload['target'], reason=node.payload['reason'])
            else:
                semantic = [[node.id, digest(raw)]]
                event = self.envelope.capability(
                    event_id=event_id, repository='heathsanchez/test', commit=PINS['development']['commit'],
                    authority_snapshot='udm-local-warrant-log-v1',
                    verifier_id='metatron-causal-support-projection-v1', source_evidence=raw,
                    capability={'capability_id':event_id, 'input_type':'SupportNodeId',
                                'output_type':'SupportRecordSHA256', 'semantics':semantic,
                                'guard_inputs':[node.id], 'certificate_id':node.id,
                                'dependencies':['udm:warrant:'+p for p in node.premises],
                                'authority_snapshot':'udm-local-warrant-log-v1',
                                'verifier_id':'metatron-causal-support-projection-v1',
                                'provenance_ids':[node.id], 'cost':0}, oracle=semantic,
                    support_ids=['udm:warrant:'+p for p in node.premises], origin='support-projection-only')
            folder = self.state/'flash-events'/node.id
            folder.mkdir(parents=True, exist_ok=True)
            (folder/'event.json').write_text(event.to_text())
            (folder/'evidence.json').write_bytes(raw)
            paths.append(folder)
        self.flash = self.router.update_live_state(self.prior_flash, paths)
        (self.state/'flash-state-bundle.json').write_text(self.flash['state_bundle_text'])
        if set(self.mt.live_ids(self.log)) != self.flash_live_ids():
            raise AssertionError('independent causal closure disagreement')
        # Native frontiers are another original FLASH view of this same log.
        # Their readiness never replaces independent domain-native execution.
        from .cross_frontier import reclose_frontiers
        self.frontiers = reclose_frontiers(self)
        return self.flash['summary']

    def flash_live_ids(self):
        prefix = 'udm:warrant:'
        return {x[len(prefix):] for x in self.flash['summary']['active_capability_ids'] if x.startswith(prefix)}

    def descriptor(self, capability_id):
        node = next(n for n in self.log if n.id == capability_id)
        if node.kind != 'executable_capability':
            raise ValueError('not an executable capability')
        raw = node.payload.copy()
        for name in ('dependencies', 'evidence'):
            raw[name] = tuple(raw[name])
        return Capability(**raw)

    def applicable(self, capability_id, task):
        task = safe_task(task)
        cap = self.descriptor(capability_id)
        scope = cap.scope
        if task['task_id'] not in scope['task_ids'] or task['intent_template_id'] != scope['template']:
            return False
        return capability_id in self.mt.live_ids(self.log) and capability_id in self.flash_live_ids()

    def run_source(self, operation, task, observation, program=None, ablate=False):
        task = safe_task(task)
        if operation not in ('grouping', 'stars'):
            raise ValueError('unknown executable source operation')
        if digest(canonical(observation).encode()) != EVIDENCE['observation_sha256'][operation]:
            raise ValueError('observation outside original qualified snapshot')
        if program is not None and digest(canonical(program).encode()) != EVIDENCE['program_sha256'][operation]:
            raise ValueError('program outside original qualified representation')
        check_source(self.components/'development', 'development')
        script = ('webarena_customer_count_representation_synth.py' if operation=='grouping'
                  else 'webarena_gitlab_star_relation_synth.py')
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix='udm-producer-') as work:
            root = Path(work)
            (root/'tasks.json').write_text(canonical([task]))
            (root/'observation.json').write_text(canonical(observation))
            acquire = operation=='grouping' and program is None
            cmd = [sys.executable, '-I', '-B', str(self.components/'development'/'scripts'/script),
                   'induce' if acquire else 'compute', '--task-id', str(task['task_id']),
                   '--task-file', str(root/'tasks.json'), '--observation', str(root/'observation.json')]
            if acquire:
                cmd += ['--output', str(root/'representation.json')]
                output = root/'representation.json'
            else:
                (root/'program.json').write_text(canonical(program))
                cmd += ['--representation' if operation=='grouping' else '--binding', str(root/'program.json'),
                        '--output-dir', str(root/'output')]
                if ablate:
                    if operation != 'grouping':
                        raise ValueError('ablation outside original grouping scope')
                    cmd += ['--ablate-grouping']
                output = root/'output'/str(task['task_id'])/'agent_response.json'
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            value = json.loads(output.read_text())
        check_source(self.components/'development', 'development')
        self.costs.append({'phase':'acquisition' if acquire else 'execution',
                           'operation':operation, 'seconds':time.perf_counter()-started})
        return value

    def verify(self, response, task_id):
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix='udm-native-') as work:
            root = Path(work)
            (root/'response.json').write_text(canonical(response))
            subprocess.run([sys.executable, '-I', '-B', str(HERE/'developmental_verify.py'),
                            '--response', str(root/'response.json'), '--task-id', str(task_id),
                            '--config', str(self.config), '--evaluator', str(self.evaluator),
                            '--out', str(root/'verdict.json')], check=True, capture_output=True)
            receipt = json.loads((root/'verdict.json').read_text())
            if receipt.get('response_sha256') != digest((root/'response.json').read_bytes()):
                raise ValueError('native evidence does not bind actual response')
        self.costs.append({'phase':'verification', 'task_id':task_id,
                           'seconds':time.perf_counter()-started, 'status':receipt['status']})
        return receipt

    def admit(self, operation, task, observation, program, transition, supersedes=None):
        if transition not in TRANSITIONS:
            raise ValueError('unknown developmental transition')
        task = safe_task(task)
        response = self.run_source(operation, task, observation, program)
        receipt = self.verify(response, task['task_id'])
        if receipt['status'] != 'accepted' or receipt['score'] != 1:
            self.append('rejected_admission', {'receipt':receipt, 'operation':operation})
            self.flush()
            raise ValueError('native capability admission rejected')
        generation = 1 + sum(n.kind=='executable_capability' and n.payload['operation']==operation for n in self.log)
        support = self.append('source_support', {'source':PINS['development'], 'original_evidence':EVIDENCE['depth5'],
            'operation':operation, 'generation':generation, 'observation':self.put(observation),
            'program':self.put(program), 'supersedes':supersedes,
            'scope':'original archived WebArena snapshot; local controlled warrant'})
        evidence = self.append('native_verification', {'receipt':receipt, 'response':self.put(response)}, (support,))
        cap = Capability(operation, PINS['development'],
            {'task_ids':[62,63,64,65] if operation=='grouping' else [168,169,172],
             'template':276 if operation=='grouping' else 289,
             'observation_sha256':self.put(observation), 'freshness':'ARCHIVED_SNAPSHOT',
             'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY'},
            self.put(observation), self.put(program), generation, (support,), (evidence,), transition, supersedes)
        result = self.append('executable_capability', asdict(cap), (support, evidence))
        self.flush()
        return result

    def acquire_grouping(self, task, observation, supersedes=None):
        if task['task_id'] != 63 or task['intent_template_id'] != 276:
            raise ValueError('representation acquisition outside original training scope')
        program = self.run_source('grouping', task, observation)
        return self.admit('grouping', task, observation, program, 'REPRESENTATION_REFINEMENT', supersedes)

    def activate_stars(self, observation, binding, task):
        if task['task_id'] not in (168,169,172) or task['intent_template_id'] != 289:
            raise ValueError('star activation outside original scope')
        return self.admit('stars', task, observation, binding, 'ACTIVATION')

    def execute(self, capability_id, task):
        task = safe_task(task)
        cap = self.descriptor(capability_id)
        if task['task_id'] not in cap.scope['task_ids'] or task['intent_template_id'] != cap.scope['template']:
            raise ValueError('task outside capability scope')
        if not self.applicable(capability_id, task):
            raise PermissionError('executable capability causal support withdrawn')
        response = self.run_source(cap.operation, task, self.get(cap.observation), self.get(cap.program))
        receipt = self.verify(response, task['task_id'])
        if receipt['status'] != 'accepted' or receipt['score'] != 1:
            self.append('rejected_execution', {'receipt':receipt}, (capability_id,))
            self.flush()
            raise ValueError('independent native execution rejected')
        outcome = self.append('verified_consequence', {'task_id':task['task_id'],
            'response':self.put(response), 'receipt':receipt,
            'transition':'INDEPENDENT_VERIFICATION'}, (capability_id,))
        self.flush()
        return response, outcome

    def withdraw(self, capability_id, reason):
        cap = self.descriptor(capability_id)
        result = self.append('revoke', {'target':cap.dependencies[0], 'reason':reason,
                                       'controlled_local_withdrawal':True, 'upstream_revocation':False})
        self.flush()
        return result

    def active_capabilities(self):
        return [node.id for _, node in self.mt.live(self.log, 'executable_capability')]

    def select_and_execute(self, task):
        """Activate a unique existing typed route without a caller-selected method."""
        from .consequence_selection import select_and_execute
        return select_and_execute(self, task)

    def select_and_execute_frontier(self, frontier_id, runtime):
        """Select an existing native route; UNKNOWN never starts construction.

        The domain adapter supplies original executable semantics and independent
        verification. FLASH supplies current typed applicability, not a verdict
        on the native program itself. No caller selects a capability identifier.
        """
        from .cross_frontier import require_frontier_route
        if runtime.machine is not self:
            raise ValueError('native adapter belongs to a different warrant state')
        route = require_frontier_route(self, frontier_id, validate=runtime._validated)
        if route['status'] != 'READY':
            return route
        capability_id = route['capability_id']
        cap = self.descriptor(capability_id)
        request = self.get(route['request'])
        if cap.operation == 'flash.native_observation':
            family = request.get('family')
            if family not in cap.scope['families'] or route['profile'] != 'tomlkit:'+family:
                raise ValueError('native observation request differs from verified frontier scope')
            result, consequence = runtime.execute(capability_id, family)
        elif cap.operation == 'native.source_patch':
            if request.get('subject') != cap.scope['target']:
                raise ValueError('native constructor request differs from verified frontier scope')
            result, consequence = runtime.execute(capability_id)
        else:
            raise ValueError('native capability has no qualified executable adapter')
        return {**route, 'native': result, 'consequence': consequence,
                'transition': 'ACTIVATION', 'new_constructor_invocations': 0}
