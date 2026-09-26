#!/usr/bin/env python3
"""Compile the complete 12-odd / 19-two-cost contracting reverse-block language.

Every positive composition a_1+...+a_12=19 defines the reverse affine cocycle
  p=(2^19*y-C)/3^12.
Its integrality condition is one residue y=C*2^-19 mod 3^12.
This cycle compiles all 31,824 block shapes, quotients duplicate residues, and
studies the blocked 3-adic complement under one symbolic forward step.

It is exact finite arithmetic. It does not assert that arbitrary symbolic
forward residue transitions are dynamically reachable from an M>=0 cylinder.
"""
from itertools import combinations
import json
O=12;S=19;M=3**O
inv2=pow(2,-1,M)

def compositions(total,parts):
    # stars/bars: choose parts-1 cut positions among 1..total-1
    for cuts in combinations(range(1,total),parts-1):
        prev=0;out=[]
        for c in cuts+(total,):
            out.append(c-prev);prev=c
        yield tuple(out)

def cocycle(actions):
    s=C=0
    for i,a in enumerate(actions):
        s+=a;C=(1<<a)*C+3**i
    return s,C

residue_to_word={}
count=0
for w in compositions(S,O):
    count+=1
    s,C=cocycle(w);assert s==S
    r=(C*pow(1<<S,-1,M))%M
    residue_to_word.setdefault(r,w)
assert count==31824
A=set(residue_to_word)
# Any valid odd-poststep endpoint is nonzero mod 3; report coverage there.
domain={r for r in range(M) if r%3}
blocked=domain-A

# Symbolic one-step images modulo 3^12. Even step is bijective. Odd step maps
# to a residue congruent to inv2 mod3 and discards one source trit.
def even(r): return r*inv2%M
def odd(r): return (3*r+1)*inv2%M
stats={
 "even_blocked_to_admissible":sum(even(r) in A for r in blocked),
 "odd_blocked_to_admissible":sum(odd(r) in A for r in blocked),
 "blocked_both_miss":sum(even(r) not in A and odd(r) not in A for r in blocked),
}
# Minimal precision at which A membership is decided for each blocked residue:
# if its class mod 3^m contains no A residue, m is an exclusion witness.
Amods={m:{r%(3**m) for r in A} for m in range(1,O+1)}
witness_hist={}
unseparated=0
for r in blocked:
    found=None
    for m in range(1,O+1):
        if r%(3**m) not in Amods[m]:
            found=m;break
    if found is None:unseparated+=1
    else:witness_hist[found]=witness_hist.get(found,0)+1
assert unseparated==0
result={
 "schema":"COLLATZ_12_19_BLOCK_LANGUAGE_V0",
 "block_shapes":count,
 "modulus":M,
 "unique_admissibility_residues":len(A),
 "nonzero_mod3_domain":len(domain),
 "blocked_residues":len(blocked),
 "coverage_fraction":len(A)/len(domain),
 "blocked_exclusion_precision_histogram":witness_hist,
 "symbolic_forward_one_step":stats,
 "sample_admissible":[{"residue":r,"actions":list(residue_to_word[r])} for r in sorted(A)[:12]],
 "scope_warning":"forward residue transitions are symbolic; reachability from universal M>=0 cylinders is not yet proved",
 "next":"quotient blocked residues by exclusion precision/context and test all parity-word transitions until either A is forced or a recurrent blocked context is exhibited",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
