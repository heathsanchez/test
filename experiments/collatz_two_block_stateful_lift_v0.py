#!/usr/bin/env python3
"""Exact stateful mixed-base lift tree for the two historical recurrent blocks.

This is a focused obstruction test, NOT a universal Collatz quotient.

Odd-step valuation blocks:
 A=(2,1,1,2,1,1,2,2)
 B=(1,1,2,1,1,2,2,2)
Both have L=8 odd steps, S=12 powers of two, hence block maps
  F_i(x)=(3^8*x+C_i)/2^12
with multiplier 6561/4096 > 1.

For a block word of length m, the exact composition is
  x_m=(a^m*x+N_m)/b^m.
Its canonical source residue is
  r_m=-N_m*(a^m)^(-1) mod b^m.
We enumerate the full switching tree through depth 20, carrying N and r
statefully. We record the base-b lift digit
  t_m=(r_m-r_{m-1})/b^(m-1).
A fixed natural source supporting an infinite switching itinerary would require
these lift digits eventually to be all zero. A finite bound on zero-runs would
therefore exclude this two-block recurrent core.

Scope: the historical finite recurrent-core reduction itself is not currently
a universal theorem, so even a green result here does not prove Collatz.
"""
import json
A=(2,1,1,2,1,1,2,2)
B=(1,1,2,1,1,2,2,2)
blocks=(A,B)

def affine(block):
    # numerator recurrence x -> (3^L*x+C)/2^S
    p=1; C=0; S=0
    for v in block:
        # compose (3*x+1)/2^v
        C=3*C+(1<<S)
        p*=3; S+=v
    return p,C,1<<S

vals=[affine(x) for x in blocks]
assert vals[0][0]==vals[1][0]==3**8
assert vals[0][2]==vals[1][2]==2**12
a=vals[0][0]; b=vals[0][2]; Cs=[x[1] for x in vals]
# Cross-check constants by direct rational composition convention.
# Our recurrence above yields numerator constants in common denominator form.

DEPTH=20
states=[(0,0,0,"")] # N, r, trailing-zero-run, word
rows=[]
global_max_zero=0; witness=""
for m in range(1,DEPTH+1):
    bp=b**(m-1); mod=bp*b
    invam=pow(pow(a,m,mod),-1,mod)
    new=[]; zero_edges=0; minr=None; minword=None; maxtrail=0
    for N,rprev,zrun,w in states:
        for i,C in enumerate(Cs):
            N2=a*N+C*bp
            r=(-N2*invam)%mod
            assert (r-rprev)%bp==0
            t=(r-rprev)//bp
            z2=zrun+1 if t==0 else 0
            if t==0: zero_edges+=1
            if z2>global_max_zero:
                global_max_zero=z2; witness=w+str(i)
            maxtrail=max(maxtrail,z2)
            if minr is None or r<minr:
                minr=r; minword=w+str(i)
            new.append((N2,r,z2,w+str(i)))
    rows.append({"depth":m,"nodes":len(new),"zero_lift_edges":zero_edges,
                 "max_trailing_zero_run":maxtrail,"min_canonical_residue":minr,
                 "min_residue_bits":minr.bit_length(),"min_word":minword})
    states=new
result={
 "schema":"COLLATZ_TWO_BLOCK_STATEFUL_LIFT_TREE_V0",
 "blocks":[list(A),list(B)],"a":a,"b":b,"constants":Cs,
 "multiplier_superunit":a>b,
 "depth":DEPTH,"leaves":len(states),
 "global_max_consecutive_zero_lifts":global_max_zero,
 "zero_run_witness":witness,
 "rows":rows,
 "decision":"NO_TWO_CONSECUTIVE_ZERO_LIFTS_THROUGH_DEPTH_20" if global_max_zero<2 else "ZERO_RUN_LENGTH_AT_LEAST_2_FOUND",
 "periodic_subcase":"excluded algebraically: infinite exact repetition forces x=-C/(3^L-2^S)<0",
 "scope_warning":"the two-block recurrent-core reduction is historical finite/quotient evidence, not a proved universal reduction",
 "next":"if max zero run remains 1, derive a symbolic no-00 lift lemma for arbitrary prefix composition; otherwise preserve the first exact longer zero-run as the new obstruction",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
