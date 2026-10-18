"""Prospective reattempt through admitted v2, using existing discovery machinery.

This controller is frozen before target bytes. Unsupported admission is retained
as UNKNOWN; it never supplies a task-specific repair, weakens the native suite,
or treats a green evidence workflow as developmental success.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

from .developmental_machine import Machine, canonical, digest
from .decisive_native import catalog, orders, is_test, passed as original_passed, task_roles
from .native_meta_decision import choose_meta_decision, invoke_meta_policy
from .native_runtime_v2 import NativeRuntimeV2, AUTHORITY
from .native_environment_v2 import provision
from . import native_execution_v2 as worker
from .qualify_decisive_native import copy_state

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-frontier-v2'
PROTOCOL = RECORDS/'PROTOCOL.json'
METADATA = RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v2'


def protocol():
    value = json.loads(PROTOCOL.read_text())
    if value['metadata_sha256'] != digest(METADATA.read_bytes()):
        raise ValueError('prepared metadata changed')
    for key in ('policy', 'packages'):
        record = value[key]
        if digest((HERE.parents[1]/record['path']).read_bytes()) != record['sha256']:
            raise ValueError('externally fixed '+key+' changed')
    return value


def require_admission_gate(value):
    gate = value.get('admission_gate')
    fields = {'status', 'source_commit', 'run_id', 'artifact_id', 'artifact_sha256',
              'qualification_result_sha256', 'result_path'}
    if (not isinstance(gate, dict) or set(gate) != fields
            or gate['status'] != 'ADMISSION_ONLY_QUALIFIED'
            or not re.fullmatch('[0-9a-f]{40}', gate.get('source_commit', ''))
            or any(not isinstance(gate[key], int) or gate[key] <= 0 for key in ('run_id', 'artifact_id'))
            or any(not re.fullmatch('[0-9a-f]{64}', gate.get(key, ''))
                   for key in ('artifact_sha256', 'qualification_result_sha256'))):
        raise ValueError('independent admission qualification is required before prospective freeze')
    path = (HERE.parents[1]/gate['result_path']).resolve()
    if not path.is_relative_to(HERE.parents[1]) or digest(path.read_bytes()) != gate['qualification_result_sha256']:
        raise ValueError('independent admission qualification result changed')
    result = json.loads(path.read_text())
    if (result.get('source_commit') != gate['source_commit'] or result.get('status') != gate['status']
            or result.get('first_task_gate', {}).get('status') != 'PASS'
            or any(result.get('verdicts', {}).get(key) != 'UNKNOWN' for key in ('G2', 'G3', 'G4'))):
        raise ValueError('independent admission qualification is not the required separate gate')
    qualified = result.get('freeze', {}).get('files', {})
    names = ['research/unified_consequence_runtime/'+name+'.py' for name in (
        'native_admission_v2', 'native_environment_v2', 'native_execution_v2',
        'native_runtime_v2', 'qualify_native_admission_v2')]
    names.append('.github/workflows/udm-native-admission-v2.yml')
    for name in names:
        current = HERE.parents[1]/name
        if (not current.is_file() or current.is_symlink()
                or qualified.get(name) != digest(current.read_bytes())):
            raise ValueError('current bridge differs from exact qualified admission source: '+name)
    return gate


def write_freeze(repo, out):
    repo = Path(repo).resolve(); value = protocol(); gate = require_admission_gate(value)
    if subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain']).strip():
        raise ValueError('commit implementation and protocol before target source access')
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    names = subprocess.check_output(['git', '-C', str(repo), 'ls-files',
        'research/unified_consequence_runtime', '.github/workflows/udm-native-frontier-v2.yml',
        '.github/workflows/udm-native-admission-v2.yml'], text=True).splitlines()
    files = {}
    for name in names:
        raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo), 'show', head+':'+name])
        if (repo/name).read_bytes() != raw: raise ValueError('working source differs from commit')
        files[name] = digest(raw)
    committed = int(subprocess.check_output(['git', '-C', str(repo), 'show', '-s', '--format=%ct', head], text=True))
    result = {'schema': 'UDM_NATIVE_FRONTIER_FREEZE_V2', 'source_commit': head,
        'frozen_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(committed)),
        'files': files, 'protocol_sha256': digest(PROTOCOL.read_bytes()), 'admission_gate': gate,
        'prior_source_exposure': 'DECLARED_NONE_FOR_SELECTED_TASK_BYTES; METADATA_ONLY_CURATION',
        'repeat_boundary': 'Only the original pre-outcome freeze is prospective; repeats do not restore untouchedness.'}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(canonical(result)+'\n')
    return result


def check_freeze(repo, path):
    result = json.loads(Path(path).read_text()); repo = Path(repo)
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if result.get('schema') != 'UDM_NATIVE_FRONTIER_FREEZE_V2' or result['source_commit'] != head:
        raise ValueError('prospective freeze/execution source differs')
    for name, value in result['files'].items():
        if digest((repo/name).read_bytes()) != value: raise ValueError('frozen implementation changed')
    if digest(PROTOCOL.read_bytes()) != result['protocol_sha256']:
        raise ValueError('frozen protocol changed')
    if require_admission_gate(protocol()) != result['admission_gate']:
        raise ValueError('independent admission qualification changed')
    return result


def native_probe(machine, runtime, candidate, label, dependencies=()):
    started = time.monotonic(); before = len(machine.costs)
    runtime._live(*dependencies)
    try:
        receipt = runtime._verify(candidate)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        outputs = [row['output'] for row in machine.costs[before:] if row.get('output')]
        folder = outputs[-1] if outputs else ''
        retained = Path(folder)/'receipt.json' if folder else None
        if retained is not None and retained.is_file(): receipt = json.loads(retained.read_text())
        else:
            execution = Path(folder)/'execution/checked-report.json' if folder else None
            actual = json.loads(execution.read_text()) if execution is not None and execution.is_file() else {}
            for row in machine.costs[before:]:
                if (row.get('phase') == 'generic_native_v2_independent_verification'
                        and row.get('output') == folder and not row.get('costs')):
                    row['costs'] = actual.get('costs', {})
            receipt = {'status': 'UNKNOWN_NATIVE_ADMISSION', 'error': str(error),
                'junit': dict(tests=0, passed=0, failures=0, errors=0, skipped=0),
                'costs': {'native_calls': actual.get('costs', {}).get('native_calls', 0),
                          'total_seconds': time.monotonic()-started},
                'retained_raw_output': folder}
    else: folder = machine.costs[-1]['output']
    runtime._live(*dependencies)
    record = {'schema': 'UDM_NATIVE_PROFILE_RECORD_V2', 'receipt': receipt,
        'contract': runtime.contract, 'candidate': candidate, 'authority': runtime.suite_authority,
        'certificate': runtime.certificate, 'policy': runtime.policy, 'evidence_dir': folder,
        'producer': {'source': runtime.source, 'authority': runtime.authority, 'dependencies': list(dependencies)}}
    key = machine.put(record)
    event = machine.append('native_frontier_v2_probe', {'record': key, 'label': label},
                           (runtime.source, runtime.authority, *dependencies))
    machine.costs.append({'phase': 'native_v2_probe_envelope', 'seconds': time.monotonic()-started,
        'inclusive_not_additive': True, 'native_calls': receipt['costs']['native_calls'], 'status': receipt['status']})
    machine.flush()
    return {'record': key, 'evidence': event, **record}


def passed(receipt):
    """Reuse the original success rule after the explicit v2 receipt binding."""
    return original_passed(dict(receipt, exit_code=receipt.get('execution', {}).get('process_exit_code')))


def native_observation(receipt):
    """Use retained v2 stream bytes identically during proposal and checking."""
    text = '\n'.join(base64.b64decode(receipt.get('packet', {}).get(name, ''), validate=True).decode(errors='replace')
                     for name in ('stdout.log', 'stderr.log', 'native.xml'))
    return dict(receipt, evidence_text=text)


def acquisition_budget(machine, scope, *, reserve=True):
    value = protocol()
    calls = sum(row.get('costs', {}).get('native_calls', 0) for row in machine.costs
                if row.get('phase') in ('generic_native_v2_independent_verification',
                                       'independent_native_v2_receipt_reexecution'))
    if (calls + int(reserve) > value['acquisition_native_calls']
            or time.monotonic()-scope['acquisition_started_monotonic'] >= value['training_seconds']):
        raise ValueError('UNKNOWN_SEARCH: inclusive native acquisition or verification budget exhausted')


def budgeted_native_probe(machine, runtime, candidate, label, scope):
    """Keep a completed native result even when its elapsed budget forbids promotion."""
    acquisition_budget(machine, scope)
    probe = native_probe(machine, runtime, candidate, label)
    try:
        acquisition_budget(machine, scope, reserve=False)
    except ValueError as error:
        return dict(probe, status='UNKNOWN_ACQUISITION_BUDGET',
                    budget_eligibility='UNKNOWN_OVER_BUDGET', budget_obstruction=str(error))
    return dict(probe, budget_eligibility='ELIGIBLE')


def checked_record(record, machine=None, *, scope=None, cache=None):
    if record.get('schema') != 'UDM_NATIVE_PROFILE_RECORD_V2':
        raise ValueError('wrong independently retained native record')
    if record['receipt']['status'] not in ('PASS_NATIVE', 'FAIL_NATIVE'):
        raise ValueError('UNKNOWN_SEARCH: incomplete native obligation is not a closed profile')
    key = worker.fingerprint(record)
    if cache is not None and key in cache: return cache[key]
    if machine is None: raise ValueError('independent native producer lineage is required')
    nodes = {node.id: node for node in machine.log}; producer = record['producer']
    premises = (producer['source'], producer['authority'], *producer['dependencies'])
    events = [node for node in machine.log if node.kind == 'native_frontier_v2_probe'
              and node.payload.get('record') == key and tuple(node.premises) == premises]
    live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    if not events or any(ident not in live for ident in premises) or not any(node.id in live for node in events):
        raise ValueError('native receipt has no exact live producer event and causal premises')
    source, authority = nodes[producer['source']], nodes[producer['authority']]
    descriptor = source.payload.get('source', {})
    if (source.kind != 'generic_native_source' or tuple(source.premises) != (authority.id,)
            or authority.kind != 'execution_authority_ceiling' or authority.payload != AUTHORITY or authority.premises
            or any(machine.get(descriptor[key]) != record[field] for key, field in (
                ('contract', 'contract'), ('suite_authority', 'authority'), ('certificate', 'certificate'), ('policy', 'policy')))):
        raise ValueError('native receipt producer has wrong source or external authority lineage')
    if scope is not None: acquisition_budget(machine, scope)
    out = machine.state.parent/'independent-native-profile'/secrets.token_hex(16)
    started = time.monotonic(); checked = None
    try:
        checked = worker.validate_receipt(record['contract'], record['candidate'], record['authority'],
            record['certificate'], record['receipt'], policy=record['policy'], output_dir=out, independent=True)
    finally:
        raw = out/'receipt.json'
        partial = out/'execution/checked-report.json'
        actual = (json.loads(raw.read_text()) if raw.is_file() else
                  json.loads(partial.read_text()) if partial.is_file() else {})
        machine.costs.append({'phase': 'independent_native_v2_receipt_reexecution', 'output': str(out),
            'seconds': time.monotonic()-started, 'costs': actual.get('costs', {}),
            'status': actual.get('status', 'UNKNOWN_NATIVE_REEXECUTION')})
    if scope is not None: acquisition_budget(machine, scope, reserve=False)
    if cache is not None: cache[key] = record['receipt']
    return record['receipt']


def search(machine, runtime, rows, order, budget, cache, label, *, seconds, reuse=False,
           unique_ceiling=None, deadline=None, dependencies=(), scope=None):
    started = time.monotonic(); by_id = {row['id']: row for row in rows}; attempts = []; winner = None
    status = 'UNKNOWN_SEARCH'
    for ident in order[:budget]:
        if time.monotonic()-started >= seconds or deadline is not None and time.monotonic() >= deadline: break
        if reuse and ident in cache: probe = cache[ident]
        else:
            if unique_ceiling is not None and len(cache) >= unique_ceiling: break
            if scope is not None:
                try: acquisition_budget(machine, scope)
                except ValueError: status = 'UNKNOWN_SEARCH_BUDGET'; break
            probe = native_probe(machine, runtime, by_id[ident]['candidate'], label+':'+ident,
                                 dependencies=dependencies); cache[ident] = probe
        attempts.append(probe['record'])
        if passed(probe['receipt']): winner = ident; status = 'PASS_BOUNDED_SEARCH'; break
        if probe['receipt']['status'] != 'FAIL_NATIVE': status = 'UNKNOWN_NATIVE_OBLIGATION'; break
    elapsed = time.monotonic()-started
    within = elapsed <= seconds and (deadline is None or started+elapsed <= deadline)
    if not within: status, winner = 'UNKNOWN_SEARCH_BUDGET', None
    return {'status': status, 'winner': winner, 'attempts': attempts, 'budget': budget,
        'seconds': elapsed, 'horizon_seconds': seconds, 'within_budget': within,
        'complete_old_language_obstruction': 'NOT_ESTABLISHED'}


def closed_failure(machine, episode, order, budget, *, scope=None, cache=None):
    return (bool(order) and episode.get('within_budget') is True and episode['winner'] is None
        and len(episode['attempts']) == min(budget, len(order))
        and all(worker.fingerprint(machine.get(key)['candidate']) == order[index]
            and checked_record(machine.get(key), machine, scope=scope, cache=cache)['status'] == 'FAIL_NATIVE'
            for index, key in enumerate(episode['attempts'])))


def future_selection_warrant(machine, outcomes, cold_order, budget, *, scope=None):
    cache = {}
    return (bool(outcomes) and outcomes['warm'].get('within_budget') is True
        and outcomes['warm']['winner'] is not None and bool(outcomes['warm']['attempts'])
        and closed_failure(machine, outcomes['cold'], cold_order, budget, scope=scope, cache=cache)
        and checked_record(machine.get(outcomes['warm']['attempts'][-1]), machine, scope=scope, cache=cache)['status'] == 'PASS_NATIVE')


def bounded_catalog(spec, out, timeout, machine):
    specpath = Path(out).with_suffix('.spec.json'); specpath.write_text(canonical(spec)+'\n')
    started = time.monotonic()
    try:
        subprocess.run([sys.executable, '-B', '-m', MODULE, '--catalog-spec', str(specpath), '--out', str(out)],
                       check=True, timeout=timeout)
        return json.loads(Path(out).read_text())
    finally:
        machine.costs.append({'phase': 'original_v104_catalog', 'seconds': time.monotonic()-started,
                             'horizon_seconds': timeout, 'native_calls': 0})


def _checked_context(machine, future, scope, frozen, cache):
    context = machine.get(scope['contexts'][future]); contract = context['contract']; spec = frozen[future]
    bounds = context['source_boundaries']
    if (contract['repository'] != future or contract['protocol_binding'] != scope['protocol_binding']
            or bounds['repository'] != future or bounds['base_commit'] != spec['base_commit']
            or bounds['author_test_head_commit'] != spec['head_commit']
            or bounds['augmented_commit'] != contract['commit'] or bounds['head_production_fetched'] is not False
            or bounds['production_preserved'] is not True):
        raise ValueError('native context differs from frozen source frontier')
    identity, files, _ = worker.original._snapshot(contract['repo_path'], contract['commit'])
    if any(contract[key] != value for key, value in identity.items()): raise ValueError('native source changed')
    _, base, _ = worker.original._snapshot(contract['repo_path'], spec['base_commit'])
    tests = {row['filename']: row for row in spec['files'] if is_test(row['filename'])}
    if set(tests) != {row['path'] for row in bounds['author_tests']}:
        raise ValueError('independent author-test scope differs')
    for row in bounds['author_tests']:
        raw = files[row['path']]
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob != row['git_blob'] or blob != tests[row['path']]['sha'] or digest(raw) != row['sha256']:
            raise ValueError('author-test bytes differ from pre-outcome Git blob identity')
    if files != {**base, **{name: files[name] for name in tests}}:
        raise ValueError('native author overlay changed production')
    baseline = machine.get(context['baseline_record'])
    if baseline['contract'] != contract or baseline['candidate'] != {'replacements': []}:
        raise ValueError('wrong independently verified native residual')
    if baseline['producer']['source'] != context['runtime_source'] or baseline['producer']['authority'] != context['runtime_authority']:
        raise ValueError('baseline producer differs from retained native source')
    receipt = checked_record(baseline, machine, scope=scope, cache=cache)
    if receipt['status'] != 'FAIL_NATIVE': raise ValueError('no verified failing native obligation')
    paths = [row['filename'] for row in spec['files'] if row['filename'].endswith('.py') and not is_test(row['filename'])]
    spec_catalog = context['catalog_spec']
    if (spec_catalog['repo'] != contract['repo_path'] or spec_catalog['commit'] != contract['commit']
            or spec_catalog['production_paths'] != paths or spec_catalog['cap'] != protocol()['candidate_cap_per_file']):
        raise ValueError('wrong original constructor source scope')
    observation = native_observation(receipt)
    regenerated = dict(spec_catalog, observation=observation)
    # Pure original grammar regeneration is separately bounded and charged.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='udm-v2-catalog-check-') as folder:
        rows = bounded_catalog(regenerated, Path(folder)/'catalog.json', protocol()['catalog_seconds'], machine)
    if canonical(rows) != canonical(context['catalog']) or orders(rows, spec_catalog['msi']) != context['orders']:
        raise ValueError('reported catalog or MSI ranking differs from original executable machinery')
    if worker.fingerprint(rows) != scope['candidate_catalog_sha256']:
        raise ValueError('native profile catalog binding differs')
    return context


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    """Source-bound independent carrier for the unchanged MSI/MDA meta-choice."""
    started = time.monotonic(); value = protocol()
    try:
        frozen_rows = task_roles(json.loads(METADATA.read_text())['selected'])
        frozen = {row['repo']: row for row in frozen_rows}; nodes = {node.id: node for node in machine.log}
        profiles = {candidate: {} for candidate in candidates}; scope = None; contexts = {}; cache = {}
        for ident in evidence_ids:
            node = nodes[ident]
            if node.kind != 'native_frontier_v2_profile': raise ValueError('wrong native profile evidence kind')
            report = machine.get(node.payload['report'])
            if scope is None: scope = report['scope']
            if (report['scope'] != scope or scope['protocol_sha256'] != digest(PROTOCOL.read_bytes())
                    or scope['source_binding'] != worker.fingerprint(frozen_rows)
                    or scope['budget'] != value['search_budget']):
                raise ValueError('mixed or changed frozen native evidence scope')
            policy, future = report['candidate'], report['future']
            if policy not in candidates or future not in futures: raise ValueError('profile replayed across task/policy')
            if future not in contexts: contexts[future] = _checked_context(machine, future, scope, frozen, cache)
            context = contexts[future]; order = context['orders'][policy]
            if report['order'] != order or len(report['attempts']) > scope['budget']:
                raise ValueError('native search order or budget changed')
            receipts = []; producer_events = []
            objects = {scope['contexts'][future], context['baseline_record'], *report['attempts']}
            if not objects <= set(scope['receipt_objects']): raise ValueError('native transitive evidence not retained')
            for index, key in enumerate(report['attempts']):
                record = machine.get(key)
                if (record['contract'] != context['contract'] or worker.fingerprint(record['candidate']) != order[index]
                        or record['producer']['source'] != context['runtime_source']
                        or record['producer']['authority'] != context['runtime_authority']
                        or any(passed(receipt) for receipt in receipts)):
                    raise ValueError('native receipt from wrong task, order or post-winner attempt')
                matching = [event.id for event in machine.log if event.kind == 'native_frontier_v2_probe'
                            and event.payload.get('record') == key]
                if len(matching) != 1: raise ValueError('ambiguous native profile producer')
                producer_events.append(matching[0])
                receipts.append(checked_record(record, machine, scope=scope, cache=cache))
            if tuple(node.premises) != tuple(producer_events):
                raise ValueError('native profile event premises differ from exact executed trace')
            if not any(passed(receipt) for receipt in receipts) and len(receipts) != min(scope['budget'], len(order)):
                raise ValueError('UNKNOWN_SEARCH: frozen policy horizon not fully observed')
            if future in profiles[policy]: raise ValueError('duplicate native profile')
            profiles[policy][future] = [0 if any(passed(receipt) for receipt in receipts) else 1,
                                      sum(receipt['costs']['native_calls'] for receipt in receipts)]
        if scope is None or any(set(row) != set(futures) for row in profiles.values()):
            raise ValueError('incomplete native profile carrier')
        return {'schema': 'UDM_NATIVE_META_PROFILE_EVIDENCE_V1', 'profiles': profiles,
                'evidence_ids': list(evidence_ids), 'scope': scope}
    finally:
        machine.costs.append({'phase': 'independent_native_v2_profile_reconstruction',
                             'seconds': time.monotonic()-started, 'native_calls': 0})


def agent_arm(context, destination, binding, budget):
    """Write executable comparator inputs, never a simulated comparator result."""
    limits = protocol()
    value = {'schema': 'UDM_CODING_AGENT_NATIVE_ARM_V2', 'status': 'READY_NOT_EXECUTED',
        'protocol_binding': binding, 'candidate_budget': budget,
        'candidate_budget_semantics': 'At most eight proposals in each declared original policy-order search; the future ordered proposal horizon is also eight',
        'total_acquisition_native_calls': limits['acquisition_native_calls'],
        'total_acquisition_wall_seconds': limits['training_seconds'],
        'native_budget_includes_independent_verification': True,
        'available_machinery': 'Same original constructor grammar and declared policy orders, source, observations and historical evidence; no extra operators, tools or history',
        'contract': context['setup']['contract'], 'authority': context['setup']['authority'],
        'certificate': context['certificate'], 'policy': context['setup']['policy'],
        'candidate_catalog': context.get('catalog', []), 'orders': context.get('orders', {}),
        'native_residual': context['baseline']['receipt'],
        'allowed_source': 'Exact predecessor source plus independently authored tests; no repaired production, PR body or patch',
        'native_command': 'python -B -m '+MODULE+' --agent-spec ARM.json --candidate CANDIDATE.json --out NEW_EVIDENCE_DIR',
        'comparability': 'Same per-search proposal horizon and total acquisition native-call/wall ceilings, including independent checks; same frozen 600s native ceiling. Charge all acquisition, tool, model, execution and maintenance costs. No external authority grant.'}
    Path(destination).write_text(canonical(value)+'\n'); return value


def qualify(args):
    value = protocol(); out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    frozen = check_freeze(args.repo, args.freeze); binding = digest(Path(args.freeze).read_bytes())
    policy = json.loads((HERE.parents[1]/value['policy']['path']).read_text())
    packages = json.loads((HERE.parents[1]/value['packages']['path']).read_text())
    tasks = task_roles(json.loads(METADATA.read_text())['selected'])
    started = time.monotonic(); machine = None; original = b''
    early_scope = {'acquisition_started_monotonic': started}
    result = {'schema': 'UDM_NATIVE_FRONTIER_RESULT_V2', 'source_commit': frozen['source_commit'],
        'freeze': frozen, 'freeze_sha256': binding,
        'verdicts': {'G0_G1': 'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY', 'G2': 'UNKNOWN', 'G3': 'UNKNOWN',
                     'G4': 'UNKNOWN', 'G5': 'UNKNOWN', 'G6': 'UNKNOWN'},
        'tasks': [{'repository': row['repo'], 'pr': row['pr'], 'role': row['role'], 'source_opened': False} for row in tasks],
        'conditions': {}, 'agent_comparator': {'status': 'NOT_EXECUTED_BY_CONTROLLER; USE_RETAINED_AGENT_ARM'},
        'cost_boundary': 'All setup, build, collection, verification, acquisition, integration, reclosure, restart and maintenance retained. Nested wall times are not additive. Engineering/model-dollar/token total remains UNKNOWN.'}
    def save():
        result['total_wall_seconds'] = time.monotonic()-started
        if machine is not None:
            raw = (out/'state/metatron-ledger.jsonl').read_bytes()
            for row in machine.costs:
                if (row.get('phase') in ('generic_native_v2_independent_verification',
                                         'independent_native_v2_receipt_reexecution')
                        and row.get('output') and not row.get('costs')):
                    partial = Path(row['output'])/'execution/checked-report.json'
                    if partial.is_file(): row['costs'] = json.loads(partial.read_text()).get('costs', {})
            result['machine_costs'] = machine.costs
            result['retention'] = {'records': len(machine.log), 'ledger_sha256': digest(raw),
                'original_prefix_preserved': raw.startswith(original),
                'persistent_bytes': sum(path.stat().st_size for path in (out/'state').rglob('*') if path.is_file())}
        (out/'RESULT.json').write_text(canonical(result)+'\n')
    contexts = {}
    try:
        copy_state(out); original = (out/'state/metatron-ledger.jsonl').read_bytes()
        machine = Machine(Path(args.components), out/'state', Path(args.components)/'evaluator', out/'state/unused-native-config.json')
        result['original_records'] = len(machine.log)
        def prepare(index):
            item = result['tasks'][index]
            try: acquisition_budget(machine, early_scope)
            except ValueError as error:
                item.update(status='UNKNOWN_ACQUISITION_BUDGET', reason=str(error)); save(); return None
            item['source_opened'] = True; save()
            setup = provision(tasks[index], out/('task-'+str(index)), binding, policy=policy, packages=packages)
            item['setup'] = setup; item['status'] = setup['status']; save()
            if setup['status'] != 'PREPARED': return None
            try:
                acquisition_budget(machine, early_scope)
                certificate = worker.collect(setup['contract'], setup['authority'], out/('task-'+str(index))/'collection', policy=policy)
                worker.validate_certificate(setup['contract'], setup['authority'], certificate, policy=policy,
                                            output_dir=out/('task-'+str(index))/'independent-collection')
                runtime = NativeRuntimeV2(machine, setup['contract'], setup['authority'], certificate, policy,
                                          out/('task-'+str(index))/'native-evidence')
                baseline = budgeted_native_probe(machine, runtime, {'replacements': []},
                                                  'original-system-'+str(index), early_scope)
                item['baseline'] = baseline; item['status'] = baseline['receipt']['status']
                if baseline['budget_eligibility'] != 'ELIGIBLE':
                    item.update(status='UNKNOWN_ACQUISITION_BUDGET', reason=baseline['budget_obstruction'])
                    save(); return None
                context = {'runtime': runtime, 'setup': setup, 'certificate': certificate, 'baseline': baseline}
                contexts[index] = context; save(); return context
            except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
                item['status'] = 'UNKNOWN_ADMISSION_INTERFACE'; item['reason'] = str(error); save(); return None
        training = prepare(0)
        if training is None or training['baseline']['receipt']['status'] != 'FAIL_NATIVE':
            if training is not None:
                try:
                    ledger = budgeted_native_probe(machine, training['runtime'], {'replacements': []},
                                                    'informed-ledger-original', early_scope)
                except ValueError as error:
                    ledger = {'status': 'UNKNOWN_ACQUISITION_BUDGET', 'reason': str(error), 'native_calls': 0}
                result['conditions']['fully_informed_executable_ledger'] = ledger
                result['agent_comparator'] = agent_arm(training, out/'AGENT_ARM.json', binding, value['search_budget'])
            else:
                result['conditions']['fully_informed_executable_ledger'] = {'status': 'UNKNOWN_SHARED_ADMISSION_REFUSAL', 'native_calls': 0}
            result['conditions']['original_system'] = result['tasks'][0].get('baseline', {'status': result['tasks'][0]['status'], 'native_calls': 0})
            result.update(status='UNKNOWN_NO_NATIVE_ACQUISITION_RESIDUAL',
                smallest_obstruction=result['tasks'][0].get('reason', result['tasks'][0].get('setup', {}).get('reason',
                    'No complete independently executable native failing obligation under frozen interface')),
                futures_remain_unopened=True, complete_old_language_obstruction='NOT_ESTABLISHED')
            return result
        paths = [row['filename'] for row in tasks[0]['files'] if row['filename'].endswith('.py') and not is_test(row['filename'])]
        spec = {'repo': training['setup']['contract']['repo_path'], 'commit': training['setup']['contract']['commit'],
            'production_paths': paths, 'triskelion': str(Path(args.source_repos)/'triskelion'),
            'observation': native_observation(training['baseline']['receipt']),
            'cap': value['candidate_cap_per_file']}
        rows = bounded_catalog(spec, out/'training-catalog.json', value['catalog_seconds'], machine)
        all_orders = orders(rows, Path(args.source_repos)/'msi'); training.update(catalog=rows, orders=all_orders)
        result['agent_comparator'] = agent_arm(training, out/'AGENT_ARM.json', binding, value['search_budget'])
        context_id = machine.put({'contract': training['setup']['contract'], 'catalog': rows, 'orders': all_orders,
            'catalog_spec': dict(spec, msi=str(Path(args.source_repos)/'msi')),
            'baseline_record': training['baseline']['record'], 'source_boundaries': training['setup']['source_boundaries'],
            'runtime_source': training['runtime'].source, 'runtime_authority': training['runtime'].authority})
        scope = {'protocol_binding': binding, 'protocol_sha256': digest(PROTOCOL.read_bytes()),
            'candidate_catalog_sha256': worker.fingerprint(rows), 'source_binding': worker.fingerprint(tasks),
            'budget': value['search_budget'], 'contexts': {tasks[0]['repo']: context_id},
            'receipt_objects': [context_id, training['baseline']['record']],
            'acquisition_started_monotonic': started}
        cache = {}; selection_start = time.monotonic(); episodes = {}
        for name, order in all_orders.items():
            episodes[name] = search(machine, training['runtime'], rows, order, scope['budget'], cache, 'train:'+name,
                seconds=value['per_search_seconds'], reuse=True, unique_ceiling=value['training_unique_calls'],
                deadline=started+value['training_seconds'], scope=scope)
        scope['receipt_objects'] = sorted(set(scope['receipt_objects']) | {probe['record'] for probe in cache.values()})
        profiles = {}; evidence = []; train_name = tasks[0]['repo']
        for name, order in all_orders.items():
            attempts = []
            for ident in order[:scope['budget']]:
                if ident not in cache: break
                attempts.append(cache[ident]['record'])
                if passed(cache[ident]['receipt']) or cache[ident]['receipt']['status'] != 'FAIL_NATIVE': break
            report = {'candidate': name, 'future': train_name, 'scope': scope, 'attempts': attempts, 'order': order}
            by_record = {probe['record']: probe['evidence'] for probe in cache.values()}
            evidence.append(machine.append('native_frontier_v2_profile', {'report': machine.put(report)},
                tuple(by_record[key] for key in attempts)))
            receipts = [machine.get(key)['receipt'] for key in attempts]
            profiles[name] = {train_name: [0 if any(passed(receipt) for receipt in receipts) else 1,
                                          sum(receipt['costs']['native_calls'] for receipt in receipts)]}
        machine.flush()
        training_elapsed = time.monotonic()-started
        result['training_elapsed_seconds'] = training_elapsed
        if training_elapsed > value['training_seconds']:
            result.update(status='UNKNOWN_TRAINING_BUDGET', smallest_obstruction='Training process exceeded frozen charged wall ceiling; no policy promotion')
            return result
        # Strong baseline actually reexecutes the best evidence-known order with
        # the same available operators and horizon; no cache-only comparison.
        ledger_name = min(all_orders, key=lambda name: (profiles[name][train_name], name))
        result['conditions']['fully_informed_executable_ledger'] = search(machine, training['runtime'], rows,
            all_orders[ledger_name], scope['budget'], {}, 'training-informed-ledger', seconds=value['per_search_seconds'],
            scope=scope, deadline=started+value['training_seconds'])
        result['conditions']['original_system'] = episodes['COLD_V104_ORDER']
        decision = choose_meta_decision(machine, tuple(all_orders), (train_name,), profiles, tuple(evidence),
            independent_check=reconstruct_profiles, source_repo=Path(args.source_repos))
        result.update(meta_decision=decision, training_profiles=profiles, training_episodes=episodes)
        if decision['status'] != 'WARRANTED_BOUNDED_POLICY_SELECTION':
            result.update(status='UNKNOWN_META_CHOICE', smallest_obstruction=decision.get('reason', decision['status']),
                          futures_remain_unopened=True); return result
        selected = invoke_meta_policy(machine, decision['policy_id'], protocol_binding=binding,
                                      candidate_catalog_sha256=scope['candidate_catalog_sha256'])
        result['selected_policy'] = selected
        # First source-distinct future remains withheld until selection is fixed.
        future = prepare(1)
        if future is None or future['baseline']['receipt']['status'] != 'FAIL_NATIVE':
            result.update(status='UNKNOWN_FUTURE_NATIVE_RESIDUAL', smallest_obstruction=result['tasks'][1].get('reason',
                'Future did not expose a complete verified failing native obligation')); return result
        future_paths = [row['filename'] for row in tasks[1]['files'] if row['filename'].endswith('.py') and not is_test(row['filename'])]
        future_spec = dict(spec, repo=future['setup']['contract']['repo_path'], commit=future['setup']['contract']['commit'],
            production_paths=future_paths, observation=native_observation(future['baseline']['receipt']))
        future_rows = bounded_catalog(future_spec, out/'future-1-catalog.json', value['catalog_seconds'], machine)
        future_orders = orders(future_rows, Path(args.source_repos)/'msi')
        outcomes = {}
        for label, order in (('cold', future_orders['COLD_V104_ORDER']), ('warm', future_orders[selected]),
                             ('ledger', future_orders[selected])):
            outcomes[label] = search(machine, future['runtime'], future_rows, order, scope['budget'], {},
                'future-'+label, seconds=value['per_search_seconds'], scope=scope,
                dependencies=(decision['policy_id'],) if label == 'warm' else ())
        result['future_results'] = outcomes
        try:
            warranted = future_selection_warrant(machine, outcomes, future_orders['COLD_V104_ORDER'],
                                                  scope['budget'], scope=scope)
            if warranted:
                acquisition_budget(machine, scope, reserve=3)
                candidate = next(row['candidate'] for row in future_rows if row['id'] == outcomes['warm']['winner'])
                capability = future['runtime'].admit(candidate, dependencies=(decision['policy_id'],))
                native, consequence = future['runtime'].execute(capability)
                acquisition_budget(machine, scope, reserve=False)
                result['future_admission'] = {'capability': capability, 'native': native, 'consequence': consequence}
                if not passed(native): raise ValueError('future native reexecution did not warrant selected operation')
                result['verdicts']['G2'] = 'WARRANTED_BOUNDED_PROSPECTIVE_NATIVE_POLICY_SELECTION'
        except (ValueError, PermissionError) as error:
            result.update(status='UNKNOWN_FUTURE_QUALIFICATION', smallest_obstruction=str(error))
            return result
        # This version does not silently inherit v1 constructor/profile authority.
        # It retains the real policy-selected future result, with the exact next
        # unclosed authority gate explicit rather than fabricating a second stage.
        result.update(status='BOUNDED_META_SELECTION_ONLY',
            smallest_obstruction='Versioned native v2 constructor-support and restoration correspondence not independently qualified',
            source_native_future_expansion_observed=warranted, future_2_remains_unopened=True)
        result['verdicts']['G3'] = 'UNKNOWN_UNQUALIFIED_SECOND_GENERATION_AND_CAUSAL_CONTROLS'
        result['verdicts']['G4'] = 'UNKNOWN_NO_FULL_LIFECYCLE_ADVANTAGE'
        return result
    except BaseException as error:
        result['verdicts_before_integration_error'] = dict(result['verdicts'])
        result['verdicts'].update({key: 'UNKNOWN_INTEGRATION_NOT_QUALIFIED' for key in ('G2', 'G3', 'G4')})
        result.update(status='INTEGRATION_ERROR_NOT_SCIENTIFIC_SUCCESS',
                      smallest_obstruction=type(error).__name__+': '+str(error))
        raise
    finally:
        save()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--repo'); parser.add_argument('--components')
    parser.add_argument('--source-repos'); parser.add_argument('--freeze'); parser.add_argument('--out', required=True)
    parser.add_argument('--write-freeze', action='store_true'); parser.add_argument('--catalog-spec')
    parser.add_argument('--agent-spec'); parser.add_argument('--candidate'); args = parser.parse_args()
    if args.write_freeze: result = write_freeze(args.repo, args.out)
    elif args.catalog_spec:
        spec = json.loads(Path(args.catalog_spec).read_text()); spec.pop('msi', None)
        result = catalog(**spec); Path(args.out).write_text(canonical(result)+'\n')
    elif args.agent_spec:
        arm = json.loads(Path(args.agent_spec).read_text()); candidate = json.loads(Path(args.candidate).read_text())
        result = worker.verify(arm['contract'], candidate, args.out, authority=arm['authority'],
            admission_certificate=arm['certificate'], policy=arm['policy'])
    else:
        try: result = qualify(args)
        except BaseException as error:
            out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
            partial = out/'RESULT.json'
            if partial.exists():
                retained = json.loads(partial.read_text())
                retained.setdefault('verdicts_before_integration_error', retained.get('verdicts', {}))
                retained['verdicts'] = {**retained.get('verdicts', {}), **{key: 'UNKNOWN_INTEGRATION_NOT_QUALIFIED' for key in ('G2', 'G3', 'G4')}}
                retained['status'] = 'INTEGRATION_ERROR_NOT_SCIENTIFIC_SUCCESS'
                partial.write_text(canonical(retained)+'\n')
            (out/'ERROR.json').write_text(canonical({'type': type(error).__name__, 'error': str(error)})+'\n')
            raise
    print(canonical({'status': result.get('status', result.get('schema')), 'verdicts': result.get('verdicts', {})})
              if isinstance(result, dict) else canonical({'catalog_candidates': len(result)}))


if __name__ == '__main__': main()
