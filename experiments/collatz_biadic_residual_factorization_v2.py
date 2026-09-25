#!/usr/bin/env python3
"""Exact residual factorization across intrinsic Q2 x Q3 Collatz cells.

Parent V1 left 27 genuine first-difference Q3 cylinders after restoring one
Q2 parity bit. This audit asks what happens when the Q2 coordinate is refined
by an exact forward prefix while retaining only coefficient-persistent prefixes
(the transfer theorem closes every rejected prefix long before the first
dangerous Farey resonance).

For each live Q2 prefix and each parent Q3 cylinder:
  1. execute the exact Q2-determined shortcut prefix symbolically,
  2. transport all known Q3 precision through it,
  3. search an exact reverse-predecessor word from the transported endpoint,
  4. require the predecessor to lie below y-G uniformly for y>=L.

The audit then compares the common survivor language with the existing
Complete-O RIGID classifier and symbolic lower-merge residual.

Bounded symbolic result only; no global Collatz theorem.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

import collatz_reverse_trit_separator_v0 as v0
import collatz_prefix_residues as pref
import collatz_q0_coalescence_component_audit as q0
import collatz_symbolic_merge as sm

G=v0.G
L=v0.L
DEPTH=v0.DEPTH


def q3_residuals():
    acts,_,_=v0.extremal_reverse_actions()
    out=[]
    prev=None
    for j in range(1,DEPTH+1):
        qj=v0.terminal_residue(tuple(acts[:j]))
        if prev is not None:
            assert qj%(3**(j-1))==prev
        prev=qj
        base=qj%(3**(j-1)) if j>1 else 0
        digit=(qj//(3**(j-1)))%3
        for alt in range(3):
            if alt==digit:
                continue
            r=base+alt*3**(j-1)
            if v0.best_contracting_prefix(r,j) is not None:
                continue
            # At a live resonance Q>0, endpoint residue 0 mod3 is impossible:
            # after any odd shortcut step the orbit is nonzero mod3 forever.
            if r%3==0:
                continue
            out.append((j,r))
    assert len(out)==27, len(out)
    return out


def prefix_affine(s,h):
    """For y=s mod 2^h: 2^h T^h(y)=3^q y + A."""
    x=s
    q=0
    A=0
    for t in range(h):
        if x&1:
            q+=1
            A=3*A+(1<<t)
            x=(3*x+1)//2
        else:
            x//=2
    return q,A


def max_reverse_cost(h,q,o):
    """Largest S with 2^S 3^q < 2^h 3^o."""
    S=o-1
    while (1<<(S+1))*(3**q) < (1<<h)*(3**o):
        S+=1
    return S


def crt(a,m,b,n):
    assert __import__("math").gcd(m,n)==1
    return (a + ((b-a)*pow(m,-1,n)%n)*m)%(m*n)


def closes(j,r,h,s,replay=False):
    """Uniform h-forward / reverse lower merge on one Q2xQ3 cell."""
    q,A=prefix_affine(s,h)
    prec=j+q
    P=3**prec
    zres=((3**q)*r+A)*pow(1<<h,-1,P)%P

    for o in range(1,prec+1):
        budget=max_reverse_cost(h,q,o)
        if budget<o:
            continue
        den3=3**o
        ro=zres%den3
        w=v0.contracting_word(o,ro,budget)
        if w is None:
            continue
        S,C=v0.cocycle(w)
        den=(1<<h)*den3
        coeff=(1<<S)*(3**q)
        const=(1<<S)*A-(1<<h)*C
        gap=den-coeff
        if gap<=0:
            continue
        # p=(coeff*y+const)/den; require 0<p<y-G for every y>=L.
        if coeff*L+const<=0:
            continue
        margin=gap*L-const-den*G
        if margin<=0:
            continue

        if replay:
            M3=3**j
            M2=1<<h
            y0=crt(r,M3,s,M2)
            step=M3*M2
            y=y0+max(0,(L-y0+step-1)//step)*step
            assert y%M3==r and y%M2==s
            z=y
            for _ in range(h):
                z=(3*z+1)//2 if z&1 else z//2
            assert z%den3==ro
            num=(1<<S)*z-C
            assert num%den3==0
            p=num//den3
            assert 0<p<y-G
            x=p
            for a in reversed(w):
                assert x&1
                x=(3*x+1)//2
                for _ in range(a-1):
                    assert x%2==0
                    x//=2
            assert x==z
        return True
    return False


def lawful_odd(h):
    return [s for s in range(1,1<<h,2) if pref.survives_prefix(s,h)]


def factor_at(h,q3s):
    q2=lawful_odd(h)
    survivor_sets=[]
    closed_checks=0
    for j,r in q3s:
        live=[]
        for s in q2:
            if closes(j,r,h,s,replay=True):
                closed_checks+=1
            else:
                live.append(s)
        survivor_sets.append(tuple(live))

    first=survivor_sets[0]
    factorized=all(x==first for x in survivor_sets[1:])
    return dict(
        depth=h,
        lawful_q2=len(q2),
        q3_classes=len(q3s),
        product_cells=len(q2)*len(q3s),
        factorized=factorized,
        common_survivors=len(first) if factorized else None,
        common_survivor_residues=list(first) if factorized else None,
        closed_cell_checks=closed_checks,
        survivor_set_sizes=sorted(set(map(len,survivor_sets))),
    )


def run(output:Path):
    q3s=q3_residuals()
    rows=[factor_at(h,q3s) for h in (10,12,14,16)]
    assert all(row["factorized"] for row in rows)

    row14=next(x for x in rows if x["depth"]==14)
    common=set(row14["common_survivor_residues"])
    assert len(common)==436, len(common)

    rigid={s for s in common if q0.cylinder_status(14,s)[0]=="RIGID"}
    assert rigid==common, (len(rigid),len(common))

    _,merge_residual,_=sm.compile_portfolio(14)
    merge_b={x["b"] for x in merge_residual}
    assert common<=merge_b
    merge_closed_by_product=sorted(merge_b-common)
    assert len(merge_closed_by_product)==157, len(merge_closed_by_product)

    result=dict(
        schema="COLLATZ_BIADIC_RESIDUAL_FACTORIZATION_V2",
        q3_residual_classes=[{"depth":j,"residue":r,"modulus":3**j} for j,r in q3s],
        depths=rows,
        depth14=dict(
            common_survivors=sorted(common),
            all_common_survivors_complete_o_rigid=True,
            all_common_survivors_in_symbolic_lower_merge_residual=True,
            symbolic_lower_merge_residual=len(merge_b),
            additional_symbolic_residual_classes_closed_by_product=len(merge_closed_by_product),
            additionally_closed=merge_closed_by_product,
        ),
        verdict="PASS_Q3_FACTORS_OUT_TO_COMMON_Q2_RIGID_RESIDUAL",
        scope=("depths 10/12/14/16; extremal first-resonance Q3 first-difference classes; "
               "coefficient-persistent Q2 prefixes; no all-depth termination claim"),
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3_CLASSES",len(q3s))
    for row in rows:
        print("DEPTH",row["depth"],
              "LAWFUL_Q2",row["lawful_q2"],
              "COMMON_SURVIVORS",row["common_survivors"],
              "FACTORIZED",row["factorized"])
    print("DEPTH14_COMPLETE_O_RIGID",len(rigid),"/",len(common))
    print("DEPTH14_SYMBOLIC_RESIDUAL",len(merge_b),
          "PRODUCT_SURVIVORS",len(common),
          "ADDITIONAL_CLOSED",len(merge_closed_by_product))
    print("FIRST_COMMON_SURVIVORS",sorted(common)[:80])
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.output)
