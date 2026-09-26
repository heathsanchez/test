#!/usr/bin/env python3
"""Rung-2 intrinsic Q2xQ3 cycle after the direct reverse separator."""
import json
import collatz_rung2_reverse_trit_v0 as r2

G=r2.G;L=r2.L;DEPTH=r2.DEPTH

def one_step(r,j,parity):
    M=3**j;r%=M
    if parity==0:
        prec=j;P=3**prec;zres=r*pow(2,-1,P)%P
        def budget(o):return (3**o).bit_length()
        mode="EVEN"
    else:
        prec=j+1;P=3**prec;zres=(3*r+1)*pow(2,-1,P)%P
        def budget(o):return 0 if o<=1 else (3**(o-1)).bit_length()
        mode="ODD"
    for oo in range(1,prec+1):
        b=budget(oo)
        if b<oo:continue
        ro=zres%(3**oo);w=r2.word(oo,ro,b)
        if w is None:continue
        S,C=r2.cocycle(w);den=3**oo
        if S<1:continue
        h=1<<(S-1)
        if parity==0:
            coeff=h;const=-C;margin=(den-coeff)*L+C-den*G
            positive=coeff*L-C
        else:
            coeff=3*h;const=h-C;margin=(den-coeff)*L+C-h-den*G
            positive=coeff*L+h-C
        if den<=coeff or margin<=0 or positive<=0:continue
        return dict(mode=mode,o=oo,S=S,C=C,margin=margin)
    return None

acts,_=r2.reverse_actions(DEPTH);centre=[];cells=[];closed=0
for j in range(1,DEPTH+1):
    qj=r2.terminal(tuple(acts[:j]))
    if j>1:assert qj%(3**(j-1))==centre[-1]
    centre.append(qj);base=qj%(3**(j-1)) if j>1 else 0
    cd=(qj//(3**(j-1)))%3
    for alt in range(3):
        if alt==cd:continue
        rr=base+alt*3**(j-1);direct=r2.cert(rr,j)
        for parity in (0,1):
            kind=None;c=None
            if direct is not None:kind="DIRECT_REVERSE";c=direct
            elif rr%3==0:kind="IMPOSSIBLE_ENDPOINT_MOD3";c={"reason":"post-odd endpoint nonzero mod3"}
            else:
                c=one_step(rr,j,parity)
                if c:kind="ONE_FORWARD_THEN_REVERSE"
            status="CLOSED" if kind else "RESIDUAL"
            closed+=status=="CLOSED"
            cells.append(dict(depth=j,residue=rr,parity=parity,status=status,kind=kind,certificate=c))
res=[x for x in cells if x["status"]=="RESIDUAL"]
result={
 "schema":"COLLATZ_RUNG2_BICELL_V1",
 "cells":len(cells),"closed":closed,"residual":len(res),
 "residual_parity":{"even":sum(x["parity"]==0 for x in res),"odd":sum(x["parity"]==1 for x in res)},
 "residual_depth_histogram":{str(j):sum(x["depth"]==j for x in res) for j in range(1,DEPTH+1)},
 "residual_cells":res,
 "next_cycle":"impose minimal-bad source language F and source-relative consequences on these residuals",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
