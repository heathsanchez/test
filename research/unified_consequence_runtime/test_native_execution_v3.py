"""Portable v3 authority on disposable repositories and real native interpreters."""
import ast
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from . import decisive_native_verify as original
from . import native_admission_v2 as admission
from . import native_execution_v2 as frozen
from . import test_native_admission_v2_adversarial as qualified_tests

try:
    from . import native_execution_v3 as worker
except ImportError:
    worker = None


class PortableNativeWorkerContracts(unittest.TestCase):
    def test_versioned_portable_worker_is_available(self):
        self.assertIsNotNone(worker, 'portable v3 worker is required')

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_controller_bytecode_and_original_globals_are_unchanged(self):
        self.assertEqual(worker.ADMISSION_REVISION, '3.1')
        self.assertEqual(worker.SCHEMA, 'UDM_GENERIC_NATIVE_PYTEST_V3')
        self.assertEqual(worker.CERTIFICATE_SCHEMA, 'UDM_NATIVE_ADMISSION_CERTIFICATE_V3')
        self.assertEqual(worker.POLICY_SCHEMA, 'UDM_NATIVE_EXECUTION_POLICY_V3')
        for name in ('_roots', '_collection', '_binding', 'collect',
                     'validate_certificate', '_status', 'verify', 'validate_receipt'):
            with self.subTest(function=name):
                self.assertIs(getattr(worker, name).__code__, getattr(frozen, name).__code__)
                self.assertIsNot(getattr(worker, name).__globals__, vars(frozen))
        self.assertEqual(frozen.SCHEMA, 'UDM_GENERIC_NATIVE_PYTEST_V2')
        self.assertIs(frozen.original, original)
        self.assertIs(worker._controller_context.__code__, frozen._context.__code__)
        self.assertIs(worker._controller_run.__code__, frozen._run.__code__)
        self.assertIs(worker._portable_environment_identity.__code__, original.environment_identity.__code__)
        self.assertIsNot(worker.original, original)
        self.assertIs(worker.original.environment_identity, worker.environment_identity)
        self.assertIn('importlib.metadata as md', original._ENVIRONMENT)
        self.assertNotIn('import importlib_metadata as md', original._ENVIRONMENT)
        self.assertEqual(worker._runner_hash(), original.sha256(Path(worker.__file__).read_bytes()))

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_new_and_frozen_sources_are_guarded_before_context_use(self):
        # Separate processes keep imported module state and on-disk old bytes intact.
        script = '''import pathlib,tempfile
from research.unified_consequence_runtime import native_execution_v3 as w
with tempfile.TemporaryDirectory() as folder:
    replacement=pathlib.Path(folder)/'changed.py'
    replacement.write_bytes(b'changed source')
    if __import__('sys').argv[1]=='new':
        w.__file__=str(replacement)
    elif __import__('sys').argv[1]=='old':
        w.frozen.__file__=str(replacement)
    elif __import__('sys').argv[1]=='loaded-old':
        w.frozen._LOADED_SOURCE_SHA256='f'*64
    elif __import__('sys').argv[1]=='loaded-admission':
        w.admission._LOADED_SOURCE_SHA256='f'*64
    elif __import__('sys').argv[1]=='verifier':
        w.frozen.original.__file__=str(replacement)
    else:
        w.admission.__file__=str(replacement)
    assert w.attempt_snapshot()['subprocess_attempts'] >= 0
    try:w._context({}, {}, {})
    except ValueError as error:
        assert 'SOURCE' in str(error),str(error)
    else:raise AssertionError('changed loaded source accepted')
'''
        for target in ('new', 'old', 'verifier', 'admission', 'loaded-old', 'loaded-admission'):
            result = subprocess.run([sys.executable, '-B', '-c', script, target],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_child_programs_compile_in_selected_interpreter(self):
        interpreter = os.environ.get('UDM_NATIVE_V3_INTERPRETER', sys.executable)
        for name in ('_ENVIRONMENT', '_PLUGINS', '_BOOTSTRAP'):
            result = subprocess.run([interpreter, '-I', '-B', '-c',
                                     'import sys;compile(sys.stdin.read(),"portable-child","exec")'],
                                    input=getattr(worker, name), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_runtime_identity_needs_no_pytest_and_binds_stdlib_bytes(self):
        self.assertTrue(callable(getattr(worker, 'runtime_identity', None)),
                        'bare runtime identity is required before pytest provisioning')
        interpreter = os.environ.get('UDM_NATIVE_V3_INTERPRETER', sys.executable)
        identity = worker.runtime_identity(interpreter)
        self.assertEqual(set(identity), {'implementation', 'version_info', 'executable_sha256',
                                         'base_prefix', 'stdlib_manifest_sha256'})
        self.assertEqual(len(identity['stdlib_manifest_sha256']), 64)
        self.assertEqual(len(identity['executable_sha256']), 64)
        environment = worker.environment_identity(interpreter)
        self.assertEqual(environment['runtime_identity'], identity)
        self.assertEqual(len(environment['runtime_import_roots']), 3)
        roots = sorted({str(Path(root).resolve()) for root in environment['runtime_import_roots']})
        self.assertEqual(original.fingerprint(worker.host_stdlib(roots)), identity['stdlib_manifest_sha256'])
        # -S removes site-packages, proving the pre-provisioning child needs no pytest.
        result = subprocess.run([interpreter, '-I', '-B', '-S', '-c', worker._RUNTIME],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), identity)

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_environment_identity_refuses_an_executable_replaying_old_identity(self):
        interpreter = os.environ.get('UDM_NATIVE_V3_INTERPRETER', sys.executable)
        retained = worker.environment_identity(interpreter)
        with tempfile.TemporaryDirectory() as folder:
            wrapper = Path(folder) / 'python'
            wrapper.write_text('#!' + sys.executable + '\nimport sys\nsys.stdout.write(' +
                               repr(json.dumps(retained)) + ')\n')
            wrapper.chmod(0o755)
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_ENVIRONMENT_HOST_EXECUTABLE'):
                worker.environment_identity(wrapper)

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_environment_identity_refuses_a_forged_standard_library_digest(self):
        interpreter = os.environ.get('UDM_NATIVE_V3_INTERPRETER', sys.executable)
        retained = worker.environment_identity(interpreter)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'stdlib_probe.py'
            source.write_text('VALUE = 1\n')
            retained['runtime_import_roots'] = [str(root)] * 3
            retained['runtime_identity']['stdlib_manifest_sha256'] = original.fingerprint(
                [[str(source), original.sha256(source.read_bytes())]])
            source.write_text('VALUE = 2\n')
            with patch.object(worker, '_portable_environment_identity', return_value=retained):
                with self.assertRaisesRegex(ValueError, 'UNKNOWN_ENVIRONMENT_HOST_STDLIB'):
                    worker.environment_identity(interpreter)

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_environment_identity_refuses_an_executable_changed_during_child_check(self):
        interpreter = os.environ.get('UDM_NATIVE_V3_INTERPRETER', sys.executable)
        retained = worker.environment_identity(interpreter)
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / 'python'
            executable.write_bytes(b'before child check')
            def changed_child(path):
                executable.write_bytes(b'after child check')
                retained['executable_sha256'] = original.sha256(executable.read_bytes())
                retained['runtime_identity']['executable_sha256'] = retained['executable_sha256']
                return retained
            with patch.object(worker, '_portable_environment_identity', side_effect=changed_child):
                with self.assertRaisesRegex(ValueError, 'UNKNOWN_ENVIRONMENT_HOST_EXECUTABLE'):
                    worker.environment_identity(executable)

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_runtime_identity_detects_loadable_bytecode_changes(self):
        import py_compile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'portable_stdlib_probe.py'
            source.write_text('VALUE = 1\n')
            stamp = source.stat()
            cache = Path(py_compile.compile(str(source), doraise=True))
            namespace = dict(hashlib=hashlib, json=json, pathlib=__import__('pathlib'), sys=sys,
                             os=os, sysconfig=types.SimpleNamespace(get_path=lambda name: str(root),
                                                                    get_config_var=lambda name: None))
            exec(worker._RUNTIME_HELPER.replace('import os,sysconfig\n', ''), namespace)
            before = namespace['runtime_identity']()
            source.write_text('VALUE = 2\n')
            os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            py_compile.compile(str(source), doraise=True)
            source.write_text('VALUE = 1\n')
            os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            self.assertNotEqual(namespace['runtime_identity']()['stdlib_manifest_sha256'],
                                before['stdlib_manifest_sha256'])
            # Timestamp-normalized source permits the changed cache to execute under -B.
            result = subprocess.run([sys.executable, '-I', '-B', '-c',
                'import sys;sys.path.insert(0,sys.argv[1]);import portable_stdlib_probe;print(portable_stdlib_probe.VALUE)', folder],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), '2')
            self.assertTrue(cache.is_file())

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_runtime_identity_refuses_included_symlink_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'stdlib'
            root.mkdir()
            (root / 'sentinel.py').write_text('VALUE = 0\n')
            external = Path(folder) / 'external'
            external.mkdir()
            (external / '__init__.py').write_text('VALUE = 1\n')
            namespace = dict(hashlib=hashlib, json=json, pathlib=__import__('pathlib'), sys=sys,
                             os=os, sysconfig=types.SimpleNamespace(get_path=lambda name: str(root),
                                                                    get_config_var=lambda name: None))
            exec(worker._RUNTIME_HELPER.replace('import os,sysconfig\n', ''), namespace)
            (root / 'site-packages').symlink_to(external, target_is_directory=True)
            (root / 'dist-packages').symlink_to(external, target_is_directory=True)
            self.assertEqual(len(namespace['runtime_identity']()['stdlib_manifest_sha256']), 64)
            included = root / 'linked_package'
            included.symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, 'UNKNOWN_RUNTIME_SYMLINK_DIRECTORY'):
                namespace['runtime_identity']()
            included.unlink()
            alias = Path(folder) / 'stdlib_alias'
            alias.symlink_to(root, target_is_directory=True)
            namespace['sysconfig'].get_path = lambda name: str(alias)
            with self.assertRaisesRegex(RuntimeError, 'UNKNOWN_RUNTIME_SYMLINK_DIRECTORY'):
                namespace['runtime_identity']()

    @unittest.skipIf(worker is None, 'portable worker missing')
    def test_code_identity_preserves_optional_fields_and_legacy_line_table(self):
        tree = ast.parse(worker._BOOTSTRAP)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'code_hash')
        with tempfile.TemporaryDirectory() as folder:
            namespace = dict(hashlib=hashlib, json=json, struct=struct, types=types,
                             pathlib=__import__('pathlib'), world=Path(folder))
            exec(compile(ast.Module(body=[function], type_ignores=[]), '<code-identity>', 'exec'), namespace)
            local = {}
            exec(compile('def sample(): return "a literal with spaces"', folder + '/native.py', 'exec'), local)
            sample = local['sample']
            before = namespace['code_hash'](sample)
            sys.intern(sample.__code__.co_consts[1])
            self.assertEqual(namespace['code_hash'](sample), before)
            changed = types.FunctionType(sample.__code__.replace(co_consts=(None, 'changed')), {})
            self.assertNotEqual(namespace['code_hash'](changed), before)
            self.assertIn('co_lnotab', ast.unparse(function))
            self.assertIn('absent-code-field', ast.unparse(function))


def _qualified_realm():
    """Retest the frozen fixture assertions against v3 without shared mutation."""
    realm = dict(vars(qualified_tests))
    realm['execution'] = worker
    realm['frozen'] = types.SimpleNamespace(**dict(vars(original), environment_identity=worker.environment_identity))
    return realm


if worker is not None:
    _realm = _qualified_realm()
    _fixture = qualified_tests.NativeAdmissionV2AdversarialTests
    _methods = {}
    for _name, _value in vars(_fixture).items():
        if isinstance(_value, types.FunctionType):
            _methods[_name] = types.FunctionType(_value.__code__, _realm, _value.__name__,
                                                 _value.__defaults__, _value.__closure__)
    _refresh = _methods['refresh']

    def _refresh_v3(self):
        _refresh(self)
        self.contract['schema'] = worker.SCHEMA

    def _set_up_v3(cls):
        cls.environment = worker.environment_identity(sys.executable)
        cls.policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 7,
                      'execution_seconds': 7, 'pytest_version': cls.environment['pytest_version'], 'plugins': []}

    _methods['refresh'] = _refresh_v3
    _methods['setUpClass'] = classmethod(_set_up_v3)
    NativePortableQualifiedAdversarialTests = type('NativePortableQualifiedAdversarialTests',
                                                  (unittest.TestCase,), _methods)
    del _fixture


class SelectedInterpreterNativeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if worker is None:
            raise unittest.SkipTest('portable worker missing')
        cls.interpreter = os.environ.get('UDM_NATIVE_V3_INTERPRETER', sys.executable)
        cls.environment = worker.environment_identity(cls.interpreter)
        cls.policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 15,
                      'execution_seconds': 15, 'pytest_version': cls.environment['pytest_version'], 'plugins': []}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='udm-native-v3-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        (self.repo / 'subject.py').write_text('def value():\n return 0\n')
        (self.repo / 'test_subject.py').write_text('def test_old(): assert True\n')
        (self.repo / 'conftest.py').write_text('')
        self.git('init', '-q')
        self.base = self.commit()
        self.counter = 0

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Portable Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def fixture(self, tests, conftest=None):
        if conftest is not None:
            (self.repo / 'conftest.py').write_text(conftest)
            self.base = self.commit()
        (self.repo / 'test_subject.py').write_text(tests)
        commit = self.commit()
        contract = {'schema': worker.SCHEMA, 'repository': 'fixture/portable-v3', 'repo_path': str(self.repo),
                    'commit': commit, **original.source_identity(self.repo, commit), 'interpreter': self.interpreter,
                    'environment_sha256': original.fingerprint(self.environment), 'protocol_binding': 'e' * 64,
                    'horizon_seconds': self.policy['execution_seconds']}
        authority = admission.derive_suite_contract(self.repo, self.base, commit, 'e' * 64, repository=contract['repository'])
        return contract, authority

    def output(self):
        self.counter += 1
        return self.root / ('evidence-' + str(self.counter))

    def test_actual_failure_success_and_independent_receipt_reexecution(self):
        contract, authority = self.fixture('from subject import value\ndef test_old(): assert True\ndef test_new(): assert value()==1\n')
        certificate = worker.collect(contract, authority, self.output(), policy=self.policy)
        failed = worker.verify(contract, {'replacements': []}, self.output(), authority=authority,
                               admission_certificate=certificate, policy=self.policy)
        self.assertEqual(failed['status'], 'FAIL_NATIVE')
        candidate = {'replacements': [{'path': 'subject.py', 'original_sha256': original.sha256((self.repo / 'subject.py').read_bytes()),
                                      'replacement': 'def value():\n return 1\n'}]}
        passed = worker.verify(contract, candidate, self.output(), authority=authority,
                               admission_certificate=certificate, policy=self.policy)
        self.assertEqual(passed['status'], 'PASS_NATIVE')
        checked = worker.validate_receipt(contract, candidate, authority, certificate, passed,
                                          policy=self.policy, output_dir=self.output())
        self.assertIn('independent_reexecution', checked)

    def test_reasonless_xpass_is_refused_in_selected_native_environment(self):
        for marker in ('@pytest.mark.xfail', '@pytest.mark.xfail(strict=True)'):
            with self.subTest(marker=marker):
                contract, authority = self.fixture('import pytest\ndef test_old(): assert True\n' + marker + '\ndef test_new(): assert True\n')
                certificate = worker.collect(contract, authority, self.output(), policy=self.policy)
                receipt = worker.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                        admission_certificate=certificate, policy=self.policy)
                self.assertEqual(receipt['status'], 'UNKNOWN_SKIPPED_OR_XFAIL')

    def test_original_selected_order_is_retained_in_selected_native_environment(self):
        contract, authority = self.fixture('def test_old(): assert True\ndef test_new(): assert True\n',
            'def pytest_collection_modifyitems(items):\n items.reverse()\n')
        certificate = worker.collect(contract, authority, self.output(), policy=self.policy)
        self.assertEqual(certificate['collection']['selected_test_nodes'],
                         list(reversed(certificate['collection']['collected_test_nodes'])))
        receipt = worker.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                admission_certificate=certificate, policy=self.policy)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')

    def test_independent_licensed_plugin_distribution_in_selected_environment(self):
        contract, authority = self.fixture('def test_old(): assert True\ndef test_new(): assert True\n')
        policy = dict(self.policy, plugins=[{'module': 'doctest', 'distribution': 'pytest',
                                           'version': self.environment['pytest_version']}])
        certificate = worker.collect(contract, authority, self.output(), policy=policy)
        self.assertEqual(certificate['plugins'][0]['module'], 'doctest')
        receipt = worker.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                admission_certificate=certificate, policy=policy)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')

    def test_missing_protected_assertion_is_refused_in_selected_environment(self):
        contract, authority = self.fixture('def test_old(): assert True\nclass TestProtected:\n __test__ = False\n def test_new(self): assert True\n')
        with self.assertRaisesRegex(ValueError, 'MISSING_PROTECTED_ASSERTION'):
            worker.collect(contract, authority, self.output(), policy=self.policy)

    def test_changed_test_code_is_refused_in_selected_environment(self):
        contract, authority = self.fixture('def test_old(): assert True\ndef test_new(): assert True\n',
            'def pytest_runtest_setup(item):\n item.obj.__code__ = (lambda: None).__code__\n')
        certificate = worker.collect(contract, authority, self.output(), policy=self.policy)
        receipt = worker.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                admission_certificate=certificate, policy=self.policy)
        self.assertEqual(receipt['status'], 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY')
        self.assertTrue(receipt['execution']['changed_test_code'])

    def test_malformed_native_report_preserves_actual_attempt_counts(self):
        contract, authority = self.fixture('''def test_old(): assert True
def test_new():
 import atexit, pathlib, sys
 path = pathlib.Path(sys.argv[3])
 atexit.register(lambda: path.write_text('{'))
 assert True
''')
        certificate = worker.collect(contract, authority, self.output(), policy=self.policy)
        snapshot = getattr(worker, 'attempt_snapshot', lambda: {
            'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0})
        before = snapshot()
        output = self.output()
        with self.assertRaises(json.JSONDecodeError):
            worker.verify(contract, {'replacements': []}, output, authority=authority,
                          admission_certificate=certificate, policy=self.policy)
        self.assertEqual((output / 'execution' / 'report.json').read_bytes(), b'{')
        self.assertFalse((output / 'receipt.json').exists())
        self.assertEqual({key: value - before[key] for key, value in snapshot().items()},
                         {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2})


if __name__ == '__main__':
    unittest.main()
