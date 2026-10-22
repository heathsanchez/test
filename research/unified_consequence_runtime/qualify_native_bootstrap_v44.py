"""Native metadata-bootstrap qualification; never a prospective G2 result.

The driver reuses the existing source/index/runtime/archive checks and original
native verifier. Acceptance fixtures exercise infrastructure only. No unfamiliar
task is selected, no learner or comparator is invoked, and G2--G6 stay UNKNOWN.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout, redirect_stderr
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from . import qualify_experiment_interface_v43 as original

HERE, ROOT, PREFIX = original.HERE, original.ROOT, original.PREFIX
BASE = '8830a66fcb261b192d98da495b6cb91697d21f28'
RECORDS = HERE/'archaeology/native-bootstrap-v44'
CATALOG = original.CATALOG
FREEZE_SCHEMA = 'UDM_NATIVE_BOOTSTRAP_FREEZE_V44'
RESULT_SCHEMA = 'UDM_NATIVE_BOOTSTRAP_QUALIFICATION_V44'
QUALIFIED = 'QUALIFIED_BOUNDED_NATIVE_METADATA_BOOTSTRAP_ONLY'
TESTS = ('test_native_environment_v44.py', 'test_native_bootstrap_runtime_v44.py',
         'test_native_runtime_v44.py', 'test_qualify_native_frontier_v44.py',
         'test_native_frontier_helpers_v44.py', 'test_native_inventory_transport_v44.py')
BOOTSTRAP_GATE_FILES = tuple(PREFIX+name for name in (
    'native_metadata_v44.py', 'native_environment_selection_v44.py',
    'native_environment_v44.py', 'native_bootstrap_runtime_v44.py',
    'cross_frontier_v44.py', 'developmental_machine_v44.py',
    'native_runtime_v44.py', 'qualify_native_frontier_v44.py',
    'qualify_native_bootstrap_v44.py', *TESTS,
    'archaeology/native-bootstrap-v44/preimplementation/PROTOCOL.json',
    'archaeology/native-bootstrap-v44/preimplementation/FREEZE_MANIFEST.json',
    'archaeology/native-bootstrap-v44/preimplementation/test_native_metadata_v44_acceptance.py',
    'archaeology/native-bootstrap-v44/metadata-cost-preimplementation/test_metadata_attempts_v44.py',
    'archaeology/native-bootstrap-v44/metadata-review-preimplementation/test_metadata_review_v44.py',
    'archaeology/native-bootstrap-v44/metadata-review-preimplementation/test_metadata_absent_static_v44.py',
    'archaeology/native-bootstrap-v44/prospective/curate_frontier.py',
    'archaeology/native-bootstrap-v44/prospective/prepare_records.py',
    'archaeology/native-bootstrap-v44/prospective/watch_actual_agent.py',
    'archaeology/native-bootstrap-v44/prospective/training_history_projection_v44.py',
    'archaeology/native-bootstrap-v44/prospective/PRIOR_EXPOSURE.json',
    'archaeology/native-bootstrap-v44/prospective/training-history-original/training_history_projection.py',
)) + ('.github/workflows/udm-native-bootstrap-v44.yml',
      '.github/workflows/udm-prospective-native-selection-v44.yml')
canonical, sha, write, file_sha = original.canonical, original.sha, original.write, original.file_sha


def _source(repo):
    value = original._source(repo)
    before, after = original._tree(repo, BASE), value['source_tree']
    if len(before) != 2628 or any(after.get(name) != row for name, row in before.items()):
        raise ValueError('previous V43 complete source bytes/modes changed')
    if any(name not in value['files'] for name in BOOTSTRAP_GATE_FILES):
        raise ValueError('commit complete V44 installed source, acceptance and workflow before freezing')
    return dict(value, v43_preserved_files=len(before))


def _acceptance():
    root = RECORDS/'preimplementation'
    manifest = json.loads((root/'FREEZE_MANIFEST.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if sha((root/name).read_bytes()) != expected:
            raise ValueError('preimplementation V44 acceptance changed: '+name)
    protocol = json.loads((root/'PROTOCOL.json').read_text())
    if (protocol.get('baseline_commit') != BASE or len(protocol.get('cases', [])) != 28
            or not protocol.get('original_verifier_bytes_immutable')):
        raise ValueError('wrong independently frozen bootstrap acceptance')
    for name, expected in protocol['source_pins_sha256'].items():
        if sha((HERE/name).read_bytes()) != expected:
            raise ValueError('original metadata/native authority changed: '+name)
    red = json.loads((root/'PREIMPLEMENTATION_RED_RESULT.json').read_text())
    if (red.get('status') != 'RED_MISSING_V44_IMPLEMENTATION'
            or red.get('junit', {}).get('tests') != '32'
            or red.get('junit', {}).get('failures') != '32'
            or red.get('junit', {}).get('errors') != '0'
            or red.get('junit', {}).get('skipped') != '0'):
        raise ValueError('missing actual preimplementation V44 RED')
    return {'protocol_sha256': sha((root/'PROTOCOL.json').read_bytes()),
            'manifest_sha256': sha((root/'FREEZE_MANIFEST.json').read_bytes()),
            'files_sha256': manifest['files_sha256'], 'red': red}


def _control_tests():
    return [PREFIX+'archaeology/native-bootstrap-v44/preimplementation/test_native_metadata_v44_acceptance.py',
            PREFIX+'archaeology/native-bootstrap-v44/metadata-cost-preimplementation/test_metadata_attempts_v44.py',
            PREFIX+'archaeology/native-bootstrap-v44/metadata-review-preimplementation/test_metadata_review_v44.py',
            PREFIX+'archaeology/native-bootstrap-v44/metadata-review-preimplementation/test_metadata_absent_static_v44.py',
            *(PREFIX+name for name in TESTS)]


def _collect_controls(repo, out):
    import pytest
    inventory = original._PytestInventory()
    previous = Path.cwd()
    try:
        os.chdir(repo)
        with Path(out).open('w') as stream:
            with redirect_stdout(stream), redirect_stderr(stream):
                code = int(pytest.main(['-q', '-p', 'no:cacheprovider', '--import-mode=importlib',
                                       '--collect-only', *_control_tests()],
                                       plugins=[inventory]))
    finally:
        os.chdir(previous)
    if code or not inventory.collected or len(set(inventory.collected)) != len(inventory.collected):
        raise ValueError('cannot independently freeze complete V44 acceptance collection')
    return inventory.collected


def write_freeze(repo, out, runtime_paths):
    out = Path(out).absolute()
    if out.exists():
        raise ValueError('refusing to overwrite an existing V44 freeze')
    with original.index_interval(repo, out.with_name(out.name+'.INDEX')):
        value = {'schema': FREEZE_SCHEMA, **_source(repo),
                 **original._runtime_freeze(runtime_paths), 'acceptance': _acceptance(),
                 'control_collection': _collect_controls(repo, out.with_name(out.name+'.COLLECTION.log')),
                 'scope': 'NATIVE_METADATA_BOOTSTRAP_INFRASTRUCTURE_ONLY',
                 'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
        write(out, value)
        return value


def check_freeze(repo, path):
    frozen = json.loads(Path(path).read_text())
    if frozen.get('schema') != FREEZE_SCHEMA:
        raise ValueError('wrong V44 source/runtime freeze')
    source = _source(repo)
    if any(frozen.get(key) != value for key, value in source.items()) or frozen.get('acceptance') != _acceptance():
        raise ValueError('committed V44 source/acceptance changed after freeze')
    runtimes = original._runtime_freeze({name: row['interpreter'] for name, row in frozen['runtimes'].items()})
    if any(frozen.get(key) != value for key, value in runtimes.items()):
        raise ValueError('original frozen native environment changed')
    return frozen


def _git(repo, *args):
    return original._git(repo, *args).decode().strip()


def _commit(repo, message):
    _git(repo, 'add', '.')
    _git(repo, '-c', 'user.name=V44 Native Acceptance', '-c', 'user.email=v44@example.invalid',
         'commit', '-qm', message)
    return _git(repo, 'rev-parse', 'HEAD')


def _native_context(repo, base, augmented, environment, interpreter, binding):
    from . import native_execution_v43 as worker
    from . import native_source_v42 as source
    identity, _, _ = source.snapshot(repo, augmented)
    authority = worker.admission.derive_suite_contract(repo, base, augmented, binding,
                                                      repository='fixture/native-bootstrap-v44')
    policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 30, 'execution_seconds': 30,
              'pytest_version': environment['pytest_version'], 'plugins': []}
    contract = {'schema': worker.SCHEMA, 'repository': 'fixture/native-bootstrap-v44',
                'repo_path': str(repo), 'commit': augmented, **identity,
                'interpreter': str(interpreter), 'environment_sha256': worker.fingerprint(environment),
                'protocol_binding': binding, 'horizon_seconds': 30, 'generated_build': None}
    worker._context(contract, authority, policy)
    return {'contract': contract, 'authority': authority, 'policy': policy,
            'candidate': {'replacements': []}}


def _execute_native(context, out):
    from . import native_execution_v43 as worker
    out = Path(out)
    certificate = worker.collect(context['contract'], context['authority'], out/'collection',
                                 policy=context['policy'])
    receipt = worker.verify(context['contract'], context['candidate'], out/'execution',
        authority=context['authority'], admission_certificate=certificate, policy=context['policy'])
    checked = worker.validate_receipt(context['contract'], context['candidate'], context['authority'],
        certificate, receipt, policy=context['policy'], output_dir=out/'independent')
    if checked['status'] != receipt['status']:
        raise ValueError('original independent native execution disagrees')
    return dict(context, certificate=certificate, receipt=receipt, independent_receipt=checked)


_CHILD = '''import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine_v44 import Machine
from research.unified_consequence_runtime.native_bootstrap_runtime_v44 import MetadataRuntime
from research.unified_consequence_runtime import native_environment_v44 as environment
from research.unified_consequence_runtime import native_execution_v43 as worker
from research.unified_consequence_runtime.native_runtime_v44 import NativeRuntimeV44
s=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.mkdir()
m=Machine(Path(s['components']),Path(s['state']),out/'evaluator',out/'unused.json')
r=MetadataRuntime(m,out/'metadata')
o,c=r.execute(s['capability'],s['request']);binding=r.bind(s['capability'],c)
environment.preflight_bootstrap(m,s['native_binding'],s['native']['contract'],s['native']['authority'],s['native']['policy'])
n=s['native'];before=worker.attempt_snapshot()
native=NativeRuntimeV44(m,n['contract'],n['authority'],n['certificate'],n['policy'],out/'native-runtime',bootstrap_binding=s['native_binding'])
receipt,consequence=native.execute(s['native_capability'])
checked=worker.validate_receipt(n['contract'],n['candidate'],n['authority'],n['certificate'],receipt,policy=n['policy'],output_dir=out/'independent-native')
assert checked['status']=='PASS_NATIVE' and checked['junit']['passed']>0
assert set(m.mt.live_ids(m.log))==m.flash_live_ids()
after=worker.attempt_snapshot()
(out/'RESULT.json').write_text(json.dumps({'status':'PASS_SEPARATE_PROCESS_METADATA_AND_PROTECTED_NATIVE_EXECUTION','metadata_observation':dict(o),'binding':binding,'native_status':checked['status'],'native_junit':checked['junit'],'native_consequence':consequence,'costs':m.costs,'native_calls':after['native_calls']-before['native_calls']},sort_keys=True)+'\\n')
'''


def native_supplement(out, frozen, components):
    """Actual original protected PASS/FAIL, selective withdrawal and native restart."""
    from . import decisive_native_verify as verifier
    from . import native_source_v42 as source
    from . import native_environment_selection_v44 as selection
    from . import native_environment_v44 as environment_operation
    from .native_bootstrap_runtime_v44 import MetadataRuntime, request
    from .developmental_machine_v44 import Machine
    from .native_runtime_v44 import NativeRuntimeV44
    from . import native_execution_v43 as worker
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    interpreter = str(next(row['interpreter'] for row in frozen['runtimes'].values()
                           if row['identity']['version_info'][:2] == [3, 12]))
    metadata_environment = verifier.environment_identity(interpreter)
    environment = worker.environment_identity(interpreter)
    repo = out/'source'
    shutil.copytree(RECORDS/'preimplementation/original_backend_fixture', repo)
    full = (repo/'tests/test_protected.py').read_bytes()
    marker = b'\n\ndef test_protected_failure():'
    if full.count(marker) != 1:
        raise ValueError('frozen original native acceptance test boundary changed')
    passing = full.split(marker)[0]+b'\n'
    import_only = passing.split(b'\n\ndef test_original_pass():')[0]+b'\n'
    (repo/'tests/test_protected.py').write_bytes(import_only)
    _git(repo, 'init', '-q'); base = _commit(repo, 'original immutable native fixture source')
    (repo/'tests/test_protected.py').write_bytes(passing)
    pass_augmented = _commit(repo, 'frozen original passing assertion only')
    (repo/'tests/test_protected.py').write_bytes(full)
    fail_augmented = _commit(repo, 'frozen original protected failing assertion only')
    protocol = frozen['acceptance']['protocol_sha256']
    source_before = source.snapshot(repo, fail_augmented)
    machine = Machine(Path(components), out/'state', out/'evaluator', out/'unused.json')
    runtime = MetadataRuntime(machine, out/'metadata')
    value = request(repo, base, interpreter, environment_sha256=verifier.fingerprint(metadata_environment),
                    protocol_binding=protocol, horizon_seconds=90)
    runtime.register('original-protected-native', value)
    cold = selection.select_profile(source.snapshot(repo, base)[1], json.loads(CATALOG.read_text()))
    if cold['status'] != 'UNKNOWN' or cold['reason'] != 'UNKNOWN_DYNAMIC_METADATA':
        raise ValueError('acceptance source no longer exposes its frozen metadata obstruction')
    cap = runtime.admit(value)
    activated = machine.select_and_execute_frontier('original-protected-native', runtime)
    observation = activated['metadata_observation']
    selected = selection.select_profile(source.snapshot(repo, base)[1], json.loads(CATALOG.read_text()), observation)
    selection.validate_selection(source.snapshot(repo, base)[1], json.loads(CATALOG.read_text()), selected, observation)
    if selected['status'] != 'CANDIDATE_SOURCE_ENVIRONMENT':
        raise ValueError('independently observed metadata did not select an original profile')
    binding = runtime.bind(cap, activated['consequence'])
    context = _native_context(repo, base, pass_augmented, environment, interpreter, protocol)
    profile = selected['selected_profile']
    def native_binding(metadata_binding, selected_observation, selected_context):
        setup = dict(selected_context, status='PREPARED', bootstrap_binding=metadata_binding,
            selection=selection.select_profile(source.snapshot(repo, base)[1], json.loads(CATALOG.read_text()), selected_observation),
            pinned_packages_sha256=verifier.fingerprint(environment_operation.installed_package_identity(interpreter, profile)))
        return environment_operation.bind_bootstrap_environment(machine, setup, json.loads(CATALOG.read_text()), selected_observation)
    bound = native_binding(binding, observation, context)
    environment_operation.preflight_bootstrap(machine, bound, context['contract'], context['authority'], context['policy'])
    refusal_checks = []
    def require_closed(label, supplied_binding, supplied_contract, scope=None):
        scope = context if scope is None else scope
        before_calls = worker.attempt_snapshot()
        refused = False
        try:
            environment_operation.preflight_bootstrap(machine, supplied_binding, supplied_contract,
                                                      scope['authority'], scope['policy'])
        except (ValueError, PermissionError):
            refused = True
        after_calls = worker.attempt_snapshot()
        if not refused or any(after_calls[key] != before_calls[key] for key in ('native_calls', 'collection_calls')):
            raise ValueError('invalid metadata/native binding reached execution: '+label)
        refusal_checks.append({'control': label, 'status': 'REFUSED_BEFORE_NATIVE_OR_COLLECTION'})
    require_closed('wrong-native-contract', bound, dict(context['contract'], environment_sha256='0'*64))
    require_closed('forged-environment-selection', dict(bound, environment_selection_id=cap), context['contract'])
    spare_context = _native_context(repo, base, fail_augmented, environment, interpreter, protocol)
    spare = native_binding(binding, observation, spare_context)
    environment_operation.preflight_bootstrap(machine, spare, spare_context['contract'],
                                             spare_context['authority'], spare_context['policy'])
    machine.append('revoke', {'target': spare['environment_selection_id'],
        'reason': 'V44 exact unused environment-selection witness negative',
        'controlled_local_withdrawal': True, 'upstream_revocation': False})
    machine.flush()
    require_closed('withdrawn-environment-selection', spare, spare_context['contract'], spare_context)
    environment_operation.preflight_bootstrap(machine, bound, context['contract'], context['authority'], context['policy'])
    def native_admission(selected_context, selected_binding, folder):
        certificate = worker.collect(selected_context['contract'], selected_context['authority'], folder/'collection', policy=selected_context['policy'])
        native = NativeRuntimeV44(machine, selected_context['contract'], selected_context['authority'], certificate,
                                  selected_context['policy'], folder/'runtime', bootstrap_binding=selected_binding)
        native_cap = native.admit(selected_context['candidate'])
        receipt, consequence = native.execute(native_cap)
        independent = worker.validate_receipt(selected_context['contract'], selected_context['candidate'], selected_context['authority'],
            certificate, receipt, policy=selected_context['policy'], output_dir=folder/'independent')
        return dict(selected_context, certificate=certificate, receipt=receipt, independent_receipt=independent), native_cap, consequence
    passed, native_capability, native_consequence = native_admission(context, bound, out/'native-pass')
    if passed['receipt']['status'] != 'PASS_NATIVE' or passed['receipt']['junit']['passed'] != 1:
        raise ValueError('original protected PASS assertion did not execute completely')
    write(out/'PASS_CONTEXT.json', passed)
    unrelated = machine.append('source_support', {'family': 'unrelated-original-native-acceptance-input'})
    machine.flush()
    machine.withdraw(cap, 'V44 metadata ancestor acceptance withdrawal')
    live = set(machine.mt.live_ids(machine.log))
    if native_capability in live or native_consequence in live or activated['consequence'] in live or unrelated not in live:
        raise ValueError('exact metadata ancestor withdrawal did not preserve causal separation')
    refused = False
    try:
        environment_operation.preflight_bootstrap(machine, bound, context['contract'], context['authority'], context['policy'])
    except PermissionError:
        refused = True
    if not refused:
        raise ValueError('revoked metadata invocation reached subsequent native execution')
    restored = runtime.restore(cap, value)
    fresh_observation, fresh_invocation = runtime.execute(restored, value)
    fresh_binding = runtime.bind(restored, fresh_invocation)
    fresh_bound = native_binding(fresh_binding, fresh_observation, context)
    environment_operation.preflight_bootstrap(machine, fresh_bound, context['contract'], context['authority'], context['policy'])
    fresh, restored_native_capability, restored_native_consequence = native_admission(context, fresh_bound, out/'native-restoration')
    if fresh['receipt']['status'] != 'PASS_NATIVE':
        raise ValueError('fresh restoration did not reexecute the protected original consequence')
    failing_context = _native_context(repo, base, fail_augmented, environment, interpreter, protocol)
    fail_binding = native_binding(fresh_binding, fresh_observation, failing_context)
    fail_certificate = worker.collect(failing_context['contract'], failing_context['authority'], out/'native-fail/collection', policy=failing_context['policy'])
    failing_runtime = NativeRuntimeV44(machine, failing_context['contract'], failing_context['authority'], fail_certificate,
        failing_context['policy'], out/'native-fail/runtime', bootstrap_binding=fail_binding)
    observed_fail = failing_runtime.observe()
    fail_receipt = {key: item for key, item in observed_fail.items() if key != 'observation_id'}
    independent_fail = worker.validate_receipt(failing_context['contract'], failing_context['candidate'], failing_context['authority'],
        fail_certificate, fail_receipt, policy=failing_context['policy'], output_dir=out/'native-fail/independent')
    failed = dict(failing_context, certificate=fail_certificate, receipt=fail_receipt, independent_receipt=independent_fail)
    if failed['receipt']['status'] != 'FAIL_NATIVE' or failed['receipt']['junit']['failures'] != 1:
        raise ValueError('protected assertion failure was not independently reported FAIL_NATIVE')
    write(out/'FAIL_CONTEXT.json', failed)
    spec = {'components': str(Path(components).resolve()), 'state': str(machine.state),
            'capability': restored, 'request': value, 'native': fresh,
            'native_binding': fresh_bound, 'native_capability': restored_native_capability}
    write(out/'RESTART_SPEC.json', spec)
    command = [sys.executable, '-B', '-c', _CHILD, str(out/'RESTART_SPEC.json'), str(out/'restart')]
    before = time.monotonic()
    child = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT),
        PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0'), capture_output=True, timeout=300)
    (out/'RESTART.stdout.log').write_bytes(child.stdout); (out/'RESTART.stderr.log').write_bytes(child.stderr)
    write(out/'RESTART_PROCESS.json', {'argv': command, 'seconds': time.monotonic()-before,
                                      'returncode': child.returncode})
    if child.returncode:
        raise ValueError('separate-process original native restart failed; raw evidence retained')
    restart = json.loads((out/'restart/RESULT.json').read_text())
    if source.snapshot(repo, fail_augmented) != source_before:
        raise ValueError('metadata/native qualification changed immutable original fixture bytes')
    report = {'status': 'PASS_BOUNDED_METADATA_TO_ORIGINAL_NATIVE_ASSERTIONS',
        'fixture_role': 'Preimplementation infrastructure fixture only; no prospective scientific result',
        'environment_identities': {'metadata': metadata_environment, 'native': environment,
            'metadata_sha256': verifier.fingerprint(metadata_environment),
            'native_sha256': worker.fingerprint(environment),
            'boundary': 'Original backend identity and extended native-execution identity remain distinct; neither digest substitutes for the other.'},
        'cold_selection': cold, 'observed_selection': selected, 'pass': passed['receipt']['junit'],
        'fail': failed['receipt']['junit'], 'initial_capability': cap, 'restored_capability': restored,
        'initial_native_capability': native_capability, 'restored_native_capability': restored_native_capability,
        'restored_native_consequence': restored_native_consequence,
        'withdrawn_native_consequence': native_consequence, 'unrelated_support': unrelated,
        'binding_refusal_controls': refusal_checks,
        'withdrawal_refused_before_native_execution': refused, 'restart': restart,
        'restoration_native_status': fresh['receipt']['status'], 'source_preserved': True,
        'costs': machine.costs, 'formal_refinement': 'UNKNOWN', 'external_containment': 'UNKNOWN'}
    write(out/'RESULT.json', report)
    return report


def _build_inventory(root):
    records = []
    for path in sorted(Path(root).rglob('build-attempt.json')):
        if path.is_symlink():
            raise ValueError('redirected actual backend attempt')
        row = json.loads(path.read_text())
        if row.get('schema') == 'udm.generic-build-attempt.v1':
            records.append({'path': str(path), 'sha256': sha(path.read_bytes()), 'record': row})
    return {'actual_unique_attempt_paths': len(records),
            'build_calls': sum(row['record'].get('build_calls', 0) for row in records),
            'build_seconds': sum(row['record'].get('build_seconds', 0) for row in records), 'records': records,
            'boundary': 'All retained actual original backend attempt paths, including child processes; nested costs are nonadditive.'}


def audit_native_packets(root, frozen):
    """Reuse the original raw packet checker, with a metadata-only final scope."""
    namespace = dict(vars(original))
    code = inspect.getsource(original.audit_native_packets)
    before = 'if not certificates or not generated_passes or not generated_failures:'
    after = ("if not certificates or not any(row['status']=='PASS_NATIVE' for row in receipts) "
             "or not any(row['status']=='FAIL_NATIVE' for row in receipts):")
    if code.count(before) != 1:
        raise ValueError('original raw-native audit scope binding changed')
    code = code.replace(before, after).replace(
        'missing actual generated-source collection, protected failure or native pass',
        'missing actual original-source collection, protected failure or native pass').replace(
        'Actual V43 generated-module native PASS and protected FAIL independently reconstructed',
        'Actual original-worker native PASS and protected FAIL independently reconstructed').replace(
        'UDM_V43_RAW_NATIVE_PACKET_AUDIT', 'UDM_V44_RAW_NATIVE_PACKET_AUDIT')
    exec(compile(code, __file__+':original-raw-native-scope-binding', 'exec'), namespace)
    return namespace['audit_native_packets'](root, frozen)


def qualify(repo, freeze_path, out, components):
    import pytest
    from . import native_execution_v43 as worker
    repo, out = Path(repo).resolve(), Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    result = {'schema': RESULT_SCHEMA, 'status': 'UNKNOWN_NATIVE_BOOTSTRAP_QUALIFICATION',
        'scope': 'NATIVE_METADATA_BOOTSTRAP_INFRASTRUCTURE_ONLY',
        'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
        'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
    started, before = time.monotonic(), worker.attempt_snapshot()
    try:
        with original.index_interval(repo, out/'index-interval'):
            frozen = check_freeze(repo, freeze_path)
            result.update(source_commit=frozen['source_commit'], freeze=frozen)
            components_before = original.component_inventory(components, out/'components-before')
            inventory = original._PytestInventory()
            tests = _control_tests()
            args = ['-q', '-p', 'no:cacheprovider', '--import-mode=importlib', '--basetemp='+str(out/'pytest'),
                    '--junitxml='+str(out/'contracts.xml'), *tests]
            previous = Path.cwd()
            try:
                os.chdir(repo)
                with (out/'stdout.log').open('w') as stdout, (out/'stderr.log').open('w') as stderr:
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        code = int(pytest.main(args, plugins=[inventory]))
            finally:
                os.chdir(previous)
            counts = original._junit((out/'contracts.xml').read_bytes())
            result['contracts'] = {'collection': inventory.collected, 'reports': inventory.reports,
                                   'junit': counts, 'pytest_exit_code': code}
            write(out/'PYTEST_INVENTORY.json', result['contracts'])
            if (code or not counts['tests'] or counts['tests'] != len(inventory.collected)
                    or inventory.collected != frozen['control_collection']
                    or len(set(inventory.collected)) != len(inventory.collected)
                    or any(counts[key] for key in ('failures', 'errors', 'skipped'))
                    or any(not any(node.startswith(name+'::') for node in inventory.collected) for name in tests)):
                raise ValueError('new frozen bootstrap controls failed or collection changed')
            result['inherited_controls'] = original.inherited_controls(out/'original-adversarial-controls', frozen)
            result['native_supplement'] = native_supplement(out/'native-supplement', frozen, components)
            result['raw_native_audit'] = audit_native_packets(out, frozen)
            write(out/'RAW_NATIVE_AUDIT.json', result['raw_native_audit'])
            if original.component_inventory(components, out/'components-after') != components_before:
                raise ValueError('original independent authority component source changed')
            result['loaded_authorities'] = original.loaded_authorities(components, components_before)
            write(out/'LOADED_AUTHORITIES.json', result['loaded_authorities'])
            check_freeze(repo, freeze_path)
            result['status'] = QUALIFIED
    except (Exception, KeyboardInterrupt) as error:
        result['smallest_obstruction'] = type(error).__name__+': '+str(error)
    finally:
        after = worker.attempt_snapshot()
        result['native_attempts'] = {'before': before, 'after': after,
            'delta': {key: after[key]-before[key] for key in after if isinstance(after[key], (int, float))}}
        result['build_attempts'] = _build_inventory(out)
        result['wall_seconds'] = time.monotonic()-started
        result['cost_boundary'] = 'Measured native/backend/controller intervals are retained and nested; complete engineering/model/tool/storage lifecycle cost remains UNKNOWN.'
        if (out/'index-interval/AUDIT.json').is_file():
            result['index_audit'] = json.loads((out/'index-interval/AUDIT.json').read_text())
        if result['status'] == QUALIFIED and (not result['native_attempts']['delta'].get('native_calls')
                or not result['native_attempts']['delta'].get('collection_calls') or not result['build_attempts']['build_calls']):
            result.update(status='UNKNOWN_NATIVE_BOOTSTRAP_QUALIFICATION',
                          smallest_obstruction='Missing actual native, collection or original backend execution accounting')
        write(out/'RESULT.json', result)
    return result


def archive(repo, out, freeze_path=None, preparation=(), components=None):
    # Version only the archive schema/name; original topology/index/hash logic.
    namespace = dict(vars(original))
    code = inspect.getsource(original.archive).replace('EXPERIMENT_INTERFACE_V43_EVIDENCE', 'NATIVE_BOOTSTRAP_V44_EVIDENCE').replace(
        'UDM_EXPERIMENT_INTERFACE_ARCHIVE_MANIFEST_V43', 'UDM_NATIVE_BOOTSTRAP_ARCHIVE_MANIFEST_V44')
    exec(compile(code, __file__+':original-archive-bindings', 'exec'), namespace)
    return namespace['archive'](repo, out, freeze_path, preparation, components)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--runtimes', type=Path)
    parser.add_argument('--write-freeze', action='store_true')
    parser.add_argument('--archive', action='store_true')
    parser.add_argument('--preparation', type=Path, action='append', default=[])
    parser.add_argument('--components', type=Path, default=Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')))
    args = parser.parse_args()
    if args.archive:
        value = archive(args.repo, args.out, args.freeze, args.preparation, args.components)
    elif args.write_freeze:
        if args.runtimes is None:
            parser.error('--runtimes is required for --write-freeze')
        value = write_freeze(args.repo, args.out, json.loads(args.runtimes.read_text()))
    else:
        if args.freeze is None:
            parser.error('--freeze is required for qualification')
        value = qualify(args.repo, args.freeze, args.out, args.components)
    print(canonical({key: value[key] for key in ('schema', 'status', 'source_commit', 'smallest_obstruction') if key in value}))
    return 0 if not value.get('status', '').startswith('UNKNOWN_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
