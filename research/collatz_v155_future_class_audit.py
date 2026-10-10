"""V155 independent semantics controls — finite SOURCE-ATTACHED tests only.

The full proof of the Collatz conjecture is NOT here. Tests:
 - independently selected actual trajectory meeting clocks;
 - one true terminal future class for tested positive sources;
 - a synthetic *non-Collatz* two-basin model that defeats every
   fixed dyadic-residue classifier, for ALL k by exact formula;
 - explicit protection against treating this as QED.
"""
from __future__ import annotations
import json

def shortcut(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def toy(n:int)->int:
    assert n>0
    return n if n in (1,3) else n//2

def run_to_terminal(n:int, T, max_time:int=50_000):
    x=n
    seen={}
    for clock in range(max_time+1):
        if x in (1,2) and T==shortcut:
            return {'terminal':x,'time':clock}
        if x in (1,3) and T==toy:
            return {'terminal':x,'time':clock}
        if x in seen:
            return {'terminal':None,'time':clock}
        seen[x]=clock
        x=T(x)
    return {'terminal':None,'time':max_time}

def main():
    actual=[]
    for n in range(1,20001):
        result=run_to_terminal(n,shortcut)
        assert result['terminal'] in (1,2),n
        actual.append(result['time'])
    # Infinite parametric separator proved algebraically: for any
    # integer k>=0, the two sources 2^k and 3*2^k are both 0 mod
    # 2^k, but toy^k takes them respectively to absorbing 1 and 3.
    toy_cases=[]
    for k in range(0,90):
        modulus=1<<k
        p=modulus
        q=3*modulus
        assert p>0 and q>0
        assert p%modulus == q%modulus == 0
        x=p
        y=q
        for i in range(k):
            assert toy(x)==x//2
            assert toy(y)==y//2
            x=toy(x)
            y=toy(y)
        assert (x,y)==(1,3)
        for _ in range(5):
            x=toy(x); y=toy(y)
            assert (x,y)==(1,3)
        toy_cases.append({'k':k,'same_low_k_bits':True,
            'toy_left_root':1,'toy_right_root':3})
    return {
      'schema':'COLLATZ_V155_EXACT_FUTURE_CLASS_SEPARATOR',
      'actual_shortcut_tested_sources':len(actual),
      'actual_max_terminal_clock':max(actual),
      'actual_tested_all_reached_terminal':True,
      'synthetic_toy_not_collatz':True,
      'dyadic_collision_k_min':0,'dyadic_collision_k_max':89,
      'all_sampled_fixed_dyadic_resolutions_fail_to_separate_toy_basins':True,
      'general_formula':'for every k>=0, toy^k(2^k)=1, toy^k(3*2^k)=3; both sources are 0 mod2^k',
      'actual_collatz_global_terminal_class_proved':False,
      'no_second_class_exclusion_proved':False,
      'global_collatz':'UNKNOWN','qed':False,
      'sample_cases':[toy_cases[j] for j in (0,1,2,5,10,20,50,89)]
    }

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
