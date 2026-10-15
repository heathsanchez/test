"""Adversarial adapter contracts; native subjects are qualified by the workflow."""
from dataclasses import asdict
import hashlib
import json
import os
import py_compile
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.unified_consequence_runtime import native_constructor as nc
from research.unified_consequence_runtime.developmental_machine import Capability


class Node:
    def __init__(self, kind, payload, premises=()):
        self.kind, self.payload, self.premises = kind, payload, tuple(premises)
        self.id = nc.digest(nc.canonical({'kind': kind, 'payload': payload, 'premises': premises}).encode())


class MemoryMachine:
    """Only support bookkeeping is substituted; no native acceptance is mocked."""
    def __init__(self):
        self.log, self.objects, self.costs = [], {}, []
        self.mt = self
    def append(self, kind, payload, premises=()):
        node=Node(kind,payload,premises);self.log.append(node);return node.id
    def live_ids(self, log):
        dead={n.payload['target'] for n in log if n.kind=='revoke'}
        changed=True
        while changed:
            old=set(dead)
            dead.update(n.id for n in log if any(p in dead for p in n.premises))
            changed=old!=dead
        return {n.id for n in log if n.id not in dead}
    def flash_live_ids(self):return self.live_ids(self.log)
    def flush(self):pass
    def put(self, value):
        key=nc.digest(nc.canonical(value).encode());self.objects[key]=json.loads(nc.canonical(value));return key
    def get(self, key):return self.objects[key]
    def descriptor(self, key):
        raw=dict(next(n.payload for n in self.log if n.id==key));raw['dependencies']=tuple(raw['dependencies']);raw['evidence']=tuple(raw['evidence']);return Capability(**raw)


class NativeConstructorContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.machine=MemoryMachine()
        self.runtime=object.__new__(nc.NativeConstructorRuntime)
        self.runtime.machine=self.machine
        self.runtime.worlds=self.root/'worlds';self.runtime.worlds.mkdir()
        self.runtime.output=self.root/'output';self.runtime.output.mkdir()
        self.runtime.sources=self.runtime.output/'source';self.runtime.sources.mkdir()
        self.runtime.authority=self.machine.append('execution_authority_ceiling',nc.AUTHORITY)
        self.runtime.source=self.machine.append('source_constructor',{'source':nc.SOURCE},(self.runtime.authority,))

    def test_unknown_frontier_refuses_before_discovery(self):
        with patch.object(self.runtime,'_call') as call:
            with self.assertRaisesRegex(ValueError,'UNKNOWN_SCOPE'):
                self.runtime.observe('unfamiliar-source')
            call.assert_not_called()

    def test_withdrawn_authority_refuses_before_original_code(self):
        self.machine.append('revoke',{'target':self.runtime.authority})
        with patch.object(nc,'_load_sources') as load:
            with self.assertRaises(PermissionError):self.runtime._scope('cachetools')
            load.assert_not_called()

    def test_redirected_world_root_refuses_before_original_code(self):
        self.runtime.worlds.rmdir()
        elsewhere=self.root/'elsewhere';elsewhere.mkdir()
        self.runtime.worlds.symlink_to(elsewhere,target_is_directory=True)
        with patch.object(nc,'_load_sources') as load:
            with self.assertRaises(PermissionError):self.runtime._scope('cachetools')
            load.assert_not_called()

    def test_changed_original_source_rejected_before_execution(self):
        folder=self.root/'altered';folder.mkdir()
        for name in nc.SOURCE_FILES:(folder/name).write_text('altered')
        with patch.object(nc,'ModuleType') as load:
            with self.assertRaisesRegex(ValueError,'source changed'):nc._load_sources(folder)
            load.assert_not_called()

    def test_no_external_authority_in_scope(self):
        self.assertEqual(nc.AUTHORITY['external_effects'],'NONE')
        self.assertEqual(nc.AUTHORITY['reference_monitor'],'UNKNOWN_NONBYPASSABILITY')
        self.assertEqual(nc.FRONTIER_PROFILES['cachetools'],
            ['cachetools:protected-observer','cachetools:inherited-suite'])
        self.assertFalse(set(nc.FRONTIER_PROFILES['cachetools']) & set(nc.FRONTIER_PROFILES['boltons']))

    def test_wrong_constructor_dependency_rejected(self):
        observation=self.machine.append('native_observation',{},(self.runtime.source,))
        cap=Capability('native.source_patch',nc.SOURCE,{'target':'cachetools'},'x','y',1,(observation,),(), 'CAPABILITY_LANGUAGE_EXTENSION')
        key=self.machine.append('executable_capability',asdict(cap),(observation,))
        with patch.object(self.runtime,'_scope'):
            with self.assertRaisesRegex(ValueError,'scope|dependencies'):
                self.runtime._validated(key)

    def test_revoked_authority_blocks_prepare_before_fetch_or_write(self):
        self.runtime.worlds.rmdir()
        self.machine.append('revoke',{'target':self.runtime.authority})
        with patch.object(self.runtime,'_call') as call:
            with self.assertRaises(PermissionError):self.runtime.prepare()
            call.assert_not_called()
        self.assertFalse(self.runtime.worlds.exists())

    def test_authenticated_source_ignores_valid_stale_bytecode(self):
        folder=self.root/'cached-source';folder.mkdir()
        hashes={}
        for name in ('observer_genesis.py','repair_compiler.py'):
            path=folder/name;path.write_text('VALUE=9\n');py_compile.compile(str(path),doraise=True)
            stamp=path.stat();path.write_text('VALUE=1\n');os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
            hashes[name]=nc.digest(path.read_bytes())
        with patch.dict(nc.SOURCE_FILES,hashes,clear=True):
            modules=nc._load_sources(folder)
        self.assertEqual([m.VALUE for m in modules],[1,1])

    def test_untracked_import_interference_blocks_scope(self):
        folder=self.runtime.worlds/'cachetools'
        for key in ('original','base','head'):(folder/key).mkdir(parents=True)
        def git(root,*args):
            if args==('rev-parse','HEAD'):
                return nc.TARGETS['cachetools'][Path(root).name].encode()+b'\n'
            if '--others' in args:return b'injected.py\0'
            return b''
        with patch.object(nc,'_load_sources'),patch.object(nc,'_git',side_effect=git):
            with self.assertRaisesRegex(ValueError,'untracked|import'):
                self.runtime._scope('cachetools')

    def test_git_replacement_cannot_change_pinned_source_bytes(self):
        repo=self.root/'replacement-repo';repo.mkdir()
        def git(*args):
            return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE)
        git('init','-q')
        file=repo/'source.py'
        file.write_text('VALUE=1\n');git('add','source.py')
        git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original')
        original=git('rev-parse','HEAD').decode().strip()
        file.write_text('VALUE=9\n');git('add','source.py')
        git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','replacement')
        other=git('rev-parse','HEAD').decode().strip();git('replace',original,other)
        self.assertEqual(git('show',original+':source.py'),b'VALUE=9\n')
        self.assertEqual(nc._git(repo,'show',original+':source.py'),b'VALUE=1\n')

    def test_wrong_subject_projection_refuses_before_publication(self):
        name='cachetools'
        scope={'target':name,'target_pins':nc.TARGETS[name],'authority_ceiling':nc.AUTHORITY,
               'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY',
               'frontier_contract':nc.FRONTIER_CONTRACT,'frontier_profiles':nc.FRONTIER_PROFILES['boltons']}
        cap=Capability('native.source_patch',nc.SOURCE,scope,'x','y',1,(),(), 'CAPABILITY_LANGUAGE_EXTENSION')
        key=self.machine.append('executable_capability',asdict(cap))
        with patch.object(self.runtime,'_scope'):
            with self.assertRaisesRegex(ValueError,'scope'):
                self.runtime.projection_payload(key)

    def test_record_reuse_does_not_restore_revoked_support(self):
        payload={'family':'test-only'}
        first=self.runtime._record_once('source_constructor',payload)
        self.machine.append('revoke',{'target':first})
        self.assertEqual(self.runtime._record_once('source_constructor',payload),first)
        with self.assertRaises(PermissionError):self.runtime._live(first)

    def retained_capability(self, name='cachetools', generation=1, wrong_scope=False):
        scope={'target':name,'target_pins':dict(nc.TARGETS[name]),'authority_ceiling':nc.AUTHORITY,
               'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY',
               'frontier_contract':nc.FRONTIER_CONTRACT,'frontier_profiles':nc.FRONTIER_PROFILES[name]}
        if wrong_scope:scope['target_pins']['base']='0'*40
        cap=Capability('native.source_patch',nc.SOURCE,scope,'observation','program',generation,(),(),
                       'CAPABILITY_LANGUAGE_EXTENSION')
        key=self.machine.append('executable_capability',asdict(cap))
        return key,cap

    def test_repeated_acquisition_activates_existing_without_construction(self):
        key,cap=self.retained_capability()
        with patch.object(self.runtime,'_scope'),patch.object(self.runtime,'_validated',return_value=(cap,{},{})),\
                patch.object(self.runtime,'observe') as observe,patch.object(self.runtime,'_call') as call:
            self.assertEqual(self.runtime.acquire('cachetools'),key)
            observe.assert_not_called();call.assert_not_called()
        activation=self.machine.log[-1]
        self.assertEqual(activation.payload['transition'],'ACTIVATION')
        self.assertEqual(activation.payload['capability_id'],key)
        self.assertIn(key,activation.premises)

    def test_wrong_scope_existing_capability_is_not_activated(self):
        self.retained_capability(wrong_scope=True)
        with patch.object(self.runtime,'_scope'),patch.object(self.runtime,'_validated') as validated,\
                patch.object(self.runtime,'observe',return_value={'status':'UNKNOWN_OBSERVATION'}):
            with self.assertRaisesRegex(ValueError,'UNKNOWN_OBSERVATION'):
                self.runtime.acquire('cachetools')
            validated.assert_not_called()
        self.assertFalse(any(n.kind=='capability_activation' for n in self.machine.log))

    def test_multiple_lawful_existing_capabilities_preserve_unknown_choice(self):
        first,cap1=self.retained_capability(generation=1)
        second,cap2=self.retained_capability(generation=2)
        by_id={first:cap1,second:cap2}
        with patch.object(self.runtime,'_scope'),\
                patch.object(self.runtime,'_validated',side_effect=lambda key:(by_id[key],{},{})),\
                patch.object(self.runtime,'observe') as observe,patch.object(self.runtime,'_call') as call:
            with self.assertRaisesRegex(ValueError,'UNKNOWN_CHOICE'):
                self.runtime.acquire('cachetools')
            observe.assert_not_called();call.assert_not_called()
        choice=self.machine.log[-1]
        self.assertEqual(choice.payload['status'],'UNKNOWN_CHOICE')
        self.assertEqual(set(choice.payload['candidates']),{first,second})
        self.assertTrue({first,second}<=self.machine.live_ids(self.machine.log))

    def test_explicit_restoration_does_not_reuse_existing_generation(self):
        self.retained_capability()
        with patch.object(self.runtime,'_scope'),patch.object(self.runtime,'_validated') as validated,\
                patch.object(self.runtime,'observe',return_value={'status':'UNKNOWN_OBSERVATION'}) as observe:
            with self.assertRaisesRegex(ValueError,'UNKNOWN_OBSERVATION'):
                self.runtime.acquire('cachetools',supersedes='old-revoked-generation')
            observe.assert_called_once_with('cachetools');validated.assert_not_called()

    def test_bytecode_removal_does_not_touch_source(self):
        folder=self.root/'fixture';folder.mkdir();(folder/'x.py').write_text('source')
        cache=folder/'__pycache__';cache.mkdir();(cache/'x.pyc').write_bytes(b'stale')
        nc._purge_bytecode(folder)
        self.assertFalse(cache.exists());self.assertEqual((folder/'x.py').read_text(),'source')


if __name__=='__main__':unittest.main()
