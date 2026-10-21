"""Original source-native constructor instances through the existing UDM.

The two constructor families and observation grammar are human supplied. Their
source-derived outputs are executable patches, independently checked against
original native objects and original tests. This adapter grants no external
permission and does not claim a hostile-process sandbox.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from dataclasses import asdict
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import ModuleType

try:
    from .developmental_machine import Capability, canonical, digest
except ImportError:  # Separate-process verifier/producer; no Machine is created.
    Capability = None
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    def digest(raw):
        return hashlib.sha256(raw).hexdigest()

SOURCE_COMMIT = '8befdf9d9d9565bc2640d380f98c6547b3660a63'
SOURCE_ROOT = 'research/mathgraph_obligation_compiler_20261015'
SOURCE_FILES = {
    'observer_genesis.py': '600f74215e420ddf0ded533bc923b12095b1a2f3972b46a9b01ee32eeb4d0091',
    'repair_compiler.py': 'aae8e63ab945e063cb85d0a0a4ed8e1a24a885dec9b487d2a687f0ffce7ab338',
    'FROZEN_PROTOCOL.md': '82eb4b152ee4df53f0e94d19fcd5409056a805f55775abb84672eaa6e7e7d4cd',
    'FROZEN_REPAIR_PROTOCOL.md': 'f3d21357cc1dacd7ca0a5b17c3d01c0e737086063c063891d9fa29b2b4c6cb1e',
}
TARGETS = {
    'cachetools': {'repo': 'tkem/cachetools', 'pr': 441,
        'base': 'f4f288579dc3c8f82f62d0eaca7774303d9d3768',
        'head': '2417c0d63b286772169c0eab4ccf141213e1ca45', 'role': 'development'},
    'boltons': {'repo': 'mahmoud/boltons', 'pr': 474,
        'base': '967864f89791509f9eb36b22b4579d36b72a6df2',
        'head': 'adce5659b0b4a23ad5839d5aa2c88063b5b6f76b', 'role': 'transfer'},
}
SOURCE = {'repository': 'heathsanchez/test', 'commit': SOURCE_COMMIT,
          'path': SOURCE_ROOT, 'files': SOURCE_FILES}
AUTHORITY = {'principal': 'independent user research mission',
             'allowed_effects': 'pinned local research worktrees and native tests',
             'external_effects': 'NONE', 'reference_monitor': 'UNKNOWN_NONBYPASSABILITY'}
PROTOCOL = 'UDM_ORIGINAL_NATIVE_CONSTRUCTOR_INTEGRATION_V1'
FRONTIER_CONTRACT = {'input_type': 'NativeConstructorProfile',
    'output_type': 'NativeBooleanPass',
    'authority_snapshot': 'udm-native-constructor-8befdf9d',
    'verifier_id': 'original-native-obligation-compiler-independent-v1'}
FRONTIER_PROFILES = {name: [name+':protected-observer', name+':inherited-suite'] for name in TARGETS}


def _git(root, *args):
    return subprocess.check_output(['git', '--no-replace-objects', '-C', str(root), *args], stderr=subprocess.PIPE)


def _purge_bytecode(root):
    for path in root.rglob('__pycache__'):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
    for path in root.rglob('*.pyc'):
        if path.is_file():
            path.unlink()


def _load_sources(folder):
    folder = Path(folder)
    for name, expected in SOURCE_FILES.items():
        if digest((folder/name).read_bytes()) != expected:
            raise ValueError('original constructor source changed: '+name)
    modules = []
    for name in ('observer_genesis', 'repair_compiler'):
        path = folder/(name+'.py')
        module = ModuleType(name)
        module.__file__ = str(path)
        module.__package__ = ''
        sys.modules[name] = module
        # Read authenticated bytes directly: -B alone still permits old pyc reads.
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        modules.append(module)
    return modules


def _run_json(args, timeout=240, interpreter=None):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_NO_REPLACE_OBJECTS='1')
    process = subprocess.run([str(interpreter or sys.executable), '-I', '-B', str(Path(__file__).resolve()), *args],
        text=True, capture_output=True, env=env, timeout=timeout, check=True)
    return json.loads(process.stdout)


def _source_worker(args):
    obs, repair = _load_sources(args['sources'])
    target = TARGETS[args['target']]
    folder = Path(args['worlds'])/args['target']
    trees = {key: folder/key for key in ('base', 'head')}
    if args['action'] == 'prepare':
        obs.make_worktrees(folder, target)
        return {'status': 'PREPARED'}
    if args['action'] == 'discover':
        return {'candidates': obs.discover_methods(folder/'original', trees, target)}
    if args['action'] == 'synthesize':
        source = (trees['base']/args['subject']['file']).read_text()
        candidate, receipt = repair.synthesize(source, args['subject'])
        return {'source': candidate, 'generator_receipt': receipt}
    if args['action'] == 'suite':
        tests = repair.original_test_files(folder/'original', target)
        result = obs.pytest_baseline(trees['base'], target, tests)
        matches = re.findall(r'(\d+)\s+passed\b', result.get('stdout_tail', ''))
        result['count_passed'] = int(matches[-1]) if matches else 0
        if result['status']=='PASS' and result['count_passed']<1:
            result['status']='UNKNOWN_NO_TEST_EXECUTION'
        return {'suite': result, 'test_files': tests}
    raise ValueError('unknown original constructor phase')


def _probe_worker(args):
    obs, _ = _load_sources(args['sources'])
    root = Path(args['tree']).resolve()
    output = io.StringIO()
    with redirect_stdout(output):
        obs.worker([str(root), canonical(dict(args['subject'], sha=args['sha']))])
    native = json.loads(output.getvalue())
    manifest = []
    for module in tuple(sys.modules.values()):
        location = getattr(module, '__file__', None)
        if not location:
            continue
        path = Path(location).resolve()
        if path.is_relative_to(root) and path.is_file():
            manifest.append({'path': str(path.relative_to(root)), 'sha256': digest(path.read_bytes())})
    manifest.sort(key=lambda x: x['path'])
    expected = root/args['subject']['file']
    if not any(x['path'] == args['subject']['file'] for x in manifest):
        raise ValueError('native observer did not import discovered source')
    if native.get('source_file_sha256') != digest(expected.read_bytes()):
        raise ValueError('native observer source receipt mismatch')
    return {'native': native, 'import_manifest': manifest,
            'original_observer_sha256': SOURCE_FILES['observer_genesis.py'],
            'interpreter': sys.executable, 'bytecode_disabled': sys.dont_write_bytecode}


class NativeConstructorRuntime:
    """Source-bound local adapter; the existing Machine owns all causal state."""
    def __init__(self, machine, source_repo, worlds, output, *, native_python=None):
        self.machine = machine
        self.native_python = Path(native_python or sys.executable).absolute()
        self.source_repo = Path(source_repo).resolve()
        self.worlds = Path(worlds).absolute()
        self.output = Path(output).absolute()
        if self.worlds.resolve() != self.worlds or self.output.resolve() != self.output:
            raise ValueError('native paths must be canonical')
        if (self.output == self.worlds or self.output.is_relative_to(self.worlds)
                or self.worlds.is_relative_to(self.output)):
            raise ValueError('native worlds and output must not overlap')
        self.output.mkdir(parents=True, exist_ok=True)
        self.sources = self.output/'original-source'
        self.sources.mkdir(exist_ok=True)
        for name, expected in SOURCE_FILES.items():
            raw = _git(self.source_repo, 'show', f'{SOURCE_COMMIT}:{SOURCE_ROOT}/{name}')
            if digest(raw) != expected:
                raise ValueError('constructor source pin mismatch')
            path = self.sources/name
            if path.exists() and path.read_bytes() != raw:
                raise ValueError('materialized constructor source changed')
            path.write_bytes(raw)
        self.authority = self._record_once('execution_authority_ceiling', AUTHORITY)
        self.source = self._record_once('source_constructor',
            {'family': 'original-native-obligation-compiler', 'source': SOURCE,
             'constructor_status': 'SUPPLIED_HUMAN_AUTHORED_GRAMMAR'}, (self.authority,))
        machine.flush()

    def _record_once(self, kind, payload, premises=()):
        for node in self.machine.log:
            if node.kind == kind and node.payload == payload and tuple(node.premises) == tuple(premises):
                return node.id
        return self.machine.append(kind, payload, premises)

    def _live(self, *node_ids):
        live = self.machine.mt.live_ids(self.machine.log)
        flash = self.machine.flash_live_ids()
        if any(node not in live or node not in flash for node in node_ids):
            raise PermissionError('native constructor causal authority withdrawn')

    def _scope(self, name):
        if name not in TARGETS:
            raise ValueError('UNKNOWN_SCOPE: no original native verifier bridge')
        for root in (self.worlds, self.output, self.sources):
            if not root.is_dir() or root.resolve() != root:
                raise PermissionError('native scope path redirected or missing')
        self._live(self.authority, self.source)
        _load_sources(self.sources)  # Pin source before every original invocation.
        folder = self.worlds/name
        for key in ('original', 'base', 'head'):
            path = folder/key
            if not path.is_dir() or path.resolve() != path:
                raise PermissionError('native checkout scope redirected or missing')
            if key != 'original':
                if _git(path, 'rev-parse', 'HEAD').decode().strip() != TARGETS[name][key]:
                    raise ValueError('native world source pin mismatch')
                if _git(path, 'diff', '--name-only', 'HEAD').strip():
                    raise ValueError('native world source has unqualified edits')
                for options in (('--others','--exclude-standard'),
                                ('--others','--ignored','--exclude-standard')):
                    extras=_git(path,'ls-files',*options,'-z').decode().split('\0')
                    if any(Path(extra).suffix.lower() in ('.py','.pyc','.pyo','.so','.pyd','.pth')
                           for extra in extras if extra):
                        raise ValueError('untracked or ignored Python import interference')

    def _call(self, name, action, **extra):
        args = {'sources': str(self.sources), 'worlds': str(self.worlds),
                'target': name, 'action': action, **extra}
        return _run_json(['_source', canonical(args)], timeout=360 if action=='prepare' else 200,
                         interpreter=self.native_python)

    def prepare(self):
        self._live(self.authority, self.source)
        for root in (self.worlds,self.output,self.sources):
            if root.resolve()!=root or (root.exists() and not root.is_dir()):
                raise PermissionError('native preparation path redirected or invalid')
        _load_sources(self.sources)
        self.worlds.mkdir(parents=True, exist_ok=True)
        for name in TARGETS:
            if not (self.worlds/name).exists():
                self._call(name, 'prepare')
            self._scope(name)
        return {'status': 'PREPARED', 'worlds': str(self.worlds), 'pins': TARGETS}

    def _probe(self, name, subject, key):
        root = self.worlds/name/key
        _purge_bytecode(root)
        before = digest((root/subject['file']).read_bytes())
        try:
            result = _run_json(['_probe', canonical({'sources': str(self.sources),
                'tree': str(root), 'subject': subject, 'sha': TARGETS[name][key]})], timeout=60,
                interpreter=self.native_python)
        finally:
            _purge_bytecode(root)
        if digest((root/subject['file']).read_bytes()) != before:
            raise ValueError('native observer altered source')
        if result['native'].get('checkout_sha') != TARGETS[name][key]:
            raise ValueError('native verifier source identity mismatch')
        if not result['bytecode_disabled'] or not result['import_manifest']:
            raise ValueError('native observer import authority missing')
        for imported in result['import_manifest']:
            relative=imported['path']
            if relative==subject['file']:
                expected_hash=before
            else:
                try:
                    expected_hash=digest(_git(root,'show',f"{TARGETS[name][key]}:{relative}"))
                except subprocess.CalledProcessError as error:
                    raise ValueError('native observer imported untracked source') from error
            if imported['sha256']!=expected_hash:
                raise ValueError('native imported dependency differs from original tracked tree')
        return result

    def observe(self, name):
        self._scope(name)
        started = time.perf_counter()
        discovery = self._call(name, 'discover')
        warranted = []
        observations = []
        for subject in discovery['candidates']:
            if 'kind' not in subject:
                continue
            old = self._probe(name, subject, 'base')
            author = self._probe(name, subject, 'head')
            row = {'subject': subject, 'base': old, 'author_head': author}
            observations.append(row)
            if old['native']['status'] == 'FAIL' and author['native']['status'] == 'PASS':
                warranted.append(row)
        status = ('WARRANTED_BOUNDED_NATIVE_RESIDUAL' if len(warranted)==1
                  else 'UNKNOWN_CHOICE' if len(warranted)>1 else 'UNKNOWN_OBSERVATION')
        report = {'protocol': PROTOCOL, 'target': name, 'source': SOURCE,
                  'target_pins': TARGETS[name], 'status': status,
                  'candidates': discovery['candidates'], 'observations': observations,
                  'subject': warranted[0]['subject'] if len(warranted)==1 else None,
                  'residual': warranted[0]['base']['native']['observation'] if len(warranted)==1 else None,
                  'new_observation_language': False,
                  'grammar': 'original supplied stateful observation templates',
                  'seconds': time.perf_counter()-started}
        self._scope(name)
        node = self.machine.append('native_observation', {'report': self.machine.put(report),
            'target': name, 'status': status}, (self.source, self.authority))
        self.machine.flush()
        self.machine.costs.append({'phase': 'native_constructor_observation', 'seconds': report['seconds']})
        return dict(report, observation_id=node)

    def _verify(self, name, program):
        self._scope(name)
        subject = program['subject']
        if subject not in self._call(name, 'discover')['candidates']:
            raise ValueError('constructor subject outside original source discovery')
        sourcepath = self.worlds/name/'base'/subject['file']
        original = sourcepath.read_bytes()
        if digest(original) != program['original_source_sha256']:
            raise ValueError('constructor original source binding changed')
        proposed = program['source'].encode()
        if digest(proposed) != program['source_sha256'] or proposed == original:
            raise ValueError('altered or sham constructor output')
        regenerated = self._call(name, 'synthesize', subject=subject)
        if regenerated != {'source': program['source'], 'generator_receipt': program['generator_receipt']}:
            raise ValueError('output differs from original source-native constructor')
        started = time.perf_counter()
        old = self._probe(name, subject, 'base')
        author = self._probe(name, subject, 'head')
        baseline = self._call(name, 'suite')
        try:
            sourcepath.write_bytes(proposed)
            patched = self._probe(name, subject, 'base')
            suite = self._call(name, 'suite')
            unchanged = sourcepath.read_bytes() == proposed
        finally:
            sourcepath.write_bytes(original)
            _purge_bytecode(self.worlds/name/'base')
        removed = self._probe(name, subject, 'base')
        self._scope(name)
        gates = {'native_original_fails': old['native']['status']=='FAIL',
                 'author_head_passes': author['native']['status']=='PASS',
                 'native_candidate_passes': patched['native']['status']=='PASS',
                 'physical_removal_fails': removed['native']['status']=='FAIL',
                 'original_baseline_passes': baseline['suite']['status']=='PASS',
                 'original_suite_passes': suite['suite']['status']=='PASS',
                 'candidate_source_unchanged': unchanged,
                 'original_bytes_restored': sourcepath.read_bytes()==original}
        result = {'protocol': PROTOCOL, 'target': name, 'target_pins': TARGETS[name],
            'source': SOURCE, 'program_sha256': digest(canonical(program).encode()),
            'verifier_sha256': digest(Path(__file__).read_bytes()), 'native_python': str(self.native_python),
            'gates': gates,
            'status': 'WARRANTED_BOUNDED_NATIVE_CONSTRUCTOR_INSTANCE' if all(gates.values()) else 'REJECTED_OR_UNKNOWN',
            'native': patched['native'], 'suite': suite['suite'], 'baseline_suite': baseline,
            'native_original': old, 'native_author_head': author, 'native_candidate': patched,
            'native_removed': removed, 'test_files': suite['test_files'],
            'seconds': time.perf_counter()-started,
            'not_established': ['new constructor grammar', 'blind unfamiliar-source discovery',
                                'general repair correctness', 'external permission']}
        self.machine.costs.append({'phase': 'native_constructor_verification', 'seconds': result['seconds']})
        folder = self.output/'receipts'; folder.mkdir(exist_ok=True)
        (folder/(digest(canonical(result).encode())+'.json')).write_text(canonical(result)+'\n')
        if not all(gates.values()):
            self.machine.append('native_rejection', {'receipt': self.machine.put(result)}, (self.source,))
            self.machine.flush()
            raise ValueError('independent native constructor verification rejected')
        return result

    def acquire(self, name, supersedes=None):
        # Activation and construction are different transitions. An adequate
        # retained executable is reused before another constructor invocation.
        if supersedes is None:
            started = time.perf_counter()
            self._scope(name)
            expected_scope = {'target': name, 'target_pins': TARGETS[name],
                'authority_ceiling': AUTHORITY, 'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
                'frontier_contract': FRONTIER_CONTRACT, 'frontier_profiles': FRONTIER_PROFILES[name]}
            live = set(self.machine.mt.live_ids(self.machine.log)) & self.machine.flash_live_ids()
            candidates = []
            for node in self.machine.log:
                if (node.kind=='executable_capability' and node.id in live
                        and node.payload.get('operation')=='native.source_patch'
                        and node.payload.get('source')==SOURCE
                        and node.payload.get('scope')==expected_scope):
                    self._validated(node.id)
                    candidates.append(node.id)
            candidates = sorted(set(candidates))
            if len(candidates)>1:
                self.machine.append('developmental_choice', {'family': 'original-native-obligation-compiler',
                    'target': name, 'status': 'UNKNOWN_CHOICE', 'candidates': candidates,
                    'reason': 'independent future consequence has not selected among lawful retained capabilities'},
                    (self.source, self.authority, *candidates))
                self.machine.flush()
                raise ValueError('UNKNOWN_CHOICE: multiple warranted existing native capabilities')
            if candidates:
                capability_id = candidates[0]
                self._live(self.authority, self.source, capability_id)
                self.machine.append('capability_activation', {'family': 'original-native-obligation-compiler',
                    'target': name, 'capability_id': capability_id, 'transition': 'ACTIVATION',
                    'existing_executable_reused': True, 'constructor_invocations': 0},
                    (capability_id, self.source, self.authority))
                self.machine.flush()
                self.machine.costs.append({'phase': 'native_constructor_existing_activation',
                    'seconds': time.perf_counter()-started})
                return capability_id
        observation = self.observe(name)
        if observation['status'] != 'WARRANTED_BOUNDED_NATIVE_RESIDUAL':
            raise ValueError(observation['status'])
        subject = observation['subject']
        started = time.perf_counter()
        candidate = self._call(name, 'synthesize', subject=subject)
        self.machine.costs.append({'phase': 'native_constructor_instance_construction',
            'seconds': time.perf_counter()-started})
        original = (self.worlds/name/'base'/subject['file']).read_bytes()
        program = {'target': name, 'subject': subject, **candidate,
                   'source_sha256': digest(candidate['source'].encode()),
                   'original_source_sha256': digest(original)}
        receipt = self._verify(name, program)
        self._scope(name)
        generation = 1+sum(n.kind=='executable_capability' and n.payload.get('operation')=='native.source_patch'
            and n.payload.get('scope',{}).get('target')==name for n in self.machine.log)
        support = self.machine.append('source_support', {'family': 'original-native-obligation-compiler',
            'target': name, 'program': self.machine.put(program), 'generation': generation,
            'supersedes': supersedes}, (self.source, observation['observation_id']))
        verified = self.machine.append('native_constructor_verification',
            {'receipt': self.machine.put(receipt), 'program': self.machine.put(program)}, (support,))
        cap = Capability('native.source_patch', SOURCE,
            {'target': name, 'target_pins': TARGETS[name], 'authority_ceiling': AUTHORITY,
             'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
             'frontier_contract': FRONTIER_CONTRACT, 'frontier_profiles': FRONTIER_PROFILES[name]},
            self.machine.put(observation), self.machine.put(program), generation,
            (support, observation['observation_id']), (verified,), 'CAPABILITY_LANGUAGE_EXTENSION', supersedes)
        node = self.machine.append('executable_capability', asdict(cap), (support, verified, observation['observation_id']))
        self.machine.flush()
        return node

    def _validated(self, capability_id):
        self._live(self.authority, self.source, capability_id)
        cap = self.machine.descriptor(capability_id)
        name = cap.scope.get('target')
        self._scope(name)
        expected_scope = {'target': name, 'target_pins': TARGETS[name], 'authority_ceiling': AUTHORITY,
                          'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
                          'frontier_contract': FRONTIER_CONTRACT, 'frontier_profiles': FRONTIER_PROFILES[name]}
        if cap.operation!='native.source_patch' or cap.source!=SOURCE or cap.scope!=expected_scope:
            raise ValueError('wrong constructor capability source, scope or executable class')
        if len(cap.dependencies)!=2 or len(cap.evidence)!=1 or cap.transition!='CAPABILITY_LANGUAGE_EXTENSION':
            raise ValueError('incorrect constructor dependencies')
        self._live(*cap.dependencies, *cap.evidence)
        nodes = {node.id: node for node in self.machine.log}
        support, observation = (nodes[x] for x in cap.dependencies)
        verification = nodes[cap.evidence[0]]
        program, receipt = self.machine.get(cap.program), self.machine.get(verification.payload['receipt'])
        if (support.kind!='source_support' or support.payload.get('program')!=cap.program
                or support.payload.get('target')!=name or support.payload.get('generation')!=cap.generation
                or support.payload.get('supersedes')!=cap.supersedes
                or tuple(support.premises)!=(self.source, observation.id)
                or observation.kind!='native_observation' or observation.payload.get('target')!=name
                or tuple(observation.premises)!=(self.source, self.authority)
                or verification.kind!='native_constructor_verification'
                or tuple(verification.premises)!=(support.id,)
                or verification.payload.get('program')!=cap.program
                or tuple(nodes[capability_id].premises)!=(support.id, verification.id, observation.id)):
            raise ValueError('constructor evidence lineage differs from descriptor')
        persisted_observation = self.machine.get(cap.observation)
        if (persisted_observation.get('observation_id')!=observation.id
                or persisted_observation.get('subject')!=program.get('subject')
                or persisted_observation.get('status')!='WARRANTED_BOUNDED_NATIVE_RESIDUAL'
                or program.get('target')!=name
                or receipt.get('program_sha256')!=digest(canonical(program).encode())
                or receipt.get('source')!=SOURCE or receipt.get('target_pins')!=TARGETS[name]
                or receipt.get('target')!=name or receipt.get('protocol')!=PROTOCOL
                or receipt.get('status')!='WARRANTED_BOUNDED_NATIVE_CONSTRUCTOR_INSTANCE'
                or receipt.get('verifier_sha256')!=digest(Path(__file__).read_bytes())
                or receipt.get('native_python')!=str(self.native_python)
                or set(receipt.get('gates',{}))!={'native_original_fails','author_head_passes',
                    'native_candidate_passes','physical_removal_fails','original_baseline_passes',
                    'original_suite_passes','candidate_source_unchanged','original_bytes_restored'}
                or not all(v is True for v in receipt['gates'].values())
                or receipt.get('native',{}).get('status')!='PASS'
                or receipt.get('suite',{}).get('status')!='PASS'
                or receipt['suite'].get('count_passed',0)<1
                or program.get('source_sha256')!=digest(program.get('source','').encode())):
            raise ValueError('constructor receipt does not bind native executable output')
        if program['subject'] not in self._call(name,'discover')['candidates']:
            raise ValueError('retained constructor subject differs from pinned source discovery')
        for key, world, expected_hash, status in (
                ('native_original','base',program['original_source_sha256'],'FAIL'),
                ('native_author_head','head',program['subject']['source_sha256'],'PASS'),
                ('native_candidate','base',program['source_sha256'],'PASS'),
                ('native_removed','base',program['original_source_sha256'],'FAIL')):
            probe=receipt.get(key,{})
            native=probe.get('native',{})
            if (native.get('status')!=status or native.get('checkout_sha')!=TARGETS[name][world]
                    or native.get('source_file_sha256')!=expected_hash
                    or native.get('method')!=program['subject']['method']
                    or native.get('method_kind')!=program['subject']['kind']
                    or probe.get('original_observer_sha256')!=SOURCE_FILES['observer_genesis.py']
                    or probe.get('bytecode_disabled') is not True
                    or not any(item.get('path')==program['subject']['file'] and item.get('sha256')==expected_hash
                        for item in probe.get('import_manifest',[]))):
                raise ValueError('retained native probe source or observation channel changed')
        if receipt['native']!=receipt['native_candidate']['native']:
            raise ValueError('retained native consequence differs from independent candidate probe')
        return cap, program, receipt

    def projection_payload(self, capability_id):
        cap, _, _ = self._validated(capability_id)
        return {'contract': dict(FRONTIER_CONTRACT),
                'profiles': list(FRONTIER_PROFILES[cap.scope['target']]),
                'verification_id': cap.evidence[0]}

    def execute(self, capability_id):
        cap, program, _ = self._validated(capability_id)
        receipt = self._verify(cap.scope['target'], program)
        self._validated(capability_id)
        consequence = self.machine.append('verified_consequence',
            {'family': 'original-native-constructor', 'target': cap.scope['target'],
             'receipt': self.machine.put(receipt), 'program': cap.program}, (capability_id,))
        self.machine.flush()
        return receipt, consequence

    def withdraw(self, capability_id, reason='exact native constructor ancestor withdrawal'):
        self._validated(capability_id)
        return self.machine.withdraw(capability_id, reason)

    def restore(self, capability_id):
        cap = self.machine.descriptor(capability_id)
        if cap.operation!='native.source_patch' or cap.source!=SOURCE:
            raise ValueError('wrong restoration capability')
        if capability_id in self.machine.mt.live_ids(self.machine.log):
            raise ValueError('restoration requires revoked prior generation')
        new_id = self.acquire(cap.scope['target'], supersedes=capability_id)
        if self.machine.get(self.machine.descriptor(new_id).program) != self.machine.get(cap.program):
            raise ValueError('restored constructor program differs from retained executable')
        return new_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('_source', '_probe'))
    parser.add_argument('input')
    args = parser.parse_args()
    raw = json.loads(args.input)
    result = _source_worker(raw) if args.action=='_source' else _probe_worker(raw)
    print(canonical(result))


if __name__ == '__main__':
    main()
