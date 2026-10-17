#!/usr/bin/env python3
"""Independent v2 relation oracle with no imports from producing module.

Exhaustively recomputes factor-base classifications, ordered relation stream
hashes, partial pair matching, factor/product/multiplicative certificates, and
counters over the pre-committed calibration + eight heldout numbers.
"""
import hashlib, json, math
from pathlib import Path
from sympy import primerange, isprime
ROOT=Path(__file__).resolve().parent

def oracle(n,side,limit,prime_limit,cofactor_limit):
    primes=[2]+[int(p) for p in primerange(3,prime_limit+1) if pow(n%int(p),(int(p)-1)//2,int(p))==1]
    assert all(n%p for p in primes)
    start=math.isqrt(n)
    if start*start<n:start+=1
    digest=hashlib.sha256(); partials=set()
    count_smooth=0;count_pair=0;rank=0
    for offset in range(limit):
        if side=='forward':x=start+offset
        else:x=(start if offset==0 else start-((offset+1)//2) if offset%2 else start+offset//2)
        q=x*x-n
        assert q!=0
        remainder=abs(q)
        exps={-1:1} if q<0 else {}
        for p in primes:
            if remainder%p==0:
                e=0
                while remainder%p==0:
                    e+=1;remainder//=p
                exps[p]=e
            if remainder==1:break
        digest.update((str(remainder)+'/'+str(sorted(exps.items()))+';').encode())
        if remainder==1:count_smooth+=1
        elif 1<remainder<=cofactor_limit:
            if remainder in partials:count_pair+=1
            else:partials.add(remainder)
    return {'stream_sha256':digest.hexdigest(),'smooth':count_smooth,
            'matched_pairs':count_pair,'retained':count_smooth+count_pair,'factor_base_size':len(primes)}

def main():
    manifest=json.loads((ROOT/'frozen_manifest.json').read_text())
    byid={r['id']:r for r in manifest['target_records']}
    assert len(byid)==11 and {r['split'] for r in byid.values()}=={'calibration','heldout'}
    counts={'calibration':{'cases':0,'forward_success':0,'sym_success':0,'siqs_success':0,'sym_relation_gain':0},
            'heldout':{'cases':0,'forward_success':0,'sym_success':0,'siqs_success':0,'sym_relation_gain':0}}
    checked=0;tampered=0;hash_checks=0
    audit_details=[]
    for split in ('calibration','heldout'):
        report=json.loads((ROOT/f'results_{split}.json').read_text())
        assert report['split']==split
        assert report['params']==manifest['params']
        assert report['freeze_sha256']==hashlib.sha256((ROOT/'frozen_manifest.json').read_bytes()).hexdigest()
        assert [v['id'] for v in report['cases']]==[v['id'] for v in manifest['target_records'] if v['split']==split]
        for result in report['cases']:
            ref=byid[result['id']];n=int(ref['n']);assert n.bit_length()==ref['bits_actual']
            siqs=result['siqs'];assert siqs['factor_found'], f"SIQS failed {ref['id']}"
            factors=tuple(sorted(map(int,siqs['factors'])))
            assert len(factors)==2 and math.prod(factors)==n
            assert all(isprime(f) for f in factors)
            assert hashlib.sha256(f'{factors[0]}:{factors[1]}'.encode()).hexdigest()==ref['factor_pair_sha256']
            hash_checks+=1
            one={}
            for side in ('forward','symmetric'):
                independent=oracle(n,side,manifest['params']['candidates_per_arm'],
                                   manifest['params']['factor_base_bound'],
                                   manifest['params']['large_cofactor_bound'])
                one[side]=independent
                for mode in ('trial','root-sieve'):
                    s=result['arms'][side+'_'+mode]
                    assert s['relation_stream_sha256']==independent['stream_sha256'],(ref['id'],side,mode,'stream diverged')
                    assert s['smooth']==independent['smooth']
                    assert s['matched_pairs']==independent['matched_pairs']
                    assert s['retained_relations']==independent['retained']
                assert independent['factor_base_size']==result['factor_base_len']
                w=result['arms'][side+'_trial']['factor']
                if w:
                    xx=int(w['square_x_mod_n']);yy=int(w['square_y_mod_n']);d=int(w['factor']);other=int(w['cofactor'])
                    assert (xx*xx-yy*yy)%n==0
                    assert 1<d<n and d*other==n and tuple(sorted((d,other)))==factors
                    assert d in (math.gcd(xx-yy,n),math.gcd(xx+yy,n))
                    assert w==result['arms'][side+'_root-sieve']['factor']
                    assert (xx*xx-(yy+1)*(yy+1))%n!=0
                    tampered+=1
                    # Explicitly construct a nontrivial idempotent if 2y is a unit.
                    if math.gcd(2*yy,n)==1:
                        e=((xx+yy)*pow(2*yy,-1,n))%n
                        assert (e*e-e)%n==0 and e not in (0,1)
                    checked+=1
            z=counts[split];z['cases']+=1
            z['forward_success']+=int(result['arms']['forward_trial']['factor'] is not None)
            z['sym_success']+=int(result['arms']['symmetric_trial']['factor'] is not None)
            z['siqs_success']+=1
            z['sym_relation_gain']+=int(one['symmetric']['retained']>one['forward']['retained'])
            audit_details.append({'id':ref['id'],'split':split,'rows_forward':one['forward']['retained'],
                                  'rows_symmetric':one['symmetric']['retained'],
                                  'delta':one['symmetric']['retained']-one['forward']['retained']})
            print('AUDITED',ref['id'],'rows',one['forward']['retained'],one['symmetric']['retained'],flush=True)
    assert counts['calibration']['cases']==3 and counts['heldout']['cases']==8
    assert tampered>=1
    outcome={'status':'WARRANTED_LOCAL_INDEPENDENT_EXHAUSTIVE_CANDIDATE_AUDIT',
             'authority':'Standalone independent primality/product/stream/certificate checks, no importing producer',
             'samples':counts,'checked_factor_witnesses':checked,'tampered_controls_rejected':tampered,
             'precommitted_SIQS_factor_pairs_checked':hash_checks,'row_deltas':audit_details,
             'limitation':'Synthetic inputs, standard QS prior art, not a new factoring algorithm; speed results require unbiased dedicated control.'}
    (ROOT/'audit_independent.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print('INDEPENDENT VERIFIED',json.dumps(counts),flush=True)

if __name__=='__main__':main()
