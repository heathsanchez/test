"""Native admission certificates: isolated fixtures, never prospective wins."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import decisive_native_verify as original
from .native_admission_v2 import derive_suite_contract
try:
    from . import native_execution_v2 as worker
except ImportError:
    worker=None


class NativeExecutionCertificateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.folder.cleanup)
        cls.root=Path(cls.folder.name);cls.repo=cls.root/'source';cls.repo.mkdir()
        def git(*args):return subprocess.check_output(['git','-C',str(cls.repo),*args],stderr=subprocess.PIPE).decode().strip()
        git('init','-q');(cls.repo/'subject.py').write_text('def value():\n return 0\n')
        (cls.repo/'test_subject.py').write_text('from subject import value\ndef test_contract(): assert value()==0\n')
        git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','base');cls.base=git('rev-parse','HEAD')
        (cls.repo/'test_subject.py').write_text('from subject import value\ndef test_contract(): assert value()==1\n')
        git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','author test');cls.commit=git('rev-parse','HEAD')
        cls.env=original.environment_identity(sys.executable)
        cls.contract={'schema':'UDM_GENERIC_NATIVE_PYTEST_V2','repository':'fixture/source','repo_path':str(cls.repo),
            'commit':cls.commit,**original.source_identity(cls.repo,cls.commit),'interpreter':sys.executable,
            'environment_sha256':original.fingerprint(cls.env),'protocol_binding':'e'*64,'horizon_seconds':7}
        cls.policy={'schema':'UDM_NATIVE_EXECUTION_POLICY_V2','collection_seconds':7,'execution_seconds':7,
            'pytest_version':cls.env['pytest_version'],'plugins':[]}
        cls.authority=derive_suite_contract(cls.repo,cls.base,cls.commit,'e'*64,repository='fixture/source')

    def setUp(self):self.assertIsNotNone(worker,'versioned independent native worker is missing')

    def test_independent_collection_and_honest_protected_failure_then_native_success(self):
        certificate=worker.collect(self.contract,self.authority,self.root/'collect-positive',policy=self.policy)
        self.assertEqual(certificate['status'],'ADMITTED_NATIVE_COLLECTION')
        self.assertEqual(certificate['collection']['collected_test_nodes'],['test_subject.py::test_contract'])
        failed=worker.verify(self.contract,{'replacements':[]},self.root/'fail',authority=self.authority,
            admission_certificate=certificate,policy=self.policy)
        self.assertEqual(failed['status'],'FAIL_NATIVE');self.assertEqual(failed['junit']['failures'],1)
        candidate={'replacements':[{'path':'subject.py','original_sha256':original.sha256((self.repo/'subject.py').read_bytes()),
            'replacement':'def value():\n return 1\n'}]}
        passed=worker.verify(self.contract,candidate,self.root/'pass',authority=self.authority,
            admission_certificate=certificate,policy=self.policy)
        self.assertEqual(passed['status'],'PASS_NATIVE');self.assertEqual(passed['junit']['passed'],1)

    def test_certificate_validation_reexecutes_independent_original_collection(self):
        certificate=worker.collect(self.contract,self.authority,self.root/'collect-replay',policy=self.policy)
        checked=worker.validate_certificate(self.contract,self.authority,certificate,policy=self.policy)
        self.assertEqual(checked['status'],'ADMITTED_NATIVE_COLLECTION')
        weaker=json.loads(json.dumps(certificate));weaker['collection']['collected_test_nodes']=[]
        with self.assertRaises(ValueError):worker.validate_certificate(self.contract,self.authority,weaker,policy=self.policy)


if __name__=='__main__':unittest.main()
