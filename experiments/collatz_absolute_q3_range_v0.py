#!/usr/bin/env python3
"""Absolute Q3-range closeout audit for the first two Collatz Farey rungs.

For each certified rung choose the least R with 3^R above the rung's entire
possible endpoint interval.  At that precision an endpoint matching the
extremal reverse centre is an ordinary integer equality question, not an
infinite 3-adic possibility.

Every first-difference Q3 cylinder through depth R is then crossed with endpoint
parity and classified only by already-qualified mechanisms:
  * RANGE_EMPTY: no integer in the certified endpoint interval occupies the cell;
  * DIRECT_REVERSE: existing coefficient-contracting reverse predecessor;
  * IMPOSSIBLE_ENDPOINT_MOD3;
  * ONE_FORWARD_THEN_REVERSE: V1's exact composed certificate;
  * RESIDUAL.

No new lower-merge constructor is introduced.  This is a finite exact audit,
not a Collatz proof.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from fractions import Fraction
from collections import Counter

import collatz_reverse_trit_separator_v0 as v0
import collatz_reverse_trit_bicell_v1 as v1
import collatz_transfer_farey as farey
import collatz_transfer_ladder as ladder


def ceil_frac(x:Fraction)->int:
    return (x.numerator+x.denominator-1)//x.denominator


def rung2_gap()->int:
    hi=(Fraction(ladder.q2,1)/(6*ladder.ln2_lo)+Fraction(1,3)
        - ladder.eps2_lo*ladder.B1)
    assert hi>0
    return ceil_frac(hi)


def least_q3_depth_above(upper:int)->int:
    r=0;m=1
    while m<=upper:
        r+=1;m*=3
    assert 3**(r-1)<=upper<3**r
    return r


def configure(Q:int,T:int,L:int,G:int,depth:int)->None:
    v0.Q=Q;v0.T=T;v0.L=L;v0.G=G;v0.DEPTH=depth
    v1.G=G;v1.L=L;v1.DEPTH=depth


def first_in_cell(lo:int,hi:int,res3:int,j:int,parity:int):
    """Smallest y in [lo,hi] with y=res3 mod3^j and y=parity mod2."""
    m3=3**j
    # m3 is odd.  Pick the representative with requested parity modulo 2*m3.
    x=res3 % m3
    if x%2!=parity:
        x+=m3
    mod=2*m3
    if x<lo:
        x += ((lo-x+mod-1)//mod)*mod
    return x if x<=hi else None


def classify_rung(name:str,Q:int,T:int,lo:int,hi:int,G:int):
    R=least_q3_depth_above(hi)
    configure(Q,T,lo,G,R)
    acts,_,_=v0.extremal_reverse_actions(R)
    assert len(acts)==R
    modulus=3**R
    centre=v0.terminal_residue(tuple(acts))
    assert modulus>hi
    centre_candidates=[]
    for parity in (0,1):
        y=first_in_cell(lo,hi,centre,R,parity)
        if y is not None:
            centre_candidates.append(dict(parity=parity,y=y))
    assert not centre_candidates, (name,centre,lo,hi,modulus,centre_candidates)

    rows=[];counts=Counter()
    residual=[]
    centre_prefix=[]
    for j in range(1,R+1):
        qj=v0.terminal_residue(tuple(acts[:j]))
        if j>1:
            assert qj%(3**(j-1))==centre_prefix[-1]
        centre_prefix.append(qj)
        base=qj%(3**(j-1)) if j>1 else 0
        qdigit=(qj//(3**(j-1)))%3
        for digit in range(3):
            if digit==qdigit:
                continue
            r=base+digit*3**(j-1)
            direct=v0.best_contracting_prefix(r,j)
            for parity in (0,1):
                y=first_in_cell(lo,hi,r,j,parity)
                cert=None
                if y is None:
                    kind="RANGE_EMPTY"
                elif direct is not None:
                    kind="DIRECT_REVERSE";cert=direct
                elif r%3==0:
                    kind="IMPOSSIBLE_ENDPOINT_MOD3"
                    cert={"reason":"after any odd shortcut step endpoint is nonzero mod 3"}
                else:
                    cert=v1.one_step_reverse_cert(r,j,parity)
                    if cert is not None:
                        kind="ONE_FORWARD_THEN_REVERSE"
                    else:
                        kind="RESIDUAL"
                counts[kind]+=1
                row=dict(rung=name,depth=j,first_difference_depth=j-1,
                         centre_digit=qdigit,alternate_digit=digit,
                         residue=r,modulus=3**j,parity=parity,
                         first_interval_point=y,status=kind,certificate=cert)
                rows.append(row)
                if kind=="RESIDUAL":
                    residual.append({k:row[k] for k in
                        ("depth","first_difference_depth","centre_digit",
                         "alternate_digit","residue","modulus","parity",
                         "first_interval_point")})
    assert len(rows)==4*R
    assert sum(counts.values())==4*R
    out=dict(
        name=name,Q=Q,T=T,lower=lo,upper=hi,gap=G,
        absolute_q3_depth=R,absolute_modulus=str(modulus),
        centre_residue=str(centre),centre_above_upper=(centre>hi),
        centre_interval_candidates=centre_candidates,
        reverse_actions=acts,
        first_difference_cells=len(rows),
        counts=dict(sorted(counts.items())),
        residual_count=len(residual),
        residual_cells=residual,
    )
    print("RUNG_ABSOLUTE",json.dumps({
        "name":name,"lower":lo,"upper":hi,"gap":G,
        "absolute_q3_depth":R,"absolute_modulus":str(modulus),
        "centre_residue":str(centre),"centre_above_upper":centre>hi,
        "cells":len(rows),"counts":dict(sorted(counts.items())),
        "residual_count":len(residual)},sort_keys=True))
    for x in residual[:30]:
        print("RESIDUAL",name,json.dumps(x,sort_keys=True))
    return out


def run(output:Path):
    G2=rung2_gap()
    assert G2==30243148343
    r1=classify_rung("rung1",farey.q1,farey.t1,farey.L,
                     farey.dk_live_ceiling_int,farey.live_gap_ceiling)
    r2=classify_rung("rung2",ladder.q2,ladder.t2,ladder.B1,
                     ladder.B2,G2)
    assert r1["absolute_q3_depth"]==46
    assert r2["absolute_q3_depth"]==48

    # Compare the shallow residual language while both rungs have depth.
    common=[]
    for a,b in zip(r1["residual_cells"],r2["residual_cells"]):
        ka=(a["depth"],a["residue"],a["parity"])
        kb=(b["depth"],b["residue"],b["parity"])
        if ka==kb:
            common.append(ka)
        else:
            break

    result=dict(
        schema="COLLATZ_ABSOLUTE_Q3_RANGE_V0",
        rung1=r1,rung2=r2,
        common_residual_prefix_length=len(common),
        common_residual_prefix=[list(x) for x in common],
        verdict="PASS_FINITE_ABSOLUTE_Q3_RANGE_WITH_RESIDUAL",
        scope=("first two certified Farey rungs; exact extremal reverse centre; "
               "existing direct/V1 reverse certificates plus exact interval emptiness; "
               "no universal rung theorem and no Collatz claim")
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("COMMON_RESIDUAL_PREFIX_LENGTH",len(common))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.output)
