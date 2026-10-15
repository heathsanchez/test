"""Typed V54 source adapter over the qualified Machine, its log and FLASH closure.

This module mediates its own local routes; it is not a non-bypassable sandbox.
Candidates, native warrants and the fixed local authority ceiling are distinct.
"""
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import subprocess
import time
import uuid

from .developmental_machine import Capability, canonical, digest
from .v54_source import OriginalV54, SOURCE_COMMIT, SOURCE_PATH, SOURCE_SHA256, WORLD_PINS
from .v54_verify import receipt_binding_valid, STAGES, TESTS, _NATIVE_RUNNER


@dataclass(frozen=True)
class SourceConstructor:
    source_commit: str
    cold_entrypoint: str = 'one_rewrite_discovery'
    warm_entrypoint: str = 'discover_after_O1'
    new_rewrite_horizon: int = 1
    status: str = 'SUPPLIED_ORIGINAL_CONSTRUCTOR'


class V54Runtime:
    def __init__(self,machine,session:OriginalV54,source_repo:Path,worlds:Path,native_python:Path):
        self.machine,self.session=machine,session
        self.source_repo,self.worlds=Path(source_repo).resolve(),Path(worlds).resolve()
        self.native_python=Path(native_python).absolute()
        self.authority_ceiling={'principal':'independent user research mission',
            'allowed_effects':'pinned local research worktrees and native tests',
            'external_effects':'NONE','reference_monitor':'UNKNOWN_NONBYPASSABILITY'}
        self.authority=machine.append('execution_authority_ceiling',self.authority_ceiling)
        self.source=machine.append('source_constructor',{'constructor':asdict(SourceConstructor(SOURCE_COMMIT)),
            'source_path':SOURCE_PATH,'source_sha256':SOURCE_SHA256,'world_pins':WORLD_PINS},(self.authority,))
        machine.flush()

    def _live(self,node_id):
        if node_id not in self.machine.mt.live_ids(self.machine.log) or node_id not in self.machine.flash_live_ids():
            raise PermissionError('causal support or local route authority withdrawn')

    def _world_scope(self,target=False):
        for name,variable in (('django','DJ'),('requests','RQ'),('rich','RH')):
            expected=self.worlds/name
            if self.session.world_paths[name]!=expected or Path(self.session.env[variable])!=expected:
                raise PermissionError('native world path differs from pinned local scope')
        if target:
            expected=self.worlds/'requests/src/requests/utils.py'
            actual=self.session.env.get('rq_path')
            if actual is None or Path(actual).absolute()!=expected or Path(actual).resolve()!=expected:
                raise PermissionError('native executable path differs from pinned local scope')

    def _native_evidence_valid(self,receipt,stage,program):
        if not receipt_binding_valid(receipt,stage,program):return False
        required={'learned_scope_matches','django_truncate_repaired','django_pagination_repaired',
                  'rich_scoped_preserved','rich_global_rejected','requests_cold_fails','requests_O1_residual_fails'}
        if STAGES[stage]=='final':required|={'requests_O1_O2_passes','requests_O1_ablation_fails'}
        gates=receipt.get('gates',{})
        pins=receipt.get('native_pins',{})
        if (receipt.get('protocol')!='UDM_V54_INDEPENDENT_NATIVE_VERIFICATION_V1' or
                receipt.get('source_commit')!=SOURCE_COMMIT or receipt.get('source_path')!=SOURCE_PATH or
                receipt.get('verifier_source_sha256')!=digest(Path(__file__).with_name('v54_verify.py').read_bytes()) or
                receipt.get('native_runner_sha256')!=digest(_NATIVE_RUNNER.encode()) or
                receipt.get('native_python')!=str(self.native_python) or
                receipt.get('evaluated') is not True or receipt.get('source_unchanged') is not True or
                set(gates)!=required or not all(value is True for value in gates.values()) or
                set(pins)!=set(WORLD_PINS) or any(pins[n].get('commit')!=pin for n,pin in WORLD_PINS.items())):
            return False
        native=receipt.get('native_receipts',[])
        if len(native)<(17 if STAGES[stage]=='final' else 15):return False
        for item in native:
            if (item.get('test') not in TESTS or item.get('original_command')!=TESTS[item['test']][2] or
                    item.get('imports_verified') is not True or item.get('source_unchanged') is not True or
                    item.get('import_count',0)<1):return False
        expected={'django_truncate:baseline':True,'django_pagination:baseline':True,
                  'rich_json:baseline':True,'requests_iter_slices:baseline':True,
                  'django_truncate:candidate_O1':True,'django_pagination:candidate_O1':True,
                  'rich:scoped_O1':True,'rich:deliberately_global_O1':False,
                  'requests:double_broken':False,'requests:O1_only':False}
        if STAGES[stage]=='final':expected.update({'requests:O1_then_O2':True,'requests:O1_ablated':False})
        by_label={item.get('label'):item for item in native}
        return all(label in by_label and by_label[label].get('passed') is passed for label,passed in expected.items())

    def _validated(self,node_id,*,target=True,seen=()):
        """Validate retained typed evidence and graph edges before a routed effect.

        The existing append-only state is the authority for admitted receipts.
        Their hashes bind persisted evidence; new admission always runs native tests.
        This check is not a signature scheme or a hostile-process security boundary.
        """
        if node_id in seen:
            raise ValueError('cyclic executable dependency')
        self._live(self.authority);self._live(self.source);self._live(node_id)
        self._world_scope(target=target)
        cap=self.machine.descriptor(node_id)
        expected_source={'repository':'heathsanchez/triskelion','commit':SOURCE_COMMIT,
                         'path':SOURCE_PATH,'sha256':SOURCE_SHA256}
        if cap.operation!='v54.token_rewrite' or cap.source!=expected_source:
            raise ValueError('wrong executable capability source or class')
        if cap.scope.get('world_pins')!=WORLD_PINS or cap.scope.get('authority_ceiling')!=self.authority_ceiling or cap.scope.get('authorization')!='LOCAL_RESEARCH_EXECUTION_ONLY':
            raise PermissionError('wrong native scope or independent authority ceiling')
        scope=cap.scope.get('target',{})
        if (set(scope)!=set(('world','relative_path','line_no','first_word')) or
                scope.get('world')!='requests' or scope.get('relative_path')!='src/requests/utils.py' or
                type(scope.get('line_no')) is not int or scope['line_no']<1 or scope.get('first_word')!='if'):
            raise ValueError('wrong pinned native target scope')
        if target and self.session.target_scope()!=scope:
            raise ValueError('wrong native capability scope')
        observation=self.machine.get(cap.observation)
        label=observation.get('label')
        acquisition=observation.get('acquisition_source',{})
        if (any(acquisition.get(key)!=value for key,value in {'commit':SOURCE_COMMIT,'path':SOURCE_PATH,'sha256':SOURCE_SHA256,'world_pins':WORLD_PINS}.items()) or
                cap.transition!='CAPABILITY_LANGUAGE_EXTENSION' or type(cap.generation) is not int or cap.generation<1):
            raise ValueError('retained source acquisition or transition provenance changed')
        if label not in ('O1','O2') or len(cap.evidence)!=1 or len(cap.dependencies)!=(1 if label=='O1' else 2):
            raise ValueError('incorrect constructor dependency shape')
        nodes={node.id:node for node in self.machine.log}
        for dependency in (*cap.dependencies,*cap.evidence):self._live(dependency)
        support=nodes[cap.dependencies[0]];verified=nodes[cap.evidence[0]]
        parent_ids=cap.dependencies[1:]
        program=self.machine.get(cap.program)
        if (support.kind!='source_support' or support.payload.get('operator')!=program or
                support.payload.get('label')!=label or support.payload.get('source_commit')!=SOURCE_COMMIT or
                support.payload.get('source_sha256')!=SOURCE_SHA256 or support.payload.get('generation')!=cap.generation or support.payload.get('supersedes')!=cap.supersedes or
                tuple(support.premises)!=(self.source,*parent_ids) or
                verified.kind!='independent_native_verification' or tuple(verified.premises)!=(support.id,) or
                tuple(nodes[node_id].premises)!=(support.id,verified.id,*parent_ids)):
            raise ValueError('capability descriptor differs from causal evidence graph')
        parents=[self._validated(parent,target=target,seen=(*seen,node_id)) for parent in parent_ids]
        if parents and parents[0][1]!='O1':
            raise ValueError('O2 requires exact warranted O1 parent')
        expected_program={'operators':[parent[2] for parent in parents]+[program],
                          'scope_word':scope['first_word']}
        persisted_program=self.machine.get(verified.payload['program'])
        receipt=self.machine.get(verified.payload['receipt'])
        if (persisted_program!=expected_program or
                not self._native_evidence_valid(receipt,'o1' if label=='O1' else 'o2',expected_program) or
                receipt.get('verifier_source_sha256')!=digest(Path(__file__).with_name('v54_verify.py').read_bytes()) or
                receipt.get('source_commit')!=SOURCE_COMMIT or receipt.get('source_path')!=SOURCE_PATH or
                not receipt.get('evaluated') or not receipt.get('gates') or not all(receipt['gates'].values())):
            raise ValueError('retained native evidence does not bind executable capability')
        witnessed_rows={int(item['label'].split(':')[2]) for item in receipt['native_receipts']
            if item.get('label','').startswith('requests_iter_slices:breaking_site:') and item.get('passed') is False}
        if witnessed_rows!={scope['line_no']}:
            raise ValueError('target row differs from independently verified source witness')
        return cap,label,program

    def independent_verify(self,program,stage):
        self._live(self.authority);self._live(self.source)
        self._world_scope()
        folder=self.machine.state/'v54-native';folder.mkdir(exist_ok=True)
        name=uuid.uuid4().hex
        input_file=folder/(name+'-program.json');receipt_file=folder/(name+'-receipt.json')
        input_file.write_text(canonical(program))
        started=time.perf_counter()
        subprocess.run([str(self.native_python),'-I','-B',str(Path(__file__).with_name('v54_verify.py')),
            '--source',str(self.source_repo),'--worlds',str(self.worlds),'--operators',str(input_file),
            '--stage',stage,'--out',str(receipt_file)],check=True,capture_output=True,timeout=240)
        receipt=json.loads(receipt_file.read_text())
        self.machine.costs.append({'phase':'v54_independent_verification','stage':stage,
            'seconds':time.perf_counter()-started,'status':receipt.get('status')})
        if not self._native_evidence_valid(receipt,stage,program):
            self.machine.append('native_rejection',{'stage':stage,'receipt':self.machine.put(receipt)})
            self.machine.flush()
            raise ValueError('independent native verification rejected executable program: '+str(receipt.get('reason')))
        return receipt

    def admit_operator(self,label,operator,parents=(),supersedes=None):
        self._live(self.authority);self._live(self.source)
        if label not in ('O1','O2') or not self.session._acquired or operator!=self.session.env.get(label):
            raise PermissionError('operator must come from original native acquisition/search')
        if (label=='O1' and parents) or (label=='O2' and len(parents)!=1):
            raise ValueError('incorrect constructor dependency shape')
        for parent in parents:
            self._live(parent)
            previous,parent_label,_=self._validated(parent)
            if parent_label!='O1':
                raise ValueError('O2 requires its exact live O1 capability')
        operators=([self.machine.get(self.machine.descriptor(parents[0]).program)] if parents else [])+[operator]
        program={'operators':operators,'scope_word':self.session.env['scope_word']}
        receipt=self.independent_verify(program,'o1' if label=='O1' else 'o2')
        self._live(self.authority);self._live(self.source)
        for parent in parents:self._validated(parent)
        generation=1+sum(n.kind=='executable_capability' and n.payload['operation']=='v54.token_rewrite'
            and self.machine.get(n.payload['observation'])['label']==label for n in self.machine.log)
        scope={'target':self.session.target_scope(),'world_pins':WORLD_PINS,
            'authority_ceiling':self.authority_ceiling,'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY'}
        support=self.machine.append('source_support',{'source_commit':SOURCE_COMMIT,'source_sha256':SOURCE_SHA256,
            'operator':operator,'label':label,'generation':generation,'supersedes':supersedes},(self.source,*parents))
        verified=self.machine.append('independent_native_verification',{'receipt':self.machine.put(receipt),
            'program':self.machine.put(program)},(support,))
        cap=Capability('v54.token_rewrite',{'repository':'heathsanchez/triskelion','commit':SOURCE_COMMIT,
            'path':SOURCE_PATH,'sha256':SOURCE_SHA256},scope,
            self.machine.put({'label':label,'acquisition_source':self.session.source_provenance}),
            self.machine.put(operator),generation,(support,*parents),(verified,),
            'CAPABILITY_LANGUAGE_EXTENSION',supersedes)
        capability_id=self.machine.append('executable_capability',asdict(cap),(support,verified,*parents))
        self.machine.flush()
        return capability_id

    def apply(self,capability_id,scope=None):
        cap,_,operator=self._validated(capability_id)
        expected=cap.scope['target']
        if scope is not None and scope!=expected:
            raise ValueError('wrong native capability scope')
        self._live(capability_id);self._live(self.authority);self._live(self.source)
        started=time.perf_counter()
        effect=self.session.apply_operator(operator,expected)
        self.machine.costs.append({'phase':'v54_operator_execution','seconds':time.perf_counter()-started})
        node=self.machine.append('native_operator_effect',{'effect':effect},(capability_id,))
        self.machine.flush()
        return effect,node

    def construct_next(self,ancestor=None):
        self._live(self.authority);self._live(self.source)
        self._world_scope(target=True)
        if ancestor is None:
            result=self.session.cold_search()
            node=self.machine.append('bounded_native_search',{'constructor':asdict(SourceConstructor(SOURCE_COMMIT)),
                'survivors':result,'status':'NO_SURVIVOR_WITHIN_ONE_NEW_REWRITE_HORIZON' if not result else 'CANDIDATE',
                'unrestricted_nonreachability':'UNKNOWN'},(self.source,))
        else:
            _,label,op=self._validated(ancestor)
            if label!='O1':raise ValueError('warm constructor requires O1')
            self._live(ancestor);self._live(self.source);self._live(self.authority)
            self.session.prepare_warm(op)
            self.apply(ancestor)
            self._live(ancestor);self._live(self.source);self._live(self.authority)
            result=self.session.warm_search()
            self._live(ancestor);self._live(self.source);self._live(self.authority)
            node=self.machine.append('bounded_native_search',{'constructor':asdict(SourceConstructor(SOURCE_COMMIT)),
                'result':result,'status':'CANDIDATE' if result['operator'] else 'UNKNOWN'},(self.source,ancestor))
        self.machine.flush()
        return result,node

    def native_consequence(self,operators,stage='final'):
        validated=[self._validated(node) for node in operators]
        if [item[1] for item in validated]!=['O1','O2'] or validated[1][0].dependencies[1:]!=(operators[0],):
            raise ValueError('native consequence requires exact O1 to O2 dependency chain')
        program={'operators':[self.machine.get(self.machine.descriptor(n).program) for n in operators],
                 'scope_word':self.session.env['scope_word']}
        receipt=self.independent_verify(program,stage)
        for node in operators:self._validated(node)
        result=self.machine.append('verified_consequence',{'scope':'V54 native source-distinct future',
            'receipt':self.machine.put(receipt),'program':self.machine.put(program)},tuple(operators))
        self.machine.flush()
        return result,receipt

    def restore_session(self,operators):
        """Reload executable data from warranted state; do not rerun acquisition."""
        validated=[self._validated(node,target=False) for node in operators]
        if [item[1] for item in validated]!=['O1','O2'] or validated[1][0].dependencies[1:]!=(operators[0],):
            raise ValueError('restoration requires exact O1 to O2 dependency chain')
        if validated[0][0].scope!=validated[1][0].scope:
            raise ValueError('restored operators have different scopes')
        for cap,label,program in validated:
            self.session.env[label]=program
            self.session.env['scope_word']=cap.scope['target']['first_word']
        for node in operators:self._live(node)
        self._live(self.authority);self._live(self.source)
        self.session._acquired=True
        self.session.prepare_target()
        for node in operators:self._validated(node)
