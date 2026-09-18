#!/usr/bin/env python3
"""Freeze/restart/replay audit; replication cohort is not a new sealed holdout."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import collatz_macro_authority as authority


def write(path,obj):
    Path(path).write_text(authority.canonical(obj))


def acquire(sources=None):
    import collatz_forward_descent_macro_transfer as old
    caps=[]; seen=set(); events=[]; selected=[]
    root={'operation':'declare','contract':authority.contract(),'training':[3,8191]}
    root['id']=authority.digest(root);events.append(root)
    for n in (range(3,8192,2) if sources is None else sources):
        if sources is None and not old.candidate(n):continue
        starts,words=old.q0_odd_starts_and_words(n)
        if not words:continue
        selected.append(n)
        for i in range(max(0,len(words)-12),len(words)):
            c=authority.capability(words[i:])
            k,r,m,x=starts[i]
            z=authority.replay(c,m)
            authority.require(z['legal'] and z['minimum']<n,'training did not actually descend')
            authority.verify_descent(n,k+z['arg'],z['minimum'])
            if c['id'] in seen:continue
            seen.add(c['id']);caps.append(c)
            event={'operation':'promote_guarded_path','parents':[root['id']],
                   'capability_id':c['id'],'verifier':authority.contract()['verifier'],
                   'certificate':{'n':n,'t':k+z['arg'],'y':z['minimum']},
                   'claim':'guarded exact path; independently replay each future descent'}
            event['id']=authority.digest(event);events.append(event)
    return authority.seal(caps),events,selected


def prepare(directory):
    import collatz_forward_descent_macro_transfer as old
    import collatz_q0_rigid_recharge_audit as ra
    directory.mkdir(parents=True,exist_ok=True)
    bank,ledger,sources=acquire()
    authority.require(len(bank['capabilities'])==481 and len(sources)==252,'training replication drift')
    write(directory/'bank.json',bank)
    write(directory/'ledger.json',ledger)
    write(directory/'raw-history.json',{'selected_training_sources':sources,
          'contract':bank['contract'],'role':'raw source identities; rerun acquisition to recover macros'})
    rows=[]
    for n in range(8193,16384,2):
        if not old.candidate(n):continue
        starts,words=ra.rigid_episode_segment(n,96)
        if not words:continue
        for k,r,m,x in starts:
            actual=n
            for _ in range(k):actual=authority.step(actual)
            authority.require(actual==x==2**r*m-1,'cohort endpoint mismatch')
        rows.append({'n':n,'starts':[list(x) for x in starts]})
    authority.require(len(rows)==162,'cohort replication drift')
    write(directory/'cohort.json',{'sources':rows,'selection':'frozen retrospective replication of run35327397877',
                                 'digest':authority.digest(rows)})
    print('PREPARED',len(sources),len(bank['capabilities']),len(rows),flush=True)


def evaluate(bank,cohort,sham=False):
    by_anchor={}
    for c in authority.active(bank):by_anchor.setdefault(c['r0'],[]).append(c)
    rows=[]
    for source in cohort['sources']:
        n=source['n']; used=0;attempts=0;certificate=None
        preparation=max(x[0] for x in source['starts'])
        for k,r,m,x in source['starts']:
            for c in by_anchor.get(r,[]):
                attempts+=1
                # Same-size valid bank, but an irrelevant restricted input domain.
                if sham and m<10**100:continue
                z=authority.replay(c,m);used+=z['steps']
                if z['legal'] and z['minimum']<n:
                    t=k+z['arg'];y=z['minimum']
                    authority.verify_descent(n,t,y)
                    certificate={'n':n,'t':t,'y':y,'capability_id':c['id']}
                    break
            if certificate:break
        rows.append({'n':n,'preparation_steps':preparation,'replay_steps':used,
                     'attempts':attempts,'certificate':certificate})
    return {'closed':sum(x['certificate'] is not None for x in rows),
            'rows':rows,'replay_steps':sum(x['replay_steps'] for x in rows),
            'preparation_steps':sum(x['preparation_steps'] for x in rows)}


def worker(directory,arm):
    cohort=json.loads((directory/'cohort.json').read_text())
    authority.require(authority.digest(cohort['sources'])==cohort['digest'],'cohort changed')
    acquisition=0
    if arm=='raw':
        raw=json.loads((directory/'raw-history.json').read_text())
        bank,_,sources=acquire(raw['selected_training_sources']);acquisition=len(sources)
    else:
        bank=authority.restore((directory/'bank.json').read_text())
        authority.require('collatz_forward_descent_macro_transfer' not in sys.modules,
                          'discovery code imported during history-free restart')
    if arm=='raw':
        authority.require(bank['digest']==authority.restore((directory/'bank.json').read_text())['digest'],
                          'raw reconstruction differs from compiled bank')
    if arm=='ablation':
        warm=json.loads((directory/'warm.json').read_text())
        revoked=sorted({x['certificate']['capability_id'] for x in warm['rows'] if x['certificate']})
        bank=authority.restore(authority.canonical(authority.seal(bank['capabilities'],revoked)))
        write(directory/'revoked-bank.json',bank)
    result=evaluate(bank,cohort,sham=arm=='sham')
    result.update(arm=arm,bank_digest=bank['digest'],acquisition_sources_reprocessed=acquisition)
    write(directory/(arm+'.json'),result)
    print('ARM',arm,'CLOSED',result['closed'],'STEPS',result['replay_steps'],
          'ACQUISITION_SOURCES_REPROCESSED',acquisition,flush=True)


def qualify(directory):
    prepare(directory)
    for arm in ('warm','raw','sham','ablation'):
        subprocess.run([sys.executable,__file__,'worker','--output',str(directory),'--arm',arm],check=True)
    results={arm:json.loads((directory/(arm+'.json')).read_text())
             for arm in ('warm','raw','sham','ablation')}
    warm=results['warm'];cold=[]
    for row in warm['rows']:
        # Shared cohort preparation has already traversed to all offered starts.
        # Charge that traversal to both arms. Exclude the common selector's
        # classifier overhead and final certificate-verification overhead.
        n=row['n'];x=n;certificate=None;spent=0
        budget=row['preparation_steps']+row['replay_steps']
        for t in range(1,budget+1):
            x=authority.step(x);spent=t
            if x<n:
                authority.verify_descent(n,t,x)
                certificate={'n':n,'t':t,'y':x};break
        cold.append({'n':n,'budget':budget,'steps':spent,'certificate':certificate})
        if row['certificate']:
            authority.require(certificate is not None,'matched forward baseline lost warm closure')
    write(directory/'cold.json',cold)
    authority.require(warm['closed']==88,'protected 88-case transfer changed')
    authority.require(results['raw']['rows']==warm['rows'],'raw/warm consequence mismatch')
    authority.require(results['sham']['closed']==0,'irrelevant-domain sham unexpectedly applies')
    authority.require(results['ablation']['closed']<88,'targeted ablation did not remove any coverage')
    cold_closed=sum(x['certificate'] is not None for x in cold)
    cold_steps=sum(x['steps'] for x in cold)
    warm_steps=warm['preparation_steps']+warm['replay_steps']
    advantage=(warm['closed']>cold_closed or
               (warm['closed']==cold_closed and warm_steps<cold_steps))
    summary={'qualification':'PASS_BOUNDED_RESTART_REPLAY',
       'compounding_promotion':'PASS' if advantage else 'REJECT_FORWARD_STEP_ADVANTAGE',
       'macro_count':481,'cohort':162,'warm_closed':88,'warm_unresolved':74,
       'cold_closed':cold_closed,'cold_steps':cold_steps,'warm_steps':warm_steps,
       'raw_closed':results['raw']['closed'],'raw_acquisition_sources':results['raw']['acquisition_sources_reprocessed'],
       'warm_acquisition_sources':warm['acquisition_sources_reprocessed'],
       'sham_closed':results['sham']['closed'],'targeted_ablation_closed':results['ablation']['closed'],
       'bank_digest':warm['bank_digest'],'independent_task_certificates':True,
       'claims':['exact guarded replay','canonical fresh-process restart','bounded macro coverage contribution'],
       'not_claimed':['QCKN full reference conformance','prospective new holdout','universal termination','Collatz'],
       'controls':'matched forward budget; raw selected-source rediscovery; restricted-domain sham; post-hoc successful-capability ablation'}
    write(directory/'summary.json',summary)
    print(authority.canonical(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['qualify','worker','promotion'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--arm',choices=['warm','raw','sham','ablation'])
    args=parser.parse_args()
    if args.mode=='qualify':qualify(args.output)
    elif args.mode=='worker':worker(args.output,args.arm)
    else:
        summary=json.loads((args.output/'summary.json').read_text())
        if summary['compounding_promotion']!='PASS':
            print(summary['compounding_promotion']);sys.exit(1)
