"""Bounded sustained native repair pilot: existing V100 base + original Refactory Tester.

No replacement learning architecture or reference-code solver. Native test maps
are empirical evidence inside the frozen source/test/runtime boundary only.
"""
from __future__ import annotations
import ast,copy
from collections import defaultdict
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import platform
import sysconfig
import tempfile
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
WORK=REPO.parent
sys.path.insert(0,str(REPO))
PROTOCOL_SHA='347baa0a3b84997f77475ecf2bcde20a031f6b097768f3826c1869bf45bbe865'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def write(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def protocol():
    raw=(HERE/'protocol_v3.json').read_bytes()
    if sha(raw)!=PROTOCOL_SHA:raise ValueError('frozen protocol changed')
    return json.loads(raw)
class ExistingBaseGrammar:
    def _source(self,root):
        namespace={'ast':ast,'copy':copy}
        def load(path):return subprocess.check_output(['git','-C',str(root),'show','426c54f7c774560e0fabe7213c5ef333b1327c71:'+path])
        path='experiments/METALOGIC_V98_RICH_K_PROTECTED_DYNAMIC_RANKING.py';tree=ast.parse(load(path))
        defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rich_candidates' or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'CMP','BIN','BOOL'} for t in n.targets)]
        exec(compile(ast.Module(body=defs,type_ignores=[]),path,'exec'),namespace)
        rich=namespace['rich_candidates'];namespace['ORIGINAL_RICH']=rich
        path='experiments/METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py'
        defs=[n for n in ast.parse(load(path)).body if isinstance(n,ast.FunctionDef) and n.name=='balanced_rich_candidates']
        exec(compile(ast.Module(body=defs,type_ignores=[]),path,'exec'),namespace)
        return namespace,rich
    def generate_candidates(self,root,source,allowed=None,cap=32):
        namespace,rich=self._source(root)
        if allowed is not None:
            kinds={sig[0][1] for sig in allowed}
            namespace['ORIGINAL_RICH']=lambda src,n:[row for row in rich(src,n) if row[0] in kinds]
        return [(('V100_FAMILY',kind),('UNCHANGED_BASE',),text) for kind,text in namespace['balanced_rich_candidates'](source,cap)]
    def original_retention(self,root,pairs):
        from research.unified_consequence_runtime import decisive_constructor as old
        namespace,statements=old._original(root);support=defaultdict(set)
        for sig,source in pairs:support[(tuple(sig[0]),tuple(sig[1]))].add(source)
        namespace['support']=support
        namespace['SELECTORS']=[('V100_FAMILY',kind) for kind in protocol()['operator_menu']]
        namespace['BUILDERS']=[('UNCHANGED_BASE',)]
        exec(compile(ast.Module(body=statements,type_ignores=[]),'original-V104-retention-rebound-to-existing-base-families','exec'),namespace)
        return {'signatures':[[list(s),list(b)] for s,b in namespace['retained']]}

def generator():
    return ExistingBaseGrammar(),Path(os.environ.get('UDM_V104_SOURCE',str(WORK/'components/triskelion')))

def candidates(source,signatures,arm):
    original,root=generator();base=original.generate_candidates(root,source,cap=32)
    if arm=='A' or not signatures:return base
    retained=original.generate_candidates(root,source,allowed=signatures,cap=16)
    result=[];seen=set()
    for row in retained+base:
        key=sha(row[2].encode())
        if key not in seen:seen.add(key);result.append(row)
        if len(result)==32:break
    return result

def classify(result,ids):
    if (not ids or not isinstance(result,dict) or set(result)!=set(ids)
            or any(type(v) is not bool for v in result.values())):
        return {'status':'UNKNOWN_INCOMPLETE_NATIVE_TESTS','passed':0,'tests':len(ids),'cases':{}}
    return {'status':'PASS_NATIVE' if all(result.values()) else 'FAIL_NATIVE',
            'passed':sum(result.values()),'tests':len(ids),'cases':result}

def support_pairs(rows):
    pairs=[]
    for row in rows:
        if row.get('split')!='train':raise ValueError('evaluation cannot enter training memory')
        for sig in row.get('improvements',[]):pairs.append((sig,row['source']))
    return pairs

def selected(rows):
    original,root=generator()
    return original.original_retention(root,support_pairs(rows))['signatures']

def arm_order(i):
    return 'ABCD'[i%4:]+'ABCD'[:i%4]

def tree_hash(root):
    root=Path(root)
    return sha(canonical({str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}).encode())

def context(external,question):
    external=Path(external);question=Path(question)
    files=subprocess.check_output(['git','-C',str(external),'ls-files','-z']).decode().split('\0')
    source=sha(canonical({n:sha((external/n).read_bytes()) for n in files if n and n.endswith('.py')}).encode())
    return {'protocol':PROTOCOL_SHA,'verifier_tree':source,'tests':tree_hash(question),
            'runner':sha(Path(__file__).read_bytes()),'python_executable':sha(Path(sys.executable).read_bytes()),
            'python_version':platform.python_version(),'environment':sha((WORK/'qualification/refactory_environment.txt').read_bytes())}

def check_reply(value,code_hash,binding):
    if not isinstance(value,dict) or value.get('candidate_sha256')!=code_hash or value.get('binding')!=binding:
        raise ValueError('oracle source/verifier/protocol binding differs')
    ids=list(value.get('cases',{}))
    checked=classify(value.get('cases'),ids)
    if value.get('status')!=checked['status'] or value.get('passed')!=checked['passed'] or value.get('tests')!=checked['tests']:
        raise ValueError('oracle case map/status/count disagrees')
    return value

def read_source(path):
    return Path(path).read_bytes().decode('utf-8')

def oracle(request):
    """Separate process. Only original external Tester supplies truth values."""
    sys.path.insert(0,request['external_repo'])
    from basic_framework.core_testing import Tester
    t=time.perf_counter();before=context(request['external_repo'],request['question_dir'])
    if before!=request['binding']:raise ValueError('oracle pre-source drift')
    tester=Tester(request['question_dir']);ids=tester.get_tc_id_list()
    code=read_source(request['candidate_file'])
    result=tester.tv_code(code,timeout=0.10)
    value=classify(result,ids)
    after=context(request['external_repo'],request['question_dir'])
    if before!=after:raise ValueError('oracle source changed during native verification')
    value.update(candidate_sha256=sha(code.encode()),elapsed_seconds=time.perf_counter()-t,binding=after,
                 verifier_source_sha256=sha(Path(sys.modules[Tester.__module__].__file__).read_bytes()))
    print('UDM_ORACLE_RESULT='+canonical(value))

class Native:
    def __init__(self,out,external,archive):
        self.out=Path(out);self.external=Path(external);self.archive=archive
        self.calls=[];self.domain=self.out/'domain';self.number=0;self.arm_calls={a:0 for a in 'ABCD'};self.contexts={}
    def materialize(self,question):
        prefix='data/'+question+'/'
        for name in self.archive.namelist():
            if not name.startswith(prefix):continue
            rel=name[len('data/'):]
            if ('/ans/' in name or name.endswith('/code/global.py') or name.endswith('/code/global_append.py')) and not name.endswith('/'):
                dest=self.domain/rel;dest.parent.mkdir(parents=True,exist_ok=True)
                raw=self.archive.read(name)
                if dest.exists() and dest.read_bytes()!=raw:raise ValueError('native domain drift')
                dest.write_bytes(raw)
        return self.domain/question
    def verify(self,source,question,label):
        self.number+=1
        if self.number>9700:raise RuntimeError('frozen native call budget exhausted')
        arm=label[0] if label and label[0] in 'ABCD' else None
        if arm:
            self.arm_calls[arm]+=1
            if self.arm_calls[arm]>2400:raise RuntimeError('matched arm native call budget exhausted')
        folder=self.out/'native'/f'{self.number:05d}'
        folder.mkdir(parents=True)
        program=folder/'candidate.py';program.write_text(source)
        question_dir=self.materialize(question)
        binding=context(self.external,question_dir)
        if question in self.contexts and binding!=self.contexts[question]:raise ValueError('native context drift')
        self.contexts[question]=binding
        request={'external_repo':str(self.external),'question_dir':str(question_dir),'binding':binding,
                 'candidate_file':str(program),'label':label}
        write(folder/'request.json',request)
        before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.perf_counter()
        try:
            run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--oracle',str(folder/'request.json')],
                capture_output=True,text=True,timeout=8,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            stdout,stderr,exit=run.stdout,run.stderr,run.returncode
            (folder/'stdout.log').write_text(stdout);(folder/'stderr.log').write_text(stderr)
            markers=[line[len('UDM_ORACLE_RESULT='):] for line in stdout.splitlines() if line.startswith('UDM_ORACLE_RESULT=')]
            value=check_reply(json.loads(markers[0]),sha(source.encode()),binding) if exit==0 and len(markers)==1 else {'status':'UNKNOWN_ORACLE_EXECUTION','passed':0,'tests':0,'cases':{}}
            if context(self.external,question_dir)!=binding:raise ValueError('native post-source drift')
        except subprocess.TimeoutExpired as e:
            stdout=(e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else (e.stdout or '')
            stderr='UNKNOWN_ORACLE_PROCESS_TIMEOUT';exit=124
            value={'status':'UNKNOWN_ORACLE_PROCESS_TIMEOUT','passed':0,'tests':0,'cases':{}}
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        (folder/'stdout.log').write_text(stdout);(folder/'stderr.log').write_text(stderr)
        value.update(source_sha256=sha(source.encode()),label=label,call=self.number,process_exit=exit,
          process_wall_seconds=time.perf_counter()-start,cpu_user_seconds=after.ru_utime-before.ru_utime,
          cpu_system_seconds=after.ru_stime-before.ru_stime)
        write(folder/'receipt.json',value);self.calls.append(value)
        return value

class Graph:
    """Thin native profile over the existing Machine and its original causal log."""
    def __init__(self,root):
        from research.unified_consequence_runtime.developmental_machine import Machine
        self.root=Path(root);self.machine=Machine(WORK/'components',self.root,WORK/'unused-evaluator',WORK/'unused-config')
        self.rows=[];self.supports={};self.current=[]
        self.unrelated=self.machine.append('irrelevant_control',{'protocol':PROTOCOL_SHA})
        self.machine.flush()
    def add(self,row,native):
        if row['split']!='train':raise ValueError('evaluation cannot enter graph')
        if row.get('source') not in protocol()['train']:raise ValueError('unfrozen graph training source')
        with zipfile.ZipFile(WORK/'refactory_data_sealed.zip') as archive:original=archive.read(row['source']).decode()
        if sha(original.encode())!=row['source_sha256']:raise ValueError('changed graph training source')
        baseline=native.verify(original,row['question'],'D-source-baseline-requalification')
        if baseline['cases']!=row['baseline']['cases'] or baseline['status']!=row['baseline']['status']:
            raise ValueError('forged graph improvement baseline')
        source_node=self.machine.append('source_artifact',{'source':row['source'],'sha256':row['source_sha256'],'protocol':PROTOCOL_SHA,'generation':1+sum(n.kind=='source_artifact' and n.payload.get('source')==row['source'] for n in self.machine.log)})
        seen=set()
        for item in row['witnesses']:
            key=canonical(item['signature'])
            if key in seen:continue
            seen.add(key)
            # Qualification repeats the original independent native execution.
            repeated=native.verify(item['program'],row['question'],'D-source-support-requalification')
            if (repeated['status'] not in ('PASS_NATIVE','FAIL_NATIVE') or repeated['cases']!=item['receipt']['cases']
                    or repeated['tests']!=row['baseline']['tests'] or repeated['passed']<=row['baseline']['passed']):
                raise RuntimeError('native support failed fresh requalification')
            receipt=self.machine.put({'first':item['receipt'],'fresh':repeated,'baseline':row['baseline'],
                                      'program':item['program'],'signature':item['signature'],'source':row['source'],'source_sha256':row['source_sha256'],'question':row['question']})
            node=self.machine.append('independent_native_improvement',{'receipt':receipt,'generation':1+sum(n.kind=='independent_native_improvement' for n in self.machine.log)},(source_node,))
            self.supports.setdefault(canonical(item['signature']),[]).append(node)
        self.rows.append(row)
        self.current=[]
        from research.unified_consequence_runtime.developmental_machine import Capability
        for sig in selected(self.rows):
            live=set(self.machine.mt.live_ids(self.machine.log))
            basis=[];source_ids=set()
            for ident in self.supports.get(canonical(sig),[]):
                if ident not in live:continue
                node=next(x for x in self.machine.log if x.id==ident)
                source_id=self.machine.get(node.payload['receipt'])['source']
                if source_id not in source_ids:basis.append(ident);source_ids.add(source_id)
                if len(basis)==2:break
            support=tuple(basis)
            if len(support)<2:continue  # Pending requalification is UNKNOWN, never an admitted capability.
            p=self.machine.put({'signature':sig,'generator':protocol()['generator_source']})
            observation=self.machine.put({'support_ids':list(support)})
            cap=Capability('refactory.v100.retained_family_search',protocol()['generator_source'],
                 {'protocol_binding':PROTOCOL_SHA,'input_type':'PythonSourceText','output_type':'CandidateSourceText',
                  'authority':'NONE','native_verifier':'Refactory.Tester.tv_code'},observation,p,1+sum(n.kind=='executable_capability' and n.payload.get('operation')=='refactory.v100.retained_family_search' for n in self.machine.log),support,(),
                  'CONSTRUCTOR_ACQUISITION')
            ident=self.machine.append('executable_capability',asdict(cap),support)
            self.current.append(ident)
        self.machine.flush()
        write(self.root/'profile-index.json',{'current':self.current,'protocol':PROTOCOL_SHA})
    def _check_support(self,ident,sig):
        nodes={n.id:n for n in self.machine.log};node=nodes[ident]
        if node.kind!='independent_native_improvement' or len(node.premises)!=1:raise ValueError('forged graph support')
        record=self.machine.get(node.payload['receipt'])
        source=record['source']
        if source not in protocol()['train']:raise ValueError('graph source outside training scope')
        with zipfile.ZipFile(WORK/'refactory_data_sealed.zip') as archive:original=archive.read(source).decode()
        parent=nodes[node.premises[0]]
        expected={'source':source,'sha256':sha(original.encode()),'protocol':PROTOCOL_SHA,'generation':parent.payload.get('generation')}
        if parent.kind!='source_artifact' or parent.payload!=expected or type(parent.payload.get('generation')) is not int or parent.payload['generation']<1:raise ValueError('graph source binding differs')
        if record['source_sha256']!=sha(original.encode()) or record['signature']!=sig:raise ValueError('graph program/source tamper')
        original_generator,root=generator()
        if record['program'] not in [x[2] for x in original_generator.generate_candidates(root,original,allowed=[sig],cap=320)]:raise ValueError('graph program outside original constructor')
        binding=context(WORK/'external-refactory',self.root.parent/'domain'/record['question'])
        baseline=check_reply(record['baseline'],sha(original.encode()),binding)
        path=self.root.parent/'native'/f"{baseline['call']:05d}"/'receipt.json'
        if json.loads(path.read_text())!=baseline:raise ValueError('graph baseline native transcript differs')
        for name in ['first','fresh']:
            receipt=check_reply(record[name],sha(record['program'].encode()),binding)
            path=self.root.parent/'native'/f"{receipt['call']:05d}"/'receipt.json'
            if json.loads(path.read_text())!=receipt:raise ValueError('graph native transcript differs')
            if receipt['tests']!=baseline['tests'] or receipt['passed']<=baseline['passed']:raise ValueError('fabricated native improvement')
        return record

    def signatures(self):
        live=set(self.machine.mt.live_ids(self.machine.log))&self.machine.flash_live_ids()
        result=[]
        for ident in self.current:
            if ident not in live:continue
            cap=self.machine.descriptor(ident)
            expected={'protocol_binding':PROTOCOL_SHA,'input_type':'PythonSourceText','output_type':'CandidateSourceText','authority':'NONE','native_verifier':'Refactory.Tester.tv_code'}
            if cap.operation!='refactory.v100.retained_family_search' or cap.source!=protocol()['generator_source'] or cap.scope!=expected:
                raise ValueError('unqualified graph source/protocol/profile')
            program=self.machine.get(cap.program)
            if program.get('generator')!=protocol()['generator_source']:raise ValueError('graph generator changed')
            observation=self.machine.get(cap.observation)
            if observation!={'support_ids':list(cap.dependencies)}:raise ValueError('graph dependency binding changed')
            if any(p not in live for p in cap.dependencies):continue
            sig=program['signature']
            sources={self._check_support(p,sig)['source'] for p in cap.dependencies}
            if len(sources)<2:raise ValueError('graph independent source support shortfall')
            result.append(sig)
        return result
    def reopen(self):
        old=self.signatures()
        request=self.root/'cold-request.json'
        write(request,{'root':str(self.root),'protocol':PROTOCOL_SHA})
        run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--cold-read',str(request)],capture_output=True,text=True,timeout=60)
        if run.returncode or json.loads(run.stdout)!=old:raise RuntimeError('fresh-process graph restart changed executable selection')
        self.__init_from_restart()
    def __init_from_restart(self):
        from research.unified_consequence_runtime.developmental_machine import Machine
        self.machine=Machine(WORK/'components',self.root,WORK/'unused-evaluator',WORK/'unused-config')

def episode(native,archive,task,arm,signatures,split):
    source=archive.read(task).decode();question=task.split('/')[1]
    started=time.perf_counter();before=native.number
    baseline=native.verify(source,question,arm+'-'+split+'-baseline')
    row={'source':task,'source_sha256':sha(source.encode()),'question':question,'arm':arm,'split':split,
         'baseline':baseline,'improvements':[],'witnesses':[],'candidates':[],'status':'UNKNOWN_NO_FULL_REPAIR',
         'signatures':signatures}
    if baseline['status']=='PASS_NATIVE':row['status']='ALREADY_NATIVE_PASS'
    elif baseline['status']!='FAIL_NATIVE':row['status']='UNKNOWN_BASELINE'
    else:
        for sel,builder,program in candidates(source,signatures,arm):
            r=native.verify(program,question,arm+'-'+split+'-candidate')
            sig=[list(sel),list(builder)]
            item={'signature':sig,'program':program,'receipt':r}
            row['candidates'].append(item)
            if r['status'] in ('PASS_NATIVE','FAIL_NATIVE') and r['tests']==baseline['tests'] and r['passed']>baseline['passed']:
                if sig not in row['improvements']:row['improvements'].append(sig)
                row['witnesses'].append(item)
            if r['status']=='PASS_NATIVE':
                fresh=native.verify(program,question,arm+'-'+split+'-solution-confirmation')
                if fresh['status']=='PASS_NATIVE' and fresh['cases']==r['cases']:
                    row['status']='WARRANTED_BOUNDED_REPAIR';row['winner']=item
                else:raise RuntimeError('false or unstable full native warrant')
                # Training explores all candidates for support; evaluation stops at verified success.
                if split=='eval':break
    row.update(wall_seconds=time.perf_counter()-started,native_calls=native.number-before)
    return row

def causal_checks(graph,native,archive,task,expected):
    """Post-evaluation causal replay; no evaluation result is added to memory."""
    before=graph.signatures();saved_rows=list(graph.rows)
    if not before:return {'status':'UNKNOWN_NO_ACQUIRED_SIGNATURE'}
    unrelated_before=graph.unrelated in graph.machine.mt.live_ids(graph.machine.log)
    # An irrelevant independent node can disappear without changing the learned route.
    irrelevant=graph.machine.append('ablation_irrelevant',{'task':task,'protocol':PROTOCOL_SHA})
    graph.machine.append('revoke',{'target':irrelevant,'reason':'predeclared irrelevant ablation'})
    graph.machine.flush()
    if graph.signatures()!=before:raise RuntimeError('irrelevant removal changed independent capability')
    irrelevant_result=episode(native,archive,task,'D',graph.signatures(),'eval')
    ancestors=sorted({p for ident in graph.current for p in graph.machine.descriptor(ident).dependencies})
    for ancestor in ancestors:graph.machine.append('revoke',{'target':ancestor,'reason':'predeclared ancestor ablation'})
    graph.machine.flush()
    if graph.signatures():raise RuntimeError('revoked source support remained active')
    absent=episode(native,archive,task,'D',graph.signatures(),'eval')
    if unrelated_before and graph.unrelated not in graph.machine.mt.live_ids(graph.machine.log):raise RuntimeError('source withdrawal damaged unrelated control')
    # Native requalification of the original training programs, not reuse of old IDs.
    for row in saved_rows:graph.add(row,native)
    restored=episode(native,archive,task,'D',graph.signatures(),'eval')
    # Explicit changed-assumption withdrawal; this is local controlled revision,
    # not a claim that an upstream publisher actually revoked the source.
    source_roots=[]
    nodes={n.id:n for n in graph.machine.log}
    if graph.current:
        first=graph.machine.descriptor(graph.current[0]).dependencies[0]
        source_roots=list(nodes[first].premises)
        protected={ident for ident in graph.current if not any(p in source_roots for d in graph.machine.descriptor(ident).dependencies for p in nodes[d].premises)}
        for root in source_roots:graph.machine.append('revoke',{'target':root,'reason':'controlled changed source assumption'})
        graph.machine.flush()
        if not protected<=set(graph.machine.mt.live_ids(graph.machine.log)):raise RuntimeError('changed assumption over-withdrew unrelated capability')
        for row in saved_rows:graph.add(row,native)
    causal=(absent['status']!='WARRANTED_BOUNDED_REPAIR' and restored['status']==expected['status'] and irrelevant_result['status']==expected['status'])
    return {'status':'WARRANTED_BOUNDED_CAUSAL_SEARCH_REUSE' if causal else 'REJECTED_CAUSAL_SEARCH_REUSE',
            'removed_ancestors':ancestors,'without':absent,'restored':restored,'irrelevant':irrelevant_result,
            'changed_assumption_source_roots':source_roots,'scope':'Existing finite-grammar search under fixed candidate budget; no new primitive or G3 promotion.'}

def setup(out,external,archive):
    native=Native(out,external,archive);controls=[]
    # Original reference code is read only inside the independent control path.
    # Generator receives no reference program, aligned code or expected outputs.
    for q in range(1,5):
        question=f'question_{q}'
        ref=archive.read(f'data/{question}/code/reference/reference.py').decode()
        good=native.verify(ref,question,'original-reference-positive-control')
        bad=native.verify('def __udm_absent_function__():\n    return None\n',question,'missing-function-negative-control')
        controls.append({'question':question,'reference':good,'negative':bad})
        if good['status']!='PASS_NATIVE' or bad['status']!='FAIL_NATIVE':
            write(out/'apparatus.json',controls);raise RuntimeError('UNKNOWN_ORIGINAL_VERIFIER_QUALIFICATION')
    empty=native.domain/'missing_tests'/'ans';empty.mkdir(parents=True)
    missing=native.verify('def missing(): return None\n','missing_tests','missing-test-negative-control')
    if not missing['status'].startswith('UNKNOWN_'):raise RuntimeError('missing test oracle falsely warranted')
    controls.append({'missing_test_control':missing})
    write(out/'apparatus.json',controls)
    return native

def campaign(out,external,archive_path):
    p=protocol();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    archive_path=Path(archive_path)
    if sha(archive_path.read_bytes())!=p['data_zip_sha256']:raise ValueError('external dataset changed')
    if subprocess.check_output(['git','-C',str(external),'rev-parse','HEAD'],text=True).strip()!=p['source_commit']:
        raise ValueError('external verifier source changed')
    subprocess.run(['git','-C',str(external),'diff','--exit-code','HEAD'],check=True)
    archive=zipfile.ZipFile(archive_path)
    start=time.perf_counter();native=setup(out,external,archive);graph=Graph(out/'D-graph');histories={a:[] for a in 'ABC'}
    results=[];costs=[];ledger_signatures=[];group=0
    for n in [0,4,8,12]:
        if n:
            for task in p['train'][n-4:n]:
                for arm in arm_order(group):
                    before=time.perf_counter()
                    signatures=[] if arm=='A' else (graph.signatures() if arm=='D' else (ledger_signatures if arm=='C' else selected(histories[arm])))
                    retrieve=time.perf_counter()-before
                    row=episode(native,archive,task,arm,signatures,'train')
                    row['retrieval_seconds']=retrieve
                    before=time.perf_counter()
                    if arm=='D':graph.add(row,native);graph.reopen()
                    elif arm!='A':
                        histories[arm].append(row)
                        write(out/(arm+'-history.json'),histories[arm])
                        if arm=='C':
                            ledger_signatures=selected(histories[arm])
                            write(out/'C-executable-ledger-index.json',{'signatures':ledger_signatures,'support_pairs':support_pairs(histories[arm])})
                    row['memory_seconds']=time.perf_counter()-before
                    results.append(row);write(out/'rows.json',results)
                    print('TRAIN',n,task,arm,row['status'],len(row['improvements']),flush=True)
                    if time.perf_counter()-start>5400:raise RuntimeError('frozen wall budget exhausted')
                group+=1
        checkpoint=[]
        for task in p['eval_shards'][str(n)]:
            for arm in arm_order(group):
                before=time.perf_counter()
                signatures=[] if arm=='A' else (graph.signatures() if arm=='D' else (ledger_signatures if arm=='C' else selected(histories[arm])))
                retrieve=time.perf_counter()-before
                row=episode(native,archive,task,arm,signatures,'eval');row.update(checkpoint=n,retrieval_seconds=retrieve)
                results.append(row);checkpoint.append(row);write(out/'rows.json',results)
                print('EVAL',n,task,arm,row['status'],flush=True)
                if time.perf_counter()-start>5400:raise RuntimeError('frozen wall budget exhausted')
            group+=1
        write(out/f'checkpoint-{n}.json',checkpoint)
        for task in p['eval_shards'][str(n)]:
            paired={r['arm']:r for r in checkpoint if r['source']==task}
            if paired['D']['status']=='WARRANTED_BOUNDED_REPAIR' and paired['A']['status']!='WARRANTED_BOUNDED_REPAIR':
                ablation=causal_checks(graph,native,archive,task,paired['D'])
                write(out/f'causal-{n}-{Path(task).stem}.json',ablation)
                if ablation['status']!='WARRANTED_BOUNDED_CAUSAL_SEARCH_REUSE':raise RuntimeError('causal gain falsified')
        costs.append({'checkpoint':n,'native_calls':native.number,'elapsed_seconds':time.perf_counter()-start,
                      'D_nodes':len(graph.machine.log),'D_current_capabilities':len(graph.current),
                      'storage_bytes':sum(f.stat().st_size for f in out.rglob('*') if f.is_file())})
        write(out/'costs.json',costs)
    write(out/'native-calls.json',native.calls)
    write(out/'summary.json',{'status':'EXECUTED_BOUNDED_PILOT','protocol_sha256':PROTOCOL_SHA,'costs':costs,
        'learning_curve':{str(n):{a:sum(r['status']=='WARRANTED_BOUNDED_REPAIR' for r in results if r.get('checkpoint')==n and r['arm']==a) for a in 'ABCD'} for n in [0,4,8,12]},
        'model_calls':0,'strict_g2':'UNKNOWN','strict_g3':'UNKNOWN','G4':'UNKNOWN_PENDING_ALL_COST_ANALYSIS',
        'transfer':'NOT_STARTED','ablation':'REQUIRED_IF_ANY_D_GAIN_OVER_A','source_commit':p['source_commit']})

def main():
    a=argparse.ArgumentParser();a.add_argument('--oracle');a.add_argument('--cold-read');a.add_argument('--out');a.add_argument('--external');a.add_argument('--archive');args=a.parse_args()
    if args.oracle:oracle(json.loads(Path(args.oracle).read_text()))
    elif args.cold_read:
        request=json.loads(Path(args.cold_read).read_text())
        if request['protocol']!=PROTOCOL_SHA:raise ValueError('wrong cold protocol')
        g=Graph(Path(request['root']));index=json.loads((g.root/'profile-index.json').read_text())
        if index['protocol']!=PROTOCOL_SHA:raise ValueError('wrong persisted protocol')
        g.current=index['current'];print(canonical(g.signatures()))
    else:
        try:campaign(Path(args.out),Path(args.external),Path(args.archive))
        except Exception as error:
            write(Path(args.out)/'STOP.json',{'status':'STOPPED_UNKNOWN','exception':type(error).__name__,'reason':str(error),'strict_g2':'UNKNOWN','strict_g3':'UNKNOWN'})
            raise
if __name__=='__main__':main()
