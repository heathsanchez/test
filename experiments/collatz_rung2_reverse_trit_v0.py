#!/usr/bin/env python3
"""Rung-2 reverse-trit separator cycle, informed by prior Crystal cycles.

Uses exact rung-2 constants from the handoff, reconstructs the latest-odd
mechanical reverse centre to the first informative ternary depth 23, and tests
the existing coefficient-contracting reverse grammar with the new live lower
bound and gap. Residuals are emitted, never promoted.

External first-rung coverage remains a premise of the handoff.
"""
import json
from functools import lru_cache
import collatz_transfer_farey as f

Q=137_528_045_312
T=217_976_794_617
L=4*3**44+2
G=42_302_805_099
DEPTH=23

def floor_frac(x): return x.numerator//x.denominator

def reverse_actions(depth):
    beta_lo=f.ln3_lo/f.ln2_hi
    beta_hi=f.ln3_hi/f.ln2_lo
    cumulative=[];positions=[]
    for k in range(1,depth+1):
        jm1=Q-k
        flo=floor_frac(jm1*beta_lo); fhi=floor_frac(jm1*beta_hi)
        assert flo==fhi,(k,flo,fhi)
        positions.append(flo); cumulative.append(T-flo)
    acts=[cumulative[0]]+[cumulative[i]-cumulative[i-1] for i in range(1,depth)]
    for k,S in enumerate(cumulative,1):
        assert (1<<(S-1)) < 3**k < (1<<S)
    return acts,cumulative

def terminal(actions):
    S=C=0
    for i,a in enumerate(actions):
        S+=a; C=(1<<a)*C+3**i
    M=3**len(actions)
    return (C*pow(1<<S,-1,M))%M

def cocycle(actions):
    S=C=0
    for i,a in enumerate(actions):
        S+=a;C=(1<<a)*C+3**i
    return S,C

@lru_cache(None)
def word(j,r,budget):
    if j==0:return ()
    if budget<j:return None
    M=3**j;r%=M
    if r%3==0:return None
    tailM=3**(j-1)
    start=2 if r%3==1 else 1
    for a in range(start,budget-(j-1)+1,2):
        z=(pow(2,a,M)*r-1)%M
        if z%3:continue
        rp=(z//3)%tailM if j>1 else 0
        tail=word(j-1,rp,budget-a)
        if tail is not None:return (a,)+tail
    return None

def cert(r,depth):
    for oo in range(1,depth+1):
        M=3**oo;ro=r%M
        budget=M.bit_length()-1
        w=word(oo,ro,budget)
        if w is None:continue
        S,C=cocycle(w)
        if not ((1<<S)<M):continue
        if (1<<S)*L-C<=0:continue
        margin=(M-(1<<S))*L+C-M*G
        if margin<=0:continue
        y=ro+((L-ro+M-1)//M)*M
        p=((1<<S)*y-C)//M
        assert 0<p<y-G
        return dict(o=oo,S=S,C=C,actions=list(w),margin=margin)
    return None

acts,cums=reverse_actions(DEPTH)
rows=[];closed=0
centre=[]
for j in range(1,DEPTH+1):
    qj=terminal(tuple(acts[:j]))
    if j>1:assert qj%(3**(j-1))==centre[-1]
    centre.append(qj)
    base=qj%(3**(j-1)) if j>1 else 0
    digit=(qj//(3**(j-1)))%3
    for alt in range(3):
        if alt==digit:continue
        r=base+alt*3**(j-1)
        c=cert(r,j)
        rows.append(dict(depth=j,first_difference=j-1,centre_digit=digit,
                         alternate_digit=alt,residue=r,status="LOWER_MERGE" if c else "RESIDUAL",
                         certificate=c))
        closed+=c is not None
residual=[x for x in rows if x["status"]=="RESIDUAL"]
result={
 "schema":"COLLATZ_RUNG2_REVERSE_TRIT_V0",
 "rung":{"q":Q,"t":T,"live_lower":L,"gap":G,"depth":DEPTH},
 "reverse_actions":acts,
 "classes":len(rows),"closed":closed,"residual":len(residual),
 "first_residual":residual[0] if residual else None,
 "residual_depth_histogram":{str(j):sum(x["depth"]==j for x in residual) for j in range(1,DEPTH+1)},
 "next_cycle":"add Q2/source-admission coordinates only to these residual classes",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
