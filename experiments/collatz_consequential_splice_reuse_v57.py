"""Trace one exit collision, erase incidental coordinates, reuse its warrant.

No new residue feature is admitted. The only universal claim is the explicit
dyadic exit theorem checked separately by Lean. Full Collatz remains unknown.
"""
import hashlib
import json
import collatz_crystal_parameter_quotient_v25 as bank

BASE = 188790896379371192347
LOWER = 69989685430801362591
DEPTH = 69
MODULUS = 2**DEPTH
FRONTIER = [132,388,68,196,452,12,268,332,204,460,300,172,428,28,284,412,
            220,476,2,258,130,386,66,322,194,450,18,274,82,338,466,114,
            370,242,498,346,218,474,58,314,186,442,122,378,250,506,14,270,
            142,398,78,334,206,462,46,302,430,30,158,414,94,350,9,265]

def orbit(n,k):
    q=0
    for _ in range(k):
        q+=n%2
        n=(3*n+1)//2 if n%2 else n//2
    return n,q

def applies(d,r):
    n=bank.N0+bank.NC*r
    s=bank.NC*2**d
    return n%MODULUS==BASE and s%MODULUS==0

def main():
    collisions=[]
    for r in (644,900):
        n=bank.N0+bank.NC*r;s=bank.NC*1024
        pref=bank.fixed_prefix(n,s)
        j,z,c,q=pref[66]
        old=bank.classify_cell(10,r)
        collisions.append(dict(r=r,endpoint_mod8=z%8,endpoint_slope_mod8=c%8,
            quarter_owner_intercept=(z-1)//4,quarter_owner_slope=c//4,
            below_source=(z-1)//4<n and c//4<=s,
            terminal=old['terminal'],exit=old.get('exit')))
    assert collisions[0]['endpoint_mod8']==5 and collisions[0]['terminal']
    assert collisions[1]['endpoint_mod8']==7 and not collisions[1]['terminal']
    assert all(x['below_source'] for x in collisions)
    # Exact owner-lift admission, before any size comparison. A floor quotient
    # is not an owner when (endpoint-1) is not divisible by four.
    assert collisions[0]['endpoint_mod8']==5
    assert collisions[1]['endpoint_mod8']%4!=1

    assert orbit(BASE,66)==(4*LOWER+1,42)
    assert orbit(BASE,69)==((3*LOWER+1)//2,43)
    assert 0<LOWER<BASE and LOWER%2==1
    assert 2*3**42<=MODULUS
    replays=[]
    for u in (0,1,3,8,27,81,243):
        n=BASE+MODULUS*u;p=LOWER+2*3**42*u
        common,_=orbit(n,69)
        assert 0<p<n and orbit(p,1)[0]==common
        replays.append(dict(u=u,n=str(n),lower=str(p),source_mod3=n%3))
    assert any(x['source_mod3']!=0 for x in replays)

    # Minimality relative to this fixed 66-step/quarter-splice mechanism.
    z0,_=orbit(BASE,66);z1,_=orbit(BASE+2**68,66)
    assert z0%8==5 and z1%8==1
    # Both share their 66-step parity word; the missing bit flips owner parity.
    assert orbit(BASE,66)[1]==orbit(BASE+2**68,66)[1]==42

    closed=remaining=matched=new=0
    for r in FRONTIER:
        for bit in (0,1):
            child=r+bit*512
            old=bank.classify_cell(10,child)
            hit=applies(10,child)
            matched+=hit
            new+=hit and not old['terminal']
            closed+=old['terminal'] or hit
            remaining+=not (old['terminal'] or hit)
    assert (matched,new,closed,remaining)==(1,0,13,115)

    result=dict(schema='COLLATZ_CONSEQUENTIAL_SPLICE_REUSE_V57',
        collision=collisions,
        distinguishing_guard='endpoint at step 66 is exactly 4*p+1 with p odd (5 mod 8)',
        warrant='ordinary_exit_of_source_cylinder_odd_merge',
        compiled_theorem='collision_splice_dyadic_exit',
        removed_incidental_coordinates=['owner phase id','parameter mod 3^k','source factor 3^8'],
        dyadic_class=dict(base=str(BASE),modulus=str(MODULUS),depth=69),
        universal_law_scope='all natural u in BASE + 2^69*u; Lean checked separately',
        fixed_macro_minimum_dyadic_depth=69,
        neighbor=dict(depth=68,endpoint_mod8=[z0%8,z1%8]),
        replays=replays,source_family_expansion_factor=3**8,
        frozen_child_reclosure=dict(input=128,matched=matched,new_closures=new,
            closed=closed,remaining=remaining),
        earlier_3adic_necessity_claim='WITHDRAWN: one exact collision is explained by an existing dyadic splice guard',
        status='EXISTING_WARRANT_REUSED_ON_LARGER_UNIVERSAL_DYADIC_CLASS',
        global_collatz='UNKNOWN')
    result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
