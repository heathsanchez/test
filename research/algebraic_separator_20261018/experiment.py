#!/usr/bin/env python3
"""Frozen RSA-style algebraic separator benchmark; existing QS relation technique.

Arms A smooth-only, B paired-cofactor, identical polynomial and factor-base;
independent established SymPy SIQS comparator and simple Fermat/rho controls.
NOT a novel factoring algorithm or RSA-270 attack.
"""
import argparse
import hashlib
import json
import math
import multiprocessing as mp
import time
from collections import defaultdict
from pathlib import Path

from sympy import primerange

ROOT=Path(__file__).resolve().parent


def factor_base(n, bound):
    primes=[2]
    for p in primerange(3,bound+1):
        p=int(p)
        if n%p==0:
            raise ValueError('factor base prime divides modulus: benchmark control N invalid')
        if pow(n%p, (p-1)//2, p)==1:
            primes.append(p)
    return primes


def q_factor(value, primes, cost):
    """Trial-divide on fixed eligible factor base; exact remainder retained."""
    exps={}
    rem=value
    for p in primes:
        cost['modular_divisions']+=1
        if rem%p:
            continue
        e=0
        while rem%p == 0:
            cost['modular_divisions']+=1
            rem//=p
            e+=1
        exps[p]=e
        if rem==1: break
    return exps,rem


def combine(a,b,extra):
    exps=a['exps'].copy()
    for p,e in b['exps'].items():
        exps[p]=exps.get(p,0)+e
    exps[extra]=exps.get(extra,0)+2
    return {'x':a['x']*b['x'], 'exps':exps,'origin':(a['origin'][0],b['origin'][0])}


class Basis:
    def __init__(self,n,primes):
        self.n=n
        self.primes=primes
        self.positions={p:i for i,p in enumerate(primes)}
        self.rows=[]
        self.pivots={}
        self.dependencies=0
        self.trivial=0
        self.found=None
        self.rank_at_factor=None
    def parity(self,row):
        bits=0
        for p,e in row['exps'].items():
            if e & 1:
                bits^=1<<self.positions[p]
        return bits
    def admit(self,row,case_id,candidate_number):
        index=len(self.rows)
        self.rows.append(row)
        vec=self.parity(row)
        comb=1<<index
        while vec:
            pivot=vec.bit_length()-1
            if pivot not in self.pivots:
                self.pivots[pivot]=(vec,comb)
                return None
            b, mask=self.pivots[pivot]
            vec^=b
            comb^=mask
        self.dependencies+=1
        x=1
        exps=defaultdict(int)
        n=self.n
        used=[]
        while comb:
            lowbit=comb & (-comb)
            k=lowbit.bit_length()-1
            row2=self.rows[k]
            used.append(k)
            x=(x*row2['x'])%n

            for p,e in row2['exps'].items():
                exps[p]+=e
            comb ^= lowbit
        assert all(v%2==0 for v in exps.values()), 'invalid GF2 reconstruction'
        y=1
        for p,e in exps.items():
            y=(y*pow(p,e//2,n))%n

        assert (x*x-y*y)%n==0, 'bad modular square congruence'
        minus=math.gcd(x-y,n)
        plus=math.gcd(x+y,n)
        if 1<minus<n: d=minus
        elif 1<plus<n: d=plus
        else:
            self.trivial+=1
            return None
        other=n//d
        assert d*other==n
        witness={
            'case_id':case_id,'candidate_number':candidate_number,
            'factor':str(d),'cofactor':str(other),
            'square_x_mod_n':str(x),'square_y_mod_n':str(y),
            'nontrivial_minus':1<minus<n,'nontrivial_plus':1<plus<n,
            'dependency_rows':len(used), 'basis_rank':len(self.pivots),
            'certificate_sha256':hashlib.sha256(f'{n}:{x}:{y}:{d}'.encode()).hexdigest(),
        }
        self.found=witness
        return witness


def run_arm(n,primes,case_id,arm,limit,lpmax):
    assert arm in ('A','B')
    t0=time.perf_counter()
    ledger=Basis(n,primes)
    square=math.isqrt(n)
    start=square+(square*square<n)
    partials={}
    charge={'modular_divisions':0,'smooth_rows':0,'partials_seen':0,'partials_matched':0,'discarded':0,
            'candidates_examined':0}
    for i in range(limit):
        x=start+i
        q=x*x-n
        assert q>0
        exps,rem=q_factor(q,primes,charge)
        charge['candidates_examined']+=1
        if rem==1:
            charge['smooth_rows']+=1
            rel={'x':x,'exps':exps,'origin':(i,)}
        elif arm=='B' and 1<rem<=lpmax:
            charge['partials_seen']+=1
            cur={'x':x,'exps':exps,'origin':(i,)}
            if rem not in partials:
                partials[rem]=cur
                continue
            charge['partials_matched']+=1
            rel=combine(partials[rem],cur,rem)
        else:
            charge['discarded']+=1
            continue
        witness=ledger.admit(rel,case_id,i+1)
        if witness:
            break
    return {
        'arm':arm,'case_id':case_id,'factor_found':ledger.found is not None,
        'witness':ledger.found,'charge':charge,'basis_rank':len(ledger.pivots),
        'dependences_tested':ledger.dependencies,'trivial_dependences':ledger.trivial,
        'retained_rows':len(ledger.rows),'retained_partial_keys':len(partials),
        'elapsed_seconds':round(time.perf_counter()-t0,6)
    }


def fermat(n,steps):
    t=time.perf_counter(); x=math.isqrt(n)
    if x*x<n:x+=1
    for i in range(steps):
        t2=x*x-n;y=math.isqrt(t2)
        if y*y==t2:
            d=x-y
            if 1<d<n and n%d==0:
                return {'factor_found':True,'factor':str(d),'steps':i+1,'elapsed_seconds':round(time.perf_counter()-t,6)}
        x+=1
    return {'factor_found':False,'factor':None,'steps':steps,'elapsed_seconds':round(time.perf_counter()-t,6)}


def rho(n,steps,seed):
    t=time.perf_counter()
    x=y=seed
    for i in range(steps):
        x=(x*x+1)%n
        y=(y*y+1)%n;y=(y*y+1)%n
        d=math.gcd(abs(x-y),n)
        if 1<d<n:
            return {'factor_found':True,'factor':str(d),'steps':i+1,'elapsed_seconds':round(time.perf_counter()-t,6)}
        if d==n:
            return {'factor_found':False,'factor':None,'steps':i+1,'elapsed_seconds':round(time.perf_counter()-t,6),'note':'cycle collision; no restarts'}
    return {'factor_found':False,'factor':None,'steps':steps,'elapsed_seconds':round(time.perf_counter()-t,6)}


def siqs_job(n,bound,M,seed,queue):
    from sympy.ntheory import qs
    try:
        t=time.perf_counter()
        f=qs(n,bound,M,seed=seed)
        queue.put({'factor_found':len(f)>1,'factors':[str(v) for v in sorted(f)],
                   'elapsed_seconds':round(time.perf_counter()-t,6)})
    except Exception as e:
        queue.put({'factor_found':False,'error':repr(e)})


def strong_siqs(n,par):
    # Spawn a clean process; timeout is a hard wall budget including setup.
    t=time.perf_counter()
    queue=mp.Queue()
    proc=mp.Process(target=siqs_job,args=(n,par['siqs_prime_bound'],par['siqs_interval'],par['siqs_seed'],queue))
    proc.start()
    proc.join(par['siqs_wall_timeout_seconds'])
    if proc.is_alive():
        proc.terminate();proc.join(3)
        return {'factor_found':False,'status':'TIMEOUT','elapsed_seconds':round(time.perf_counter()-t,6)}
    if queue.empty():
        return {'factor_found':False,'status':f'NO_RESULT_EXIT_{proc.exitcode}',
                'elapsed_seconds':round(time.perf_counter()-t,6)}
    out=queue.get_nowait()
    out['end_to_end_seconds']=round(time.perf_counter()-t,6)
    return out


def verify_result(n,result):
    if not result['factor_found']:return False
    w=result['witness']; d=int(w['factor']);other=int(w['cofactor']);
    x=int(w['square_x_mod_n']);y=int(w['square_y_mod_n'])
    return 1<d<n and d*other==n and (x*x-y*y)%n==0 and (
        math.gcd(x-y,n)==d or math.gcd(x+y,n)==d)


def one_case(record,par):
    n=int(record['n'])
    assert n.bit_length()==record['bits'] and n%2==1
    primes=factor_base(n,par['factor_base_prime_max'])
    arms={}
    for arm in ('A','B'):
        r=run_arm(n,primes,record['id'],arm,par['candidate_limit'],par['large_cofactor_max'])
        assert not r['factor_found'] or verify_result(n,r)
        arms[arm]=r
    controls={
        'fermat':fermat(n,par['fermat_max_steps']),
        'rho':rho(n,par['pollard_max_steps'],par['pollard_seed']),
        'siqs':strong_siqs(n,par)
    }
    for k,v in controls.items():
        if v['factor_found']:
            if k=='siqs':
                assert math.prod(map(int,v['factors']))==n and len(v['factors'])==2
            else:
                f=int(v['factor']);assert 1<f<n and n%f==0
    return {'case_id':record['id'],'split':record['split'],'bits':record['bits'],
            'n':record['n'],'factor_commitment_sha256':record['factor_pair_sha256'],
            'factor_base_size':len(primes),'arms':arms,'controls':controls}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--split',choices=['calibration','heldout','all'],required=True)
    p.add_argument('--limit',type=int,default=0,help='only for diagnostic calibration; avoid on heldout')
    args=p.parse_args()
    protocol=json.loads((ROOT/'protocol.json').read_text())
    par=protocol['params'].copy()
    if args.limit: par['candidate_limit']=args.limit
    tests=[r for r in protocol['target_records'] if args.split=='all' or r['split']==args.split]
    report={'epistemic_status':'LOCAL_EXECUTED_NOT_NOVEL', 'freeze_version':protocol['freeze_version'],
            'declared_protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
            'split':args.split,'parameters':par,'sympy_version':__import__('sympy').__version__,'results':[]}
    for case in tests:
        start=time.perf_counter()
        r=one_case(case,par)
        report['results'].append(r)
        print(f"{case['id']} nbits={case['bits']} A={r['arms']['A']['charge']['candidates_examined']} success={r['arms']['A']['factor_found']} B={r['arms']['B']['charge']['candidates_examined']} success={r['arms']['B']['factor_found']} SIQS={r['controls']['siqs']['factor_found']} rho={r['controls']['rho']['factor_found']} dt={time.perf_counter()-start:.2f}s",flush=True)
    path=ROOT/f'results_{args.split}.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(f'RESULT {path}',flush=True)


if __name__=='__main__':main()
