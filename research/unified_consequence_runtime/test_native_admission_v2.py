"""Static v2 admission authority tests; no target or protected suite execution."""
import copy
import importlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from research.unified_consequence_runtime import decisive_native_verify as v1


class NativeAdmissionV2(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(
            'research.unified_consequence_runtime.native_admission_v2'),
            'versioned admission module is required')
        self.admission = importlib.import_module(
            'research.unified_consequence_runtime.native_admission_v2')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'; self.repo.mkdir()
        self.git('init', '-q')
        (self.repo / 'tests').mkdir()
        (self.repo / 'sample.py').write_text('VALUE = 42\n')
        (self.repo / 'pytest.ini').write_text('[pytest]\naddopts = -q\n')
        (self.repo / 'tests/test_sample.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Admission Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def derive(self, source='def test_old(): assert True\ndef test_new(): assert True\n'):
        (self.repo / 'tests/test_sample.py').write_text(source)
        self.commit_id = self.commit()
        return self.admission.derive_suite_contract(self.repo, self.base, self.commit_id,
            'e' * 64, repository='local/admission')

    def test_literal_container_data_is_not_a_registered_test(self):
        authority = self.derive('test_inputs = [None, False, 1, "a", ([], {}), {1, 2}]\n'
            'other_data = {"value": [1]}\ntest_examples = other_data\n'
            'class TestCases:\n test_data: list = [1, 2]\n def test_new(self): assert test_inputs\n')
        self.assertEqual(authority['required_test_nodes'], ['tests/test_sample.py::TestCases::test_new'])
        self.assertNotEqual(authority['schema'], v1.NATIVE_SUITE_SCHEMA)
        self.assertEqual(authority['test_source_sha256'], {
            'tests/test_sample.py': v1.sha256((self.repo / 'tests/test_sample.py').read_bytes())})

    def test_callable_aliases_and_imported_test_bindings_fail_closed(self):
        bad = ['test_alias = lambda: None', 'test_alias = helper', 'test_alias = module.helper',
            'test_alias = factory()', 'from other import test_alias',
            'from other import helper as test_alias', 'import other as test_alias',
            'from other import *', 'test_alias, other = helper, 1',
            'test_alias: object = helper', 'test_alias = [1]\ntest_alias += helper',
            'test_alias = [1]\ntest_alias = helper']
        for statement in bad:
            with self.subTest(statement=statement), self.assertRaisesRegex(ValueError, 'UNKNOWN_SUITE_CONTRACT'):
                self.derive('def test_new(): assert True\n' + statement + '\n')

    def test_dynamic_conditional_nested_and_duplicate_tests_fail_closed(self):
        bad = ['globals()["test_alias"] = lambda: None',
            'setattr(module, "test_alias", helper)', 'vars(module)["test_alias"] = helper',
            'module.__dict__["test_alias"] = helper', 'module.test_alias = helper',
            'if True:\n def test_other(): assert True',
            'if True:\n test_alias = [1]',
            'def helper():\n def test_nested(): assert True',
            'def test_new(): assert False']
        for statement in bad:
            with self.subTest(statement=statement), self.assertRaisesRegex(ValueError, 'UNKNOWN_SUITE_CONTRACT'):
                self.derive('def test_new(): assert True\n' + statement + '\n')

    def test_actual_functions_with_default_pytest_prefix_are_bound(self):
        authority = self.derive('def testwithoutunderscore(): assert True\n')
        self.assertEqual(authority['required_test_nodes'], ['tests/test_sample.py::testwithoutunderscore'])

    def test_unittest_mixin_methods_map_to_every_concrete_descendant(self):
        authority = self.derive('from unittest import TestCase as Case\n'
            'class SharedChecks:\n def test_inherited(self): assert True\n'
            'class First(SharedChecks, Case): pass\n'
            'class Second(SharedChecks, Case): pass\n')
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::First::test_inherited',
            'tests/test_sample.py::Second::test_inherited'])

    def test_unittest_module_alias_and_local_ancestry_ignore_pytest_class_patterns(self):
        authority = self.derive('import unittest as unit\n'
            'class Common(unit.TestCase):\n def test_base(self): assert True\n'
            'class Concrete(Common):\n def test_added(self): assert True\n')
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::Common::test_base',
            'tests/test_sample.py::Concrete::test_added',
            'tests/test_sample.py::Concrete::test_base'])

    def test_changed_mixin_assertion_cannot_hide_behind_an_override(self):
        with self.assertRaisesRegex(ValueError, 'uncollected|unreachable|mapping'):
            self.derive('from unittest import TestCase\n'
                'class Shared:\n def test_hidden(self): assert False\n'
                'class Concrete(Shared, TestCase):\n def test_hidden(self): assert True\n')

    def test_unmodified_overridden_mixin_assertions_do_not_require_impossible_nodes(self):
        original = ('from unittest import TestCase\n'
            'class Shared:\n def test_hidden(self): assert False\n'
            'class Concrete(Shared, TestCase):\n def test_hidden(self): assert True\n')
        (self.repo / 'tests/test_sample.py').write_text(original)
        self.base = self.commit()
        authority = self.derive(original + 'def test_new(): assert True\n')
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::Concrete::test_hidden', 'tests/test_sample.py::test_new'])

    def test_mixin_assertion_with_one_shadow_and_one_live_route_is_bound(self):
        authority = self.derive('from unittest import TestCase\n'
            'class Shared:\n def test_protected(self): assert False\n'
            'class Inheriting(Shared, TestCase): pass\n'
            'class Overriding(Shared, TestCase):\n def test_protected(self): assert True\n')
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::Inheriting::test_protected',
            'tests/test_sample.py::Overriding::test_protected'])

    def test_c3_diamond_maps_the_actual_winning_method(self):
        original = ('class Shared:\n def test_protected(self): assert False\n'
            'class Left(Shared): pass\n'
            'class Right(Shared):\n def test_protected(self): assert True\n'
            'class TestConcrete(Left, Right): pass\n')
        (self.repo / 'tests/test_sample.py').write_text(original)
        self.base = self.commit()
        authority = self.derive(original.replace('assert True', 'assert 2 == 2'))
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::TestConcrete::test_protected'])

    def test_cached_static_authority_cannot_claim_changed_source_bytes(self):
        with patch.object(self.admission, '_LOADED_SOURCE_SHA256', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_ADMISSION_SOURCE_MUTATION'):
                self.derive()
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_ADMISSION_SOURCE_MUTATION'):
                self.admission.validate_candidate({'replacements': []}, {})

    def test_unmapped_nested_class_assertions_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'nested|mapping'):
            self.derive('class TestOuter:\n class TestInner:\n'
                '  def test_nested(self): assert False\n'
                'def test_new(): assert True\n')

    def test_unknown_dynamic_bases_with_protected_methods_fail_closed(self):
        for base in ('factory()', 'ExternalBase', 'external.TestCase'):
            with self.subTest(base=base), self.assertRaisesRegex(ValueError, 'base|mapping'):
                self.derive('class TestChecks(' + base + '):\n def test_new(self): assert True\n')

    def test_ordinary_uncollected_helper_classes_are_not_required_nodes(self):
        original = ('class Helper:\n def test_protocol(self): return True\n'
            'def test_old(): assert True\n')
        (self.repo / 'tests/test_sample.py').write_text(original)
        self.base = self.commit()
        authority = self.derive(original + 'def test_new(): assert True\n')
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::test_new', 'tests/test_sample.py::test_old'])

    def test_pytest_custom_class_and_function_patterns_preserve_inherited_assertions(self):
        (self.repo / 'pytest.ini').write_text('[pytest]\npython_classes = Check\npython_functions = check_\n')
        self.base = self.commit()
        authority = self.derive('class Shared:\n def check_inherited(self): assert True\n'
            'class CheckConcrete(Shared):\n def check_new(self): assert True\n')
        self.assertEqual(authority['required_test_nodes'], [
            'tests/test_sample.py::CheckConcrete::check_inherited',
            'tests/test_sample.py::CheckConcrete::check_new'])

    def test_unittest_method_prefix_is_independent_of_pytest_function_patterns(self):
        (self.repo / 'pytest.ini').write_text('[pytest]\npython_functions = check_\n')
        self.base = self.commit()
        authority = self.derive('from unittest.case import TestCase as Case\n'
            'class Concrete(Case):\n def test_native(self): assert True\n')
        self.assertEqual(authority['required_test_nodes'], ['tests/test_sample.py::Concrete::test_native'])

    def test_configuration_preserves_lawful_original_import_and_reporting_options(self):
        parsed = self.admission.configuration({'pyproject.toml': b'''[tool.pytest.ini_options]
addopts = ['-ra', '--strict-markers', '--strict-config', '--import-mode=importlib', '-l']
testpaths = 'tests'
xfail_strict = true
filterwarnings = ['once::Warning']
'''})
        self.assertEqual(parsed['active_config'], 'pyproject.toml')
        self.assertIn('--import-mode=importlib', parsed['pytest_options'])
        self.assertIn('-l', parsed['pytest_options'])
        self.assertEqual(parsed['plugin_requirements'], [])
        self.assertEqual(parsed['config_sha256'], {'pyproject.toml': v1.sha256(b'''[tool.pytest.ini_options]
addopts = ['-ra', '--strict-markers', '--strict-config', '--import-mode=importlib', '-l']
testpaths = 'tests'
xfail_strict = true
filterwarnings = ['once::Warning']
''')})

    def test_benchmark_options_declare_explicit_plugin_requirement(self):
        parsed = self.admission.configuration({'pytest.ini': b'[pytest]\naddopts = -l --benchmark-sort=fullname --benchmark-warmup=true --benchmark-warmup-iterations=5 --benchmark-group-by=fullname\n'})
        self.assertEqual(parsed['plugin_requirements'], ['pytest_benchmark.plugin'])

    def test_unsupported_authority_options_and_unknown_config_fail_closed(self):
        for option in ('-c other.ini', '--rootdir=other', '-o python_files=other.py',
                       '-p other', 'tests/other.py', '--ignore=tests', '--deselect=x',
                       '--confcutdir=tests', '--import-mode=prepend', '--unknown-flag'):
            with self.subTest(option=option), self.assertRaisesRegex(ValueError, 'UNKNOWN_INTERFACE'):
                self.admission.configuration({'pytest.ini': ('[pytest]\naddopts = ' + option + '\n').encode()})
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_INTERFACE'):
            self.admission.configuration({'pytest.ini': b'[pytest]\nunknown_plugin_setting = true\n'})

    def test_pytest_config_precedence_is_bound(self):
        parsed = self.admission.configuration({'pytest.ini': b'[pytest]\naddopts = -q\n',
            'pyproject.toml': b'[tool.pytest.ini_options]\naddopts = "--unknown"\n'})
        self.assertEqual(parsed['active_config'], 'pytest.ini')
        self.assertEqual(parsed['pytest_options'], ['-q'])
        self.assertEqual(len(parsed['config_sha256']), 2)

    def test_pyproject_fallback_root_config_is_bound(self):
        parsed = self.admission.configuration({'pyproject.toml': b'[project]\nname = "fixture"\n'})
        self.assertEqual(parsed['active_config'], 'pyproject.toml')

    def test_inactive_malformed_config_does_not_override_effective_pytest_config(self):
        parsed = self.admission.configuration({'pytest.ini': b'[pytest]\naddopts=-q\n',
                                                'pyproject.toml': b'this is not valid toml'})
        self.assertEqual(parsed['active_config'], 'pytest.ini')
        self.assertEqual(parsed['pytest_options'], ['-q'])

    def test_candidate_validation_uses_v2_options_and_protects_configured_test_scope(self):
        files = {'module.py': b'VALUE = 1\n', 'checks/native.py': b'def test_it(): pass\n',
                 'nativecheck.py': b'def test_it(): pass\n',
                 'pytest.ini': b'[pytest]\naddopts=-l --import-mode=importlib\npython_files=nativecheck.py\ntestpaths=checks\n'}
        def candidate(path, replacement='VALUE = 2\n'):
            return {'replacements': [{'path': path, 'original_sha256': v1.sha256(files[path]),
                                      'replacement': replacement}]}
        self.assertIsNone(self.admission.validate_candidate(candidate('module.py'), files))
        for path in ('checks/native.py', 'nativecheck.py', 'pytest.ini'):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'production|tracked'):
                self.admission.validate_candidate(candidate(path), files)
        for value in ({'replacements': [], 'authority': {}},
                      {'replacements': [candidate('module.py')['replacements'][0]] * 2},
                      candidate('module.py', 'VALUE = 1\n'),
                      {'replacements': [{'path': 'module.py', 'original_sha256': '0' * 64,
                                         'replacement': 'VALUE=2\n'}]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.admission.validate_candidate(value, files)

    def test_new_configuration_or_plugin_source_paths_are_refused(self):
        for name, content in [('tests/conftest.py', 'import pytest\n'),
                              ('tests/plugin.py', 'pytest_plugins = ["external_plugin"]\n'),
                              ('tests/hooks.py', 'def pytest_collection_modifyitems(items): items.clear()\n')]:
            with self.subTest(path=name):
                self.git('reset', '--hard', self.base)
                (self.repo / name).write_text(content)
                with self.assertRaisesRegex(ValueError, 'configuration|plugin|collection'):
                    self.derive()

    def test_static_data_alias_proofs_are_invalidated_by_reassignment(self):
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_SUITE_CONTRACT'):
            self.derive('data = []\ndata = helper\ntest_inputs = data\ndef test_new(): assert True\n')
        authority = self.derive('data = []\nother = data\ndata = helper\ntest_inputs = other\ndef test_new(): assert True\n')
        self.assertEqual(authority['required_test_nodes'], ['tests/test_sample.py::test_new'])

    def test_initializer_calls_and_decorators_cannot_reuse_stale_data_proofs(self):
        sources = [
            'test_data = []\ndef mutate():\n global test_data\n test_data = lambda: None\n'
            'mutate()\ntest_alias = test_data\ndef test_new(): assert True\n',
            'test_data = []\ndef mutate(fn):\n global test_data\n test_data = lambda: None\n return fn\n'
            '@mutate\ndef helper(): pass\ntest_alias = test_data\ndef test_new(): assert True\n',
        ]
        for source in sources:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'UNKNOWN_SUITE_CONTRACT'):
                self.derive(source)

    def test_initializer_helper_cannot_hide_registration_operations(self):
        sources = [
            'def register():\n globals()["test_alias"] = lambda: None\nregister()\n',
            'def register():\n setattr(module, "test_alias", helper)\nregister()\n',
            'test_data=[]\ndef mutate():\n global test_data\n test_data=lambda: None\nmutate()\n',
        ]
        for source in sources:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'UNKNOWN_SUITE_CONTRACT'):
                self.derive(source + 'def test_new(): assert True\n')

    def test_runtime_test_body_namespace_operations_do_not_define_collection_authority(self):
        authority = self.derive('def test_new():\n setattr(object(), "attribute", 1)\n')
        self.assertEqual(authority['required_test_nodes'], ['tests/test_sample.py::test_new'])

    def test_registration_primitive_aliases_and_conditional_bindings_are_refused(self):
        statements = ['register = globals\nregister()["test_alias"] = helper',
            'from builtins import setattr as register\nregister(module, "test_alias", helper)',
            'builtins.setattr(module, "test_alias", helper)',
            'for test_alias in [helper]: pass', 'with context() as test_alias: pass',
            'try:\n pass\nexcept Exception as test_alias:\n pass',
            'match value:\n case {"item": test_alias}: pass',
            'items = [(test_alias := helper)]']
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaisesRegex(ValueError, 'UNKNOWN_SUITE_CONTRACT'):
                self.derive('def test_new(): assert True\n' + statement + '\n')

    def test_new_config_new_selection_scope_and_production_overlay_are_refused(self):
        for name, content in [('pytest.ini', '[pytest]\naddopts = -k old\n'),
                              ('new.ini', '[pytest]\n'), ('sample.py', 'VALUE = 99\n')]:
            with self.subTest(path=name):
                self.git('reset', '--hard', self.base)
                (self.repo / name).write_text(content)
                with self.assertRaisesRegex(ValueError, 'configuration|source overlay'):
                    self.derive()

    def test_source_config_protocol_and_test_scope_are_recomputed(self):
        authority = self.derive()
        contract = {'repo_path': str(self.repo), 'commit': self.commit_id,
                    'repository': 'local/admission', 'protocol_binding': 'e' * 64}
        self.assertEqual(self.admission.validate_suite_contract(contract, authority), v1.fingerprint(authority))
        changes = [{'required_test_nodes': []}, {'test_source_sha256': {}}, {'source_commit': self.base},
                   {'repository': 'wrong/repo'}, {'protocol_binding': 'f' * 64}, {'configuration': {}}]
        for update in changes:
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.admission.validate_suite_contract(contract, {**authority, **update})

    def test_comment_only_and_unchanged_deltas_do_not_grant_suite_authority(self):
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_NATIVE_SUITE_DELTA'):
            self.derive('# only a comment\ndef test_old(): assert True\n')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_NATIVE_SUITE_DELTA'):
            self.admission.derive_suite_contract(self.repo, self.base, self.base, 'e' * 64,
                repository='local/admission')


if __name__ == '__main__':
    unittest.main()
