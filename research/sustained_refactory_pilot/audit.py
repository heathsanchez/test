"""Read-only, independently recomputed audit of frozen native pilot evidence."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path
import subprocess, zipfile

def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)

def audit(root,repo,archive):
    root,repo,archive=map(Path,(root,repo,archive))
    protocol=json.loads((repo/'research/sustained_refactory_pilot/protocol.json').read_text())
    ph=sha((repo/'research/sustained_refactory_pilot/protocol.json').read_bytes())
    require(ph=='4ad23a6440d6fb7f85e01cb276a563320d569f68d04f48aede2991cbb809b94f','protocol changed')
    require(sha(archive.read_bytes())==protocol['data_zip_sha256'],'dataset changed')
    rows=json.loads((root/'rows.json').read_text());summary=json.loads((root/'summary.json').read_text())
    require(summary['status']=='EXECUTED_BOUNDED_PILOT','pilot incomplete')
    require(not (root/'STOP.json').exists(),'pilot stopped')
    source_pin='f917955b2f83d3f21d598a81634aeeb60a7c0af5'
    runner=subprocess.check_output(['git','-C',str(repo),'show',source_pin+':research/sustained_refactory_pilot/pilot.py'])
    require(sha(runner)==sha((repo/'research/sustained_refactory_pilot/pilot.py').read_bytes()),'runner differs from pre-execution commit')
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
    history={a:[] for a in 'ABCD'};evaluation={};training=collections.Counter();partial=collections.Counter();full=collections.Counter()
    by_task=collections.defaultdict(list)
    for row in rows:
        arm=row['arm'];source=row['source'];split=row['split']
        require(source in protocol['train' if split=='train' else 'eval'],'source outside split')
        require(row['source_sha256']==sha(z.read(source)),'row original source changed')
        require(len(row['candidates'])<=32,'search budget exceeded')
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
            require(f.exists() and json.loads(f.read_text())['status']=='WARRANTED_BOUNDED_CAUSAL_SEARCH_REUSE','unqualified causal gain')
    for arm in 'ABCD':require(calls[arm]<=2400,'arm native budget exceeded')
    require(len(receipts)<=9700,'total native budget exceeded')
    return {'schema':'udm.sustained.refactory.independent-audit.v1','status':'PASS_BOUNDED_EVIDENCE_AUDIT',
      'source_commit':source_pin,'protocol_sha256':ph,'rows':len(rows),'training_episodes_per_arm':dict(training),
      'learning_curve_disjoint_three_task_shards':evaluation,'paired_D_vs':paired,'partial_training_improvement_signatures':dict(partial),
      'native_calls':dict(calls),'native_process_wall_seconds':dict(wall),'native_cpu_seconds':dict(cpu),'native_storage_bytes':dict(storage),
      'status_counts':dict(collections.Counter(r['status'] for r in rows)),
      'independent_boundary':'Source hashes, original external native test identities/results and paired evidence consistency; not a formal soundness proof, generic agent comparison, authenticated external receipt service or complete all-in economics.',
      'uncertainty':'12 related held-out source programs in four repeated exercise families. Descriptive paired counts; no population independence or same-task learning-curve inference.',
      'strict_G2':'UNKNOWN','strict_G3':'UNKNOWN','G5':'UNKNOWN','G6':'UNKNOWN','model_calls':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--repo',required=True);p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    result=audit(a.root,a.repo,a.archive);Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(result['status'])
