#!/usr/bin/env python3
"""Exact 3-adic nearest-centre transport audit for Collatz RIGID returns.

For a return macro c:
    F_c(m)=(A_c*m+B_c)/2^D_c,  A_c=3^R_c,
    C_c=2^D_c-A_c,  q_c=B_c/C_c,
    Delta_c(m)=C_c*m-B_c.

Because C_c is a 3-adic unit, v3(Delta_c(m)) is the 3-adic depth of m
relative to q_c. Executing c gives
    F_c(m)-q_c = (3^R_c/2^D_c) * (m-q_c),
so active-centre 3-adic depth rises exactly by R_c.

For any other centre i:
    F_c(m)-q_i = (q_c-q_i) + (3^R_c/2^D_c)(m-q_c).
Thus, outside the exact valuation-tie case, the next 3-adic depth is the
ultrametric minimum of the centre separation and active transported depth.

This probe checks:
  1. nearest-centre state determines active-centre depth exactly;
  2. every non-tie target depth follows the ultrametric min law;
  3. whether any continuing RIGID transition encounters a tie;
  4. whether nearest-centre + depth predicts the next nearest centre on all
     tie-free transitions.

Discovery only; finite corpus evidence, not a Collatz proof.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base


def r_exp(c):
    a=int(c["A"]); r=0
    while a>1:
        assert a%3==0
        a//=3; r+=1
    assert a==1
    return r


def sep3(a,b):
    if fk.semantic_tuple(a)==fk.semantic_tuple(b):
        return None
    j=int(a["C"])*int(b["B"])-int(b["C"])*int(a["B"])
    assert j!=0
    return fk.vpz(j,3)


def nearest(bank,m):
    vals=tuple(fk.vpz(fk.defect(c,m),3) for c in bank)
    assert all(v is not None for v in vals)
    h=max(vals)
    idx=next(i for i,v in enumerate(vals) if v==h)
    return idx,h,vals


def audit(lo,hi,K,out):
    patterns=defaultdict(dict)
    seqs=[]
    incomplete=[]
    counts=Counter()

    for n in range(max(3,lo)|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID":
            continue
        counts["hereditary_birth_rigid"]+=1
        if not fk.completed_rigid_source(n,K):
            incomplete.append(n); continue
        counts["completed_sources"]+=1
        rs=fk.return_sequences(n,K)
        for r,seq in rs.items():
            if not seq: continue
            seqs.append(seq)
            counts["anchor_sequences"]+=1
            counts["return_occurrences"]+=len(seq)
            for e in seq:
                c=e["cert"]
                patterns[r][fk.semantic_id(c)]=c

    bank_by_anchor={
        r:tuple(sorted(patterns[r].values(),key=fk.semantic_tuple))
        for r in sorted(patterns)
    }
    counts["anchors"]=len(bank_by_anchor)
    counts["semantic_patterns"]=sum(len(v) for v in bank_by_anchor.values())

    tie_rows=[]
    continuing_ties=[]
    prediction_fail=[]
    active_depth_fail=[]
    nontie_depth_checks=0
    nearest_prediction_checks=0

    for seq in seqs:
        for pos,e in enumerate(seq):
            c=e["cert"]; r=e["anchor"]; m0=e["m0"]; m1=e["m1"]
            bank=bank_by_anchor[r]
            ci=next(i for i,z in enumerate(bank)
                    if fk.semantic_tuple(z)==fk.semantic_tuple(c))
            ni,h,vals=nearest(bank,m0)
            qstar=bank[ni]

            # Nearest-centre + depth must reconstruct active-centre depth.
            if ni==ci:
                xpred=h
            else:
                s=sep3(qstar,c)
                xpred=min(h,s)
            xactual=vals[ci]
            if xpred!=xactual:
                active_depth_fail.append((e["source"],r,pos,ni,ci,h,xpred,xactual))
                continue

            t=xactual+r_exp(c)
            pred=[]
            ties=[]
            actual_after=[]
            for ii,z in enumerate(bank):
                va=fk.vpz(fk.defect(z,m1),3)
                assert va is not None
                actual_after.append(va)
                if ii==ci:
                    pred.append(t)
                    assert va==t
                    continue
                s=sep3(c,z)
                if s==t:
                    ties.append(ii)
                    pred.append(None)
                else:
                    p=min(s,t)
                    pred.append(p)
                    assert va==p,(e["source"],r,pos,ii,s,t,va,p)
                    nontie_depth_checks+=1

            if ties:
                row={
                    "source":e["source"],"anchor":r,"position":pos,
                    "current":fk.semantic_id(c),
                    "nearest_before":fk.semantic_id(qstar),
                    "h":h,"active_depth":xactual,"transported_depth":t,
                    "tie_targets":[fk.semantic_id(bank[i]) for i in ties],
                    "continuing":pos+1<len(seq),
                }
                tie_rows.append(row)
                if row["continuing"]:
                    continuing_ties.append(row)
            else:
                # Fully predicted profile => predicted canonical nearest.
                hp=max(pred)
                pi=next(i for i,v in enumerate(pred) if v==hp)
                ai,ha,_=nearest(bank,m1)
                nearest_prediction_checks+=1
                if (pi,hp)!=(ai,ha):
                    prediction_fail.append({
                        "source":e["source"],"anchor":r,"position":pos,
                        "predicted":[pi,hp],"actual":[ai,ha],
                    })

    result={
        "scope":"finite completed hereditary q0 RIGID corpus; discovery only",
        "range":[lo,hi],"K":K,
        "counts":dict(counts),
        "incomplete_sources":incomplete,
        "active_depth_failures":active_depth_fail,
        "non_tie_depth_checks":nontie_depth_checks,
        "tie_count":len(tie_rows),
        "continuing_tie_count":len(continuing_ties),
        "tie_examples":tie_rows[:40],
        "nearest_prediction_checks":nearest_prediction_checks,
        "nearest_prediction_failures":prediction_fail,
    }
    if (not incomplete and not active_depth_fail and not prediction_fail
            and not continuing_ties):
        result["verdict"]="PASS_BOUNDED_TIE_FREE_CONTINUING_3ADIC_TRANSPORT"
    elif (not incomplete and not active_depth_fail and not prediction_fail):
        result["verdict"]="SEPARATOR_CONTINUING_3ADIC_TIES"
    else:
        result["verdict"]="SEPARATOR_3ADIC_NEAREST_TRANSPORT"

    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("COUNTS",json.dumps(dict(counts),sort_keys=True))
    print("INCOMPLETE",len(incomplete))
    print("ACTIVE_DEPTH_FAILURES",len(active_depth_fail))
    print("NONTIE_DEPTH_CHECKS",nontie_depth_checks)
    print("TIES",len(tie_rows),"CONTINUING_TIES",len(continuing_ties))
    for z in continuing_ties[:20]:
        print("CONTINUING_TIE",json.dumps(z,sort_keys=True))
    print("NEAREST_PREDICTION_CHECKS",nearest_prediction_checks,
          "FAILURES",len(prediction_fail))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--lo",type=int,default=3)
    p.add_argument("--hi",type=int,default=32767)
    p.add_argument("--K",type=int,default=128)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    audit(a.lo,a.hi,a.K,a.out)
