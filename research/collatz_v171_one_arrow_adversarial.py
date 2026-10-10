"""V171 exact source-attached one-arrow adversarial no-giant control.

S5(n)=5 for n=5, otherwise S5(n)=true shortcut T(n).
This differs from the actual Collatz shortcut at exactly ONE input.
Yet 5 becomes a second absorbing positive class and most finite
original sources flow into it, while {1,2} remains terminal.

V171's separate Lean proof establishes that S5 retains the
unconditional all-depth 3-adic endpoint sieve AND has NO
nontrivial fixed-modulus periodic invariant label, for EVERY M.
This audit checks finite instances and reports the actual
full source/clock component populations to expose the failure
of an easy no-giant inference.

It deliberately DOES NOT claim S5 preserves V160's exact
all-source affine law: it fails on families crossing the
exceptional source5. That distinction is indispensable.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path


def T(n: int) -> int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2

def S5(n: int) -> int:
    return 5 if n==5 else T(n)

def it(n,k,fn):
    for _ in range(k):n=fn(n)
    return n


def mod_periodic_label_graph(M:int):
    parent=list(range(M))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def join(a,b):
        a=find(a);b=find(b)
        if a!=b:parent[a]=b
    for n in range(1,6*M+15):
        join(n%M,S5(n)%M)
    return len({find(i) for i in range(M)})


def source_graph(k,H):
    X=1<<k;N=X-1
    parent=list(range(X))
    size=[1]*X
    is_terminal=bytearray(X)
    first={}
    def find(n):
        p=parent
        x=n
        while p[x]!=x:x=p[x]
        while p[n]!=n:
            y=p[n];p[n]=x;n=y
        return x
    def join(a,b):
        a=find(a);b=find(b)
        if a==b:return
        if size[a]<size[b]:a,b=b,a
        parent[b]=a
        size[a]+=size[b]
        is_terminal[a]|=is_terminal[b]
    for n in range(1,X):
        y=n
        for i in range(H+1):
            if y in (1,2):
                is_terminal[find(n)]=1
            prev=first.get(y)
            if prev is None:
                first[y]=(n,i)
            else:
                p,j=prev
                if p!=n:join(n,p)
            if i<H:y=S5(y)
    is_terminal[find(1)]=1
    is_terminal[find(2)]=1
    comp=Counter(find(i) for i in range(1,X))
    unknown=sorted([v for r,v in comp.items() if not is_terminal[r]],reverse=True)
    assert sum(comp.values())==N
    assert not is_terminal[find(5)]
    assert find(5)!=find(1)
    # All sources whose genuine T orbit encounters5 in this finite
    # horizon must be S5-unseeded; the latter statement is proved
    # universally in Lean, not derived by this sample.
    checked_T_to_5=0
    for n in range(1,X):
        x=n
        for _ in range(H+1):
            if x==5:
                checked_T_to_5+=1
                assert find(n)==find(5)
                break
            x=T(x)
    return {
      'k':k,'H':H,'cutoff_positive':N,
      'unseeded_population':sum(unknown),
      'largest_unseeded_component':max(unknown,default=0),
      'unseeded_component_count':len(unknown),
      'unseeded_fraction':sum(unknown)/X,
      'tested_true_T_predecessors_of_5':checked_T_to_5,
      'true_T_hits_5_are_nonterminal_in_S5':True,
      'separate_5_fixed_cycle_retained':True
    }


def finite_parity(n,h,fn):
    ans=0
    for i in range(h):
        ans |= (n%2)<<i
        n=fn(n)
    return ans


def main():
    assert S5(5)==5 and T(5)==8
    assert S5(1)==2 and S5(2)==1
    assert all(S5(n)==T(n) for n in range(1,100001) if n!=5)
    assert all(S5(2*n)==n for n in range(0,100000))
    assert all(S5(n)%3==2 for n in range(1,100000,2))
    sieve_cases=0
    for n in range(0,8192):
        x=n
        for k in range(25):
            assert (x%3==0)==(n%(3*2**k)==0),(n,k,x)
            sieve_cases+=1
            x=S5(x)

    modular=Counter()
    for M in range(1,501):
        components=mod_periodic_label_graph(M)
        assert components==1,M
        modular[components]+=1

    parity_word_fail=next(h for h in range(1,12)
        if len({finite_parity(n,h,S5) for n in range(1<<h)}) != 1<<h)
    assert parity_word_fail==3
    rows=[]
    for k in (8,10,12,14):
        rows.append(source_graph(k,8*k))
    assert [r['largest_unseeded_component'] for r in rows] == [
        234,954,3839,15386
    ]
    assert all(x['unseeded_component_count']==1 for x in rows)
    assert rows[-1]['unseeded_fraction']>0.93

    return {
      'schema':'COLLATZ_V171_ONE_ARROW_NONMODULAR_GIANT_COUNTERMODEL',
      'synthetic_map':'S5(5)=5, S5(n)=T(n) for all n!=5',
      'actual_Collatz_map_unchanged_in_original_repo':True,
      'one_defect_at_source':5,
      'true_T_successor_5':8,
      'one_arrow_fixed_5':True,
      'source_mod3_sieve_all_cases_exact':True,
      'source_mod3_sieve_cases':sieve_cases,
      'tested_fixed_moduli_from_one_to':500,
      'all_tested_periodic_label_graphs_connected':True,
      'finite_parity_word_permutation_first_fails_at_length':parity_word_fail,
      'exact_v160_all_source_affine_identity_preserved':False,
      'source_cutoff_rows':rows,
      'last_largest_unseeded_component':rows[-1]['largest_unseeded_component'],
      'last_unseeded_fraction':rows[-1]['unseeded_fraction'],
      'external_target5_density_locally_imported':False,
      'countermodel_is_not_true_Collatz':True,
      'no_giant_for_true_Collatz_proved':False,
      'global_collatz':'UNKNOWN','qed':False
    }

if __name__=='__main__':
    out=main()
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/v171-one-arrow.json').write_text(
      json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
      'schema':out['schema'],
      'largest_unseeded_S5_at_k14':out['last_largest_unseeded_component'],
      'unseeded_fraction':out['last_unseeded_fraction'],
      'global_collatz':out['global_collatz']
    },sort_keys=True))
