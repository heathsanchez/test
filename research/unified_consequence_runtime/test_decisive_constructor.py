"""Exact V104 constructor interface fixtures; no prospective source tasks."""
import copy
from dataclasses import asdict, replace
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import decisive_native_verify as verifier
from .decisive_native_frontier import NativeFrontierRuntime
from .test_native_frontier import MemoryMachine

_CONTEXTS={}
def fixture_checker(machine,context_id):
    return machine.get(context_id)
def wrong_checker_same_file(machine,context_id):
    return machine.get(context_id)

class DecisiveConstructorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from . import decisive_constructor as constructor
        from .qualify_decisive_native import native_probe
        cls.constructor=constructor;cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name);cls.source=Path(os.environ.get('UDM_SOURCE_REPOS','/workspace/repos'))/'triskelion'
        cls.machine=MemoryMachine();cls.supports=[]
        environment=verifier.fingerprint(verifier.environment_identity(sys.executable))
        for number in (1,2):
            repo=cls.root/('repo'+str(number));repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            name='answer_'+str(number);before='def '+name+'():\n return 0\n'
            (repo/'subject.py').write_text(before)
            (repo/'test_subject.py').write_text('from subject import '+name+'\ndef test_value(): assert '+name+'() == 1\n')
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Constructor Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
            commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            contract={'schema':verifier.SCHEMA,'repository':'fixture/constructor-'+str(number),'repo_path':str(repo),
                'commit':commit,**verifier.source_identity(repo,commit),'interpreter':sys.executable,
                'environment_sha256':environment,'protocol_binding':'b'*64,'horizon_seconds':7}
            runtime=NativeFrontierRuntime(cls.machine,contract,cls.root/('native'+str(number)))
            baseline=native_probe(cls.machine,runtime,{'replacements':[]},'fixture-baseline')
            programs=constructor.generate_candidates(cls.source,before,allowed=None,cap=320)
            row=next((sel,builder,text) for sel,builder,text in programs if sel==('Return','value') and repr(builder)=="('CONST', 1)")
            candidate={'replacements':[{'path':'subject.py','original_sha256':verifier.sha256(before.encode()),'replacement':row[2]}]}
            probe=native_probe(cls.machine,runtime,candidate,'fixture-generated-candidate')
            if probe['receipt']['status']!='PASS_NATIVE':raise AssertionError('fixture native witness failed')
            catalog=[{'id':verifier.fingerprint(candidate),'candidate':candidate,'selector':row[0],'builder':row[1],'path':'subject.py'}]
            context={'contract':contract,'baseline_record':baseline['record'],'catalog':catalog,
                'catalog_spec':{'cap':320,'production_paths':['subject.py'],'triskelion':str(cls.source)}}
            context_id=cls.machine.put(context)
            cls.supports.append({'context':context_id,'record':probe['record'],'signature':[list(row[0]),list(row[1])],'evidence':probe['evidence']})
        cls.log=copy.deepcopy(cls.machine.log);cls.objects=copy.deepcopy(cls.machine.objects)
    def setUp(self):
        self.machine=MemoryMachine();self.machine.log=copy.deepcopy(self.log);self.machine.objects=copy.deepcopy(self.objects)
    def retain(self,supports=None,**kwargs):
        return self.constructor.retain_constructor(self.machine,supports or self.supports,protocol_binding='b'*64,
            source_repo=self.source,independent_check=fixture_checker,**kwargs)
    def invoke(self,key,**kwargs):
        return self.constructor.invoke_constructor(self.machine,key,protocol_binding='b'*64,
            source_repo=self.source,independent_check=fixture_checker,**kwargs)
    def test_actual_two_source_native_support_retains_executable_original_program(self):
        retained=self.retain();self.assertEqual(retained['status'],'WARRANTED_BOUNDED_CONSTRUCTOR')
        key=retained['constructor_id'];cap=self.machine.descriptor(key)
        self.assertEqual(cap.operation,'v104.ast_constructor')
        self.assertEqual(cap.transition,'CONSTRUCTOR_ACQUISITION')
        loaded=self.invoke(key);self.assertEqual(loaded['signatures'],retained['signatures'])
        self.assertEqual(loaded['null_signatures'],retained['null_signatures'])
        programs=self.constructor.generate_candidates(self.source,'def future(x):\n return x\n',allowed=loaded['signatures'],cap=2)
        self.assertTrue(programs)
        self.assertTrue(all(sel==('Return','value') for sel,builder,text in programs))
        self.assertTrue(all('return 1' in text or 'return True' in text for sel,builder,text in programs))
    def test_single_source_and_duplicated_source_support_remain_unknown(self):
        for supports in ([self.supports[0]],[self.supports[0],self.supports[0]]):
            result=self.retain(supports);self.assertTrue(result['status'].startswith('UNKNOWN'))
            self.assertFalse(any(n.kind=='executable_capability' and n.payload.get('operation')=='v104.ast_constructor' for n in self.machine.log))
    def test_wrong_signature_source_protocol_and_boolean_checker_rejected(self):
        wrong=copy.deepcopy(self.supports);wrong[0]['signature']=[['If','test'],['CONST',1]]
        self.assertTrue(self.retain(wrong)['status'].startswith('UNKNOWN'))
        result=self.constructor.retain_constructor(self.machine,self.supports,protocol_binding='f'*64,
            source_repo=self.source,independent_check=fixture_checker)
        self.assertTrue(result['status'].startswith('UNKNOWN'))
        result=self.constructor.retain_constructor(self.machine,self.supports,protocol_binding='b'*64,
            source_repo=self.source,independent_check=lambda *_:True)
        self.assertTrue(result['status'].startswith('UNKNOWN'))
    def test_dead_native_support_and_wrong_evidence_lineage_refused(self):
        wrong=copy.deepcopy(self.supports);wrong[0]['evidence']=self.supports[1]['evidence']
        self.assertTrue(self.retain(wrong)['status'].startswith('UNKNOWN'))
        self.machine.append('revoke',{'target':self.supports[0]['evidence'],'reason':'fixture ancestor withdrawal'})
        self.assertTrue(self.retain()['status'].startswith('UNKNOWN'))
    def test_false_source_distinctness_and_native_receipt_forgery_refused(self):
        wrong=copy.deepcopy(self.supports)
        original=self.machine.get(wrong[1]['context']);original['contract']['repository']='fixture/constructor-1'
        wrong[1]['context']=self.machine.put(original)
        self.assertTrue(self.retain(wrong)['status'].startswith('UNKNOWN'))
        forged=self.machine.get(self.supports[0]['record']);forged['receipt']['junit']['passed']=999
        wrong=copy.deepcopy(self.supports);wrong[0]['record']=self.machine.put(forged)
        self.assertTrue(self.retain(wrong)['status'].startswith('UNKNOWN'))
    def test_physical_removal_revocation_unrelated_preservation_and_reload(self):
        retained=self.retain();key=retained['constructor_id'];cap=self.machine.descriptor(key)
        unrelated=self.machine.append('unrelated_support',{'fixture':True})
        raw=self.machine.objects.pop(cap.program)
        with self.assertRaises((ValueError,KeyError)):self.invoke(key)
        self.assertEqual(self.machine.costs[-1]['phase'],'original_v104_constructor_invocation')
        self.machine.objects[cap.program]=raw
        clone=MemoryMachine();clone.log=copy.deepcopy(self.machine.log);clone.objects=copy.deepcopy(self.machine.objects)
        loaded=self.constructor.invoke_constructor(clone,key,protocol_binding='b'*64,source_repo=self.source,independent_check=fixture_checker)
        self.assertEqual(loaded['signatures'],retained['signatures'])
        self.machine.append('revoke',{'target':cap.dependencies[0],'reason':'exact constructor source support'})
        with self.assertRaises(PermissionError):self.invoke(key)
        self.assertIn(unrelated,self.machine.live_ids(self.machine.log))
        self.assertTrue(self.retain(supersedes=key)['status'].startswith('UNKNOWN'))
    def test_forged_scope_checker_and_downgraded_assertion_authority_refused(self):
        retained=self.retain();key=retained['constructor_id'];cap=self.machine.descriptor(key)
        node=next(node for node in self.machine.log if node.id==key)
        for scope in ({**cap.scope,'authority_ceiling':{'external_effects':'ALL'}},
                      {**cap.scope,'input_type':'ArbitraryExternalAction'}):
            forged=self.machine.append('executable_capability',asdict(replace(cap,scope=scope)),node.premises)
            with self.assertRaises(ValueError):self.invoke(forged)
        with self.assertRaises(ValueError):
            self.constructor.invoke_constructor(self.machine,key,protocol_binding='b'*64,
                source_repo=self.source,independent_check=wrong_checker_same_file)
        wrong=copy.deepcopy(self.supports)
        context=self.machine.get(wrong[0]['context']);context['native_suite_authority']={'fixture':'cannot downgrade'}
        wrong[0]['context']=self.machine.put(context)
        self.assertTrue(self.retain(wrong)['status'].startswith('UNKNOWN'))
    def test_restoration_requires_and_accepts_fresh_native_two_source_lineage(self):
        from .qualify_decisive_native import native_probe
        retained=self.retain();key=retained['constructor_id'];old=self.machine.descriptor(key)
        self.machine.append('revoke',{'target':old.dependencies[0],'reason':'fresh qualification fixture'})
        self.assertTrue(self.retain(supersedes=key)['status'].startswith('UNKNOWN'))
        fresh=[]
        for index,support in enumerate(self.supports):
            context=self.machine.get(support['context']);record=self.machine.get(support['record'])
            runtime=NativeFrontierRuntime(self.machine,context['contract'],self.root/('fresh-native-'+str(index)))
            probe=native_probe(self.machine,runtime,record['candidate'],'fresh constructor restoration fixture')
            fresh.append({**support,'record':probe['record'],'evidence':probe['evidence']})
        restored=self.retain(fresh,supersedes=key)
        self.assertEqual(restored['status'],'WARRANTED_BOUNDED_CONSTRUCTOR')
        self.assertNotEqual(restored['constructor_id'],key)
        cap=self.machine.descriptor(restored['constructor_id'])
        self.assertEqual(cap.supersedes,key)
        self.assertGreater(cap.generation,old.generation)
        self.assertEqual(self.invoke(restored['constructor_id'])['signatures'],restored['signatures'])
    def test_original_retention_and_null_rule_matches_exact_source_statements(self):
        supported={repr((('Return','value'),('CONST',1))):('a','b')}
        selected=self.constructor.original_retention(self.source,[((('Return','value'),('CONST',1)),'a'),((('Return','value'),('CONST',1)),'b')])
        self.assertEqual(selected['signatures'],[[['Return','value'],['CONST',1]]])
        self.assertEqual(len(selected['null_signatures']),1)
        self.assertEqual(self.constructor.original_retention(self.source,[((('Return','value'),('CONST',1)),'a')])['signatures'],[])

if __name__=='__main__':unittest.main()
