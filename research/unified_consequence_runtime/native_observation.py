"""Original FLASH V11 observation selection over source-pinned native TOML.

This is executable integration of exposed historical source families, not a new
defect discovery. The operation and observation vocabularies remain supplied.
"""
from __future__ import annotations

import ast
from dataclasses import asdict
import json
from pathlib import Path
from threading import RLock
import subprocess
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace
import uuid

from .developmental_machine import Capability, canonical, digest

SOURCES = {
    'producer': {'commit':'bda00d75ac186b02b44eac93d0e64f67d19c5b9a',
        'path':'research/real_native_observation_basis_20261015/native_basis.py',
        'sha256':'188fa09e7cbb9fa347bb1b3b7b2d283d518c294267c6aa0ba6a8575ebd371e1e'},
    'solver': {'commit':'bda00d75ac186b02b44eac93d0e64f67d19c5b9a',
        'path':'research/flash_genesis_v11/learned_repair.py',
        'sha256':'1200898dfafa0c431c49f4eeab23f500e8dca92d0fdebfa72d6aca2ec9861506'},
    'verifier': {'commit':'32a31e261fdef54fce3cdef902077100cf7c7094',
        'path':'research/real_native_observation_basis_20261015/audit_independent.py',
        'sha256':'c3fbfffe3598763d76efb983668faa6ba7881a1d6069ba1ecd6635820d7dc344'},
}
NATIVE_PINS = {
    'A': {'old':'7ab7469addd60e03ca3bfbb1287642e8d771e1c0', 'head':'dcdfda3f825189c7f31048b6598142a944151073'},
    'B': {'old':'858186a3edb4cad6d66281ee7ad5fb07fe820406', 'head':'5d0b1825134a05da4e49654baa4717094a9f0896'},
    'C': {'old':'4b38becd75405e0f38ef3e47e9839eb407591c8a', 'head':'d17910d46bcc0f3d5b9c1de607a41836e1c85ce2'},
}
OPERATION = 'flash.native_observation'
CONTRACT = {'input_type':'NativeTomlProgramFamily', 'output_type':'NativeCoherenceClassification',
    'authority_snapshot':'udm-native-observation-v1', 'verifier_id':'original-independent-tomllib-audit-v1'}
_SOURCE_LOAD_LOCK = RLock()


def source_bytes(repo, key):
    pin = SOURCES[key]
    try:
        raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo),
            'show', pin['commit']+':'+pin['path']], stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError('missing original native observation source: '+key) from error
    if digest(raw) != pin['sha256']:
        raise ValueError('original native observation source hash changed: '+key)
    return raw


def load_sources(repo, destination):
    """Materialize original authenticated bytes; no scientific algorithm edits."""
    destination = Path(destination)
    for key, pin in SOURCES.items():
        raw = source_bytes(repo, key)
        path = destination/pin['path']
        if path.exists() and path.read_bytes() != raw:
            raise ValueError('materialized original observation source changed')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    path = destination/SOURCES['producer']['path']
    producer = ModuleType('_udm_original_native_basis_'+uuid.uuid4().hex)
    producer.__file__ = str(path)
    # A valid cached pyc can shadow hash-checked .py even with Python -B.
    # Compile the authenticated bytes directly rather than consult that cache.
    exec(compile(source_bytes(repo, 'producer'), str(path), 'exec'), producer.__dict__)
    original_basis_solver = producer.basis_solver
    def checked_basis_solver():
        # The unchanged original uses SourceFileLoader for its retained solver.
        # Give that loader a fresh isolated bytecode namespace for every call.
        with _SOURCE_LOAD_LOCK, tempfile.TemporaryDirectory(prefix='udm-original-solver-bytecode-') as cache:
            if digest(producer.SOURCE_SOLVER.read_bytes()) != SOURCES['solver']['sha256']:
                raise ValueError('original retained solver source changed')
            old_prefix, old_write = sys.pycache_prefix, sys.dont_write_bytecode
            try:
                sys.pycache_prefix, sys.dont_write_bytecode = cache, True
                return original_basis_solver()
            finally:
                sys.pycache_prefix, sys.dont_write_bytecode = old_prefix, old_write
    producer.basis_solver = checked_basis_solver
    # The receiver's main() reads files relative to argv. Load its unchanged
    # semantic definitions without running that historical audit entrypoint.
    tree = ast.parse(source_bytes(repo, 'verifier'))
    names = {'OBS', 'IDENTITY', 'COUNT', 'FULL_CASES'}
    body = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))
        or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)]
    namespace = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), '<original-independent-native-audit>', 'exec'), namespace)
    return SimpleNamespace(producer=producer, verifier=SimpleNamespace(**namespace), path=path)


def checked_world(root, sha):
    """Bind actual working bytes, including executable import files, to the pin."""
    root = Path(root)
    if not root.is_dir() or root.resolve(strict=True) != root.absolute():
        raise PermissionError('native observation world missing or redirected')
    head = subprocess.check_output(['git', '--no-replace-objects', '-C', str(root),
        'rev-parse', 'HEAD'], text=True).strip()
    if head != sha:
        raise ValueError('wrong native observation source revision')
    entries = subprocess.check_output(['git', '--no-replace-objects', '-C', str(root),
        'ls-tree', '-rz', sha]).split(b'\0')
    manifest = {}
    for item in entries:
        if not item:
            continue
        meta, name = item.split(b'\t', 1)
        mode, kind, blob = meta.decode().split()
        name = name.decode()
        path = root/name
        if mode == '160000' and kind == 'commit':
            # Original tomlkit carries an unused TOML test-suite submodule.
            # Native array execution does not initialize or import that suite.
            if path.is_symlink() or not path.is_dir() or any(path.iterdir()):
                raise ValueError('unqualified native submodule contents')
            manifest[name] = 'uninitialized-gitlink:'+blob
            continue
        if mode not in ('100644', '100755') or kind != 'blob' or path.is_symlink() or not path.is_file():
            raise ValueError('native source mode or file missing')
        expected = subprocess.check_output(['git', '--no-replace-objects', '-C', str(root), 'cat-file', 'blob', blob])
        if path.read_bytes() != expected:
            raise ValueError('native executable source differs from pin: '+name)
        manifest[name] = digest(expected)
    # Ignore rules are not evidence authority: ignored extension modules can
    # shadow tracked Python modules. Reject all untracked working files.
    unexpected = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--others'], text=True)
    if unexpected.strip():
        raise ValueError('untracked native source can affect imports')
    return digest(canonical(manifest).encode())


def validate_rows(native, observed, family, version):
    """Original independent semantics, exact native source and complete case grammar."""
    try:
        if (family not in NATIVE_PINS or version not in ('old', 'head') or
                observed['family'] != family or observed['source_sha'] != NATIVE_PINS[family][version] or
                observed['repo'] != 'python-poetry/tomlkit' or
                observed['source_package'] != 'tomlkit/__init__.py'):
            raise ValueError('wrong native observation source or scope')
        cases = native.producer.cases(family)
        if observed['case_grammar_sha256'] != native.producer.hashbytes(native.producer.dump(cases).encode()):
            raise ValueError('wrong native experiment grammar')
        if observed['native_tests'] != len(cases) or len(observed['rows']) != len(cases):
            raise ValueError('incomplete native experiment family')
        for row, case in zip(observed['rows'], cases):
            if row['id'] != case['id'] or row['task'] != case or set(row['features']) != set(native.verifier.OBS):
                raise ValueError('wrong native observation channel or task')
            if native.verifier.checkrow(row) != row['label']:
                raise ValueError('forged native observation verdict')
    except (KeyError, TypeError, AssertionError) as error:
        raise ValueError('invalid independent native observations') from error
    return digest(canonical(observed).encode())


class NativeObservationRuntime:
    def __init__(self, machine, source_repo:Path, worlds:Path, output:Path):
        self.machine = machine
        self.source_repo, self.worlds, self.output = Path(source_repo).resolve(), Path(worlds).absolute(), Path(output).resolve()
        if self.output == self.worlds or self.worlds in self.output.parents or self.output in self.worlds.parents:
            raise ValueError('native output and native worlds must be disjoint')
        self.output.mkdir(parents=True, exist_ok=True)
        self.native = load_sources(self.source_repo, self.output/'original-source')
        self.authority_ceiling = {'principal':'independent user research mission',
            'allowed_effects':'pinned local native research worktrees and tests', 'external_effects':'NONE',
            'reference_monitor':'UNKNOWN_NONBYPASSABILITY'}
        self.authority = machine.append('execution_authority_ceiling', self.authority_ceiling)
        self.source = machine.append('native_observation_constructor', {'sources':SOURCES,
            'native_pins':NATIVE_PINS, 'contract':CONTRACT,
            'constructor_status':'SUPPLIED_ORIGINAL_FINITE_OBSERVATION_SELECTION'}, (self.authority,))
        machine.flush()

    def _check_sources(self):
        for key in SOURCES:
            source_bytes(self.source_repo, key)
        for pin in SOURCES.values():
            if digest((self.output/'original-source'/pin['path']).read_bytes()) != pin['sha256']:
                raise ValueError('materialized source changed after independent admission')

    def _live(self, node):
        if node not in self.machine.mt.live_ids(self.machine.log) or node not in self.machine.flash_live_ids():
            raise PermissionError('native observation causal support withdrawn')

    def _guards(self):
        self._live(self.authority)
        self._live(self.source)
        self._check_sources()

    def _native(self, family, version, *, independent=False):
        self._guards()
        if family not in NATIVE_PINS or version not in ('old', 'head'):
            raise ValueError('native observation family outside frozen scope')
        original = self.worlds/(family+version)
        sha = NATIVE_PINS[family][version]
        manifest = checked_world(original, sha)
        name = uuid.uuid4().hex
        out = self.output/(name+'.json')
        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix='udm-independent-observation-') as directory:
            root = original
            if independent:
                root = Path(directory)/'source'
                subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', '--no-hardlinks',
                    str(original), str(root)], check=True, capture_output=True)
                subprocess.run(['git', '--no-replace-objects', '-C', str(root), 'checkout', '--quiet', '--detach', sha],
                    check=True, capture_output=True)
                if checked_world(root, sha) != manifest:
                    raise ValueError('independent clean native source differs')
            call = subprocess.run([sys.executable, '-I', '-B', '-X', 'pycache_prefix='+str(Path(directory)/'bytecode'),
                str(self.native.path), 'child',
                str(root), sha, family, str(out)], cwd=directory, capture_output=True, text=True, timeout=60)
            (self.output/(name+'.stdout')).write_text(call.stdout)
            (self.output/(name+'.stderr')).write_text(call.stderr)
            if call.returncode:
                raise ValueError('native observation subprocess failed: '+call.stderr[-500:])
        self._guards()
        if checked_world(original, sha) != manifest:
            raise ValueError('native source changed during observation')
        result = json.loads(out.read_text())
        validate_rows(self.native, result, family, version)
        self.machine.costs.append({'phase':'native_observation_independent_execution' if independent else 'native_observation_execution',
            'family':family, 'version':version, 'seconds':time.perf_counter()-start,
            'native_programs':result['native_tests'], 'source_manifest':manifest})
        return result

    def observe(self, family):
        self._guards()
        if family not in NATIVE_PINS:
            raise ValueError('native observation family outside frozen scope')
        return {version:self._native(family, version) for version in ('old', 'head')}

    def _verify(self, program, observations, family):
        """Fresh independent native execution plus original receiver semantics."""
        self._guards()
        for version in ('old', 'head'):
            validate_rows(self.native, observations[version], family, version)
            fresh = self._native(family, version, independent=True)
            if fresh != observations[version]:
                raise ValueError('producer observations differ from independent native execution')
        if family == 'A':
            rows = observations['old']['rows'] + observations['head']['rows']
            try:
                eligible, minimum, minimizers = self.native.verifier.source_optimum(rows)
            except (AssertionError, ValueError) as error:
                raise ValueError('UNKNOWN_CHOICE: original finite observation contract not independently closed') from error
            if len(minimizers) != 1 or tuple(program['selected_channels']) != minimizers[0]:
                raise ValueError('UNKNOWN_CHOICE: preserve unresolved observation frontier')
            if (program['source_A'] != NATIVE_PINS['A'] or
                    program['original_v11_solver_blob'] != self.native.producer.SOURCE_BLOB or
                    program['candidate_observation_masks_exhaustively_checked'] != 128 or
                    program['exact_A_observation_optimum'] != minimum):
                raise ValueError('native observation policy differs from independent minimum')
            expected = {}
            for row in rows:
                if row['label'] != 'UNKNOWN':
                    expected[self.native.producer.key(row['features'], program['selected_channels'])] = row['label']
            if expected != program['source_compiled_lookup']:
                raise ValueError('forged compiled native observation semantics')
        else:
            _, independent = self.native.verifier.evaluate(program, {family:(observations['old'], observations['head'])})
            if independent[family]['false'] or not independent[family]['detected']:
                raise ValueError('independent native future consequence rejected')
            minimizers = [tuple(program['selected_channels'])]
        return {'schema':'udm.native-observation.verification.v1', 'status':'PASS_INDEPENDENT_NATIVE_FINITE',
            'protocol':'ORIGINAL_SOURCE_NATIVE_FLASH_OBSERVATION_INTEGRATION', 'sources':SOURCES,
            'native_pins':NATIVE_PINS, 'family':family, 'program_sha256':digest(canonical(program).encode()),
            'observations_sha256':digest(canonical(observations).encode()),
            'adapter_sha256':digest(Path(__file__).read_bytes()), 'minimal_observation_frontier':minimizers,
            'native_reexecuted':True, 'independent_tomllib_reconstruction':True,
            'classification':'EXPOSED_HISTORICAL_NATIVE_INTEGRATION_REUSE',
            'verification_nonce':uuid.uuid4().hex}

    def acquire(self, *, supersedes=None):
        self._guards()
        if supersedes is None:
            # Installation is not an instruction to reconstruct an already
            # independently warranted operation. Preserve unresolved choices.
            started = time.perf_counter()
            available, rejected = [], []
            for capability_id in self.machine.active_capabilities():
                candidate = self.machine.descriptor(capability_id)
                if candidate.operation != OPERATION or candidate.scope.get('contract') != CONTRACT:
                    continue
                try:
                    self._validated(capability_id)
                except (ValueError, PermissionError, KeyError, StopIteration) as error:
                    rejected.append({'capability_id':capability_id, 'status':'UNKNOWN_EVIDENCE', 'reason':str(error)})
                else:
                    available.append(capability_id)
            if available:
                status = 'ACTIVATION' if len(available) == 1 else 'UNKNOWN_CHOICE'
                self.machine.append('native_observation_existing_method_selection',
                    {'operation':OPERATION, 'transition':status, 'contract':CONTRACT,
                     'available_capabilities':available, 'rejected_existing_methods':rejected,
                     'constructor_invoked':False, 'language_changed':False}, tuple(available))
                self.machine.flush()
                self.machine.costs.append({'phase':'native_observation_existing_method_activation',
                    'seconds':time.perf_counter()-started, 'constructor_invoked':False})
                if len(available) != 1:
                    raise ValueError('UNKNOWN_CHOICE: preserve all independently warranted observation methods')
                return available[0]
        if supersedes is not None:
            previous = self.machine.descriptor(supersedes)
            if (previous.operation != OPERATION or previous.source != {'repository':'heathsanchez/test', **SOURCES['producer']} or
                    previous.scope.get('native_pins') != NATIVE_PINS or previous.scope.get('contract') != CONTRACT or
                    supersedes in self.machine.mt.live_ids(self.machine.log)):
                raise ValueError('restoration must name an inactive same-scope original capability')
        start = time.perf_counter()
        observations = self.observe('A')
        folder = self.output/('acquire-'+uuid.uuid4().hex)
        folder.mkdir()
        paths = []
        for version in ('old', 'head'):
            path = folder/(version+'.json')
            path.write_text(canonical(observations[version]))
            paths.append(path)
        policy_path = folder/'policy.json'
        compilation_start = time.perf_counter()
        self.native.producer.acquire(*paths, policy_path)
        program = json.loads(policy_path.read_text())
        self.machine.costs.append({'phase':'native_observation_selection_and_compilation',
            'seconds':time.perf_counter()-compilation_start,
            'declared_observation_masks':program['candidate_observation_masks_exhaustively_checked'],
            'original_solver_oracle_calls':program['source_v11_oracle_calls']})
        receipt = self._verify(program, observations, 'A')
        # Freeze the A-only selected program before independently establishing
        # its two declared, already exposed native applicability scopes.
        frozen = digest(canonical(program).encode())
        receipt['scope_verifications'] = {}
        for family in ('B', 'C'):
            future = self.observe(family)
            checked = self._verify(program, future, family)
            receipt['scope_verifications'][family] = {
                'observations':self.machine.put(future), 'receipt':self.machine.put(checked)}
        if digest(canonical(program).encode()) != frozen:
            raise ValueError('native observation program changed during scope verification')
        self._guards()
        generation = 1+sum(n.kind == 'executable_capability' and n.payload['operation'] == OPERATION for n in self.machine.log)
        support = self.machine.append('source_support', {'operation':OPERATION, 'sources':SOURCES,
            'native_pins':NATIVE_PINS, 'observation':self.machine.put(observations),
            'program':self.machine.put(program), 'generation':generation, 'supersedes':supersedes}, (self.source,))
        verified = self.machine.append('native_observation_verification', {'receipt':self.machine.put(receipt),
            'program':self.machine.put(program)}, (support,))
        cap = Capability(OPERATION, {'repository':'heathsanchez/test', **SOURCES['producer']},
            {'families':['B','C'], 'native_pins':NATIVE_PINS, 'contract':CONTRACT,
             'frontier_contract':CONTRACT, 'frontier_profiles':['tomlkit:B','tomlkit:C'],
             'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY', 'authority_ceiling':self.authority_ceiling},
            self.machine.put(observations), self.machine.put(program), generation, (support,), (verified,),
            'REPRESENTATION_REFINEMENT', supersedes)
        node = self.machine.append('executable_capability', asdict(cap), (support, verified))
        self.machine.flush()
        self.machine.costs.append({'phase':'native_observation_acquisition_and_verification',
            'seconds':time.perf_counter()-start, 'inclusive_of_native_execution':True,
            'program_bytes':len(canonical(program).encode()), 'observation_bytes':len(canonical(observations).encode())})
        return node

    def _validated(self, capability_id):
        self._guards()
        self._live(capability_id)
        cap = self.machine.descriptor(capability_id)
        if (cap.operation != OPERATION or cap.source != {'repository':'heathsanchez/test', **SOURCES['producer']} or
                cap.scope != {'families':['B','C'], 'native_pins':NATIVE_PINS, 'contract':CONTRACT,
                    'frontier_contract':CONTRACT, 'frontier_profiles':['tomlkit:B','tomlkit:C'],
                    'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY', 'authority_ceiling':self.authority_ceiling} or
                len(cap.dependencies) != 1 or len(cap.evidence) != 1 or cap.transition != 'REPRESENTATION_REFINEMENT'):
            raise ValueError('wrong typed native observation capability or authority')
        nodes = {n.id:n for n in self.machine.log}
        for node in (*cap.dependencies, *cap.evidence):
            self._live(node)
        support, evidence = nodes[cap.dependencies[0]], nodes[cap.evidence[0]]
        if (support.kind != 'source_support' or tuple(support.premises) != (self.source,) or
                support.payload != {'operation':OPERATION, 'sources':SOURCES, 'native_pins':NATIVE_PINS,
                    'observation':cap.observation, 'program':cap.program, 'generation':cap.generation, 'supersedes':cap.supersedes} or
                evidence.kind != 'native_observation_verification' or tuple(evidence.premises) != (support.id,) or
                evidence.payload['program'] != cap.program or tuple(nodes[capability_id].premises) != (support.id, evidence.id)):
            raise ValueError('native observation capability differs from exact causal evidence')
        program, observations = self.machine.get(cap.program), self.machine.get(cap.observation)
        receipt = self.machine.get(evidence.payload['receipt'])
        if (receipt.get('schema') != 'udm.native-observation.verification.v1' or receipt.get('status') != 'PASS_INDEPENDENT_NATIVE_FINITE' or
                receipt.get('sources') != SOURCES or receipt.get('native_pins') != NATIVE_PINS or receipt.get('family') != 'A' or
                receipt.get('program_sha256') != cap.program or receipt.get('observations_sha256') != cap.observation or
                receipt.get('adapter_sha256') != digest(Path(__file__).read_bytes()) or
                receipt.get('native_reexecuted') is not True or receipt.get('independent_tomllib_reconstruction') is not True):
            raise ValueError('forged or stale native observation evidence binding')
        for version in ('old','head'):
            validate_rows(self.native, observations[version], 'A', version)
        _, _, minimizers = self.native.verifier.source_optimum(observations['old']['rows']+observations['head']['rows'])
        if len(minimizers) != 1 or tuple(program['selected_channels']) != minimizers[0]:
            raise ValueError('retained observation choice is ambiguous or incorrect')
        expected = {self.native.producer.key(row['features'],program['selected_channels']):row['label']
            for version in ('old','head') for row in observations[version]['rows'] if row['label'] != 'UNKNOWN'}
        if program['source_compiled_lookup'] != expected:
            raise ValueError('retained compiled observation semantics changed')
        scoped = receipt.get('scope_verifications', {})
        if set(scoped) != {'B','C'}:
            raise ValueError('native future applicability scopes not independently verified')
        for family, bound in scoped.items():
            future = self.machine.get(bound['observations'])
            checked = self.machine.get(bound['receipt'])
            for version in ('old', 'head'):
                validate_rows(self.native, future[version], family, version)
            if (checked.get('schema') != receipt['schema'] or checked.get('status') != receipt['status'] or
                    checked.get('sources') != SOURCES or checked.get('native_pins') != NATIVE_PINS or
                    checked.get('family') != family or checked.get('program_sha256') != cap.program or
                    checked.get('observations_sha256') != bound['observations'] or
                    checked.get('adapter_sha256') != receipt['adapter_sha256'] or
                    checked.get('native_reexecuted') is not True or
                    checked.get('independent_tomllib_reconstruction') is not True):
                raise ValueError('wrong native applicability evidence binding')
            _, evaluated = self.native.verifier.evaluate(program, {family:(future['old'], future['head'])})
            if evaluated[family]['false'] or not evaluated[family]['detected']:
                raise ValueError('native applicability receipt does not support executable scope')
        return cap

    def execute(self, capability_id, family):
        cap = self._validated(capability_id)
        if family not in cap.scope['families']:
            raise ValueError('native observation execution outside capability scope')
        program = self.machine.get(cap.program)
        observations = self.observe(family)
        self._validated(capability_id)
        # Invoke the original transfer implementation, including its executable
        # lookup, unsupported-signature UNKNOWN and local physical-file control.
        folder = self.output/('execute-'+uuid.uuid4().hex)
        folder.mkdir()
        policy = folder/'policy.json'
        policy.write_text(canonical(program))
        for version in ('old', 'head'):
            (folder/(version+'.json')).write_text(canonical(observations[version]))
        original_report = folder/'original-report.json'
        self.native.producer.transfer(policy, [(family, folder/'old.json', folder/'head.json')], original_report)
        transferred = json.loads(original_report.read_text())
        predictions = transferred['future'][family]['prediction']
        receipt = self._verify(program, observations, family)
        self._validated(capability_id)
        oldfail = {r['id'] for r in observations['old']['rows'] if r['label']=='FAIL'}
        repaired = oldfail & {r['id'] for r in observations['head']['rows'] if r['label']=='PASS'}
        detected = sum(p['version']=='old' and p['id'] in repaired and p['predicted']=='FAIL' for p in predictions)
        false = sum(p['predicted'] in ('PASS','FAIL') and p['predicted'] != p['actual'] for p in predictions)
        result = {'status':'PASS_BOUNDED_NATIVE_OBSERVATION', 'family':family,
            'native_repaired':len(repaired), 'detected_repaired':detected, 'false_warrants':false,
            'predictions':predictions, 'observations':self.machine.put(observations),
            'receipt':self.machine.put(receipt), 'program':cap.program,
            'baseline':'TIE_SAME_INFORMATION_EXHAUSTIVE', 'new_defect_discovery':False}
        node = self.machine.append('verified_consequence', result, (capability_id,))
        self.machine.flush()
        return result, node

    def withdraw(self, capability_id):
        self._validated(capability_id)
        return self.machine.withdraw(capability_id, 'exact native observation ancestor withdrawal')

    def restore(self, oldcap):
        previous = self.machine.descriptor(oldcap)
        if previous.operation != OPERATION or previous.source != {'repository':'heathsanchez/test', **SOURCES['producer']}:
            raise ValueError('wrong native observation capability restoration')
        if oldcap in self.machine.mt.live_ids(self.machine.log):
            raise ValueError('restoration requires an inactive previous capability')
        return self.acquire(supersedes=oldcap)

    def projection_payload(self, capability_id, families=('B','C')):
        cap = self._validated(capability_id)
        if not families or any(f not in cap.scope['families'] for f in families):
            raise ValueError('wrong native observation frontier scope')
        node = next(n for n in self.machine.log if n.id == cap.evidence[0])
        return {'contract':CONTRACT, 'profiles':['tomlkit:'+f for f in families],
            'verification_id':node.id, 'evidence_binding':digest(canonical(node.payload).encode())}
