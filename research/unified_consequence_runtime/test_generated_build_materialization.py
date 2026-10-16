"""Build-boundary fixtures, not unfamiliar research tasks or sandbox proofs."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from research.unified_consequence_runtime import decisive_native_verify as verifier
from research.unified_consequence_runtime.test_native_frontier import MemoryMachine


BACKEND = r'''from pathlib import Path
import base64,hashlib,zipfile

def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    root=Path(__file__).parent
    files={str(p.relative_to(root/'src')):p.read_bytes() for p in (root/'src').rglob('*.py')}
    files['sample/_version.py']=b'GENERATED_VALUE = 42\n'
    prefix='build_fixture-0.1.dist-info/'
    files[prefix+'METADATA']=b'Metadata-Version: 2.1\nName: build-fixture\nVersion: 0.1\n'
    files[prefix+'WHEEL']=b'Wheel-Version: 1.0\nGenerator: fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n'
    records=[]
    for name,raw in sorted(files.items()):
        digest=base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode()
        records.append(name+',sha256='+digest+','+str(len(raw)))
    files[prefix+'RECORD']=('\n'.join(records)+'\n'+prefix+'RECORD,,\n').encode()
    name='build_fixture-0.1-py3-none-any.whl'
    with zipfile.ZipFile(Path(wheel_directory)/name,'w') as z:
        for name2,raw in sorted(files.items()): z.writestr(name2,raw)
    return name
'''


def fixture(root):
    repo=root/'source';repo.mkdir()
    subprocess.run(['git','init','-q',str(repo)],check=True)
    (repo/'src/sample').mkdir(parents=True);(repo/'tests').mkdir()
    (repo/'src/sample/__init__.py').write_text('VALUE = 42\n')
    (repo/'tests/test_native.py').write_text('from sample._version import GENERATED_VALUE\ndef test_native(): assert GENERATED_VALUE == 42\n')
    (repo/'pyproject.toml').write_text('[build-system]\nrequires = []\nbuild-backend = "fixture_backend"\nbackend-path = ["."]\n')
    (repo/'fixture_backend.py').write_text(BACKEND)
    subprocess.run(['git','-C',str(repo),'add','.'],check=True)
    subprocess.run(['git','-C',str(repo),'-c','user.name=Build Fixture','-c','user.email=fixture@example.invalid','commit','-qm','frozen fixture'],check=True)
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    contract={'schema':verifier.SCHEMA,'repository':'local/build-fixture','repo_path':str(repo),'commit':commit,
        **verifier.source_identity(repo,commit),'interpreter':sys.executable,
        'environment_sha256':verifier.fingerprint(verifier.environment_identity(sys.executable)),
        'protocol_binding':'a'*64,'horizon_seconds':7}
    return repo,contract


class GeneratedBuildContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from research.unified_consequence_runtime.generic_build_materialization import materialize
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name);cls.repo,cls.contract=fixture(cls.root)
        cls.built=materialize(cls.repo,cls.root/'build',python=sys.executable)
        cls.evidence=cls.built['generated_wheel_evidence']
        cls.files=verifier._snapshot(cls.repo,cls.contract['commit'])[1]

    def setUp(self):
        self.local=tempfile.TemporaryDirectory();self.addCleanup(self.local.cleanup)
        self.out=Path(self.local.name)

    def test_real_pep517_build_retains_wheel_and_source_bound_evidence(self):
        self.assertEqual(self.built['status'],'BUILT_NOT_SCIENTIFICALLY_VERIFIED')
        self.assertTrue(Path(self.evidence['wheel_path']).is_file())
        self.assertEqual(self.evidence['source_commit'],self.contract['commit'])
        self.assertEqual(self.evidence['source_tree_sha256'],self.contract['tracked_tree_sha256'])
        self.assertEqual(hashlib.sha256(Path(self.evidence['wheel_path']).read_bytes()).hexdigest(),self.evidence['wheel_sha256'])
        self.assertEqual(self.built['costs']['build_calls'],1)
        self.assertFalse((self.repo/'src/sample/_version.py').exists())

    def test_src_layout_generated_module_passes_only_after_independent_build(self):
        cold=verifier.verify(self.contract,{'replacements':[]},self.out/'cold')
        self.assertEqual(cold['status'],'UNKNOWN_NATIVE_ERROR')
        warm=verifier.verify(self.contract,{'replacements':[]},self.out/'warm',generated_wheel_evidence=self.evidence)
        self.assertEqual(warm['status'],'PASS_NATIVE')
        self.assertEqual(warm['junit']['passed'],1)
        self.assertEqual(warm['generated_module_count'],1)
        self.assertIn('src/sample/_version.py',[x['path'] for x in warm['import_manifest']])
        self.assertEqual(warm['costs']['build_calls'],1)
        self.assertTrue((self.out/'warm/build-verification/wheels'/Path(self.evidence['wheel_path']).name).is_file())

    def test_forged_wheel_with_plausible_hashes_is_rejected_by_rebuild(self):
        evidence=dict(self.evidence)
        wheel=self.out/Path(evidence['wheel_path']).name
        with zipfile.ZipFile(evidence['wheel_path']) as src, zipfile.ZipFile(wheel,'w') as dst:
            for name in src.namelist(): dst.writestr(name,b'GENERATED_VALUE = 999\n' if name=='sample/_version.py' else src.read(name))
        evidence['wheel_path']=str(wheel);evidence['wheel_sha256']=hashlib.sha256(wheel.read_bytes()).hexdigest()
        from research.unified_consequence_runtime.generated_overlay_gate import wheel_content_digest
        evidence['wheel_content_sha256']=wheel_content_digest(wheel)
        with self.assertRaisesRegex(ValueError,'independent build'):
            verifier.verify(self.contract,{'replacements':[]},self.out/'forged',generated_wheel_evidence=evidence)
        failure=json.loads((self.out/'forged/receipt.json').read_text())
        self.assertEqual(failure['status'],'UNKNOWN_BUILD_AUTHENTICATION')
        self.assertEqual(failure['costs']['build_calls'],1)
        self.assertEqual(failure['costs']['native_calls'],0)
        from research.unified_consequence_runtime.decisive_native_frontier import NativeFrontierRuntime
        machine=MemoryMachine()
        runtime=NativeFrontierRuntime(machine,self.contract,self.out/'forged-runtime',generated_wheel_evidence=evidence)
        with self.assertRaisesRegex(ValueError,'independent build'):
            runtime.admit({'replacements':[]})
        self.assertEqual(machine.costs[-1]['costs']['build_calls'],1)
        self.assertFalse(any(n.kind=='executable_capability' for n in machine.log))

    def test_wrong_build_source_environment_or_recipe_rejected(self):
        for field in ('source_commit','source_tree_sha256','build_environment_sha256','build_recipe_sha256','builder_sha256'):
            wrong={**self.evidence,field:'0'*(40 if field=='source_commit' else 64)}
            with self.subTest(field=field),self.assertRaises(ValueError):
                verifier.verify(self.contract,{'replacements':[]},self.out/field,generated_wheel_evidence=wrong)

    def test_arbitrary_generated_bytes_are_not_an_authority_input(self):
        with self.assertRaises(TypeError):
            verifier.verify(self.contract,{'replacements':[]},self.out/'raw',generated_modules={'src/sample/_version.py':b'GENERATED_VALUE=42\n'})

    def test_runtime_native_lifecycle_retains_wheel_in_existing_cas(self):
        from research.unified_consequence_runtime.decisive_native_frontier import NativeFrontierRuntime
        machine=MemoryMachine()
        runtime=NativeFrontierRuntime(machine,self.contract,self.out/'runtime',generated_wheel_evidence=self.evidence)
        key=runtime.admit({'replacements':[]})
        self.assertEqual(runtime.execute(key)[0]['status'],'PASS_NATIVE')
        unrelated=machine.append('unrelated_evidence',{'status':'independent'})
        runtime.withdraw(key)
        with self.assertRaises(PermissionError):runtime.execute(key)
        self.assertIn(unrelated,machine.live_ids(machine.log))
        restored=runtime.restore(key)
        reloaded=MemoryMachine();reloaded.log=copy.deepcopy(machine.log);reloaded.objects=copy.deepcopy(machine.objects)
        # Native restoration/reload can recover the retained wheel even if the original path vanished.
        evidence=dict(self.evidence,wheel_path=str(self.out/'missing-original.whl'))
        restart=NativeFrontierRuntime(reloaded,self.contract,self.out/'restart',generated_wheel_evidence=evidence)
        receipt,_=restart.execute(restored)
        self.assertEqual(receipt['status'],'PASS_NATIVE')
        self.assertEqual(receipt['costs']['build_calls'],1)
        self.assertFalse((self.repo/'src/sample/_version.py').exists())


class GeneratedOverlayContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def overlay(self, files, members):
        from research.unified_consequence_runtime.generated_overlay_gate import generated_overlay
        wheel=self.root/'sample.whl'
        with zipfile.ZipFile(wheel,'w') as archive:
            for name,raw in members:archive.writestr(name,raw)
        return generated_overlay(wheel,files,expected_wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest())
    def test_src_wheel_installed_layout_maps_to_tracked_package_root(self):
        additions=self.overlay({'src/sample/__init__.py':b'VALUE=1\n'},[('sample/__init__.py',b'VALUE=1\n'),('sample/_version.py',b'VERSION=1\n')])
        self.assertEqual(additions,{'src/sample/_version.py':b'VERSION=1\n'})
    def test_generated_source_cannot_overwrite_tracked_or_test_or_config(self):
        for name,raw in [('sample/__init__.py',b'ALTERED=1\n'),('sample/test_extra.py',b'pass\n'),('sample/extra_test.py',b'pass\n'),('sample/conftest.py',b'pass\n'),('sample/pytest.py',b'pass\n'),('sample/pyproject.toml',b'bad'),('newpackage/extra.py',b'pass\n'),('../escape.py',b'pass\n')]:
            with self.subTest(name=name),self.assertRaises(ValueError):
                self.overlay({'src/sample/__init__.py':b'VALUE=1\n'},[(name,raw)])
    def test_custom_pytest_patterns_and_ambiguous_layout_are_rejected(self):
        with self.assertRaises(ValueError):
            self.overlay({'src/sample/__init__.py':b'', 'pytest.ini':b'[pytest]\npython_files = authority.py\n'}, [('sample/authority.py',b'pass\n')])
        with self.assertRaises(ValueError):
            self.overlay({'src/sample/__init__.py':b'', 'sample/__init__.py':b''}, [('sample/_version.py',b'V=1\n')])
    def test_no_unexpected_bytecode_extension_or_duplicate_members(self):
        for members in [[('sample/x.pyc',b'bad')],[('sample/x.so',b'bad')],[('sample/_version.py',b'V=1'),('sample/_version.py',b'V=2')]]:
            with self.subTest(members=members),self.assertRaises(ValueError):
                self.overlay({'src/sample/__init__.py':b''},members)

if __name__=='__main__':unittest.main()
