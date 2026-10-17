#!/usr/bin/env python3
"""Exact read-only PARI/GP SEA census over one frozen P-224 candidate shard.

No post-hoc candidate edits. A zero from ellsea(E,1) is an early torsion
rejection, not an exact cardinality. All other errors -> UNKNOWN, not zero.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import v9_candidates as v9

HERE=Path(__file__).resolve().parent
TABLE_SHA='6ae4d488768e622d5ff307ca7bb1af2c2b7d10c0f6935fac2e7107eac1fa5d22'
N_SHARDS=8
PROTO_FREEZE='405550256a06c74d1a06d9af30a57b84f0ef9457'


def witness(b):
    for x in range(0,80):
        v=(pow(x,3,v9.P)-3*x+b)%v9.P
        if not v: return (x,0)
        if v9.is_square(v):
            y=v9.tonelli(v)
            if y&1:y=v9.P-y
            assert (y*y-x*x*x+3*x-b)%v9.P==0
            return x,y
    raise AssertionError('No deterministic witness x<80')


def add(P,Q):
    if P is None:return Q
    if Q is None:return P
    x,y=P;u,v=Q
    if x==u and (y+v)%v9.P==0:return None
    if x==u:
        m=((3*x*x-3)*pow(2*y,-1,v9.P))%v9.P
    else:
        m=((v-y)*pow(u-x,-1,v9.P))%v9.P
    xp=(m*m-x-u)%v9.P
    return (xp,(m*(x-xp)-y)%v9.P)


def mul(n,Q):
    R=None
    while n:
        if n&1:R=add(R,Q)
        Q=add(Q,Q);n>>=1
    return R


def check_prime_order(idx:int,b:int,n:int,ip:int):
    assert n>0 and ip in (0,1)
    assert abs(n-(v9.P+1))**2<=4*v9.P,('hasse',idx)
    status='PRIME_ORDER' if ip==1 else 'COMPOSITE_ORDER'
    out={'index':idx,'b':hex(b),'order':str(n),'prime_proved_by_pari':ip==1,
        'method':'ellsea(E,1)_exact_positive', 'hasse':True, 'status':status}
    if ip==1:
        pt=witness(b)
        assert mul(n,pt) is None,('independent_group_law_disagrees',idx)
        k=None;rem=v9.P%n
        for j in range(1,1024):
            if rem==1:k=j;break
            rem=rem*v9.P%n
        out.update({'point_check':True,'witness':[hex(pt[0]),hex(pt[1])],
                    'bits':n.bit_length(),'embedding_bad_k_up_to_1023':k,'anomalous':n==v9.P,
                    'qualifies_224bit':n.bit_length()==224 and n!=v9.P and k is None})
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--shard',type=int,required=True)
    parser.add_argument('--gp',default='gp')
    parser.add_argument('--timeout',type=int,default=1200)
    args=parser.parse_args()
    assert 0<=args.shard<N_SHARDS
    assert args.timeout<=1200
    a=HERE/'V9_CANDIDATES.json'
    rows=json.loads(a.read_text())
    packed=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(packed).hexdigest()==TABLE_SHA
    eligible=[r for r in rows if r['state']=='ELIGIBLE_FOR_POINT_COUNT' and r['index']%N_SHARDS==args.shard]
    assert len(eligible)>0
    gpcode=['default(parisizemax, 1500000000);',f'p={v9.P};',
            'print("V9_VERSION|",version());',
            'v9(i,b)={ my(E,n,ip); E=ellinit([-3,b],p); n=ellsea(E,1); '
            'if(n>0,ip=isprime(n),ip=-1); print("V9|",i,"|",n,"|",ip); };']
    gpcode.extend(f"v9({r['index']},{int(r['b'],16)});" for r in eligible)
    gpcode.append('print("V9_FINISHED");')
    gpcode.append('quit(0);')
    gp_source='\n'.join(gpcode)+'\n'
    gp_path=HERE/f'V9_SHARD_{args.shard}.gp'
    gp_path.write_text(gp_source)
    outcome={'shard':args.shard,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'candidate_table_sha256':TABLE_SHA,'protocol_freeze':PROTO_FREEZE,
             'gp_sha256':hashlib.sha256(gp_source.encode()).hexdigest(),
             'eligible_indices':[r['index'] for r in eligible],
             'status':'UNKNOWN_NOT_STARTED', 'results':[], 'gp_version':None,
             'full_census':False,'errors':[]}
    out=HERE/f'V9_SHARD_{args.shard}.json'
    def save():out.write_text(json.dumps(outcome,sort_keys=True,indent=2)+'\n')
    save()
    started=time.monotonic()
    try:
        proc=subprocess.run([args.gp,'-q','-f',str(gp_path)],capture_output=True,text=True,timeout=args.timeout,check=False)
    except subprocess.TimeoutExpired as e:
        outcome['status']='UNKNOWN_RESOURCE_TIMEOUT'
        outcome['errors'].append('PARI GP timeout, no zero count assumed')
        outcome['elapsed_seconds']=round(time.monotonic()-started,3)
        save();raise SystemExit(2)
    outtext=proc.stdout+'\n'+proc.stderr
    (HERE/f'V9_SHARD_{args.shard}_PARI_LOG.txt').write_text(outtext)
    result_lines=re.findall(r'^V9\|(\d+)\|(\d+)\|(-?\d+)$',outtext,re.M)
    raw_errors=[s for s in outtext.splitlines() if '***' in s and 'Warning:' not in s]
    versions=re.findall(r'^V9_VERSION\|(.+)$',outtext,re.M)
    outcome['gp_version']=versions[0] if versions else None
    outcome['elapsed_seconds']=round(time.monotonic()-started,3)
    if proc.returncode!=0 or 'V9_FINISHED' not in outtext or raw_errors:
        outcome['status']='UNKNOWN_GP_ERROR_OR_PARTIAL'
        outcome['errors']+=raw_errors[:20]
        outcome['errors'] +=[f'return={proc.returncode}, rows={len(result_lines)}/{len(eligible)}']
        save();raise SystemExit(2)
    actual={}
    for idx,order,pr in result_lines:
        idx=int(idx);order=int(order);pr=int(pr)
        if idx in actual:raise AssertionError('Duplicate index')
        actual[idx]=(order,pr)
    if set(actual)!={r['index'] for r in eligible}:
        outcome['status']='UNKNOWN_INCOMPLETE_INDICES';save();raise SystemExit(2)
    verdict=[]
    for row in eligible:
        i=row['index'];n,ip=actual[i]
        if n==0:
            assert ip==-1
            verdict.append({'index':i,'status':'NOT_PRIME_BY_TORSION_TEST','exact_order':None,
                            'origin':'ellsea(E,1) early exit'})
        elif n>0:verdict.append(check_prime_order(i,int(row['b'],16),n,ip))
        else:raise AssertionError(f'Unexpected negative SEA at {i}: {n}')
    outcome['status']='QUALIFIED_BOUNDED_SHARD'
    outcome['full_census']=True
    outcome['results']=verdict
    outcome['counts']={s:sum(x['status']==s for x in verdict) for s in
         ('NOT_PRIME_BY_TORSION_TEST','COMPOSITE_ORDER','PRIME_ORDER')}
    save()
    print(json.dumps({k:outcome[k] for k in ('shard','status','counts','elapsed_seconds','gp_version')},sort_keys=True))

if __name__=='__main__':main()
