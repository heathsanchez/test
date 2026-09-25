#!/usr/bin/env python3
"""Exact 3-adic nearest-centre ball-transport audit.

If q_* is a nearest return centre to m at depth h, then m lies in the 3-adic
ball B(q_*,h). A return macro c has affine factor alpha=3^R/2^D, hence maps
that entire ball to B(F_c(q_*), h+R).

If every return centre has fixed 3-adic distance from the image-ball centre
strictly below h+R, the whole image ball lies in one fixed Voronoi cell and
the next nearest centre+depth is determined without resolving valuation ties
at m directly.

This is finite theorem discovery, not a Collatz proof.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path

import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base


def r_exp(c):
    a=int(c["A"]); r=0
    while a>1:
        assert a%3==0
        a//=3;r+=1
    return r


def centre(c):
    return Fraction(int(c["B"]),int(c["C"]))


def apply(c,x):
    return (int(c["A"])*x+int(c["B"])) / (1<<int(c["D"]))


def v3_frac(x):
    if x==0:return None
    assert x.denominator%3!=0
    return fk.vpz(x.numerator,3)


def nearest(bank,m):
    vals=tuple(fk.vpz(fk.defect(c,m),3) for c in bank)
    assert all(v is not None for v in vals)
    h=max(vals); i=next(i for i,v in enumerate(vals) if v==h)
    return i,h,vals


def audit(lo,hi,K,out):
    patterns=defaultdict(dict); seqs=[]; incomplete=[]; counts=Counter()
    for n in range(max(3,lo)|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID":continue
        counts["hereditary_birth_rigid"]+=1
        if not fk.completed_rigid_source(n,K):
            incomplete.append(n);continue
        counts["completed_sources"]+=1
        for r,seq in fk.return_sequences(n,K).items():
            if not seq:continue
            seqs.append(seq);counts["anchor_sequences"]+=1
            counts["return_occurrences"]+=len(seq)
            for e in seq:
                c=e["cert"];patterns[r][fk.semantic_id(c)]=c
    banks={r:tuple(sorted(patterns[r].values(),key=fk.semantic_tuple)) for r in sorted(patterns)}
    counts["semantic_patterns"]=sum(len(v) for v in banks.values())

    certified=0; exact_centre=0; ambiguous=[]; failures=[]; overcancel=[]; equality_checks=0
    for seq in seqs:
        for pos,e in enumerate(seq[:-1]):
            c=e["cert"]; bank=banks[e["anchor"]]
            ni,h,_=nearest(bank,e["m0"]); qstar=centre(bank[ni])
            radius=h+r_exp(c)
            z=apply(c,qstar)

            depths=[v3_frac(z-centre(q)) for q in bank]
            ai,ah,_=nearest(bank,e["m1"])

            # m'-z has EXACT 3-adic depth radius. Hence for each centre:
            #   image depth < radius  => preserved exactly;
            #   image depth > radius (or z==centre) => actual depth exactly radius;
            #   image depth = radius => only genuine cancellation ambiguity.
            pred=[]
            equal_ties=[]
            for ii,s in enumerate(depths):
                if s is None or s>radius:
                    pred.append(radius)
                    if s is None:
                        exact_centre+=1
                elif s<radius:
                    pred.append(s)
                else:
                    pred.append(None)
                    equal_ties.append(ii)

            if equal_ties:
                equality_checks += len(equal_ties)
                actual_vals=[fk.vpz(fk.defect(q,e["m1"]),3) for q in bank]
                bad=[i for i in equal_ties if actual_vals[i] > radius]
                if bad:
                    overcancel.append({
                        "source":e["source"],"anchor":e["anchor"],"position":pos,
                        "nearest_before":fk.semantic_id(bank[ni]),"h":h,
                        "current":fk.semantic_id(c),"radius":radius,
                        "overcancel_centres":[fk.semantic_id(bank[i]) for i in bad],
                        "actual_depths":[actual_vals[i] for i in bad],
                    })
                # Candidate no-overcancellation law predicts equality targets at radius.
                for i in equal_ties:
                    pred[i]=radius
            certified+=1
            hp=max(pred); pi=next(i for i,v in enumerate(pred) if v==hp)
            if (ai,ah)!=(pi,hp):
                failures.append((e["source"],e["anchor"],pos,"exact_ball",pi,hp,ai,ah,radius))

    result={
      "range":[lo,hi],"K":K,"counts":dict(counts),
      "incomplete_sources":incomplete,
      "margin_certified":certified,
      "exact_centre_cases":exact_centre,
      "ambiguous_count":len(ambiguous),
      "ambiguous_examples":ambiguous[:40],
      "equality_checks":equality_checks,
      "overcancellation_count":len(overcancel),
      "overcancellation_examples":overcancel[:40],
      "failures":failures,
    }
    if not incomplete and not failures and not overcancel:
        result["verdict"]="PASS_BOUNDED_NO_3ADIC_OVERCANCELLATION_BALL_TRANSPORT"
    elif not incomplete and not failures:
        result["verdict"]="SEPARATOR_3ADIC_OVERCANCELLATION"
    else:
        result["verdict"]="SEPARATOR_IMAGE_BALL_TRANSPORT_FAILURE"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("COUNTS",json.dumps(dict(counts),sort_keys=True))
    print("INCOMPLETE",len(incomplete))
    print("MARGIN_CERTIFIED",certified,"EXACT_CENTRE",exact_centre,
          "EQUALITY_CHECKS",equality_checks,"OVERCANCELLATION",len(overcancel),
          "FAILURES",len(failures))
    for z in overcancel[:20]: print("OVERCANCEL",json.dumps(z,sort_keys=True))
    for z in failures[:20]: print("FAILURE",z)
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--lo",type=int,default=3)
    p.add_argument("--hi",type=int,default=8191)
    p.add_argument("--K",type=int,default=128)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();audit(a.lo,a.hi,a.K,a.out)
