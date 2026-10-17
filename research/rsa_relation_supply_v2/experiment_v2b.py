#!/usr/bin/env python3
"""Post-hoc unbiassed timing calibration of source-pinned ablation of exact p-adic sieve and symmetric relation supply.

Proof scope: exact modular-root divisibility results only. All techniques
are standard quadratic-sieve mathematics. Original predecessor GF2 verifier
and independently executed SIQS are reused from source at ../algebraic_separator_20261018.
"""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
from collections import defaultdict
from sympy.ntheory.residue_ntheory import sqrt_mod
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'algebraic_separator_20261018'))
import experiment as original


def xstream(n, count, side):
    s=math.isqrt(n);s += s*s<n
    if side=='forward':
        return [s+i for i in range(count)]
    if side=='symmetric':
        return [s] + [s-(i+1)//2 if i%2 else s+i//2 for i in range(1,count)]
    raise ValueError(side)


def exact_root_sieve(n,base, xs):
    """Return exact divisor exponents and quotient for *all* candidate x.

    Mark all residue classes for x^2=n mod p^k. Hensel lifting for odd p,
    exhaustive binary lift for p=2. No logarithmic approximations or
    probabilistic omission. Charge all setup and modular marks.
    """
    start=time.perf_counter()
    lo,hi=min(xs),max(xs)
    size=hi-lo+1
    products=[1]*size
    exps=[{} for _ in range(size)]
    maxabs=max(abs(lo*lo-n),abs(hi*hi-n))
    count_marks=0;power_roots=0
    for p in base:
        roots=[1] if p==2 else [int(z) for z in sqrt_mod(n,p,all_roots=True)]
        assert roots and all((r*r-n)%p==0 for r in roots)
        pk=p
        while pk<=maxabs and roots:
            power_roots+=len(roots)
            for r in roots:
                pos=(r-lo)%pk
                for i in range(pos,size,pk):
                    exps[i][p]=exps[i].get(p,0)+1
                    products[i]*=p
                    count_marks+=1
            # Lift actual roots modulo p^k to modulo p^(k+1).
            new_mod=pk*p
            if new_mod>maxabs:break
            if p==2:
                roots=sorted({(r+t*pk)%new_mod for r in roots for t in (0,1)
                              if ((r+t*pk)**2-n)%new_mod==0})
            else:
                lifted=[]
                for r in roots:
                    assert (n-r*r)%pk==0
                    t=((n-r*r)//pk * pow((2*r)%p,-1,p))%p
                    lifted.append((r+t*pk)%new_mod)
                roots=sorted(set(lifted))
            pk=new_mod
    results=[]
    for x in xs:
        i=x-lo;q=x*x-n
        assert q!=0 and abs(q)%products[i]==0
        rem=abs(q)//products[i]
        ev=exps[i]
        if q<0:ev={**ev,-1:1}
        results.append((ev,rem))
    return results,dict(elapsed_seconds=round(time.perf_counter()-start,6),
         modular_marks=count_marks,modular_power_roots=power_roots,
         candidate_residue_quotients=len(xs),range_len=size)


def process(n,base,side,mode,limit,large):
    t=time.perf_counter()
    xs=xstream(n,limit,side)
    sieve_rows,sieve_cost=(exact_root_sieve(n,base,xs) if mode=='root-sieve'
                           else (None,{}))
    basis=original.Basis(n,[-1]+base)
    partials={}
    stats={'smooth':0,'partial_observed':0,'matched_pairs':0,'retained_relations':0,
           'modular_trial_checks':0,'tried_candidates':limit,
           'basis_max_rank':0,'factor_first_candidate':None,'factor':None}
    h=hashlib.sha256()
    verify_controls=0
    for i,x in enumerate(xs):
        q=x*x-n
        if sieve_rows is not None:
            exps, rem=sieve_rows[i]
        else:
            cost={'modular_divisions':0}
            exps, rem=original.q_factor(abs(q),base,cost)
            stats['modular_trial_checks']+=cost['modular_divisions']
            if q<0:exps={**exps,-1:1}
        # Strong full equality audit on first 250 candidates + periodic heldout slots;
        # separate exhaustive stream membership hashes are compared by process pairs.
        if mode=='root-sieve' and (i<250 or i%997==0):
            e0,rem0=original.q_factor(abs(q),base,{'modular_divisions':0})
            if q<0:e0[-1]=1
            assert e0==exps and rem0==rem
            verify_controls+=1
        h.update((str(rem)+'/'+str(sorted(exps.items()))+';').encode())
        if rem==1:
            stats['smooth']+=1
            relation={'x':x,'exps':exps,'origin':(i,)}
        elif 1<rem<=large:
            stats['partial_observed']+=1
            current={'x':x,'exps':exps,'origin':(i,)}
            if rem not in partials:
                partials[rem]=current
                continue
            relation=original.combine(partials[rem],current,rem)
            stats['matched_pairs']+=1
        else:
            continue
        stats['retained_relations']+=1
        if stats['factor'] is None:
            witness=basis.admit(relation,'pilot-v2',i+1)
            if witness:
                stats['factor_first_candidate']=i+1
                stats['factor']=witness
        stats['basis_max_rank']=max(stats['basis_max_rank'],len(basis.pivots))
    stats['relation_stream_sha256']=h.hexdigest()
    stats['sampled_classification_controls']=verify_controls
    stats.update(sieve_cost)
    stats['elapsed_total_seconds']=round(time.perf_counter()-t,6)
    return stats


def case(rec,par):
    n=int(rec['n']); assert n.bit_length()==rec['bits_actual']
    base=original.factor_base(n,par['factor_base_bound'])
    L=par['candidates_per_arm'];large=par['large_cofactor_bound']
    runs={}
    for side in ('forward','symmetric'):
        for mode in ('trial','root-sieve'):
            key=side+'_'+mode
            runs[key]=process(n,base,side,mode,L,large)
            print(rec['id'],key,'rows',runs[key]['retained_relations'],
                  'first_factor',runs[key]['factor_first_candidate'],
                  'time',runs[key]['elapsed_total_seconds'],flush=True)
        a=runs[side+'_trial'];b=runs[side+'_root-sieve']
        assert a['relation_stream_sha256']==b['relation_stream_sha256'], 'exact sieve mismatch'
        assert (a['smooth'],a['matched_pairs'],a['retained_relations'],a['factor_first_candidate'])==(
             b['smooth'],b['matched_pairs'],b['retained_relations'],b['factor_first_candidate']), 'sequential producer mismatch'
    old_si=original.strong_siqs(n,{'siqs_prime_bound':par['siqs_prime_bound'],'siqs_interval':par['siqs_interval'],
      'siqs_seed':par['siqs_seed'],'siqs_wall_timeout_seconds':par['siqs_timeout_seconds']})
    if old_si['factor_found']:
        factors=sorted(map(int,old_si['factors']))
        assert factors[0]*factors[1]==n
        assert hashlib.sha256(f'{factors[0]}:{factors[1]}'.encode()).hexdigest()==rec['factor_pair_sha256']
    print(rec['id'],'SIQS',old_si['factor_found'],old_si.get('end_to_end_seconds'),flush=True)
    return dict(id=rec['id'],split=rec['split'],n=rec['n'],bits=rec['bits_actual'],
                factor_hash=rec['factor_pair_sha256'],factor_base_len=len(base),
                arms=runs,siqs=old_si)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=('calibration','heldout'),required=True)
    args=parser.parse_args()
    manifest=json.loads((ROOT/'frozen_manifest.json').read_text())
    results={'split':args.split,'freeze_sha256':hashlib.sha256((ROOT/'frozen_manifest.json').read_bytes()).hexdigest(),
             'method_authority':'PRIOR_ART','params':manifest['params'],'cases':[]}
    for rec in manifest['target_records']:
        if rec['split']==args.split:
            results['cases'].append(case(rec,manifest['params']))
    dest=ROOT/('results_v2b_'+args.split+'.json')
    dest.write_text(json.dumps(results,indent=2)+'\n')
    print('DONE',str(dest),flush=True)

if __name__=='__main__': main()
