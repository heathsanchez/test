"""Read-only, independently recomputed audit of frozen native pilot evidence."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path
import subprocess, zipfile, importlib.util

def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)

def audit(root,repo,archive):
    root,repo,archive=map(Path,(root,repo,archive))
    protocol=json.loads((repo/'research/sustained_refactory_pilot/protocol_v3.json').read_text())
    ph=sha((repo/'research/sustained_refactory_pilot/protocol_v3.json').read_bytes())
    require(ph=='347baa0a3b84997f77475ecf2bcde20a031f6b097768f3826c1869bf45bbe865','protocol changed')
    require(sha(archive.read_bytes())==protocol['data_zip_sha256'],'dataset changed')
    rows=json.loads((root/'rows.json').read_text());summary=json.loads((root/'summary.json').read_text())
    require(summary['status']=='EXECUTED_BOUNDED_PILOT','pilot incomplete')
    require(not (root/'STOP.json').exists(),'pilot stopped')
    source_pin='c4cc55d79a7ebc879491475276531959799d37cd'
    runner=subprocess.check_output(['git','-C',str(repo),'show',source_pin+':research/sustained_refactory_pilot/pilot_v3.py'])
    require(sha(runner)==sha((repo/'research/sustained_refactory_pilot/pilot_v3.py').read_bytes()),'runner differs from pre-execution commit')
    z=zipfile.ZipFile(archive);cases={}
    for q in range(1,5):
        prefix=f'data/question_{q}/ans/'
        cases[f'question_{q}']={Path(n).name[len('input_'):].split('.')[0] for n in z.namelist() if n.startswith(prefix) and Path(n).name.startswith('input_') and not n.endswith('/')}
    receipts={};calls=collections.Counter();wall=collections.Counter();cpu=collections.Counter();storage=collections.Counter()
    for f in sorted((root/'native').glob('*/receipt.json')):
        r=json.loads(f.read_text());request=json.loads(f.with_name('request.json').read_text())
        raw=f.with_name('candidate.py').read_bytes();code_hash=sha(raw)
        require(r['source_sha256']==code_hash,'candidate raw byte mismatch')
        if r['status'] in ('PASS_NATIVE','FAIL_NATIVE'):
            question=Path(request['question_dir']).name;expected=cases[question]
            require(set(r['cases'])==expected and all(type(v) is bool for v in r['cases'].values()),'native test identities incomplete')
            require(r['tests']==len(expected) and r['passed']==sum(r['cases'].values()),'native count mismatch')
            require(r['status']==('PASS_NATIVE' if all(r['cases'].values()) else 'FAIL_NATIVE'),'false native verdict')
            require(r['candidate_sha256']==code_hash and r['binding']==request['binding'],'oracle source binding mismatch')
            require(r['binding']['protocol']==ph and r['binding']['runner']==sha(runner),'oracle method drift')
            markers=[l.split('=',1)[1] for l in f.with_name('stdout.log').read_text().splitlines() if l.startswith('UDM_ORACLE_RESULT=')]
            require(len(markers)==1,'missing native raw oracle transcript')
            emitted=json.loads(markers[0]);require(all(r[k]==v for k,v in emitted.items()),'native raw oracle transcript changed')
        receipts[r['call']]=r
        arm=r['label'][0] if r['label'][0] in 'ABCD' else 'COMMON'
        calls[arm]+=1;wall[arm]+=r['process_wall_seconds'];cpu[arm]+=r['cpu_user_seconds']+r['cpu_system_seconds']
        storage[arm]+=sum(x.stat().st_size for x in f.parent.iterdir() if x.is_file())
    require(len(rows)==96,'four arms times 24 episodes required')
    spec=importlib.util.spec_from_file_location('frozen_pilot_v3',repo/'research/sustained_refactory_pilot/pilot_v3.py');method=importlib.util.module_from_spec(spec);spec.loader.exec_module(method)
    history={a:[] for a in 'ABCD'};evaluation={};training=collections.Counter();partial=collections.Counter();full=collections.Counter()
    by_task=collections.defaultdict(list)
    for row in rows:
        arm=row['arm'];source=row['source'];split=row['split']
        require(source in protocol['train' if split=='train' else 'eval'],'source outside split')
        require(row['source_sha256']==sha(z.read(source)),'row original source changed')
        require(len(row['candidates'])<=32,'search budget exceeded')
        expected_priorities=[] if arm=='A' else method.selected(history[arm])
        require(row['signatures']==expected_priorities,'retained priorities differ from prior training evidence')
        source_text=z.read(source).decode()
        expected_programs=method.candidates(source_text,expected_priorities,arm) if row['baseline']['status']=='FAIL_NATIVE' else []
        actual_programs=[(tuple(c['signature'][0]),tuple(c['signature'][1]),c['program']) for c in row['candidates']]
        require(actual_programs==expected_programs[:len(actual_programs)],'candidate ordering differs from frozen method')
        if split=='train' or row['status']!='WARRANTED_BOUNDED_REPAIR':
            require(len(actual_programs)==len(expected_programs),'candidate stream unexpectedly truncated')
        improvements=[]
        for candidate in row['candidates']:
            native=candidate['receipt']
            if native['status'] in ('PASS_NATIVE','FAIL_NATIVE') and native['tests']==row['baseline']['tests'] and native['passed']>row['baseline']['passed']:
                if candidate['signature'] not in improvements:improvements.append(candidate['signature'])
            if native['status']=='PASS_NATIVE':
                confirmation=receipts.get(native['call']+1,{})
                require(confirmation.get('status')=='PASS_NATIVE' and confirmation.get('cases')==native['cases'] and confirmation.get('source_sha256')==native['source_sha256'],'full repair lacks fresh native confirmation')
                require(confirmation.get('label')==arm+'-'+split+'-solution-confirmation','full repair confirmation has wrong scope')
        require(row['improvements']==improvements,'training score-improvement facts were fabricated')
        require(receipts[row['baseline']['call']]==row['baseline'],'baseline receipt mismatch')
        for c in row['candidates']:
            require(receipts[c['receipt']['call']]==c['receipt'],'candidate receipt mismatch')
            require(c['receipt']['source_sha256']==sha(c['program'].encode()),'candidate source changed')
        if row['status']=='WARRANTED_BOUNDED_REPAIR':
            require(row['winner']['receipt']['status']=='PASS_NATIVE','false full repair')
            full[arm]+=1
        if split=='train':
            training[arm]+=1;partial[arm]+=len(row['improvements']);history[arm].append(row)
        else:
            n=row['checkpoint'];require(source in protocol['eval_shards'][str(n)],'checkpoint source mismatch')
            evaluation.setdefault(str(n),{})[arm]=evaluation.get(str(n),{}).get(arm,0)+(row['status']=='WARRANTED_BOUNDED_REPAIR')
            by_task[source].append(row)
    require(all(training[a]==12 for a in 'ABCD'),'training episode count mismatch')
    require(evaluation==summary['learning_curve'],'checkpoint summary mismatch')
    paired={a:{'wins':0,'ties':0,'losses':0} for a in 'ABC'}
    for task,rs in by_task.items():
        require(set(r['arm'] for r in rs)==set('ABCD') and len(rs)==4,'unmatched evaluation')
        ok={r['arm']:r['status']=='WARRANTED_BOUNDED_REPAIR' for r in rs}
        for a in 'ABC':paired[a]['wins' if ok['D']>ok[a] else ('losses' if ok['D']<ok[a] else 'ties')]+=1
        if ok['D'] and not ok['A']:
            n=rs[0]['checkpoint'];f=root/f'causal-{n}-{Path(task).stem}.json'
            require(f.exists(),'missing causal replay')
            causal=json.loads(f.read_text())
            require(causal['status']=='WARRANTED_BOUNDED_CAUSAL_SEARCH_REUSE','unqualified causal gain')
            require(causal['without']['status']!='WARRANTED_BOUNDED_REPAIR' and causal['without']['signatures']==[],'ancestor removal did not eliminate priority bundle')
            require(causal['restored']['status']=='WARRANTED_BOUNDED_REPAIR' and causal['irrelevant']['status']=='WARRANTED_BOUNDED_REPAIR','restoration/noninterference not observed')
            for key in ['without','restored','irrelevant']:
                for candidate in causal[key]['candidates']:
                    require(receipts[candidate['receipt']['call']]==candidate['receipt'],'causal native receipt mismatch')
                    if candidate['receipt']['status']=='PASS_NATIVE':
                        confirm=receipts.get(candidate['receipt']['call']+1,{})
                        require(confirm.get('status')=='PASS_NATIVE' and confirm.get('cases')==candidate['receipt']['cases'],'causal full repair lacks confirmation')
            nodes=[json.loads(l) for l in (root/'D-graph/metatron-ledger.jsonl').read_text().splitlines()]
            revoked={v['payload']['target'] for v in nodes if v['kind']=='revoke'}
            require(set(causal['removed_ancestors'])<=revoked and set(causal['changed_assumption_source_roots'])<=revoked,'causal withdrawal missing from append-only ledger')
    for arm in 'ABCD':require(calls[arm]<=2400,'arm native budget exceeded')
    require(len(receipts)<=9700,'total native budget exceeded')
    return {'schema':'udm.sustained.refactory.independent-audit.v3','status':'PASS_BOUNDED_EVIDENCE_AUDIT',
      'source_commit':source_pin,'protocol_sha256':ph,'rows':len(rows),'training_episodes_per_arm':dict(training),
      'learning_curve_disjoint_three_task_shards':evaluation,'paired_D_vs':paired,'partial_training_improvement_signatures':dict(partial),
      'native_calls':dict(calls),'native_process_wall_seconds':dict(wall),'native_cpu_seconds':dict(cpu),'native_storage_bytes':dict(storage),
      'status_counts':dict(collections.Counter(r['status'] for r in rows)),
      'independent_boundary':'Source hashes, original external native test identities/results and paired evidence consistency; not a formal soundness proof, generic agent comparison, authenticated external receipt service or complete all-in economics.',
      'uncertainty':'12 related held-out source programs in four repeated exercise families. Descriptive paired counts; no population independence or same-task learning-curve inference.',
      'policy_reconstruction':'PASS_PRIOR_TRAINING_ONLY_ORDERING_AND_FRESH_FULL_CONFIRMATION',
      'causal_scope':'Retained-priority bundle only; irrelevant-node control is not an unrelated executable-operation ablation.',
      'strict_G2':'UNKNOWN','strict_G3':'UNKNOWN','G5':'UNKNOWN','G6':'UNKNOWN','model_calls':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--repo',required=True);p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    result=audit(a.root,a.repo,a.archive);Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(result['status'])
