#!/usr/bin/env python3
"""Farey-rung normalization falsifier for the Collatz closeout.

Compare the protected endpoint survivor language at the first two certified
Farey contraction rungs.  Each rung gets its own exact live lower bound,
near-return gap, and minimal 3-adic squeeze depth.  We then reuse exactly the
V0/V1/V2 direct/forward/reverse certificate compiler and ask:

  * do all first-difference Q3 parent charts quotient to one Q2 language?
  * after quotienting parent identity, is that canonical Q2 language the same
    at rung 1 and rung 2?

This is a bounded normalization falsifier (Q2 depths <= requested maximum),
not a Collatz proof.  A mismatch is emitted as the first earned rung
separator; equality is evidence for a rung-independent protected quotient.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from fractions import Fraction

import collatz_reverse_trit_separator_v0 as v0
import collatz_reverse_trit_bicell_v1 as v1
import collatz_reverse_trit_bicell_v2 as v2
import collatz_transfer_farey as farey
import collatz_transfer_ladder as ladder


def ceil_frac(x: Fraction) -> int:
    return (x.numerator + x.denominator - 1) // x.denominator


def squeeze_depth(gap: int) -> int:
    b=0
    m=2
    while m <= gap:
        b += 1
        m *= 3
    return b


def rung2_gap() -> int:
    # Same exact DK displacement inequality used at rung 1, now with the
    # single-convergent error 1/3 and conditional lower bound B1.
    hi = Fraction(ladder.q2,1)/(6*ladder.ln2_lo) + Fraction(1,3) \
         - ladder.eps2_lo * ladder.B1
    assert hi > 0
    return ceil_frac(hi)


def configure(Q:int,T:int,L:int,G:int,depth:int):
    # V0/V1/V2 were written with frozen rung-1 globals.  Their certificate
    # formulas are rung-parametric, so patch only those declared constants.
    v0.Q=Q; v0.T=T; v0.L=L; v0.G=G; v0.DEPTH=depth
    v1.G=G; v1.L=L; v1.DEPTH=depth
    v2.G=G; v2.L=L; v2.DEPTH=depth


def residual_parents(Q:int,T:int,L:int,G:int,depth:int):
    configure(Q,T,L,G,depth)
    acts,_,_=v0.extremal_reverse_actions(depth)
    assert len(acts)==depth
    out=[]
    for j in range(1,depth+1):
        qj=v0.terminal_residue(tuple(acts[:j]))
        base=qj%(3**(j-1)) if j>1 else 0
        qdigit=(qj//(3**(j-1)))%3
        for digit in range(3):
            if digit==qdigit:
                continue
            r=base+digit*3**(j-1)
            direct=v0.best_contracting_prefix(r,j)
            for parity in (0,1):
                closed=False
                kind=None
                if direct is not None:
                    closed=True; kind="DIRECT_REVERSE"
                elif r%3==0:
                    closed=True; kind="IMPOSSIBLE_ENDPOINT_MOD3"
                elif v1.one_step_reverse_cert(r,j,parity) is not None:
                    closed=True; kind="ONE_FORWARD_THEN_REVERSE"
                if not closed:
                    out.append(dict(depth=j,first_difference_depth=j-1,
                                    centre_digit=qdigit,alternate_digit=digit,
                                    residue=r,modulus=3**j,parity=parity))
    return acts,out


def evolve(name,Q,T,L,G,depth,max_q2):
    configure(Q,T,L,G,depth)
    acts,parents=residual_parents(Q,T,L,G,depth)
    live={i:{1} for i in range(len(parents))}
    rows=[]
    canon={}
    equal_all=True
    for a in range(1,max_q2+1):
        if a>1:
            bit=1<<(a-1)
            live={i:{x for s in vals for x in (s,s|bit)}
                  for i,vals in live.items()}
        nxt={}
        kinds={}
        for i,vals in live.items():
            keep=set()
            for s in sorted(vals):
                cert=v2.composed_certificate(parents[i],s,a)
                if cert is None:
                    keep.add(s)
                else:
                    kinds[cert["kind"]]=kinds.get(cert["kind"],0)+1
            nxt[i]=keep
        live=nxt
        langs=[tuple(sorted(live[i])) for i in range(len(parents))]
        distinct=sorted(set(langs))
        eq=(len(distinct)<=1)
        equal_all &= eq
        canonical=list(distinct[0]) if len(distinct)==1 else None
        if canonical is not None:
            canon[a]=canonical
        row=dict(rung=name,q2_depth=a,q3_parent_count=len(parents),
                 distinct_parent_languages=len(distinct),
                 per_parent_counts=sorted(set(map(len,langs))) if langs else [],
                 canonical_language=canonical,
                 closure_kinds=dict(sorted(kinds.items())))
        rows.append(row)
        print("RUNG_LANGUAGE",json.dumps(row,sort_keys=True))
    return dict(
        name=name,Q=Q,T=T,L=L,G=G,squeeze_depth=depth,
        reverse_actions=acts,q3_parent_count=len(parents),
        parent_languages_equal_all_depths=equal_all,
        canonical=canon,rows=rows,
    )


def run(max_q2:int,out:Path):
    G1=farey.live_gap_ceiling
    d1=squeeze_depth(G1)
    assert d1==20

    G2=rung2_gap()
    d2=squeeze_depth(G2)
    assert G2==30243148343
    assert d2==22

    r1=evolve("rung1",farey.q1,farey.t1,farey.L,G1,d1,max_q2)
    r2=evolve("rung2",ladder.q2,ladder.t2,ladder.B1,G2,d2,max_q2)

    comparisons=[]
    same_all=True
    first_separator=None
    for a in range(1,max_q2+1):
        c1=r1["canonical"].get(a)
        c2=r2["canonical"].get(a)
        same=(c1 is not None and c2 is not None and c1==c2)
        same_all &= same
        row=dict(depth=a,same=same,
                 rung1_count=None if c1 is None else len(c1),
                 rung2_count=None if c2 is None else len(c2))
        if not same and first_separator is None:
            s1=set(c1 or ()); s2=set(c2 or ())
            first_separator=dict(depth=a,
                rung1_only=sorted(s1-s2)[:100],
                rung2_only=sorted(s2-s1)[:100],
                rung1_parent_languages=r1["rows"][a-1]["distinct_parent_languages"],
                rung2_parent_languages=r2["rows"][a-1]["distinct_parent_languages"])
        comparisons.append(row)
        print("RUNG_COMPARE",json.dumps(row,sort_keys=True))

    result=dict(
        schema="COLLATZ_FAREY_RUNG_NORMALIZATION_V0",
        max_q2_depth=max_q2,
        rung1={k:v for k,v in r1.items() if k!="canonical"},
        rung2={k:v for k,v in r2.items() if k!="canonical"},
        comparisons=comparisons,
        same_canonical_language_all_depths=same_all,
        first_separator=first_separator,
        verdict=("PASS_BOUNDED_RUNG_INDEPENDENT_ENDPOINT_QUOTIENT"
                 if same_all else "EXACT_RUNG_SEPARATOR_REMAINS"),
        scope=("first two certified Farey rungs; exact first-difference Q3 "
               "charts and existing V2 certificate compiler; bounded Q2 depth; "
               "rung2 conditional on closure below B1; no global Collatz claim")
    )
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RUNG1_GAP",G1,"TRITS",d1,"PARENTS",r1["q3_parent_count"])
    print("RUNG2_GAP",G2,"TRITS",d2,"PARENTS",r2["q3_parent_count"])
    print("FIRST_SEPARATOR",json.dumps(first_separator,sort_keys=True))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-q2-depth",type=int,default=14)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert 2<=a.max_q2_depth<=16
    run(a.max_q2_depth,a.output)
