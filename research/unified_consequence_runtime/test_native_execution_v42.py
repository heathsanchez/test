"""Frozen V42 real-native controls; no task outcomes or developmental claims.

Inherited adversarial contracts are privately rebound, preserving original
worker modules. Additional controls exercise actual original file-link imports.
"""
from __future__ import annotations

import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

from . import decisive_native_verify as original
from . import native_execution_v2 as frozen_worker
from . import test_native_admission_v2_adversarial as original_controls


def worker():
    return importlib.import_module(__package__ + '.native_execution_v42')


class NativeExecutionV42Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = worker()
        cls.interpreter = os.environ.get('UDM_NATIVE_V42_INTERPRETER', sys.executable)
        cls.environment = cls.worker.environment_identity(cls.interpreter)
        cls.policy = {'schema': cls.worker.POLICY_SCHEMA, 'collection_seconds': 15,
                      'execution_seconds': 15, 'pytest_version': cls.environment['pytest_version'], 'plugins': []}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='udm-execution-v42-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        (self.repo / 'subject.py').write_text('def value():\n return 0\n')
        (self.repo / 'alias.py').symlink_to('subject.py')
        (self.repo / 'test_subject.py').write_text('def test_old(): assert True\n')
        (self.repo / 'pytest.ini').write_text('[pytest]\naddopts=--import-mode=importlib\n')
        (self.repo / 'data').mkdir()
        (self.repo / 'data/malformed.py').write_bytes(b'def invalid(:\n print "data only"\n')
        self.git('init', '-q')
        self.base = self.commit()
        self.counter = 0

    def git(self, *args):
        return subprocess.check_output(['git', '--no-replace-objects', '-C', str(self.repo), *args],
            stderr=subprocess.PIPE, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Native V42 Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'frozen native fixture')
        return self.git('rev-parse', 'HEAD')

    def output(self):
        self.counter += 1
        return self.root / ('evidence-' + str(self.counter))

    def contract(self, tests):
        (self.repo / 'test_subject.py').write_text(tests)
        commit = self.commit()
        contract = {'schema': self.worker.SCHEMA, 'repository': 'fixture/native-v42', 'repo_path': str(self.repo),
                    'commit': commit, **self.worker.original.source_identity(self.repo, commit),
                    'interpreter': self.interpreter, 'environment_sha256': original.fingerprint(self.environment),
                    'protocol_binding': 'd' * 64, 'horizon_seconds': self.policy['execution_seconds']}
        authority = self.worker.admission.derive_suite_contract(
            self.repo, self.base, commit, 'd' * 64, repository=contract['repository'])
        return contract, authority

    def candidate(self, name='subject.py', value=1):
        return {'replacements': [{'path': name,
            'original_sha256': original.sha256((self.repo / name).read_bytes()),
            'replacement': 'def value():\n return ' + str(value) + '\n'}]}

    def test_existing_collection_assertion_and_replay_algorithms_remain_original_code(self):
        for name in ('_roots', '_collection', '_binding', 'collect', 'validate_certificate',
                     '_status', 'verify', 'validate_receipt'):
            with self.subTest(function=name):
                self.assertIs(getattr(self.worker, name).__code__, getattr(frozen_worker, name).__code__)
                self.assertIsNot(getattr(self.worker, name).__globals__, vars(frozen_worker))
        self.assertEqual(self.worker.SCHEMA, 'UDM_GENERIC_NATIVE_PYTEST_V42')
        self.assertEqual(self.worker.CERTIFICATE_SCHEMA, 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42')
        self.assertEqual(self.worker.POLICY_SCHEMA, 'UDM_NATIVE_EXECUTION_POLICY_V42')
        self.assertEqual(frozen_worker.SCHEMA, 'UDM_GENERIC_NATIVE_PYTEST_V2')

    def test_actual_link_import_failure_success_and_independent_reexecution(self):
        contract, authority = self.contract('from alias import value\ndef test_old(): assert True\ndef test_new(): assert value()==1\n')
        certificate = self.worker.collect(contract, authority, self.output(), policy=self.policy)
        self.assertEqual(certificate['collection']['collected_test_nodes'],
                         ['test_subject.py::test_old', 'test_subject.py::test_new'])
        self.worker.validate_certificate(contract, authority, certificate, policy=self.policy, output_dir=self.output())
        failed = self.worker.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                    admission_certificate=certificate, policy=self.policy)
        self.assertEqual(failed['status'], 'FAIL_NATIVE')
        self.assertEqual(failed['junit']['failures'], 1)
        candidate = self.candidate()
        passed = self.worker.verify(contract, candidate, self.output(), authority=authority,
                                    admission_certificate=certificate, policy=self.policy)
        self.assertEqual(passed['status'], 'PASS_NATIVE')
        self.assertEqual(passed['junit']['passed'], 2)
        checked = self.worker.validate_receipt(contract, candidate, authority, certificate, passed,
                                              policy=self.policy, output_dir=self.output())
        self.assertIn('independent_reexecution', checked)
        imports = passed['execution']['import_manifest']
        self.assertTrue(any(row['path'] == 'subject.py' for row in imports), imports)

    def test_alias_candidate_is_refused_before_native_warrant(self):
        contract, authority = self.contract('from alias import value\ndef test_old(): assert True\ndef test_new(): assert value()==1\n')
        certificate = self.worker.collect(contract, authority, self.output(), policy=self.policy)
        with self.assertRaises(ValueError):
            self.worker.verify(contract, self.candidate('alias.py'), self.output(), authority=authority,
                               admission_certificate=certificate, policy=self.policy)

    def test_malformed_imported_python_is_collection_unknown(self):
        contract, authority = self.contract('import importlib\nimportlib.import_module("data.malformed")\ndef test_old(): assert True\ndef test_new(): assert True\n')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_COLLECTION_ERROR'):
            self.worker.collect(contract, authority, self.output(), policy=self.policy)

    def test_raw_link_text_change_cannot_replay_identical_projection_evidence(self):
        contract, authority = self.contract('from alias import value\ndef test_old(): assert True\ndef test_new(): assert value()==0\n')
        certificate = self.worker.collect(contract, authority, self.output(), policy=self.policy)
        (self.repo / 'alias.py').unlink()
        (self.repo / 'alias.py').symlink_to('./subject.py')
        changed = self.commit()
        other = dict(contract, commit=changed, **self.worker.original.source_identity(self.repo, changed))
        with self.assertRaises(ValueError):
            other_authority = self.worker.admission.derive_suite_contract(self.repo, self.base, changed, 'd' * 64,
                                                                         repository=contract['repository'])
            self.worker.validate_certificate(other, other_authority, certificate, policy=self.policy)

    def test_old_worker_certificate_is_not_v42_authority(self):
        contract, authority = self.contract('from alias import value\ndef test_old(): assert True\ndef test_new(): assert value()==0\n')
        certificate = self.worker.collect(contract, authority, self.output(), policy=self.policy)
        forged = copy.deepcopy(certificate)
        forged['schema'] = 'UDM_NATIVE_ADMISSION_CERTIFICATE_V3'
        with self.assertRaises(ValueError):
            self.worker.validate_certificate(contract, authority, forged, policy=self.policy)


# Reuse the already frozen real-native adversarial fixture statements with only
# explicit worker/source/static-authority dependencies changed in private globals.
# No test statement, protected assertion, collection oracle or original module is
# patched. Import laziness lets the source-only RED run precede implementation.
def inherited_suite():
    execution = worker()
    realm = dict(vars(original_controls), execution=execution, admission=execution.admission,
                 frozen=execution.original)
    fixture = original_controls.NativeAdmissionV2AdversarialTests
    methods = {}
    for name, value in vars(fixture).items():
        if isinstance(value, types.FunctionType):
            methods[name] = types.FunctionType(value.__code__, realm, value.__name__,
                                               value.__defaults__, value.__closure__)
    refresh = methods['refresh']
    def refresh_v42(self):
        refresh(self)
        self.contract['schema'] = execution.SCHEMA
    def setup_v42(cls):
        cls.environment = execution.environment_identity(sys.executable)
        cls.policy = {'schema': execution.POLICY_SCHEMA, 'collection_seconds': 15,
                      'execution_seconds': 15, 'pytest_version': cls.environment['pytest_version'], 'plugins': []}
    methods['refresh'] = refresh_v42
    methods['setUpClass'] = classmethod(setup_v42)
    return type('NativeV42InheritedAdversarialTests', (unittest.TestCase,), methods)


def load_tests(loader, tests, pattern):
    tests.addTests(loader.loadTestsFromTestCase(inherited_suite()))
    return tests


if __name__ == '__main__':
    unittest.main()
