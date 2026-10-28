"""Independent source-only V45 fixtures; no target imports or native execution."""
import ast
import copy
import hashlib
import importlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from research.unified_consequence_runtime import native_admission_v42 as original
from research.unified_consequence_runtime import test_native_admission_v2 as original_static_tests


FREEZE = Path(__file__).parent / 'archaeology/native-namespace-v45/control-freeze/fixtures'


class NativeAdmissionV45(unittest.TestCase):
    def setUp(self):
        name = 'research.unified_consequence_runtime.native_admission_v45'
        # The preimplementation RED exercises the actual predecessor refusal.
        self.admission = importlib.import_module(name) if importlib.util.find_spec(name) else original
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'; self.repo.mkdir()
        self.git('init', '-q')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Namespace fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def prepare(self, files=None, source=None):
        data = {'library/__init__.py': '', 'library/constants.py': 'ANSWER = 42\n',
                'ordinary.py': 'VALUE = 1\n', 'pytest.ini': '[pytest]\n',
                'tests/test_native.py': 'def test_contract():\n    assert True\n'}
        data.update(files or {})
        for name, raw in data.items():
            path = self.repo / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw if isinstance(raw, bytes) else raw.encode())
        self.base = self.commit()
        if source is None:
            source = 'from library.constants import *\ndef test_contract():\n    assert ANSWER == 42\n'
        (self.repo / 'tests/test_native.py').write_text(source)
        self.head = self.commit()

    def frozen(self, name):
        root = FREEZE / name
        shutil.copytree(root / 'baseline', self.repo, dirs_exist_ok=True, copy_function=shutil.copyfile)
        self.base = self.commit()
        shutil.copytree(root / 'augmented', self.repo, dirs_exist_ok=True, copy_function=shutil.copyfile)
        self.head = self.commit()

    def derive(self):
        return self.admission.derive_suite_contract(self.repo, self.base, self.head,
            'e' * 64, repository='local/namespace')

    def positive(self):
        try:
            return self.derive()
        except ValueError as error:
            self.fail('closed original namespace must derive: ' + str(error))

    def contract(self):
        return {'repo_path': str(self.repo), 'commit': self.head,
                'protocol_binding': 'e' * 64, 'repository': 'local/namespace'}

    def test_closed_original_wildcard_binds_raw_source_and_declaration(self):
        self.frozen('W01_closed_production_wildcard')
        with self.assertRaisesRegex(ValueError, 'wildcard'):
            original.derive_suite_contract(self.repo, self.base, self.head, 'e' * 64,
                                           repository='local/namespace')
        authority = self.positive()
        self.assertEqual(authority['schema'], 'UDM_NATIVE_SUITE_AUTHORITY_V45')
        self.assertEqual(authority['required_test_nodes'], ['tests/test_native.py::test_contract'])
        certificate = authority['namespace_certificate']
        self.assertEqual(certificate['schema'], 'UDM_NATIVE_TEST_NAMESPACE_CERTIFICATE_V45')
        witness = certificate['wildcard_imports'][0]
        self.assertEqual(witness['module'], 'library.constants')
        self.assertEqual(witness['path'], 'library/constants.py')
        self.assertEqual(witness['exports'], ['ANSWER', 'Node', 'VALUES', 'describe'])
        self.assertEqual(witness['source_sha256'], hashlib.sha256(
            (self.repo / 'library/constants.py').read_bytes()).hexdigest())
        self.assertEqual(witness['route'][0]['path'], 'library/__init__.py')
        declaration = certificate['required_declarations']['tests/test_native.py::test_contract']
        self.assertEqual(declaration['path'], 'tests/test_native.py')
        self.assertEqual(declaration['origin'], 'test_contract')
        expected_ast = ast.dump(ast.parse('def test_contract():\n    assert ANSWER == 42\n').body[0],
                                include_attributes=False)
        self.assertEqual(declaration['ast_sha256'], hashlib.sha256(expected_ast.encode()).hexdigest())
        self.assertEqual(declaration['source_sha256'], hashlib.sha256(
            (self.repo / 'tests/test_native.py').read_bytes()).hexdigest())

    def test_original_c3_winning_declaration_maps_every_required_route(self):
        base = ('from unittest import TestCase\nclass Shared:\n'
                ' def test_shared(self): assert False\nclass Left(Shared): pass\n'
                'class Right(Shared):\n def test_shared(self): assert False\n'
                'class Concrete(Left, Right, TestCase): pass\n')
        self.prepare({'tests/test_native.py': base}, base.replace(
            'class Right(Shared):\n def test_shared(self): assert False',
            'class Right(Shared):\n def test_shared(self): assert True'))
        authority = self.positive()
        self.assertEqual(authority['required_test_nodes'], ['tests/test_native.py::Concrete::test_shared'])
        self.assertEqual(authority['namespace_certificate']['required_declarations'][
            'tests/test_native.py::Concrete::test_shared']['origin'], 'Right::test_shared')

    def test_forged_wrapped_noop_retains_failing_original_declaration_authority(self):
        self.frozen('B03_forged_wrapped_noop')
        authority = self.positive()
        declaration = authority['namespace_certificate']['required_declarations'][
            'tests/test_native.py::test_contract']
        self.assertEqual(declaration['origin'], 'test_contract')
        node = ast.parse((self.repo / declaration['path']).read_bytes()).body[-1]
        self.assertIsInstance(node.body[0], ast.Assert)
        self.assertEqual(declaration['ast_sha256'], hashlib.sha256(
            ast.dump(node, include_attributes=False).encode()).hexdigest())
        # This is source authority only; the separate worker must reject the outer no-op.

    def test_unrelated_legacy_python_is_data_but_imported_legacy_source_refuses(self):
        self.frozen('W02_unimported_malformed_python_data')
        self.positive()
        self.temp.cleanup()
        self.setUp()
        self.frozen('W03_collection_imported_malformed_python')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            self.derive()

    def test_runtime_legacy_import_does_not_enter_static_import_grammar(self):
        self.frozen('W04_runtime_imported_malformed_python')
        authority = self.positive()
        self.assertEqual(authority['required_test_nodes'], ['tests/test_native.py::test_contract'])

    def test_frozen_wildcard_negatives_and_all_attribute_writes_stay_unknown(self):
        cases = [p.name for p in FREEZE.iterdir() if p.name.startswith(('W', 'O'))
                 and not p.name.startswith(('W01_', 'W02_', 'W04_'))]
        for name in sorted(cases):
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as folder:
                    previous = self.repo; self.repo = Path(folder) / 'repo'; self.repo.mkdir()
                    try:
                        self.git('init', '-q'); self.frozen(name)
                        with self.assertRaisesRegex(ValueError, 'UNKNOWN|unsupported'):
                            self.derive()
                    finally:
                        self.repo = previous

    def test_literal_all_can_only_name_actual_closed_non_test_bindings(self):
        self.prepare({'library/constants.py': 'ANSWER = 42\nHIDDEN = 1\n__all__ = ["ANSWER"]\n'})
        authority = self.positive()
        self.assertEqual(authority['namespace_certificate']['wildcard_imports'][0]['exports'], ['ANSWER'])

    def test_wildcard_collision_with_local_helper_or_import_is_refused(self):
        for source in ['ANSWER = 0\nfrom library.constants import *\ndef test_contract(): assert ANSWER == 42\n',
                       'from library.constants import *\nANSWER = 0\ndef test_contract(): assert ANSWER == 42\n']:
            with self.subTest(source=source):
                if not hasattr(self, 'base'):
                    self.prepare(source=source)
                else:
                    (self.repo / 'tests/test_native.py').write_text(source); self.head = self.commit()
                with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                    self.derive()

    def test_ambiguous_flat_src_module_is_refused(self):
        self.prepare({'src/library/__init__.py': '', 'src/library/constants.py': 'ANSWER = 42\n'})
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            self.derive()

    def test_wildcard_target_cannot_be_test_source(self):
        self.prepare({'tests/__init__.py': '', 'tests/helpers.py': 'ANSWER = 42\n'},
            'from tests.helpers import *\ndef test_contract(): assert ANSWER == 42\n')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            self.derive()

    def test_package_import_control_dunders_cannot_redirect_the_original_route(self):
        self.prepare({'library/__init__.py': '__path__ = ["/unlicensed"]\n'})
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            self.derive()

    def test_definition_expressions_and_string_captures_cannot_shadow_exports(self):
        statements = ['match 0:\n case ANSWER: pass\n',
                      'match {}:\n case {**ANSWER}: pass\n',
                      'try:\n raise RuntimeError()\nexcept RuntimeError as ANSWER:\n pass\n',
                      'def helper(x=(ANSWER := 0)): pass\n',
                      'def helper(x: (ANSWER := 0)): pass\n',
                      '@(ANSWER := lambda function: function)\ndef helper(): pass\n',
                      'class Helper((ANSWER := object)): pass\n',
                      'class Helper(metaclass=(ANSWER := type)): pass\n']
        for statement in statements:
            source = 'from library.constants import *\n' + statement + 'def test_contract(): assert True\n'
            with self.subTest(statement=statement):
                if not hasattr(self, 'base'):
                    self.prepare(source=source)
                else:
                    (self.repo / 'tests/test_native.py').write_text(source); self.head = self.commit()
                with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                    self.derive()

    def test_collection_class_global_cannot_shadow_a_wildcard_export(self):
        self.prepare(source='from library.constants import *\nclass Helper:\n'
                     ' global ANSWER\n ANSWER = 0\ndef test_contract(): assert ANSWER == 42\n')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            self.derive()

    def test_function_or_class_all_is_not_a_literal_export_protocol(self):
        for source in ['ANSWER = 42\ndef __all__(): pass\n',
                       'ANSWER = 42\nclass __all__: pass\n']:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as folder:
                previous_repo = self.repo; self.repo = Path(folder) / 'repo'; self.repo.mkdir()
                try:
                    self.git('init', '-q'); self.prepare({'library/constants.py': source})
                    with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                        self.derive()
                finally:
                    self.repo = previous_repo

    def test_namespace_reconstruction_rejects_forged_export_origin_and_assertion_set(self):
        self.prepare()
        authority = self.positive()
        for field in ('exports', 'path', 'required'):
            forged = copy.deepcopy(authority)
            if field == 'exports':
                forged['namespace_certificate']['wildcard_imports'][0]['exports'] = []
            elif field == 'path':
                forged['namespace_certificate']['wildcard_imports'][0]['path'] = 'ordinary.py'
            else:
                forged['required_test_nodes'] = []
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.admission.validate_suite_contract(self.contract(), forged)
        self.admission.validate_suite_contract(self.contract(), authority)

    def test_candidate_cannot_reuse_namespace_after_imported_source_change(self):
        self.prepare()
        authority = self.positive()
        _, files, _ = original._snapshot(self.repo, self.head)
        def candidate(path, replacement):
            return {'replacements': [{'path': path, 'original_sha256': hashlib.sha256(files[path]).hexdigest(),
                                      'replacement': replacement}]}
        helper = getattr(self.admission, 'revalidate_candidate_namespace', None)
        self.assertIsNotNone(helper, 'candidate namespace revalidation is required')
        for path, replacement in [('library/constants.py', 'ANSWER = 43\n'),
                                  ('library/__init__.py', 'raise RuntimeError("mutated")\n')]:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                helper(candidate(path, replacement), files, authority)
        helper(candidate('ordinary.py', 'VALUE = 2\n'), files, authority)

    def test_per_call_namespaces_cannot_reuse_other_source_exports(self):
        self.prepare()
        first = self.positive()
        (self.repo / 'library/constants.py').write_text('def test_unsafe(): pass\n')
        bad_base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(
            'from library.constants import *\ndef test_contract(): assert False\n')
        bad_head = self.commit()
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            self.admission.derive_suite_contract(self.repo, bad_base, bad_head, 'e' * 64,
                                                repository='local/namespace')
        self.admission.validate_suite_contract(self.contract(), first)


class NativeAdmissionV45Inherited(unittest.TestCase):
    """Run original fixture statements and assertions with versioned authority."""
    git = original_static_tests.NativeAdmissionV2.git
    commit = original_static_tests.NativeAdmissionV2.commit
    derive = original_static_tests.NativeAdmissionV2.derive

    def setUp(self):
        original_static_tests.NativeAdmissionV2.setUp(self)
        self.admission = importlib.import_module('research.unified_consequence_runtime.native_admission_v45')


# These three original V2 expectations were superseded by the preserved V42
# typed-source API. Run the entire original module separately against V2 too.
_V2_ONLY_INTERFACES = {
    'test_candidate_validation_uses_v2_options_and_protects_configured_test_scope',
    'test_cached_static_authority_cannot_claim_changed_source_bytes',
    'test_new_config_new_selection_scope_and_production_overlay_are_refused',
}
for _method in dir(original_static_tests.NativeAdmissionV2):
    if _method.startswith('test_') and _method not in _V2_ONLY_INTERFACES:
        setattr(NativeAdmissionV45Inherited, _method, getattr(original_static_tests.NativeAdmissionV2, _method))
del _method


if __name__ == '__main__':
    unittest.main()
