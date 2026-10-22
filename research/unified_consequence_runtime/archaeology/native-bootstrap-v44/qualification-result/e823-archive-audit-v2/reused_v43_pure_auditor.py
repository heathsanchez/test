"""Independent read-only V43 archive audit; never execute archived source.

Regular archive bytes are cached under their SHA256, never at archive paths.
Links are inventoried but never followed or extracted. Scientific G2--G6 stay
UNKNOWN: this checks the declared native-interface qualification only.
"""
from __future__ import annotations

import argparse
import ast
import base64
import collections
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import zlib

BASE = '8c1ff8db64415b9ce6db865f2744f40a866293c9'
BRANCH = 'research/udm-experiment-interface-v43-20261022'
WORKFLOW = '.github/workflows/udm-experiment-interface-v43.yml'
PREFIX = 'research/unified_consequence_runtime/'
CONTROL_COUNTS = {'test_native_build_v43.py': 56, 'test_native_execution_v43.py': 20,
    'test_native_build_boundary_v43.py': 13, 'test_native_execution_controls_v43.py': 11,
    'test_native_materialization_v43.py': 3, 'test_native_materialization_lineage_v43.py': 1,
    'test_qualify_native_frontier_v43.py': 8}
EXTRA_REQUIRED = ('test_controller_setup_preflight_v43.py',)


def canonical(value, *, ascii=True):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=ascii,
                      allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fp(value):
    return sha(canonical(value).encode())


def object_id(kind, raw):
    return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def safe_name(name):
    if not isinstance(name, str) or not name or '\x00' in name or '\\' in name:
        return False
    p = PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and p.as_posix() == name.rstrip('/')


def hash_stream(stream):
    h = hashlib.sha256()
    while chunk := stream.read(1024*1024):
        h.update(chunk)
    return h.hexdigest()


def junit(raw):
    result = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    if not raw:
        return result
    for case in ET.fromstring(raw).iter('testcase'):
        result['tests'] += 1
        category = next((key for key, tag in (('errors', 'error'), ('failures', 'failure'),
                         ('skipped', 'skipped')) if case.find(tag) is not None), 'passed')
        result[category] += 1
    return result


def native_status(data, counts, collection):
    """Reconstruct native outcomes without importing any producer function."""
    if data.get('timeout'):
        return 'UNKNOWN_TIMEOUT'
    if any(data.get(key) for key in ('source_mutations', 'unexpected_imports',
            'external_project_imports', 'changed_test_code', 'plugin_violations')):
        return 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    if (any(data.get(key) != collection[key] for key in ('collected_test_nodes',
            'selected_test_nodes', 'plugin_manifest', 'test_items'))
            or data.get('deselected_test_nodes') or data.get('collection_errors')):
        return 'UNKNOWN_EXACT_COLLECTION'
    nodes, rows = collection['selected_test_nodes'], data.get('reports', [])
    if not nodes or any(not isinstance(row, dict) or set(row) != {'nodeid', 'when', 'outcome', 'wasxfail'}
            or row['when'] not in ('setup', 'call', 'teardown')
            or row['outcome'] not in ('passed', 'failed', 'skipped')
            or not isinstance(row['wasxfail'], str) for row in rows):
        return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
    if counts['skipped'] or any(row['wasxfail'] or row['outcome'] == 'skipped' for row in rows):
        return 'UNKNOWN_SKIPPED_OR_XFAIL'
    phases = {phase: [row for row in rows if row['when'] == phase]
              for phase in ('setup', 'call', 'teardown')}
    if (any([row['nodeid'] for row in phase] != nodes for phase in phases.values())
            or any(row['outcome'] != 'passed' for phase in ('setup', 'teardown') for row in phases[phase])
            or counts['tests'] != len(nodes) or counts['errors']
            or counts['passed'] != sum(row['outcome'] == 'passed' for row in phases['call'])
            or counts['failures'] != sum(row['outcome'] == 'failed' for row in phases['call'])):
        return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
    if counts['failures'] and data.get('process_exit_code') == 1:
        return 'FAIL_NATIVE'
    if counts['passed'] == len(nodes) and data.get('process_exit_code') == 0:
        return 'PASS_NATIVE'
    return 'UNKNOWN_NATIVE_ERROR'


class Checks:
    def __init__(self):
        self.rows = []

    def __call__(self, name, ok, detail=None):
        row = {'check': name, 'pass': bool(ok)}
        if detail is not None:
            row['detail'] = detail
        self.rows.append(row)
        return bool(ok)


class Store:
    """Safe regular-member access; archive links can never become host paths."""
    def __init__(self, cache):
        self.cache, self.entries = Path(cache), {}
        self.cache.mkdir(parents=True, exist_ok=True)

    def add(self, member, stream=None):
        name = member.name
        if not safe_name(name) or name in self.entries:
            raise ValueError('unsafe or duplicate archive member: '+repr(name))
        if member.issym():
            self.entries[name] = {'kind': 'symlink', 'target': member.linkname,
                                  'mode': member.mode, 'size': member.size}
            return
        if not member.isfile():
            raise ValueError('unsupported archive member kind: '+repr(name))
        h = hashlib.sha256()
        temporary = self.cache/('incoming-'+str(len(self.entries)))
        with temporary.open('xb') as output:
            while chunk := stream.read(1024*1024):
                h.update(chunk)
                output.write(chunk)
        digest = h.hexdigest()
        destination = self.cache/digest
        if destination.exists():
            temporary.unlink()
        else:
            temporary.replace(destination)
        self.entries[name] = {'kind': 'file', 'sha256': digest, 'mode': member.mode,
                              'size': member.size, 'cache': str(destination)}

    def raw(self, name):
        entry = self.entries[name]
        if entry['kind'] != 'file':
            raise ValueError('refusing archive link or other nonregular member: '+name)
        return Path(entry['cache']).read_bytes()

    def js(self, name):
        return json.loads(self.raw(name))

    def matching(self, suffix):
        return sorted(name for name in self.entries if name == suffix or name.endswith('/'+suffix))

    def one(self, suffix):
        matches = self.matching(suffix)
        if len(matches) != 1:
            raise ValueError('expected one archived '+suffix+', got '+repr(matches))
        return matches[0]

    def path_for_absolute(self, path):
        matches = [name for name, entry in self.entries.items()
                   if path == name or path.endswith('/'+name)]
        if len(matches) != 1:
            raise ValueError('absolute artifact does not map uniquely to archive: '+str(path))
        return matches[0]


def index_snapshot(repo, out, label):
    repo = Path(repo).absolute()
    marker = repo/'.git'
    if marker.is_dir():
        admin = marker.resolve()
    else:
        value = marker.read_text().strip()
        if not value.startswith('gitdir: '):
            raise ValueError('invalid Git administration marker')
        p = Path(value[8:])
        admin = (p if p.is_absolute() else repo/p).resolve()
    common = (admin/(admin/'commondir').read_text().strip()).resolve() if (admin/'commondir').is_file() else admin
    paths = {common/'index', admin/'index'}
    if (common/'worktrees').exists():
        paths.update(child/'index' for child in (common/'worktrees').iterdir())
    if os.environ.get('GIT_INDEX_FILE'):
        p = Path(os.environ['GIT_INDEX_FILE'])
        paths.add(p if p.is_absolute() else repo/p)
    destination = Path(out)/label
    destination.mkdir()
    rows = []
    for number, p in enumerate(sorted(paths)):
        if p.is_symlink():
            raise ValueError('Git index is unexpectedly a symlink')
        raw = p.read_bytes() if p.exists() else None
        rows.append({'path': str(p), 'exists': raw is not None,
                     'sha256': None if raw is None else sha(raw),
                     'size_bytes': None if raw is None else len(raw)})
        if raw is not None:
            (destination/f'index-{number}.bytes').write_bytes(raw)
    (destination/'SNAPSHOT.json').write_text(canonical(rows)+'\n')
    return rows


def git(repo, *args):
    return subprocess.check_output(['git', '--no-pager', '--no-replace-objects',
        '-c', 'core.fsmonitor=false', '-C', str(repo), *args],
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), stderr=subprocess.PIPE, timeout=120)


def git_tree(repo, commit):
    rows = {}
    for row in git(repo, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        rows[name.decode()] = {'mode': mode, 'kind': kind, 'oid': oid}
    return rows


def fetch_api(path, out):
    url = 'https://api.github.com/repos/heathsanchez/test/'+path
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'UDM-V43-independent-archive-auditor'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
        headers = {key: response.headers.get(key) for key in ('Date', 'ETag', 'X-GitHub-Request-Id')}
    Path(out).write_bytes(raw)
    return json.loads(raw), {'url': url, 'sha256': sha(raw), 'headers': headers}


def archive_identity(args, check, out):
    run, run_receipt = fetch_api(f'actions/runs/{args.run}', out/'API_RUN.json')
    listing, list_receipt = fetch_api(f'actions/runs/{args.run}/artifacts?per_page=100', out/'API_ARTIFACTS.json')
    artifacts = [row for row in listing['artifacts'] if row['id'] == args.artifact]
    check('api_exact_artifact_found', len(artifacts) == 1)
    if len(artifacts) != 1:
        raise ValueError('exact requested artifact not found on independent GitHub API read')
    artifact = artifacts[0]
    check('api_run_identity', run['id'] == args.run and run['head_sha'] == args.source
          and run['head_branch'] == BRANCH and run['path'] == WORKFLOW)
    check('api_run_green', run['status'] == 'completed' and run['conclusion'] == 'success')
    check('api_owned_isolated_event', run['event'] in ('push', 'workflow_dispatch')
          and run['repository']['full_name'] == 'heathsanchez/test')
    check('api_artifact_identity', not artifact['expired']
          and artifact['workflow_run']['id'] == args.run
          and artifact['workflow_run']['head_sha'] == args.source
          and artifact['workflow_run']['head_branch'] == BRANCH
          and artifact['name'] == f'experiment-interface-v43-{args.source}-{run["run_attempt"]}')
    with args.zip.open('rb') as stream:
        digest = hash_stream(stream)
    check('api_artifact_size', args.zip.stat().st_size == artifact['size_in_bytes'])
    check('api_artifact_digest', artifact.get('digest') == 'sha256:'+digest)
    return {'run': run, 'artifact': artifact, 'run_fetch': run_receipt,
            'artifact_fetch': list_receipt, 'zip_sha256': digest}


def load_archive(args, check, out):
    source, evidence = Store(out/'source-by-sha256'), Store(out/'evidence-by-sha256')
    with zipfile.ZipFile(args.zip) as packet:
        names = packet.namelist()
        check('zip_unique_safe_members', len(names) == len(set(names)) and all(safe_name(name) for name in names))
        check('zip_crc', packet.testzip() is None)
        def one(name):
            matches = [item for item in names if item == name or item.endswith('/'+name)]
            if len(matches) != 1:
                raise ValueError('expected one ZIP '+name)
            return matches[0]
        manifest = json.loads(packet.read(one('MANIFEST.json')))
        check('archive_manifest_identity', manifest['schema'] == 'UDM_EXPERIMENT_INTERFACE_ARCHIVE_MANIFEST_V43'
              and manifest['source_commit'] == args.source and str(manifest['run_id']) == str(args.run))
        for name, store, expected in [('SOURCE.tar.gz', source, manifest['source_sha256']),
                ('EXPERIMENT_INTERFACE_V43_EVIDENCE.tar.gz', evidence, manifest['archive_sha256'])]:
            with packet.open(one(name)) as raw:
                check(name+'_sha256', hash_stream(raw) == expected)
            with packet.open(one(name)) as raw:
                with tarfile.open(fileobj=raw, mode='r|gz') as archive:
                    for member in archive:
                        if member.isdir():
                            if not safe_name(member.name):
                                raise ValueError('unsafe archive directory')
                            continue
                        store.add(member, archive.extractfile(member) if member.isfile() else None)
                    if name == 'SOURCE.tar.gz':
                        check('source_git_archive_commit', archive.pax_headers.get('comment') == args.source)
        actual = {name: {key: value for key, value in entry.items()
                         if key in ('kind', 'sha256', 'target')} for name, entry in evidence.entries.items()}
        check('complete_evidence_manifest', actual == manifest['files'],
              {'actual_count': len(actual), 'manifest_count': len(manifest['files'])})
        embedded = evidence.js('run/RESULT.json')
        check('zip_result_equals_evidence', embedded == json.loads(packet.read(one('run/RESULT.json'))))
    return source, evidence, manifest


def audit_source(args, source, evidence, check, out, control_counts):
    tree, baseline = git_tree(args.repo, args.source), git_tree(args.repo, BASE)
    commit_raw = git(args.repo, 'cat-file', 'commit', args.source)
    check('commit_git_object_sha', object_id('commit', commit_raw) == args.source)
    freeze = evidence.js('FREEZE.json')
    check('freeze_exact_identity', freeze['schema'] == 'UDM_EXPERIMENT_INTERFACE_FREEZE_V43'
          and freeze['source_commit'] == args.source and freeze['mode'] == 'whole'
          and freeze['scope'] == 'NATIVE_INTERFACE_INFRASTRUCTURE_ONLY')
    check('freeze_science_separate', all(freeze['scientific_verdicts'][f'G{i}'] == 'UNKNOWN' for i in range(2, 7)))
    hashes, mismatches = {}, []
    for name, row in tree.items():
        entry = source.entries.get(name)
        if entry is None or row['kind'] != 'blob' or entry['kind'] != 'file':
            mismatches.append(name)
            continue
        raw = source.raw(name)
        hashes[name] = sha(raw)
        mode = '100'+format(entry['mode'], '03o')
        if object_id('blob', raw) != row['oid'] or mode != row['mode']:
            mismatches.append(name)
    check('source_exact_git_inventory_bytes_modes', not mismatches and set(source.entries) == set(tree), mismatches)
    check('source_full_freeze_hashes', hashes == freeze['files'])
    check('all_2361_baseline_objects_modes_preserved', len(baseline) == 2361
          and all(tree.get(name) == row for name, row in baseline.items()))
    descriptor = source.js(PREFIX+'archaeology/experiment-interface-v43/preimplementation/TEST_FREEZE.json')
    check('core_preimplementation_red', descriptor['counts'] == {
        'tests': 76, 'failures': 68, 'passed': 8, 'errors': 0, 'skipped': 0} and descriptor['returncode'] == 1)
    for name, expected in descriptor['files_sha256'].items():
        check('original_core_test_bytes:'+name, hashes.get(name) == expected)
    for name, expected in descriptor['artifacts_sha256'].items():
        path = PREFIX+'archaeology/experiment-interface-v43/preimplementation/'+name
        check('original_core_red_bytes:'+name, hashes.get(path) == expected)
    for name in control_counts:
        check('mandatory_control_frozen:'+name, freeze['tests'].get(PREFIX+name) == hashes.get(PREFIX+name))
    (out/'GIT_SOURCE_TREE.json').write_text(canonical(tree)+'\n')
    return freeze, hashes


def audit_controls(source, evidence, check, control_counts):
    result = evidence.js('run/RESULT.json')
    check('whole_gate_result', result['schema'] == 'UDM_EXPERIMENT_INTERFACE_QUALIFICATION_V43'
          and result['status'] == 'QUALIFIED_BOUNDED_CAUSAL_NATIVE_INTERFACE_ONLY' and result['mode'] == 'whole')
    check('no_scientific_promotion', all(result['verdicts'][f'G{i}'] == 'UNKNOWN' for i in range(2, 7))
          and result['prospective_task_sources_accessed'] is False and result['coding_agent_executed'] is False
          and result['external_enforcement'] == 'UNKNOWN_NONBYPASSABILITY')
    inventory = evidence.js('run/PYTEST_INVENTORY.json')
    check('pytest_inventory_matches_result', inventory == result['contracts'])
    xml = evidence.raw('run/contracts.xml')
    counts = junit(xml)
    check('pytest_actual_zero_failure_skip', result['pytest_exit_code'] == 0
          and counts == inventory['junit'] and counts['tests'] == sum(control_counts.values())
          and not any(counts[key] for key in ('failures', 'errors', 'skipped')))
    collected, reports = inventory['collection'], inventory['reports']
    check('pytest_complete_unique_collection', len(collected) == len(set(collected)) == counts['tests'])
    for filename, expected_count in control_counts.items():
        names = [node for node in collected if node.startswith(PREFIX+filename+'::')]
        check('test_count:'+filename, len(names) == expected_count)
        module = ast.parse(source.raw(PREFIX+filename))
        definitions = {node.name for node in module.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and node.name.startswith('test_')}
        executed = {node.split('::', 1)[1].split('[', 1)[0] for node in names}
        check('every_test_definition_executed:'+filename, definitions == executed)
    for phase in ('setup', 'call', 'teardown'):
        rows = [row for row in reports if row['when'] == phase]
        check('pytest_complete_phase:'+phase, [row['nodeid'] for row in rows] == collected
              and all(row['outcome'] == 'passed' and not row['wasxfail'] for row in rows))
    prior_xml = source.raw(PREFIX+'archaeology/experiment-interface-v43/preimplementation/junit.xml')
    old_names = sorted((case.attrib['classname'].replace('.', '/')+'.py::'+case.attrib['name'])
                       for case in ET.fromstring(prior_xml).iter('testcase'))
    actual_core = sorted(node for node in collected if any(node.startswith(PREFIX+name+'::')
                         for name in ('test_native_build_v43.py', 'test_native_execution_v43.py')))
    check('all_original_76_case_ids_preserved', old_names == actual_core)
    inherited = evidence.js('run/inherited-controls/controls/result.json')
    log = evidence.raw('run/inherited-controls/controls/unittest.log').decode()
    check('all_27_original_adversarial_statements_executed', inherited['status'] == 'PASS'
          and inherited['tests'] == 27 and not inherited['failures'] and not inherited['errors']
          and inherited['test_method_code_objects_unchanged'] is True
          and sum(line.endswith(' ... ok') for line in log.splitlines()) == 27
          and 'Ran 27 tests' in log and log.rstrip().endswith('OK'))
    original_raw = source.raw(PREFIX+'test_native_admission_v2_adversarial.py')
    original_ast = ast.parse(original_raw)
    original_class = next(node for node in original_ast.body if isinstance(node, ast.ClassDef)
                          and node.name == 'NativeAdmissionV2AdversarialTests')
    methods = [node for node in original_class.body if isinstance(node, ast.FunctionDef)
               and not any(isinstance(decorator, ast.Name) and decorator.id == 'classmethod'
                           for decorator in node.decorator_list)]
    method_names = {node.name for node in methods if node.name.startswith('test_')}
    executed_names = [line.split(' ', 1)[0] for line in log.splitlines() if line.endswith(' ... ok')]
    check('inherited_exact_original_test_method_ids', len(method_names) == 27
          and len(executed_names) == len(set(executed_names)) == 27 and set(executed_names) == method_names)
    lines = original_raw.splitlines(keepends=True)
    method_hashes = {node.name: sha(b''.join(lines[node.lineno-1:node.end_lineno])) for node in methods}
    check('inherited_exact_original_method_source_hashes', method_hashes == inherited['original_method_source_sha256'])
    provenance = evidence.js('run/inherited-controls/controls/provenance.json')
    check('inherited_retained_provenance_binding', all(inherited[key] == item for key, item in provenance.items()))
    check('inherited_original_source_byte_identity', sha(evidence.raw('run/inherited-controls/controls/original-test-source.py'))
          == inherited['original_test_source_sha256']
          == sha(source.raw(PREFIX+'test_native_admission_v2_adversarial.py')))
    check('inherited_runner_byte_identity', sha(evidence.raw('run/inherited-controls/controls/runner-source.py'))
          == inherited['runner_sha256'] == sha(source.raw(PREFIX+'native_inherited_controls_v43.py')))
    return result


def packet(value, check, label):
    decoded = {name: base64.b64decode(raw, validate=True) for name, raw in value['packet'].items()}
    check('packet_hashes:'+label, {name: sha(raw) for name, raw in decoded.items()} == value['packet_sha256'])
    return decoded


def audit_native(source, evidence, freeze, check):
    runner = sha(source.raw(PREFIX+'native_execution_v43.py'))
    environments = [row['environment'] for row in freeze['profile_identities'].values()]
    if 'run/RESULT.json' in evidence.entries:
        environments.append(evidence.js('run/RESULT.json')['controller_environment'])
    certs, certificates, receipts = {}, [], []
    certificate_versions, receipt_versions = collections.Counter(), collections.Counter()
    fields = {'process_exit_code', 'timeout', 'source_mutations', 'unexpected_imports', 'costs'}
    for name in evidence.matching('admission-certificate.json'):
        value = evidence.js(name)
        schema = value.get('schema')
        if schema not in ('UDM_NATIVE_ADMISSION_CERTIFICATE_V43', 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42'):
            continue
        version = '43' if schema.endswith('_V43') else '42'
        expected_runner = sha(source.raw(PREFIX+'native_execution_v'+version+'.py'))
        raw = packet(value, check, name)
        data = json.loads(raw['checked-report.json'])
        producer = json.loads(raw['report.json'])
        folder = name.rsplit('/', 1)[0]
        check('certificate_runner:'+name, value['runner_sha256'] == expected_runner)
        check('certificate_known_environment:'+name, value['environment'] in environments)
        check('certificate_raw_checked:'+name, producer == {key: item for key, item in data.items() if key not in fields})
        check('certificate_retained_packet:'+name, all(evidence.raw(folder+'/'+key) == item for key, item in raw.items()))
        collection = value['collection']
        check('certificate_actual_collection:'+name, {key: data[key] for key in collection} == collection
              and data.get('mode') == 'collect' and data.get('process_exit_code') == 0
              and data.get('exit_code') == 0 and not data.get('timeout')
              and data['costs']['collection_calls'] == 1 and data['costs']['native_calls'] == 0)
        check('certificate_complete_collection:'+name, bool(collection['selected_test_nodes'])
              and len(collection['selected_test_nodes']) == len(collection['collected_test_nodes'])
              and set(collection['selected_test_nodes']) == set(collection['collected_test_nodes'])
              and len(set(collection['collected_test_nodes'])) == len(collection['collected_test_nodes'])
              and not any(data.get(key) for key in ('deselected_test_nodes', 'collection_errors',
                  'source_mutations', 'unexpected_imports', 'external_project_imports', 'plugin_violations')))
        check('certificate_pytest_import:'+name, data['pytest_import'] == value['environment']['pytest_import'])
        certificate_versions[version] += 1
        certs[fp(value)] = value
        certificates.append({'path': name, 'sha256': fp(value), 'nodes': collection['selected_test_nodes']})
    for name in evidence.matching('receipt.json'):
        value = evidence.js(name)
        schema = value.get('schema')
        if schema not in ('UDM_GENERIC_NATIVE_PYTEST_V43', 'UDM_GENERIC_NATIVE_PYTEST_V42'):
            continue
        version = '43' if schema.endswith('_V43') else '42'
        expected_runner = sha(source.raw(PREFIX+'native_execution_v'+version+'.py'))
        raw = packet(value, check, name)
        data, producer = json.loads(raw['checked-report.json']), json.loads(raw['report.json'])
        counts = junit(raw.get('native.xml'))
        certificate = certs.get(value['certificate_sha256'])
        folder = name.rsplit('/', 1)[0]
        check('native_source_runner:'+name, value['runner_sha256'] == expected_runner and certificate is not None)
        if certificate is None:
            continue
        inferred = native_status(data, counts, certificate['collection'])
        check('native_independent_status:'+name, value['execution'] == data and value['junit'] == counts
              and value['status'] == inferred)
        check('native_raw_checked:'+name, producer == {key: item for key, item in data.items() if key not in fields})
        check('native_packet_retained:'+name, all(evidence.raw(folder+'/execution/'+key) == item for key, item in raw.items()))
        check('native_binding:'+name, all(value[key] == certificate[key] for key in
            ('runner_sha256', 'policy_sha256', 'contract_sha256', 'authority_sha256', 'environment', 'plugins')))
        recollection = evidence.js(folder+'/independent-collection/checked-report.json')
        check('native_actual_recollection:'+name, recollection['mode'] == 'collect'
              and recollection['costs']['collection_calls'] == 1 and recollection['costs']['native_calls'] == 0
              and {key: recollection[key] for key in certificate['collection']} == certificate['collection'])
        check('native_actual_execution:'+name, data['mode'] == 'run' and data['costs']['native_calls'] == 1
              and data['costs']['collection_calls'] == 0)
        receipt_versions[version] += 1
        receipts.append({'path': name, 'sha256': fp(value), 'version': version, 'status': inferred, 'junit': counts,
                         'source_manifest': json.loads(raw['tracked-source-manifest.json'])})
    check('native_required_version_coverage', all(certificate_versions[v] > 0 and receipt_versions[v] > 0 for v in ('42', '43')),
          {'certificates': dict(certificate_versions), 'receipts': dict(receipt_versions)})
    check('native_real_pass_and_fail', any(row['status'] == 'PASS_NATIVE' and row['junit']['passed'] == 2 for row in receipts)
          and any(row['status'] == 'FAIL_NATIVE' and row['junit']['failures'] >= 1 for row in receipts))
    return {'runner_sha256': runner, 'certificates': certificates, 'receipts': receipts,
            'status_counts': dict(collections.Counter(row['status'] for row in receipts)),
            'boundary': 'All retained native packet outcomes reconstructed; exact candidate/import context additionally checked for the explicit native-context supplement.'}


def wheel_members(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as wheel:
        names = wheel.namelist()
        if len(names) != len(set(names)) or any(not safe_name(name) for name in names):
            raise ValueError('unsafe or duplicate native wheel member')
        result = {}
        for info in wheel.infolist():
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('native wheel contains a symlink')
            if not info.is_dir():
                result[info.filename] = wheel.read(info)
        return result


def check_wheel(evidence, declaration, store, check, label):
    name = store.path_for_absolute(evidence['wheel_path'])
    raw = store.raw(name)
    members = wheel_members(raw)
    check('wheel_artifact_sha:'+label, sha(raw) == evidence['wheel_sha256'])
    check('wheel_normalized_sha:'+label, fp({key: sha(value) for key, value in sorted(members.items())})
          == evidence['wheel_content_sha256'])
    generated = {}
    for path in declaration:
        installed = path[4:] if path.startswith('src/') else path
        generated[path] = members[installed]
    return members, generated


def loose_git_source(store, root, commit):
    """Read archived Git objects as data, without Git or source execution."""
    def obj(oid):
        path = root+'/.git/objects/'+oid[:2]+'/'+oid[2:]
        raw = zlib.decompress(store.raw(path))
        if hashlib.sha1(raw).hexdigest() != oid:
            raise ValueError('archived Git object digest differs: '+path)
        head, body = raw.split(b'\0', 1)
        kind, size = head.split(b' ', 1)
        if int(size) != len(body):
            raise ValueError('archived Git object length differs')
        return kind.decode(), body
    kind, body = obj(commit)
    if kind != 'commit':
        raise ValueError('exact archived source is not a commit')
    lines = body.split(b'\n')
    tree = next(line[5:].decode() for line in lines if line.startswith(b'tree '))
    entries, blobs = {}, {}
    def descend(oid, prefix=''):
        kind, body = obj(oid)
        if kind != 'tree':
            raise ValueError('archived source tree object has wrong type')
        while body:
            meta, body = body.split(b'\0', 1)
            mode, name = meta.split(b' ', 1)
            oid, body = body[:20].hex(), body[20:]
            path = prefix+name.decode('utf-8')
            if not safe_name(path) or path in entries:
                raise ValueError('unsafe or duplicate immutable source path')
            if mode in (b'40000', b'040000'):
                descend(oid, path+'/')
            elif mode in (b'100644', b'100755', b'120000'):
                kind, raw = obj(oid)
                if kind != 'blob':
                    raise ValueError('archived source blob has wrong type')
                blobs[path] = raw
                entries[path] = {'path': path, 'mode': mode.decode(), 'blob': oid, 'sha256': sha(raw)}
            else:
                raise ValueError('unsupported archived source topology: '+path)
    descend(tree)
    def resolve(name, active=()):
        if name in active:
            raise ValueError('archived source alias cycle')
        target = blobs[name].decode()
        if not target or target.startswith('/') or '\\' in target or '\0' in target:
            raise ValueError('unsafe archived source alias')
        parts = list(PurePosixPath(name).parent.parts)
        for part in target.split('/'):
            if part in ('', '.'):
                continue
            if part == '..':
                if not parts:
                    raise ValueError('archived source alias escape')
                parts.pop()
            else:
                parts.append(part)
        path = '/'.join(parts)
        if path not in entries:
            raise ValueError('archived source alias is not a tracked file')
        return resolve(path, (*active, name)) if entries[path]['mode'] == '120000' else path
    files = {}
    for name, row in sorted(entries.items()):
        if row['mode'] == '120000':
            path = resolve(name)
            row.update(target=blobs[name].decode(), resolved_path=path, content_sha256=sha(blobs[path]))
            files[name] = blobs[path]
        else:
            files[name] = blobs[name]
    manifest = [row for _, row in sorted(entries.items())]
    identity = {'git_tree': tree, 'tracked_tree_sha256': fp(manifest), 'file_count': len(files)}
    ancestry, todo = set(), [commit]
    while todo:
        current = todo.pop()
        if current in ancestry:
            continue
        kind, raw = obj(current)
        if kind != 'commit':
            raise ValueError('archived parent is not a commit')
        ancestry.add(current)
        todo.extend(line[7:].decode() for line in raw.splitlines() if line.startswith(b'parent '))
    return identity, files, manifest, ancestry


def recipe(source):
    original = ast.parse(source.raw(PREFIX+'generic_build_materialization.py'))
    old = next(ast.literal_eval(node.value) for node in original.body
               if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'BUILD_RECIPE' for t in node.targets))
    current = ast.parse(source.raw(PREFIX+'native_build_v43.py'))
    value = next(node.value for node in current.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'BUILD_RECIPE' for t in node.targets))
    result = {}
    for key, expression in zip(value.keys, value.values):
        name = ast.literal_eval(key)
        if name == 'comparison':
            if not (isinstance(expression, ast.Subscript) and isinstance(expression.value, ast.Attribute)
                    and isinstance(expression.value.value, ast.Name) and expression.value.value.id == 'original_builder'
                    and expression.value.attr == 'BUILD_RECIPE' and ast.literal_eval(expression.slice) == 'comparison'):
                raise ValueError('unrecognized original build recipe reference')
            result[name] = old['comparison']
        else:
            result[name] = ast.literal_eval(expression)
    return result


def audit_components(source, evidence, freeze, check):
    manifest = evidence.js('COMPONENT_SOURCE_MANIFEST.json')
    pins = source.js(PREFIX+'developmental_sources.json')
    result = {}
    for key in ('development', 'metatron', 'flash'):
        value = manifest[key]
        expected = pins[key]
        check('component_exact_pin:'+key, value['repository'] == expected['repository']
              and value['commit'] == expected['commit'] and value['original_entrypoint_pins'] == expected['files'])
        name = value['archive']
        raw = evidence.raw(name)
        check('component_archive_sha:'+key, sha(raw) == value['archive_sha256'])
        seen = {}
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
            for member in archive:
                if member.isdir():
                    continue
                if not safe_name(member.name) or member.name in seen or member.name not in value['files']:
                    raise ValueError('unsafe or unexpected component member')
                row = value['files'][member.name]
                if member.issym() and row['mode'] == '120000':
                    body = member.linkname.encode('utf-8', errors='surrogateescape')
                elif member.isfile() and row['mode'] in ('100644', '100755'):
                    body = archive.extractfile(member).read()
                    check('component_mode:'+key+':'+member.name,
                          bool(member.mode & 0o111) == (row['mode'] == '100755'))
                else:
                    raise ValueError('unsupported component archive topology')
                check('component_blob:'+key+':'+member.name, sha(body) == row['sha256']
                      and len(body) == row['size_bytes'] and object_id('blob', body) == row['oid'])
                seen[member.name] = row
            check('component_archive_commit:'+key, archive.pax_headers.get('comment') == value['commit'])
        check('component_complete_source:'+key, seen == value['files'])
        original_tree = git_tree(Path('/workspace/components')/key, value['commit'])
        check('component_independent_original_git_tree:'+key,
              set(original_tree) == set(seen) and all(
                  all(row[field] == original_tree[name][field] for field in ('mode', 'kind', 'oid'))
                  for name, row in seen.items()))
        for path, digest in expected['files'].items():
            check('component_original_entrypoint:'+key+':'+path, value['files'][path]['sha256'] == digest)
        result[key] = {'repository': value['repository'], 'commit': value['commit'], 'files': len(seen)}
    loaded_name = 'run/LOADED_AUTHORITIES.json'
    check('loaded_authorities_nonvacuous', loaded_name in evidence.entries)
    loaded = evidence.js(loaded_name)
    check('loaded_authorities_required_modules', {'metatron.nucleus', 'qckn_flash_live_router', 'realitygraph.flash'} <= set(loaded))
    check('loaded_authorities_result_binding', loaded == evidence.js('run/RESULT.json')['loaded_authorities'])
    for name in evidence.matching('LOADED_AUTHORITIES.json'):
        for module, value in evidence.js(name).items():
            row = manifest[value['component']]['files'][value['relative_path']]
            expected_component = 'metatron' if module == 'metatron' or module.startswith('metatron.') else 'flash'
            module_path = module.replace('.', '/')
            expected_stem = ('runtime/' if expected_component == 'metatron' else '')+module_path
            check('actual_loaded_authority_module_mapping:'+module, value['component'] == expected_component
                  and value['relative_path'] in (expected_stem+'.py', expected_stem+'/__init__.py'))
            check('actual_loaded_authority:'+module, value['sha256'] == row['sha256']
                  and value['commit'] == manifest[value['component']]['commit'])
    return result



def authenticated_build_launch(value, builder_sha, recipe_sha):
    """A recorded failed attempt is retained for costs, never a build warrant."""
    commands = value.get('commands', [])
    costs = value.get('costs', {})
    return (value.get('status') == 'BUILT_NOT_SCIENTIFICALLY_VERIFIED'
        and value.get('builder_sha256') == builder_sha and value.get('recipe_sha256') == recipe_sha
        and bool(commands) and sum(row.get('phase') == 'base-native-wheel' for row in commands) == 1
        and all(row.get('returncode') == 0 and row.get('status') == 'PASS' for row in commands)
        and costs.get('build_calls') == 1 and costs.get('command_calls') == len(commands)
        and isinstance(costs.get('build_seconds'), (float, int)) and not isinstance(costs.get('build_seconds'), bool)
        and costs['build_seconds'] >= 0)


def audit_build_accounting(source, evidence, check):
    builder_sha = sha(source.raw(PREFIX+'native_build_v43.py'))
    recipe_sha = fp(recipe(source))
    records, distinct_launches = [], set()
    for name in evidence.matching('receipt.json'):
        native = evidence.js(name)
        if native.get('schema') != 'UDM_GENERIC_NATIVE_PYTEST_V43':
            continue
        collection = native['independent_collection']
        if 'build_verification' not in collection:
            continue
        value = collection['build_verification']
        output = value['native_output']
        sidecar = evidence.path_for_absolute(output+'/generated-build-verification.json')
        independent = evidence.path_for_absolute(output+'/generated-build-verification/verification.json')
        check('build_accounting_exact_sidecar:'+name, evidence.js(sidecar) == value
              and value['receipt'] == evidence.js(independent))
        receipt, before, after = value['receipt'], value['builder_attempts_before'], value['builder_attempts_after']
        report, costs = receipt['build'], receipt['costs']
        check('build_accounting_source_recipe:'+name,
              receipt['schema'] == 'UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43'
              and receipt['status'] == 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
              and report['builder_sha256'] == builder_sha and report['recipe_sha256'] == recipe_sha
              and report['binding'] == receipt['binding'] and value['status'] == 'VERIFIED_GENERATED_BUILD')
        command = [row for row in report['commands'] if row['phase'] == 'base-native-wheel']
        check('build_accounting_actual_attempt_delta:'+name, len(command) == 1
              and costs['build_calls'] == report['costs']['build_calls'] == 1
              and costs['command_calls'] == len(report['commands'])
              and all(row['returncode'] == 0 and row['status'] == 'PASS' for row in report['commands'])
              and command[0]['seconds'] == costs['build_seconds']
              and after['build_calls'] == before['build_calls']+1
              and after['records'][:-1] == before['records'] and len(after['records']) == len(before['records'])+1
              and math.isclose(after['build_seconds']-before['build_seconds'], costs['build_seconds'],
                               rel_tol=1e-9, abs_tol=1e-9))
        path = evidence.path_for_absolute(after['records'][-1])
        check('build_accounting_retained_launch_receipt:'+name, evidence.js(path) == report)
        distinct_launches.add(path)
        records.append({'native_receipt': name, 'independent_build_receipt': path,
                        'build_calls': costs['build_calls'], 'build_seconds': costs['build_seconds']})
    check('generated_build_accounting_nonvacuous', bool(records) and bool(distinct_launches))
    counters = evidence.js('run/BUILD_ATTEMPTS.json')
    actual = counters['after']['builder_attempts']
    check('main_builder_counter_unique_attempts', actual['build_calls'] == len(actual['records'])
          and len(set(actual['records'])) == len(actual['records']))
    measured_calls, measured_seconds = 0, 0.0
    for raw_path in actual['records']:
        name = evidence.path_for_absolute(raw_path)
        value = evidence.js(name)
        calls = sum(row['phase'] == 'base-native-wheel' for row in value['commands'])
        check('retained_builder_attempt:'+name, calls == value['costs']['build_calls'] == 1)
        measured_calls += calls
        measured_seconds += value['costs']['build_seconds']
    check('main_builder_counter_reconstructed', actual['build_calls'] == measured_calls
          and math.isclose(actual['build_seconds'], measured_seconds, rel_tol=1e-9, abs_tol=1e-6))
    all_builds, by_scope = [], collections.Counter()
    parent_paths = {evidence.path_for_absolute(path) for path in actual['records']}
    for name in evidence.matching('build-receipt.json'):
        value = evidence.js(name)
        if value.get('schema') != 'UDM_EXACT_BASE_BUILD_RECEIPT_V43':
            continue
        calls = sum(row['phase'] == 'base-native-wheel' for row in value['commands'])
        check('actual_build_receipt_counter:'+name, calls == value['costs']['build_calls']
            and value['builder_sha256'] == builder_sha and value['recipe_sha256'] == recipe_sha)
        scope = next((prefix for prefix in ('run/native-fixtures', 'run/native-context',
            'run/native-handoff', 'run/inherited-controls') if name.startswith(prefix+'/')), 'other')
        by_scope[scope] += calls
        all_builds.append({'path': name, 'build_calls': calls, 'build_seconds': value['costs']['build_seconds'],
            'scope': scope, 'in_main_process_counter': name in parent_paths})
    check('all_main_counter_attempts_have_actual_receipt', parent_paths <= {row['path'] for row in all_builds})
    build_fingerprints = {fp(evidence.js(row['path'])) for row in all_builds
                          if authenticated_build_launch(evidence.js(row['path']), builder_sha, recipe_sha)}
    verification_fingerprints, untrusted_verifications = set(), []
    for name in evidence.matching('verification.json'):
        value = evidence.js(name)
        if value.get('schema') != 'UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43':
            continue
        build = value.get('build')
        # Retain failed and intentionally forged negative-control files as
        # untrusted evidence. Only a receipt tied to an actual launch enters
        # the accepted fingerprint set subsequently required by every CAS use.
        trusted = (value.get('status') == 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
            and isinstance(build, dict) and fp(build) in build_fingerprints
            and value.get('binding') == build.get('binding')
            and value.get('costs', {}).get('build_calls') == build.get('costs', {}).get('build_calls') == 1)
        if trusted:
            verification_fingerprints.add(fp(value))
        else:
            untrusted_verifications.append({'path': name, 'sha256': fp(value),
                'claimed_status': value.get('status'), 'status': 'NOT_ADMITTED_AS_BUILD_WITNESS'})
    check('independent_build_verification_nonvacuous', bool(verification_fingerprints))
    return {'untrusted_or_failed_verification_records': untrusted_verifications,
            'audited_verification_sha256': sorted(verification_fingerprints), 'all_actual_build_receipts': all_builds, 'distinct_actual_build_calls': sum(row['build_calls'] for row in all_builds),
            'actual_build_calls_by_scope': dict(by_scope),
            'independent_recollection_records': records, 'distinct_recollection_launches': len(distinct_launches),
            'main_builder_counter': {'build_calls': measured_calls, 'build_seconds': measured_seconds},
            'boundary': 'Local measured commands/counters, not signed historical timing or complete engineering/model/tool cost.'}



def receipt_identity_matches(value, contract, authority, policy, certificate, candidate, runner_sha):
    """Joint concrete context binding; no producer code or self-reported match."""
    version = '42' if certificate.get('schema') == 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42' else '43'
    expected = {'schema': 'UDM_GENERIC_NATIVE_PYTEST_V'+version, 'repository': contract['repository'],
        'commit': contract['commit'], 'protocol_binding': contract['protocol_binding'],
        'source': {key: contract[key] for key in ('git_tree', 'tracked_tree_sha256', 'file_count')},
        'contract_sha256': fp(contract), 'authority_sha256': fp(authority),
        'policy_sha256': fp(policy), 'certificate_sha256': fp(certificate),
        'candidate_sha256': fp(candidate), 'runner_sha256': runner_sha,
        'environment': certificate['environment'], 'plugins': certificate['plugins']}
    return (all(value.get(key) == item for key, item in expected.items())
            and fp(value['environment']) == contract['environment_sha256'])


def protected_failure_matches(raw, reports, required, expected_assertion='assert 0 == 1'):
    """Reconcile exact fixture XML cases to call rows and inspect their failure."""
    calls = [row for row in reports if row.get('when') == 'call']
    expected = {}
    for row in calls:
        parts = row['nodeid'].split('::')
        if len(parts) < 2 or not parts[0].endswith('.py'):
            return False
        key = ('.'.join([parts[0][:-3].replace('/', '.'), *parts[1:-1]]), parts[-1])
        if key in expected:
            return False
        expected[key] = row
    cases = list(ET.fromstring(raw).iter('testcase'))
    seen, protected = set(), False
    for case in cases:
        key = case.get('classname'), case.get('name')
        if key not in expected or key in seen:
            return False
        seen.add(key)
        row = expected[key]
        failures, errors, skipped = case.findall('failure'), case.findall('error'), case.findall('skipped')
        if errors or skipped or len(failures) != int(row['outcome'] == 'failed'):
            return False
        is_required = any(row['nodeid'] == prefix or row['nodeid'].startswith(prefix+'[')
                          or row['nodeid'].startswith(prefix+'::') for prefix in required)
        if failures and is_required:
            failure = failures[0]
            text = failure.get('message', '')+' '+''.join(failure.itertext())
            protected = protected or expected_assertion in text
    return seen == set(expected) and protected


def audit_context(source, evidence, check):
    root = 'run/native-context/'
    context, result = evidence.js(root+'REPLAY_CONTEXT.json'), evidence.js(root+'RESULT.json')
    contract, authority, candidate = context['contract'], context['authority'], context['candidate']
    policy, certificate, receipt = context['policy'], context['certificate'], context['receipt']
    check('context_infrastructure_only', context['scope'] == 'QUALIFICATION_INFRASTRUCTURE_ONLY')
    check('context_retained_objects_exact', certificate == evidence.js(root+'collection/admission-certificate.json')
          and receipt == evidence.js(root+'native-pass/receipt.json'))
    check('context_exact_contract_authority_candidate', fp(contract) == certificate['contract_sha256'] == receipt['contract_sha256']
          and fp(authority) == certificate['authority_sha256'] == receipt['authority_sha256']
          and fp(policy) == certificate['policy_sha256'] == receipt['policy_sha256']
          and fp(candidate) == receipt['candidate_sha256'] and fp(certificate) == receipt['certificate_sha256'])
    check('context_source_base_distinct_augmented', context['base_commit'] == authority['baseline_commit']
          and context['augmented_commit'] == contract['commit'] and context['base_commit'] != context['augmented_commit'])
    files = {name: base64.b64decode(raw, validate=True) for name, raw in context['source_files'].items()}
    generated = {name: base64.b64decode(raw, validate=True) for name, raw in context['generated_files'].items()}
    manifest = context['source_manifest']
    check('context_source_inventory_identity', fp(manifest) == contract['tracked_tree_sha256'] and len(files) == contract['file_count'])
    check('context_raw_source_blobs', all(row['mode'] in ('100644', '100755') and sha(files[row['path']]) == row['sha256']
          and object_id('blob', files[row['path']]) == row['blob'] for row in manifest))
    build = contract['generated_build']
    original_root = evidence.path_for_absolute(context['source_git_directory']+'/.git/HEAD').rsplit('/.git/', 1)[0]
    base_identity, base_files, base_manifest, ancestors = loose_git_source(evidence, original_root, context['base_commit'])
    augmented_identity, augmented_files, augmented_manifest, _ = loose_git_source(evidence, original_root, context['augmented_commit'])
    check('context_archived_original_git_objects', base_identity == authority['baseline_source']
          and augmented_manifest == manifest and augmented_files == files
          and augmented_identity == {key: contract[key] for key in ('git_tree', 'tracked_tree_sha256', 'file_count')})
    check('context_build_binding', build['binding']['contract_sha256'] == fp(dict(contract, generated_build=None))
          and build['binding']['authority_sha256'] == fp(authority) and build['binding']['policy_sha256'] == fp(policy)
          and build['binding']['base_commit'] == context['base_commit']
          and build['binding']['augmented_commit'] == context['augmented_commit']
          and build['wheel_evidence']['builder_sha256'] == sha(source.raw(PREFIX+'native_build_v43.py')))
    check('context_build_base_source_and_ancestry', build['binding']['base_source'] == base_identity
          and set(build['binding']['scm']['ancestor_commits']) == ancestors
          and build['binding']['base_commit'] in ancestors and build['binding']['augmented_commit'] not in ancestors)
    check('context_only_base_reachable_tags', all(row['target'] in ancestors for row in build['binding']['scm']['ancestor_tags'])
          and build['binding']['scm']['ancestor_tags'] == [row for row in build['binding']['scm']['all_observed_tags']
                                                        if row['target'] in ancestors])
    expected_recipe = recipe(source)
    check('context_actual_recipe_source', build['wheel_evidence']['build_recipe_sha256'] == fp(expected_recipe))
    import tomllib
    original_project = tomllib.loads(base_files['pyproject.toml'].decode())
    declaration = original_project['tool']['hatch']['build']['hooks']['vcs']['version-file']
    check('context_original_declared_generated_path', build['binding']['declared_outputs'] == [declaration]
          and set(generated) == {declaration} and declaration not in files)
    original_members, actual_generated = check_wheel(build['wheel_evidence'], [declaration], evidence, check, 'context-original')
    check('context_generated_bytes', actual_generated == generated
          and build['generated_sha256'] == {name: sha(raw) for name, raw in generated.items()})
    independent = evidence.js(root+'collection/generated-build-verification/verification.json')
    rebuilt_members, _ = check_wheel(independent['build']['generated_wheel_evidence'], [declaration], evidence, check, 'context-independent')
    check('context_complete_independent_wheel_equality', original_members == rebuilt_members
          and independent['status'] == 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
          and independent['evidence_sha256'] == fp(build) and independent['binding'] == build['binding'])
    for label, report in [('original', evidence.js(root+'build/build-receipt.json')), ('independent', independent['build'])]:
        commands = report['commands']
        check('context_exact_backend_recipe:'+label, report['builder_sha256'] == sha(source.raw(PREFIX+'native_build_v43.py'))
              and report['recipe_sha256'] == fp(expected_recipe) and report['binding'] == build['binding']
              and report['status'] == 'BUILT_NOT_SCIENTIFICALLY_VERIFIED'
              and report['costs']['build_calls'] == 1 and report['costs']['command_calls'] == len(commands)
              and all(row['returncode'] == 0 and row['status'] == 'PASS' for row in commands))
        fetched = next(row['argv'] for row in commands if row['phase'] == 'base-local-fetch')
        checkout = next(row['argv'] for row in commands if row['phase'] == 'base-checkout')
        native = next(row['argv'] for row in commands if row['phase'] == 'base-native-wheel')
        check('context_exact_base_fetch_checkout:'+label, fetched[-1] == context['base_commit']
              and '--no-tags' in fetched and '--no-recurse-submodules' in fetched
              and checkout[-1] == context['base_commit'])
        check('context_actual_native_backend_command:'+label, native[0] == contract['interpreter']
              and native[1:1+len(expected_recipe['command'])] == expected_recipe['command'])
        build_root = evidence.path_for_absolute(str(PurePosixPath(native[-1])/'pyproject.toml')).rsplit('/pyproject.toml', 1)[0]
        built_identity, built_files, built_manifest, built_ancestors = loose_git_source(evidence, build_root, context['base_commit'])
        check('context_build_source_original_blobs:'+label, built_identity == base_identity
              and built_manifest == base_manifest and built_files == base_files and built_ancestors == ancestors)
        for path, raw in base_files.items():
            check('context_postbuild_tracked_bytes:'+label+':'+path, evidence.raw(build_root+'/'+path) == raw)
    expected = dict(files, **generated)
    for row in candidate['replacements']:
        check('context_candidate_original:'+row['path'], row['original_sha256'] == sha(files[row['path']]))
        expected[row['path']] = row['replacement'].encode()
    check('context_candidate_hash_inventory', {name: sha(raw) for name, raw in expected.items()}
          == context['expected_candidate_files_sha256'])
    for phase in ('native-pass', 'independent-native-pass', 'separate-process/reexecution'):
        value = evidence.js(root+phase+'/receipt.json')
        check('context_joint_receipt_identity:'+phase, receipt_identity_matches(value, contract, authority, policy,
              certificate, candidate, sha(source.raw(PREFIX+'native_execution_v43.py'))))
        imports = value['execution']['import_manifest']
        check('context_exact_native_imports:'+phase, bool(imports)
              and all(row['path'] in expected and row['sha256'] == sha(expected[row['path']]) for row in imports)
              and declaration in {row['path'] for row in imports})
        check('context_complete_pass:'+phase, value['status'] == 'PASS_NATIVE'
              and value['junit'] == dict(tests=2, passed=2, failures=0, errors=0, skipped=0))
    failure = evidence.js(root+'protected-failure/receipt.json')
    failed_nodes = [row['nodeid'] for row in failure['execution']['reports'] if row['when'] == 'call' and row['outcome'] == 'failed']
    check('context_protected_failure_joint_identity', receipt_identity_matches(failure, contract, authority, policy,
          certificate, {'replacements': []}, sha(source.raw(PREFIX+'native_execution_v43.py'))))
    check('context_actual_protected_assertion_failure', failure['status'] == 'FAIL_NATIVE'
          and failure['junit']['failures'] == 1 and protected_failure_matches(
              base64.b64decode(failure['packet']['native.xml'], validate=True),
              failure['execution']['reports'], authority['required_test_nodes']))
    child, controller = evidence.js(root+'separate-process/RESULT.json'), evidence.js(root+'child-controller.json')
    child_argv = controller['argv']
    check('context_exact_separate_process_launch', len(child_argv) == 5 and child_argv[1] == '-B'
          and evidence.path_for_absolute(child_argv[2]) == root+'CHILD_REPLAY.py'
          and evidence.path_for_absolute(child_argv[3]) == root+'REPLAY_CONTEXT.json'
          and evidence.path_for_absolute(child_argv[4]+'/RESULT.json') == root+'separate-process/RESULT.json'
          and child['controller'] == child_argv[0])
    check('context_actual_separate_process', controller['returncode'] == 0
          and child['status'] == 'PASS_SEPARATE_PROCESS_NATIVE_REPLAY'
          and child['runner_sha256'] == sha(source.raw(PREFIX+'native_execution_v43.py'))
          and child['attempt_delta']['native_calls'] >= 1 and child['attempt_delta']['collection_calls'] >= 1)
    check('context_child_source_identity', sha(evidence.raw(root+'CHILD_REPLAY.py')) == result['child_source_sha256'])
    return {'base_commit': context['base_commit'], 'augmented_commit': context['augmented_commit'],
            'generated_path': declaration, 'child': child, 'failure_nodes': failed_nodes}



def audit_handoff(source, evidence, native, check):
    """Independent native packet/context checks for the fixed handoff fixture."""
    root = 'run/native-handoff/'
    value = evidence.js(root+'handoff/RESULT.json')
    controller = evidence.js(root+'controller.json')
    runner = PREFIX+'archaeology/experiment-interface-v43/prospective-implementation/native_handoff_supplement.py'
    check('handoff_exact_executed_runner', controller['returncode'] == 0
          and controller['runner_sha256'] == sha(source.raw(runner))
          and controller['argv'][1] == '-B' and controller['argv'][2].endswith('/'+runner))
    check('handoff_source_byte_identity', value['source_unchanged'] is True
          and all(digest == sha(source.raw(PREFIX+name)) for name, digest in value['source_sha256'].items()))
    check('handoff_science_boundary', value['schema'] == 'UDM_V43_REAL_ENVIRONMENT_HANDOFF_SUPPLEMENT_V1'
          and value['status'] == 'PASS_BOUNDED_REAL_NATIVE_ENVIRONMENT_HANDOFF'
          and all(value['verdicts'][f'G{i}'] == 'UNKNOWN' for i in range(2, 7)))
    reporting = evidence.js(root+'handoff/reporting-controls/RESULT.json')
    expected = {'original-refusal-preserved', 'native-cost-shape-preserved', 'separate-build-delta',
                'strict-manifest-acceptance', 'exact-controller-source-guard', 'negative-delta-rejected'}
    check('all_six_reporting_controls_retained', reporting == value['reporting_controls']
          and reporting['status'] == 'PASS_WIRING_ONLY' and reporting['native_oracle_doubles'] is False
          and reporting['requested_zero_manifest_is_diagnostic_only'] is True
          and len(reporting['controls']) == len(expected) and set(reporting['controls']) == expected)
    audited = {row['sha256'] for row in native['receipts']}
    contexts = {}
    for label, status in (('alpha', 'PASS_NATIVE'), ('beta', 'FAIL_NATIVE')):
        context = evidence.js(root+'handoff/'+label+'-warm-context.json')
        setup, certificate, probe = context['setup'], context['certificate'], context['probe']
        receipt = probe['receipt']
        check('handoff_joint_native_context:'+label, fp(receipt) in audited
              and receipt_identity_matches(receipt, setup['contract'], setup['authority'], setup['policy'],
                  certificate, {'replacements': []}, sha(source.raw(PREFIX+'native_execution_v43.py')))
              and receipt['status'] == status and receipt['junit']['tests'] == 2
              and probe['producer']['dependencies'][:2] == [setup['materialization_capability'],
                  setup['materialization_binding']['consequence_id']])
        contexts[label] = context
    check('handoff_common_instrument_and_exact_cut',
          contexts['alpha']['setup']['materialization_capability'] == contexts['beta']['setup']['materialization_capability']
              == value['shared_generic_instrument']
          and value['exact_revoked_witness'] == contexts['beta']['setup']['materialization_binding']['consequence_id'])
    check('handoff_both_native_statuses_admissible', value['original_statuses'] == {'alpha': 'PASS_NATIVE', 'beta': 'FAIL_NATIVE'}
          and len(value['selected']) == 2 and value['unrelated_native_status'] == 'PASS_NATIVE')
    denied = {'cached-profile', 'uncached-profile', 'new-native-probe', 'actual-agent-worker-path'}
    check('handoff_all_preflight_control_paths', len(value['denied_before_any_producer']) == len(denied)
          and set(value['denied_before_any_producer']) == denied)
    return {'reporting_controls': sorted(expected), 'native_contexts': {label: context['probe']['receipt']['status']
        for label, context in contexts.items()}, 'preflight_control_paths': sorted(denied),
        'boundary': 'Fixed source-frozen handoff diagnostic; actual packet and CAS lineage independently checked. Preflight no-launch assertions are frozen executed control statements, not external signed action-monitor attestations.'}


def live_nodes(records):
    revoked = {row['payload']['target'] for row in records if row['kind'] == 'revoke'}
    live = set()
    for row in records:
        if row['kind'] != 'revoke' and row['id'] not in revoked and set(row['premises']) <= live:
            live.add(row['id'])
    return live


def audit_ledger(name, store, check):
    records, known = [], set()
    for number, line in enumerate(store.raw(name).splitlines(), 1):
        row = json.loads(line)
        raw = {key: value for key, value in row.items() if key != 'id'}
        check(f'ledger_content_id:{name}:{number}', sha(canonical(raw, ascii=False).encode()) == row['id'])
        check(f'ledger_ordered_premises:{name}:{number}', row['id'] not in known
              and len(set(row['premises'])) == len(row['premises']) and set(row['premises']) <= known)
        if row['kind'] == 'revoke':
            check(f'ledger_known_revocation:{name}:{number}', row['payload']['target'] in known)
        known.add(row['id'])
        records.append(row)
    root = name.rsplit('/', 1)[0]
    objects = {}
    for path in store.entries:
        if path.startswith(root+'/objects/'):
            key = path.rsplit('/', 1)[1]
            raw = store.raw(path)
            check('cas_hash:'+path, sha(raw) == key)
            objects[key] = json.loads(raw)
    return records, objects, root



def audit_cas_native_links(rows, objects, source, native, builds, check, label):
    """Close native ledger evidence against already audited retained packets.

    This authenticates concrete graph-to-receipt/context identities. Full import
    byte reconstruction remains the explicitly complete supplement's scope.
    """
    audited = {row['sha256'] for row in native['receipts']}
    certificates = {row['sha256'] for row in native['certificates']}
    by_id = {row['id']: row for row in rows}
    native_caps = {row['id']: row for row in rows if row['kind'] == 'executable_capability'
                   and row['payload'].get('operation') == 'native.pytest_suite'}
    for ident, node in native_caps.items():
        cap, inputs = node['payload'], node['payload']['source']
        contract, authority, policy, certificate = (objects[inputs[key]] for key in
            ('contract', 'suite_authority', 'policy', 'certificate'))
        candidate = objects[cap['program']]
        version = '42' if certificate['schema'] == 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42' else '43'
        runner = sha(source.raw(PREFIX+'native_execution_v'+version+'.py'))
        check('native_cas_original_inputs:'+label+':'+ident,
            inputs['verifier_sha256'] == runner and fp(certificate) in certificates
            and all(inputs[key] == contract[key] for key in
                ('repository', 'commit', 'git_tree', 'tracked_tree_sha256', 'protocol_binding', 'environment_sha256')))
        observation = by_id[cap['dependencies'][1]]
        observed = objects[observation['payload']['receipt']]
        verification = by_id[cap['evidence'][0]]
        bundle = objects[verification['payload']['receipt']]
        check('native_cas_observation_identity:'+label+':'+ident,
            observation['kind'] == 'generic_native_observation'
            and observation['payload']['candidate'] == cap['program']
            and observation['payload']['contract_sha256'] == fp(contract)
            and objects[cap['observation']] == dict(observed, observation_id=observation['id']))
        check('native_cas_independent_admission_runs:'+label+':'+ident,
            verification['kind'] == 'generic_native_verification'
            and verification['payload']['program'] == cap['program']
            and bundle['program'] == cap['program'] and bundle['generation'] == cap['generation']
            and len(bundle['runs']) == 2 and observed == bundle['runs'][0]
            and len({fp(receipt) for receipt in bundle['runs']}) == 2)
        for number, receipt in enumerate([observed, *bundle['runs']]):
            check('native_cas_audited_receipt:'+label+':'+ident+':'+str(number),
                fp(receipt) in audited and receipt['status'] == 'PASS_NATIVE'
                and receipt_identity_matches(receipt, contract, authority, policy, certificate, candidate, runner))
        binding = objects[inputs['materialization_binding']] if 'materialization_binding' in inputs else None
        check('native_cas_materialization_scope:'+label+':'+ident, cap['scope'].get('materialization') == binding)
        if binding is not None:
            witness = by_id[binding['consequence_id']]
            instrument = by_id[binding['capability_id']]
            retained = objects[witness['payload']['receipt']]
            invocation = objects[retained['invocation']]
            request = objects[invocation['request']]
            generated = contract['generated_build']
            check('native_cas_exact_materialization_witness:'+label+':'+ident,
                binding['consequence_id'] in cap['dependencies']
                and binding['consequence_id'] in node['premises']
                and binding['consequence_id'] in observation['premises']
                and witness['kind'] == 'verified_consequence'
                and witness['premises'] == [binding['capability_id']]
                and witness['payload']['evidence'] == binding['evidence_sha256'] == fp(generated)
                and witness['payload']['request'] == binding['request_sha256'] == invocation['request']
                and request['contract'] == dict(contract, generated_build=None)
                and request['authority'] == authority and request['policy'] == policy
                and objects[invocation['evidence']] == generated
                and retained['instrument'] == instrument['id']
                and retained['program'] == instrument['payload']['program']
                and retained['generation'] == binding['generation'] == instrument['payload']['generation'])
            independent = objects[invocation['verification']]
            check('native_cas_independent_materialization:'+label+':'+ident,
                fp(independent) in builds['audited_verification_sha256']
                and independent['status'] == 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME'
                and independent['evidence_sha256'] == fp(generated)
                and independent['binding'] == generated['binding'])
            original_wheel = objects[invocation['artifact']]
            independent_wheel = objects[invocation['independent_artifact']]
            original_raw = base64.b64decode(original_wheel['base64'], validate=True)
            independent_raw = base64.b64decode(independent_wheel['base64'], validate=True)
            check('native_cas_authenticated_wheel_members:'+label+':'+ident,
                sha(original_raw) == generated['wheel_evidence']['wheel_sha256']
                and sha(independent_raw) == independent['build']['generated_wheel_evidence']['wheel_sha256']
                and wheel_members(original_raw) == wheel_members(independent_raw))
    outcomes = []
    for row in rows:
        if row['kind'] != 'verified_consequence' or row['payload'].get('family') != 'generic-native-frontier':
            continue
        check('native_cas_outcome_capability:'+label+':'+row['id'], len(row['premises']) == 1 and row['premises'][0] in native_caps)
        cap = native_caps[row['premises'][0]]['payload']
        inputs = cap['source']
        receipt = objects[row['payload']['receipt']]
        contract, authority, policy, certificate = (objects[inputs[key]] for key in
            ('contract', 'suite_authority', 'policy', 'certificate'))
        check('native_cas_audited_consequence:'+label+':'+row['id'], fp(receipt) in audited
            and receipt['status'] == 'PASS_NATIVE' and row['payload']['program'] == cap['program']
            and row['payload']['contract_sha256'] == fp(contract)
            and receipt_identity_matches(receipt, contract, authority, policy, certificate,
                objects[cap['program']], sha(source.raw(PREFIX+'native_execution_v'+('42' if certificate['schema'].endswith('_V42') else '43')+'.py'))))
        outcomes.append(row['id'])
    probes = []
    for row in rows:
        if row['kind'] != 'native_frontier_v2_probe':
            continue
        profile = objects[row['payload']['record']]
        producer = profile['producer']
        inputs = by_id[producer['source']]['payload']['source']
        check('native_cas_probe_source_inputs:'+label+':'+row['id'],
            profile['schema'] == 'UDM_NATIVE_PROFILE_RECORD_V2'
            and by_id[producer['source']]['kind'] == 'generic_native_source'
            and by_id[producer['source']]['premises'] == [producer['authority']]
            and by_id[producer['authority']]['kind'] == 'execution_authority_ceiling'
            and row['premises'] == [producer['source'], producer['authority'], *producer['dependencies']]
            and all(objects[inputs[key]] == profile[field] for key, field in
                (('contract', 'contract'), ('suite_authority', 'authority'), ('certificate', 'certificate'), ('policy', 'policy'))))
        contract, authority, policy, certificate, candidate, receipt = (profile[key] for key in
            ('contract', 'authority', 'policy', 'certificate', 'candidate', 'receipt'))
        check('native_cas_probe_audited_receipt:'+label+':'+row['id'], fp(receipt) in audited
            and receipt_identity_matches(receipt, contract, authority, policy, certificate, candidate,
                sha(source.raw(PREFIX+'native_execution_v'+('42' if certificate['schema'].endswith('_V42') else '43')+'.py'))))
        if contract.get('generated_build') is not None:
            binding = objects[inputs['materialization_binding']]
            witness = by_id[binding['consequence_id']]
            check('native_cas_probe_exact_witness:'+label+':'+row['id'],
                producer['dependencies'][:2] == [binding['capability_id'], binding['consequence_id']]
                and witness['kind'] == 'verified_consequence'
                and witness['premises'] == [binding['capability_id']]
                and witness['payload']['request'] == binding['request_sha256']
                and witness['payload']['evidence'] == binding['evidence_sha256'] == fp(contract['generated_build'])
                and objects[witness['payload']['evidence']] == contract['generated_build'])
        probes.append(row['id'])
    return {'native_capabilities': sorted(native_caps), 'native_outcomes': outcomes, 'native_probes': probes}


def audit_causality(source, evidence, native, builds, check):
    ledgers, result = {}, {'ledgers': [], 'instrument_withdrawals': [], 'exact_invocation_withdrawals': [], 'restarts': []}
    for name in evidence.matching('metatron-ledger.jsonl'):
        rows, objects, root = audit_ledger(name, evidence, check)
        ledgers[root] = (rows, objects)
        live = live_nodes(rows)
        by_id = {row['id']: row for row in rows}
        cas = audit_cas_native_links(rows, objects, source, native, builds, check, root)
        result['ledgers'].append({'path': name, 'nodes': len(rows), 'live': len(live), 'cas_native_links': cas})
        bundle_name = root+'/flash-state-bundle.json'
        check('nonempty_ledger_flash_bundle_present:'+root, not rows or bundle_name in evidence.entries)
        if rows:
            bundle = evidence.js(bundle_name)
            admissions, revoked, event_digests = {}, set(), {}
            check('flash_bundle_event_inventory:'+root, bundle['schema'] == 'qckn-flash-state-bundle-v1'
                  and {event['event_id'] for event in bundle['events']} == {'udm:warrant:'+row['id'] for row in rows}
                  and len(bundle['events']) == len(rows))
            for event in bundle['events']:
                ident = event['event_id'].removeprefix('udm:warrant:')
                row = by_id[ident]
                record = {key: value for key, value in row.items() if key != 'id'}
                payload = event['payload']
                check('flash_original_record_binding:'+root+':'+ident,
                    event['schema'] == 'qckn-flash-external-event-v1'
                    and event['source_evidence_sha256'] == fp(record)
                    and event['payload_sha256'] == fp(payload)
                    and event['authority_snapshot'] == 'udm-local-warrant-log-v1'
                    and event['verifier_id'] == 'metatron-causal-support-projection-v1')
                if row['kind'] == 'revoke':
                    check('flash_exact_revocation:'+root+':'+ident,
                        event['event_kind'] == 'capability_revocation'
                        and payload == {'capability_id': 'udm:warrant:'+row['payload']['target'],
                                        'reason': row['payload']['reason']})
                    revoked.add(payload['capability_id'])
                    typename = 'CapabilityRevocationEvent'
                else:
                    cap = payload['capability']
                    supports = ['udm:warrant:'+key for key in row['premises']]
                    semantic = [[ident, fp(record)]]
                    check('flash_exact_support_projection:'+root+':'+ident,
                        event['event_kind'] == 'capability_admission'
                        and cap['capability_id'] == event['event_id']
                        and cap['input_type'] == 'SupportNodeId' and cap['output_type'] == 'SupportRecordSHA256'
                        and cap['semantics'] == semantic and cap['guard_inputs'] == [ident]
                        and cap['certificate_id'] == ident and cap['dependencies'] == supports
                        and cap['provenance_ids'] == [ident] and cap['cost'] == 0
                        and payload['oracle'] == semantic and payload['support_ids'] == supports
                        and payload['origin'] == 'support-projection-only')
                    admissions[event['event_id']] = cap
                    typename = 'CapabilityAdmissionEvent'
                event_digests[event['event_id']] = sha(typename.encode()+b':'+canonical(
                    {'event_id': event['event_id'], **payload}).encode())
            manifest = {'schema': 'qckn-flash-event-manifest-v1',
                        'events': [[key, value] for key, value in sorted(event_digests.items())]}
            check('flash_exact_event_manifest:'+root, bundle['event_manifest'] == manifest)
            flash_live = set()
            while True:
                next_live = flash_live | {key for key, cap in admissions.items()
                    if key not in revoked and set(cap['dependencies']) <= flash_live}
                if next_live == flash_live:
                    break
                flash_live = next_live
            check('independent_metatron_flash_liveness_agreement:'+root,
                  {key.removeprefix('udm:warrant:') for key in flash_live} == live)
        for number, row in enumerate(rows):
            if row['kind'] != 'revoke':
                continue
            old_live, new_live = live_nodes(rows[:number]), live_nodes(rows[:number+1])
            target = row['payload']['target']
            instruments = [item for item in rows[:number] if item['kind'] == 'executable_capability'
                           and item['payload']['operation'] == 'source.materialize_declared_backend'
                           and target in item['payload']['dependencies']]
            for instrument in instruments:
                ident = instrument['id']
                check('instrument_was_live:'+root+':'+ident, ident in old_live and ident not in new_live)
                dependents = [item for item in rows[:number] if item['kind'] == 'executable_capability'
                              and item['payload']['operation'] == 'native.pytest_suite'
                              and ident in item['payload']['dependencies'] and item['id'] in old_live]
                check('instrument_native_dependents_withdrawn:'+root+':'+ident,
                      bool(dependents) and all(item['id'] not in new_live for item in dependents))
                unrelated = [item for item in rows[:number] if item['kind'] == 'executable_capability'
                             and item['payload']['operation'] == 'native.pytest_suite'
                             and item['payload']['scope'].get('materialization') is None and item['id'] in old_live]
                check('instrument_unrelated_native_survives:'+root+':'+ident,
                      bool(unrelated) and all(item['id'] in new_live for item in unrelated))
                restored = [item for item in rows[number+1:] if item['kind'] == 'executable_capability'
                            and item['payload'].get('supersedes') == ident]
                check('instrument_new_evidence_generation:'+root+':'+ident, bool(restored)
                      and all(item['payload']['generation'] > instrument['payload']['generation']
                          and item['payload']['program'] == instrument['payload']['program']
                          and item['payload']['evidence'] != instrument['payload']['evidence'] for item in restored)
                      and ident not in live)
                live_restored = [item for item in restored if item['id'] in live]
                restored_native = [item for item in rows if item['id'] in live
                    and item['kind'] == 'executable_capability' and item['payload'].get('operation') == 'native.pytest_suite'
                    and any(parent['id'] in item['payload']['dependencies'] for parent in live_restored)]
                restored_outcomes = [item for item in rows if item['id'] in live
                    and item['kind'] == 'verified_consequence' and item['payload'].get('family') == 'generic-native-frontier'
                    and any(parent['id'] in item['premises'] for parent in restored_native)]
                check('instrument_live_native_restoration:'+root+':'+ident, bool(live_restored)
                      and bool(restored_native) and bool(restored_outcomes))
                result['instrument_withdrawals'].append({'ledger': name, 'instrument': ident,
                    'target': target, 'native_dependents': [item['id'] for item in dependents],
                    'restored': [item['id'] for item in restored]})
        cache_name = root+'/native-frontiers.json'
        registrations = [row for row in rows if row['kind'] == 'native_frontier_registration']
        check('registered_frontier_cache_present:'+root, not registrations or cache_name in evidence.entries)
        if cache_name in evidence.entries:
            cache = evidence.js(cache_name)
            check('frontier_cache_log_hash:'+root, cache['ledger_sha256'] == sha(evidence.raw(name)))
            check('frontier_cache_complete_registration_inventory:'+root, set(cache['frontiers']) == {row['payload']['frontier_id'] for row in registrations})
            publications = [row for row in rows if row['kind'] == 'native_frontier_route']
            for registration in registrations:
                payload = registration['payload']
                eligible = [row for row in publications if row['id'] in live
                    and row['payload']['contract'] == payload['contract']
                    and payload['profile'] in row['payload']['profiles']]
                candidates = sorted({row['payload']['capability_id'] for row in eligible})
                status = 'UNKNOWN_MISSING_AUTHORITY' if registration['id'] not in live else (
                    'READY' if len(candidates) == 1 else 'UNKNOWN_CHOICE' if candidates else 'UNKNOWN_SEARCH')
                actual = cache['frontiers'][payload['frontier_id']]
                check('frontier_independent_readiness:'+root+':'+payload['frontier_id'],
                    actual['status'] == status and actual['candidates'] == candidates
                    and actual['capability_id'] == (candidates[0] if status == 'READY' else None))
    for name in evidence.matching('INVOCATION_LINEAGE.json'):
        value = evidence.js(name)
        root = name.rsplit('/', 1)[0]+'/state'
        rows, objects = ledgers[root]
        nodes = {row['id']: row for row in rows}
        witness, cap = value['source_beta_witness'], nodes[value['native_capability']]
        check('invocation_exact_edges:'+name, witness in cap['premises']
              and witness in cap['payload']['dependencies']
              and witness in nodes[value['native_observation']]['premises'])
        cut = next(number for number, row in enumerate(rows)
                   if row['kind'] == 'revoke' and row['payload']['target'] == witness)
        before, after = live_nodes(rows[:cut]), live_nodes(rows[:cut+1])
        affected = [value['native_observation'], value['native_capability'], value['native_outcome']]
        unaffected = [value['instrument'], value['source_alpha_witness'], value['unrelated_capability'], value['native_source']]
        check('invocation_actual_selective_cut:'+name, witness in before and witness not in after
              and all(ident in before and ident not in after for ident in affected)
              and all(ident in after for ident in unaffected))
        check('invocation_flags_correspond_to_graph:'+name, all(value['graph_before'].values())
              and all(value['graph_after'].values()) and value['native_status'] == 'PASS_NATIVE')
        result['exact_invocation_withdrawals'].append({'path': name, 'witness': witness, 'affected': affected,
                                                      'unaffected': unaffected})
    for name in evidence.matching('RESTART_RESULT.json'):
        value = evidence.js(name)
        if 'instrument' not in value:
            continue
        check('causal_separate_process_native_restart:'+name, value['status'] == 'PASS_NATIVE'
              and value['junit'] == dict(tests=2, passed=2, failures=0, errors=0, skipped=0)
              and value['native_attempts']['native_calls'] == 1
              and value['native_attempts']['collection_calls'] >= 1 and value['build_calls'] >= 1
              and value['closure_agrees'] is True)
        matches = [(root, rows, objects) for root, (rows, objects) in ledgers.items()
                   if any(row['id'] == value['capability'] for row in rows)]
        check('causal_restart_retained_capability:'+name, len(matches) == 1)
        if len(matches) == 1:
            root, rows, objects = matches[0]
            cap = next(row for row in rows if row['id'] == value['capability'])
            check('causal_restart_same_source_and_live_generation:'+name, cap['payload']['source'] == value['source']
                  and value['instrument'] in cap['payload']['dependencies']
                  and value['instrument'] in live_nodes(rows) and value['capability'] in live_nodes(rows))
        result['restarts'].append({'path': name, 'instrument': value['instrument'], 'capability': value['capability']})
    check('whole_causal_evidence_nonvacuous', bool(result['instrument_withdrawals'])
          and bool(result['exact_invocation_withdrawals']) and bool(result['restarts']))
    return result


def interface_gate_files(source):
    """Interpret the one literal file-list comprehension, never module code."""
    module = ast.parse(source.raw(PREFIX+'qualify_native_frontier_v43.py'))
    value = next(node.value for node in module.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'INTERFACE_GATE_FILES' for target in node.targets))
    suffix = []
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
        suffix = ast.literal_eval(value.right)
        if not isinstance(suffix, tuple) or any(not isinstance(name, str) or not safe_name(name) for name in suffix):
            raise ValueError('unsupported literal interface file-list suffix')
        value = value.left
    if (not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name) or value.func.id != 'tuple'
            or len(value.args) != 1 or not isinstance(value.args[0], ast.GeneratorExp)):
        raise ValueError('unsupported literal interface file-list grammar')
    generator = value.args[0]
    if (len(generator.generators) != 1 or generator.generators[0].ifs or generator.generators[0].is_async
            or not isinstance(generator.elt, ast.BinOp) or not isinstance(generator.elt.op, ast.Add)
            or not isinstance(generator.elt.right, ast.Name)
            or not isinstance(generator.generators[0].target, ast.Name)
            or generator.elt.right.id != generator.generators[0].target.id):
        raise ValueError('unsupported literal interface file-list comprehension')
    prefix = ast.literal_eval(generator.elt.left)
    names = ast.literal_eval(generator.generators[0].iter)
    if not isinstance(prefix, str) or not isinstance(names, tuple) or any(not isinstance(name, str) for name in names):
        raise ValueError('unsupported literal interface file-list values')
    result = [prefix+name for name in names]+list(suffix)
    if len(set(result)) != len(result) or any(not safe_name(name) for name in result):
        raise ValueError('unsafe or duplicate interface file-list entry')
    return result


def audit_indexes(evidence, check):
    intervals = []
    for name in evidence.matching('SNAPSHOT.json'):
        value = evidence.js(name)
        if not isinstance(value, dict) or 'indexes' not in value:
            continue
        parent = name.rsplit('/', 1)[0]
        for number, row in enumerate(value['indexes']):
            if row['exists']:
                raw_name = parent+f'/index-{number}.bytes'
                check('raw_index_bytes:'+raw_name, raw_name in evidence.entries
                      and sha(evidence.raw(raw_name)) == row['sha256']
                      and len(evidence.raw(raw_name)) == row['size_bytes'])
    for name in evidence.entries:
        if not name.endswith(('AUDIT.json', 'INDEX_AUDIT.json')):
            continue
        value = evidence.js(name)
        if not isinstance(value, dict):
            continue
        if 'before' in value and 'after' in value and 'changes' in value:
            check('unchanged_index_interval:'+name, value['before'] == value['after'] and not value['changes'])
            intervals.append(name)
    post = evidence.js('POST_CONTROL_RUNTIME_AUDIT.json')
    check('runtime_post_bytes', post['status'] == 'PASS_FROZEN_RUNTIME_BYTES'
          and post['frozen_authority_modified'] is False
          and all(not any(row[key] for key in ('added', 'removed', 'changed', 'executable_changed'))
                  for row in post['runtimes'].values()))
    check('index_intervals_nonvacuous', bool(intervals))
    return {'intervals': intervals, 'runtime_post_status': post['status']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', required=True, type=Path)
    parser.add_argument('--source', required=True)
    parser.add_argument('--run', required=True, type=int)
    parser.add_argument('--artifact', required=True, type=int)
    parser.add_argument('--repo', type=Path, default=Path('/workspace/udm-v54'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--qualification-result-path', type=Path,
        help='Optional already retained exact RESULT destination used by the prospective gate descriptor')
    parser.add_argument('--extra-control-count', action='append', default=[], metavar='FILENAME=N',
        help='Final frozen count for the independently identified controller-setup control module')
    args = parser.parse_args(argv)
    if not re.fullmatch('[0-9a-f]{40}', args.source):
        parser.error('an exact full source commit is required')
    if args.out.exists() or args.out.absolute().resolve() != args.out.absolute():
        parser.error('new canonical output directory required')
    control_counts = dict(CONTROL_COUNTS)
    for item in args.extra_control_count:
        name, count = item.split('=', 1)
        if name in control_counts or name not in EXTRA_REQUIRED or not count.isdigit() or int(count) < 1:
            parser.error('explicit positive final count required for identified extra control, without overriding baseline counts')
        control_counts[name] = int(count)
    if any(name not in control_counts for name in EXTRA_REQUIRED):
        parser.error('final controller-setup control count must be supplied after its independent test freeze')
    args.out.mkdir(parents=True)
    check = Checks()
    report = {'schema': 'UDM_V43_INDEPENDENT_NATIVE_INTERFACE_ARCHIVE_AUDIT_V1',
        'source_commit': args.source, 'run_id': args.run, 'artifact_id': args.artifact,
        'branch': BRANCH, 'scope': 'NATIVE_INTERFACE_INFRASTRUCTURE_ONLY',
        'auditor_source_sha256': sha(Path(__file__).read_bytes()),
        'archive_policy': 'Stream regular bytes to SHA256 cache; inventory links, never follow or extract them.',
        'scientific_verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)},
        'external_enforcement': 'UNKNOWN_NONBYPASSABILITY',
        'portability': 'SAME_FILESYSTEM_COLD_RESTART_ONLY; RELOCATION_UNKNOWN',
        'complete_lifecycle_cost': 'UNKNOWN; engineering/model/tool costs and some setup commands are outside native/build counters'}
    report['expected_control_counts'] = control_counts
    before = index_snapshot(args.repo, args.out, 'local-index-before')
    component_before = {key: index_snapshot(Path('/workspace/components')/key, args.out,
        'local-component-'+key+'-index-before') for key in ('development', 'metatron', 'flash')}
    try:
        report['api'] = archive_identity(args, check, args.out)
        source, evidence, manifest = load_archive(args, check, args.out)
        report['manifest'] = {key: value for key, value in manifest.items() if key != 'files'}
        frozen, hashes = audit_source(args, source, evidence, check, args.out, control_counts)
        result = audit_controls(source, evidence, check, control_counts)
        report['native'] = audit_native(source, evidence, frozen, check)
        report['native_context'] = audit_context(source, evidence, check)
        report['native_handoff'] = audit_handoff(source, evidence, report['native'], check)
        report['build_accounting'] = audit_build_accounting(source, evidence, check)
        report['causal'] = audit_causality(source, evidence, report['native'], report['build_accounting'], check)
        report['components'] = audit_components(source, evidence, frozen, check)
        report['indexes_runtime'] = audit_indexes(evidence, check)
        report['available_costs'] = {'scope': result['cost_boundary'], 'wall_seconds': result['wall_seconds'],
            'native_attempts': result['attempts'],
            'builder_attempts': result['build_attempts']['after'].get('builder_attempts'),
            'child_and_inherited_counters': 'Retained separately; not silently summed as disjoint full lifecycle cost.'}
        report['inventory'] = {'source_files': len(source.entries), 'evidence_members': len(evidence.entries)}
        retained_result = args.out/'QUALIFICATION_RESULT.json'
        retained_result.write_bytes(evidence.raw('run/RESULT.json'))
        result_path = args.qualification_result_path or retained_result
        result_path = result_path if result_path.is_absolute() else args.repo/result_path
        check('gate_result_path_exact_bytes', result_path.resolve() == result_path.absolute()
              and not result_path.is_symlink() and result_path.read_bytes() == retained_result.read_bytes())
        gate = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': args.source,
            'run_id': args.run, 'artifact_id': args.artifact, 'artifact_sha256': report['api']['zip_sha256'],
            'qualification_result_sha256': sha(retained_result.read_bytes()), 'result_path': str(result_path)}
        report['prospective_gate_wrapper_material'] = {'interface_gate': gate,
            'gate_files_sha256': {name: hashes[name] for name in interface_gate_files(source)}}
    except BaseException as error:
        report['obstruction'] = type(error).__name__+': '+str(error)
    finally:
        after = index_snapshot(args.repo, args.out, 'local-index-after')
        check('local_read_only_index_interval', before == after)
        for key, snapshot in component_before.items():
            after_component = index_snapshot(Path('/workspace/components')/key, args.out,
                'local-component-'+key+'-index-after')
            check('local_read_only_component_index:'+key, snapshot == after_component)
        report['checks'] = check.rows
        report['failures'] = [row for row in check.rows if not row['pass']]
        report['status'] = ('PASS_BOUNDED_NATIVE_INTERFACE_ARTIFACT_AUDIT'
            if not report.get('obstruction') and not report['failures'] else 'UNKNOWN_OBSTRUCTION')
        report_raw = (json.dumps(report, sort_keys=True, indent=2)+'\n').encode()
        (args.out/'REPORT.json').write_bytes(report_raw)
        if report['status'] == 'PASS_BOUNDED_NATIVE_INTERFACE_ARTIFACT_AUDIT':
            wrapper = {'schema': 'UDM_V43_INDEPENDENT_INTERFACE_ARCHIVE_AUDIT_V1',
                'status': 'PASS_INDEPENDENT_ARCHIVE_AUDIT',
                **report['prospective_gate_wrapper_material'], 'all_native_packets_checked': True,
                'native_packet_scope': 'Retained raw collection/assertion/status packets; exact candidate/import bytes additionally closed for the complete native-context supplement. No universal Python refinement claim.',
                'independent_report_sha256': sha(report_raw),
                'scientific_verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
            (args.out/'INTERFACE_ARCHIVE_AUDIT.json').write_text(json.dumps(wrapper, sort_keys=True, indent=2)+'\n')
        print(json.dumps({'status': report['status'], 'checks': len(check.rows),
            'obstruction': report.get('obstruction'), 'failures': report['failures']}, sort_keys=True))
    return int(report['status'] != 'PASS_BOUNDED_NATIVE_INTERFACE_ARTIFACT_AUDIT')


if __name__ == '__main__':
    raise SystemExit(main())
