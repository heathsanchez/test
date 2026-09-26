#!/usr/bin/env python3
"""Exact closure of the historical two-block recurrent survivor core.

This closes ONLY the historical core reduction; it does not establish that every
universal M>=0 cylinder enters this core.

A=(2,1,1,2,1,1,2,2)
B=(1,1,2,1,1,2,2,2)

We compute the unique canonical source for each two-block word and replay exact
v2(3x+1) valuations. B->A and B->B are impossible. Hence any infinite exact
word over {A,B} must be A^infinity. Repeating A forever would require the
positive natural source to equal the b-adic limit -C_A/(a-b), which is negative
as a rational because a=3^8>b=2^12 and C_A>0. Thus no positive natural supports
an infinite path in this two-block core.
"""
import json
A=(2,1,1,2,1,1,2,2)
B=(1,1,2,1,1,2,2,2)

def affine(vals):
    S=0;C=0
    for v in vals:
        C=3*C+(1<<S);S+=v
    return 3**len(vals),C,1<<S

def canonical(vals):
    a,C,b=affine(vals)
    return (-C*pow(a,-1,b))%b

def v2(n):
    c=0
    while n%2==0:
        c+=1;n//=2
    return c

def replay(vals):
    x=canonical(vals); start=x
    for i,want in enumerate(vals):
        z=3*x+1; got=v2(z)
        if got!=want:
            return {"source":start,"ok":False,"failure_index":i,
                    "wanted":want,"actual":got,"state_before":x}
        x=z>>got
    return {"source":start,"ok":True,"endpoint":x}

pairs={}
for ni,X in (("A",A),("B",B)):
    for nj,Y in (("A",A),("B",B)):
        pairs[ni+nj]=replay(X+Y)

assert pairs["AA"]["ok"] and pairs["AB"]["ok"]
assert not pairs["BA"]["ok"] and not pairs["BB"]["ok"]
assert pairs["BA"]["failure_index"]==15 and pairs["BB"]["failure_index"]==15
assert pairs["BA"]["wanted"]==pairs["BB"]["wanted"]==2
assert pairs["BA"]["actual"]==pairs["BB"]["actual"]==5

a,C,b=affine(A)
assert (a,b,C)==(3**8,2**12,13015)
assert a>b and C>0
# If a positive integer x realized A forever, its residues modulo b^m would
# stabilize to x, while the repeated-A congruence has b-adic limit
# x = -C/(a-b). Multiplying gives (a-b)x=-C, impossible for x>0.
result={
 "schema":"COLLATZ_TWO_BLOCK_EXACT_CORE_CLOSURE_V0",
 "blocks":{"A":list(A),"B":list(B)},
 "pair_replay":pairs,
 "A_affine":{"a":a,"b":b,"C":C},
 "B_is_terminal_in_exact_core":True,
 "only_possible_infinite_symbolic_word":"A^infinity",
 "A_infinite_positive_natural_impossible":True,
 "reason":"eventual stabilized natural source would satisfy (3^8-2^12)*x=-13015",
 "historical_two_block_recurrent_core":"EMPTY_OVER_POSITIVE_NATURALS",
 "scope_warning":"still need a universal theorem that every canonical M>=0 first-crossing obstruction maps into this historical two-block core",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
