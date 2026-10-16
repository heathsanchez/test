"""Frozen v4.1 contracts for literal, tracked dependency-file includes.

``UDM_INCLUDES_BASELINE=v4 python -B -m unittest <this module> -v`` runs
behavioral RED against the actual V4 selector.  The normal import is lazy so
absence of the future module is never the reason for the recorded RED result.
Native authority uses the existing real V3 worker and disposable Git fixtures.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import unittest

from . import decisive_native_verify as original
from . import native_execution_v3 as execution
from . import test_native_environment_selection_v3 as metadata_helpers
from . import test_native_execution_v3 as native_helpers


BASELINE_VARIABLE = 'UDM_INCLUDES_BASELINE'
METADATA = b'[project]\nrequires-python=">=3.11,<3.13"\n'
MALFORMED = b'def invalid(:\n    print "python two corpus"\n'
INCLUDE_FORMS = ('-r deps/root.in', '-rdeps/root.in', '--requirement deps/root.in')
REQUIREMENT_ROOTS = (
    'requirements-test.txt', 'requirements-tests.txt', 'test-requirements.txt',
    'tests-requirements.txt', 'requirements/test.txt', 'requirements/tests.txt',
    'requirements/testing.txt', 'tests/requirements.txt',
)


def selector():
    baseline = os.environ.get(BASELINE_VARIABLE)
    if baseline not in (None, 'v4'):
        raise ValueError('only the explicit v4 RED baseline alias is accepted')
    version = 'v4' if baseline == 'v4' else 'v41'
    return importlib.import_module(__package__ + '.native_environment_selection_' + version)


def inventory_hash(files):
    rows = {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(files.items())}
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def tox_files(directive='-r deps/root.in', body=b'attrs>=25\n'):
    return {'pyproject.toml': METADATA,
            'tox.ini': ('[tox]\nenvlist=py{311,312}\n[testenv]\ndeps=\n    ' + directive + '\n').encode(),
            'deps/root.in': body}


class MetadataDependencyIncludesV41(unittest.TestCase):
    def select(self, files, *profiles):
        return selector().select_profile(files, metadata_helpers.catalog(
            *(profiles or (metadata_helpers.profile(packages=['attrs==25.4.0']),))))

    def derived(self, files):
        result = selector().derive_constraints(files)
        self.assertEqual(result['status'], 'DERIVED_SOURCE_CONSTRAINTS', result)
        self.assertEqual(result['source_sha256'], inventory_hash(files))
        return result

    def candidate(self, files, *profiles):
        result = self.select(files, *profiles)
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', result)
        self.assertEqual(result['constraints']['source_sha256'], inventory_hash(files))
        return result

    def refused(self, files, reason='UNKNOWN_REQUIREMENT_GRAMMAR'):
        result = self.select(files)
        self.assertEqual(result['status'], 'UNKNOWN', result)
        self.assertEqual(result['reason'], reason, result)
        self.assertEqual(result['constraints']['status'], 'UNKNOWN', result)
        self.assertEqual(result['constraints']['reasons'][0]['reason'], reason, result)
        self.assertIsNone(result['selected_profile'])
        return result

    def assert_file_evidence(self, constraints, files, path):
        digest = hashlib.sha256(files[path]).hexdigest()
        self.assertEqual(constraints['metadata_sha256'][path], digest)
        self.assertIn({'path': path, 'field': 'test-requirements', 'value': digest},
                      constraints['evidence'])

    def test_global_tox_spaced_include_constrains_real_catalog_pins(self):
        result = self.candidate(tox_files(),
            metadata_helpers.profile('underpinned', '3.11.9', packages=['attrs==24.1.0']),
            metadata_helpers.profile('valid', packages=['attrs==25.4.0']))
        self.assertEqual(result['selected_profile']['id'], 'valid')
        self.assertEqual([row['status'] for row in result['candidates']], ['UNKNOWN', 'COMPATIBLE'])
        self.assertEqual(result['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')

    def test_global_tox_compact_include_is_supported(self):
        constraints = self.derived(tox_files('-rdeps/root.in'))
        self.assertIn({'requirement': 'attrs>=25', 'path': 'deps/root.in',
                       'field': 'test-requirements', 'extra': ''}, constraints['requirements'])

    def test_global_tox_long_spaced_include_is_supported(self):
        self.candidate(tox_files('--requirement deps/root.in'))

    def test_existing_requirement_roots_retain_all_three_include_forms(self):
        for root in REQUIREMENT_ROOTS:
            parent = str(Path(root).parent)
            leaf = ('deps/root.in' if parent == '.' else parent + '/deps/root.in')
            for directive in INCLUDE_FORMS:
                with self.subTest(root=root, directive=directive):
                    files = {'pyproject.toml': METADATA, root: (directive + '\n').encode(),
                             leaf: b'attrs>=25\n'}
                    constraints = self.derived(files)
                    self.assertIn({'requirement': 'attrs>=25', 'path': leaf,
                                   'field': 'test-requirements', 'extra': ''}, constraints['requirements'])
                    self.assert_file_evidence(constraints, files, root)
                    self.assert_file_evidence(constraints, files, leaf)

    def test_recursive_relative_includes_preserve_leaf_provenance_and_raw_hashes(self):
        files = tox_files(body=b'# root comment\n--requirement nested/base.in\npytest>=8 # runner\n')
        files['deps/nested/base.in'] = b'\n-rleaf.in # recursive include\n'
        files['deps/nested/leaf.in'] = b'attrs>=25 # leaf declaration\n'
        constraints = self.derived(files)
        self.assertIn({'requirement': 'attrs>=25', 'path': 'deps/nested/leaf.in',
                       'field': 'test-requirements', 'extra': ''}, constraints['requirements'])
        self.assertIn({'requirement': 'pytest>=8', 'path': 'deps/root.in',
                       'field': 'test-requirements', 'extra': ''}, constraints['requirements'])
        for path in ('deps/root.in', 'deps/nested/base.in', 'deps/nested/leaf.in'):
            self.assert_file_evidence(constraints, files, path)
        self.assertEqual(constraints['metadata_sha256']['tox.ini'], hashlib.sha256(files['tox.ini']).hexdigest())
        self.assertTrue(any(row['path'] == 'tox.ini' and row['field'] == 'testenv.deps'
                            and '-r deps/root.in' in row['value'] for row in constraints['evidence']))

    def test_duplicate_include_is_not_a_cycle_and_deduplicates_equal_leaf_rows(self):
        files = tox_files(body=b'-r nested/leaf.in\n-rnested/leaf.in\n--requirement nested/leaf.in\n')
        files['deps/nested/leaf.in'] = b'attrs>=25\nattrs>=25\n'
        constraints = self.derived(files)
        self.assertEqual([row for row in constraints['requirements'] if row['path'] == 'deps/nested/leaf.in'],
                         [{'requirement': 'attrs>=25', 'path': 'deps/nested/leaf.in',
                           'field': 'test-requirements', 'extra': ''}])
        self.assert_file_evidence(constraints, files, 'deps/nested/leaf.in')

    def test_python_specific_nested_includes_keep_markers_and_scope(self):
        files = {'pyproject.toml': METADATA,
                 'tox.ini': b'[tox]\nenvlist=py{311,312}\n[testenv:py311]\ndeps=-r deps/old.in\n[testenv:py312]\ndeps=-rdeps/new.in\n',
                 'deps/old.in': b'-r shared/old.in\n',
                 'deps/new.in': b'--requirement shared/new.in\n',
                 'deps/shared/old.in': b'attrs<25; python_version < "3.12"\n',
                 'deps/shared/new.in': b'attrs>=25; python_version >= "3.12"\n'}
        result = self.candidate(files,
            metadata_helpers.profile('old', '3.11.9', packages=['attrs==24.1.0']),
            metadata_helpers.profile('modern', packages=['attrs==25.4.0']))
        self.assertEqual([row['status'] for row in result['candidates']], ['COMPATIBLE', 'COMPATIBLE'])
        self.assertEqual(result['selected_profile']['id'], 'modern')
        for path, minor, requirement in (
                ('deps/shared/old.in', '3.11', 'attrs<25; python_version < "3.12"'),
                ('deps/shared/new.in', '3.12', 'attrs>=25; python_version >= "3.12"')):
            self.assertIn({'requirement': requirement, 'path': path, 'field': 'test-requirements',
                           'extra': '', 'python_versions': [minor]}, result['constraints']['requirements'])
            self.assert_file_evidence(result['constraints'], files, path)
        for section in ('testenv:py311.deps', 'testenv:py312.deps'):
            self.assertTrue(any(row['path'] == 'tox.ini' and row['field'] == section
                                for row in result['constraints']['evidence']))

    def test_shared_leaf_retains_global_and_each_python_applicability_context(self):
        files = tox_files()
        files['tox.ini'] += b'[testenv:py311]\ndeps=-r deps/root.in\n[testenv:py312]\ndeps=--requirement deps/root.in\n'
        constraints = self.derived(files)
        scopes = [row.get('python_versions') for row in constraints['requirements'] if row['path'] == 'deps/root.in']
        self.assertCountEqual(scopes, [None, ['3.11'], ['3.12']])

    def test_scoped_only_leaf_is_not_promoted_to_a_global_requirement(self):
        files = {'pyproject.toml': METADATA,
                 'tox.ini': b'[tox]\nenvlist=py{311,312}\n[testenv:py311]\ndeps=-r deps/old.in\n',
                 'deps/old.in': b'legacy-only>=1\n'}
        result = self.candidate(files,
            metadata_helpers.profile('old', '3.11.9', packages=['legacy-only==1.0']),
            metadata_helpers.profile())
        self.assertEqual([row['status'] for row in result['candidates']], ['COMPATIBLE', 'COMPATIBLE'])
        self.assertEqual(result['constraints']['requirements'], [
            {'requirement': 'legacy-only>=1', 'path': 'deps/old.in', 'field': 'test-requirements',
             'extra': '', 'python_versions': ['3.11']}])

    def test_markers_use_external_profile_environment_and_retain_provenance(self):
        files = tox_files(body=b'windows-only>=1; sys_platform == "win32"\n')
        linux = metadata_helpers.profile(marker_environment={'sys_platform': 'linux'})
        result = self.candidate(files, linux)
        self.assertEqual(result['constraints']['requirements'], [
            {'requirement': 'windows-only>=1; sys_platform == "win32"', 'path': 'deps/root.in',
             'field': 'test-requirements', 'extra': ''}])
        missing = self.select(files, metadata_helpers.profile())
        self.assertEqual(missing['status'], 'UNKNOWN')
        self.assertEqual(missing['candidates'][0]['reason'], 'UNKNOWN_MARKER_ENVIRONMENT')
        windows = self.select(files, metadata_helpers.profile(marker_environment={'sys_platform': 'win32'}))
        self.assertEqual(windows['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')

    def test_every_included_and_unparsed_byte_remains_in_complete_inventory(self):
        files = tox_files()
        files.update({'fixtures/legacy.py': MALFORMED, 'fixtures/payload.pydata': b'\xff\x00\x81',
                      'README.md': b'original\n'})
        constraints = self.derived(files)
        self.assertFalse(any(row['path'].startswith('fixtures/') for row in constraints['evidence']))
        for path in files:
            with self.subTest(path=path):
                changed = {**files, path: files[path] + b'\n'}
                current = self.derived(changed)
                self.assertNotEqual(current['source_sha256'], constraints['source_sha256'])
                if path == 'deps/root.in':
                    self.assertNotEqual(current['metadata_sha256'][path], constraints['metadata_sha256'][path])

    def test_selection_replay_after_included_or_unparsed_byte_change_is_rejected(self):
        files = tox_files()
        files['fixtures/unparsed.py'] = MALFORMED
        catalog = metadata_helpers.catalog(metadata_helpers.profile(packages=['attrs==25.4.0']))
        selected = self.candidate(files)
        self.assertEqual(selector().validate_selection(files, catalog, selected), selected)
        for path in ('deps/root.in', 'fixtures/unparsed.py'):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, 'UNKNOWN_SELECTION_IDENTITY'):
                    selector().validate_selection({**files, path: files[path] + b'# changed\n'}, catalog, selected)

    def test_forged_requirements_evidence_hash_scope_and_profile_are_rejected(self):
        files = tox_files()
        catalog = metadata_helpers.catalog(metadata_helpers.profile(packages=['attrs==25.4.0']))
        selected = self.candidate(files)
        variants = []
        forged = copy.deepcopy(selected); forged['constraints']['requirements'] = []; variants.append(forged)
        forged = copy.deepcopy(selected); forged['constraints']['evidence'] = []; variants.append(forged)
        forged = copy.deepcopy(selected); forged['constraints']['metadata_sha256']['deps/root.in'] = '0' * 64; variants.append(forged)
        forged = copy.deepcopy(selected); forged['constraints']['requirements'][0]['python_versions'] = ['3.11']; variants.append(forged)
        forged = copy.deepcopy(selected); forged['selected_profile']['packages'] = ['pytest==8.4.1']; variants.append(forged)
        for index, forged in enumerate(variants):
            with self.subTest(forgery=index):
                with self.assertRaisesRegex(ValueError, 'UNKNOWN_SELECTION_IDENTITY'):
                    selector().validate_selection(files, catalog, forged)

    def test_unsatisfied_included_dependency_remains_unknown(self):
        result = self.select(tox_files(body=b'not-in-the-external-catalog>=1\n'))
        self.assertEqual(result['constraints']['status'], 'DERIVED_SOURCE_CONSTRAINTS', result)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'UNKNOWN_NO_COMPATIBLE_PROFILE')
        self.assertEqual(result['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')
        self.assertIsNone(result['selected_profile'])

    def test_existing_root_unsatisfied_dependency_control_remains_unknown(self):
        files = {'pyproject.toml': METADATA, 'requirements-test.txt': b'not-in-the-external-catalog>=1\n'}
        result = self.select(files)
        self.assertEqual(result['reason'], 'UNKNOWN_NO_COMPATIBLE_PROFILE')
        self.assertEqual(result['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')

    def test_unreferenced_requirement_like_files_do_not_become_metadata(self):
        files = {'pyproject.toml': METADATA, 'deps/unreferenced.in': b'-e unlicensed\n',
                 'fixtures/legacy.py': MALFORMED}
        result = self.candidate(files)
        self.assertEqual(result['constraints']['requirements'], [])
        self.assertNotIn('deps/unreferenced.in', result['constraints']['metadata_sha256'])

    def test_long_equals_and_malformed_include_spellings_remain_precise_unknown(self):
        for directive in ('--requirement=deps/root.in', '-r', '--requirement', '-r ',
                          '--requirements deps/root.in', '-R deps/root.in'):
            for origin in ('tox', 'known-root'):
                with self.subTest(directive=directive, origin=origin):
                    files = tox_files(directive)
                    if origin == 'known-root':
                        files.pop('tox.ini')
                        files['requirements-test.txt'] = (directive + '\n').encode()
                    self.refused(files)

    def test_missing_self_and_mutual_cyclic_includes_are_precise_unknown(self):
        for root in (b'-r absent.in\n', b'-rroot.in\n', b'-r nested/other.in\n'):
            with self.subTest(root=root):
                files = {'pyproject.toml': METADATA, 'requirements-test.txt': b'-r deps/root.in\n',
                         'deps/root.in': root, 'deps/nested/other.in': b'-r loop.in\n',
                         'deps/nested/loop.in': b'-r other.in\n'}
                self.refused(files)
        self.refused(tox_files('-r absent.in'))

    def test_noncanonical_parent_absolute_url_and_backslash_targets_are_refused(self):
        targets = ('../escape.in', '/tmp/dependency.in', './deps/root.in', 'deps//root.in',
                   'https://example.invalid/deps.in', 'file:///tmp/deps.in', 'deps\\root.in')
        for target in targets:
            for prefix in ('-r ', '-r', '--requirement '):
                with self.subTest(target=target, prefix=prefix):
                    self.refused({'pyproject.toml': METADATA,
                                  'requirements-test.txt': (prefix + target + '\n').encode()})

    def test_unsupported_pip_directives_and_hash_suffix_are_not_package_authority(self):
        lines = ('-e .', '--editable .', '-c constraints.in', '--constraint constraints.in',
                 '--index-url https://example.invalid/simple', '--extra-index-url https://example.invalid/simple',
                 '--find-links wheels', '--hash=sha256:abcd', '--require-hashes',
                 'attrs==25.4.0 --hash=sha256:abcd', 'attrs @ https://example.invalid/a.whl', 'attrs===arbitrary')
        for line in lines:
            with self.subTest(line=line):
                self.refused({'pyproject.toml': METADATA, 'requirements-test.txt': b'-r deps/root.in\n',
                              'deps/root.in': (line + '\n').encode()})

    def test_dynamic_tox_substitution_and_factor_deps_are_not_evaluated(self):
        for directive in ('-r {toxinidir}/deps/root.in', '-r {env:REQ_FILE}',
                          '-r {env:REQ_FILE:deps/root.in}', '{[testenv:other]deps}',
                          'py311: -r deps/root.in'):
            with self.subTest(directive=directive):
                self.refused(tox_files(directive))

    def test_invalid_source_paths_and_nonbyte_values_remain_source_unknown(self):
        for path in ('../escape.in', '/absolute.in', './deps/root.in', 'deps//root.in',
                     'https://example.invalid/deps.in', 'deps\\root.in'):
            with self.subTest(path=path):
                self.refused({'pyproject.toml': METADATA, path: b'attrs>=25\n'}, 'UNKNOWN_SOURCE_INPUT')
        for value in ({'target': 'deps/root.in'}, Path('deps/root.in'), 'deps/root.in'):
            with self.subTest(value=repr(value)):
                self.refused({'pyproject.toml': METADATA, 'deps/link.in': value}, 'UNKNOWN_SOURCE_INPUT')

    def test_static_setup_and_unparsed_python_are_not_executed_during_inference(self):
        files = tox_files()
        files['setup.py'] = (b'raise RuntimeError("must not execute metadata")\n'
                             b'from setuptools import setup\nsetup(python_requires=">=3.11,<3.13")\n')
        files['fixtures/legacy.py'] = MALFORMED
        self.candidate(files)

    def test_malformed_and_dynamic_setup_controls_keep_exact_refusals(self):
        files = tox_files()
        self.refused({**files, 'setup.py': MALFORMED}, 'UNKNOWN_SOURCE_PARSER')
        self.refused({**files, 'setup.py': b'from setuptools import setup\nsetup(python_requires=load())\n'},
                     'UNKNOWN_DYNAMIC_METADATA')

    def test_unchanged_input_order_has_identical_constraints_and_selection(self):
        files = tox_files(body=b'-r nested/leaf.in\n')
        files['deps/nested/leaf.in'] = b'attrs>=25\n'
        reversed_files = dict(reversed(list(files.items())))
        self.assertEqual(self.derived(files), self.derived(reversed_files))
        self.assertEqual(self.candidate(files), self.candidate(reversed_files))


class IncludedDependenciesNativeV41(unittest.TestCase):
    setUpClass = classmethod(native_helpers.SelectedInterpreterNativeContracts.setUpClass.__func__)
    setUp = native_helpers.SelectedInterpreterNativeContracts.setUp
    git = native_helpers.SelectedInterpreterNativeContracts.git
    commit = native_helpers.SelectedInterpreterNativeContracts.commit
    fixture = native_helpers.SelectedInterpreterNativeContracts.fixture
    output = native_helpers.SelectedInterpreterNativeContracts.output

    def test_selected_actual_runtime_include_allows_real_native_pass_and_independent_reexecution(self):
        runtime = self.environment['runtime_identity']['version_info']
        version = '.'.join(str(value) for value in runtime[:3])
        (self.repo / 'pyproject.toml').write_bytes(b'[project]\nrequires-python=">=3.6,<4"\n')
        (self.repo / 'tox.ini').write_text('[tox]\nenvlist=py' + str(runtime[0]) + str(runtime[1]) +
                                         '\n[testenv]\ndeps=-rdeps/runtime.in\n')
        (self.repo / 'deps').mkdir()
        (self.repo / 'deps/runtime.in').write_text('pytest==' + self.environment['pytest_version'] + '\n')
        (self.repo / 'fixtures').mkdir()
        (self.repo / 'fixtures/python2_payload.pydata').write_bytes(MALFORMED + b'\xff\x00')
        self.base = self.commit()
        contract, authority = self.fixture('def test_old(): assert True\ndef test_new(): assert True\n')
        files = original._snapshot(self.repo, contract['commit'])[1]
        profile = metadata_helpers.profile('selected-runtime', version, self.environment['pytest_version'])
        catalog = metadata_helpers.catalog(profile)
        selected = selector().select_profile(files, catalog)
        self.assertEqual(selected['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', selected)
        self.assertEqual(selected['selected_profile'], profile)
        self.assertEqual(selected['constraints']['source_sha256'], inventory_hash(files))
        self.assertEqual(selector().validate_selection(files, catalog, selected), selected)
        self.assertIn({'requirement': 'pytest==' + self.environment['pytest_version'], 'path': 'deps/runtime.in',
                       'field': 'test-requirements', 'extra': ''}, selected['constraints']['requirements'])
        certificate = execution.collect(contract, authority, self.output(), policy=self.policy)
        receipt = execution.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                   admission_certificate=certificate, policy=self.policy)
        self.assertEqual(receipt['status'], 'PASS_NATIVE', receipt)
        self.assertEqual(receipt['junit']['passed'], 2)
        checked = execution.validate_receipt(contract, {'replacements': []}, authority, certificate, receipt,
            policy=self.policy, output_dir=self.output(), independent=True)
        self.assertEqual(checked['status'], 'PASS_NATIVE')
        self.assertIn('independent_reexecution', checked)

    def test_real_git_symlink_include_cannot_enter_regular_file_snapshot(self):
        (self.repo / 'deps').mkdir()
        (self.repo / 'deps/real.in').write_text('pytest>=1\n')
        (self.repo / 'deps/link.in').symlink_to('real.in')
        (self.repo / 'tox.ini').write_text('[tox]\nenvlist=py312\n[testenv]\ndeps=-rdeps/link.in\n')
        commit = self.commit()
        with self.assertRaisesRegex(ValueError, 'only regular tracked files supported'):
            original._snapshot(self.repo, commit)


if __name__ == '__main__':
    unittest.main()
