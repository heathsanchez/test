"""V159 first-principles fixed-modulus equivalence separator.

For each M=1..3000, form an undirected quotient graph on Z/M:
  r ~ 2*r (real even inverse); and
  r ~ 3*r+1 for a residue r admitting an odd positive lift.
All edges are actual future-coalescence equalities on positive naturals.
The test is a BOUNDED regression. The GENERAL proof belongs to
AllModuliFutureLabelCollapse.lean, not to the finite enumeration.

No convergence, terminal-class uniqueness, or invented QED.
"""
from __future__ import annotations
import json
from hashlib import sha256

def graph(M):
    assert M>0
    parent=list(range(M))
    def root(x):
        while x!=parent[x]:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def merge(a,b):
        ra,rb=root(a),root(b)
        if ra!=rb:parent[ra]=rb
    for r in range(M):
        merge(r,(2*r)%M)
        if M%2==1 or r%2==1:
            merge(r,(3*r+1)%M)
    return len({root(r) for r in range(M)})

def arith_reduction(M):
    if M==1:
        return 1,'BASE'
    if M%2==0:
        return M//2,'EVEN_HALF'
    if M%3==0:
        return M//3,'ODD_THIRD'
    return (M-1)//2,'COPRIME_SIX_COMMUTATOR'

def main():
    results=[]
    counts={}
    for M in range(1,3001):
        c=graph(M)
        assert c==1, (M,c)
        nextM,tag=arith_reduction(M)
        counts[tag]=counts.get(tag,0)+1
        assert nextM<M or M==1
        if M in (1,2,3,4,5,6,7,8,9,11,15,21,25,27,35,97,101,1024,1729,2048,2999,3000):
            results.append(dict(M=M,components=c,reduced_period=nextM,method=tag))
    return {
        'schema':'COLLATZ_V159_EXACT_FIXED_MODULUS_CLASS_COLLAPSE',
        'finite_moduli_checked':3000,
        'all_checked_modular_class_graphs_connected':True,
        'real_even_relation':'n ~ 2n',
        'real_odd_relation':'odd n ~ 3n+1',
        'cases':counts,
        'examples':results,
        'lean_universal_proof_required':True,
        'synthetic_countermodel_used':False,
        'global_collatz':'UNKNOWN',
        'qed':False,
    }

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
