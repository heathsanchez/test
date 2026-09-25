#!/usr/bin/env python3
"""Exact bi-adic centre audit for Collatz same-anchor return laws.

Discovery target:
  the old 2-adic switch constant and the new 3-adic nearest-centre geometry
  are the same projective determinant J_ij = C_i B_j - C_j B_i.

This is a bounded theorem-discovery audit, not a Collatz proof.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict, Counter
from fractions import Fraction
from pathlib import Path

import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base


def vpq(q: Fraction, p: int):
    if q == 0:
        return None
    return fk.vpz(q.numerator, p) - fk.vpz(q.denominator, p)


def centre(c):
    return Fraction(c["B"], c["C"])


def det(a,b):
    return a["C"]*b["B"] - b["C"]*a["B"]


def centre_key(c):
    q=centre(c)
    return (q.numerator,q.denominator)


def event_state(e, bank, with_v2=False):
    c=e["cert"]; m=e["m0"]
    vals=[fk.vpz(fk.defect(d,m),3) for d in bank]
    finite=[v for v in vals if v is not None]
    if any(v is None for v in vals):
        r=None
        inds=[i for i,v in enumerate(vals) if v is None]
    else:
        r=max(finite,default=0)
        inds=[i for i,v in enumerate(vals) if v==r]
    # centre identity, not semantic-map identity
    nearest_centres=sorted({centre_key(bank[i]) for i in inds})
    nq=nearest_centres[0] if nearest_centres else None
    key=(fk.semantic_id(c),nq,r)
    if with_v2:
        v2=fk.v2z(fk.defect(c,m))
        key=key+(None if v2 is None else v2-(c["D"]+1),)
    return key, vals, inds


def analyze(lo,hi,K,out):
    patterns=defaultdict(dict)
    seqs=[]
    incomplete=[]
    counts=Counter()
    start=lo|1
    for n in range(start,hi+1,2):
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
            seqs.append((r,seq))
            counts["anchor_sequences"]+=1
            counts["return_occurrences"]+=len(seq)
            for e in seq:
                c=e["cert"]; patterns[r][fk.semantic_id(c)]=c

    bank={r:tuple(patterns[r][k] for k in sorted(patterns[r])) for r in sorted(patterns)}
    counts["anchors"]=len(bank)
    counts["semantic_patterns"]=sum(len(v) for v in bank.values())
    distinct_centres={r:len({centre_key(c) for c in cs}) for r,cs in bank.items()}
    counts["distinct_centres"]=sum(distinct_centres.values())
    counts["semantic_minus_centre_duplicates"]=counts["semantic_patterns"]-counts["distinct_centres"]

    # Projective determinant = p-adic centre separation at p=2 and 3.
    pair_checks=0
    for r,cs in bank.items():
        for i,a in enumerate(cs):
            assert a["C"]%2 and a["C"]%3
            for b in cs[i+1:]:
                J=det(a,b)
                if J==0:
                    assert centre(a)==centre(b)
                    continue
                dq=centre(b)-centre(a)
                assert vpq(dq,2)==fk.v2z(J)
                assert vpq(dq,3)==fk.vpz(J,3)
                pair_checks+=1

    profile_checks=0
    own_transport_checks=0
    reselection=Counter()
    transition_rows=[]
    succ0=defaultdict(set)
    succ1=defaultdict(set)
    centre_id_kernel_data=[]

    for r,seq in seqs:
        cs=bank[r]
        states0=[]; states1=[]
        for e in seq:
            s0,vals,inds=event_state(e,cs,False)
            s1,_,_=event_state(e,cs,True)
            states0.append(s0); states1.append(s1)
            nearest_q=Fraction(*s0[1])
            rr=s0[2]
            # Recover entire v3 profile from nearest centre + radius.
            rep=next(c for c in cs if centre(c)==nearest_q)
            for d,actual in zip(cs,vals):
                if centre(d)==nearest_q:
                    pred=rr
                else:
                    sd=fk.vpz(det(rep,d),3)
                    pred=sd if rr is None else min(rr,sd)
                assert actual==pred,(r,e["source"],s0,fk.semantic_tuple(d),actual,pred)
                profile_checks+=1

            c=e["cert"]; m0=e["m0"]; m1=e["m1"]
            d0=fk.defect(c,m0); d1=fk.defect(c,m1)
            assert (1<<c["D"])*d1==c["A"]*d0
            if d0:
                assert fk.v2z(d1)==fk.v2z(d0)-c["D"]
                assert fk.vpz(d1,3)==fk.vpz(d0,3)+fk.vpz(c["A"],3)
                own_transport_checks+=1

            # Exact 3-adic reselection law after executing current return.
            out_vals=[fk.vpz(fk.defect(d,m1),3) for d in cs]
            if any(v is None for v in out_vals):
                rout=None
                out_inds=[i for i,v in enumerate(out_vals) if v is None]
            else:
                rout=max(out_vals,default=0)
                out_inds=[i for i,v in enumerate(out_vals) if v==rout]
            qj=centre(c)
            active_before=fk.vpz(fk.defect(c,m0),3)
            active_after=fk.vpz(fk.defect(c,m1),3)
            t=None if active_before is None else active_before+fk.vpz(c["A"],3)
            assert active_after==t
            if t is None:
                reselection["zero_active_defect"]+=1
            else:
                assert rout is None or rout>=t
                out_centres=sorted({centre_key(cs[i]) for i in out_inds})
                qout=Fraction(*out_centres[0])
                if qout==qj:
                    reselection["active_centre"]+=1
                else:
                    repout=next(d for d in cs if centre(d)==qout)
                    sj=fk.vpz(det(c,repout),3)
                    if rout is not None and rout>t:
                        assert sj==t,(qj,qout,t,rout,sj)
                        reselection["strict_overtake_at_critical_sphere"]+=1
                    else:
                        assert sj>=t,(qj,qout,t,rout,sj)
                        reselection["tie_inside_active_ball"]+=1
                transition_rows.append({
                    "source":e["source"],"anchor":r,
                    "active":fk.semantic_tuple(c),
                    "active_centre":centre_key(c),
                    "before_nearest":s0[1],"before_radius":rr,
                    "active_depth_before":active_before,
                    "active_depth_after":t,
                    "after_nearest":out_centres[0] if out_inds else None,
                    "after_radius":rout,
                })

        for a,b in zip(states0,states0[1:]): succ0[a].add(b)
        for a,b in zip(states1,states1[1:]): succ1[a].add(b)

    amb0={repr(k):len(v) for k,v in succ0.items() if len(v)>1}
    amb1={repr(k):len(v) for k,v in succ1.items() if len(v)>1}

    result={
        "range":[start,hi],"K":K,
        "counts":dict(sorted(counts.items())),
        "incomplete_sources":incomplete,
        "distinct_centres_by_anchor":{str(k):v for k,v in distinct_centres.items()},
        "determinant_pair_checks":pair_checks,
        "nearest_profile_reconstruction_checks":profile_checks,
        "own_biadic_transport_checks":own_transport_checks,
        "reselection":dict(sorted(reselection.items())),
        "compressed_state_nodes":len(succ0),
        "compressed_state_ambiguous_successors":len(amb0),
        "compressed_plus_v2_nodes":len(succ1),
        "compressed_plus_v2_ambiguous_successors":len(amb1),
        "first_ambiguous_compressed":next(iter(amb0.items()),None),
        "first_ambiguous_plus_v2":next(iter(amb1.items()),None),
        "verdict":"PASS_EXACT_BIADIC_CENTRE_GEOMETRY_WITH_TRANSITION_RESIDUAL",
        "scope":"bounded completed hereditary q0 RIGID return language; no Collatz theorem",
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("COUNTS",json.dumps(result["counts"],sort_keys=True))
    print("DETERMINANT_PAIR_CHECKS",pair_checks)
    print("PROFILE_RECONSTRUCTION_CHECKS",profile_checks)
    print("OWN_BIADIC_TRANSPORT_CHECKS",own_transport_checks)
    print("RESELECTION",json.dumps(result["reselection"],sort_keys=True))
    print("AMBIGUOUS",len(amb0),len(amb1))
    print("FIRST_AMBIGUOUS_COMPRESSED",result["first_ambiguous_compressed"])
    print("FIRST_AMBIGUOUS_PLUS_V2",result["first_ambiguous_plus_v2"])
    print("VERDICT",result["verdict"])
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=43009)
    ap.add_argument("--hi",type=int,default=45055)
    ap.add_argument("--K",type=int,default=128)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    analyze(a.lo,a.hi,a.K,a.output)
