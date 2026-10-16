"""Admission-only V4.1 qualification over frozen original native controls.

No historical task is rerun and no prospective task is queried. The original
worker, assertions, source freezer and persistent default-output context remain
authoritative. Retained reconstructions are labeled separately from test locals.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from types import FunctionType
import unittest

from . import native_environment_v41 as environment
from . import native_execution_v3 as execution
from . import qualify_environment_selection_v4 as previous
from .audit_index_v4 import snapshot_indexes, compare_indexes
from .decisive_native_verify import canonical, fingerprint, sha256

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECORDS = HERE/'archaeology/native-authority-v41'
CATALOG = RECORDS/'ENVIRONMENT_CATALOG.json'
BASE = '7edf1018342b50f73ca226de3e0d0b7acdb31647'
FREEZE_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V41'
RESULT_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V41'
ACCEPTANCE_SHA256 = 'b7a21fbaececd597b15d68ca6350741f2bc652055c6637c4b21bdb76758c68b9'
TEST_SHA256 = '8087a1c58749e4c04fe895eaa361661bab36ae938354fff999409a0b622d24d7'
PREVIOUS_SHA256 = 'e1516f57bf9ba564d747a8944d3d636f17836e56fb71a0ea52909bae842f11b4'
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
source_authority = previous.source_authority
RecordedResult = previous.RecordedResult
retained_temporary_outputs = previous.retained_temporary_outputs
# Pin the complete retained selected/rejected metadata inventory independently
# of directory contents, so deletion cannot silently shrink a later gate.
METADATA_EVIDENCE_FILES = tuple(
    'research/unified_consequence_runtime/archaeology/native-authority-v41/'
    'bootstrap/metadata-evidence/'+name for name in (
        'ast-serialize==0.13.0.METADATA', 'ast-serialize==0.13.0.entry_points.txt',
        'ast-serialize==0.13.0.json', 'librt==0.16.0.METADATA',
        'librt==0.16.0.entry_points.txt', 'librt==0.16.0.json',
        'mypy==2.4.0.METADATA', 'mypy==2.4.0.entry_points.txt', 'mypy==2.4.0.json',
        'mypy-extensions==1.1.0.METADATA', 'mypy-extensions==1.1.0.entry_points.txt',
        'mypy-extensions==1.1.0.json', 'pytest-cov==6.3.0.METADATA',
        'pytest-cov==6.3.0.entry_points.txt', 'pytest-cov==6.3.0.json',
        'pytest-cov==7.0.0.METADATA', 'pytest-cov==7.0.0.json',
        'pytest-cov==7.1.0.METADATA', 'pytest-cov==7.1.0.json',
        'setuptools-git-versioning==3.2.0.METADATA',
        'setuptools-git-versioning==3.2.0.entry_points.txt',
        'setuptools-git-versioning==3.2.0.json'))
SOURCE_GATE_FILES = tuple(dict.fromkeys((*previous.SOURCE_GATE_FILES,
    *(('research/unified_consequence_runtime/'+name) for name in (
        'native_environment_selection_v3.py', 'native_environment_selection_v41.py',
        'native_environment_v41.py', 'test_native_environment_v41.py',
        'qualify_environment_selection_v41.py',
        'test_native_dependency_includes_v41.py', 'test_native_execution_v3.py',
        'test_native_admission_v2_adversarial.py', 'test_native_environment_selection_v3.py',
        'qualify_native_frontier_v41.py', 'test_qualify_native_frontier_v41.py',
        'archaeology/native-authority-v41/ACCEPTANCE_PROTOCOL.json',
        'archaeology/native-authority-v41/PLUMBING_TEST_FREEZE.json',
        'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json',
        'archaeology/native-authority-v41/PACKAGE_METADATA.json',
        'archaeology/native-authority-v41/bootstrap/PROFILE_EXTENSION_PROTOCOL.json',
        'archaeology/native-authority-v41/bootstrap/prepare_profile.py',
        'archaeology/native-authority-v41/bootstrap/METADATA_RECEIPT.json',
        'archaeology/native-authority-v41/bootstrap/PACKAGE_EXTENSION_RECEIPT.json',
        'archaeology/native-authority-v41/bootstrap/PYPI_REQUESTS.json',
        'archaeology/native-authority-v41/bootstrap/PACKAGE_DECISIONS.json',
        'archaeology/native-authority-v41/curate_frontier.py',
        'archaeology/native-authority-v41/prepare_records.py')),
    '.github/workflows/udm-native-authority-v41.yml',
    '.github/workflows/udm-prospective-native-selection-v41.yml',
    *METADATA_EVIDENCE_FILES)))


def _guard():
    if (sha256(Path(previous.__file__).read_bytes()) != PREVIOUS_SHA256
            or sha256(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_V41_QUALIFICATION_SOURCE_CHANGED')


def inputs():
    _guard()
    if sha256((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_bytes()) != ACCEPTANCE_SHA256:
        raise ValueError('frozen V41 acceptance protocol changed')
    if sha256((HERE/'test_native_dependency_includes_v41.py').read_bytes()) != TEST_SHA256:
        raise ValueError('frozen V41 acceptance tests changed')
    acceptance = json.loads((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_text())
    for name, digest in acceptance['source_sha256'].items():
        if sha256((HERE/name).read_bytes()) != digest:
            raise ValueError('frozen native authority source changed: '+name)
    catalog = json.loads(CATALOG.read_text())
    environment.selection._catalog(catalog)
    if catalog.get('package_metadata_sha256') != sha256((RECORDS/'PACKAGE_METADATA.json').read_bytes()):
        raise ValueError('V41 catalog package metadata binding changed')
    return catalog


def _profile_identities(catalog, runtimes):
    profiles = {row['id']: row for row in catalog['profiles']}
    if not isinstance(runtimes, dict) or set(runtimes) != set(profiles):
        raise ValueError('complete independent two-profile runtime inventory required')
    result = {}
    for ident, profile in profiles.items():
        record = runtimes[ident]
        environment.validate_runtime(profile, record)
        result[ident] = {
            'environment': execution.environment_identity(record['interpreter']),
            'package_files_sha256': fingerprint(environment.installed_package_identity(
                record['interpreter'], profile))}
    return result


def _write_freeze(repo, out, runtime_paths):
    started = time.monotonic(); catalog = inputs()
    head = source_authority._git(repo, 'rev-parse', 'HEAD').decode().strip()
    paths = source_authority._git(repo, 'ls-tree', '-r', '--name-only', head).decode().splitlines()
    if not set(SOURCE_GATE_FILES) <= set(paths):
        raise ValueError('commit every V41 qualification/frontier authority source first')
    frozen = source_authority.freeze_source(repo, BASE, paths)
    profiles = {p['id']: p for p in catalog['profiles']}
    if not isinstance(runtime_paths, dict) or set(runtime_paths) != set(profiles):
        raise ValueError('complete externally supplied runtime inventory required')
    runtimes = {name: environment.freeze_runtime(runtime_paths[name]) for name in sorted(profiles)}
    frozen.update(schema=FREEZE_SCHEMA, catalog_sha256=fingerprint(catalog), runtimes=runtimes,
        profile_identities=_profile_identities(catalog, runtimes), mode='ADMISSION_ONLY',
        acceptance_sha256=ACCEPTANCE_SHA256, test_sha256=TEST_SHA256,
        freeze_wall_seconds=time.monotonic()-started)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(canonical(frozen)+'\n')
    return frozen


# Reuse the qualified source/runtime reconstruction checks in private globals.
_previous_check_freeze = FunctionType(previous.check_freeze.__code__, globals(), 'check_freeze')


def check_freeze(repo, path):
    frozen = _previous_check_freeze(repo, path)
    if (frozen.get('mode') != 'ADMISSION_ONLY' or frozen.get('test_sha256') != TEST_SHA256
            or frozen.get('all_baseline_files_preserved') is not True
            or not set(SOURCE_GATE_FILES) <= set(frozen['files'])
            or frozen.get('profile_identities') != _profile_identities(inputs(), frozen['runtimes'])):
        raise ValueError('frozen V41 profile/source authority changed')
    return frozen


def _retain_index_bytes(snapshot, destination):
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    for index, row in enumerate(snapshot['indexes']):
        if row['exists']:
            raw = Path(row['path']).read_bytes()
            if sha256(raw) != row['sha256'] or len(raw) != row['size_bytes']:
                raise ValueError('index changed while retaining pre-read bytes')
            (destination/('index-'+str(index)+'.bytes')).write_bytes(raw)
    (destination/'SNAPSHOT.json').write_text(canonical(snapshot)+'\n')


def _record_include_context(case):
    """Save reconstruction and both existing native receipts before cleanup."""
    shutil.copyfile(HERE/'test_native_dependency_includes_v41.py',
                    case.root/'test_native_dependency_includes_v41.py')
    if not hasattr(case, 'contract'):
        return
    from . import test_native_environment_selection_v3 as helpers
    identity, files, manifest = execution.original._snapshot(case.repo, case.contract['commit'])
    version = '.'.join(str(v) for v in case.environment['runtime_identity']['version_info'][:3])
    profile = helpers.profile('selected-runtime', version, case.environment['pytest_version'])
    catalog = helpers.catalog(profile)
    selection = environment.selection.select_profile(files, catalog)
    environment.selection.validate_selection(files, catalog, selection)
    reconstruction = {'label': 'INDEPENDENT_POST_TEST_SELECTION_RECONSTRUCTION_NOT_TEST_LOCAL_OBJECT',
        'source_identity': identity, 'manifest': manifest, 'catalog': catalog, 'selection': selection}
    (case.root/'selection_reconstruction.json').write_text(canonical(reconstruction)+'\n')
    certificate = json.loads((case.root/'evidence-1/admission-certificate.json').read_text())
    pair = []
    for name in ('evidence-2', 'evidence-3'):
        receipt = json.loads((case.root/name/'receipt.json').read_text())
        execution.validate_receipt(case.contract, {'replacements': []}, case.authority,
            certificate, receipt, policy=case.policy, independent=False)
        pair.append(receipt)
    if (pair[0]['status'] != 'PASS_NATIVE' or pair[1]['status'] != 'PASS_NATIVE'
            or pair[0]['junit'] != pair[1]['junit'] or pair[0]['junit']['passed'] != 2
            or {k:v for k,v in pair[0]['execution'].items() if k != 'costs'} !=
               {k:v for k,v in pair[1]['execution'].items() if k != 'costs'}):
        raise ValueError('retained included-dependency positive native pair differs')
    (case.root/'positive-pair-structural-check.json').write_text(canonical({
        'status': 'TWO_TEST_EXECUTIONS_STRUCTURALLY_VALIDATED',
        'independence': 'Frozen test independently executed evidence-3; this check launches no native attempt',
        'receipts': {name: sha256((case.root/name/'receipt.json').read_bytes())
                     for name in ('evidence-2', 'evidence-3')}})+'\n')


def _included_native_case():
    from . import test_native_authority_v4 as old
    from . import test_native_dependency_includes_v41 as tests
    base = tests.IncludedDependenciesNativeV41
    def fixture(case, *args, **kwargs):
        case.contract, case.authority = base.fixture(case, *args, **kwargs)
        return case.contract, case.authority
    def set_up(case):
        old._with_evidence_retention(base.setUp)(case)
        case.addCleanup(_record_include_context, case)
    return type(base.__name__, (base,), {'__module__': base.__module__,
                                       'setUp': set_up, 'fixture': fixture})


def _suite(legacy_only=False):
    from . import test_native_authority_v4 as old
    from . import test_native_dependency_includes_v41 as tests
    loader = unittest.defaultTestLoader
    retained = _included_native_case()
    acceptance = set(json.loads((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_text())['tests'])
    if legacy_only:
        return loader.loadTestsFromTestCase(retained), {
            name for name in acceptance if '.IncludedDependenciesNativeV41.' in name}
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(cls) for cls in (
        tests.MetadataDependencyIncludesV41, retained, old.NativeAuthorityPreservationV4,
        old.MalformedPythonNativeAuthorityV4, old.LicensedPluginReplacementAuthorityV4))
    expected = acceptance
    for cls in (old.NativeAuthorityPreservationV4, old.MalformedPythonNativeAuthorityV4,
                old.LicensedPluginReplacementAuthorityV4):
        expected.update(case.id() for case in loader.loadTestsFromTestCase(cls))
    if suite.countTestCases() != 47 or len(expected) != 47:
        raise ValueError('frozen 27 new plus 20 native preservation controls required')
    return suite, expected


def _positive_pair(out):
    name = (__package__+'.test_native_dependency_includes_v41.IncludedDependenciesNativeV41.'
            'test_selected_actual_runtime_include_allows_real_native_pass_and_independent_reexecution')
    root = Path(out)/'native-evidence'/name
    checked = json.loads((root/'positive-pair-structural-check.json').read_text())
    selection = json.loads((root/'selection_reconstruction.json').read_text())
    if selection['selection']['status'] != 'CANDIDATE_SOURCE_ENVIRONMENT':
        raise ValueError('retained selection reconstruction is not a source candidate')
    rows = []
    for name, digest in checked['receipts'].items():
        path = root/name/'receipt.json'; receipt = json.loads(path.read_text())
        if sha256(path.read_bytes()) != digest:
            raise ValueError('retained positive receipt bytes changed')
        for key, encoded in receipt['packet'].items():
            raw = base64.b64decode(encoded, validate=True)
            if (sha256(raw) != receipt['packet_sha256'][key]
                    or (root/name/'execution'/key).read_bytes() != raw):
                raise ValueError('retained positive raw native packet differs from receipt')
        if (receipt['status'] != 'PASS_NATIVE' or receipt['junit']['passed'] != 2
                or receipt['costs']['native_calls'] != 1):
            raise ValueError('positive native execution pair is incomplete')
        rows.append({'output': str(path.relative_to(out)), 'sha256': digest,
                     **{k:receipt[k] for k in ('status', 'junit', 'costs')}})
    if len(rows) != 2:
        raise ValueError('both positive native executions must be retained')
    return {'status': 'PASS_NATIVE', 'executions': rows,
            'selection_reconstruction': str((root/'selection_reconstruction.json').relative_to(out))}


def qualify(repo, freeze, out, *, legacy_only=False):
    before = snapshot_indexes(repo); os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    out = Path(out).absolute(); out.mkdir(parents=True, exist_ok=False)
    _retain_index_bytes(before, out/'index-before')
    started = time.monotonic(); attempts = execution.attempt_snapshot()
    result = {'schema': RESULT_SCHEMA, 'status': 'UNKNOWN_ADMISSION',
        'mode': 'LEGACY_NATIVE_CONTROLS_ONLY' if legacy_only else 'ADMISSION_ONLY',
        'first_task_gate': {'status': 'UNKNOWN'}, 'acquisitions': 0, 'candidates': 0,
        'verdicts': {'G0_G1': 'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY',
                     **{f'G{i}':'UNKNOWN' for i in range(2, 7)}},
        'cost_boundary': 'Worker native/collection attempts and observed wall; full lifecycle/model/tool/engineering costs UNKNOWN.'}
    saved_env = {key: os.environ.get(key) for key in
                 ('UDM_V4_NATIVE_EVIDENCE_ROOT', 'UDM_NATIVE_V3_INTERPRETER')}
    try:
        frozen = check_freeze(repo, freeze)
        result.update(source_commit=frozen['source_commit'], freeze=frozen)
        choose = min if legacy_only else max
        modern = choose(frozen['runtimes'].values(), key=lambda row:row['identity']['version_info'][:3])
        os.environ.update(UDM_V4_NATIVE_EVIDENCE_ROOT=str(out/'native-evidence'),
                          UDM_NATIVE_V3_INTERPRETER=modern['interpreter'])
        suite, expected = _suite(legacy_only)
        with (out/'contracts.log').open('w') as stream, retained_temporary_outputs(out/'default-collection-evidence'):
            RecordedResult.ids = []
            verdict = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult).run(suite)
        result['contracts'] = {'run': verdict.testsRun, 'ids': sorted(verdict.ids),
            'failures': len(verdict.failures), 'errors': len(verdict.errors),
            'skipped': len(verdict.skipped), 'successful': verdict.wasSuccessful()}
        result['runtime_scope'] = {'new_acceptance_controls': 2 if legacy_only else 27,
            'old_native_controls': 0 if legacy_only else 20,
            'selected_profile_native_controls': 1 if legacy_only else 6,
            'controller_native_controls': 0 if legacy_only else 15,
            'controller_environment': execution.environment_identity(os.sys.executable),
            'selected_profile_interpreter': modern['interpreter']}
        result['positive_independent_native'] = _positive_pair(out)
        check_freeze(repo, freeze)
        current = execution.attempt_snapshot()
        if (verdict.wasSuccessful() and verdict.ids and set(verdict.ids) == expected
                and len(verdict.ids) == len(expected) == (2 if legacy_only else 47) and not verdict.skipped
                and current['native_calls'] > attempts['native_calls']
                and current['collection_calls'] > attempts['collection_calls']):
            if legacy_only:
                result['status'] = 'LEGACY_NATIVE_CONTROLS_VERIFIED'
            else:
                result.update(status='ADMISSION_ONLY_QUALIFIED',
                    first_task_gate={'status': 'PASS', 'boundary': 'Frozen synthetic metadata/native admission controls only'})
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        result['error'] = type(error).__name__+': '+str(error)
    finally:
        for key, value in saved_env.items():
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value
        after = snapshot_indexes(repo); _retain_index_bytes(after, out/'index-after')
        result['index_audit'] = {'before': before, 'after': after, 'changes': compare_indexes(before, after)}
        if result['index_audit']['changes']:
            result.update(status='UNKNOWN_ADMISSION', first_task_gate={'status':'UNKNOWN'})
        current = execution.attempt_snapshot()
        result['attempt_costs'] = {key:current[key]-attempts[key] for key in current}
        result['total_wall_seconds'] = time.monotonic()-started
        (out/'RESULT.json').write_text(canonical(result)+'\n')
    return result


def write_freeze(repo, out, runtime_paths):
    before = snapshot_indexes(repo); os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    path = Path(out).absolute()
    if any(p.exists() for p in (path, *(path.with_name(path.name+suffix) for suffix in
           ('.INDEX_AUDIT.json', '.INDEX_BEFORE', '.INDEX_AFTER')))):
        raise ValueError('refusing to replace existing source freeze or index audit')
    # The original source freezer requires a clean commit. Keep pre-Git copies
    # outside the checkout until that check has completed, including on failure.
    with tempfile.TemporaryDirectory(prefix='udm-v41-prefreeze-index-') as scratch:
        retained = Path(scratch)/'before'; _retain_index_bytes(before, retained)
        try:
            return _write_freeze(repo, path, runtime_paths)
        finally:
            after = snapshot_indexes(repo)
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(retained, path.with_name(path.name+'.INDEX_BEFORE'))
            _retain_index_bytes(after, path.with_name(path.name+'.INDEX_AFTER'))
            audit = {'before':before, 'after':after, 'changes':compare_indexes(before, after)}
            path.with_name(path.name+'.INDEX_AUDIT.json').write_text(canonical(audit)+'\n')
            if audit['changes']:
                raise ValueError('Git index changed during V41 freeze; original evidence retained')


def main():
    os.environ.update(GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True); parser.add_argument('--out', required=True)
    parser.add_argument('--runtimes'); parser.add_argument('--freeze')
    parser.add_argument('--write-freeze', action='store_true')
    parser.add_argument('--legacy-native-controls', action='store_true')
    args = parser.parse_args()
    if args.write_freeze:
        result = write_freeze(args.repo, args.out, json.loads(Path(args.runtimes).read_text()))
    else:
        result = qualify(args.repo, args.freeze, args.out, legacy_only=args.legacy_native_controls)
    print(canonical({'status':result.get('status', result.get('schema')), 'verdicts':result.get('verdicts', {})}))
    expected = 'LEGACY_NATIVE_CONTROLS_VERIFIED' if args.legacy_native_controls else 'ADMISSION_ONLY_QUALIFIED'
    if not args.write_freeze and result['status'] != expected:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
