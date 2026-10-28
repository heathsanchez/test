#!/usr/bin/env python3
"""Read-only independent V45 ZIP/tar/source audit; never import project code.

Run only after the actual GitHub artifact and API records are retained. This
program reads source/data, authenticates loose Git objects, and launches only
fresh_compile.py under authenticated native profiles. Compiled fixture code is
never executed. All writes are confined to --out, outside the checkout.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile
import zlib

BASE = '88aa5090c310d2f75683a019a5bc958cdb3b576e'
SEAL = '48584499e067742a877b0ebf3c662ab96004e4ed628ebdc88a68bb42dbed2cce'
PREFIX = 'research/unified_consequence_runtime/'
CONTROL = PREFIX+'archaeology/native-namespace-v45/control-freeze/'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def fp(value):
    return sha(canonical(value).encode())


def need(condition, message):
    if not condition:
        raise ValueError(message)


def clean_name(name):
    p = PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and str(p) == name.rstrip('/'),
         'unsafe/noncanonical archive path: '+name)
    return str(p)


class TarData:
    """Hash every member, cache regular data by digest, never create links."""
    def __init__(self, archive, cache, omit_runtime=False):
        self.files = {}
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.pax = {}
        with tarfile.open(archive, 'r|gz') as packet:
            for member in packet:
                name = clean_name(member.name)
                if member.isdir():
                    continue
                need(name not in self.files, 'duplicate tar member: '+name)
                row = {'mode': member.mode, 'size': member.size}
                if member.issym():
                    row.update(kind='symlink', target=member.linkname)
                elif member.islnk():
                    row.update(kind='hardlink', target=clean_name(member.linkname))
                elif member.isfile():
                    row['kind'] = 'file'
                    stream = packet.extractfile(member)
                    need(stream is not None, 'unreadable tar member: '+name)
                    data = stream.read()
                    need(len(data) == member.size, 'short tar member: '+name)
                    row['sha256'] = sha(data)
                    # Runtime content is hashed in full. Native/source evidence
                    # and nested component archives remain readable as data.
                    skip = omit_runtime and (name.startswith('modern-runtime-final/venv/')
                        or name.startswith('original-runtimes/') and '/venv/' in name)
                    if not skip:
                        path = self.cache/row['sha256']
                        if not path.exists():
                            path.write_bytes(data)
                else:
                    raise ValueError('unsupported tar member kind: '+name)
                self.files[name] = row
            self.pax = dict(packet.pax_headers)
        for name, row in self.files.items():
            if row['kind'] == 'hardlink':
                target = self.files.get(row['target'])
                need(target is not None and target['kind'] == 'file', 'unsupported hardlink target: '+name)
                row.update(sha256=target['sha256'], size=target['size'])

    def read(self, name):
        row = self.files[name]
        need(row['kind'] in ('file', 'hardlink'), 'artifact is not regular data: '+name)
        path = self.cache/row['sha256']
        need(path.is_file(), 'uncached runtime member unexpectedly requested: '+name)
        raw = path.read_bytes()
        need(sha(raw) == row['sha256'], 'audit cache changed: '+name)
        return raw

    def js(self, name):
        return json.loads(self.read(name))


class FixtureGit:
    """Read archived loose Git objects directly, authenticating every object."""
    def __init__(self, evidence, root):
        self.evidence, self.root = evidence, root.rstrip('/')
        self.objects = {}

    def obj(self, oid):
        need(bool(re.fullmatch('[0-9a-f]{40}', oid)), 'non-exact fixture Git object')
        if oid not in self.objects:
            raw = zlib.decompress(self.evidence.read(self.root+'/.git/objects/'+oid[:2]+'/'+oid[2:]))
            need(hashlib.sha1(raw).hexdigest() == oid, 'archived fixture Git object hash differs')
            header, content = raw.split(b'\0', 1)
            kind, size = header.decode('ascii').split()
            need(len(content) == int(size), 'archived fixture Git object length differs')
            self.objects[oid] = kind, content
        return self.objects[oid]

    def tree(self, commit):
        kind, raw = self.obj(commit)
        need(kind == 'commit', 'fixture identity is not a commit')
        oid = raw.splitlines()[0].decode().removeprefix('tree ')
        rows = {}
        def descend(tree_oid, prefix=''):
            kind, data = self.obj(tree_oid)
            need(kind == 'tree', 'fixture directory is not a tree')
            while data:
                raw_mode, rest = data.split(b' ', 1)
                raw_name, rest = rest.split(b'\0', 1)
                child, data = rest[:20].hex(), rest[20:]
                name = prefix+raw_name.decode('utf-8')
                mode = raw_mode.decode()
                if mode in ('40000', '040000'):
                    descend(child, name+'/')
                else:
                    need(mode in ('100644', '100755', '120000'), 'opaque fixture entry: '+name)
                    kind, contents = self.obj(child)
                    need(kind == 'blob', 'fixture leaf is not a blob')
                    rows[name] = {'mode': mode, 'blob': child, 'raw': contents}
        descend(oid)
        return oid, rows


def git_tree(repo, commit):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
    raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo),
                                   'ls-tree', '-rz', '--full-tree', commit], env=env)
    rows = {}
    for entry in filter(None, raw.split(b'\0')):
        meta, name = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        need(kind == 'blob', 'unexpected nonblob source tree entry')
        rows[name.decode()] = {'mode': mode, 'oid': oid}
    return rows


def blob_oid(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def junit(raw):
    result = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    for case in ET.fromstring(raw).iter('testcase'):
        result['tests'] += 1
        key = next((name for name, tag in [('errors', 'error'), ('failures', 'failure'),
                                           ('skipped', 'skipped')] if case.find(tag) is not None), 'passed')
        result[key] += 1
    return result


def status(data, counts, collected):
    """Independently spell the frozen outcome semantics; no product import."""
    if data.get('timeout'):
        return 'UNKNOWN_TIMEOUT'
    if any(data.get(k) for k in ('source_mutations', 'unexpected_imports', 'external_project_imports',
                                 'changed_test_code', 'plugin_violations')):
        return 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    if (any(data.get(k) != collected[k] for k in ('collected_test_nodes', 'selected_test_nodes',
                                                 'plugin_manifest', 'test_items'))
            or data.get('deselected_test_nodes') or data.get('collection_errors')):
        return 'UNKNOWN_EXACT_COLLECTION'
    reports, nodes = data.get('reports', []), collected['selected_test_nodes']
    if any(not isinstance(r, dict) or set(r) != {'nodeid', 'when', 'outcome', 'wasxfail'}
           or r['when'] not in ('setup', 'call', 'teardown')
           or r['outcome'] not in ('passed', 'failed', 'skipped') or not isinstance(r['wasxfail'], str)
           for r in reports):
        return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
    if counts['skipped'] or any(r['wasxfail'] or r['outcome'] == 'skipped' for r in reports):
        return 'UNKNOWN_SKIPPED_OR_XFAIL'
    calls = [r for r in reports if r['when'] == 'call']
    if (any([r['nodeid'] for r in reports if r['when'] == phase] != nodes
            for phase in ('setup', 'call', 'teardown'))
            or any(r['outcome'] != 'passed' for r in reports if r['when'] != 'call')
            or counts['tests'] != len(nodes) or counts['errors']
            or counts['passed'] != sum(r['outcome'] == 'passed' for r in calls)
            or counts['failures'] != sum(r['outcome'] == 'failed' for r in calls)):
        return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
    if counts['failures'] and data.get('process_exit_code') == 1:
        return 'FAIL_NATIVE'
    if counts['passed'] == len(nodes) and data.get('process_exit_code') == 0:
        return 'PASS_NATIVE'
    return 'UNKNOWN_NATIVE_ERROR'


def compiler_environment(version, executable, library_dir, output):
    """Relocate only the exact public Actions build used by this bounded run.

    This is independent audit tooling, not an additional native admission
    environment. The executable and linked CPython library retain exact bytes.
    The public build URL was recovered from the actual Actions setup log.
    """
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(output),
           'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}
    if library_dir is None:
        return env, None
    need(version == '3.12.14', 'compiler library override has another profile')
    need(file_sha(executable) == 'bef88f140b625959f8af25c7b75cce2cd5d4b29cc2f2b079befd7f68eda4dba0',
         'compiler executable differs from exact recovered Actions build')
    library_dir = Path(library_dir)
    need(library_dir.is_absolute() and library_dir.resolve() == library_dir,
         'compiler library directory is not canonical')
    library = library_dir/'libpython3.12.so.1.0'
    need(library.is_file() and not library.is_symlink()
         and file_sha(library) == '1fa3c52ba5aa8f6b2852836a4bf6cbb23161f7cf379f6f19248d87124b28b38a',
         'compiler library differs from exact recovered Actions build')
    env['LD_LIBRARY_PATH'] = str(library_dir)
    return env, {'library_directory': str(library_dir), 'libpython_sha256': file_sha(library),
                 'build_url': 'https://github.com/actions/python-versions/releases/download/3.12.14-31661455385/python-3.12.14-linux-24.04-x64.tar.gz',
                 'build_archive_sha256': '5a03168292516f6dd6dcf630f4bf5369b108abd7c699a7e1db37f1e622257fff',
                 'boundary': 'Exact executable and CPython library; relocated audit-only compiler on the local host, not whole-host identity or native replay.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zip', required=True, type=Path)
    p.add_argument('--run-api', required=True, type=Path)
    p.add_argument('--artifact-api', required=True, type=Path)
    p.add_argument('--head', required=True)
    p.add_argument('--run-id', required=True, type=int)
    p.add_argument('--artifact-id', required=True, type=int)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--repo', type=Path, default=Path('/workspace/udm-v54'))
    p.add_argument('--profiles', type=Path, default=Path('/workspace/qualification/native-namespace-v45-environment/RUNTIME_PATHS.json'))
    p.add_argument('--modern-library-dir', type=Path)
    p.add_argument('--published-result-path')
    p.add_argument('--published-raw-audit-path')
    args = p.parse_args()
    need(args.out.is_absolute() and args.out.resolve() == args.out
         and not args.out.is_relative_to(args.repo.resolve()), 'audit output must be new canonical storage outside checkout')
    args.out.mkdir(parents=True, exist_ok=False)
    result = {'schema': 'UDM_V45_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT',
              'status': 'UNKNOWN_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT',
              'source_commit': args.head, 'task_queries': 0, 'fixture_executions': 0,
              'native_calls': 0, 'git_mutations': 0, 'repository_imports': 0}
    result['independent_auditor_files_sha256'] = {name: file_sha(Path(__file__).with_name(name))
        for name in ('audit_artifact.py', 'fresh_compile.py', 'source_authority.py', 'test_source_grammar.py', 'test_compiler_loader.py')}
    try:
        audit(args, result)
    except Exception as error:
        result['smallest_obstruction'] = type(error).__name__+': '+str(error)
    (args.out/'INDEPENDENT_AUDIT.json').write_text(canonical(result)+'\n')
    print(canonical({k: result[k] for k in ('status', 'source_commit', 'smallest_obstruction') if k in result}))
    return int(result['status'].startswith('UNKNOWN'))


def audit(args, result):
    need(sys.version_info[:3] == (3, 12, 14), 'auditor requires matching Python 3.12.14 controller AST grammar')
    run = json.loads(args.run_api.read_bytes())
    artifact = json.loads(args.artifact_api.read_bytes())
    if 'artifacts' in artifact:
        artifact, = [x for x in artifact['artifacts'] if x['id'] == args.artifact_id]
    need(run['id'] == args.run_id and run['head_sha'] == args.head, 'API run/head differs')
    need(run.get('repository', {}).get('full_name') == 'heathsanchez/test'
         and run.get('path') == '.github/workflows/udm-native-namespace-v45.yml', 'foreign repository/workflow')
    need(run['status'] == 'completed' and run['conclusion'] == 'success', 'actual workflow did not succeed')
    need(run['head_branch'] == 'research/udm-native-namespace-v45-20261029', 'foreign workflow branch')
    need(artifact['id'] == args.artifact_id and not artifact.get('expired'), 'wrong/expired artifact')
    need(artifact['name'] == 'native-namespace-v45-'+args.head+'-'+str(run['run_attempt']), 'foreign artifact name/attempt')
    need(artifact.get('workflow_run', {}).get('id', args.run_id) == args.run_id, 'artifact belongs to another run')
    size = args.zip.stat().st_size
    need(size == artifact['size_in_bytes'], 'downloaded ZIP size differs from API')
    digest = file_sha(args.zip)
    if artifact.get('digest'):
        need(artifact['digest'] == 'sha256:'+digest, 'downloaded ZIP digest differs from API')
    result['artifact'] = {'id': args.artifact_id, 'run_id': args.run_id, 'name': artifact['name'],
                          'bytes': size, 'sha256': digest, 'crc': 'PENDING'}
    with zipfile.ZipFile(args.zip) as z:
        need(z.testzip() is None, 'ZIP CRC failed')
        names = z.namelist()
        need(len(names) == len(set(names)), 'duplicate ZIP members')
        for name in names:
            clean_name(name)
        roots = []
        for name in names:
            if PurePosixPath(name).name == 'MANIFEST.json':
                value = json.loads(z.read(name))
                if value.get('schema') == 'UDM_NATIVE_NAMESPACE_ARCHIVE_MANIFEST_V45':
                    roots.append((str(PurePosixPath(name).parent), value))
        root, manifest = roots.pop() if len(roots) == 1 else (None, None)
        need(root is not None, 'missing/ambiguous V45 archive manifest')
        root = '' if root == '.' else root+'/'
        for name in ('SOURCE.tar.gz', 'NATIVE_NAMESPACE_V45_EVIDENCE.tar.gz'):
            with z.open(root+name) as inp, (args.out/name).open('xb') as out:
                shutil.copyfileobj(inp, out, 1024*1024)
    result['artifact']['crc'] = 'PASS_ALL_MEMBERS'
    source_tar = args.out/'SOURCE.tar.gz'
    evidence_tar = args.out/'NATIVE_NAMESPACE_V45_EVIDENCE.tar.gz'
    need(file_sha(source_tar) == manifest['source_sha256'], 'source archive hash differs')
    need(file_sha(evidence_tar) == manifest['archive_sha256'], 'evidence archive hash differs')
    need(manifest['source_commit'] == args.head, 'archive source/head differs')
    need(str(manifest['run_id']) == str(args.run_id) and str(manifest['run_attempt']) == str(run['run_attempt']), 'archive run/attempt identity differs')
    source = TarData(source_tar, args.out/'data')
    need(source.pax.get('comment') == args.head, 'source archive lacks exact Git commit identity')
    evidence = TarData(evidence_tar, args.out/'data', omit_runtime=True)
    need(set(evidence.files) == set(manifest['files']), 'evidence member inventory differs from manifest')
    for name, expected in manifest['files'].items():
        row = evidence.files[name]
        if expected['kind'] == 'file':
            need(row['kind'] in ('file', 'hardlink') and row['sha256'] == expected['sha256'], 'evidence bytes differ: '+name)
        else:
            need(row['kind'] == 'symlink' and row['target'] == expected['target'], 'evidence link identity differs: '+name)
    freeze, whole = evidence.js('FREEZE.json'), evidence.js('run/RESULT.json')
    need(freeze['source_commit'] == whole['source_commit'] == args.head, 'freeze/result source differs')
    need(whole['status'] == 'QUALIFIED_BOUNDED_NATIVE_NAMESPACE_ADMISSION_ONLY', 'whole run was not qualified')
    need(whole['freeze'] == freeze, 'whole result embeds another freeze')
    need(whole['verdicts'] == {'G'+str(i): 'UNKNOWN' for i in range(2, 7)}, 'scientific warrant was promoted')
    need(whole['prospective_task_sources_accessed'] is False and whole['coding_agent_executed'] is False, 'qualification exceeded engineering scope')
    need(freeze['controller']['packaging_version'] == '26.3'
         and freeze['controller']['environment']['pytest_version'] == '8.3.5'
         and freeze['controller']['environment']['version'].startswith('3.12.14'), 'actual controller profile differs')
    post = evidence.js('POST_CONTROL_RUNTIME_AUDIT.json')
    need(post['schema'] == 'UDM_POST_FIXTURE_RUNTIME_BYTE_AUDIT_V3' and post['status'] == 'PASS_FROZEN_RUNTIME_BYTES'
         and post['frozen_authority_modified'] is False and set(post['runtimes']) == set(freeze['runtimes']), 'actual post-control runtime audit did not pass')
    for row in post['runtimes'].values():
        need(not row['added'] and not row['removed'] and not row['changed'] and row['executable_changed'] is False,
             'actual native executable/stdlib changed during controls')
    actual = git_tree(args.repo, args.head)
    baseline = git_tree(args.repo, BASE)
    need(len(baseline) == 3011 and all(actual.get(k) == v for k, v in baseline.items()), '3011-entry immutable baseline differs')
    need(set(source.files) == set(actual) == set(freeze['files']), 'complete source inventory differs')
    need(freeze['source_tree'] == {name: {'mode': row['mode'], 'kind': 'blob', 'oid': row['oid']}
                                   for name, row in actual.items()}, 'frozen complete source tree metadata differs')
    for name, row in actual.items():
        raw = source.read(name)
        need(blob_oid(raw) == row['oid'] and sha(raw) == freeze['files'][name], 'source bytes differ: '+name)
        need('100'+format(source.files[name]['mode'], '03o') == row['mode'], 'source mode differs: '+name)
    need(len(json.loads(source.read(PREFIX+'capability_index.json'))['capabilities']) == 70, 'original 70-entry inventory differs')
    seal = json.loads(source.read(CONTROL+'FINAL_SEAL.json'))
    need(sha(source.read(CONTROL+'FINAL_SEAL.json')) == SEAL and len(seal['files']) == 257, 'independent control seal differs')
    need({name[len(CONTROL):] for name in source.files if name.startswith(CONTROL)} == set(seal['files'])|{'FINAL_SEAL.json'}, 'control pack inventory differs')
    for name, row in seal['files'].items():
        raw = source.read(CONTROL+name)
        need(sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'sealed control differs: '+name)
    controls = json.loads(source.read(CONTROL+'FIXTURE_INDEX.json'))
    for case in controls['cases']:
        for variant, rows in case['source_variants'].items():
            for name, row in rows.items():
                member = CONTROL+'fixtures/'+case['id']+'/'+variant+'/'+name
                need('100'+format(source.files[member]['mode'], '03o') == row['mode'], 'sealed fixture Git mode differs')
    nodes = freeze['control_collection']
    contracts = whole['contracts']
    counts = junit(evidence.read('run/contracts.xml'))
    need(contracts['collection'] == nodes and len(nodes) == len(set(nodes)), 'actual ordered node inventory differs')
    need(contracts['pytest_exit_code'] == 0 and counts == contracts['junit'], 'qualification JUnit/exit differs')
    need(counts['tests'] == counts['passed'] == len(nodes) and not any(counts[k] for k in ('failures', 'errors', 'skipped')), 'qualification did not execute every control')
    for phase in ('setup', 'call', 'teardown'):
        rows = [r for r in contracts['reports'] if r['when'] == phase]
        need([r['nodeid'] for r in rows] == nodes and all(r['outcome'] == 'passed' and not r['wasxfail'] for r in rows), 'missing/altered control execution phase')
    result['source_and_controls'] = {'source_files': len(source.files), 'preserved_baseline_files': len(baseline),
                                      'control_seal_files': 257, 'actual_passing_control_nodes': len(nodes), 'original_index_entries': 70}
    gate_files = static_gate_files(source.read(PREFIX+'qualify_native_namespace_v45.py'))
    result['gate_files_sha256'] = {name: freeze['files'][name] for name in gate_files}
    result['namespace_gate'] = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': args.head,
        'run_id': args.run_id, 'artifact_id': args.artifact_id, 'artifact_sha256': digest,
        'qualification_result_sha256': sha(evidence.read('run/RESULT.json')),
        'result_path': args.published_result_path or 'UNPUBLISHED_ACTUAL_ARTIFACT_RESULT'}
    # Remaining stages are implemented separately so archive checks stay useful
    # if source authority or fresh compilation exposes a later obstruction.
    result['archive_file_count'] = len(evidence.files)
    worker_source = source.read(PREFIX+'native_execution_v45.py').decode()
    for fragment in ("_BOOTSTRAP = previous._BOOTSTRAP.replace(_unwrap, '')",
                     'if _native_type(obj) is _native_method:obj=obj.__func__',
                     'code=obj.__code__ if _native_type(obj) is _native_function else None',
                     'def code_hash(obj,_native_type=type,_native_function=types.FunctionType,_native_method=types.MethodType):'):
        need(fragment in worker_source, 'qualified direct callable type guard differs')
    result['direct_callable_guard'] = {'source_sha256': sha(worker_source.encode()),
        'recursive_wrapped_lookup_removed': True, 'exact_function_method_types_captured_before_source_execution': True}
    components = evidence.js('COMPONENT_SOURCE_MANIFEST.json')
    pins = {'development': 'c9092fa57c8943e638f95689cd36e6a63310f41e',
            'metatron': 'b9d1b5cc10477188be6e55617699be60e70f6dad',
            'flash': '50c43b14e7272469bc51ff7204dec07682a996d7'}
    need(set(components) == set(pins), 'original component inventory differs')
    for name, expected in components.items():
        need(expected['commit'] == pins[name], 'original component pin differs')
        raw = evidence.read(expected['archive'])
        need(sha(raw) == expected['archive_sha256'], 'component archive digest differs')
        archive_path = args.out/expected['archive']
        archive_path.write_bytes(raw)
        contents = TarData(archive_path, args.out/'data')
        need(contents.pax.get('comment') == pins[name], 'component archive lacks original Git identity')
        need(set(contents.files) == set(expected['files']), 'component full source inventory differs')
        for path, row in expected['files'].items():
            member = contents.files[path]
            blob = member['target'].encode() if member['kind'] == 'symlink' else contents.read(path)
            need(sha(blob) == row['sha256'] and len(blob) == row['size_bytes'] and blob_oid(blob) == row['oid'], 'component source bytes differ')
            need((member['kind'] == 'symlink') == (row['mode'] == '120000'), 'component source kind differs')
            if member['kind'] != 'symlink':
                need(bool(member['mode'] & 0o111) == (row['mode'] == '100755'), 'component source mode differs')
    result['components'] = {name: {'commit': row['commit'], 'files': len(row['files'])} for name, row in components.items()}
    remote = '/workspace/qualification/native-namespace-v45-ci-'+str(args.run_id)+'-'+str(run['run_attempt'])
    audit_native(args, result, source, evidence, freeze, whole, remote)
    result['status'] = 'PASS_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT'
    result['boundary'] = 'Actual ZIP/API/source and raw evidence audit; fresh original-source compilation only. No fixture execution, task query, scientific result, or hostile-process nonbypassability claim.'


def audit_native(args, result, source, evidence, freeze, whole, remote):
    def mapped(path):
        path = str(path)
        need(path.startswith(remote+'/'), 'foreign absolute artifact reference: '+path)
        name = clean_name(path[len(remote)+1:])
        need(name in evidence.files, 'referenced artifact is missing: '+name)
        return name

    def read_ref(path):
        return evidence.read(mapped(path))

    def js_ref(path):
        return json.loads(read_ref(path))

    def load_helper(filename):
        path = Path(__file__).with_name(filename)
        spec = importlib.util.spec_from_file_location('_independent_'+path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    authority_checker = load_helper('source_authority.py')
    identities = {}
    contexts = []
    def remember(value):
        if isinstance(value, dict):
            if isinstance(value.get('schema'), str) or set(value) == {'replacements'}:
                identities.setdefault(fp(value), value)
            for child in value.values():
                if isinstance(child, dict):
                    remember(child)
    for name, row in evidence.files.items():
        if row['kind'] not in ('file', 'hardlink'):
            continue
        if name.endswith('.CONTEXT.json') or name.endswith('/CONTEXT.json') or '/state/objects/' in name:
            try:
                value = evidence.js(name)
            except (ValueError, UnicodeError):
                continue
            remember(value)
            if value.get('schema') == 'UDM_NATIVE_V45_TEST_CONTEXT':
                contexts.append((name, value))
    certificates, receipts, raw_invocations = {}, {}, {}
    def fixture_data(name):
        return '/.git/' in name or any(prefix+'/.git/config' in evidence.files for prefix in ancestors(name.rsplit('/', 1)[0]))
    controller_fields = {'process_exit_code', 'timeout', 'source_mutations', 'unexpected_imports', 'costs'}
    for name, row in evidence.files.items():
        if row['kind'] not in ('file', 'hardlink') or not name.endswith('/checked-report.json'):
            continue
        # Repository fixture bytes are data, never invocation authority.
        directory = name.rsplit('/', 1)[0]
        if fixture_data(name):
            continue
        checked = evidence.js(name)
        costs = checked['costs']
        need(type(costs.get('native_calls')) is int and type(costs.get('collection_calls')) is int
             and costs['native_calls']+costs['collection_calls'] == 1, 'raw invocation counters differ')
        raw = evidence.js(directory+'/report.json')
        need(raw == {k: v for k, v in checked.items() if k not in controller_fields}, 'raw/checked native packet differs: '+directory)
        for sibling in ('stdout.log', 'stderr.log', 'tracked-source-manifest.json'):
            need(directory+'/'+sibling in evidence.files, 'missing raw native sibling')
        raw_invocations[directory] = checked
    for name, row in evidence.files.items():
        if row['kind'] not in ('file', 'hardlink') or not name.endswith(('/admission-certificate.json', '/receipt.json')):
            continue
        if fixture_data(name):
            continue
        value = evidence.js(name)
        schema = value.get('schema', '')
        if schema.startswith('UDM_NATIVE_ADMISSION_CERTIFICATE_'):
            certificates[fp(value)] = (name, value)
        elif schema.startswith('UDM_GENERIC_NATIVE_PYTEST_'):
            receipts[name] = value
    genuine_roles, genuine_manifests = {}, []
    for name, row in evidence.files.items():
        if row['kind'] not in ('file', 'hardlink') or not name.endswith('/V45_NATIVE_EVIDENCE.json') or fixture_data(name):
            continue
        manifest = evidence.js(name)
        need(manifest['schema'] == 'UDM_NATIVE_V45_TEST_EVIDENCE', 'foreign genuine-evidence schema')
        genuine_manifests.append(name)
        for entry in manifest['records']:
            need(entry['role'] in ('certificate', 'receipt', 'independent_reexecution'), 'unknown genuine evidence role')
            path = entry['path']
            target = mapped(path) if path.startswith('/') else clean_name(str(PurePosixPath(name).parent/path))
            need(target in evidence.files and sha(evidence.read(target)) == entry['sha256'], 'genuine evidence manifest refers to changed/foreign bytes')
            if entry['role'] == 'certificate':
                need(target in {n for n, _ in certificates.values()}, 'genuine certificate was not retained')
            else:
                need(target in receipts, 'genuine receipt was not retained')
                need(target not in genuine_roles or genuine_roles[target] == entry['role'], 'one actual native invocation has duplicate roles')
                genuine_roles[target] = entry['role']
    for digest, (name, cert) in certificates.items():
        version = cert['schema'].rsplit('_', 1)[-1]
        need(version in ('V2', 'V42', 'V43', 'V45'), 'unknown native certificate version')
        need(cert['runner_sha256'] == freeze['files'][PREFIX+'native_execution_'+version.lower()+'.py'], 'native certificate worker source differs')
        allowed_environments = [row['environment'] for row in freeze['profile_identities'].values()]
        if version == 'V2':
            allowed_environments.append(freeze['controller']['original_v2_environment'])
        need(cert['environment'] in allowed_environments, 'native certificate environment is not an actual frozen profile')
        directory = name.rsplit('/', 1)[0]
        checked = check_packet(evidence, directory, cert)
        need(directory in raw_invocations and checked['mode'] == 'collect'
             and checked['process_exit_code'] == checked['exit_code'] == 0
             and not checked.get('timeout') and not checked.get('collection_errors')
             and not checked.get('deselected_test_nodes'), 'certificate collection incomplete')
        need(cert['collection'] == {key: checked[key] for key in cert['collection']}, 'native certificate collection differs')
    counts_by_version = {}
    for name, receipt in receipts.items():
        version = receipt['schema'].rsplit('_', 1)[-1]
        need(version in ('V2', 'V42', 'V43', 'V45'), 'unknown native receipt version')
        need(receipt['runner_sha256'] == freeze['files'][PREFIX+'native_execution_'+version.lower()+'.py'], 'native receipt worker differs')
        need(receipt['certificate_sha256'] in certificates, 'receipt lacks authenticated collection certificate')
        cert = certificates[receipt['certificate_sha256']][1]
        need(all(receipt[key] == cert[key] for key in ('contract_sha256', 'authority_sha256', 'policy_sha256', 'environment', 'plugins')),
             'native receipt source/environment/policy differs from original certificate')
        directory = name.rsplit('/', 1)[0]+'/execution'
        checked = check_packet(evidence, directory, receipt)
        need(directory in raw_invocations and checked == receipt['execution'], 'receipt does not bind actual raw invocation')
        inferred = junit(evidence.read(directory+'/native.xml')) if directory+'/native.xml' in evidence.files else dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
        need(inferred == receipt['junit'] and status(checked, inferred, cert['collection']) == receipt['status'], 'native outcome does not match actual raw evidence')
        if name in genuine_roles:
            need(version == 'V45' and receipt['status'] in ('PASS_NATIVE', 'FAIL_NATIVE'), 'UNKNOWN/foreign packet mislabeled as genuine native evidence')
        counts_by_version.setdefault(version, {}).setdefault(receipt['status'], 0)
        counts_by_version[version][receipt['status']] += 1
    result['raw_native_packets'] = {'retained_invocations': len(raw_invocations), 'certificates': len(certificates),
                                    'receipts': len(receipts), 'outcomes_by_version': counts_by_version,
                                    'native_calls': sum(v['costs']['native_calls'] for v in raw_invocations.values()),
                                    'collection_calls': sum(v['costs']['collection_calls'] for v in raw_invocations.values())}
    positive = {name: receipt for name, receipt in receipts.items() if receipt['schema'] == 'UDM_GENERIC_NATIVE_PYTEST_V45'}
    actual_counts = {'native_passes': sum(r['status'] == 'PASS_NATIVE' for r in positive.values()),
                     'native_failures': sum(r['status'] == 'FAIL_NATIVE' for r in positive.values()),
                     'independent_replays': sum(genuine_roles.get(name) == 'independent_reexecution'
                          and r['status'] in ('PASS_NATIVE', 'FAIL_NATIVE') for name, r in positive.items())}
    need(genuine_manifests and all(value > 0 for value in actual_counts.values()), 'actual V45 native PASS/FAIL/independent replay evidence missing')
    need(all(whole['raw_native_audit'][key] == value for key, value in actual_counts.items()), 'qualified V45 native counters differ from independently counted actual invocations')
    claimed = whole['raw_native_audit']['receipts']
    by_invocation = {remote+'/'+name.rsplit('/', 1)[0]+'/execution': (name, receipt) for name, receipt in receipts.items()}
    need(len(claimed) == len(by_invocation) and len({r['invocation_path'] for r in claimed}) == len(claimed), 'qualified native receipt inventory duplicates/omits invocations')
    for row in claimed:
        need(row['invocation_path'] in by_invocation, 'qualified native audit has foreign invocation')
        name, receipt = by_invocation[row['invocation_path']]
        need(row['path'] == remote+'/'+name and row['schema'] == receipt['schema']
             and row['status'] == receipt['status'] and row['junit'] == receipt['junit']
             and row['role'] == genuine_roles.get(name, 'retained_receipt'), 'qualified raw audit receipt binding differs')
    result['raw_native_packets'].update(actual_counts, genuine_manifest_count=len(genuine_manifests))
    # Authenticate selected local compiler profiles before compiling any source.
    profiles = json.loads(args.profiles.read_bytes())
    catalog = json.loads(source.read(PREFIX+'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'))
    selected = {p['id']: p for p in catalog['profiles']}
    need(set(profiles) == set(selected) == set(freeze['profile_identities']), 'selected profile inventory differs')
    local_profiles = {}
    result['offline_compiler_profiles'] = {}
    for ident, executable in profiles.items():
        profile = selected[ident]
        env = freeze['profile_identities'][ident]['environment']
        executable_digest = sha(Path(executable).read_bytes())
        result['offline_compiler_profiles'][ident] = {'local_executable': executable,
            'local_executable_sha256': executable_digest, 'ci_executable': env['executable'],
            'ci_executable_sha256': env['executable_sha256'], 'ci_sys_version': env['version'],
            'binary_identity_equal': executable_digest == env['executable_sha256']}
        need(executable_digest == env['executable_sha256'], 'local compiler executable differs from actual selected CI executable: '+ident)
        _, loader = compiler_environment(profile['python_version'], executable,
            args.modern_library_dir if profile['python_version'] == '3.12.14' else None, args.out)
        result['offline_compiler_profiles'][ident]['audit_loader'] = loader
        site = Path(executable).parent.parent/'lib'/('python'+'.'.join(profile['python_version'].split('.')[:2]))/'site-packages'
        ci_pytest = env['pytest_import']['path']
        pytest_relative = ci_pytest.split('/site-packages/', 1)[1]
        need(sha((site/pytest_relative).read_bytes()) == env['pytest_import']['sha256'], 'local selected pytest import differs')
        code = {path.relative_to(site).as_posix(): sha(path.read_bytes()) for path in (site/'_pytest').rglob('*.py')}
        if (site/'pytest').is_dir():
            code.update({path.relative_to(site).as_posix(): sha(path.read_bytes()) for path in (site/'pytest').rglob('*.py')})
        else:
            code['pytest.py'] = sha((site/'pytest.py').read_bytes())
        ci_site = ci_pytest.split('/site-packages/', 1)[0]+'/site-packages/'
        archived = {path: evidence.files.get(ci_site[len(remote)+1:]+path, {}).get('sha256') for path in code}
        if all(value is not None for value in archived.values()):
            need(archived == code, 'selected local pytest/rewrite source differs from archived CI package')
            source_basis = 'COMPLETE_ARCHIVED_PYTEST_PYTHON_SOURCE'
        else:
            wheel = profile['package_artifacts']['pytest']
            matches = [path for path in args.profiles.parent.rglob(wheel['filename'])
                       if '/wheels/' in path.as_posix() and sha(path.read_bytes()) == wheel['sha256']]
            need(bool(matches), 'authenticated original pytest wheel unavailable for omitted runtime content')
            with zipfile.ZipFile(matches[0]) as package:
                expected = {name: sha(package.read(name)) for name in package.namelist()
                            if name.endswith('.py') and (name.startswith('_pytest/') or name.startswith('pytest/') or name == 'pytest.py')}
            need(code == expected, 'selected local pytest/rewrite source differs from original independently pinned wheel')
            source_basis = 'ORIGINAL_CATALOG_PINNED_PYTEST_WHEEL'
        local_profiles[env['pytest_version']] = {'id': ident, 'interpreter': executable, 'site': str(site.resolve()),
                                                'authenticated_python_source': code, 'profile': profile,
                                                'environment': env, 'package_source_basis': source_basis,
                                                'pytest_python_files': len(code), 'audit_loader': loader}
    validations, compilations, negative_bindings = {}, {}, []
    pure = args.out/'fresh-compilations'
    pure.mkdir()
    for cert_hash, (cert_name, cert) in certificates.items():
        if cert['schema'] != 'UDM_NATIVE_ADMISSION_CERTIFICATE_V45':
            continue
        contract = identities.get(cert['contract_sha256'])
        authority = identities.get(cert['authority_sha256'])
        need(contract is not None and authority is not None, 'V45 certificate lacks original retained CONTEXT/CAS authority')
        need(contract['schema'] == 'UDM_GENERIC_NATIVE_PYTEST_V45' and authority['schema'] == 'UDM_NATIVE_SUITE_AUTHORITY_V45', 'context has foreign schema')
        need(authority['repository'] == contract['repository'] and authority['source_commit'] == contract['commit']
             and authority['protocol_binding'] == contract['protocol_binding'], 'original authority/contract binding differs')
        key = cert['authority_sha256']
        if key not in validations:
            repo = mapped(contract['repo_path']+'/.git/config').removesuffix('/.git/config')
            original_git = FixtureGit(evidence, repo)
            tree_oid, git_rows = original_git.tree(contract['commit'])
            baseline_oid, base_rows = original_git.tree(authority['baseline_commit'])
            need(tree_oid == contract['git_tree'], 'original fixture Git tree differs from contract')
            files = {name: row['raw'] for name, row in git_rows.items()}
            before = {name: row['raw'] for name, row in base_rows.items()}
            modes = {name: row['mode'] for name, row in git_rows.items()}
            base_modes = {name: row['mode'] for name, row in base_rows.items()}
            manifest = [{'path': name, 'mode': row['mode'], 'blob': row['blob'], 'sha256': sha(row['raw'])}
                        for name, row in sorted(git_rows.items())]
            need(len(files) == contract['file_count'] and fp(manifest) == contract['tracked_tree_sha256'], 'typed original source inventory differs')
            need(authority['source'] == {key: contract[key] for key in ('git_tree', 'tracked_tree_sha256', 'file_count')}, 'authority original source identity differs')
            base_manifest = [{'path': name, 'mode': row['mode'], 'blob': row['blob'], 'sha256': sha(row['raw'])}
                             for name, row in sorted(base_rows.items())]
            need(authority['baseline_source'] == {'git_tree': baseline_oid, 'tracked_tree_sha256': fp(base_manifest), 'file_count': len(base_rows)}, 'authority baseline identity differs')
            expected = authority_checker.derive(files, before, modes, base_modes, authority)
            comparison = authority_checker.validate(expected, authority)
            need(comparison.get('ok') is True, 'independent source authority differs: '+repr(comparison))
            payload = {'sources': {}}
            for prefix, row in expected['namespace_certificate']['required_declarations'].items():
                item = payload['sources'].setdefault(row['path'], {'source': base64.b64encode(files[row['path']]).decode(),
                     'source_sha256': sha(files[row['path']]), 'origins': {}})
                item['origins'][prefix] = row['origin']
            validations[key] = {'expected': expected, 'payload': payload, 'files': files, 'manifest': manifest, 'git_source': repo,
                                'original_commit': contract['commit'], 'baseline_commit': authority['baseline_commit']}
        validation = validations[key]
        profile = local_profiles[cert['environment']['pytest_version']]
        need(contract['interpreter'] == cert['environment']['executable']
             and cert['environment'] == profile['environment'], 'original contract selected another native interpreter')
        compile_key = key+'-'+profile['id']
        if compile_key not in compilations:
            folder = pure/compile_key
            folder.mkdir()
            payload = dict(validation['payload'], profile={name: profile['profile'][name]
                                                          for name in ('python_version', 'pytest_version')})
            (folder/'input.json').write_text(canonical(payload)+'\n')
            helper = Path(__file__).with_name('fresh_compile.py')
            compiler_env, _ = compiler_environment(profile['profile']['python_version'], profile['interpreter'],
                Path(profile['audit_loader']['library_directory']) if profile['audit_loader'] else None, folder)
            process = subprocess.run([profile['interpreter'], '-I', '-B', str(helper),
                str(folder/'input.json'), str(folder/'output.json')], cwd=folder,
                env=compiler_env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            (folder/'stdout.log').write_bytes(process.stdout)
            (folder/'stderr.log').write_bytes(process.stderr)
            need(process.returncode == 0, 'fresh original-source compilation failed: '+process.stderr.decode(errors='replace'))
            compiled = json.loads((folder/'output.json').read_bytes())
            validate_tooling(compiled, profile, helper)
            compilations[compile_key] = compiled
        compiled = compilations[compile_key]
        validate_collection(cert['collection'], validation['expected'], validation['files'])
        compare_outer(cert['collection'], validation['expected'], compiled)
        expected_hashes = {name: sha(raw) for name, raw in validation['files'].items()}
        generated = contract.get('generated_build')
        if generated is not None:
            wheel = generated['wheel_evidence']
            raw = read_ref(wheel['wheel_path'])
            need(sha(raw) == wheel['wheel_sha256'], 'generated source wheel bytes differ')
            with zipfile.ZipFile(io.BytesIO(raw)) as package:
                for path, digest in generated['generated_sha256'].items():
                    candidates = [name for name in (path, path.removeprefix('src/')) if name in package.namelist()]
                    need(candidates and all(sha(package.read(name)) == digest for name in candidates), 'generated import differs from exact rebuilt wheel')
                    expected_hashes[path] = digest
        compare_imports(cert['collection'], expected_hashes, cert)
        # An archived expected-code sidecar is compared with fresh expectations;
        # it never selects original source or supplies expected hashes.
        directory = cert_name.rsplit('/', 1)[0]
        need(evidence.js(directory+'/tracked-source-manifest.json') == validation['manifest'], 'collection packet manifest differs from authenticated original Git source')
        compare_compiler_sidecar(evidence, directory, validation['payload'], compiled)
        for name, receipt in receipts.items():
            if receipt['schema'] == 'UDM_GENERIC_NATIVE_PYTEST_V45' and receipt['certificate_sha256'] == cert_hash:
                compare_compiler_sidecar(evidence, name.rsplit('/', 1)[0]+'/execution', validation['payload'], compiled)
                need(evidence.js(name.rsplit('/', 1)[0]+'/execution/tracked-source-manifest.json') == validation['manifest'], 'execution packet manifest differs from authenticated original Git source')
                candidate = identities.get(receipt['candidate_sha256'])
                need(candidate is not None, 'V45 receipt lacks retained original candidate input')
                executable_hashes = dict(expected_hashes)
                for row in candidate['replacements']:
                    need(row['path'] in validation['files'] and row['original_sha256'] == sha(validation['files'][row['path']]), 'candidate does not bind original production source')
                    executable_hashes[row['path']] = sha(row['replacement'].encode())
                if receipt['status'] in ('PASS_NATIVE', 'FAIL_NATIVE'):
                    compare_outer(receipt['execution'], validation['expected'], compiled)
                    compare_imports(receipt['execution'], executable_hashes, cert)
                else:
                    try:
                        compare_outer(receipt['execution'], validation['expected'], compiled)
                        compare_imports(receipt['execution'], executable_hashes, cert)
                        binding = 'ORIGINAL_BINDING_PRESENT_OUTCOME_STILL_UNKNOWN'
                    except ValueError as error:
                        binding = 'REFUSED_BINDING_OR_IMPORT: '+str(error)
                    negative_bindings.append({'receipt': name, 'status': receipt['status'], 'binding': binding})
    need(validations and compilations, 'no independently source-bound V45 declaration compilation')
    result['declaration_authority'] = {'original_authorities': len(validations), 'fresh_compiler_launches': len(compilations),
        'protected_declarations': sum(len(v['expected']['required_test_nodes']) for v in validations.values()),
        'source_basis': 'ARCHIVED_CONTEXT_CAS_PLUS_AUTHENTICATED_ORIGINAL_LOOSE_GIT_OBJECTS',
        'expected_basis': 'INDEPENDENT_AST_C3_DELTA_NAMESPACE_DERIVATION_AND_FRESH_RAW_PYTEST_REWRITE_COMPILATION',
        'profiles': {k: {key: v[key] for key in ('id', 'package_source_basis', 'pytest_python_files')} for k, v in local_profiles.items()}}
    result['declaration_authority']['unknown_negative_bindings'] = negative_bindings
    # Main and child attempt fields are reconstructed independently below.
    verify_costs(evidence, whole, mapped, read_ref, js_ref)
    result['cost_accounting'] = {'main_scope': whole['native_attempts']['scope'],
        'authenticated_children': len(whole['child_attempts']), 'known_totals': whole['known_attempt_totals'],
        'all_retained_raw_counts': result['raw_native_packets'], 'complete_lifecycle_cost': 'UNKNOWN'}
    result['all_native_packets_checked'] = True
    result['raw_native_audit'] = {'path': remote+'/run/RAW_NATIVE_AUDIT.json',
                                 'sha256': sha(evidence.read('run/RAW_NATIVE_AUDIT.json'))}
    if args.published_raw_audit_path:
        result['raw_native_audit']['path'] = args.published_raw_audit_path


def static_gate_files(raw):
    """Evaluate only the finite literal tuple/generator used for file names."""
    tree = ast.parse(raw)
    expressions = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                   for target in node.targets if isinstance(target, ast.Name)}
    env = {'PREFIX': PREFIX, 'TESTS': ast.literal_eval(expressions['TESTS'])}
    def value(node, scope):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return scope[node.id]
        if isinstance(node, (ast.Tuple, ast.List)):
            items = []
            for child in node.elts:
                items.extend(value(child.value, scope)) if isinstance(child, ast.Starred) else items.append(value(child, scope))
            return tuple(items) if isinstance(node, ast.Tuple) else items
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return value(node.left, scope)+value(node.right, scope)
        if isinstance(node, ast.GeneratorExp) and len(node.generators) == 1:
            generator = node.generators[0]
            need(isinstance(generator.target, ast.Name) and not generator.ifs and not generator.is_async, 'unsupported gate file generator')
            return [value(node.elt, dict(scope, **{generator.target.id: item})) for item in value(generator.iter, scope)]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tuple' and len(node.args) == 1 and not node.keywords:
            return tuple(value(node.args[0], scope))
        raise ValueError('unsupported finite gate-file expression')
    result = value(expressions['GATE_FILES'], env)
    need(result and len(result) == len(set(result)) and all(isinstance(name, str) for name in result), 'gate file names are not unique finite literals')
    return result


def ancestors(path):
    parts = PurePosixPath(path).parts
    return ['/'.join(parts[:i]) for i in range(1, len(parts)+1)]


def check_packet(evidence, directory, value):
    packet = {name: base64.b64decode(raw, validate=True) for name, raw in value['packet'].items()}
    required = {'stdout.log', 'stderr.log', 'report.json', 'checked-report.json', 'tracked-source-manifest.json'}
    if value['schema'].startswith('UDM_NATIVE_ADMISSION_CERTIFICATE_'):
        required.add('native.xml')
        need(set(packet) == required, 'native admission packet file set differs')
    else:
        need(required <= set(packet) <= required|{'native.xml'}, 'native execution packet file set differs')
    need(value['packet_sha256'] == {name: sha(raw) for name, raw in packet.items()}, 'native packet public hashes differ')
    for name, raw in packet.items():
        clean_name(name)
        need('/' not in name and evidence.read(directory+'/'+name) == raw, 'native packet differs from exact on-disk bytes')
    checked, raw = json.loads(packet['checked-report.json']), json.loads(packet['report.json'])
    fields = {'process_exit_code', 'timeout', 'source_mutations', 'unexpected_imports', 'costs'}
    need(raw == {key: val for key, val in checked.items() if key not in fields}, 'native producer/controller relation differs')
    return checked


def compare_outer(observed, expected, compiled):
    declarations = compiled['declarations']
    for prefix in expected['required_test_nodes']:
        original = expected['namespace_certificate']['required_declarations'][prefix]
        items = [r for r in observed['test_items'] if r['nodeid'] == prefix
                 or r['nodeid'].startswith(prefix+'[') or r['nodeid'].startswith(prefix+'::')]
        need(items, 'actual collection omitted original protected declaration: '+prefix)
        for item in items:
            need(item['path'] == original['path'] and item['sha256'] == original['source_sha256']
                 and item['code_sha256'] in declarations[prefix]['code_sha256'],
                 'actual outer code does not match independently compiled original: '+item['nodeid'])


def validate_collection(collection, expected, files):
    fields = {'collected_test_nodes', 'selected_test_nodes', 'deselected_test_nodes', 'test_items',
              'import_manifest', 'external_project_imports', 'pytest_import', 'plugin_manifest', 'plugin_violations'}
    need(set(collection) == fields, 'collection is not the fixed original nine-field projection')
    nodes, selected = collection['collected_test_nodes'], collection['selected_test_nodes']
    need(nodes and len(nodes) == len(set(nodes)) and len(selected) == len(set(selected))
         and set(selected) == set(nodes) and not collection['deselected_test_nodes'], 'native exact original collection is incomplete')
    need([row['nodeid'] for row in collection['test_items']] == nodes, 'observed items do not bind exact original collected nodes')
    need(not collection['external_project_imports'] and not collection['plugin_violations'], 'native collection has unlicensed imports/plugins')
    for row in collection['test_items']:
        need(row['path'] in files and row['sha256'] == sha(files[row['path']]), 'collected item source differs from original Git object')
    for prefix in expected['required_test_nodes']:
        need(any(node == prefix or node.startswith(prefix+'[') or node.startswith(prefix+'::') for node in nodes),
             'actual original collected nodes omit required assertion: '+prefix)


def validate_tooling(compiled, selected, helper):
    actual, profile = compiled['tooling'], selected['profile']
    need(actual['python_version'] == profile['python_version'] and actual['pytest_version'] == profile['pytest_version']
         and actual['implementation'] == 'cpython' and actual['flags']['optimize'] == 0
         and actual['flags']['isolated'] == 1 and actual['flags']['dont_write_bytecode'] == 1,
         'fresh compiler did not use selected original interpreter flags/version')
    need(actual['executable']['path'] == str(Path(selected['interpreter']).resolve())
         and actual['executable']['sha256'] == selected['environment']['executable_sha256'], 'actual compiler executable identity differs')
    site = Path(selected['site'])
    code = selected['authenticated_python_source']
    imported = {}
    for key in ('pytest_package', '_pytest_package'):
        package = actual[key]
        root = Path(package['root'])
        need(root.is_relative_to(site), 'actual compiler imported a foreign pytest package')
        need(fp(package['python_files']) == package['python_files_sha256']
             and len(package['python_files']) == package['python_file_count'], 'actual compiler package inventory differs')
        for row in package['python_files']:
            imported[(root/row['path']).relative_to(site).as_posix()] = row['sha256']
    need(imported == code, 'actual compiler pytest/rewrite Python code differs from preauthenticated package')
    for key in ('pytest', 'rewrite'):
        path = Path(actual[key]['path'])
        need(path.is_relative_to(site) and code.get(path.relative_to(site).as_posix()) == actual[key]['sha256'],
             'actual compiler module origin differs: '+key)
    need(compiled['helper']['sha256'] == file_sha(helper), 'fresh compilation used another independent helper')


def compare_imports(observed, expected_hashes, certificate):
    need(observed.get('pytest_import') == certificate['environment']['pytest_import'], 'actual pytest import differs')
    for row in observed['import_manifest']:
        need(expected_hashes.get(row['path']) == row['sha256'], 'actual imported source differs from original executable view: '+row['path'])
    licensed = {row['path']: row['sha256'] for row in certificate['plugins']}
    for row in observed.get('plugin_manifest', []):
        if row['kind'] == 'source':
            need(expected_hashes.get(row['path']) == row['sha256'], 'source plugin identity differs')
        elif row['kind'] == 'licensed':
            need(licensed.get(row['path']) == row['sha256'], 'licensed plugin identity differs')
        else:
            need(row['kind'] == 'pytest-core' and row['module'].startswith('_pytest.'), 'unknown actual plugin origin')


def compare_compiler_sidecar(evidence, directory, payload, fresh):
    sidecar = evidence.js(directory+'/original-declaration-compilation.json')
    original_input = evidence.js(directory+'/original-declaration-compiler/original-input.json')
    report = evidence.js(directory+'/original-declaration-compiler/expected-code.json')
    need(original_input == payload, 'worker compiler selected another source/origin')
    need(sidecar['status'] == report['status'] == fresh['status'] == 'COMPILED_ORIGINAL_DECLARATIONS_WITHOUT_EXECUTION'
         and sidecar['declarations'] == report['declarations']
         and set(sidecar['declarations']) == set(fresh['declarations']), 'worker expected compiler declaration set/status differs')
    for prefix, row in sidecar['declarations'].items():
        expected = fresh['declarations'][prefix]
        need(row['path'] == expected['path'] and row['origin'] == expected['origin']
             and row['source_sha256'] == expected['source_sha256'] and row['code_sha256'] == expected['code_sha256'],
             'archived expected compiler output differs from independent fresh compilation')


def verify_costs(evidence, whole, mapped, read_ref, js_ref):
    import math
    native = whole['native_attempts']
    compiler = whole['compilation_attempts']
    need(native['scope'] == compiler['scope'] == 'MAIN_CONTROLLER_CONTEXT_ONLY', 'main counter scope differs')
    def delta(record, fields):
        for field in fields:
            need(type(record['delta'][field]) in (int, float) and math.isfinite(record['delta'][field])
                 and record['delta'][field] >= 0 and math.isclose(record['after'][field]-record['before'][field],
                     record['delta'][field], rel_tol=1e-12, abs_tol=1e-12), 'attempt counter arithmetic differs')
    native_fields = ('native_calls', 'collection_calls', 'subprocess_attempts')
    compiler_fields = ('compilation_calls', 'compilation_seconds')
    delta(native, native_fields); delta(compiler, compiler_fields)
    totals = {**{k: native['delta'][k] for k in native_fields}, **{k: compiler['delta'][k] for k in compiler_fields}}
    children = whole['child_attempts']
    need(children, 'actual child attempt ledger missing')
    ledgers = [compiler]
    for descriptor in children:
        summary = js_ref(descriptor['path'])
        need(sha(read_ref(descriptor['path'])) == descriptor['sha256'] and summary == descriptor['summary'], 'child ledger bytes differ')
        report = js_ref(descriptor['stdout']['path'])
        need(report['attempts'] == summary and report['status'] == summary['status'], 'child stdout binding differs')
        for name in ('stdout', 'stderr'):
            need(sha(read_ref(descriptor[name]['path'])) == descriptor[name]['sha256'], 'child stream hash differs')
        delta(summary['native_attempts'], native_fields)
        delta(summary['compilation_attempts'], compiler_fields)
        ledgers.append(summary['compilation_attempts'])
        for key in native_fields:
            totals[key] += summary['native_attempts']['delta'][key]
        for key in compiler_fields:
            totals[key] += summary['compilation_attempts']['delta'][key]
        need(len(set(summary['native_run_outputs'])) == summary['native_attempts']['delta']['native_calls'], 'child launch/output counts differ')
        parent = str(PurePosixPath(descriptor['path']).parent)
        for output in summary['native_run_outputs']:
            need(output.startswith(parent+'/restart/'), 'child receipt points outside its restart output')
            receipt = js_ref(output+'/receipt.json')
            need(receipt['costs']['native_calls'] == receipt['costs']['collection_calls'] == 1, 'child receipt did not charge both calls')
    for ledger in ledgers:
        old, new = ledger['before']['records'], ledger['after']['records']
        need(new[:len(old)] == old, 'compiler ledger prefix changed')
        added = new[len(old):]
        need(sum(r['compilation_calls'] for r in added) == ledger['delta']['compilation_calls']
             and math.isclose(sum(r['seconds'] for r in added), ledger['delta']['compilation_seconds'], rel_tol=1e-12, abs_tol=1e-12), 'compiler failed/successful attempt charges differ')
        for record in added:
            output = record['output']
            need(js_ref(output+'/compilation.json') == record, 'compiler metadata ledger differs')
            need(sha(read_ref(output+'/compiler.py')) == record['compiler_sha256'], 'compiler source artifact differs')
            need(fp(js_ref(output+'/original-input.json')) == record['input_sha256'], 'compiler input artifact differs')
            if record.get('report_sha256'):
                need(sha(read_ref(output+'/expected-code.json')) == record['report_sha256'], 'compiler output artifact differs')
    known = whole['known_attempt_totals']
    need(all(known[k] == v for k, v in totals.items()) and known['child_processes'] == len(children)
         and known['wall_intervals_additive'] is False, 'known main/child aggregate differs')


if __name__ == '__main__':
    raise SystemExit(main())
