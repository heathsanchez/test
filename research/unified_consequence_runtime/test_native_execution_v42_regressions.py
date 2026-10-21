"""Pre-fix V42 review regression: source imports cannot use installed aliases.

This disposable admission diagnostic was frozen after the independent reviewer
observed a false native warrant. It is not a prospective developmental result.
The original acceptance tests and old verifiers remain byte-for-byte intact.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from . import native_execution_v42 as worker


class NativeV42SourceImportRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interpreter = os.environ.get('UDM_NATIVE_V42_INTERPRETER', sys.executable)
        cls.environment = worker.environment_identity(cls.interpreter)
        cls.policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 15,
            'execution_seconds': 15, 'pytest_version': cls.environment['pytest_version'], 'plugins': []}

    def test_flat_src_module_and_internal_alias_refuse_preloaded_installed_substitution(self):
        for kind in ('regular', 'internal-file-alias'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix='udm-v42-import-review-') as folder:
                root = Path(folder)
                repo = root/'source'
                (repo/'src').mkdir(parents=True)
                (repo/'target.py').write_text('VALUE = 42\n')
                if kind == 'regular':
                    (repo/'src/pluggy.py').write_text('VALUE = 42\n')
                else:
                    (repo/'src/pluggy.py').symlink_to('../target.py')
                (repo/'pytest.ini').write_text('[pytest]\naddopts=--import-mode=importlib\n')
                (repo/'test_native.py').write_text('def test_old(): assert True\n')
                def git(*args):
                    return subprocess.check_output(['git','--no-replace-objects','-C',str(repo),*args],
                        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),stderr=subprocess.PIPE).decode().strip()
                def commit():
                    git('add','.')
                    git('-c','user.name=Independent Review Fixture','-c','user.email=fixture@example.invalid',
                        'commit','-qm','original diagnostic fixture')
                    return git('rev-parse','HEAD')
                git('init','-q')
                base = commit()
                # Pytest already imports installed pluggy. This assertion can pass
                # on that installed module while bypassing the original src file.
                (repo/'test_native.py').write_text('import pluggy\ndef test_old(): assert True\n'
                                                  'def test_new(): assert pluggy.__name__=="pluggy"\n')
                head = commit()
                contract = {'schema':worker.SCHEMA,'repository':'fixture/review-src-module','repo_path':str(repo),
                    'commit':head,**worker.original.source_identity(repo,head),'interpreter':self.interpreter,
                    'environment_sha256':worker.fingerprint(self.environment),'protocol_binding':'b'*64,
                    'horizon_seconds':self.policy['execution_seconds']}
                authority = worker.admission.derive_suite_contract(repo,base,head,'b'*64,
                                                                   repository=contract['repository'])
                with self.assertRaisesRegex(ValueError,'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'):
                    worker.collect(contract,authority,root/'collection',policy=self.policy)

    def test_cold_import_refuses_changed_transitive_source_bytes(self):
        names = ('decisive_native_verify.py', 'native_admission_v2.py', 'native_execution_v2.py',
                 'native_execution_v3.py', 'native_source_v42.py', 'native_admission_v42.py',
                 'native_execution_v42.py')
        origin = Path(worker.__file__).parent
        script = ('import sys;sys.path.insert(0,sys.argv[1]);'
                  'from research.unified_consequence_runtime import native_execution_v42 as worker;'
                  'worker._runner_hash()')
        # A source comment changes provenance while preserving Python behavior.
        # Retained runtime authority must reject it before a restarted capability
        # can treat freshly loaded implementation bytes as their own source pin.
        for changed in ('native_source_v42.py', 'native_admission_v42.py', 'native_execution_v3.py'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory(prefix='udm-v42-cold-import-') as folder:
                package = Path(folder)/'research/unified_consequence_runtime'
                package.mkdir(parents=True)
                for name in names:
                    shutil.copyfile(origin/name,package/name)
                original = subprocess.run([sys.executable,'-I','-B','-c',script,folder],
                                           capture_output=True,text=True,timeout=30)
                self.assertEqual(original.returncode,0,original.stderr)
                with (package/changed).open('ab') as stream:
                    stream.write(b'\n# independent cold-restart provenance mutation\n')
                altered = subprocess.run([sys.executable,'-I','-B','-c',script,folder],
                                          capture_output=True,text=True,timeout=30)
                self.assertNotEqual(altered.returncode,0,'altered transitive source admitted on cold import: '+changed)
                self.assertIn('SOURCE',altered.stderr.upper())


if __name__ == '__main__':
    unittest.main()
