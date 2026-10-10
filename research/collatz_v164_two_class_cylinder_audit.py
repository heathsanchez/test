"""V164 exact two-class cylinder-coexistence audit, synthetic G7 only.

The same genuinely source-attached V160/V162 affine chart can construct
ancestors of BOTH disjoint 3n+7 cycles in EVERY tested dyadic cylinder.
Elementary unit arithmetic: powers of 2 generate (Z/3^aZ)^times,
so the algebraic construction actually works for every finite k and
every binary prefix once targets b=7 and b=5 are 3-coprime. This
audit checks the arithmetic for every prefix through k=8. The
full power-surjectivity theorem is not imported into the V164 Lean
source; the Lean source **retains explicit hit hypotheses**.

This is a synthetic non-Collatz model, NOT a counterexample to Collatz.
Its purpose is to REFUTE the inference that all binary prefixes
containing members of a future class makes that class unique.
"""

import json

def G(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+7)//2

def prefix(n,k):
    a=0
    for _ in range(k):
        a+=(n&1)
        n=G(n)
    return a,n

def discrete_log_power_two(a:int):
    m=3**a
    if m==1: return {0:0},1
    seen={}
    v=1
    while v not in seen:
        seen[v]=len(seen)
        v=2*v %m
    assert v==1
    assert len(seen)==2*3**(a-1)
    return seen,len(seen)

def lift(r,k,b,cache):
    assert 0<=r<2**k and b in (5,7)
    a,g=prefix(r,k)
    modulus=3**a
    if modulus>1: assert g%3!=0
    if a not in cache:
        cache[a]=discrete_log_power_two(a)
    table,order=cache[a]
    residue=((g*pow(b,-1,modulus))%modulus) if modulus>1 else 0
    L=table[residue]
    while b*(1<<L)<g:
        L+=order
    d=b*(1<<L)-g
    assert d>=0 and d%modulus==0
    q=d//modulus
    n=r+(1<<k)*q
    assert n>0 and n%(1<<k)==r
    final_odd_count,end=prefix(n,k)
    assert end==b*(1<<L)
    assert final_odd_count==a
    # G(2y)=y, so genuine even stripping yields b after L more clocks.
    # For modest L, replay each actual time to protect source semantics.
    if L<=150:
        y=end
        for _ in range(L):
            assert y%2==0 and G(y)==y//2
            y=G(y)
        assert y==b
    return {'b':b,'L':L,'n':n,'a':a,'g':g,
      'bits':n.bit_length()}

def main():
    assert G(7)==14 and G(14)==7
    assert (G(5),G(11),G(20),G(10))==(11,20,10,5)
    assert {7,14}.isdisjoint({5,11,20,10})
    cache={}
    total=0
    all_joins=0
    rows=[]
    adversarial=[]
    for k in range(9):
        heights={'A':0,'B':0}
        worst=(0,0)
        for r in range(1<<k):
            a=lift(r,k,7,cache)
            b=lift(r,k,5,cache)
            total+=1
            all_joins+=2
            assert a['n']!=b['n']
            assert a['n']%(1<<k)==b['n']%(1<<k)==r
            heights['A']=max(heights['A'],a['bits'])
            heights['B']=max(heights['B'],b['bits'])
            if max(a['L'],b['L'])>worst[0]:
                worst=(max(a['L'],b['L']),r)
            if r==(1<<k)-1 and k in (3,5,8):
                adversarial.append({
                  'k':k,'prefix':r,
                  'A_power_exponent':a['L'],
                  'B_power_exponent':b['L'],
                  'A_source_bits':a['bits'],
                  'B_source_bits':b['bits']})
        rows.append({'k':k,'number_prefixes':1<<k,
          'two_disjoint_real_classes_per_prefix':True,
          'max_A_source_bits':heights['A'],
          'max_B_source_bits':heights['B'],
          'max_power_exponent':worst[0],
          'max_exponent_prefix':worst[1]})
    assert total==511 and all_joins==1022
    assert len(cache)<=9
    assert all(r['two_disjoint_real_classes_per_prefix'] for r in rows)

    return {
      'schema':'COLLATZ_V164_TWO_DISJOINT_CLASSES_EVERY_DYADIC_CYLINDER',
      'actual_system':'synthetic G7(n)=(3n+7)/2 odd, n/2 even',
      'NOT_actual_Collatz':True,
      'cycles':['7 -> 14 -> 7','5 -> 11 -> 20 -> 10 -> 5'],
      'all_prefix_depths_checked':'0..8',
      'all_checked_source_prefixes':total,
      'actual_source_to_target_joins_checked':all_joins,
      'both_classes_same_residue_every_checked_prefix':True,
      'source_is_positive_and_clock_is_real':True,
      'number_theory_unit_power_coverage_verified_up_to_a':max(cache),
      'all_exponent_number_theory_kernel_reified':False,
      'all_prefix_coexistence_in_lean_explicit_power_hit_hypotheses':True,
      'topological_source_coverage_implies_uniqueness':False,
      'quantitative_natural_density_coverage_proved':False,
      'actual_Collatz_second_class_excluded':False,
      'per_depth':rows,
      'adversarial_prefixes':adversarial,
      'global_collatz':'UNKNOWN','qed':False
    }

if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
