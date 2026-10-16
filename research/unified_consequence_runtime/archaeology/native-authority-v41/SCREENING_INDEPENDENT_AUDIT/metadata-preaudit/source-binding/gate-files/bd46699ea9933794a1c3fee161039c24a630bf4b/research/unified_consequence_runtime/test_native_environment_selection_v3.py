"""Metadata-only finite environment choice; no imports, installs or native runs."""
import copy
import hashlib
import importlib
import importlib.util
import subprocess
import sys
import unittest


MODULE = 'research.unified_consequence_runtime.native_environment_selection_v3'


def profile(name='modern', python='3.12.14', pytest='8.4.1', packages=(), **extra):
    return {'id': name, 'python_version': python, 'python_implementation': 'CPython',
            'pytest_version': pytest, 'packages': ['pytest==' + pytest, *packages],
            'plugins': [], **extra}


def catalog(*profiles):
    return {'schema': 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3', 'profiles': list(profiles)}


MODERN = b'''[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
[project]
requires-python = ">=3.10"
classifiers = ["Programming Language :: Python :: 3.10", "Programming Language :: Python :: 3.12"]
dependencies = ["attrs>=25.4.0", "exceptiongroup>=1.1.1; python_version < '3.11'"]
[dependency-groups]
test = ["pytest>=8.4.1", "hypothesis>=6.135.26"]
'''

LEGACY = b'''from distutils.core import setup
classifiers = ['Programming Language :: Python :: 3.5',
               'Programming Language :: Python :: 3.6',
               'Programming Language :: Python :: Implementation :: CPython']
setup_kwargs = dict(name='wrapt', version='1.10.10', classifiers=classifiers)
def run_setup():
    setup(**setup_kwargs)
'''


class NativeEnvironmentSelectionV3(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE), 'versioned selector required')
        self.selector = importlib.import_module(MODULE)

    def select(self, files, *profiles):
        return self.selector.select_profile(files, catalog(*profiles))

    def test_legacy_static_dict_classifiers_tox_and_removed_apis_choose_frozen_old_profile(self):
        files = {'setup.py': LEGACY,
                 'tox.ini': b'[tox]\nenvlist = py{35,36}-{without,with}-extensions\n[testenv]\ndeps = pytest\n',
                 'tests/compat.py': b'import pytest\nx = pytest.collect.Module\n',
                 'src/pkg.py': b'import inspect\nx = inspect.getargspec\n'}
        result = self.select(files, profile('old', '3.6.12', '5.4.3'), profile())
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')
        self.assertEqual(result['selected_profile']['id'], 'old')
        self.assertEqual(len(result['candidates']), 2)
        self.assertIn('<3.11', result['constraints']['python_specifiers'])
        self.assertIn('pytest<6', [r['requirement'] for r in result['constraints']['requirements']])

    def test_modern_source_dependencies_and_markers_choose_highest_satisfiable_declared_python(self):
        pins = ['hatchling==1.27.0', 'hatch-vcs==0.5.0', 'attrs==25.4.0', 'hypothesis==6.151.9']
        result = self.select({'pyproject.toml': MODERN},
                             profile('older', '3.10.19', packages=pins + ['exceptiongroup==1.3.0']),
                             profile(packages=pins))
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')
        self.assertEqual(result['selected_profile']['id'], 'modern')

    def test_python310_marker_requires_exceptiongroup_in_complete_exact_closure(self):
        pins = ['hatchling==1.27.0', 'hatch-vcs==0.5.0', 'attrs==25.4.0', 'hypothesis==6.151.9']
        result = self.select({'pyproject.toml': MODERN}, profile('older', '3.10.19', packages=pins))
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')
        self.assertIn('exceptiongroup', str(result['candidates'][0]['reasons']))

    def test_ranges_and_test_group_includes_use_pep508_not_string_comparison(self):
        files = {'pyproject.toml': b'''[project]
requires-python = ">=3.9,!=3.10.*"
[dependency-groups]
base = ["pytest~=8.4.0"]
tests = [{include-group = "base"}, "cloudpickle; platform_python_implementation == 'CPython'"]
''', 'tox.ini': b'[tox]\nenv_list = py3{9-12}-tests\n'}
        result = self.select(files, profile('bad', '3.10.19', packages=['cloudpickle==3.1.2']),
                             profile(packages=['cloudpickle==3.1.2']))
        self.assertEqual(result['selected_profile']['id'], 'modern')
        self.assertEqual(result['candidates'][0]['status'], 'REJECTED')

    def test_setup_python_requires_install_and_test_extra_are_not_executed(self):
        files = {'setup.py': b'''raise RuntimeError("must never execute setup.py")
from setuptools import setup
setup(python_requires='>=3.11', install_requires=['attrs>=25'],
      extras_require={'test':['pytest>=8'], 'docs':['uninstalled-docs']})
'''}
        result = self.select(files, profile(packages=['attrs==25.4.0']))
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_dependency_below_required_version_is_refused(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\ndependencies=["attrs>=25.4.0"]\n'}
        result = self.select(files, profile(packages=['attrs==24.1.0']))
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')

    def test_profiles_with_nonexact_duplicate_or_invalid_pins_are_unknown_catalog(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        for pins in (['attrs>=25'], ['attrs==25.4.0', 'Attrs==25.4.0'], ['x==1..0'], ['pytest==8.4.0']):
            with self.subTest(pins=pins):
                result = self.select(files, profile(packages=pins))
                self.assertEqual(result['status'], 'UNKNOWN')
                self.assertEqual(result['reason'], 'UNKNOWN_CATALOG_AUTHORITY')

    def test_unprovided_marker_environment_is_unknown_not_host_dependent(self):
        files = {'pyproject.toml': b'''[project]
requires-python=">=3.11"
dependencies=["only-windows; sys_platform == 'win32'"]
'''}
        result = self.select(files, profile())
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIn('UNKNOWN_MARKER_ENVIRONMENT', str(result))
        result = self.select(files, profile(marker_environment={'sys_platform': 'linux'}))
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_matrix_and_requires_python_conflict_is_precise_unknown(self):
        files = {'setup.py': LEGACY, 'pyproject.toml': b'[project]\nrequires-python=">=3.12"\n'}
        result = self.select(files, profile('old', '3.6.12', '5.4.3'), profile())
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'UNKNOWN_CONFLICTING_METADATA')

    def test_disjoint_source_matrices_are_conflicting(self):
        files = {'setup.py': LEGACY, 'tox.ini': b'[tox]\nenvlist=py312\n'}
        result = self.select(files, profile())
        self.assertEqual(result['reason'], 'UNKNOWN_CONFLICTING_METADATA')

    def test_absent_python_declaration_does_not_guess_host(self):
        result = self.select({'README.md': b'nothing'}, profile())
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'UNKNOWN_UNDECLARED_PYTHON_COMPATIBILITY')

    def test_unsupported_dynamic_setup_metadata_is_unknown_without_evaluation(self):
        files = {'setup.py': b"from setuptools import setup\nsetup(python_requires=load_requirement())\n"}
        result = self.select(files, profile())
        self.assertEqual(result['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_unsupported_range_or_direct_url_requirement_is_unknown(self):
        for requirement in ('attrs=>25', 'attrs @ https://example.invalid/pkg.whl'):
            files = {'pyproject.toml': ('[project]\nrequires-python=">=3.11"\ndependencies=[' + repr(requirement) + ']\n').encode()}
            with self.subTest(requirement=requirement):
                result = self.select(files, profile(packages=['attrs==25.4.0']))
                self.assertEqual(result['reason'], 'UNKNOWN_REQUIREMENT_GRAMMAR')

    def test_unsupported_dependency_group_cycle_is_unknown(self):
        files = {'pyproject.toml': b'''[project]
requires-python=">=3.11"
[dependency-groups]
tests=[{include-group="other"}]
other=[{include-group="tests"}]
'''}
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_DEPENDENCY_GROUP')

    def test_test_requirements_files_support_pins_and_safe_recursive_includes(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n',
                 'requirements-test.txt': b'-r requirements/base.txt\npytest>=8 # runner\n',
                 'requirements/base.txt': b'attrs>=25\n'}
        result = self.select(files, profile(packages=['attrs==25.4.0']))
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')
        files['requirements-test.txt'] = b'-r ../escape.txt\n'
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_REQUIREMENT_GRAMMAR')

    def test_legacy_removed_api_constraint_uses_ast_and_import_aliases(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.6"\n',
                 'pkg.py': b'import inspect as ins\nfrom pytest import collect as old\nx=ins.formatargspec\ny=old.Module\n'}
        result = self.select(files, profile('old', '3.6.12', '5.4.3'), profile())
        self.assertEqual(result['selected_profile']['id'], 'old')
        files['pkg.py'] = b'"inspect.getargspec pytest.collect"\n# inspect.formatargspec\n'
        self.assertEqual(self.select(files, profile())['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_same_python_prefers_highest_compatible_pytest(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        result = self.select(files, profile('older-pytest', pytest='8.3.5'), profile())
        self.assertEqual(result['selected_profile']['id'], 'modern')

    def test_equal_rank_profiles_do_not_choose_arbitrary_id(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        result = self.select(files, profile('one'), profile('two'))
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'UNKNOWN_AMBIGUOUS_PROFILE')

    def test_plugin_versions_are_independent_exact_catalog_pins(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        bad = profile(plugins=[{'module': 'hypothesis.extra.pytestplugin', 'distribution': 'hypothesis', 'version': '6.0'}])
        self.assertEqual(self.select(files, bad)['reason'], 'UNKNOWN_CATALOG_AUTHORITY')
        bad['packages'].append('hypothesis==6.0')
        self.assertEqual(self.select(files, bad)['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_external_transitive_metadata_is_checked_against_exact_closure(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        p = profile(packages=['pluggy==1.0'], package_requirements={'pytest': ['pluggy>=1.5']})
        result = self.select(files, p)
        self.assertEqual(result['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')

    def test_duplicate_normalized_dependency_metadata_keys_are_refused_in_every_order(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        metadata = {'attrs': ['missing>=1'], 'Attrs': []}
        results = []
        for mapping in (metadata, dict(reversed(list(metadata.items())))):
            p = profile(packages=['attrs==25.4.0'], package_requirements=mapping)
            result = self.select(files, p); results.append(result)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertEqual(result['reason'], 'UNKNOWN_CATALOG_AUTHORITY')
            self.assertIn('duplicate normalized', result['detail'])
        self.assertEqual(results[0], results[1])

    def test_requested_extra_activates_its_external_transitive_requirements(self):
        files = {'pyproject.toml': b'''[project]
requires-python=">=3.11"
[dependency-groups]
tests=["pytest-xdist[psutil]"]
'''}
        p = profile(packages=['pytest-xdist==3.8.0'], package_requirements={
            'pytest-xdist': ['psutil>=5.8; extra == "psutil"']})
        self.assertEqual(self.select(files, p)['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')
        p['packages'].append('psutil==7.2.2')
        self.assertEqual(self.select(files, p)['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')
        del p['package_requirements']
        self.assertEqual(self.select(files, p)['candidates'][0]['reason'], 'UNKNOWN_EXTRA_DEPENDENCY_METADATA')

    def test_setup_metadata_mutation_or_conditional_binding_remains_unknown(self):
        variants = [
            b"classifiers=['Programming Language :: Python :: 3.12']\nclassifiers.append('Programming Language :: Python :: 3.6')\nsetup(classifiers=classifiers)\n",
            b"if platform_condition():\n    python_range='>=3.11'\nsetup(python_requires=python_range)\n",
            b"kwargs=dict(python_requires='>=3.11')\nkwargs.update(python_requires='<3.7')\nsetup(**kwargs)\n",
        ]
        for raw in variants:
            with self.subTest(raw=raw):
                self.assertEqual(self.select({'setup.py': raw}, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_malformed_nested_or_unversioned_tox_matrix_never_silently_falls_back(self):
        for envlist in ('py{3{10,12}}', 'py{310,312', 'py3'):
            files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n',
                     'tox.ini': ('[tox]\nenvlist=' + envlist + '\n').encode()}
            with self.subTest(envlist=envlist):
                self.assertEqual(self.select(files, profile())['status'], 'UNKNOWN')

    def test_conflicting_python_ranges_are_source_conflict(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.12,<3.11"\n'}
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_CONFLICTING_METADATA')

    def test_candidate_status_does_not_depend_on_unrelated_incompatible_profile_dependencies(self):
        files = {'setup.py': LEGACY}
        result = self.select(files, profile('old', '3.6.12', '5.4.3'),
                             profile(package_requirements={'pytest': ['unavailable>=1']}))
        self.assertEqual(result['selected_profile']['id'], 'old')

    def test_direct_import_of_removed_api_constrains_even_if_unused(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.6"\n',
                 'pkg.py': b'from inspect import getargspec\nfrom pytest import collect\n'}
        result = self.select(files, profile('old', '3.6.12', '5.4.3'), profile())
        self.assertEqual(result['selected_profile']['id'], 'old')

    def test_large_patch_boundary_is_not_guessed_unsatisfiable(self):
        files = {'pyproject.toml': b'''[project]
requires-python=">=3.12.100,<3.13"
classifiers=["Programming Language :: Python :: 3.12"]
'''}
        result = self.select(files, profile('future-patch', '3.12.101'))
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_invalid_catalog_preserves_all_candidate_refusals(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        result = self.select(files, profile('bad', packages=['attrs>=25']), profile())
        self.assertEqual(result['reason'], 'UNKNOWN_CATALOG_AUTHORITY')
        self.assertEqual([row['id'] for row in result['candidates']], ['bad', 'modern'])
        self.assertTrue(all(row['status'] == 'UNKNOWN' for row in result['candidates']))

    def test_empty_tox_braces_refuse_without_nontermination(self):
        script = ('from ' + MODULE + ' import derive_constraints\n'
                  'r=derive_constraints({"tox.ini":b"[tox]\\nenvlist=py{}\\n"})\n'
                  'assert r["status"]=="UNKNOWN",r\n')
        try:
            result = subprocess.run([sys.executable, '-c', script], capture_output=True,
                                    text=True, timeout=2)
        except subprocess.TimeoutExpired:
            self.fail('empty tox braces must terminate with UNKNOWN')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_forward_alias_mutation_cannot_hide_setup_metadata_change(self):
        files = {'setup.py': b'''kw={'python_requires':'>=3.6','classifiers':['Programming Language :: Python :: 3.6']}
alias=kw
alias.update({'python_requires':'>=3.12'})
setup(**kw)
'''}
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_aliased_setuptools_call_cannot_hide_dynamic_metadata(self):
        files = {'tox.ini': b'[tox]\nenvlist=py312\n', 'setup.py': b'''import setuptools as st
st.setup(python_requires=dynamic_requires())
'''}
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_unknown_calls_nested_mutation_delete_or_setup_rebinding_refuse_literal_authority(self):
        variants = [
            b"kw=dict(python_requires='>=3.11')\nmutate(kw)\nsetup(**kw)\n",
            b"kw=dict(python_requires='>=3.11',classifiers=['Programming Language :: Python :: 3.12'])\nkw['classifiers'][0]='Programming Language :: Python :: 3.6'\nsetup(**kw)\n",
            b"kw=dict(python_requires='>=3.11')\ndel kw['python_requires']\nsetup(**kw)\n",
            b"setup=other_function\nsetup(python_requires='>=3.11')\n",
        ]
        for raw in variants:
            with self.subTest(raw=raw):
                self.assertEqual(self.select({'setup.py': raw}, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_setup_cfg_environment_fields_cannot_be_silently_omitted(self):
        files = {'setup.cfg': b'''[options]
python_requires = >=3.11
install_requires =
    attrs>=25.4
[options.extras_require]
tests = pytest>=8
'''}
        self.assertEqual(self.select(files, profile())['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')
        self.assertEqual(self.select(files, profile(packages=['attrs==25.4.0']))['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_tox_version_specific_dependency_override_constrains_only_matching_python(self):
        files = {'tox.ini': b'''[tox]
envlist=py36,py312
[testenv:py36]
deps=pytest<6
'''}
        bad = self.select(files, profile('old-bad', '3.6.12', '8.4.1'))
        self.assertEqual(bad['candidates'][0]['reason'], 'UNKNOWN_DEPENDENCY_UNSATISFIED')
        self.assertEqual(self.select(files, profile())['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_referenced_literal_sequence_item_write_is_unknown(self):
        files = {'setup.py': b'''classifiers=['Programming Language :: Python :: 3.12']
classifiers[0]='Programming Language :: Python :: 3.6'
setup(classifiers=classifiers)
'''}
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_subscript_derived_metadata_alias_mutation_is_unknown(self):
        for alias in ("kw['classifiers']", "kw['classifiers'][:]"):
            raw = ("kw=dict(classifiers=['Programming Language :: Python :: 3.12'])\n"
                   "alias=" + alias + "\nalias[0]='Programming Language :: Python :: 3.6'\n"
                   "setup(**kw)\n").encode()
            with self.subTest(alias=alias):
                self.assertEqual(self.select({'setup.py': raw}, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_setuptools_setup_attribute_rebinding_is_unknown(self):
        for target in ('st.setup', 'st.setup.__code__'):
            raw = ("import setuptools as st\n" + target + "=other_function\n"
                   "st.setup(classifiers=['Programming Language :: Python :: 3.12'])\n").encode()
            with self.subTest(target=target):
                self.assertEqual(self.select({'setup.py': raw}, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_demonstrably_irrelevant_top_mapping_writes_remain_supported(self):
        files = {'setup.py': b'''kw=dict(classifiers=['Programming Language :: Python :: 3.12'])
kw['ext_modules']=['separately built native extension']
kw['cmdclass']={'build_ext':'original build mechanism'}
setup(**kw)
'''}
        self.assertEqual(self.select(files, profile())['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_unsupported_metadata_binding_forms_and_receiver_calls_are_unknown(self):
        bindings = [
            "(alias,)=(kw['classifiers'],)\nalias[0]='Programming Language :: Python :: 3.6'",
            "(alias:=kw['classifiers'])\nalias[0]='Programming Language :: Python :: 3.6'",
            "for alias in [kw['classifiers']]:\n    alias[0]='Programming Language :: Python :: 3.6'",
            "kw['classifiers'].__setitem__(0,'Programming Language :: Python :: 3.6')",
            "obj.alias=kw['classifiers']\nobj.alias[0]='Programming Language :: Python :: 3.6'",
            "def f(alias=kw['classifiers']):\n    alias[0]='Programming Language :: Python :: 3.6'\nf()",
            "def expose():\n    return kw['classifiers']\nalias=expose()\nalias[0]='Programming Language :: Python :: 3.6'",
            "[alias.__setitem__(0,'Programming Language :: Python :: 3.6') for alias in [kw['classifiers']]]",
            "stash={}\nstash['x']=kw['classifiers']\nstash['x'][0]='Programming Language :: Python :: 3.6'",
            "stash=[]\nstash += [kw['classifiers']]\nstash[0][0]='Programming Language :: Python :: 3.6'",
        ]
        for binding in bindings:
            raw = ("kw=dict(classifiers=['Programming Language :: Python :: 3.12'])\n" + binding + "\nsetup(**kw)\n").encode()
            with self.subTest(binding=binding):
                result = self.select({'setup.py': raw}, profile())
                self.assertEqual(result['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_import_function_definition_and_parameter_rebinding_of_setup_authority_are_unknown(self):
        variants = [
            "import setuptools as st\nimport other as st\nst.setup(python_requires='>=3.11')",
            "def setup(**kwargs):\n    return None\nsetup(python_requires='>=3.11')",
            "from setuptools import setup\nfrom other import setup\nsetup(python_requires='>=3.11')",
            "import setuptools as st\ndef f(st):\n    st.setup(python_requires='>=3.11')",
            "import setuptools as st\nfor st in [other]:\n    st.setup(python_requires='>=3.11')",
            "import setuptools as st\n(st:=other)\nst.setup(python_requires='>=3.11')",
        ]
        for text in variants:
            with self.subTest(text=text):
                self.assertEqual(self.select({'setup.py': text.encode()}, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_dynamic_execution_namespace_and_builtin_aliases_refuse_literal_metadata_authority(self):
        statements = [
            'exec("classifiers[0]=\'Programming Language :: Python :: 3.6\'")',
            'eval("classifiers.__setitem__(0,\'Programming Language :: Python :: 3.6\')")',
            'compile("classifiers[0]=\'Programming Language :: Python :: 3.6\'", "<dynamic>", "exec")',
            'run=exec\nrun("classifiers.clear()")',
            'from builtins import exec as run\nrun("classifiers.clear()")',
            'import builtins as b\nb.exec("classifiers.clear()")',
            'import builtins as b\nnamespace=b.__dict__\nnamespace["exec"]("classifiers.clear()")',
            'namespace=globals()\nnamespace["classifiers"][0]="Programming Language :: Python :: 3.6"',
            'namespace=locals()\nnamespace["classifiers"].clear()',
            'namespace=vars()\nnamespace["classifiers"].clear()',
            'from builtins import globals as current\ncurrent()["classifiers"].clear()',
            'import builtins as b\nrun=getattr(b,"exec")\nrun("classifiers.clear()")',
            '__builtins__["exec"]("classifiers.clear()")',
            '__import__("builtins").exec("classifiers.clear()")',
            'def helper(): pass\nhelper.__globals__["classifiers"].clear()',
            'import sys\nsys._getframe().f_globals["classifiers"].clear()',
            'import inspect\ninspect.currentframe().f_locals["classifiers"].clear()',
        ]
        for statement in statements:
            raw = ("from setuptools import setup\nclassifiers=['Programming Language :: Python :: 3.12']\n"
                   + statement + "\nsetup(classifiers=classifiers)\n").encode()
            with self.subTest(statement=statement):
                self.assertEqual(self.select({'setup.py': raw}, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_dynamic_execution_words_in_comments_and_strings_do_not_refuse_literal_metadata(self):
        files = {'setup.py': b'''from setuptools import setup
# exec eval compile globals locals vars getattr __builtins__
description="exec eval compile globals locals vars getattr __builtins__"
setup(python_requires='>=3.11', description=description)
'''}
        self.assertEqual(self.select(files, profile())['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')

    def test_dynamic_setup_call_is_unknown_even_without_literal_setup_call(self):
        files = {'tox.ini': b'[tox]\nenvlist=py312\n',
                 'setup.py': b'exec("setup(python_requires=\'<3.7\')")\n'}
        self.assertEqual(self.select(files, profile())['reason'], 'UNKNOWN_DYNAMIC_METADATA')

    def test_every_source_and_metadata_hash_is_bound_and_tamper_is_rejected(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n', 'pkg.py': b'x=1\n'}
        cat = catalog(profile())
        receipt = self.selector.select_profile(files, cat)
        self.assertEqual(receipt['constraints']['metadata_sha256']['pyproject.toml'], hashlib.sha256(files['pyproject.toml']).hexdigest())
        self.assertEqual(self.selector.validate_selection(files, cat, receipt), receipt)
        for mutation in ('source', 'catalog', 'receipt'):
            f, c, r = copy.deepcopy(files), copy.deepcopy(cat), copy.deepcopy(receipt)
            if mutation == 'source': f['pkg.py'] = b'x=2\n'
            elif mutation == 'catalog': c['profiles'][0]['python_version'] = '3.12.15'
            else: r['candidates'][0]['status'] = 'PASS'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.selector.validate_selection(f, c, r)

    def test_mapping_order_does_not_change_receipt_and_inputs_are_immutable(self):
        files = {'pkg.py': b'x=1\n', 'pyproject.toml': b'[project]\nrequires-python=">=3.11"\n'}
        cat = catalog(profile()); original = copy.deepcopy(cat)
        a = self.selector.select_profile(files, cat)
        b = self.selector.select_profile(dict(reversed(list(files.items()))), cat)
        self.assertEqual(a, b)
        self.assertEqual(cat, original)


if __name__ == '__main__':
    unittest.main()
