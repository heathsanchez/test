"""V162 exact negative control: 3n+7, not the Collatz conjecture.

The actual 3n+1 shortcut T and synthetic 3n+7 shortcut G share:
 * even n -> n/2;
 * odd source-affine slope 3;
 * odd output residue 2 mod3;
 * exact 3|G^k(n) iff 3*2^k|n;
 * source affine lift slope 3^oddCount over every length-k binary cylinder;
 * exact realizability of every finite future parity word.

Yet G has distinct actual positive periodic orbits 7->14->7
and 5->11->20->10->5. Thus that entire structural list is NOT
enough to guarantee unique positive future class.

No proof or counterexample to ACTUAL 3n+1 Collatz is claimed.
"""
from __future__ import annotations
import json
from collections import Counter

def G(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+7)//2

def T(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2

def trace(n,k,F):
    parity=[]
    for _ in range(k):
        parity.append(n&1)
        n=F(n)
    return n,tuple(parity)

def cycle(n,F,cap=10000,steps=15000):
    seen={}
    x=n
    for j in range(steps):
        if x in seen:
            path=list(seen.keys())
            return path[seen[x]:],True
        if x>cap:
            return [],False
        seen[x]=j
        x=F(x)
    return [],False

def finite_prefix_mixing(k,h,F):
    assert k>=0 and h>=0
    for r in range(1<<k):
        patterns=set()
        for q in range(1<<h):
            n=r+(q<<k)
            x,_=trace(n,k,F)
            _,suffix=trace(x,h,F)
            assert suffix not in patterns,(F.__name__,k,h,r,q)
            patterns.add(suffix)
        assert len(patterns)==1<<h
    return (1<<(k+h))

def main():
    assert G(1)==5 and G(7)==14 and G(14)==7
    assert (G(5),G(11),G(20),G(10))==(11,20,10,5)
    assert 1 not in {7,14} and {7,14}.isdisjoint({5,11,20,10})
    assert all(G(n)==n//2 for n in range(0,100000,2))
    assert all(G(n)%3==2 for n in range(1,100000,2))

    mod3_cases=0
    affine_cases=0
    for k in range(0,20):
        for n in range(0,5000):
            x,parity=trace(n,k,G)
            assert (x%3==0) == (n%(3*(1<<k))==0),(k,n,x)
            mod3_cases+=1
        for r in range(0,100):
            endpoint,parity=trace(r,k,G)
            a=sum(parity)
            for q in (0,1,2,3,7,17,89,1024):
                x,_=trace(r+(1<<k)*q,k,G)
                assert x==endpoint+3**a*q,(r,k,q,x,endpoint)
                affine_cases+=1

    prefix_cases=0
    checked_sources=0
    for k in range(0,8):
        for h in range(0,8):
            for F in (T,G):
                checked_sources+=finite_prefix_mixing(k,h,F)
                prefix_cases+=(1<<k)
    assert prefix_cases==2*8*(2**8-1)
    assert checked_sources==2*(2**8-1)**2

    # Actual-orbit cycle checks in the non-Collatz synthetic map.
    cycleA=[7,14]
    cycleB=[5,11,20,10]
    assert [G(x) for x in cycleA]==[14,7]
    assert [G(x) for x in cycleB]==[11,20,10,5]

    # Bounded illustration of how both distinct cycles attract many
    # sources. These fractions are FINITE and not asymptotic warrants.
    inA,inB=0,0
    resolved={}
    for n in range(1,1<<15):
        x=n
        path=[]
        while x not in resolved and x not in cycleA and x not in cycleB:
            path.append(x)
            x=G(x)
            assert x<1<<28,(n,x)
            assert len(path)<100000,(n,x)
        root='A' if x in cycleA else 'B' if x in cycleB else resolved[x]
        for y in path:
            resolved[y]=root
        resolved[n]=root
        if root=='A':inA+=1
        else:inB+=1
    assert inA>0 and inB>0 and inA+inB==(1<<15)-1

    return {
      'schema':'COLLATZ_V162_THREE_N_PLUS_SEVEN_EXACT_ADVERSARIAL',
      'synthetic_map':'G(even)=n/2; G(odd)=(3*n+7)/2',
      'genuine_collatz_is_separate_map':True,
      'odd_step_residue_two_mod_three_verified':True,
      'same_even_branch':True,
      'same_ternary_all_depth_sieve_verified_up_to_k':19,
      'ternary_source_depth_checks':mod3_cases,
      'same_source_affine_slope_3_oddcount_verified':True,
      'affine_cases':affine_cases,
      'all_finite_parity_word_permutations_pass_for_both_maps':True,
      'finite_prefix_cases':prefix_cases,
      'finite_source_instances':checked_sources,
      'cycle_A':[7,14],
      'cycle_B':[5,11,20,10],
      'two_disjoint_real_positive_periodic_classes':True,
      'tested_basin_sources':(1<<15)-1,
      'finite_cycle_A_basin_count':inA,
      'finite_cycle_B_basin_count':inB,
      'basin_density_unbounded_theorem_proved':False,
      'actual_collatz_global_convergence_proved':False,
      'qed':False,'global_collatz':'UNKNOWN',
      'adversarial_conclusion':'Same exact ternary sieve and all finite parity mixing permit distinct cycles when odd intercept changes from +1 to +7.'
    }

if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
