"""Adapt V59's retained origin query into a cheaper consequence guard.

This enables a new portion of the same live residual, not a universal bar.
"""
import hashlib
import json
from math import gcd
import collatz_crystal_parameter_quotient_v25 as bank
from collatz_consequential_splice_reuse_v57 import orbit, FRONTIER
from collatz_live_splice_guard_v58 import compiled_exit as old_exit
from collatz_protected_query_adapter_v59 import ProtectedQuery
import collatz_owner_renewal_affine_v0 as owner
from collatz_crystal_owner_cylinder_reclosure_v54 import symbolic_block

BASE=926660659327753256987
LOWER=772958606084060086381
MODULUS=2**71

def compiled_exit(n,enabled=True):
    if not enabled or n<BASE or (n-BASE)%MODULUS:
        return None
    v=(n-BASE)//MODULUS
    return dict(theorem='composed_seam_guard_exit',source=str(n),
        lower=str(LOWER+2*3**44*v),common_step=71)

def main():
    n0=bank.N0+bank.NC*900;s=bank.NC*1024
    a,c=n0,s
    for _ in range(4):
        b=symbolic_block(a,c);assert not b['split']
        a,c=b['owner0'],b['owner_slope']
    seam=symbolic_block(a,c);assert seam['split']
    z0,zs=seam['at0'],seam['slope']
    assert (z0,zs)==(11357500336601373755463455,12922163778453346597864482)
    assert z0<4*n0 and zs<=4*s
    assert (z0%8,zs%8)==(7,2)
    assert (z0+3*zs)%8==5
    assert orbit(BASE,68)==(4*LOWER+1,44)
    assert orbit(BASE,71)==(1159437909126090129572,45)
    assert orbit(LOWER,1)[0]==orbit(BASE,71)[0]
    assert 0<LOWER<BASE and LOWER%2==1 and 2*3**44<=MODULUS
    assert orbit(BASE+2**70,68)==(4*LOWER+1+4*3**44,44)
    assert orbit(BASE+2**70,68)[0]%8==1

    # Exact guard equivalence follows from an odd coefficient modulo four.
    assert s==2**69*3**8 and 3**8%4==1
    assert (n0+3*s)%MODULUS==BASE
    queries=[]
    for u in (0,1,2,3,7,11,65539):
        n=n0+s*u;hit=compiled_exit(n)
        assert bool(hit)==(u%4==3)
        assert compiled_exit(n,enabled=False) is None
        baseline=old_exit(10,900,u)
        if hit:
            assert baseline is None
            p=int(hit['lower'])
            assert 0<p<n and orbit(n,71)[0]==orbit(p,1)[0]
            # Execute existing composed-query adapter on the earned family.
            q=ProtectedQuery(n,n)
            for _ in range(5):q=q.extend(owner.renewal_block(q.current))
            assert q.decision()=='LOWER_SOURCE_EXIT'
        queries.append(dict(u=u,old='EXIT' if baseline else 'UNKNOWN',
            new='EXIT' if hit or baseline else 'UNKNOWN',
            new_rule_disabled='EXIT' if baseline else 'UNKNOWN'))

    # Coverage is exact arithmetic in this cell, not statistical sampling.
    # Old guard u=0 mod 2^14 and new guard u=3 mod4 are disjoint.
    assert all(not (u%16384==0 and u%4==3) for u in range(16384))
    covered=sum(u%16384==0 or u%4==3 for u in range(16384))
    assert covered==4097
    # Propagate the newly compiled consequence to every frozen child key.
    # No repeated bank search is needed to decide cylinder intersection.
    matched=[];whole=[]
    for r in FRONTIER:
        for bit in (0,1):
            child=r+512*bit
            compatible=(bank.N0+bank.NC*child-BASE)%gcd(s,MODULUS)==0
            if compatible:matched.append(child)
            if compatible and s%MODULUS==0:whole.append(child)
    assert matched==[900] and whole==[]
    result=dict(schema='COLLATZ_COMPOSED_SEAM_GUARD_V60',
        lineage=['V58 scoped guard','V59 original-source adapter and retained seam','V60 composed seam applicability'],
        universal_class=dict(base=str(BASE),modulus=str(MODULUS),lower=str(LOWER),lower_slope=str(2*3**44)),
        new_guard='u=3 modulo 4 in t=900+1024*u; equivalently t=3972 modulo 4096',
        consequence='quarter owner below the original source, common future at shortcut step 71',
        seam=dict(endpoint0=str(z0),endpoint_slope=str(zs),endpoint_mod8=[7,2],below_four_original_source=True),
        old_guard_parameter_bits=14,new_guard_parameter_bits=2,
        relative_fixed_word_minimum_source_bits=71,
        combined_cell_coverage=dict(numerator=4097,denominator=16384),
        remaining='u != 3 modulo 4 AND u != 0 modulo 16384',
        queries_and_ablation=queries,
        frozen_guard_propagation=dict(input_children=128,matched_children=matched,whole_children=whole),
        new_whole_live_cell_closures=len(whole),
        evidence_boundary='universal source cylinder Lean checked separately; exact guard coverage on one live cell; no eventual guard availability theorem',
        global_collatz='UNKNOWN')
    result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
