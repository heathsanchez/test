"""Prepared prospective controller over independently qualified v3 environments.

No target or metadata is embedded here. The immutable v2 algorithms are rebound
into private globals, while this version owns its prospective information,
screening, budget and counterfactual boundaries. Missing gates refuse exposure.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import types

from . import qualify_native_frontier_v2 as previous
from . import native_execution_v3 as worker
from . import native_environment_v3 as environment
from .developmental_machine import Machine, canonical, digest
from .decisive_native import catalog, orders, is_test, task_roles
from .native_meta_decision import choose_meta_decision, invoke_meta_policy
from .native_runtime_v2 import AUTHORITY
from .qualify_decisive_native import copy_state

HERE = Path(__file__).resolve().parent
RECORDS = HERE/'archaeology/native-environment-v3'
PROTOCOL = RECORDS/'FRONTIER_PROTOCOL.json'
METADATA = RECORDS/'FRESH_TASK_METADATA.json'
MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v3'
AGENT_SCHEMA = 'UDM_CODING_AGENT_NATIVE_ARM_V3'
PREVIOUS_SHA256 = 'e06c148bc8fe701d703615186143f64545b26f1c338f775b87b5c0621473b9e2'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())
DEFAULTS = {
    'schema': 'UDM_NATIVE_FRONTIER_PROTOCOL_V3', 'state': 'PREPARED_NOT_FROZEN',
    'environment_gate': None, 'catalog': None,
    'metadata_sha256': None, 'pool': None, 'screening': None, 'prequery': None,
    'search_budget': 8, 'candidate_cap_per_file': 64, 'catalog_seconds': 45,
    'training_unique_calls': 128, 'acquisition_native_calls': 512,
    'training_seconds': 3600, 'per_search_seconds': 3600,
    'collection_seconds': 60, 'execution_seconds': 600,
    'future_native_reserve': 64, 'requested_roles': 2,
    'selection_ties': 'UNKNOWN; original 36-policy plus cold carrier unchanged',
    'G3': 'UNKNOWN_UNQUALIFIED_SECOND_GENERATION_AND_CAUSAL_CONTROLS',
}
NATIVE_PHASES = frozenset((
    'generic_native_v2_independent_verification', 'independent_native_v2_receipt_reexecution',
    'generic_native_v3_independent_verification', 'independent_native_v3_receipt_reexecution'))
ENVIRONMENT_GATE_FILES = tuple('research/unified_consequence_runtime/'+name+'.py' for name in (
    'native_environment_selection_v3', 'native_environment_v3', 'native_execution_v3',
    'native_runtime_v3', 'qualify_environment_selection_v3')) + (
    '.github/workflows/udm-native-environment-selection-v3.yml',
    'research/unified_consequence_runtime/archaeology/native-environment-v3/PROTOCOL.json',
    'research/unified_consequence_runtime/archaeology/native-environment-v3/ENVIRONMENT_CATALOG.json',
    'research/unified_consequence_runtime/archaeology/native-environment-v3/PACKAGE_METADATA.json',
    *(('research/unified_consequence_runtime/archaeology/native-environment-v3/bootstrap/'+name)
      for name in ('prepare_runtimes.py', 'stdlib_cache.py', 'metadata_receipt.py', 'METADATA_RECEIPT.json',
                   'official-legacy-installer.json', 'legacy-pins.txt')))


def _guard():
    if (digest(Path(previous.__file__).read_bytes()) != PREVIOUS_SHA256
            or digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('frozen prospective controller source changed')
    worker._runner_hash()


def _bound_json(record):
    if not isinstance(record, dict) or set(record) != {'path', 'sha256'}:
        raise ValueError('exact bound file descriptor required')
    root = HERE.parents[1]; path = (root/record['path']).resolve()
    if (not path.is_relative_to(root) or path.is_symlink() or not path.is_file()
            or digest(path.read_bytes()) != record['sha256']):
        raise ValueError('bound file differs: '+str(record.get('path')))
    return json.loads(path.read_text())


def _external_json(record):
    if (not isinstance(record, dict) or set(record) != {'path', 'sha256'}
            or not re.fullmatch('[0-9a-f]{64}', record.get('sha256', ''))):
        raise ValueError('exact external authority descriptor required')
    path = Path(record['path'])
    if (not path.is_absolute() or path.is_symlink() or path.resolve() != path or not path.is_file()
            or digest(path.read_bytes()) != record['sha256']):
        raise ValueError('external authority bytes differ')
    return json.loads(path.read_text())


def _write_record(path, value):
    path = Path(path).resolve(); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value)+'\n')
    return {'path': str(path), 'sha256': digest(path.read_bytes())}


def _committed_record(repo, record, commit='HEAD', *, as_json=True):
    repo = Path(repo).resolve(); path = Path(record['path'])
    path = path if path.is_absolute() else repo/path
    if path.is_symlink() or path.resolve() != path or not path.is_relative_to(repo):
        raise ValueError('authority input must be a canonical committed repository path')
    raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo),
                                   'show', commit+':'+path.relative_to(repo).as_posix()], stderr=subprocess.PIPE)
    if (digest(raw) != record['sha256'] or path.read_bytes() != raw):
        raise ValueError('authority input differs from its committed Git bytes')
    return json.loads(raw) if as_json else raw


def protocol():
    _guard()
    if not PROTOCOL.is_file():
        return copy.deepcopy(DEFAULTS)
    value = json.loads(PROTOCOL.read_text())
    if (value.get('schema') != DEFAULTS['schema']
            or value.get('search_budget') != 8 or value.get('candidate_cap_per_file') != 64
            or value.get('acquisition_native_calls') != 512 or value.get('training_seconds') != 3600
            or value.get('requested_roles') != 2):
        raise ValueError('wrong prospective v3 policy or resource boundary')
    return value


def require_environment_gate(value):
    gate = value.get('environment_gate')
    fields = {'status', 'source_commit', 'run_id', 'artifact_id', 'artifact_sha256',
              'qualification_result_sha256', 'result_path'}
    if (not isinstance(gate, dict) or set(gate) != fields
            or gate['status'] != 'ADMISSION_ONLY_QUALIFIED'
            or not re.fullmatch('[0-9a-f]{40}', gate.get('source_commit', ''))
            or any(type(gate[k]) is not int or gate[k] <= 0 for k in ('run_id', 'artifact_id'))
            or any(not re.fullmatch('[0-9a-f]{64}', gate.get(k, ''))
                   for k in ('artifact_sha256', 'qualification_result_sha256'))):
        raise ValueError('independent environment qualification is required before prospective freeze')
    result = _bound_json({'path': gate['result_path'], 'sha256': gate['qualification_result_sha256']})
    if (result.get('status') != gate['status'] or result.get('source_commit') != gate['source_commit']
            or result.get('schema') != 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V3'
            or result.get('freeze', {}).get('schema') != 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V3'
            or result.get('first_task_gate', {}).get('status') != 'PASS'
            or any(result.get('verdicts', {}).get(k) != 'UNKNOWN' for k in ('G2', 'G3', 'G4'))):
        raise ValueError('environment qualification is not a separate admission-only gate')
    qualified = result.get('freeze', {}).get('files', {})
    for name in ENVIRONMENT_GATE_FILES:
        path = HERE.parents[1]/name
        if not path.is_file() or path.is_symlink() or qualified.get(name) != digest(path.read_bytes()):
            raise ValueError('current environment bridge differs from qualified source: '+name)
    catalog = _bound_json(value['catalog'])
    if (qualified.get(value['catalog']['path']) != value['catalog']['sha256']
            or result['freeze'].get('catalog_sha256') != worker.fingerprint(catalog)):
        raise ValueError('environment qualification does not bind exact catalog')
    return gate


def freeze_runtime_inventory(runtime_paths, catalog):
    """Bind fresh runner-local identities; qualified CI paths are never reused."""
    _guard(); profiles = {row['id']: row for row in environment.selection._catalog(catalog)}
    if (not isinstance(runtime_paths, dict) or set(runtime_paths) != set(profiles)
            or any(not isinstance(path, str) or not path for path in runtime_paths.values())):
        raise ValueError('complete runner-local runtime paths required before task source access')
    runtimes = {}
    for ident in sorted(profiles):
        runtimes[ident] = environment.freeze_runtime(runtime_paths[ident])
        environment.validate_runtime(profiles[ident], runtimes[ident])
    return {'schema': 'UDM_NATIVE_FRONTIER_RUNTIME_INVENTORY_V3',
        'catalog_sha256': worker.fingerprint(catalog), 'runtime_paths_sha256': worker.fingerprint(runtime_paths),
        'runtimes': runtimes, 'authority': 'SOURCE_INDEPENDENT_RUNTIME_IDENTITY_ONLY_NO_TASK_ADMISSION'}


def validate_runtime_inventory(inventory, catalog):
    profiles = {row['id']: row for row in environment.selection._catalog(catalog)}
    if (not isinstance(inventory, dict) or inventory.get('schema') != 'UDM_NATIVE_FRONTIER_RUNTIME_INVENTORY_V3'
            or inventory.get('catalog_sha256') != worker.fingerprint(catalog)
            or set(inventory.get('runtimes', {})) != set(profiles)):
        raise ValueError('frozen runner-local runtime inventory or catalog differs')
    for ident, record in inventory['runtimes'].items(): environment.validate_runtime(profiles[ident], record)
    return inventory['runtimes']


def select_screened_roles(pool, reports, requested=2):
    """Pure fixed-order eligibility; native PASS and FAIL are equivalent here."""
    if not isinstance(pool, list) or not isinstance(reports, list) or len(pool) != len(reports):
        raise ValueError('complete ordered screening pool and all reports required')
    selected = []; seen = set()
    for spec, report in zip(pool, reports):
        if ({'candidate_catalog', 'catalog', 'orders', 'selected_policy', 'winner', 'profiles',
             'candidate', 'candidate_outcomes', 'setup', 'certificate', 'baseline', 'packet'} & set(report)):
            raise ValueError('admission-only screening contains search information')
        if (report.get('spec_sha256') != worker.fingerprint(spec)
                or report.get('repository') != spec['repo']
                or report.get('screening_mode') != 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'):
            raise ValueError('screening order, source identity or mode differs')
        eligible = report.get('status') in ('PASS_NATIVE', 'FAIL_NATIVE', 'ADMITTED_NATIVE')
        if report.get('eligible') is not eligible:
            raise ValueError('screening eligibility must treat native PASS and FAIL equally')
        repository = spec['repo'].lower()
        if eligible and repository not in seen and len(selected) < requested:
            selected.append(dict(spec, role='TRAINING' if not selected else 'PROTECTED_FUTURE_'+str(len(selected))))
            seen.add(repository)
    if len(selected) != requested:
        raise ValueError('screening shortfall; no outcome-selected replacement permitted')
    return selected


def require_screening_manifest(value):
    """Read only admission envelopes; future raw source/evidence stays sealed."""
    prequery = _bound_json(value['prequery']); pool_record = _bound_json(value['pool'])
    screening = _bound_json(value['screening']); pool = pool_record['pool']
    if (prequery.get('state') != 'PREQUERY_COMMITTED_BEFORE_QUERIES'
            or screening.get('schema') != 'UDM_ADMISSION_ONLY_SCREENING_V3'
            or screening.get('pool_sha256') != value['pool']['sha256']
            or screening.get('prequery_sha256') != value['prequery']['sha256']
            or screening.get('environment_gate') != value['environment_gate']
            or screening.get('independent_screener') is not True
            or screening.get('search_or_policy_outcomes_accessed') is not False
            or screening.get('learner_future_source_accessed') is not False):
        raise ValueError('independent precommitted admission-only screening boundary missing')
    roles = select_screened_roles(pool, screening['reports'], value['requested_roles'])
    envelope_fields = {'schema', 'repository', 'spec_sha256', 'status', 'eligible', 'screening_mode',
                       'sealed_report', 'costs', 'total_wall_seconds'}
    if any(set(row) != envelope_fields or row['status'] not in ('ADMITTED_NATIVE', 'UNKNOWN_ADMISSION_SCREENING')
           for row in screening['reports']):
        raise ValueError('learner screening manifest must contain sealed admission envelopes only')
    metadata = json.loads(METADATA.read_text())
    if digest(METADATA.read_bytes()) != value['metadata_sha256'] or metadata.get('selected') != roles:
        raise ValueError('role metadata differs from first eligible frozen source-distinct pool')
    audit = _bound_json(screening['independent_audit'])
    if (audit.get('status') != 'PASS_ADMISSION_ONLY_SCREENING_AUDIT'
            or audit.get('pool_sha256') != value['pool']['sha256']
            or audit.get('reports_sha256') != worker.fingerprint(screening['reports'])
            or audit.get('eligibility_rule') != 'PASS_NATIVE_OR_FAIL_NATIVE_IDENTICAL'
            or audit.get('all_screened_cases_and_costs_retained') is not True):
        raise ValueError('independent screening audit does not bind exact retained cases and costs')
    authority = _external_json(screening['screening_authority'])
    _committed_record(HERE.parents[1], screening['screening_authority'])
    meter = _external_json(screening['screening_meter'])
    if (authority.get('schema') != 'UDM_NATIVE_CLI_AUTHORITY_V3' or authority.get('operation') != 'screen'
            or meter.get('schema') != 'UDM_ORDERED_SCREENING_METER_V3'
            or meter.get('authority_sha256') != screening['screening_authority']['sha256']
            or meter.get('pending') is not None or meter.get('accounting_complete') is not True
            or len(meter.get('cases', [])) != len(pool)):
        raise ValueError('all predeclared pool members require complete retained ordered screening')
    for index, (spec, report, case) in enumerate(zip(pool, screening['reports'], meter['cases'])):
        if (case.get('index') != index or case.get('spec_sha256') != worker.fingerprint(spec)
                or case.get('accounting_complete') is not True or case.get('report') != report['sealed_report']):
            raise ValueError('screening envelope differs from complete ordered meter and sealed report')
    prepared_source = subprocess.check_output(['git', '--no-replace-objects', '-C', str(HERE.parents[1]),
        'show', meter['source_commit']+':research/unified_consequence_runtime/qualify_native_frontier_v3.py'])
    if digest(prepared_source) != _LOADED_SHA256:
        raise ValueError('prospective controller changed after screening source access')
    return screening


def write_freeze(repo, out, runtime_paths=None):
    value = protocol(); gate = require_environment_gate(value); screening = require_screening_manifest(value)
    if value.get('state') != 'READY_TO_FREEZE_NO_LEARNER_SOURCE_ACCESS':
        raise ValueError('prospective protocol is prepared but not ready to freeze')
    repo = Path(repo).resolve()
    from .qualify_environment_selection_v3 import freeze_source, _source_paths
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    source = freeze_source(repo, 'fa6bb190eff9b374ab7a95aaf9c618ad2db31419', _source_paths(repo, head))
    inventory = freeze_runtime_inventory(runtime_paths, _bound_json(value['catalog']))
    committed = int(subprocess.check_output(['git', '-C', str(repo), 'show', '-s', '--format=%ct', head], text=True))
    result = {'schema': 'UDM_NATIVE_FRONTIER_FREEZE_V3', **source,
        'frozen_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(committed)),
        'protocol_sha256': digest(PROTOCOL.read_bytes()), 'environment_gate': gate,
        'runtime_inventory': inventory,
        'screening_sha256': value['screening']['sha256'], 'screening_costs': screening.get('costs'),
        'prior_exposure': 'INDEPENDENT_ADMISSION_SCREENED; TRAINING_AND_FUTURES_SEALED_TO_LEARNER',
        'repeat_boundary': 'Only original pre-outcome commitments are prospective; repeats never restore untouchedness.'}
    Path(out).parent.mkdir(parents=True, exist_ok=True); Path(out).write_text(canonical(result)+'\n')
    return result


def check_freeze(repo, path):
    from .qualify_environment_selection_v3 import _source_paths, _preserved_baseline
    result = json.loads(Path(path).read_text()); repo = Path(repo); value = protocol()
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if result.get('schema') != 'UDM_NATIVE_FRONTIER_FREEZE_V3' or result.get('source_commit') != head:
        raise ValueError('prospective freeze/execution source differs')
    if (result.get('baseline_commit') != 'fa6bb190eff9b374ab7a95aaf9c618ad2db31419'
            or result.get('all_baseline_files_preserved') is not True
            or set(result.get('files', {})) != set(_source_paths(repo, head))):
        raise ValueError('prospective freeze omits exact committed source or baseline preservation')
    _preserved_baseline(repo, result['baseline_commit'], head)
    for name, expected in result['files'].items():
        raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo), 'show', head+':'+name])
        if digest(raw) != expected or (repo/name).read_bytes() != raw:
            raise ValueError('frozen v3 implementation changed or differs from committed source')
    if (result['protocol_sha256'] != digest(PROTOCOL.read_bytes())
            or require_environment_gate(value) != result['environment_gate']
            or result['screening_sha256'] != value['screening']['sha256']):
        raise ValueError('frozen v3 gate or protocol changed')
    require_screening_manifest(value)
    validate_runtime_inventory(result.get('runtime_inventory'), _bound_json(value['catalog']))
    return result


def cli_authority(path, expected_sha256, operation):
    """A source-reading CLI requires an externally pinned parent authority."""
    if not path or not expected_sha256:
        raise ValueError('external authority and its independently supplied SHA256 are required')
    value = protocol(); require_environment_gate(value)
    descriptor = {'path': str(Path(path).resolve()), 'sha256': expected_sha256}
    ticket = _external_json(descriptor)
    if (ticket.get('schema') != 'UDM_NATIVE_CLI_AUTHORITY_V3' or ticket.get('operation') != operation
            or Path(ticket.get('repo', '')).resolve() != HERE.parents[1]):
        raise ValueError('wrong external CLI authority type or repository')
    if operation == 'screen':
        _committed_record(ticket['repo'], descriptor)
        return ticket, descriptor, None
    if operation not in ('catalog', 'agent'):
        raise ValueError('unsupported external CLI authority operation')
    frozen = check_freeze(ticket['repo'], ticket['freeze']['path'])
    if digest(Path(ticket['freeze']['path']).read_bytes()) != ticket['freeze']['sha256']:
        raise ValueError('external CLI authority freeze bytes differ')
    parent = _external_json(ticket['parent'])
    if (parent.get('freeze') != ticket['freeze'] or parent.get('controller_source_sha256') != _LOADED_SHA256
            or frozen['files'].get('research/unified_consequence_runtime/qualify_native_frontier_v3.py') != _LOADED_SHA256):
        raise ValueError('external parent receipt has wrong freeze or controller lineage')
    return ticket, descriptor, parent


def _prepared_context(parent, freeze_descriptor):
    if parent.get('schema') != 'UDM_PREPARED_NATIVE_CONTEXT_V3' or parent.get('freeze') != freeze_descriptor:
        raise ValueError('wrong prepared native parent context')
    spec = parent['spec']; selected = json.loads(METADATA.read_text())['selected']
    if spec not in selected: raise ValueError('prepared source is outside exact frozen role metadata')
    release = _external_json(parent['source_release'])
    if (release.get('schema') != 'UDM_NATIVE_SOURCE_RELEASE_V3' or release.get('freeze') != freeze_descriptor
            or release.get('spec_sha256') != worker.fingerprint(spec)
            or release.get('role') != spec['role']
            or spec['role'] != 'TRAINING' and (release.get('policy_fixed') is not True
                or not release.get('policy_id') or not release.get('program'))):
        raise ValueError('prepared future source has no exact post-selection release receipt')
    setup = parent['setup']; contract = setup['contract']; bounds = setup['source_boundaries']
    if (setup['status'] != 'PREPARED' or contract['repository'] != spec['repo']
            or contract['protocol_binding'] != freeze_descriptor['sha256']
            or bounds.get('base_commit') != spec['base_commit']
            or bounds.get('author_test_head_commit') != spec['head_commit']
            or bounds.get('augmented_commit') != contract['commit']
            or bounds.get('head_production_fetched') is not False or bounds.get('production_preserved') is not True):
        raise ValueError('prepared context differs from frozen source-preserving frontier')
    identity, files, _ = worker.original._snapshot(contract['repo_path'], contract['commit'])
    if any(contract[key] != expected for key, expected in identity.items()):
        raise ValueError('prepared source identity changed')
    _, base, _ = worker.original._snapshot(contract['repo_path'], spec['base_commit'])
    tests = {row['filename']: row for row in spec['files'] if is_test(row['filename'])}
    if any(name not in files or hashlib.sha1(b'blob '+str(len(files[name])).encode()+b'\0'+files[name]).hexdigest()
           != row['sha'] for name, row in tests.items()) or files != {**base, **{name: files[name] for name in tests}}:
        raise ValueError('prepared catalog source changed production or author-test Git blobs')
    baseline = parent['baseline']
    if baseline['contract'] != contract or baseline['candidate'] != {'replacements': []}:
        raise ValueError('prepared context has wrong unrepaired native residual')
    worker.validate_receipt(contract, baseline['candidate'], setup['authority'], parent['certificate'],
                            baseline['receipt'], policy=setup['policy'], independent=False)
    return spec, setup, baseline


def catalog_request(spec, ticket, parent):
    role, setup, baseline = _prepared_context(parent, ticket['freeze'])
    expected = {'repo': setup['contract']['repo_path'], 'commit': setup['contract']['commit'],
        'production_paths': [row['filename'] for row in role['files']
                             if row['filename'].endswith('.py') and not is_test(row['filename'])],
        'triskelion': str(Path(parent['source_repos'])/'triskelion'),
        'observation': native_observation(baseline['receipt']), 'cap': 64}
    spec = dict(spec); spec.pop('msi', None)
    if spec != expected or baseline['receipt']['status'] != 'FAIL_NATIVE':
        raise ValueError('catalog request differs from exact frozen constructor source and observation')
    return expected


def screening_request(request, ticket, descriptor):
    from .qualify_environment_selection_v3 import freeze_source, _source_paths
    value = protocol()
    if ticket.get('environment_gate') != value['environment_gate']:
        raise ValueError('screening ticket has wrong qualified environment gate')
    prequery = _committed_record(ticket['repo'], ticket['prequery'])
    pool = _committed_record(ticket['repo'], ticket['pool'])
    if (prequery.get('state') != 'PREQUERY_COMMITTED_BEFORE_QUERIES'
            or pool.get('prequery_execution_sha256') != ticket['prequery']['sha256']
            or request.get('protocol_binding') != descriptor['sha256']
            or type(request.get('pool_index')) is not int or not 0 <= request['pool_index'] < len(pool['pool'])
            or request.get('spec') != pool['pool'][request['pool_index']]):
        raise ValueError('screening request differs from committed prequery, pool member, order or binding')
    commit = prequery.get('source_commit')
    if (not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit)
            or prequery.get('environment_gate') != ticket['environment_gate']
            or prequery.get('target_query_count_before_receipt') != 0):
        raise ValueError('prequery execution lacks exact source commitment and qualified query boundary')
    records = {}
    for key in ('plan', 'code', 'gate_descriptor'):
        record = prequery.get(key)
        if not isinstance(record, dict) or record.get('source_commit') != commit:
            raise ValueError('prequery plan/code/gate descriptor is not source-committed')
        records[key] = _committed_record(ticket['repo'], record, commit=commit, as_json=key != 'code')
        _committed_record(ticket['repo'], record, as_json=key != 'code')
    wrapper = records['gate_descriptor']
    if (set(wrapper) != {'environment_gate', 'catalog'} or wrapper['environment_gate'] != ticket['environment_gate']
            or wrapper['catalog'] != value['catalog']):
        raise ValueError('committed prequery gate/catalog differs from independently qualified source')
    require_environment_gate(wrapper)
    head = subprocess.check_output(['git', '-C', ticket['repo'], 'rev-parse', 'HEAD'], text=True).strip()
    source = freeze_source(ticket['repo'], 'fa6bb190eff9b374ab7a95aaf9c618ad2db31419',
                           _source_paths(ticket['repo'], head))
    output_root = Path(ticket['output_root'])
    if not output_root.is_absolute() or output_root.resolve() != output_root:
        raise ValueError('fixed canonical screening output root required')
    return pool, source, output_root


def agent_request(arm_path, ticket, parent):
    if parent.get('schema') != 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V3':
        raise ValueError('immutable external agent parent receipt required')
    arm_path = Path(arm_path).resolve(); arm = _external_json(parent['arm'])
    if str(arm_path) != parent['arm']['path']:
        raise ValueError('agent arm differs from immutable parent publication')
    prepared = _external_json(parent['prepared_context'])
    _prepared_context(prepared, ticket['freeze'])
    if (arm.get('protocol_binding') != ticket['freeze']['sha256']
            or arm.get('meter_path') != str(arm_path.parent/'ARM_METER.json')
            or arm.get('released_at_unix') != parent['released_at_unix']
            or worker.fingerprint(arm.get('common_acquisition_costs')) != parent['common_costs_sha256']
            or arm.get('common_acquisition_wall_seconds') != parent['common_wall_seconds']):
        raise ValueError('agent catalog, source, common costs or fixed meter differs from parent authority')
    meter_path = arm_path.parent/'ARM_METER.json'
    if not meter_path.is_file(): raise ValueError('published agent meter is missing; budget cannot restart')
    meter = json.loads(meter_path.read_text())
    if (meter['arm_sha256'] != worker.fingerprint(arm)
            or meter['started_at_unix'] != parent['started_at_unix']
            or meter['native_calls'] < parent['common_native_calls']):
        raise ValueError('published agent meter was reset or replayed')
    return arm


def isolated_binding(name):
    """Exact previous algorithm bytecode; never mutate previous module globals."""
    _guard(); namespace = dict(vars(previous))
    namespace.update(worker=worker, PROTOCOL=PROTOCOL, METADATA=METADATA, RECORDS=RECORDS, MODULE=MODULE,
                     protocol=protocol, acquisition_budget=acquisition_budget)
    functions = {}
    for key, value in vars(previous).items():
        if isinstance(value, types.FunctionType) and value.__module__ == previous.__name__:
            rebound = types.FunctionType(value.__code__, namespace, value.__name__, value.__defaults__, value.__closure__)
            rebound.__kwdefaults__ = value.__kwdefaults__; functions[key] = rebound
    namespace.update(functions)
    for key in ('protocol', 'acquisition_budget', 'native_probe', 'checked_record', 'bounded_catalog',
                'reconstruct_profiles', 'search', 'passed', 'native_observation'):
        if key != name: namespace[key] = globals()[key]
    return functions[name]


def _native_calls(machine):
    arm = getattr(machine, '_v3_arm', 'COMMON')
    return sum(row.get('costs', {}).get('native_calls', 0) for row in machine.costs
               if row.get('phase') in NATIVE_PHASES and row.get('arm', 'COMMON') in ('COMMON', arm))


def _attempt_snapshot():
    try: return worker.attempt_snapshot()
    except Exception: return None


def _attempt_delta(before):
    after = _attempt_snapshot(); keys = ('native_calls', 'collection_calls', 'subprocess_attempts')
    if not all(isinstance(row, dict) and all(type(row.get(key)) is int and row[key] >= 0 for key in keys)
               and row['subprocess_attempts'] == row['native_calls']+row['collection_calls']
               for row in (before, after)):
        return {}, False
    delta = {key: after[key]-before[key] for key in keys}
    return delta, all(value >= 0 for value in delta.values())


def _partial_report(path):
    """Optional recovery never prevents private launch deltas being retained."""
    raw = None
    try:
        raw = Path(path).read_bytes(); value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get('costs', {}), dict):
            raise ValueError('checked report and costs must be objects')
        costs = value.get('costs', {})
        if any(type(costs.get(key, 0)) is not int or costs.get(key, 0) < 0
               for key in ('native_calls', 'collection_calls', 'subprocess_attempts')):
            raise ValueError('invalid checked report launch counts')
        return {'sha256': digest(raw), 'costs': costs, 'valid': True}
    except (OSError, ValueError, TypeError):
        return {'sha256': digest(raw) if raw is not None else None, 'costs': {}, 'valid': False}


def acquisition_budget(machine, scope, *, reserve=True):
    arm = getattr(machine, '_v3_arm', 'COMMON')
    if any(row.get('accounting_complete') is False and row.get('arm', 'COMMON') in ('COMMON', arm)
           for row in machine.costs):
        raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING: exact charged budget is unavailable')
    value = protocol(); calls = _native_calls(machine); required = int(reserve)
    if scope.get('stage') == 'TRAINING':
        producers = sum(row.get('costs', {}).get('native_calls', 0) for row in machine.costs
                        if row.get('phase') in ('generic_native_v2_independent_verification',
                                                'generic_native_v3_independent_verification'))
        required += 4*(producers+int(reserve)) + 8 + value['future_native_reserve']
    if (calls+required > value['acquisition_native_calls']
            or time.monotonic()-scope['acquisition_started_monotonic'] >= value['training_seconds']):
        raise ValueError('UNKNOWN_SEARCH: inclusive native acquisition or verification budget exhausted')


def _tag_new_costs(machine, before, attempt_before=...):
    delta, complete = _attempt_delta(attempt_before) if attempt_before is not Ellipsis else ({}, None)
    native_rows = [row for row in machine.costs[before:] if row.get('phase') in NATIVE_PHASES]
    if complete is not None and not native_rows and (not complete or delta.get('subprocess_attempts', 0)):
        row = {'phase': 'independent_native_v2_receipt_reexecution',
               'status': 'UNKNOWN_INTERRUPTED_NATIVE_EVIDENCE', 'costs': {},
               'retained_outputs_root': str(machine.state.parent/'independent-native-profile')}
        machine.costs.append(row)
    for row in machine.costs[before:]:
        row.setdefault('arm', getattr(machine, '_v3_arm', 'COMMON'))
        if row.get('phase') in NATIVE_PHASES and row.get('output') and not row.get('costs'):
            path = Path(row['output'])/'execution/checked-report.json'
            if path.is_file(): row['costs'] = _partial_report(path)['costs']
    if complete is not None:
        rows = [row for row in machine.costs[before:] if row.get('phase') in NATIVE_PHASES]
        if complete:
            if any(not isinstance(row.get('costs', {}), dict) or any(
                    type(row.get('costs', {}).get(key, 0)) is not int or row.get('costs', {}).get(key, 0) < 0
                    for key in ('native_calls', 'collection_calls')) for row in rows):
                complete = False
            else:
                totals = {key: sum(row.get('costs', {}).get(key, 0) for row in rows)
                          for key in ('native_calls', 'collection_calls')}
                remainder = {key: max(0, delta[key]-totals[key]) for key in totals}
                if any(remainder.values()):
                    row = {'phase': 'independent_native_v2_receipt_reexecution', 'costs': remainder,
                           'status': 'UNKNOWN_INTERRUPTED_NATIVE_EVIDENCE', 'arm': getattr(machine, '_v3_arm', 'COMMON')}
                    machine.costs.append(row); rows.append(row)
        for index, row in enumerate(rows):
            row['accounting_complete'] = row.get('accounting_complete', True) and complete
            if index == 0: row['interval_controller_attempts'] = delta
    if complete is False: raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING')


def native_probe(machine, *args, **kwargs):
    before = len(machine.costs)
    try: return isolated_binding('native_probe')(machine, *args, **kwargs)
    finally: _tag_new_costs(machine, before)


def checked_record(record, machine=None, **kwargs):
    before = len(machine.costs) if machine is not None else 0; attempts = _attempt_snapshot()
    try: return isolated_binding('checked_record')(record, machine, **kwargs)
    finally:
        if machine is not None: _tag_new_costs(machine, before, attempts)
def bounded_catalog(spec, out, timeout, machine):
    execution = getattr(machine, '_v3_execution', None)
    contexts = getattr(machine, '_v3_prepared_contexts', {})
    parent = contexts.get(str(Path(spec['repo']).resolve()))
    if execution is None or parent is None:
        raise ValueError('external authority for exact prepared catalog context is required')
    ticket = _write_record(Path(out).with_suffix('.authority.json'), {
        'schema': 'UDM_NATIVE_CLI_AUTHORITY_V3', 'operation': 'catalog',
        'repo': execution['repo'], 'freeze': execution['freeze'], 'parent': parent})
    bound = isolated_binding('bounded_catalog')
    def run(argv, **kwargs):
        return subprocess.run([*argv, '--authority', ticket['path'], '--authority-sha256', ticket['sha256']], **kwargs)
    bound.__globals__['subprocess'] = types.SimpleNamespace(**{**vars(subprocess), 'run': run})
    return bound(spec, out, timeout, machine)
def search(*args, **kwargs): return isolated_binding('search')(*args, **kwargs)
def passed(receipt): return previous.passed(receipt)
def native_observation(receipt): return previous.native_observation(receipt)


def reconstruct_profiles(machine, candidates, futures, evidence_ids):
    nodes = {node.id: node for node in machine.log}
    for ident in evidence_ids:
        report = machine.get(nodes[ident].payload['report']); episode = report.get('episode', {})
        if (episode.get('within_budget') is not True or episode.get('attempts') != report['attempts']
                or episode.get('budget') != 8 or len(report['attempts']) > 8):
            raise ValueError('native profile requires exact complete in-budget episode')
    return isolated_binding('reconstruct_profiles')(machine, candidates, futures, evidence_ids)


def _check_episode(machine, episode, order, budget, *, contract=None, dependencies=None,
                   failure=False, scope=None, cache=None):
    if (not isinstance(episode, dict) or episode.get('within_budget') is not True
            or episode.get('budget') != budget or not order
            or not episode.get('attempts') or len(episode['attempts']) > min(budget, len(order))):
        return False
    receipts = []
    for index, key in enumerate(episode['attempts']):
        row = machine.get(key)
        if (worker.fingerprint(row['candidate']) != order[index]
                or contract is not None and row['contract'] != contract
                or dependencies is not None and row['producer']['dependencies'] != list(dependencies)
                or any(passed(receipt) for receipt in receipts)):
            return False
        receipts.append(checked_record(row, machine, scope=scope, cache=cache))
    if failure:
        return (episode.get('winner') is None and len(receipts) == min(budget, len(order))
                and all(row['status'] == 'FAIL_NATIVE' for row in receipts))
    return (episode.get('winner') == order[len(receipts)-1] and passed(receipts[-1])
            and all(row['status'] == 'FAIL_NATIVE' for row in receipts[:-1]))


def future_selection_warrant(machine, outcomes, cold_order, selected_order, budget, *, contract,
                             policy_id, scope=None):
    cache = {}
    return (bool(outcomes) and len(cold_order) >= budget
        and _check_episode(machine, outcomes.get('cold'), cold_order, budget, contract=contract,
                           dependencies=(), failure=True, scope=scope, cache=cache)
        and _check_episode(machine, outcomes.get('warm'), selected_order, budget, contract=contract,
                           dependencies=(policy_id,), scope=scope, cache=cache))


def operation_order(machine, policy_id, available_orders, *, binding, catalog_sha256):
    """Generic original-order dispatch when the acquired operation is absent."""
    nodes = {node.id: node for node in machine.log}
    node = nodes.get(policy_id)
    if node is None: raise ValueError('unknown acquired policy operation')
    program = machine.state/'objects'/node.payload['program']
    if not program.is_file():
        return {'status': 'ACQUIRED_OPERATION_PHYSICALLY_ABSENT', 'policy': 'COLD_V104_ORDER',
                'order': available_orders['COLD_V104_ORDER']}
    selected = invoke_meta_policy(machine, policy_id, protocol_binding=binding,
                                  candidate_catalog_sha256=catalog_sha256)
    return {'status': 'LIVE_ACQUIRED_OPERATION', 'policy': selected, 'order': available_orders[selected]}


def admission_only_screen(spec, destination, binding, *, catalog, runtimes):
    """Independent screener entrypoint: baseline only, never constructor/search."""
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic(); setup = None; receipt = None; attempts = _attempt_snapshot()
    report = {'schema': 'UDM_ADMISSION_ONLY_CASE_V3', 'repository': spec['repo'],
        'spec_sha256': worker.fingerprint(spec), 'status': 'UNKNOWN', 'eligible': False,
        'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH', 'costs': []}
    try:
        setup = environment.provision(spec, destination/'source-environment', binding,
                                      catalog=catalog, runtimes=runtimes)
        report['setup'] = setup
        if setup['status'] != 'PREPARED':
            report['status'] = setup['status']; return report
        certificate = worker.collect(setup['contract'], setup['authority'], destination/'collection', policy=setup['policy'])
        worker.validate_certificate(setup['contract'], setup['authority'], certificate,
                                    policy=setup['policy'], output_dir=destination/'independent-collection')
        receipt = worker.verify(setup['contract'], {'replacements': []}, destination/'baseline',
            authority=setup['authority'], admission_certificate=certificate, policy=setup['policy'])
        checked = worker.validate_receipt(setup['contract'], {'replacements': []}, setup['authority'],
            certificate, receipt, policy=setup['policy'], output_dir=destination/'independent-baseline', independent=True)
        report.update(status=receipt['status'], eligible=receipt['status'] in ('PASS_NATIVE', 'FAIL_NATIVE'),
                      certificate=certificate, baseline=receipt)
        report['costs'] += [receipt['costs'], checked['independent_reexecution']['costs']]
        return report
    except (ValueError, RuntimeError, OSError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        report.update(status='UNKNOWN_ADMISSION_SCREENING', reason=str(error)); return report
    finally:
        delta, complete = _attempt_delta(attempts)
        report['controller_attempts'] = delta; report['accounting_complete'] = complete
        if not complete:
            report.update(status='UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING', eligible=False)
        report['total_wall_seconds'] = time.monotonic()-started
        # Every raw directory and refusal survives even if no final receipt exists.
        report['retained_raw_directory'] = str(destination)
        report['partial_native_reports'] = []
        for path in sorted(destination.rglob('checked-report.json')):
            recovered = _partial_report(path)
            if not recovered['valid']: report.update(status='UNKNOWN_INVALID_CHECKED_REPORT', eligible=False)
            report['partial_native_reports'].append({'path': str(path), **recovered})
        (destination/'SCREENING_CASE.json').write_text(canonical(report)+'\n')


def screening_envelope(report, path):
    """Independent screener releases admission identity/costs, never future traces."""
    path = Path(path)
    if json.loads(path.read_text()) != report:
        raise ValueError('sealed screening report differs from retained bytes')
    costs = {'native_calls': 0, 'collection_calls': 0}
    for row in report.get('partial_native_reports', []):
        for key in costs: costs[key] += row.get('costs', {}).get(key, 0)
    if report.get('accounting_complete') is False:
        raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING: screening eligibility is unavailable')
    for key in costs: costs[key] = max(costs[key], report.get('controller_attempts', {}).get(key, 0))
    envelope = {'schema': 'UDM_SEALED_ADMISSION_ENVELOPE_V3',
        'repository': report['repository'], 'spec_sha256': report['spec_sha256'],
        'status': 'ADMITTED_NATIVE' if report['eligible'] else 'UNKNOWN_ADMISSION_SCREENING',
        'eligible': report['eligible'], 'screening_mode': report['screening_mode'],
        'sealed_report': {'path': str(path), 'sha256': digest(path.read_bytes())},
        'costs': costs, 'total_wall_seconds': report['total_wall_seconds']}
    (path.parent/'SCREENING_ENVELOPE.json').write_text(canonical(envelope)+'\n')
    return envelope


def execute_screening_request(request, ticket, descriptor, inventory, destination):
    pool, source, output_root = screening_request(request, ticket, descriptor)
    index = request['pool_index']; expected = output_root/('case-'+format(index, '03d'))
    if Path(destination).resolve() != expected:
        raise ValueError('screening output differs from fixed ordered case destination')
    budget = pool['screening_budget']
    if (budget['maximum_native_executions_per_case'] != 2
            or budget['collection_seconds_per_call'] != 60 or budget['execution_seconds_per_call'] != 600
            or len(pool['pool']) > budget['maximum_cases']):
        raise ValueError('screening budget differs from declared admission-only ceiling')
    output_root.mkdir(parents=True, exist_ok=True); lock = output_root/'SCREENING_METER.lock'
    try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error: raise ValueError('ordered screening execution already active') from error
    os.close(fd); path = output_root/'SCREENING_METER.json'
    try:
        meter = json.loads(path.read_text()) if path.is_file() else {
            'schema': 'UDM_ORDERED_SCREENING_METER_V3', 'authority_sha256': descriptor['sha256'],
            'source_commit': source['source_commit'], 'runtime_inventory_sha256': worker.fingerprint(inventory),
            'started_at_unix': time.time(), 'cases': [], 'native_calls': 0, 'collection_calls': 0,
            'accounting_complete': True, 'pending': None}
        if (meter['authority_sha256'] != descriptor['sha256'] or meter['source_commit'] != source['source_commit']
                or meter['runtime_inventory_sha256'] != worker.fingerprint(inventory)
                or meter['pending'] is not None or meter['accounting_complete'] is not True
                or index != len(meter['cases']) or expected.exists()
                or time.time()-meter['started_at_unix'] >= budget['total_screening_wall_seconds']):
            raise ValueError('screening order, once-only identity, interrupted accounting or budget differs')
        meter['pending'] = {'index': index, 'spec_sha256': worker.fingerprint(request['spec']), 'output': str(expected)}
        _write_record(path, meter); before = _attempt_snapshot(); report = None
        try:
            report = admission_only_screen(request['spec'], expected, descriptor['sha256'],
                catalog=_bound_json(protocol()['catalog']), runtimes=inventory['runtimes'])
        except (ValueError, RuntimeError, OSError, TypeError, AttributeError, subprocess.SubprocessError) as error:
            report = {'schema': 'UDM_ADMISSION_ONLY_CASE_V3', 'repository': request['spec']['repo'],
                'spec_sha256': worker.fingerprint(request['spec']), 'eligible': False,
                'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH',
                'status': 'UNKNOWN_INTERRUPTED_SCREENING', 'reason': str(error), 'partial_native_reports': [],
                'total_wall_seconds': time.time()-meter['started_at_unix']}
        finally:
            delta, complete = _attempt_delta(before)
            if report is None:
                meter['accounting_complete'] = False
            else:
                report['controller_attempts'] = delta; report['accounting_complete'] = complete
                if (not complete or delta.get('native_calls', 0) > 2
                        or time.time()-meter['started_at_unix'] > budget['total_screening_wall_seconds']):
                    report.update(status='UNKNOWN_SCREENING_BUDGET_OR_ACCOUNTING', eligible=False)
                _write_record(expected/'SCREENING_CASE.json', report)
                meter['accounting_complete'] = meter['accounting_complete'] and complete
                for key in ('native_calls', 'collection_calls'): meter[key] += delta.get(key, 0)
                meter['cases'].append({'index': index, 'spec_sha256': report['spec_sha256'],
                    'report': {'path': str(expected/'SCREENING_CASE.json'),
                               'sha256': digest((expected/'SCREENING_CASE.json').read_bytes())},
                    'costs': delta, 'accounting_complete': complete})
                meter['pending'] = None
            _write_record(path, meter)
        return screening_envelope(report, expected/'SCREENING_CASE.json')
    finally: lock.unlink()


def agent_arm(context, destination, binding, budget):
    execution = context.get('_execution'); prepared = context.get('_prepared_context')
    if execution is None or prepared is None:
        raise ValueError('external frozen prepared parent is required to publish an agent arm')
    if Path(destination).exists(): raise ValueError('new immutable agent arm destination required')
    released = time.time()
    value = {'schema': AGENT_SCHEMA, 'status': 'READY_NOT_EXECUTED', 'protocol_binding': binding,
        'released_at_unix': released,
        'candidate_budget': budget, 'total_acquisition_native_calls': 512,
        'total_acquisition_wall_seconds': 3600, 'native_budget_includes_independent_verification': True,
        'contract': context['setup']['contract'], 'authority': context['setup']['authority'],
        'certificate': context['certificate'], 'policy': context['setup']['policy'],
        'candidate_catalog': context.get('catalog', [{'id': worker.fingerprint({'replacements': []}),
                                                    'candidate': {'replacements': []}}]),
        'orders': context.get('orders', {}),
        'native_residual': context['baseline']['receipt'],
        'available_machinery': 'Same original V104 grammar, all original MSI orders, source, native observations and admissible history',
        'allowed_source': 'Exact base production and author-test Git blobs only; no repaired head/patch/PR body',
        'common_acquisition_costs': context.get('common_acquisition_costs', []),
        'common_acquisition_wall_seconds': context.get('common_acquisition_wall_seconds', 0),
        'meter_path': str(Path(destination).resolve().parent/'ARM_METER.json'),
        'native_command': 'python -B -m '+MODULE+' --agent-spec ARM.json --authority AGENT_AUTHORITY.json --authority-sha256 ROOT_SUPPLIED_AUTHORITY_SHA256 --candidate CANDIDATE.json --out NEW_EVIDENCE_DIR',
        'comparability': 'Independent equal 512-native-call/3600-second meters, including learning and independent verification; at most eight ordered proposals per declared search; all model/tool/lifecycle costs retained or UNKNOWN'}
    arm = _write_record(destination, value)
    common = sum(row.get('costs', {}).get('native_calls', 0) for row in value['common_acquisition_costs']
                 if row.get('phase') in NATIVE_PHASES)
    started = released-value['common_acquisition_wall_seconds']
    meter = {'schema': 'UDM_NATIVE_AGENT_METER_V3', 'arm_sha256': worker.fingerprint(value),
        'started_at_unix': started, 'native_calls': common, 'proposals': 0, 'attempts': [], 'accounting_complete': True}
    if Path(value['meter_path']).exists(): raise ValueError('agent budget meter already exists')
    _write_record(value['meter_path'], meter)
    parent = _write_record(Path(destination).with_name('AGENT_PARENT_RECEIPT.json'), {
        'schema': 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V3', 'freeze': execution['freeze'],
        'controller_source_sha256': _LOADED_SHA256, 'prepared_context': prepared, 'arm': arm,
        'released_at_unix': released, 'started_at_unix': started, 'common_native_calls': common,
        'common_costs_sha256': worker.fingerprint(value['common_acquisition_costs']),
        'common_wall_seconds': value['common_acquisition_wall_seconds']})
    ticket = _write_record(Path(destination).with_name('AGENT_AUTHORITY.json'), {
        'schema': 'UDM_NATIVE_CLI_AUTHORITY_V3', 'operation': 'agent', 'repo': execution['repo'],
        'freeze': execution['freeze'], 'parent': parent})
    return {**value, 'arm': arm, 'parent_receipt': parent, 'cli_authority': ticket,
            'execution_status': 'PENDING_ACTUAL_EXECUTION',
            'execute_command_argv': [sys.executable, '-B', '-m', MODULE, '--agent-spec', arm['path'],
                '--authority', ticket['path'], '--authority-sha256', ticket['sha256'],
                '--candidate', 'CANDIDATE.json', '--out', 'NEW_EVIDENCE_DIR']}


def execute_agent_candidate(arm, candidate, destination):
    """An atomic external meter prevents overlapping invocations losing costs."""
    meter = Path(arm.get('meter_path', Path(destination).resolve().parent/'ARM_METER.json')).resolve()
    meter.parent.mkdir(parents=True, exist_ok=True); lock = meter.with_name(meter.name+'.lock')
    try: descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError('coding-agent arm execution already active') from error
    try:
        os.write(descriptor, str(os.getpid()).encode()); os.close(descriptor)
        return _execute_agent_candidate(arm, candidate, destination)
    finally:
        lock.unlink()


def _execute_agent_candidate(arm, candidate, destination):
    """Execute an actual original-catalog proposal under a persistent arm meter."""
    if (arm.get('schema') != AGENT_SCHEMA or arm.get('candidate_budget') != 8
            or arm.get('total_acquisition_native_calls') != 512
            or arm.get('total_acquisition_wall_seconds') != 3600
            or arm.get('protocol_binding') != arm.get('contract', {}).get('protocol_binding')):
        raise ValueError('wrong frozen coding-agent arm boundary')
    rows = arm.get('candidate_catalog', []); ident = worker.fingerprint(candidate)
    if not any(row.get('id') == ident and row.get('candidate') == candidate for row in rows):
        raise ValueError('agent candidate is outside exact original catalog')
    destination = Path(destination).resolve(); destination.parent.mkdir(parents=True, exist_ok=True)
    meter_path = Path(arm.get('meter_path', destination.parent/'ARM_METER.json')).resolve()
    meter_path.parent.mkdir(parents=True, exist_ok=True); binding = worker.fingerprint(arm)
    common = sum(row.get('costs', {}).get('native_calls', 0) for row in arm.get('common_acquisition_costs', [])
                 if row.get('phase') in NATIVE_PHASES)
    meter = json.loads(meter_path.read_text()) if meter_path.is_file() else {
        'schema': 'UDM_NATIVE_AGENT_METER_V3', 'arm_sha256': binding,
        'started_at_unix': time.time()-arm.get('common_acquisition_wall_seconds', 0),
        'native_calls': common, 'proposals': 0, 'attempts': []}
    if meter.get('accounting_complete') is False:
        raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING: previous arm launches are unaccounted')
    if (meter['arm_sha256'] != binding or meter['native_calls']+2 > 512 or meter['proposals'] >= 8
            or time.time()-meter['started_at_unix'] >= 3600):
        raise ValueError('coding-agent aggregate acquisition budget exhausted or arm changed')
    if destination.exists(): raise ValueError('new agent evidence directory required')
    meter['proposals'] += 1; meter_path.write_text(canonical(meter)+'\n')
    started = time.monotonic(); receipt = None; checked = None; attempts = _attempt_snapshot(); result = None
    try:
        receipt = worker.verify(arm['contract'], candidate, destination,
            authority=arm['authority'], admission_certificate=arm['certificate'], policy=arm['policy'])
        checked = worker.validate_receipt(arm['contract'], candidate, arm['authority'], arm['certificate'], receipt,
            policy=arm['policy'], output_dir=destination/'independent-agent-check', independent=True)
        eligible = (meter['native_calls'] + receipt['costs']['native_calls']
                    + checked['independent_reexecution']['costs']['native_calls'] <= 512
                    and time.time()-meter['started_at_unix'] <= 3600)
        result = {'schema': 'UDM_NATIVE_AGENT_EXECUTION_V3', 'status': receipt['status'] if eligible
                else 'UNKNOWN_ACQUISITION_BUDGET', 'budget_eligibility': 'ELIGIBLE' if eligible else 'UNKNOWN_OVER_BUDGET',
                'native_receipt': receipt, 'independent_check': checked.get('independent_reexecution')}
        return result
    finally:
        delta, complete = _attempt_delta(attempts)
        producer_calls = receipt['costs']['native_calls'] if receipt else 0
        independent_calls = checked['independent_reexecution']['costs']['native_calls'] if checked else 0
        raw_errors = []
        for path in destination.rglob('checked-report.json'):
            recovered = _partial_report(path)
            if not recovered['valid']:
                raw_errors.append(str(path)); continue
            calls = recovered['costs'].get('native_calls', 0)
            if 'independent-agent-check' in path.parts:
                if checked is None: independent_calls += calls
            elif receipt is None: producer_calls += calls
        meter['native_calls'] += max(producer_calls+independent_calls, delta.get('native_calls', 0))
        meter['accounting_complete'] = meter.get('accounting_complete', True) and complete
        meter['attempts'].append({'candidate': ident, 'output': str(destination),
            'seconds': time.monotonic()-started, 'status': receipt.get('status') if receipt else 'UNKNOWN_INTERRUPTED',
            'controller_attempts': delta, 'accounting_complete': complete, 'invalid_raw_reports': raw_errors})
        meter['within_budget'] = meter['accounting_complete'] and meter['native_calls'] <= 512 and time.time()-meter['started_at_unix'] <= 3600
        meter_path.write_text(canonical(meter)+'\n')
        if result is not None and not meter['within_budget']:
            result.update(status='UNKNOWN_ACQUISITION_BUDGET', budget_eligibility='UNKNOWN_OVER_BUDGET')
        if result is not None and raw_errors: result.update(status='UNKNOWN_INVALID_CHECKED_REPORT')
        if not complete: raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING')


def _prepare(machine, spec, destination, binding, value, scope):
    from .native_runtime_v3 import NativeRuntimeV3
    acquisition_budget(machine, scope)
    setup = environment.provision(spec, destination, binding, catalog=_bound_json(value['catalog']),
        runtimes=value['_runtime_inventory'], collection_seconds=value['collection_seconds'],
        execution_seconds=value['execution_seconds'])
    if setup['status'] != 'PREPARED': return {'setup': setup, 'status': setup['status']}
    acquisition_budget(machine, scope)
    attempts = _attempt_snapshot(); certificate = None; checked = None
    try:
        certificate = worker.collect(setup['contract'], setup['authority'], destination/'collection', policy=setup['policy'])
        checked = worker.validate_certificate(setup['contract'], setup['authority'], certificate,
            policy=setup['policy'], output_dir=destination/'independent-collection')
    finally:
        delta, complete = _attempt_delta(attempts)
        machine.costs.append({'phase': 'native_v3_task_preparation', 'arm': getattr(machine, '_v3_arm', 'COMMON'),
            'setup': setup.get('costs', []), 'collection': certificate.get('costs') if certificate else None,
            'independent_recollection': checked['independent_recollection']['costs'] if checked else None,
            'costs': delta, 'controller_attempts': delta, 'accounting_complete': complete,
            'inclusive_not_additive': True})
        if not complete: raise ValueError('UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING')
    runtime = NativeRuntimeV3(machine, setup['contract'], setup['authority'], certificate, setup['policy'],
                              destination/'native-evidence')
    baseline = isolated_binding('budgeted_native_probe')(machine, runtime, {'replacements': []},
                                                        'unrepaired-baseline', scope)
    execution = getattr(machine, '_v3_execution', None); release = getattr(machine, '_v3_source_release', None)
    if execution is None or release is None:
        raise ValueError('prepared context requires external freeze and exact source release authority')
    parent = _write_record(destination/'PREPARED_CONTEXT.json', {
        'schema': 'UDM_PREPARED_NATIVE_CONTEXT_V3', 'controller_source_sha256': _LOADED_SHA256,
        'freeze': execution['freeze'], 'source_release': release, 'spec': spec,
        'source_repos': execution['source_repos'], 'setup': setup, 'certificate': certificate, 'baseline': baseline})
    if not hasattr(machine, '_v3_prepared_contexts'): machine._v3_prepared_contexts = {}
    machine._v3_prepared_contexts[str(Path(setup['contract']['repo_path']).resolve())] = parent
    return {'setup': setup, 'certificate': certificate, 'runtime': runtime, 'baseline': baseline,
            '_execution': execution, '_prepared_context': parent,
            'status': baseline['receipt']['status'] if baseline['budget_eligibility'] == 'ELIGIBLE'
                      else 'UNKNOWN_ACQUISITION_BUDGET'}


def physical_removal_counterfactual(machine, decision, task, context, rows, all_orders, args,
                                    destination, binding, value, scope):
    """Remove actual retained program bytes; original dispatch then rematerializes."""
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic(); before = len(machine.costs)
    shutil.copytree(machine.state, destination/'state')
    clone = Machine(Path(args.components), destination/'state', Path(args.components)/'evaluator',
                    destination/'state/unused-native-config.json')
    initialization = clone.costs
    for row in initialization: row.setdefault('arm', 'warm')
    clone.costs = [*copy.deepcopy(machine.costs), *initialization]; clone._v3_arm = 'warm'
    for name in ('_v3_execution', '_v3_source_release'):
        if hasattr(machine, name): setattr(clone, name, getattr(machine, name))
    program = clone.state/'objects'/decision['program']; removed = digest(program.read_bytes()); program.unlink()
    route = operation_order(clone, decision['policy_id'], all_orders, binding=binding,
                            catalog_sha256=decision['catalog_sha256'])
    result = {'status': 'UNKNOWN_COUNTERFACTUAL', 'removed_program_sha256': removed,
              'policy_program_absent': not program.exists(), 'route': route}
    try:
        if route['status'] != 'ACQUIRED_OPERATION_PHYSICALLY_ABSENT': return result
        rematerialized = _prepare(clone, task, destination/'rematerialized', binding, value, scope)
        result['setup'] = rematerialized['setup']; result['baseline'] = rematerialized.get('baseline')
        if rematerialized['status'] != 'FAIL_NATIVE': return result
        original = context['setup']; setup = rematerialized['setup']
        source_keys = ('repository', 'commit', 'git_tree', 'tracked_tree_sha256', 'file_count', 'protocol_binding')
        if (any(setup['contract'][key] != original['contract'][key] for key in source_keys)
                or setup['selection'] != original['selection'] or setup['runtime'] != original['runtime']):
            raise ValueError('counterfactual rematerialization changed original source or selected environment')
        episode = search(clone, rematerialized['runtime'], rows, route['order'], 8, {},
            'physical-operation-removal', seconds=value['per_search_seconds'], scope=scope,
            deadline=scope['acquisition_started_monotonic']+value['training_seconds'])
        result['episode'] = episode
        if (len(route['order']) >= 8 and _check_episode(clone, episode, route['order'], 8,
                contract=setup['contract'], dependencies=(), failure=True, scope=scope, cache={})):
            result['status'] = 'WARRANTED_BOUNDED_PHYSICAL_REMOVAL_COLD_FAILURE'
        return result
    finally:
        result['costs'] = clone.costs[before:]
        result['seconds'] = time.monotonic()-started
        result['retained_state'] = str(clone.state)
        machine.costs.extend(result['costs'])
        (destination/'COUNTERFACTUAL.json').write_text(canonical(result)+'\n')


def qualify(args):
    value = protocol(); require_environment_gate(value)
    frozen = check_freeze(args.repo, args.freeze); screening = require_screening_manifest(value)
    value = dict(value, _runtime_inventory=frozen['runtime_inventory']['runtimes'])
    binding = digest(Path(args.freeze).read_bytes()); tasks = json.loads(METADATA.read_text())['selected']
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic(); machine = None; original = b''
    result = {'schema': 'UDM_NATIVE_FRONTIER_RESULT_V3', 'source_commit': frozen['source_commit'],
        'freeze': frozen, 'freeze_sha256': binding, 'screening_costs': screening.get('costs'),
        'screening_cases': screening['reports'], 'conditions': {}, 'source_release_log': [],
        'verdicts': {'G0_G1': 'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY', 'G2': 'UNKNOWN',
            'G3': DEFAULTS['G3'], 'G4': 'UNKNOWN', 'G5': 'UNKNOWN', 'G6': 'UNKNOWN'},
        'agent_comparator': {'status': 'NOT_EXECUTED; ACTUAL_MATCHED_AGENT_REQUIRED'},
        'G2_scope': 'Bounded non-comparative native policy-order selection. Informed ledger may tie; no advantage or executed-agent claim. G4 remains UNKNOWN.',
        'additional_G3_frontier': 'NOT_SELECTED_FOR_G2; CONSTRUCTOR_CORRESPONDENCE_UNQUALIFIED',
        'cost_boundary': 'Independent equal 512-call/3600s acquisition meters per arm, including common learning and all native checks. All screened cases retained. Nested wall times nonadditive; unmeasured model/tool/engineering lifecycle costs UNKNOWN.'}
    def save():
        result['total_wall_seconds'] = time.monotonic()-started
        if machine is not None:
            for row in machine.costs:
                if row.get('phase') in NATIVE_PHASES and row.get('output') and not row.get('costs'):
                    path = Path(row['output'])/'execution/checked-report.json'
                    if path.is_file(): row['costs'] = _partial_report(path)['costs']
            result['machine_costs'] = machine.costs
            raw = (machine.state/'metatron-ledger.jsonl').read_bytes()
            result['retention'] = {'original_prefix_preserved': raw.startswith(original),
                                   'ledger_sha256': digest(raw), 'records': len(machine.log)}
        (out/'RESULT.json').write_text(canonical(result)+'\n')
    try:
        copy_state(out); original = (out/'state/metatron-ledger.jsonl').read_bytes()
        machine = Machine(Path(args.components), out/'state', Path(args.components)/'evaluator',
                          out/'state/unused-native-config.json'); machine._v3_arm = 'COMMON'
        machine._v3_execution = {'repo': str(Path(args.repo).resolve()),
            'freeze': {'path': str(Path(args.freeze).resolve()), 'sha256': binding},
            'source_repos': str(Path(args.source_repos).resolve())}
        scope = {'acquisition_started_monotonic': started, 'stage': 'PREPARE'}
        release = {'schema': 'UDM_NATIVE_SOURCE_RELEASE_V3', 'freeze': machine._v3_execution['freeze'],
                   'role': 'TRAINING', 'spec_sha256': worker.fingerprint(tasks[0]), 'policy_fixed': False}
        machine._v3_source_release = _write_record(out/'TRAINING_SOURCE_RELEASE.json', release)
        result['source_release_log'].append({**release, 'receipt': machine._v3_source_release})
        training = _prepare(machine, tasks[0], out/'training', binding, value, scope)
        result['training_setup'] = training['setup']; result['training_baseline'] = training.get('baseline')
        if training['status'] != 'FAIL_NATIVE':
            result.update(status='UNKNOWN_NO_TRAINING_NATIVE_RESIDUAL', smallest_obstruction=training['status'])
            if training.get('baseline'):
                result['conditions']['unchanged_method'] = training['baseline']
                result['conditions']['informed_ledger'] = isolated_binding('budgeted_native_probe')(
                    machine, training['runtime'], {'replacements': []}, 'informed-ledger-unrepaired', scope)
                training.update(common_acquisition_costs=copy.deepcopy(machine.costs),
                                common_acquisition_wall_seconds=time.monotonic()-started)
                result['agent_comparator'] = agent_arm(training, out/'AGENT_ARM.json', binding, 8)
            return result
        paths = [row['filename'] for row in tasks[0]['files'] if row['filename'].endswith('.py') and not is_test(row['filename'])]
        spec = {'repo': training['setup']['contract']['repo_path'], 'commit': training['setup']['contract']['commit'],
            'production_paths': paths, 'triskelion': str(Path(args.source_repos)/'triskelion'),
            'observation': native_observation(training['baseline']['receipt']), 'cap': 64}
        rows = bounded_catalog(spec, out/'training-catalog.json', value['catalog_seconds'], machine)
        all_orders = orders(rows, Path(args.source_repos)/'msi'); training.update(catalog=rows, orders=all_orders)
        context_id = machine.put({'contract': training['setup']['contract'], 'catalog': rows, 'orders': all_orders,
            'catalog_spec': dict(spec, msi=str(Path(args.source_repos)/'msi')),
            'baseline_record': training['baseline']['record'], 'source_boundaries': training['setup']['source_boundaries'],
            'runtime_source': training['runtime'].source, 'runtime_authority': training['runtime'].authority})
        scope.update(protocol_binding=binding, protocol_sha256=digest(PROTOCOL.read_bytes()),
            candidate_catalog_sha256=worker.fingerprint(rows), source_binding=worker.fingerprint(task_roles(tasks)),
            budget=8, contexts={tasks[0]['repo']: context_id},
            receipt_objects=[context_id, training['baseline']['record']], stage='TRAINING')
        cache = {}; episodes = {}; profiles = {}; evidence = []; train = tasks[0]['repo']
        for name, order in all_orders.items():
            episodes[name] = search(machine, training['runtime'], rows, order, 8, cache, 'training:'+name,
                seconds=value['per_search_seconds'], reuse=True, unique_ceiling=value['training_unique_calls'],
                deadline=started+value['training_seconds'], scope=scope)
        scope['receipt_objects'] = sorted(set(scope['receipt_objects']) | {row['record'] for row in cache.values()})
        scope['stage'] = 'VERIFY'
        for name, order in all_orders.items():
            episode = episodes[name]; attempts = episode['attempts']
            report = {'candidate': name, 'future': train, 'scope': scope, 'attempts': attempts,
                      'order': order, 'episode': episode}
            by_record = {row['record']: row['evidence'] for row in cache.values()}
            evidence.append(machine.append('native_frontier_v2_profile', {'report': machine.put(report)},
                                           tuple(by_record[key] for key in attempts)))
            receipts = [machine.get(key)['receipt'] for key in attempts]
            profiles[name] = {train: [0 if any(passed(row) for row in receipts) else 1,
                                      sum(row['costs']['native_calls'] for row in receipts)]}
        machine.flush(); result['training_episodes'] = episodes; result['training_profiles'] = profiles
        result['conditions']['unchanged_method'] = episodes['COLD_V104_ORDER']
        ledger_name = min(all_orders, key=lambda name: (profiles[name][train], name))
        result['conditions']['informed_training_ledger'] = search(machine, training['runtime'], rows,
            all_orders[ledger_name], 8, {}, 'informed-training-ledger', seconds=value['per_search_seconds'],
            scope=scope, deadline=started+value['training_seconds'])
        decision = choose_meta_decision(machine, tuple(all_orders), (train,), profiles, tuple(evidence),
            independent_check=reconstruct_profiles, source_repo=Path(args.source_repos))
        result['meta_decision'] = decision
        if decision['status'] != 'WARRANTED_BOUNDED_POLICY_SELECTION':
            training.update(common_acquisition_costs=copy.deepcopy(machine.costs),
                            common_acquisition_wall_seconds=time.monotonic()-started)
            result['agent_comparator'] = agent_arm(training, out/'AGENT_ARM.json', binding, 8)
            result.update(status='UNKNOWN_META_CHOICE', smallest_obstruction=decision.get('reason', decision['status']))
            return result
        selected = invoke_meta_policy(machine, decision['policy_id'], protocol_binding=binding,
                                      candidate_catalog_sha256=scope['candidate_catalog_sha256'])
        result['selected_policy'] = selected
        decision['catalog_sha256'] = scope['candidate_catalog_sha256']
        release = {'schema': 'UDM_NATIVE_SOURCE_RELEASE_V3', 'freeze': machine._v3_execution['freeze'],
            'spec_sha256': worker.fingerprint(tasks[1]), 'role': 'PROTECTED_FUTURE_1', 'policy_fixed': True,
            'policy_id': decision['policy_id'], 'program': decision['program'],
            'ledger_checkpoint': digest((machine.state/'metatron-ledger.jsonl').read_bytes())}
        machine._v3_source_release = _write_record(out/'FUTURE_ONE_SOURCE_RELEASE.json', release)
        result['source_release_log'].append({**release, 'receipt': machine._v3_source_release})
        scope['stage'] = 'FUTURE_PREPARE'
        future = _prepare(machine, tasks[1], out/'future-one', binding, value, scope)
        result['future_setup'] = future['setup']; result['future_baseline'] = future.get('baseline')
        if future['status'] != 'FAIL_NATIVE':
            if future.get('baseline'):
                future.update(common_acquisition_costs=copy.deepcopy(machine.costs),
                              common_acquisition_wall_seconds=time.monotonic()-started)
                result['agent_comparator'] = agent_arm(future, out/'AGENT_ARM.json', binding, 8)
            result.update(status='UNKNOWN_FUTURE_NATIVE_RESIDUAL', smallest_obstruction=future['status']); return result
        future_paths = [row['filename'] for row in tasks[1]['files'] if row['filename'].endswith('.py') and not is_test(row['filename'])]
        future_spec = dict(spec, repo=future['setup']['contract']['repo_path'], commit=future['setup']['contract']['commit'],
                           production_paths=future_paths, observation=native_observation(future['baseline']['receipt']))
        future_rows = bounded_catalog(future_spec, out/'future-catalog.json', value['catalog_seconds'], machine)
        future_orders = orders(future_rows, Path(args.source_repos)/'msi')
        common_seconds = time.monotonic()-started
        future.update(catalog=future_rows, orders=future_orders, common_acquisition_costs=copy.deepcopy(machine.costs),
                      common_acquisition_wall_seconds=common_seconds)
        result['agent_comparator'] = agent_arm(future, out/'AGENT_ARM.json', binding, 8)
        outcomes = {}; arm_scopes = {}
        for label, order in (('cold', future_orders['COLD_V104_ORDER']), ('warm', future_orders[selected]),
                             ('ledger', future_orders[selected])):
            machine._v3_arm = label
            arm_scope = dict(scope, acquisition_started_monotonic=time.monotonic()-common_seconds, stage='FUTURE')
            arm_scopes[label] = arm_scope
            outcomes[label] = search(machine, future['runtime'], future_rows, order, 8, {}, 'future:'+label,
                seconds=value['per_search_seconds'], scope=arm_scope,
                deadline=arm_scope['acquisition_started_monotonic']+value['training_seconds'],
                dependencies=(decision['policy_id'],) if label == 'warm' else ())
        result['future_results'] = outcomes; machine._v3_arm = 'warm'; warm_scope = arm_scopes['warm']
        # Exclude elapsed comparator time from this arm's deadline, preserving its own measured time.
        warm_scope['acquisition_started_monotonic'] += outcomes['ledger']['seconds']
        if not future_selection_warrant(machine, outcomes, future_orders['COLD_V104_ORDER'], future_orders[selected],
                8, contract=future['setup']['contract'], policy_id=decision['policy_id'], scope=warm_scope):
            result.update(status='UNKNOWN_FUTURE_COUNTERFACTUAL', smallest_obstruction='No exact independent cold-fail/selected-pass frontier'); return result
        removal = physical_removal_counterfactual(machine, decision, tasks[1], future, future_rows, future_orders,
            args, out/'physical-policy-removal', binding, value, warm_scope)
        result['physical_removal'] = removal
        if removal['status'] != 'WARRANTED_BOUNDED_PHYSICAL_REMOVAL_COLD_FAILURE':
            result.update(status='UNKNOWN_PHYSICAL_POLICY_COUNTERFACTUAL', smallest_obstruction=removal['status']); return result
        acquisition_budget(machine, warm_scope, reserve=3)
        candidate = next(row['candidate'] for row in future_rows if row['id'] == outcomes['warm']['winner'])
        before = len(machine.costs)
        try:
            capability = future['runtime'].admit(candidate, dependencies=(decision['policy_id'],))
            receipt, consequence = future['runtime'].execute(capability)
        finally: _tag_new_costs(machine, before)
        acquisition_budget(machine, warm_scope, reserve=False)
        result['future_admission'] = {'capability': capability, 'receipt': receipt, 'consequence': consequence}
        if not passed(receipt): raise ValueError('fresh admitted future execution is not native PASS')
        result['verdicts']['G2'] = 'WARRANTED_BOUNDED_PROSPECTIVE_NATIVE_POLICY_SELECTION'
        result.update(status='BOUNDED_NATIVE_POLICY_SELECTION_ONLY',
            smallest_obstruction='Versioned constructor-support/restoration correspondence remains unqualified')
        return result
    except (ValueError, RuntimeError, OSError, TypeError, AttributeError, PermissionError, subprocess.SubprocessError) as error:
        result.update(status='UNKNOWN_QUALIFICATION_OBSTRUCTION', smallest_obstruction=type(error).__name__+': '+str(error))
        result['verdicts']['G2'] = 'UNKNOWN'; return result
    finally: save()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--repo'); parser.add_argument('--components')
    parser.add_argument('--source-repos'); parser.add_argument('--freeze'); parser.add_argument('--out', required=True)
    parser.add_argument('--write-freeze', action='store_true'); parser.add_argument('--catalog-spec')
    parser.add_argument('--agent-spec'); parser.add_argument('--candidate'); parser.add_argument('--screen-spec')
    parser.add_argument('--runtimes'); parser.add_argument('--catalog')
    parser.add_argument('--write-runtime-inventory', action='store_true')
    parser.add_argument('--authority'); parser.add_argument('--authority-sha256')
    args = parser.parse_args()
    if args.write_runtime_inventory:
        if not args.runtimes or not args.catalog: parser.error('--runtimes and --catalog are required')
        result = freeze_runtime_inventory(json.loads(Path(args.runtimes).read_text()),
                                          json.loads(Path(args.catalog).read_text()))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(canonical(result)+'\n')
    elif args.write_freeze:
        if not args.runtimes: parser.error('--runtimes is required before any task source access')
        result = write_freeze(args.repo, args.out, json.loads(Path(args.runtimes).read_text()))
    elif args.catalog_spec:
        ticket, _, parent = cli_authority(args.authority, args.authority_sha256, 'catalog')
        spec = catalog_request(json.loads(Path(args.catalog_spec).read_text()), ticket, parent)
        result = catalog(**spec); Path(args.out).write_text(canonical(result)+'\n')
    elif args.agent_spec:
        ticket, _, parent = cli_authority(args.authority, args.authority_sha256, 'agent')
        result = execute_agent_candidate(agent_request(args.agent_spec, ticket, parent),
                                         json.loads(Path(args.candidate).read_text()), args.out)
    elif args.screen_spec:
        ticket, descriptor, _ = cli_authority(args.authority, args.authority_sha256, 'screen')
        value = protocol()
        if not args.runtimes: parser.error('--runtimes is required before screening source access')
        inventory = freeze_runtime_inventory(json.loads(Path(args.runtimes).read_text()), _bound_json(value['catalog']))
        inventory_path = Path(args.out).with_name(Path(args.out).name+'.RUNTIME_INVENTORY.json')
        inventory_path.parent.mkdir(parents=True, exist_ok=True); inventory_path.write_text(canonical(inventory)+'\n')
        request = json.loads(Path(args.screen_spec).read_text())
        result = execute_screening_request(request, ticket, descriptor, inventory, args.out)
    else: result = qualify(args)
    print(canonical({'status': result.get('status', result.get('schema')), 'verdicts': result.get('verdicts', {})})
          if isinstance(result, dict) else canonical({'catalog_candidates': len(result)}))


if __name__ == '__main__': main()
