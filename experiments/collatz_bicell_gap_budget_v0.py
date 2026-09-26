#!/usr/bin/env python3
"""Turn failed worst-gap reverse certificates into per-bicell displacement budgets.

For each of the 27 V1 residual bicells, search the same exact direct-reverse and
one-forward-then-reverse certificate families, but do NOT demand p<y-G.
Instead compute the largest integer delta such that p < y-delta uniformly on
that Q2xQ3 cell for all y>=L. This is the exact amount of source-admission gap
information needed to activate the existing lower-merge certificate.

No global Collatz claim.
"""
import json
import collatz_reverse_trit_bicell_v2 as v2
import collatz_reverse_trit_separator_v0 as v0

L=v0.L; G=v0.G

def first_crt_above(r3,m3,parity):
    y=r3
    if y%2!=parity: y+=m3
    step=2*m3
    if y<L: y+=((L-y+step-1)//step)*step
    assert y>=L and y%m3==r3%m3 and y%2==parity
    return y

def direct_candidates(cell):
    j=cell["depth"];r=cell["residue"]
    out=[]
    for oo in range(1,j+1):
        M=3**oo; ro=r%M
        budget=M.bit_length()-1
        w=v0.contracting_word(oo,ro,budget)
        if w is None: continue
        S,C=v0.cocycle(w); lead=1<<S
        if lead>=M: continue
        y=first_crt_above(r,M,cell["parity"])
        num=lead*y-C
        if num<=0 or num%M: continue
        p=num//M
        if p<=0 or p>=y: continue
        capacity=y-p-1
        out.append(dict(kind="DIRECT_REVERSE",o=oo,S=S,C=C,
                        y0=y,p0=p,capacity=capacity,actions=list(w)))
    return out

def one_forward_candidates(cell):
    # All 27 parents are odd, so z=(3y+1)/2 and one odd forward step gains a trit.
    assert cell["parity"]==1
    j=cell["depth"];r=cell["residue"]
    prec=j+1; P=3**prec
    zres=((3*r+1)*pow(2,-1,P))%P
    out=[]
    for oo in range(1,prec+1):
        if oo<=1: continue
        # v1 budget: 2^(S-1) < 3^(o-1)
        budget=(3**(oo-1)).bit_length()
        if budget<oo: continue
        ro=zres%(3**oo)
        w=v0.contracting_word(oo,ro,budget)
        if w is None: continue
        S,C=v0.cocycle(w)
        if S<1: continue
        h=1<<(S-1); den=3**oo; lead=3*h; const=h-C
        if lead>=den: continue
        y=first_crt_above(r,3**j,1)
        num=lead*y+const
        if num<=0 or num%den: continue
        p=num//den
        if p<=0 or p>=y: continue
        capacity=y-p-1
        out.append(dict(kind="ONE_FORWARD_THEN_REVERSE",o=oo,S=S,C=C,
                        y0=y,p0=p,capacity=capacity,actions=list(w)))
    return out

rows=[]
for i,cell in enumerate(v2.parent_residuals()):
    cand=direct_candidates(cell)+one_forward_candidates(cell)
    cand.sort(key=lambda z:(-z["capacity"],len(z["actions"]),z["kind"]))
    best=cand[0] if cand else None
    rows.append(dict(index=i,depth=cell["depth"],residue=cell["residue"],
                     parity=cell["parity"],candidate_count=len(cand),
                     best=best,required_delta_upper=(best["capacity"] if best else None),
                     global_G=G,
                     fraction_of_G=(best["capacity"]/G if best else None)))
assert len(rows)==27
with_cert=[r for r in rows if r["best"]]
caps=[r["best"]["capacity"] for r in with_cert]
result={
 "schema":"COLLATZ_BICELL_GAP_BUDGET_V0",
 "cells":27,
 "cells_with_relaxed_lower_merge_certificate":len(with_cert),
 "capacity_min":min(caps) if caps else None,
 "capacity_max":max(caps) if caps else None,
 "capacity_median":sorted(caps)[len(caps)//2] if caps else None,
 "global_gap":G,
 "rows":rows,
 "interpretation":"If source admission proves delta=y-n <= the listed capacity for a cell, its existing reverse family gives p<n and closes that cell.",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
