"""V189 independent exact source/clock inverse-height defect ledger.

Only the TRUE +1 shortcut is admitted. For every actual source n and
clock k, store the ONE scalar

  D(n,k) = 3^k*(n+1) - 2^k*(T^k(n)+1) >=0.

The exact recurrence is:
  D(n,k+1) = 3*D(n,k) + 2^k*E(T^k(n)),
  E(x)=2*x+1 if x even, otherwise 0.

Consequently every genuine two-clock source meeting obeys
  3^i*2^j*(n+1) <=3^j*2^i*(p+1)+2^j*D(n,i).

D(n,k)=0 exactly for the true all-odd prefix through k, as
independently checked in bounded arithmetic and implied by the
formal source exact recurrence.

This is a minimal CONSEQUENTIAL state for inverse HEIGHT comparisons.
It is not an all-source source-lower meeting existence theorem and
not global Collatz QED. The G5/G7 odd intercepts do not preserve the
exact +1 recurrence (negative controls).
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from hashlib import sha256
import json


def T(n: int,c: int=1)->int:
    assert n>=0 and c>0 and c%2==1
    return n//2 if n%2==0 else (3*n+c)//2


def E(x:int)->int:
    return (2*x+1) if x%2==0 else 0


def audit_sources()->tuple[dict,dict[int,list[tuple[int,int,int]]]]:
    tested=0
    even=0
    odd=0
    defect_positive=0
    src_minmax=[]
    endpoints=defaultdict(list)
    for n in range(0,3201):
        x=n
        d=0
        all_odd=True
        for k in range(56):
            assert d==3**k*(n+1)-2**k*(x+1)
            assert d>=0
            assert (d==0)==all_odd,(n,k,d,all_odd)
            if d>0:
                defect_positive+=1
            if k in (0,3,7,15,31,55) and n in (0,1,2,3,27,31,127,255,703,3199):
                src_minmax.append({'n':n,'k':k,'x':x,'D':str(d),'all_odd':all_odd})
            if len(endpoints[x])<12:
                endpoints[x].append((n,k,d))
            e=E(x)
            nxt=T(x)
            assert 2*(nxt+1)+e==3*(x+1)
            nxt_d=3*d+(2**k)*e
            assert nxt_d==3**(k+1)*(n+1)-2**(k+1)*(nxt+1)
            if x%2==0:
                even+=1
                all_odd=False
                assert e==2*x+1 and e>0
                assert nxt_d>0
            else:
                odd+=1
                assert e==0 and nxt_d==3*d
            x=nxt
            d=nxt_d
            tested+=1
    assert tested==3201*56
    assert even>0 and odd>0
    return {
      'source_cutoff_exclusive':3201,
      'actual_per_source_clock_steps':56,
      'source_clock_entries_checked':tested,
      'odd_steps':odd,'even_steps':even,
      'strictly_positive_defect_at_clock_entries':defect_positive,
      'sample_receipts':src_minmax,
    },endpoints


def audit_meetings(endpoint_map:dict[int,list[tuple[int,int,int]]])->dict:
    true_meetings=0
    zero_defect_meetings=0
    smaller_early_clock_attempts=0
    strict_negative_witness=0
    examples=[]
    for target,entries in endpoint_map.items():
        for n,i,d in entries:
            for p,j,_dp in entries:
                if true_meetings>=350000:
                    break
                assert 3**i*2**j*(n+1)<=(
                    3**j*2**i*(p+1)+2**j*d),(n,p,i,j,target,d)
                if d==0 and j<=i:
                    assert p>=n,(n,p,i,j,target)
                    zero_defect_meetings+=1
                if 0<p<n and j<=i:
                    smaller_early_clock_attempts+=1
                    assert d>0
                    if len(examples)<15:
                        examples.append({'n':n,'p':p,'i':i,'j':j,
                                         'genuine_endpoint':target,'source_defect':str(d)})
                if 0<p<n and j>i:
                    strict_negative_witness+=1
                true_meetings+=1
            if true_meetings>=350000:
                break
        if true_meetings>=350000:
            break
    assert true_meetings>100000
    assert smaller_early_clock_attempts>0
    assert zero_defect_meetings>0
    return {
      'independent_real_two_clock_meetings_checked':true_meetings,
      'zero_defect_at_earlier_companion_clock_cases':zero_defect_meetings,
      'nonzero_defect_necessary_for_smaller_earlier_clock_cases':smaller_early_clock_attempts,
      'later_clock_smaller_source_cases':strict_negative_witness,
      'sample_smaller_source_with_nonzero_slack':examples
    }


def mersenneworld()->dict:
    test_count=0
    for K in range(1,17):
        for q in (1,2,3,5,7,11):
            n=(1<<K)*q-1
            x=n
            d=0
            for k in range(K+1):
                assert x==(3**k)*(1<<(K-k))*q-1
                assert d==0
                if k<K:
                    assert x%2==1
                    d=3*d+2**k*E(x)
                    x=T(x)
                test_count+=1
    assert test_count>800
    return {
      'entire_all_odd_original_source_cylinder':
          'n=2^K*q-1, positive q,K; D(n,i)=0 for every i<=K',
      'bounded_source_cylinder_checks':test_count,
      'zero_defect_recovers_v188_early_clock_mersenne_barrier':True,
    }


def controls()->dict:
    for c in (5,7):
        assert 2*(T(1,c)+1)+E(1)!=3*(1+1)
    for x in range(0,900):
        assert 2*(T(x)+1)+E(x)==3*(x+1)
    return {
       'G5_and_G7_exact_odd_plus_one_slack_identity_fails':True,
       'true_plus_one_source_slack_one_step_checks':900,
       'any_generic_other_intercept_admission_requires_own_law':True
    }


def main()->None:
    sources,ep=audit_sources()
    meets=audit_meetings(ep)
    cylinder=mersenneworld()
    negative=controls()
    output={
      'schema':'COLLATZ_V189_MINIMUM_SOURCE_CLOCK_INVERSE_HEIGHT_DEFECT',
      'true_shortcut':'even n/2, odd (3n+1)/2',
      'exact_recurrence':'D(n,k+1)=3*D(n,k)+2^k*E(T^k(n))',
      'two_clock_budget':
         '3^i*2^j*(n+1) <=3^j*2^i*(p+1)+2^j*D(n,i) for genuine meeting',
      'actual_source_clock_audit':sources,
      'real_two_clock_meeting_audit':meets,
      'all_odd_source_cylinder_control':cylinder,
      'negative_controls':negative,
      'all_positive_original_source_convergence_claimed':False,
      'all_actual_two_clock_meeting_existence_claimed':False,
      'scope':'UNIVERSAL_EXACT_NECESSARY_SOURCE_CLOCK_CONSTRAINT_NOT_SUFFICIENT_FOR_CONVERGENCE',
      'global_collatz':'UNKNOWN','qed':False
    }
    Path('evidence').mkdir(exist_ok=True)
    p=Path('evidence/v189-defect.json')
    p.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
      'schema':output['schema'],
      'source_clock_entries_checked':sources['source_clock_entries_checked'],
      'two_clock_meetings_checked':meets['independent_real_two_clock_meetings_checked'],
      'zero_defect_clock_cases':meets['zero_defect_at_earlier_companion_clock_cases'],
      'global_collatz':'UNKNOWN'
    },sort_keys=True))


if __name__=='__main__':
    main()
