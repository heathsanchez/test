"""V160 exact finite audit of REAL source-locked dyadic target lifts.

For any original binary prefix r < 2^k:
 T^k(r + 2^k*q) = T^k(r) + 3^oddCount(r,k)*q.

For a target b coprime to 3, elementary primitive-root arithmetic
of 2 modulo 3^a chooses L such that the RIGHT side equals 2^L*b.
The resulting positive source n reaches b in k+L genuine shortcut steps,
and n is in the specified source residue r mod 2^k.

This FINITE audit independently checks the identity, modular orbit
coverage up to k=9, the source/clock transition witnesses, and the
adversarial Mersenne-family exponential-cost separator. Number-theory
surjectivity for ALL a is a documented elementary argument but is
NOT reified in the V160 Lean file. Neither this work nor the arithmetic
implies any density-one terminal certificate mass or Collatz QED.
"""
from __future__ import annotations
import json
from collections import Counter
from statistics import median


def shortcut(n: int) -> int:
    assert n >= 0
    return n // 2 if n%2==0 else (3*n+1)//2


def iter_shortcut(n: int,k:int)->int:
    for _ in range(k):
        n=shortcut(n)
    return n


def prefix(r: int,k:int):
    a=0
    x=r
    for _ in range(k):
        a+=x&1
        x=shortcut(x)
    return a,x


TABLES = {}

def pow2_primitive_log(a:int):
    if a in TABLES:
        return TABLES[a]
    modulus=3**a
    if modulus==1:
        ans=({0:0},1)
    else:
        seen={}
        cur=1
        while cur not in seen:
            seen[cur]=len(seen)
            cur=2*cur %modulus
        assert cur==1
        assert len(seen)==2*3**(a-1)
        assert len(seen)==modulus-modulus//3
        ans=(seen,len(seen))
    TABLES[a]=ans
    return ans


def least_power_lift(r:int,k:int,b:int):
    assert 0<=r<2**k and b>0 and b%3!=0
    a,g=prefix(r,k)
    modulus=3**a
    log,order=pow2_primitive_log(a)
    assert modulus==1 or g%3!=0
    desired=(g*pow(b,-1,modulus))%modulus if modulus>1 else 0
    L=log[desired]
    while (1<<L)*b < g:
        L+=order
    difference=(1<<L)*b-g
    assert difference%modulus==0
    q=difference//modulus
    n=r+(1<<k)*q
    assert n>0 and n%(1<<k)==r
    assert iter_shortcut(n,k)==(1<<L)*b
    # For a power-of-2 multiple, the next L actual transitions
    # are exact even halvings; audit all shorter test exponents by replay.
    if L<=100:
        assert iter_shortcut(n,k+L)==b
    return dict(L=L,source_bit_length=n.bit_length(),
        odd_prefix_count=a,source=n,coefficient=q,endpoint=g)


def main():
    targets=(1,2,5,7,11,13,17,19)
    depths=[]
    num_examples=0
    for k in range(1,10):
        exponents=[]
        all_classes=0
        worst=(0,0)
        for r in range(1<<k):
            a,g=prefix(r,k)
            assert g%3!=0 if 0<r else g==0
            log,_=pow2_primitive_log(a)
            for b in targets:
                witness=least_power_lift(r,k,b)
                num_examples+=1
                all_classes+=1
                if b==1:
                    exponents.append(witness['L'])
                    if witness['L']>=worst[0]:
                        worst=(witness['L'],r)
        assert worst==(3**(k-1),(1<<k)-1), (k,worst)
        r=(1<<k)-1
        a,g=prefix(r,k)
        assert a==k and g==3**k-1
        assert min(exponents)>=0
        depths.append({
          'k':k,'distinct_source_residues':1<<k,
          'targets_checked':len(targets),
          'total_real_two_clock_witnesses':all_classes,
          'median_first_power_exponent_for_target1':median(exponents),
          'worst_first_power_exponent_for_target1':worst[0],
          'worst_residue_for_target1':worst[1],
          'all_ones_target1_exponent':3**(k-1)
        })
    assert num_examples==sum((1<<k)*len(targets) for k in range(1,10))

    # Generic all-source affine formula is independently replayed,
    # including source zero and prefixes with large original tails.
    affine_cases=0
    for k in range(0,13):
        for r in range(0,384):
            a,g=prefix(r,k)
            for q in (0,1,2,3,7,16,100,1024):
                n=r+(1<<k)*q
                assert iter_shortcut(n,k)==g+3**a*q
                affine_cases+=1

    # A single dyadic residue cylinder can contain exact independently
    # certified ancestors of any chosen non-3 target, but witness
    # heights are not bounded linearly in the cylinder bit depth.
    return {
        'schema':'COLLATZ_V160_EXACT_SOURCE_LOCKED_TARGET_LIFT',
        'actual_odd_rule':'T(2x+1)=3x+2',
        'actual_even_rule':'T(2x)=x',
        'unconditional_affine_lift_regression_cases':affine_cases,
        'real_source_attached_target_witnesses':num_examples,
        'tested_dyadic_source_depths':[1,9],
        'all_dyadic_residue_target_pairs_checked':True,
        'primitive_root_power2_unit_coverage_verified_for_a_at_most':9,
        'unbounded_primitive_root_proof_in_lean':False,
        'test_targets_coprime_to_three':list(targets),
        'mersenne_one_chart_power_exponent_grows_as_three_to_k_minus_one':True,
        'per_depth':depths,
        'source_class_topological_density_implies_natural_density_one':False,
        'certified_terminal_exceptional_mass_bound_proved':False,
        'external_amplifier_rebuilt':False,
        'global_collatz':'UNKNOWN',
        'qed':False,
    }


if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
