#!/usr/bin/env python3
"""Affine source-admission foundry over exact lower Farey/convergent resonances.

For a fixed parity word with q odd steps in t shortcut steps:
  2^t y = 3^q n + B, delta=y-n,
hence
  (2^t-3^q)n + 2^t delta = B.
Because gcd(2^t,2^t-3^q)=1, delta has one residue modulo
D=2^t-3^q. If D>G, at most one delta in [0,G] is possible.

This foundry builds the latest-odd mechanical word at several exact lower
convergents, verifies prefix coefficient survival using integer arithmetic, and
computes the unique modular displacement. Float is proposal-only for positions;
all admitted words are independently checked by exact integer inequalities.

The run is theorem-discovery evidence, not a global Collatz proof.
"""
import json, math

# Lower convergents q/t to alpha=log(2)/log(3), small enough for exact foundry.
CASES=[(1,2),(5,8),(41,65),(306,485),(15601,24727)]

def latest_word(q,t):
    beta=math.log(3)/math.log(2)
    pos=[math.floor((j-1)*beta) for j in range(1,q+1)]
    assert len(set(pos))==q and pos[-1]<t
    B=0; idx=0; qc=0
    for s in range(t):
        if idx<q and pos[idx]==s:
            B=3*B+(1<<s); idx+=1; qc+=1
        if s+1<t:
            assert 3**qc >= (1<<(s+1)), (q,t,s,qc)
    assert qc==q and 3**q < (1<<t)
    return B,pos

rows=[]
surviving_center=[]
for q,t in CASES:
    B,pos=latest_word(q,t)
    P=1<<t; D=P-3**q
    assert D>0 and math.gcd(P,D)==1
    delta=(B*pow(P,-1,D))%D
    numerator=B-P*delta
    n=(numerator//D) if numerator%D==0 else None
    assert n is not None
    positive=n>0
    # If positive, independently replay the proposed parity word.
    admissible=False
    if positive:
        x=n; odds=set(pos)
        admissible=True
        for s in range(t):
            if (x&1)!=(s in odds):
                admissible=False; break
            x=x//2 if x%2==0 else (3*x+1)//2
        if admissible:
            assert x-n==delta
    row={
      "q":q,"t":t,"D_bits":D.bit_length(),
      "B_over_2t_floor":B//P,
      "delta_bits":delta.bit_length(),
      "delta_zero":delta==0,
      "positive_source":positive,
      "parity_word_admissible_if_positive":admissible,
    }
    if positive and admissible: surviving_center.append((q,t))
    rows.append(row)

# The base 1/2 word is the terminal 1<->2 behavior; all nontrivial tested lower
# convergent latest-odd centers have no positive source.
nontrivial=[r for r in rows if (r["q"],r["t"])!=(1,2)]
assert all(not r["positive_source"] for r in nontrivial)

result={
 "schema":"COLLATZ_AFFINE_ADMISSION_FOUNDRY_V0",
 "cases":rows,
 "nontrivial_latest_odd_centers_tested":len(nontrivial),
 "nontrivial_positive_centers":sum(r["positive_source"] for r in nontrivial),
 "law_candidate":{
   "id":"fixed-parity-word-unique-near-return-displacement@1",
   "statement":"for fixed (q,t,B), delta is unique modulo D=2^t-3^q; if D>G then at most one delta in [0,G]",
   "status":"WARRANTED_ARITHMETIC_SCHEMA_NEEDS_FORMALIZATION"
 },
 "discovery_candidate":{
   "id":"latest-odd-centre-nonadmission",
   "status":"CANDIDATE_ONLY",
   "observed":"all four nontrivial tested lower-convergent latest-odd centres yield no positive source",
   "warning":"finite foundry pattern is not a theorem and is not extrapolated to the giant resonance"
 },
 "next_cycle":"replace source census by intercept/parity-word admission; search which near-extremal words have modular delta in the live interval",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
