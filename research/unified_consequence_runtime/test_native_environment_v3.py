"""Versioned provisioning tests exercise source reuse and actual runtime pins."""
import hashlib,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
from . import native_environment_v2 as previous
try:
 from . import native_environment_v3 as current
except ImportError:
 current=None

class EnvironmentProvisionV3(unittest.TestCase):
 def setUp(self):self.assertIsNotNone(current,'versioned source-preserving environment operation is missing')
 def profile(self):
  v='.'.join(map(str,sys.version_info[:3]))
  return {'id':'host','python_version':v,'python_implementation':'CPython','pytest_version':'8.3.5','packages':['pytest==8.3.5'],'plugins':[]}
 def test_runtime_binary_and_stdlib_are_independently_frozen(self):
  record=current.freeze_runtime(sys.executable)
  self.assertEqual(record['identity'],current.execution.runtime_identity(sys.executable))
  profile=self.profile();current.validate_runtime(profile,record)
  changed=json.loads(json.dumps(record));changed['identity']['executable_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'runtime identity'):current.validate_runtime(profile,changed)
  changed=json.loads(json.dumps(record));changed['identity']['stdlib_manifest_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'runtime identity'):current.validate_runtime(profile,changed)
 def test_source_profile_cannot_select_a_different_interpreter(self):
  record=current.freeze_runtime(sys.executable);profile=self.profile();profile['python_version']='3.6.5'
  with self.assertRaisesRegex(ValueError,'version'):current.validate_runtime(profile,record)
 def test_existing_provision_algorithm_is_reused_with_isolated_bindings(self):
  old_exec=previous.sys.executable;old_worker=previous.execution
  bound=current.bound_provision(sys.executable)
  self.assertIs(bound.__code__,previous.provision.__code__)
  self.assertIsNot(bound.__globals__,previous.provision.__globals__)
  self.assertEqual(bound.__globals__['sys'].executable,sys.executable)
  self.assertIs(bound.__globals__['execution'],current.execution)
  self.assertIs(bound.__globals__['environment_identity'],current.execution.environment_identity)
  self.assertEqual(previous.sys.executable,old_exec);self.assertIs(previous.execution,old_worker)
 def test_invalid_runtime_refuses_before_source_transport(self):
  profile=self.profile();catalog={'schema':'UDM_NATIVE_ENVIRONMENT_CATALOG_V3','profiles':[profile]}
  record=current.freeze_runtime(sys.executable);record['identity']['executable_sha256']='0'*64
  with tempfile.TemporaryDirectory() as tmp,patch.object(current,'_command') as transport:
   out=pathlib.Path(tmp)/'new'
   with self.assertRaisesRegex(ValueError,'runtime identity'):
    current.provision({},out,'a'*64,catalog=catalog,runtimes={'host':record})
   transport.assert_not_called();self.assertFalse(out.exists())
 def test_policy_is_exact_profile_license(self):
  profile=self.profile();value=current.execution_policy(profile,collection_seconds=60,execution_seconds=600)
  self.assertEqual(value['schema'],current.execution.POLICY_SCHEMA)
  self.assertEqual(value['pytest_version'],'8.3.5');self.assertEqual(value['plugins'],[])
 def test_host_binary_pin_precedes_any_child_claim(self):
  record=current.freeze_runtime(sys.executable)
  with tempfile.TemporaryDirectory() as tmp:
   fake=pathlib.Path(tmp)/'python';fake.write_text('#!/bin/sh\nexit 0\n');fake.chmod(0o755)
   changed=dict(record,interpreter=str(fake))
   with patch.object(current.execution,'runtime_identity',return_value=record['identity']) as child:
    with self.assertRaisesRegex(ValueError,'runtime identity'):current.validate_runtime(self.profile(),changed)
    child.assert_not_called()
 def test_installed_child_must_match_external_runtime(self):
  record=current.freeze_runtime(sys.executable)
  with tempfile.TemporaryDirectory() as tmp:
   fake=pathlib.Path(tmp)/'python';fake.write_bytes(b'altered executable')
   with self.assertRaisesRegex(ValueError,'runtime identity'):
    current.validate_runtime(self.profile(),record,interpreter=fake)
 def test_pinned_distribution_bytes_are_checked_across_build(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);site=root/'lib'/('python'+'.'.join(map(str,sys.version_info[:2])))/'site-packages';site.mkdir(parents=True)
   info=site/'pytest-8.3.5.dist-info';info.mkdir();(info/'METADATA').write_text('Name: pytest\nVersion: 8.3.5\n')
   module=site/'pytest.py';module.write_text('VALUE=1\n')
   (info/'RECORD').write_text('pytest.py,,\npytest-8.3.5.dist-info/METADATA,,\npytest-8.3.5.dist-info/RECORD,,\n')
   interpreter=root/'bin/python';interpreter.parent.mkdir();interpreter.write_bytes(b'external runtime')
   before=current.installed_package_identity(interpreter,self.profile())
   module.write_text('VALUE=2\n')
   self.assertNotEqual(before,current.installed_package_identity(interpreter,self.profile()))
   (info/'METADATA').write_text('Name: pytest\nVersion: 9.0\n')
   with self.assertRaisesRegex(ValueError,'pinned distribution'):current.installed_package_identity(interpreter,self.profile())
 def test_frozen_artifact_hash_is_required_for_every_installed_pin(self):
  profile=self.profile()
  with self.assertRaisesRegex(ValueError,'artifact'):current.package_requirements(profile)
  profile['package_artifacts']={'pytest':{'sha256':'a'*64}}
  self.assertEqual(current.package_requirements(profile),'pytest==8.3.5 --hash=sha256:'+('a'*64)+'\n')
  profile['package_artifacts']['pytest']['sha256']='forged'
  with self.assertRaisesRegex(ValueError,'artifact'):current.package_requirements(profile)

if __name__=='__main__':unittest.main()
