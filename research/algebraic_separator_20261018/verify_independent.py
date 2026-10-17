#!/usr/bin/env python3
"""Standalone audit; no calls to experiment.py or its implementation.

Reads only frozen moduli and emitted result files. Rechecks modular witnesses,
nontrivial gcds, actual product, probable primality, and original factor hashes.
"""
from pathlib import Path
from hashlib import sha256
from math import gcd, prod
import json
from sympy import isprime

base=Path(__file__).resolve().parent
manifest=json.loads((base/'protocol.json').read_text())
records={r['id']:r for r in manifest['target_records']}


def fact_pair(n, f):
    assert isinstance(f, int) and 1<f<n and n%f==0
    pair=tuple(sorted((f,n//f)))
    assert all(isprime(z) for z in pair),f'not a semiprime {pair}'
    return pair


def pair_hash(pair):
    return sha256(f'{pair[0]}:{pair[1]}'.encode()).hexdigest()


def audit(results):
    counts={'cases_checked':0,'siqs_success':0,'rho_success':0,'fermat_success':0,'A_success':0,'B_success':0,'valid_nontrivial_idempotents':0,'negative_controls_passed':0,'committed_factor_pair_hashes_matched':0}
    unique=set()
    for row in results['results']:
        ref=records[row['case_id']];assert row['case_id'] not in unique
        unique.add(row['case_id']);assert row['n']==ref['n'] and row['bits']==ref['bits']
        n=int(row['n']);assert n.bit_length()==ref['bits']
        siqs=row['controls']['siqs'];assert siqs['factor_found'],f"SIQS miss on {row['case_id']}"
        f=tuple(sorted(int(z) for z in siqs['factors']))
        assert len(f)==2 and prod(f)==n and all(isprime(x) for x in f)
        assert pair_hash(f)==ref['factor_pair_sha256']
        counts['siqs_success']+=1;counts['committed_factor_pair_hashes_matched']+=1
        for method in ('rho','fermat'):
            record=row['controls'][method]
            counts[method+'_success']+=int(record['factor_found'])
            if record['factor_found']:
                assert fact_pair(n,int(record['factor']))==f
        for arm in ('A','B'):
            record=row['arms'][arm];charge=record['charge']
            assert 1 <= charge['candidates_examined'] <= manifest['params']['candidate_limit']
            assert record['dependences_tested'] >= record['trivial_dependences']
            counts[arm+'_success']+=int(record['factor_found'])
            if not record['factor_found']:
                assert record['witness'] is None
                assert charge['candidates_examined']==manifest['params']['candidate_limit']
                continue
            w=record['witness'];x=int(w['square_x_mod_n']);y=int(w['square_y_mod_n'])
            d=int(w['factor']);e=int(w['cofactor'])
            assert (x*x-y*y)%n==0
            assert w['candidate_number']==charge['candidates_examined']
            assert fact_pair(n,d)==f and d*e==n
            g_minus,g_plus=gcd(x-y,n),gcd(x+y,n)
            assert d in (g_minus,g_plus)
            if gcd(x+y,n) not in (1,n) and gcd(x-y,n) not in (1,n):
                inv=pow((2*y)%n,-1,n) if gcd(2*y,n)==1 else None
                if inv is not None:
                    t=((x+y)*inv)%n
                    assert (t*t-t)%n==0 and t not in (0,1)
                    counts['valid_nontrivial_idempotents']+=1
            assert (x*x-((y+1)*(y+1)))%n !=0
            counts['negative_controls_passed']+=1
        counts['cases_checked']+=1
    return counts


def main():
    all_reports={}
    for split in ('calibration','heldout'):
        s=json.loads((base/f'results_{split}.json').read_text())
        assert s['split']==split and s['parameters']==manifest['params']
        assert [r['case_id'] for r in s['results']]==[r['id'] for r in manifest['target_records'] if r['split']==split]
        all_reports[split]=audit(s)
    out={'status':'WARRANTED_LOCAL_INDEPENDENT_REPLAY_OF_REPORTS','checker':'standalone sympy and math.gcd, source-disjoint from solver','counts':all_reports}
    (base/'independent_verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
