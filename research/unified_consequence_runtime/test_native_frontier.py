"""Generic adapter contracts on bookkeeping fixtures, never research targets."""
from dataclasses import asdict, replace
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research.unified_consequence_runtime.developmental_machine import Capability, canonical, digest
from research.unified_consequence_runtime import generic_native_verify as verifier


class Node:
    def __init__(self, kind, payload, premises=()):
        self.kind, self.payload, self.premises = kind, payload, tuple(premises)
        self.id = digest(canonical([kind, payload, premises]).encode())


class MemoryMachine:
    """Only causal bookkeeping is substituted; native results are real pytest."""
    def __init__(self):
        self.log, self.objects, self.costs = [], {}, []
        self.mt = self
    def append(self, kind, payload, premises=()):
        node=Node(kind,payload,premises); self.log.append(node); return node.id
    def put(self, value):
        raw=canonical(value); key=digest(raw.encode()); self.objects[key]=raw; return key
    def get(self, key):
        raw=self.objects[key]
        if digest(raw.encode()) != key: raise ValueError('persisted executable object changed')
        return json.loads(raw)
    def flush(self): pass
    def live_ids(self, log):
        dead={n.payload['target'] for n in log if n.kind=='revoke'}
        while True:
            old=set(dead); dead.update(n.id for n in log if any(p in dead for p in n.premises))
            if old==dead: return {n.id for n in log if n.id not in dead}
    def flash_live_ids(self): return self.live_ids(self.log)
    def descriptor(self, key):
        raw=dict(next(n.payload for n in self.log if n.id==key))
        for name in ('dependencies','evidence'): raw[name]=tuple(raw[name])
        return Capability(**raw)
    def withdraw(self, key, reason):
        return self.append('revoke',{'target':self.descriptor(key).dependencies[0],'reason':reason})


class NativeFrontierContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_tmp=tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.root_tmp.cleanup)
        cls.root=Path(cls.root_tmp.name); cls.repo=cls.root/'repo'; cls.repo.mkdir()
        cls.git('init','-q')
        (cls.repo/'src/sample').mkdir(parents=True); (cls.repo/'tests').mkdir()
        (cls.repo/'src/sample/__init__.py').write_text('VALUE = 1\n')
        (cls.repo/'tests/test_native.py').write_text('from sample import VALUE\ndef test_value(): assert VALUE == 1\n')
        cls.git('add','.')
        cls.git('-c','user.name=Native fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
        commit=cls.git('rev-parse','HEAD').decode().strip()
        cls.contract={'schema':verifier.SCHEMA,'repository':'local/native-fixture',
            'repo_path':str(cls.repo),'commit':commit,**verifier.source_identity(cls.repo,commit),
            'interpreter':sys.executable,
            'environment_sha256':verifier.fingerprint(verifier.environment_identity(sys.executable)),
            'protocol_binding':'1'*64,'horizon_seconds':7}
    @classmethod
    def git(cls,*args):
        return subprocess.check_output(['git','-C',str(cls.repo),*args],stderr=subprocess.PIPE)
    def setUp(self):
        path=Path(__file__).with_name('native_frontier.py')
        self.assertTrue(path.exists(),'typed native-frontier adapter is not implemented')
        self.nf=importlib.import_module('research.unified_consequence_runtime.native_frontier')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.machine=MemoryMachine()
        self.runtime=self.nf.NativeFrontierRuntime(self.machine,self.contract,Path(self.tmp.name)/'out')
    def candidate(self):
        return {'replacements':[]}
    def forged(self,key,**changes):
        cap=replace(self.machine.descriptor(key),**changes)
        node=next(n for n in self.machine.log if n.id==key)
        return self.machine.append('executable_capability',asdict(cap),node.premises)

    def test_empty_candidate_admits_native_activation_and_reexecutes(self):
        key=self.runtime.admit(self.candidate())
        cap=self.machine.descriptor(key)
        self.assertEqual(cap.operation,'native.pytest_suite')
        self.assertEqual(cap.transition,'ACTIVATION')
        self.assertEqual(self.machine.get(cap.program),self.candidate())
        receipt,consequence=self.runtime.execute(key)
        self.assertEqual(receipt['status'],'PASS_NATIVE')
        self.assertEqual(receipt['junit']['passed'],1)
        self.assertEqual(next(n for n in self.machine.log if n.id==consequence).premises,(key,))
        self.assertEqual(self.runtime.projection_payload(key)['profiles'],
                         [self.contract['repository']+'@'+self.contract['commit']])
        self.assertEqual(self.runtime.authority_ceiling['external_effects'],'NONE')
        self.assertEqual(self.runtime.authority_ceiling['reference_monitor'],'UNKNOWN_NONBYPASSABILITY')

    def test_executable_patch_admission_preserves_actual_code(self):
        candidate={'replacements':[{'path':'src/sample/__init__.py',
            'original_sha256':digest(b'VALUE = 1\n'),'replacement':'VALUE = 1\nEXTRA = 2\n'}]}
        key=self.runtime.admit(candidate)
        self.assertEqual(self.machine.descriptor(key).transition,'CAPABILITY_LANGUAGE_EXTENSION')
        self.assertEqual(self.machine.get(self.machine.descriptor(key).program),candidate)
        self.assertEqual((self.repo/'src/sample/__init__.py').read_text(),'VALUE = 1\n')

    def test_native_failure_observed_but_cannot_be_admitted(self):
        candidate={'replacements':[{'path':'src/sample/__init__.py',
            'original_sha256':digest(b'VALUE = 1\n'),'replacement':'VALUE = 2\n'}]}
        with self.assertRaisesRegex(ValueError,'FAIL_NATIVE'):self.runtime.admit(candidate)
        self.assertFalse(any(n.kind=='executable_capability' for n in self.machine.log))
        self.assertTrue(any(n.kind=='generic_native_observation' for n in self.machine.log))

    def test_forged_pass_with_skipped_native_obligations_rejected(self):
        receipt=self.runtime.observe()
        receipt['junit']['skipped']=1
        receipt['junit']['tests']+=1
        with self.assertRaisesRegex(ValueError,'nonempty successful native execution'):
            self.runtime._receipt(receipt,self.candidate())

    def test_wrong_scope_rejected_before_native_execution(self):
        key=self.runtime.admit(self.candidate())
        cap=self.machine.descriptor(key)
        wrong=self.forged(key,scope={**cap.scope,'authority_ceiling':{'external_effects':'ALL'}})
        with patch.object(verifier,'verify') as execute:
            with self.assertRaises(ValueError):self.runtime.execute(wrong)
            execute.assert_not_called()

    def test_false_constructor_dependencies_rejected(self):
        key=self.runtime.admit(self.candidate())
        wrong=self.forged(key,dependencies=())
        with self.assertRaises(ValueError):self.runtime._validated(wrong)

    def test_corrupted_candidate_cas_rejected(self):
        key=self.runtime.admit(self.candidate());cap=self.machine.descriptor(key)
        self.machine.objects[cap.program]+='corruption'
        with self.assertRaises(ValueError):self.runtime._validated(key)

    def test_forged_receipt_status_and_replayed_contract_rejected(self):
        key=self.runtime.admit(self.candidate());cap=self.machine.descriptor(key)
        verification=next(n for n in self.machine.log if n.id==cap.evidence[0])
        bundle=self.machine.get(verification.payload['receipt'])
        bundle['runs'][0]['contract_sha256']='0'*64
        wrong_evidence=self.machine.append(verification.kind,
            {**verification.payload,'receipt':self.machine.put(bundle)},verification.premises)
        forged=self.forged(key,evidence=(wrong_evidence,))
        with self.assertRaises(ValueError):self.runtime._validated(forged)

    def test_ancestor_withdrawal_blocks_native_then_fresh_restore_restarts(self):
        key=self.runtime.admit(self.candidate())
        unrelated=self.machine.append('unrelated_evidence',{'status':'independent'})
        self.runtime.withdraw(key)
        with patch.object(verifier,'verify') as execute:
            with self.assertRaises(PermissionError):self.runtime.execute(key)
            execute.assert_not_called()
        self.assertIn(unrelated,self.machine.live_ids(self.machine.log))
        new=self.runtime.restore(key)
        self.assertNotEqual(new,key)
        self.assertEqual(self.machine.descriptor(new).supersedes,key)
        self.assertGreater(self.machine.descriptor(new).generation,self.machine.descriptor(key).generation)
        reloaded=MemoryMachine();reloaded.log=copy.deepcopy(self.machine.log);reloaded.objects=copy.deepcopy(self.machine.objects)
        restart=self.nf.NativeFrontierRuntime(reloaded,self.contract,Path(self.tmp.name)/'restart')
        receipt,_=restart.execute(new)
        self.assertEqual(receipt['status'],'PASS_NATIVE')

    def test_unrelated_withdrawal_preserves_capability(self):
        key=self.runtime.admit(self.candidate())
        unrelated=self.machine.append('unrelated_evidence',{'independent':True})
        self.machine.append('revoke',{'target':unrelated,'reason':'control'})
        self.runtime._validated(key)

    def test_missing_source_rejected_before_native(self):
        bad={**self.contract,'repo_path':str(Path(self.tmp.name)/'missing')}
        with patch.object(verifier,'verify') as execute:
            with self.assertRaises((ValueError,FileNotFoundError)):
                self.nf.NativeFrontierRuntime(self.machine,bad,Path(self.tmp.name)/'other')
            execute.assert_not_called()

    def test_contract_mutation_cannot_expand_scope(self):
        self.runtime.contract['horizon_seconds']=8
        with self.assertRaises(ValueError):self.runtime.observe()

    def test_revoked_authority_blocks_before_native(self):
        self.machine.append('revoke',{'target':self.runtime.authority,'reason':'ceiling withdrawn'})
        with patch.object(verifier,'verify') as execute:
            with self.assertRaises(PermissionError):self.runtime.observe()
            execute.assert_not_called()

    def test_unknown_is_retained_without_a_capability(self):
        unknown={**self.contract,'protocol_binding':'2'*64}
        runtime=self.nf.NativeFrontierRuntime(self.machine,unknown,Path(self.tmp.name)/'unknown')
        # A dedicated original fixture with zero collected tests is an UNKNOWN observation.
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)/'empty';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'README').write_text('no tests\n')
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Fixture','-c',
                'user.email=fixture@example.invalid','commit','-qm','empty'],check=True)
            commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            contract={**self.contract,'repo_path':str(repo),'commit':commit,**verifier.source_identity(repo,commit)}
            runtime=self.nf.NativeFrontierRuntime(self.machine,contract,Path(self.tmp.name)/'zero')
            observed=runtime.observe()
            self.assertEqual(observed['status'],'UNKNOWN_NO_TEST_EXECUTION')
            with self.assertRaisesRegex(ValueError,'UNKNOWN_NO_TEST_EXECUTION'):runtime.admit(self.candidate())
            self.assertFalse(any(n.kind=='executable_capability' for n in self.machine.log))


if __name__=='__main__':unittest.main()
